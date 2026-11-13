// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// The three mirrors of the police cab (left door mirror, right door mirror, inner mirror) show what is behind the car: a real reflection, drawn into a small render target per mirror.
// How: the driver's eye E is reflected in the glass plane to E'; a camera at E' looking along the glass normal, with an off-axis frustum whose near plane IS the glass rectangle, sees through the glass exactly
// what E sees reflected in it (the rays E'->P are the reflected rays), nothing behind the glass is drawn (the near plane), and the picture maps linearly on the glass (its uv are planar coordinates of the glass).
// VIEW FILE: it reads the scene and never writes to the sim.
//
// Cost (the game is GPU-bound): every number that sets the price of the mirrors is in MIRROR_COST below.
import { POLICE_CAB } from './carspec';

/** the price of the mirrors, in one place */
export const MIRROR_COST = {
  /** master switch (the page's ?mirrors=0 turns it off) */
  enabled: true,
  /** each mirror redraws at most every this-many milliseconds (5 Hz) and at most one mirror is redrawn in a frame; between redraws the picture stays */
  everyMs: 200,
  /** the player's own car parts that never go into a mirror (the inside of the cab: the dash, the seats, the door cards, the underbody) */
  ownSkip: /dash|interior|underbody|doorcard|seat|steering|headliner|pedal|cluster|vent/i,
  /** the long side of the render target in pixels per kind of mirror (the short side follows the glass's shape) */
  size: { door: 128, inner: 128 } as Record<'door' | 'inner', number>,
  /** the shortest side of a target (pixels) */
  minSide: 48,
  /** the render target holds half-float colour (the sky and the sun are brighter than 1 and the street's tone mapping comes after) */
  halfFloat: true,
  /** multisampling of the target (1 = none) */
  samples: 1,
  /** the draw distance of the mirror (m); the sky and the big ground meshes are always in */
  range: 70,
  /** a mesh smaller than this fraction of its distance (radius / distance) is not drawn in the mirror (about a pixel of a 256 target) */
  minAngle: 0.012,
  /** a mesh bigger than this radius (m) is kept at any distance (ground, sky) */
  alwaysRadius: 120,
  /** the most meshes one mirror draws (the biggest in the picture by angular size stay) */
  maxMeshes: 60,
  /** the pool of candidate meshes near the car is rebuilt every this-many frames */
  poolEvery: 40,
  /** the mirror is redrawn only if its centre is inside this cone around the view direction (radians; the camera's half-diagonal with a margin) */
  viewCone: 1.05,
  /** the horizontal tint of the glass (a little darker and blue-grey, like a real mirror) */
  tint: [0.88, 0.92, 0.96] as [number, number, number],
  /** the mirror picture is linear scene light and the glass goes through the scene's tone mapping once more: the factor that makes the mirror as bright as the same things seen directly (measured: 1.0 is white, 0.15 matches the street) */
  exposure: 0.16,
  /** particles and sprites in the mirror */
  particles: false,
};

type V3 = [number, number, number];
const cross = (a: V3, b: V3): V3 => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const dot = (a: V3, b: V3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const norm = (a: V3): V3 => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };

interface Mirror {
  id: string; mesh: BABYLON.Mesh; kind: 'door' | 'inner';
  /** in the car's frame: the centre of the glass, the normal (toward the driver), the plane's axes (across, up) and the extents of the glass along them */
  c: V3; n: V3; r: V3; u: V3; r0: number; r1: number; u0: number; u1: number;
  rtt: BABYLON.RenderTargetTexture; cam: BABYLON.FreeCamera; list: BABYLON.AbstractMesh[]; mat: BABYLON.StandardMaterial;
  /** time of the last redraw (ms) */
  last: number;
  /** the meshes whose material this mirror's target already replaces */
  done: Set<BABYLON.AbstractMesh>;
}

export class CabMirrors {
  private mirrors: Mirror[] = [];
  private own: BABYLON.TransformNode | null = null;
  /** the name of the node of the car that holds the mesh (its parent chain below the car root), the primitives of a part are named alike */
  private partName(m: BABYLON.AbstractMesh, root: BABYLON.Node): string { let n: BABYLON.Node = m, s = m.name; while (n.parent && n.parent !== root) { n = n.parent; s += '/' + n.name; } return s; }
  /** meshes whose material is replaced in the mirrors (see rebuildPool), and the plain glass that replaces it */
  private glassed = new Set<BABYLON.AbstractMesh>(); private glassMat: BABYLON.StandardMaterial | null = null;
  private score = new Map<BABYLON.AbstractMesh, number>();
  private pool: BABYLON.AbstractMesh[] = []; private poolAt = -1e9;
  private frameNo = 0;
  /** off: no redraws (the stand's A/B switch; the glass keeps its last picture) */
  on = true;
  /** the statistics for the stand: redraws done and meshes drawn in the last redraw of each mirror */
  stats = { redraws: 0, meshes: [] as number[] };
  private skip = new Set<BABYLON.AbstractMesh>();

  constructor(private scene: BABYLON.Scene, private camera: BABYLON.Camera) {}

  /** the glass nodes of the player's car (the car root and the full look's nodes by name); any earlier mirrors are dropped */
  bind(carRoot: BABYLON.TransformNode, nodes: Map<string, BABYLON.TransformNode>) {
    this.release();
    if (!MIRROR_COST.enabled) return;
    this.own = carRoot;
    carRoot.computeWorldMatrix(true);
    const inv = carRoot.getWorldMatrix().clone().invert();
    for (const spec of POLICE_CAB.mirrors) {
      const g = nodes.get(spec.glass);
      if (!(g instanceof BABYLON.Mesh) || g.getTotalVertices() === 0) { console.warn('mirror glass not found', spec.glass); continue; }
      g.computeWorldMatrix(true);
      const M = g.getWorldMatrix().multiply(inv);
      const pos = g.getVerticesData(BABYLON.VertexBuffer.PositionKind)!, nor = g.getVerticesData(BABYLON.VertexBuffer.NormalKind);
      const n3 = pos.length / 3, P: V3[] = [];
      for (let i = 0; i < n3; i++) { const v = BABYLON.Vector3.TransformCoordinates(new BABYLON.Vector3(pos[3 * i]!, pos[3 * i + 1]!, pos[3 * i + 2]!), M); P.push([v.x, v.y, v.z]); }
      const c: V3 = [0, 0, 0]; for (const p of P) { c[0] += p[0] / n3; c[1] += p[1] / n3; c[2] += p[2] / n3; }
      // the plane's normal: the vertex normals through the matrix (a single flat face), else from the points
      let n: V3;
      if (nor) { const v = BABYLON.Vector3.TransformNormal(new BABYLON.Vector3(nor[0]!, nor[1]!, nor[2]!), M); n = norm([v.x, v.y, v.z]); }
      else { let best: V3 = [0, 0, 0]; for (let i = 1; i + 1 < n3; i++) { const a = cross(sub(P[i]!, P[0]!), sub(P[i + 1]!, P[0]!)); if (Math.hypot(...a) > Math.hypot(...best)) best = a; } n = norm(best); }
      // toward the driver's eye
      if (dot(n, sub(POLICE_CAB.eye, c)) < 0) n = [-n[0], -n[1], -n[2]];
      // the axes of the plane: up is the car's up taken into the plane, across follows from the left-handed camera (right = up x forward)
      let u = sub([0, 1, 0], scale(n, n[1])); u = norm(u);
      const r = norm(cross(u, n));
      let r0 = 1e9, r1 = -1e9, u0 = 1e9, u1 = -1e9;
      for (const p of P) { const d = sub(p, c), a = dot(d, r), b = dot(d, u); r0 = Math.min(r0, a); r1 = Math.max(r1, a); u0 = Math.min(u0, b); u1 = Math.max(u1, b); }
      // planar uv, so that the render target (which covers the glass rectangle exactly) maps without a shader
      const uv = new Float32Array(n3 * 2);
      for (let i = 0; i < n3; i++) { const d = sub(P[i]!, c); uv[2 * i] = (dot(d, r) - r0) / (r1 - r0); uv[2 * i + 1] = (dot(d, u) - u0) / (u1 - u0); }
      g.makeGeometryUnique();
      g.setVerticesData(BABYLON.VertexBuffer.UVKind, uv, false);
      // the target: the long side by the kind of mirror, the short side by the glass's shape
      const w = r1 - r0, h = u1 - u0, long = MIRROR_COST.size[spec.kind];
      const tw = Math.max(MIRROR_COST.minSide, Math.round(w >= h ? long : long * w / h)), th = Math.max(MIRROR_COST.minSide, Math.round(w >= h ? long * h / w : long));
      const engine = this.scene.getEngine();
      const half = MIRROR_COST.halfFloat && engine.getCaps().textureHalfFloatRender;
      const rtt = new BABYLON.RenderTargetTexture('mirror:' + spec.id, { width: tw, height: th }, this.scene, { generateMipMaps: false, generateDepthBuffer: true, type: half ? BABYLON.Constants.TEXTURETYPE_HALF_FLOAT : BABYLON.Constants.TEXTURETYPE_UNSIGNED_BYTE, samples: MIRROR_COST.samples, samplingMode: BABYLON.Texture.BILINEAR_SAMPLINGMODE });
      rtt.wrapU = rtt.wrapV = BABYLON.Texture.CLAMP_ADDRESSMODE;
      // never 'render once' (refresh rate 0): that makes the engine ask every mesh for its hardware-instanced shader variant, which flips each submesh between two variants against the main pass (measured: 3700 effect changes a frame, +300 ms a frame). A huge rate renders only when update() resets the counter.
      rtt.refreshRate = 1e9;
      rtt.renderParticles = MIRROR_COST.particles; rtt.renderSprites = false;
      rtt.ignoreCameraViewport = true;
      rtt.clearColor = new BABYLON.Color4(0.5, 0.6, 0.75, 1);
      const cam = new BABYLON.FreeCamera('mirror-cam:' + spec.id, BABYLON.Vector3.Zero(), this.scene, false);
      cam.rotationQuaternion = BABYLON.Quaternion.Identity();
      cam.minZ = 0.05; cam.maxZ = MIRROR_COST.range * 4;
      rtt.activeCamera = cam;
      // StandardMaterial does not list an emissive texture among its render targets, so the scene is told to run this one (it renders only when its refresh counter is reset, see redraw)
      this.scene.customRenderTargets.push(rtt);
      // readiness as the plain draw asks it (the instanced variants of the street's materials are not compiled for meshes drawn singly; a mesh found not ready resets the counter, which is a redraw every frame)
      rtt.customIsReadyFunction = (mesh) => mesh.isReady(false);
      const list: BABYLON.AbstractMesh[] = []; rtt.renderList = list;
      const mat = new BABYLON.StandardMaterial('mirror-glass:' + spec.id, this.scene);
      mat.disableLighting = true; mat.diffuseColor = BABYLON.Color3.Black(); mat.specularColor = BABYLON.Color3.Black();
      mat.emissiveColor = new BABYLON.Color3(MIRROR_COST.tint[0] * MIRROR_COST.exposure, MIRROR_COST.tint[1] * MIRROR_COST.exposure, MIRROR_COST.tint[2] * MIRROR_COST.exposure); mat.emissiveTexture = rtt; mat.backFaceCulling = false; mat.fogEnabled = false;
      mat.maxSimultaneousLights = 0;
      g.material = mat; g.receiveShadows = false; g.alwaysSelectAsActiveMesh = false;
      this.mirrors.push({ id: spec.id, mesh: g, kind: spec.kind, c, n, r, u, r0, r1, u0, u1, rtt, cam, list, mat, last: -1e9, done: new Set() });
    }
    this.stats.meshes = this.mirrors.map(() => 0);
  }
  release() {
    for (const m of this.mirrors) { m.rtt.dispose(); m.cam.dispose(); m.mat.dispose(); }
    this.mirrors = []; this.pool = []; this.poolAt = -1e9;
  }
  get count() { return this.mirrors.length; }
  /** meshes that never go into a mirror (the glass itself) */
  exclude(m: BABYLON.AbstractMesh) { this.skip.add(m); }

  /**
   * One frame, after the camera is placed: redraw the mirror whose turn it is if it is inside the view and faces the eye.
   * `root` is the player's car root (position and rotation of the sim), `active` false for set cameras and verdicts.
   */
  update(root: BABYLON.TransformNode, active: boolean) {
    const f = this.frameNo++;
    if (!this.on || !active || !this.mirrors.length) return;
    const cam = this.camera, E = cam.position, q = root.rotationQuaternion!;
    // the camera's forward in the world
    const fwd = BABYLON.Vector3.TransformNormal(BABYLON.Vector3.Forward(), cam.getWorldMatrix());
    // the mirror that has waited longest and is due
    const now = performance.now();
    let pick = -1, oldest = now - MIRROR_COST.everyMs;
    for (let i = 0; i < this.mirrors.length; i++) { const t = this.mirrors[i]!.last; if (t <= oldest) { oldest = t; pick = i; } }
    if (pick >= 0) { this.mirrors[pick]!.last = now; this.redraw(this.mirrors[pick]!, pick, root, q, E, fwd, f); }
  }
  private rot(q: BABYLON.Quaternion, v: V3): V3 { const o = new BABYLON.Vector3(); BABYLON.Vector3.FromArray(v).rotateByQuaternionToRef(q, o); return [o.x, o.y, o.z]; }
  private redraw(m: Mirror, idx: number, root: BABYLON.TransformNode, q: BABYLON.Quaternion, E: BABYLON.Vector3, fwd: BABYLON.Vector3, f: number) {
    if (!m.mesh.isEnabled()) return;
    const cw = this.rot(q, m.c), C: V3 = [root.position.x + cw[0], root.position.y + cw[1], root.position.z + cw[2]];
    const n = this.rot(q, m.n), r = this.rot(q, m.r), u = this.rot(q, m.u);
    const toM: V3 = [C[0] - E.x, C[1] - E.y, C[2] - E.z], dist = Math.hypot(...toM);
    // the mirror must face the eye and lie inside the view
    const h = -dot(toM, n); if (h < 0.03) return;
    if (dot(toM, [fwd.x, fwd.y, fwd.z]) < Math.cos(MIRROR_COST.viewCone) * dist) return;
    // the reflected eye lies a distance h behind the glass; the camera looks along n from there
    const Er: V3 = [E.x - 2 * h * n[0], E.y - 2 * h * n[1], E.z - 2 * h * n[2]];   // E' = E - 2 h n   (h = distance from E to the plane, n toward E)
    // the eye's foot on the plane in the plane's coordinates (relative to the glass centre)
    const d: V3 = [Er[0] - C[0], Er[1] - C[1], Er[2] - C[2]], ae = dot(d, r), be = dot(d, u);
    const cam = m.cam;
    cam.position.set(Er[0], Er[1], Er[2]);
    lookQuat(new BABYLON.Vector3(n[0], n[1], n[2]), new BABYLON.Vector3(u[0], u[1], u[2]), cam.rotationQuaternion!);
    // the off-axis frustum: the near plane is the glass plane (h away), its rectangle the glass's
    const near = h, far = MIRROR_COST.range * 3;
    const P = offCenterLH(m.r0 - ae, m.r1 - ae, m.u0 - be, m.u1 - be, near, far, this.scene.getEngine().isNDCHalfZRange);
    cam.minZ = near; cam.maxZ = far;
    cam.unfreezeProjectionMatrix(); cam.freezeProjectionMatrix(P);
    // the frustum planes of this mirror's picture
    cam.getViewMatrix(true);
    const VP = cam.getViewMatrix().multiply(P);
    const planes = BABYLON.Frustum.GetPlanes(VP);
    this.fill(m, root, planes, Er, f);
    m.rtt.resetRefreshCounter();
    this.stats.redraws++; this.stats.meshes[idx] = m.list.length;
  }
  /** the candidates near the car (rebuilt every poolEvery frames): everything enabled with geometry, apart from the glass and tiny things */
  private rebuildPool(root: BABYLON.TransformNode, f: number) {
    if (f - this.poolAt < MIRROR_COST.poolEvery) return;
    this.poolAt = f;
    const own = this.own, p = root.position, R = MIRROR_COST.range + 30, big = MIRROR_COST.alwaysRadius, out = this.pool; out.length = 0;
    for (const m of this.scene.meshes) {
      if (this.skip.has(m) || !m.isEnabled() || !m.isVisible) continue;
      if (own && m.isDescendantOf(own) && MIRROR_COST.ownSkip.test(own === m.parent ? m.name : this.partName(m, own))) continue;
      const src = (m as BABYLON.InstancedMesh).sourceMesh ?? m;
      if (src.getTotalVertices() === 0) continue;
      if (/^(Mirror_|mirror)|^(vfx|particle|fx)/i.test(m.name)) continue;
      m.computeWorldMatrix();
      const bs = m.getBoundingInfo().boundingSphere, c = bs.centerWorld, rad = bs.radiusWorld;
      if (c.y < -5000) continue;   // the sources of instanced meshes are kept far under the ground
      if (rad < big) { const dx = c.x - p.x, dz = c.z - p.z; if (dx * dx + dz * dz > (R + rad) * (R + rad)) continue; }
      // a transmissive (refracting) material makes the engine draw the whole opaque list once more into its own texture in every pass that has it: the glass is drawn with the plain dark one instead
      const mm = m.material as unknown as { subSurface?: { isRefractionEnabled?: boolean } } | null;
      if (mm?.subSurface?.isRefractionEnabled) this.glassed.add(m);
      out.push(m);
    }
  }
  private fill(m: Mirror, root: BABYLON.TransformNode, planes: BABYLON.Plane[], Er: V3, f: number) {
    this.rebuildPool(root, f);
    const list = m.list; list.length = 0;
    if (this.glassed.size) {
      if (!this.glassMat) { const g = this.glassMat = new BABYLON.StandardMaterial('mirror-window', this.scene); g.disableLighting = true; g.diffuseColor = BABYLON.Color3.Black(); g.specularColor = BABYLON.Color3.Black(); g.emissiveColor = new BABYLON.Color3(0.012, 0.016, 0.02); g.alpha = 0.55; g.backFaceCulling = true; g.fogEnabled = false; }
      for (const gm of this.glassed) if (!m.done.has(gm)) { m.rtt.setMaterialForRendering(gm, this.glassMat); m.done.add(gm); }
    }
    const big = MIRROR_COST.alwaysRadius, ang = MIRROR_COST.minAngle, range = MIRROR_COST.range;
    for (const mesh of this.pool) {
      if (!mesh.isEnabled()) continue;
      const bs = mesh.getBoundingInfo().boundingSphere, c = bs.centerWorld, rad = bs.radiusWorld;
      if (rad < big) {
        const dx = c.x - Er[0], dy = c.y - Er[1], dz = c.z - Er[2], d = Math.sqrt(dx * dx + dy * dy + dz * dz);
        if (d - rad > range || rad < d * ang) continue;
      }
      let inside = true;
      for (let k = 0; k < 6; k++) { const pl = planes[k]!; if (pl.normal.x * c.x + pl.normal.y * c.y + pl.normal.z * c.z + pl.d < -rad) { inside = false; break; } }
      if (inside) { list.push(mesh); this.score.set(mesh, rad >= big ? 1e9 : rad / Math.max(1, Math.hypot(c.x - Er[0], c.y - Er[1], c.z - Er[2]))); }
    }
    // the budget: the meshes that cover most of the picture (the angular size) stay, the rest is dropped
    if (list.length > MIRROR_COST.maxMeshes) { list.sort((a, b) => this.score.get(b)! - this.score.get(a)!); list.length = MIRROR_COST.maxMeshes; }
  }
}

const sub = (a: V3, b: V3): V3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const scale = (a: V3, s: number): V3 => [a[0] * s, a[1] * s, a[2] * s];
/** the orientation of a left-handed camera looking along `forward` with `up` (as view.ts's lookQuat), into `out` */
function lookQuat(forward: BABYLON.Vector3, up: BABYLON.Vector3, out: BABYLON.Quaternion) {
  const z = forward.normalize(), x = BABYLON.Vector3.Cross(up, z).normalize(), y = BABYLON.Vector3.Cross(z, x);
  const m = new BABYLON.Matrix(); BABYLON.Matrix.FromXYZAxesToRef(x, y, z, m);
  BABYLON.Quaternion.FromRotationMatrixToRef(m, out);
}

/** a left-handed perspective projection through the rectangle [l, r] x [b, t] on the plane z = n (the engine has none off-centre) */
function offCenterLH(l: number, r: number, b: number, t: number, n: number, f: number, half: boolean): BABYLON.Matrix {
  const m10 = half ? f / (f - n) : (f + n) / (f - n), m14 = half ? -n * f / (f - n) : -2 * f * n / (f - n);
  return BABYLON.Matrix.FromValues(2 * n / (r - l), 0, 0, 0, 0, 2 * n / (t - b), 0, 0, -(r + l) / (r - l), -(t + b) / (t - b), m10, 1, 0, 0, m14, 0);
}

/** the stand's hook: the numbers can be changed on the running page */
(globalThis as unknown as { MIRROR_COST: typeof MIRROR_COST }).MIRROR_COST = MIRROR_COST;
