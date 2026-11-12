// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import { gustFactor, dirVec, type WeatherService } from '@ferret/weather';

/**
 * The wind on things that are not simulated one by one: trees, bushes, grass, wires, awnings. The weather (`@ferret/weather`) is the only source: `WindField` samples its gust pattern
 * (the patches that travel with the wind) onto a small texture round the camera, and `WindSway` is a material plugin that moves the vertices of a mesh by that wind, so a gust that
 * leans the grass at one place reaches the oaks downwind a moment later and the wires of the street after them.
 */
export interface SwayMode {
  /** `plant`: the vertex height in a mesh of the given unit height is the weight (the crown bends, the foot stays);
   *  `tree`: the weight is the height in the mesh's bounding box, from the vertex colour's red channel when the mesh has one (the painted weights of the models of the street);
   *  `cable`: the weight is how far a vertex hangs below the tops of the poles; `cable-uv`: the weight is sin(pi u) of the first uv set (a wire made along its length);
   *  `awning`: the weight grows from the wall edge to the free edge, along the local +x of the part. */
  kind: 'plant' | 'tree' | 'cable' | 'cable-uv' | 'awning';
  /** how strongly the leaves shiver in their own right (tree) or how much the cloth flaps (awning), 0..1 */
  flutter?: number;
  /** overall scale of the displacement (1 = a real tree of the size in the mesh) */
  gain?: number;
  /** plant: the height of the unit mesh (default 1); cable: the height of the pole tops and the sag that makes weight 1, metres */
  unit?: number; top?: number; sag?: number;
  /** tree: take the weights from the vertex colour's red channel when present */
  weightsFromColor?: boolean;
}
export interface SwayRule extends SwayMode { /** a regular expression over the material name */ match: string }

const SPAN = 768, N = 96;

export class WindField {
  readonly tex: BABYLON.RawTexture;
  private data = new Uint8Array(N * N * 4);
  private cell = SPAN / N;
  /** the wind now: direction (x, z), speed at 10 m (m/s), time (s); the texture's window origin and span */
  readonly u = { dirX: 1, dirZ: 0, speed: 0, time: 0, ox: 0, oz: 0, span: SPAN, gain: 1 };
  private last = -1e9;
  constructor(private scene: BABYLON.Scene, private weather: WeatherService) {
    this.tex = BABYLON.RawTexture.CreateRGBATexture(this.data, N, N, scene, false, false, BABYLON.Constants.TEXTURE_BILINEAR_SAMPLINGMODE);
    this.tex.wrapU = BABYLON.Constants.TEXTURE_CLAMP_ADDRESSMODE; this.tex.wrapV = BABYLON.Constants.TEXTURE_CLAMP_ADDRESSMODE;
    scene.onBeforeRenderObservable.add(() => this.update());
  }
  private update() {
    const cam = this.scene.activeCamera; if (!cam) return;
    const w = this.weather, s = w.state, t = w.world.time, p = cam.globalPosition;
    const [dx, dz] = dirVec(s.windDir);
    this.u.dirX = dx; this.u.dirZ = dz; this.u.speed = s.wind; this.u.time = t;
    // the window follows the camera in steps of a few cells, so the texture is rewritten at about 10 Hz and the gusts read the same wherever the camera is
    const ox = Math.round(p.x / (this.cell * 8)) * this.cell * 8, oz = Math.round(p.z / (this.cell * 8)) * this.cell * 8;
    if (t - this.last < 0.1 && ox === this.u.ox && oz === this.u.oz) return;
    this.last = t; this.u.ox = ox; this.u.oz = oz;
    for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) {
      const x = ox + (i + 0.5 - N / 2) * this.cell, z = oz + (j + 0.5 - N / 2) * this.cell;
      const g = gustFactor(s, x, z, t, w.seed);
      const o = (j * N + i) * 4; this.data[o] = Math.min(255, Math.round(g / 3 * 255)); this.data[o + 1] = 0; this.data[o + 2] = 0; this.data[o + 3] = 255;
    }
    this.tex.update(this.data);
  }
  /** the wind speed at a place and height (m/s), the same number the shaders read (for the litter and the flags) */
  speedAt(x: number, z: number): number {
    const gx = (x - this.u.ox) / this.cell + N / 2 - 0.5, gz = (z - this.u.oz) / this.cell + N / 2 - 0.5;
    const i = Math.max(0, Math.min(N - 2, Math.floor(gx))), j = Math.max(0, Math.min(N - 2, Math.floor(gz))), fx = Math.min(1, Math.max(0, gx - i)), fz = Math.min(1, Math.max(0, gz - j));
    const at = (a: number, b: number) => this.data[(b * N + a) * 4] / 255 * 3;
    const g = (at(i, j) * (1 - fx) + at(i + 1, j) * fx) * (1 - fz) + (at(i, j + 1) * (1 - fx) + at(i + 1, j + 1) * fx) * fz;
    return this.u.speed * g;
  }
}

const DEFS = `
uniform sampler2D wsTex;
#if defined(WSCOLOR) && !defined(VERTEXCOLOR)
attribute vec4 color;
#endif
#ifdef WSBAKED
attribute float sway; attribute float flutter; attribute float phase; attribute float level; attribute vec3 pivot;
#endif
float wsHash(vec3 p) { return fract(sin(dot(p, vec3(12.9898, 78.233, 37.719))) * 43758.5453); }
`;

const BODY = `
{
  vec2 wsUV = (worldPos.xz - wsB.xy) / wsB.z + 0.5;
  float wsG = texture2D(wsTex, clamp(wsUV, 0.001, 0.999)).r * 3.0;
  float wsU = wsA.z * wsG;
  vec2 wsDir = wsA.xy;
  float wsT = wsA.w;
  float wsKind = wsC.x;
  vec3 wsPivot = finalWorld[3].xyz;
  float wsScale = length(finalWorld[1].xyz);
  vec3 wsOff = vec3(0.0);
  float wsPh = wsHash(floor(wsPivot * 0.37)) * 6.2831;
  if (wsKind < 1.5) {
    float h = clamp(positionUpdated.y / wsC.y, 0.0, 1.6);
    float w = pow(h, 1.7);
    float H = wsC.y * wsScale;
    float lean = clamp(wsU * 0.016, 0.0, 0.42) * wsC.w;
    float osc = sin(wsT * 1.3 + wsPh) * 0.3 + sin(wsT * 2.9 + wsPh * 1.7) * 0.12;
    float a = lean * (1.0 + osc * clamp(wsU / 5.0, 0.15, 1.6));
    wsOff = vec3(wsDir.x, 0.0, wsDir.y) * a * w * H;
    wsOff.y -= 0.5 * a * a * w * H;
    wsOff += vec3(sin(wsT * 8.0 + dot(worldPos.xyz, vec3(2.3, 3.1, 2.9))), sin(wsT * 9.3 + dot(worldPos.xyz, vec3(3.7, 2.1, 3.3))), 0.0) * 0.012 * clamp(wsU / 8.0, 0.0, 1.5) * (0.4 + 0.6 * w) * wsScale * 0.5 * step(0.5, h);
  } else if (wsKind < 2.5) {
    #ifdef WSBAKED
    // the baked wind data of the model (art/street/TREES.md): _SWAY the lever arm, _FLUTTER the leaf weight, _PHASE per branch, _LEVEL trunk/limb/branch/twig/leaf, _PIVOT the branch base
    float bw = pow(sway, 1.6);
    float fq = level < 0.5 ? 0.12 : level < 1.5 ? 0.5 : level < 2.5 ? 0.9 : 1.4;
    float bt = wsT * fq * 6.2831 + phase * 6.2831;
    float ang = clamp(wsU * 0.006, 0.0, 0.16) * bw * (0.55 + 0.45 * sin(bt)) * wsC.w;
    vec3 pw = (finalWorld * vec4(pivot, 1.0)).xyz;
    vec3 axis = vec3(wsDir.y, 0.0, -wsDir.x);
    vec3 rel = worldPos.xyz - pw;
    float ca = cos(ang), sa = sin(ang);
    vec3 rot = rel * ca + cross(axis, rel) * sa + axis * dot(axis, rel) * (1.0 - ca);
    vec3 nw = normalize((finalWorld * vec4(normalUpdated, 0.0)).xyz);
    float fl = wsU * flutter * 0.035 * sin(wsT * 7.0 + dot(worldPos.xyz, vec3(3.0, 5.0, 7.0)) + phase * 6.2831) * clamp(wsU / 4.0, 0.0, 1.6);
    wsOff = (rot - rel) + nw * fl;
    #else
    float h = clamp((positionUpdated.y - wsE.y) / max(wsE.w - wsE.y, 0.001), 0.0, 1.0);
    float m = 1.0;
    #ifdef WSCOLOR
    m = wsD.x > 0.5 ? color.r : 1.0;
    #endif
    float w = (wsD.x > 0.5 ? m : pow(h, 1.6));
    float H = (wsE.w - wsE.y) * wsScale;
    float lean = clamp(wsU * 0.014, 0.0, 0.4) * wsC.w;
    float osc = sin(wsT * 1.1 + wsPh) * 0.3 + sin(wsT * 2.6 + wsPh * 1.9) * 0.14;
    float a = lean * (1.0 + osc * clamp(wsU / 5.0, 0.15, 1.6));
    wsOff = vec3(wsDir.x, 0.0, wsDir.y) * a * w * H;
    wsOff.y -= 0.5 * a * a * w * H;
    wsOff += vec3(sin(wsT * 7.1 + dot(worldPos.xyz, vec3(2.3, 3.1, 2.9))), sin(wsT * 8.3 + dot(worldPos.xyz, vec3(3.7, 2.1, 3.3))), sin(wsT * 6.7 + dot(worldPos.xyz, vec3(1.9, 2.7, 3.1)))) * 0.03 * clamp(wsU / 8.0, 0.0, 1.5) * w * wsD.y;
    #endif
  } else if (wsKind < 4.5) {
    float wsU1 = 0.5;
    #ifdef UV1
    wsU1 = uv.x;
    #endif
    float w = wsKind < 3.5 ? clamp((wsC.y - worldPos.y) / wsC.z, 0.0, 1.0) : sin(3.14159 * wsU1);
    vec2 perp = vec2(-wsDir.y, wsDir.x);
    float blow = min(wsU * wsU * 0.0022, 1.3) * wsC.w;
    float swing = sin(wsT * (1.2 + 0.4 * wsHash(floor(vec3(worldPos.x * 0.02, 0.0, worldPos.z)))) + worldPos.x * 0.07) * (0.05 + 0.04 * clamp(wsU / 10.0, 0.0, 1.5)) * wsC.w;
    float flick = sin(wsT * 9.0 + worldPos.x * 0.8) * 0.006 * clamp(wsU / 8.0, 0.0, 1.5);
    wsOff = vec3(wsDir.x * blow + perp.x * swing, -0.3 * blow * blow * w * 0.3 + flick, wsDir.y * blow + perp.y * swing) * w;
  } else {
    float w = clamp((positionUpdated.x - wsE.x) / max(wsE.z - wsE.x, 0.001), 0.0, 1.0);
    float flap = sin(wsT * (2.6 + wsU * 0.12) + wsPh + worldPos.x * 0.9 + worldPos.z * 0.9) * (0.35 + 0.65 * sin(wsT * 0.9 + wsPh * 2.0));
    float amp = clamp(wsU * 0.012, 0.0, 0.2) * wsC.w;
    wsOff = vec3(0.0, flap * amp * w * w, 0.0) + vec3(wsDir.x, 0.0, wsDir.y) * amp * 0.35 * w * w * (0.6 + 0.4 * flap);
  }
  worldPos.xyz += wsOff;
}
`;

interface PluginLike { dispose(f?: boolean): void }

export function applyWindSway(scene: BABYLON.Scene, field: WindField, rules: SwayRule[]): { materials: number; add(material: BABYLON.Material, mode: SwayMode): void; dispose(): void } {
  const taken = new Map<BABYLON.Material, PluginLike>();
  const meshes = new Map<BABYLON.Material, SwayMode>();
  class Plugin extends BABYLON.MaterialPluginBase implements PluginLike {
    constructor(material: BABYLON.Material, public mode: SwayMode) {
      super(material, 'Take37WindSway', 235, { WSWAY: false, WSCOLOR: false, WSBAKED: false });
      this._enable(true);
    }
    isCompatible(shaderLanguage: number) { return shaderLanguage === 0; }
    getClassName() { return 'Take37WindSwayPlugin'; }
    prepareDefines(defines: BABYLON.MaterialDefines, _s: BABYLON.Scene, mesh: BABYLON.AbstractMesh) {
      defines['WSWAY'] = true;
      const src = mesh instanceof BABYLON.InstancedMesh ? mesh.sourceMesh : mesh;
      defines['WSBAKED'] = this.mode.kind === 'tree' && src.isVerticesDataPresent('sway');
      defines['WSCOLOR'] = !!this.mode.weightsFromColor && src.isVerticesDataPresent(BABYLON.VertexBuffer.ColorKind);
    }
    getAttributes(attributes: string[], _s: BABYLON.Scene, mesh: BABYLON.AbstractMesh) {
      const src = mesh instanceof BABYLON.InstancedMesh ? mesh.sourceMesh : mesh;
      if (this.mode.kind === 'tree' && src.isVerticesDataPresent('sway')) for (const k of ['sway', 'flutter', 'phase', 'level', 'pivot']) if (!attributes.includes(k)) attributes.push(k);
      if (this.mode.weightsFromColor && src.isVerticesDataPresent(BABYLON.VertexBuffer.ColorKind) && !attributes.includes('color')) attributes.push('color');
    }
    getSamplers(samplers: string[]) { samplers.push('wsTex'); }
    getUniforms() {
      const names = ['wsA', 'wsB', 'wsC', 'wsD', 'wsE'];
      return { ubo: names.map(name => ({ name, size: 4, type: 'vec4' })), vertex: names.map(n => `uniform vec4 ${n};`).join('\n') };
    }
    bindForSubMesh(ub: BABYLON.UniformBuffer, _s: BABYLON.Scene, _e: unknown, subMesh: BABYLON.SubMesh) {
      const m = this.mode, u = field.u, kind = { plant: 1, tree: 2, cable: 3, 'cable-uv': 4, awning: 5 }[m.kind];
      ub.updateFloat4('wsA', u.dirX, u.dirZ, u.speed, u.time);
      ub.updateFloat4('wsB', u.ox, u.oz, u.span, 0);
      ub.updateFloat4('wsC', kind, m.kind === 'plant' ? (m.unit ?? 1) : (m.top ?? 10), m.sag ?? 1, m.gain ?? 1);
      ub.updateFloat4('wsD', m.weightsFromColor ? 1 : 0, m.flutter ?? 0, 0, 0);
      const mesh = subMesh.getMesh(), src = mesh instanceof BABYLON.InstancedMesh ? mesh.sourceMesh : mesh;
      const sb = (m.kind === 'awning' ? subMesh.getBoundingInfo() : src.getBoundingInfo()).boundingBox, a = sb.minimum, b = sb.maximum;
      ub.updateFloat4('wsE', a.x, a.y, b.x, b.y);
      ub.setTexture('wsTex', field.tex);
    }
    getCustomCode(shaderType: string) {
      if (shaderType !== 'vertex') return null;
      return { CUSTOM_VERTEX_DEFINITIONS: DEFS, CUSTOM_VERTEX_UPDATE_WORLDPOS: BODY };
    }
  }
  const add = (m: BABYLON.Material, mode: SwayMode) => { if (taken.has(m)) return; taken.set(m, new Plugin(m, mode)); meshes.set(m, mode); };
  const compiled = rules.map(r => ({ r, re: new RegExp(r.match) }));
  const one = (m: BABYLON.Material) => { const hit = compiled.find(x => x.re.test(m.name)); if (hit) add(m, hit.r); };
  for (const m of scene.materials) one(m);
  return { get materials() { return taken.size; }, add, dispose() { for (const p of taken.values()) { try { p.dispose(); } catch { /* gone */ } } taken.clear(); } };
}

/**
 * Reads the wind data baked into the models (art/street/TREES.md: `_SWAY`, `_FLUTTER`, `_PHASE`, `_LEVEL`, `_PIVOT`), which Babylon's glTF loader does not keep, from the glb itself, and puts it on
 * the loaded meshes as vertex buffers `sway`, `flutter`, `phase`, `level`, `pivot` (the mesh of a node is found by the node's name; a node with several primitives has the loader's
 * `name_primitiveN` meshes). Returns how many meshes got the data.
 */
export async function attachBakedWind(scene: BABYLON.Scene, url: string): Promise<number> {
  const buf = await (await fetch(url)).arrayBuffer(), dv = new DataView(buf), jl = dv.getUint32(12, true);
  const gltf = JSON.parse(new TextDecoder().decode(new Uint8Array(buf, 20, jl))), binStart = 20 + jl + 8;
  const names: Record<string, [string, number]> = { _SWAY: ['sway', 1], _FLUTTER: ['flutter', 1], _PHASE: ['phase', 1], _LEVEL: ['level', 1], _PIVOT: ['pivot', 3] };
  const read = (ai: number): Float32Array => {
    const a = gltf.accessors[ai], v = gltf.bufferViews[a.bufferView], n = a.count * ({ SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4 } as Record<string, number>)[a.type], off = binStart + (v.byteOffset ?? 0) + (a.byteOffset ?? 0), out = new Float32Array(n);
    const stride = v.byteStride, comps = n / a.count;
    for (let i = 0; i < a.count; i++) for (let c = 0; c < comps; c++) out[i * comps + c] = dv.getFloat32(off + (stride ? i * stride : i * comps * 4) + c * 4, true);
    return out;
  };
  let done = 0;
  for (const node of gltf.nodes as Array<{ name: string; mesh?: number }>) {
    if (node.mesh === undefined) continue;
    const prims = gltf.meshes[node.mesh].primitives as Array<{ attributes: Record<string, number> }>;
    prims.forEach((pr, i) => {
      if (!('_SWAY' in pr.attributes)) return;
      const mesh = scene.getMeshByName(prims.length > 1 ? `${node.name}_primitive${i}` : node.name);
      if (!mesh || mesh.getTotalVertices() === 0) return;
      for (const [attr, [kind, size]] of Object.entries(names)) if (attr in pr.attributes) mesh.setVerticesData(kind, read(pr.attributes[attr]), false, size);
      done++;
    });
  }
  return done;
}
