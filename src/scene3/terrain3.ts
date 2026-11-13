// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import { fieldColour, LATTICE, fieldBand } from './fields3';
import { FIELD, SITE } from './config';
import { forestAmount, lakesLocal } from './height3';
import { groundHeight as zGround } from '@zeppelin/height';
import { PAVED, HANGARS, FUEL, NISSEN, TOWER, PARKED, ROAD, rect, type Rect } from './layout3';

/**
 * The ground's picture: `TerrainView` bakes the colour of each ground layer into the vertices, and this shader adds, from the asset library's ground textures (grass, soil, rock, gravel), the near
 * detail at three scales, and from two maps seen from above: the FIELD MAP (the crop and colour of each field of the patchwork over the near 10 km, with the dark line of the hedges on the borders)
 * and the WEAR MAP of the airfield (bare earth and mud where the taxiways, the aprons and the lanes wear the grass, tyre ruts, puddles that mirror the sky, oil, the paler and darker swathes of a mown field).
 * Library textures are used by their relative brightness (their hue is green and the land here is its own colour).
 */
const VERT = `
precision highp float;
attribute vec3 position; attribute vec3 normal; attribute vec4 color; attribute float morph; attribute float shadow;
uniform mat4 world; uniform mat4 worldViewProjection; uniform vec3 cameraPosition; uniform vec2 morphRange;
varying vec3 vN; varying vec4 vC; varying float vDist; varying vec3 vW; varying float vS;
void main() {
  vec4 w = world * vec4(position, 1.0);
  float d = distance(cameraPosition.xz, w.xz);
  float k = smoothstep(morphRange.x, morphRange.y, d);
  vec3 p = position; p.y += morph * k;
  w = world * vec4(p, 1.0);
  vS = shadow; vN = normal; vC = color; vDist = distance(cameraPosition, w.xyz); vW = w.xyz;
  gl_Position = worldViewProjection * vec4(p, 1.0);
}`;

const FRAG = `
precision highp float;
varying vec3 vN; varying vec4 vC; varying float vDist; varying vec3 vW; varying float vS;
uniform vec3 sunDir; uniform vec3 sunColor; uniform vec3 ambient; uniform vec3 hazeColor; uniform float hazeDensity; uniform float exposure; uniform vec3 cameraPosition; uniform vec3 skyColor;
uniform sampler2D grassTex; uniform sampler2D soilTex; uniform sampler2D rockTex; uniform sampler2D gravelTex; uniform sampler2D fieldTex; uniform sampler2D wearTex;
uniform vec4 fieldBox; uniform vec4 farBox; uniform sampler2D farTex; uniform vec4 wearBox; uniform vec3 lat;
float h21(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vn(vec2 p) { vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f); return mix(mix(h21(i), h21(i + vec2(1, 0)), f.x), mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), f.x), f.y); }
float lum(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }
float rel(sampler2D t, vec2 uv) { return lum(texture2D(t, uv).rgb) / max(lum(texture2D(t, uv, 9.0).rgb), 0.02); }
vec3 aces(vec3 x) { return clamp((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0); }
void main() {
  vec3 n = normalize(vN);
  float near = 1.0 - smoothstep(40.0, 700.0, vDist), mid = 1.0 - smoothstep(100.0, 2600.0, vDist);
  vec2 p = vW.xz;
  float g1 = rel(grassTex, p * 0.43), g2 = rel(grassTex, p * 0.051 + 3.1), g3 = rel(grassTex, p * 2.1 + 1.7);
  float s1 = rel(soilTex, p * 0.57 + 7.7), s2 = rel(soilTex, p * 0.063), q1 = rel(gravelTex, p * 0.9);
  float r1 = 0.5 * (rel(rockTex, vW.xy * 0.33) + rel(rockTex, vW.zy * 0.33));
  float slopeK = smoothstep(0.9, 0.62, n.y);
  vec3 base = pow(vC.rgb, vec3(2.2));
  float kind = 0.1; float hedge = 0.0;
  // the fields of the patchwork (the map's alpha is the crop kind; its blue-noise is the crop's own colour)
  vec2 fu = (vW.xz - fieldBox.xy) * fieldBox.zw, fv = (vW.xz - farBox.xy) * farBox.zw;
  bool inNear = fu.x > 0.0 && fu.x < 1.0 && fu.y > 0.0 && fu.y < 1.0, inFar = fv.x > 0.0 && fv.x < 1.0 && fv.y > 0.0 && fv.y < 1.0;
  if (inNear || inFar) {
    vec4 fm = inNear ? texture2D(fieldTex, fu) : texture2D(farTex, fv);
    if (fm.a > 0.02) {
      vec3 fc = pow(fm.rgb, vec3(2.2)); kind = fm.a; base = mix(base, fc, 0.9 * fm.a / max(fm.a, 0.001)); }
  }
  // rows and furrows of the crop, running along the lattice's axis, fading with distance
  vec2 lp = vec2(vW.x * lat.x + vW.z * lat.y, -vW.x * lat.y + vW.z * lat.x);
  float rowsK = smoothstep(260.0, 30.0, vDist);
  float cereal = smoothstep(0.2, 0.3, kind) * (1.0 - smoothstep(0.35, 0.45, kind));
  float plough = smoothstep(0.62, 0.7, kind) * (1.0 - smoothstep(0.78, 0.86, kind));
  float stub = smoothstep(0.45, 0.5, kind) * (1.0 - smoothstep(0.55, 0.62, kind));
  float rows = 0.5 + 0.5 * sin(lp.y * 6.2832 / 0.75 + vn(lp * 0.05) * 3.0);
  float tram = smoothstep(0.96, 1.0, 0.5 + 0.5 * sin(lp.y * 6.2832 / 24.0));
  base *= 1.0 + rowsK * (cereal * (0.28 * (rows - 0.5) - 0.18 * tram) + plough * 0.55 * (rows - 0.5) + stub * 0.2 * (rows - 0.5));
  float soilK = clamp(plough + stub * 0.35, 0.0, 1.0);
  float d1 = mix(g1, s1, soilK), d2 = mix(g2, s2, soilK);
  float detail = mix(d1 * 0.55 + d2 * 0.3 + g3 * 0.15 * near, r1 * 0.6 + 0.4, slopeK);
  float hue = vn(vW.xz * 0.0021 + 11.0), hue2 = vn(vW.xz * 0.011 + 5.0);
  base *= mix(vec3(1.06, 1.0, 0.86), vec3(0.9, 1.0, 0.9), smoothstep(0.35, 0.7, hue)) * (0.84 + 0.32 * hue2);
  float g = (vn(vW.xz * 1.7) * 0.5 + vn(vW.xz * 6.1) * 0.35 + vn(vW.xz * 23.0) * 0.15) - 0.5;
  base *= mix(1.0, detail, 0.85 * near) * (1.0 + g * 0.4 * near);
  // chalk and flint where the plough rides a slope; bare slopes of the hills
  base = mix(base, base * vec3(1.25, 1.18, 1.0), slopeK * 0.25);
  // the airfield: mown grass with its swathes, and the wear on it
  vec2 wu = (vW.xz - wearBox.xy) * wearBox.zw;
  float wet = 0.0;
  if (wu.x > 0.0 && wu.x < 1.0 && wu.y > 0.0 && wu.y < 1.0) {
    vec4 wm = texture2D(wearTex, wu);
    float field = wm.a;                                   // 1 inside the airfield's mown part
    float swath = 0.5 + 0.5 * sin(vW.x * 6.2832 / 11.0 + vn(vec2(vW.z * 0.01, 2.0)) * 2.0); swath = mix(0.5, swath, smoothstep(220.0, 20.0, vDist));
    vec3 mown = pow(vec3(0.33, 0.47, 0.18), vec3(2.2)) * (0.8 + 0.4 * (g1 * 0.5 + g2 * 0.5)) * (0.93 + 0.14 * swath) * (0.88 + 0.24 * vn(vW.xz * 0.03));
    float dry = smoothstep(0.55, 0.8, vn(vW.xz * 0.013 + 3.0) * 0.6 + vn(vW.xz * 0.06) * 0.4);
    mown = mix(mown, pow(vec3(0.5, 0.46, 0.2), vec3(2.2)) * (0.8 + 0.4 * g1), dry * 0.55);
    base = mix(base, mown, field);
    vec3 earth = pow(vec3(0.38, 0.30, 0.20), vec3(2.2)) * (0.7 + 0.5 * mix(s1, q1, 0.5)) * (0.75 + 0.5 * g);
    vec3 mud = pow(vec3(0.20, 0.15, 0.10), vec3(2.2)) * (0.8 + 0.4 * s1);
    base = mix(base, earth, wm.r * 0.95);
    base = mix(base, mud, wm.g * 0.9);
    wet = smoothstep(0.85, 0.98, wm.g);
    base *= 1.0 - 0.3 * wm.b;                          // oil, rubber, wheel marks
  }
  float lit = max(dot(n, normalize(sunDir)), 0.0) * (1.0 - vS);
  vec3 col = base * (ambient * (0.55 + 0.45 * n.y) + sunColor * lit);
  // puddles and wet mud mirror the sky
  vec3 V = normalize(cameraPosition - vW);
  float fres = 0.04 + 0.96 * pow(1.0 - clamp(V.y, 0.0, 1.0), 5.0);
  col = mix(col, col * 0.45 + skyColor * 0.38, wet * (0.4 + 0.4 * fres) * step(0.62, n.y));
  float f = 1.0 - exp(-hazeDensity * vDist);
  col = mix(col, hazeColor, clamp(f, 0.0, 1.0));
  gl_FragColor = vec4(pow(aces(col * exposure), vec3(1.0 / 2.2)), 1.0);
}`;

export interface TerrainTextures { grass: BABYLON.BaseTexture; soil: BABYLON.BaseTexture; rock: BABYLON.BaseTexture; gravel: BABYLON.BaseTexture }

const hash = (x: number, y: number, s: number) => { let h = (Math.imul(x, 374761393) + Math.imul(y, 668265263) + Math.imul(s, 2147483647)) | 0; h = Math.imul(h ^ (h >>> 13), 1274126177); return ((h ^ (h >>> 16)) >>> 0) / 4294967296; };
const vnoise = (x: number, y: number, s: number) => { const ix = Math.floor(x), iy = Math.floor(y), fx = x - ix, fy = y - iy, ux = fx * fx * (3 - 2 * fx), uy = fy * fy * (3 - 2 * fy); return (hash(ix, iy, s) * (1 - ux) + hash(ix + 1, iy, s) * ux) * (1 - uy) + (hash(ix, iy + 1, s) * (1 - ux) + hash(ix + 1, iy + 1, s) * ux) * uy; };

/** the map of the fields: the crop's colour in rgb, the kind in alpha (0 where the airfield's own ground is), the dark line of the hedges on the borders; 7.8 m a pixel */
export const FIELD_BOX = { x0: -12000, z0: -12000, w: 24000, h: 24000 };
export const FAR_BOX = { x0: -45000, z0: -55000, w: 120000, h: 110000 };
export function fieldMapTexture(scene: BABYLON.Scene, box = FIELD_BOX, N = 3072): BABYLON.RawTexture {
  const lakes = lakesLocal(), mask = new Map<number, number>();
  const data = new Uint8Array(N * N * 4), step = box.w / N;
  for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) {
    const x = box.x0 + (i + 0.5) * step, z = box.z0 + (j + 0.5) * step, o = (j * N + i) * 4;
    const bx = i >> 4, bz = j >> 4; let m = mask.get(bz * 4096 + bx);
    if (m === undefined) { const cx = box.x0 + (bx * 16 + 8) * step, cz = box.z0 + (bz * 16 + 8) * step; m = zGround(cx + SITE.x, cz + SITE.z) > 700 || (cx > 20000 && zGround(cx + SITE.x, cz + SITE.z) < 14) || lakes.some(l => Math.hypot(cx - l.x, cz - l.z) < l.r * 1.5) ? 1 : forestAmount(cx, cz) > 0.5 ? 2 : 0; mask.set(bz * 4096 + bx, m); }
    if (fieldBand(x, z) < 12) { data[o + 3] = 0; continue; }
    if (m === 2) { const w = 0.85 + 0.3 * vnoise(x / 40, z / 40, 5); data[o] = Math.round(255 * 0.13 * w); data[o + 1] = Math.round(255 * 0.26 * w); data[o + 2] = Math.round(255 * 0.12 * w); data[o + 3] = 14; continue; }
    if (m) { data[o + 3] = 0; continue; }
    const f = fieldColour(x, z), b = f.border, edge = b < 5 ? 1 - Math.max(0, b - 1.5) / 3.5 : 0;
    const hedgeLine = edge * 0.4;
    data[o] = Math.round(255 * (f.rgb[0] * (1 - hedgeLine) + 0.09 * hedgeLine)); data[o + 1] = Math.round(255 * (f.rgb[1] * (1 - hedgeLine) + 0.2 * hedgeLine)); data[o + 2] = Math.round(255 * (f.rgb[2] * (1 - hedgeLine) + 0.07 * hedgeLine));
    data[o + 3] = Math.round(255 * f.kind);
  }
  const t = BABYLON.RawTexture.CreateRGBATexture(data, N, N, scene, true, false, BABYLON.Constants.TEXTURE_TRILINEAR_SAMPLINGMODE);
  t.wrapU = t.wrapV = BABYLON.Constants.TEXTURE_CLAMP_ADDRESSMODE; t.anisotropicFilteringLevel = 8; return t;
}

/** the wear map of the airfield: r bare earth, g mud and puddles, b oil, rubber and ruts, a = the mown part (0 outside the fence); 0.65 m a pixel */
export const WEAR_BOX = { x0: -300, z0: -700, w: 680, h: 1400 };
export function wearTexture(scene: BABYLON.Scene): BABYLON.RawTexture {
  const W = 1024, H = 2048, data = new Uint8Array(W * H * 4), sx = WEAR_BOX.w / W, sz = WEAR_BOX.h / H;
  const wx = (i: number) => WEAR_BOX.x0 + (i + 0.5) * sx, wz = (j: number) => WEAR_BOX.z0 + (j + 0.5) * sz;
  const soft = (a: number, b: number, v: number) => { const t = Math.min(1, Math.max(0, (v - a) / (b - a))); return t * t * (3 - 2 * t); };
  // distance from a rect
  const dRect = (r: Rect, x: number, z: number) => Math.hypot(Math.max(r.x0 - x, 0, x - r.x1), Math.max(r.z0 - z, 0, z - r.z1));
  const paved = [PAVED.runway, PAVED.taxi, PAVED.dispersal, PAVED.apron, ...PAVED.links];
  const pad = (c: { cx: number; cz: number; w: number; d: number }) => rect(c.cx, c.cz, c.w, c.d);
  const built: Rect[] = [...HANGARS.map(h => rect(h.cx, h.cz, h.depth + 6, h.span + 4)), rect(TOWER.cx, TOWER.cz, 14, 16), pad({ cx: FUEL.cx, cz: FUEL.cz, w: FUEL.w, d: FUEL.d }), ...NISSEN.map(n => rect(n.cx, n.cz, n.yaw === 0 ? 8 : n.len + 2, n.yaw === 0 ? n.len + 2 : 8))];
  for (let j = 0; j < H; j++) for (let i = 0; i < W; i++) {
    const x = wx(i), z = wz(j), o = (j * W + i) * 4;
    const band = fieldBand(x, z);
    let earth = 0, mud = 0, oil = 0, puddle = 0;
    // field is 1 inside the fence's line and fades into the long grass outside
    const field = 1 - soft(-24, 4, band);
    let dp = 1e9; for (const r of paved) dp = Math.min(dp, dRect(r, x, z));
    const n1 = vnoise(x * 0.35, z * 0.35, 5), n2 = vnoise(x * 0.09, z * 0.09, 6), n3 = vnoise(x * 1.4, z * 1.4, 7);
    // the edge of every pavement is worn: bare earth in a rough band, mud on its low side
    earth = Math.max(earth, (1 - soft(0.2, 2.6 + 3.5 * n2, dp)) * soft(0.1, 0.4, dp + 0.2) * 0.95);
    mud = Math.max(mud, (1 - soft(0.3, 1.1 + 2.2 * n2, dp)) * (0.2 + 0.8 * soft(0.45, 0.75, n1)));
    // ruts: two wheel lines in the grass where the taxiway links and the lane to the hangars are crossed by vehicles
    for (const k of PAVED.links) { const dz = Math.abs(z - (k.z0 + k.z1) / 2); if (x > k.x1 - 2 && x < k.x1 + 14 && dz < 7) { const f = soft(7, 2, dz) * soft(14, 6, x - k.x1); earth = Math.max(earth, f * 0.9); mud = Math.max(mud, f * 0.55 * soft(0.4, 0.7, n1)); } }
    // the grass before and around the buildings is trodden bare
    for (const r of built) { const d = dRect(r, x, z); earth = Math.max(earth, (1 - soft(0.5, 9 + 6 * n2, d)) * 0.9); mud = Math.max(mud, (1 - soft(0.5, 3.5 + 3 * n2, d)) * soft(0.5, 0.8, n1) * 0.8); }
    // the service road: a worn lane on the grass
    for (let k = 0; k + 1 < ROAD.length; k++) {
      const [ax, az] = ROAD[k], [bx, bz] = ROAD[k + 1], dx = bx - ax, dz = bz - az, l2 = dx * dx + dz * dz, u = Math.min(1, Math.max(0, ((x - ax) * dx + (z - az) * dz) / l2)), d = Math.hypot(x - ax - dx * u, z - az - dz * u);
      if (d < 7) { earth = Math.max(earth, (1 - soft(2.4, 5.5 + 2.4 * n2, d)) * 0.95); const rut = Math.abs(((d - 1.1) % 2.2 + 2.2) % 2.2 - 1.1); mud = Math.max(mud, (1 - soft(0.0, 0.6, Math.abs(d - 1.5))) * 0.7 * soft(0.3, 0.6, n1)); oil = Math.max(oil, 0.3 * (1 - soft(0.0, 0.5, rut)) * (d < 3 ? 1 : 0)); }
    }
    // standing places of the aircraft: oil and rubber under each, a stain on the dispersal
    for (const a of PARKED) { const d = Math.hypot(x - a.x, z - a.z); if (d < 3.5) oil = Math.max(oil, 0.55 * (1 - soft(0.5, 3.5, d)) * (0.5 + 0.5 * n3)); }
    // puddles in the low places of the taxiway verges and the apron's edge
    const pudN = vnoise(x * 0.045 + 3, z * 0.09 - 8, 8) * 0.7 + vnoise(x * 0.2, z * 0.2, 9) * 0.3;
    const pud = soft(0.66, 0.72, pudN) * soft(0.6, 2.0, dp) * (1 - soft(2.5, 9, dp));
    puddle = Math.max(puddle, pud);
    // outside the fence the ground is the countryside's: no wear
    earth *= field; mud *= field; oil *= field; puddle *= field;
    // inside pavements nothing shows (the meshes cover it)
    data[o] = Math.round(255 * Math.min(1, earth)); data[o + 1] = Math.round(255 * (puddle > 0.5 ? 1 : Math.min(0.6, mud))); data[o + 2] = Math.round(255 * Math.min(1, oil)); data[o + 3] = Math.round(255 * field);
  }
  const t = BABYLON.RawTexture.CreateRGBATexture(data, W, H, scene, true, false, BABYLON.Constants.TEXTURE_TRILINEAR_SAMPLINGMODE);
  t.wrapU = t.wrapV = BABYLON.Constants.TEXTURE_CLAMP_ADDRESSMODE; t.anisotropicFilteringLevel = 8; return t;
}

/** the material handed to `TerrainView.material`; the lighting is kept in step with the sky through `light()` and `haze()` by the scene */
export function terrainMaterial(scene: BABYLON.Scene, tex: TerrainTextures) {
  BABYLON.Effect.ShadersStore['take37AirfieldTerrainVertexShader'] = VERT; BABYLON.Effect.ShadersStore['take37AirfieldTerrainFragmentShader'] = FRAG;
  const m = new BABYLON.ShaderMaterial('terrain3', scene, { vertex: 'take37AirfieldTerrain', fragment: 'take37AirfieldTerrain' }, {
    attributes: ['position', 'normal', 'color', 'morph', 'shadow'],
    uniforms: ['world', 'worldViewProjection', 'cameraPosition', 'morphRange', 'sunDir', 'sunColor', 'ambient', 'hazeColor', 'hazeDensity', 'exposure', 'skyColor', 'fieldBox', 'farBox', 'wearBox', 'lat'],
    samplers: ['grassTex', 'soilTex', 'rockTex', 'gravelTex', 'fieldTex', 'farTex', 'wearTex'],
  });
  m.setTexture('grassTex', tex.grass); m.setTexture('soilTex', tex.soil); m.setTexture('rockTex', tex.rock); m.setTexture('gravelTex', tex.gravel);
  m.setTexture('fieldTex', fieldMapTexture(scene)); m.setTexture('wearTex', wearTexture(scene));
  m.setTexture('farTex', fieldMapTexture(scene, FAR_BOX, 2048)); m.setVector4('farBox', new BABYLON.Vector4(FAR_BOX.x0, FAR_BOX.z0, 1 / FAR_BOX.w, 1 / FAR_BOX.h));
  m.setVector4('fieldBox', new BABYLON.Vector4(FIELD_BOX.x0, FIELD_BOX.z0, 1 / FIELD_BOX.w, 1 / FIELD_BOX.h));
  m.setVector4('wearBox', new BABYLON.Vector4(WEAR_BOX.x0, WEAR_BOX.z0, 1 / WEAR_BOX.w, 1 / WEAR_BOX.h));
  m.setVector3('lat', new BABYLON.Vector3(Math.cos(LATTICE.angle), Math.sin(LATTICE.angle), 0));
  m.setVector3('skyColor', new BABYLON.Vector3(0.6, 0.7, 0.9)); m.setFloat('exposure', 0.85);
  m.backFaceCulling = false; m.zOffset = 3; m.zOffsetUnits = 3;
  m.onBindObservable.add((mesh) => { const r = (mesh.metadata as { morphRange?: [number, number] } | null)?.morphRange; if (r) m.getEffect()?.setFloat2('morphRange', r[0], r[1]); });
  return m;
}
void FIELD; void SITE;
