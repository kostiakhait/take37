// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
/**
 * The beach of scene 2 as a 1940 roadstead beach, not bare sand: what the sea leaves along the tide mark (driftwood, planks, wrack, shingle) and what holds the sand above it (marram
 * on the foredune hummocks of `shore.ts`) are made by the engine's terrain module (`@ferret/terrain`: a `Ground` over the beach's own height, biome zones, `ScatterView` with the
 * species below; the shapes of driftwood and wrack are this game's generators handed to the module); what the army left (stores dumps, drums, kit) is the Dunkirk sample's litter
 * view over this scene's layout and the library's materials; an abandoned lorry and gun are the library's models drawn by the perspective module (the sample's wrecks view); the
 * barbed wire and the tyre tracks are made here as geometry that follows the ground. Everything is thin instances or merged meshes (few draws), nothing is built far from the camera.
 */
import type { World } from '@ferret/core';
import type { AssetLibrary } from '@ferret/levels';
import { Ground, ScatterView, makeRock, type MeshData, type Species } from '@ferret/terrain';
import { WrecksView } from '@dunkirk/wrecks-view';
import { LitterView } from '@dunkirk/litter-view';
import type { Litter, LitterKind } from '@dunkirk/litter';
import type { Wreck } from '@dunkirk/wrecks';
import { MOLE, TIDE, bed, foredune, roadAt, roadDist, roadFrom } from './shore';

type V3 = [number, number, number];
type C3 = [number, number, number];
function rng(seed: number) { let a = seed | 0; return () => { a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

// ---- the ground the terrain module scatters on: the beach's own height as an imported grid, the coast biome everywhere ----------------------------------------------------------
const GRID = { x0: -340, z0: -300, step: 4, nx: 171, nz: 85 };
export function beachGround(): Ground {
  const heights: number[] = new Array(GRID.nx * GRID.nz);
  for (let j = 0; j < GRID.nz; j++) for (let i = 0; i < GRID.nx; i++) heights[j * GRID.nx + i] = bed(GRID.x0 + i * GRID.step, GRID.z0 + j * GRID.step);
  const X0 = GRID.x0 - 600, X1 = GRID.x0 + GRID.nx * GRID.step + 600, Z0 = GRID.z0 - 600, Z1 = GRID.z0 + GRID.nz * GRID.step + 600;
  return new Ground({
    spec: { seed: 1940, seaLevel: -100, relief: [{ op: 'import', origin: [GRID.x0, GRID.z0], step: GRID.step, nx: GRID.nx, ny: GRID.nz, heights, edge: 0 }] },
    climate: { fixed: { temperature: 14, moisture: 0.45 } },
    zones: [{ biome: 'coast', polygon: [[X0, Z0], [X1, Z0], [X1, Z1], [X0, Z1]], feather: 30 }],
  });
}

// ---- small mesh generators for the shapes the module does not draw (unit size, base at y = 0, own colours) ---------------------------------------------------------------------------------
class Builder {
  pos: number[] = []; nor: number[] = []; col: number[] = []; idx: number[] = [];
  /** a tapering tube from a to b */
  tube(a: V3, b: V3, r0: number, r1: number, seg: number, c0: C3, c1: C3) {
    const d: V3 = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], L = Math.hypot(...d) || 1, u: V3 = [d[0] / L, d[1] / L, d[2] / L];
    const h: V3 = Math.abs(u[1]) < 0.9 ? [0, 1, 0] : [1, 0, 0];
    let p: V3 = [u[1] * h[2] - u[2] * h[1], u[2] * h[0] - u[0] * h[2], u[0] * h[1] - u[1] * h[0]]; const pl = Math.hypot(...p); p = [p[0] / pl, p[1] / pl, p[2] / pl];
    const q: V3 = [u[1] * p[2] - u[2] * p[1], u[2] * p[0] - u[0] * p[2], u[0] * p[1] - u[1] * p[0]], base = this.pos.length / 3;
    for (let k = 0; k < 2; k++) for (let s = 0; s <= seg; s++) {
      const an = (s / seg) * Math.PI * 2, n: V3 = [p[0] * Math.cos(an) + q[0] * Math.sin(an), p[1] * Math.cos(an) + q[1] * Math.sin(an), p[2] * Math.cos(an) + q[2] * Math.sin(an)], c = k ? b : a, r = k ? r1 : r0, cc = k ? c1 : c0;
      this.pos.push(c[0] + n[0] * r, c[1] + n[1] * r, c[2] + n[2] * r); this.nor.push(n[0], n[1], n[2]); this.col.push(cc[0], cc[1], cc[2], 1);
    }
    for (let s = 0; s < seg; s++) { const i = base + s, j = i + seg + 1; this.idx.push(i, j, i + 1, i + 1, j, j + 1); }
  }
  /** a low-poly ellipsoid with a jittered surface */
  blob(c: V3, rx: number, ry: number, rz: number, seed: number, jit: number, c0: C3, c1: C3) {
    const r = rng(seed), lat = 5, lon = 9, base = this.pos.length / 3;
    for (let i = 0; i <= lat; i++) for (let j = 0; j <= lon; j++) {
      const th = (i / lat) * Math.PI, ph = (j / lon) * Math.PI * 2, k = 1 + (r() - 0.5) * jit, n: V3 = [Math.sin(th) * Math.cos(ph), Math.cos(th), Math.sin(th) * Math.sin(ph)], t = (n[1] + 1) / 2;
      this.pos.push(c[0] + n[0] * rx * k, c[1] + n[1] * ry * k, c[2] + n[2] * rz * k); this.nor.push(n[0] / rx, n[1] / ry, n[2] / rz); this.col.push(c0[0] + (c1[0] - c0[0]) * t, c0[1] + (c1[1] - c0[1]) * t, c0[2] + (c1[2] - c0[2]) * t, 1);
    }
    for (let i = 0; i < lat; i++) for (let j = 0; j < lon; j++) { const a = base + i * (lon + 1) + j, b = a + 1, c2 = a + lon + 1, d = c2 + 1; this.idx.push(a, c2, b, b, c2, d); }
  }
  /** a box (flat shaded) */
  box(c: V3, sx: number, sy: number, sz: number, col: C3, yaw = 0) {
    const faces: Array<[V3, V3, V3]> = [[[1, 0, 0], [0, 1, 0], [0, 0, 1]], [[-1, 0, 0], [0, 1, 0], [0, 0, -1]], [[0, 1, 0], [0, 0, 1], [1, 0, 0]], [[0, -1, 0], [0, 0, -1], [1, 0, 0]], [[0, 0, 1], [0, 1, 0], [-1, 0, 0]], [[0, 0, -1], [0, 1, 0], [1, 0, 0]]];
    const cy = Math.cos(yaw), sy2 = Math.sin(yaw), half: V3 = [sx / 2, sy / 2, sz / 2];
    for (const [n, u, v] of faces) {
      const base = this.pos.length / 3;
      for (const [a, b] of [[-1, -1], [1, -1], [1, 1], [-1, 1]] as Array<[number, number]>) {
        const x = (n[0] + u[0] * a + v[0] * b) * half[0], y = (n[1] + u[1] * a + v[1] * b) * half[1], z = (n[2] + u[2] * a + v[2] * b) * half[2];
        this.pos.push(c[0] + x * cy + z * sy2, c[1] + y, c[2] - x * sy2 + z * cy); this.nor.push(n[0] * cy + n[2] * sy2, n[1], -n[0] * sy2 + n[2] * cy); this.col.push(col[0], col[1], col[2], 1);
      }
      this.idx.push(base, base + 1, base + 2, base, base + 2, base + 3);
    }
  }
  done(): MeshData { return { positions: Float32Array.from(this.pos), normals: Float32Array.from(this.nor), indices: Uint32Array.from(this.idx), colors: Float32Array.from(this.col) }; }
}
const SILVER: C3 = [0.62, 0.58, 0.5], GREY: C3 = [0.44, 0.4, 0.34], DARK: C3 = [0.26, 0.22, 0.17];
/** driftwood of unit length along x: a bleached trunk with stubs, a root-ball trunk, a bough, a plank with a nail line (the module scales a piece by its size, 0.8 .. 2.4 m) */
function driftwood(seed: number, v: number): MeshData {
  const b = new Builder(), r = rng(seed * 31 + v * 7 + 1), n = 4;
  if (v === 3) { // sawn plank: two boards side by side, one a little turned
    b.box([0, 0.012, 0], 1, 0.024, 0.09, SILVER); b.box([0.12, 0.012, 0.11], 0.7, 0.024, 0.1, GREY, 0.12); return b.done();
  }
  const rad = 0.035 + 0.02 * r(), pts: V3[] = []; for (let i = 0; i <= n; i++) pts.push([-0.5 + i / n, rad * (1 - 0.2 * i / n) + 0.004, (r() - 0.5) * 0.05]);
  for (let i = 0; i < n; i++) b.tube(pts[i], pts[i + 1], rad * (1 - 0.2 * i / n), rad * (1 - 0.2 * (i + 1) / n), 7, i % 2 ? GREY : SILVER, i % 2 ? SILVER : GREY);
  if (v === 1) { // root ball
    b.blob([-0.5, 0.1, 0], 0.09, 0.1, 0.09, seed + 5, 0.45, DARK, GREY);
    for (let i = 0; i < 5; i++) { const a = (i / 5) * 6.28 + r(), l = 0.12 + 0.1 * r(); b.tube([-0.5, 0.1, 0], [-0.5 - Math.cos(a) * l, 0.1 + Math.abs(Math.sin(a)) * l, Math.sin(a) * l], 0.018, 0.005, 5, GREY, SILVER); }
  } else {
    for (let i = 0; i < 2 + (v === 2 ? 2 : 0); i++) { const p = pts[1 + Math.floor(r() * 3)], a = r() * 6.28, l = 0.1 + 0.18 * r(); b.tube(p, [p[0] + Math.cos(a) * l * 0.5, p[1] + 0.05 + Math.abs(Math.sin(a)) * l, p[2] + Math.sin(a) * l * 0.5], 0.016, 0.005, 5, GREY, SILVER); }
  }
  return b.done();
}
/** a drift of weed at the tide mark: flat dark olive blobs */
function wrack(seed: number, v: number): MeshData {
  const b = new Builder(), r = rng(seed * 17 + v * 3 + 2);
  for (let i = 0; i < 4 + v; i++) { const a = r() * 6.28, d = 0.28 * r(); b.blob([Math.cos(a) * d, 0.02, Math.sin(a) * d], 0.16 + 0.12 * r(), 0.025, 0.1 + 0.08 * r(), seed + i, 0.5, [0.16, 0.15, 0.07], [0.3 + 0.1 * r(), 0.27, 0.12]); }
  return b.done();
}
/** a shell-and-shingle patch: a few pale flat stones */
function shingle(seed: number, v: number): MeshData {
  const b = new Builder(), r = rng(seed * 13 + v + 9);
  for (let i = 0; i < 9; i++) { const a = r() * 6.28, d = 0.4 * Math.sqrt(r()), s = 0.04 + 0.05 * r(), g = 0.55 + 0.3 * r(); b.blob([Math.cos(a) * d, s * 0.2, Math.sin(a) * d], s, s * 0.35, s * (0.6 + 0.5 * r()), seed + i, 0.3, [g * 0.7, g * 0.66, g * 0.58], [g, g * 0.95, g * 0.85]); }
  return b.done();
}

/** what is scattered (densities per 100 m2 in the coast biome; the heights are above the mean sea level: the tide mark of a spring tide is 1.2 m) */
export const BEACH_SPECIES: Species[] = [
  { id: 'driftwood', shape: 'driftwood', biomes: { coast: 0.55 }, size: [0.8, 2.6], exponent: 1.6, variants: 4, height: [0.7, 1.75], slope: [0, 0.4], cluster: { wavelength: 34, lo: 0.3, hi: 0.62 }, dry: true },
  { id: 'wrack', shape: 'wrack', biomes: { coast: 1.8 }, size: [0.4, 1.1], exponent: 1.6, variants: 3, height: [0.55, 1.45], slope: [0, 0.3], cluster: { wavelength: 16, lo: 0.3, hi: 0.6 }, dry: true },
  { id: 'shingle', shape: 'shingle', biomes: { coast: 1.1 }, size: [0.5, 1.6], exponent: 1.5, variants: 3, height: [0.9, 1.9], slope: [0, 0.4], cluster: { wavelength: 22, lo: 0.35, hi: 0.65 }, dry: true },
  { id: 'pebble', shape: 'rock', biomes: { coast: 3.5 }, size: [0.05, 0.2], exponent: 2.2, buried: 0.4, variants: 5, height: [0.8, 2.1], slope: [0, 0.6], cluster: { wavelength: 12, lo: 0.3, hi: 0.6 }, dry: true },
  { id: 'dune-stone', shape: 'rock', biomes: { coast: 0.05 }, size: [0.3, 0.8], exponent: 2, buried: 0.4, variants: 4, height: [1.0, 2.4], slope: [0, 0.6], dry: true },
  { id: 'strand-tuft', shape: 'tuft', biomes: { coast: 0.5 }, size: [0.25, 0.6], exponent: 2, variants: 4, height: [1.3, 2.2], slope: [0, 0.5], cluster: { wavelength: 24, lo: 0.4, hi: 0.7 }, dry: true },
  { id: 'hummock-marram', shape: 'tuft', biomes: { coast: 16 }, size: [0.4, 1.0], exponent: 1.8, variants: 4, height: [1.6, 3.0], slope: [0, 0.95], cluster: { wavelength: 9, lo: 0.2, hi: 0.5 }, dry: true },
  { id: 'hummock-reed', shape: 'reed', biomes: { coast: 3.5 }, size: [0.7, 1.5], exponent: 2, variants: 3, height: [1.8, 3.0], slope: [0, 0.8], cluster: { wavelength: 14, lo: 0.45, hi: 0.75 }, dry: true },
  { id: 'sea-holly', shape: 'shrub', biomes: { coast: 0.35 }, size: [0.3, 0.7], exponent: 2, variants: 4, height: [1.7, 3.0], slope: [0, 0.8], cluster: { wavelength: 30, lo: 0.4, hi: 0.7 }, dry: true },
];

// ---- the layout: what the army left, as the Dunkirk sample's litter -------------------------------------------------------------------------------------------------------------------------------
const SIZE: Record<LitterKind, [number, number, number]> = { ammo: [0.18, 0.30, 0.47], case: [0.62, 0.55, 0.95], plank: [0.22, 0.04, 3.2], drum: [0.58, 0.88, 0.58], drumSide: [0.58, 0.58, 0.88], flimsy: [0.24, 0.35, 0.24], kitbag: [0.36, 0.30, 0.85], helmet: [0.33, 0.12, 0.36] };
/** the abandoned lorry and gun (library models); the lorry nose-down in soft sand above the tide mark, the gun at the foredune where its crew left it */
export const WRECKS2: Wreck[] = [
  { kind: 'truck', x: 96, z: -86, yaw: 0.95, pitch: 0.07, roll: 0.05, burnt: false, pier: false, hl: 3.3, hw: 1.2 },
  { kind: 'gun', x: -128, z: -112, yaw: 2.3, pitch: 0.02, roll: -0.04, burnt: false, pier: false, hl: 2.0, hw: 1.2 },
];
const near = (x: number, z: number, w: Wreck, pad: number) => Math.abs(x - w.x) < w.hl + pad && Math.abs(z - w.z) < w.hl + pad;
export function layoutBeachLitter(seed = 1940): Litter[] {
  const r = rng(seed), out: Litter[] = [];
  const put = (kind: LitterKind, x: number, z: number, o: { yaw?: number; level?: number; tilt?: number } = {}) => {
    if (Math.abs(x - MOLE.x) < MOLE.half + 1.5 && z > MOLE.rampFrom - 2) return;
    if (roadDist(x, z) < 2.6) return;
    if (WRECKS2.some(w => near(x, z, w, 0.4))) return;
    const g = bed(x, z), h = SIZE[kind][1] * (kind === 'drumSide' ? 1 : 1);
    out.push({ kind, x, y: g + h / 2 + (o.level ?? 0) * h - 0.03, z, yaw: o.yaw ?? r() * Math.PI * 2, tilt: o.tilt ?? (r() - 0.5) * 0.08, variant: Math.floor(r() * 3) });
  };
  // the stores dump at the mole's landward end (east side): a block of cases two high, drums, tins, ammunition boxes, a plank leaned on them
  for (let i = 0; i < 3; i++) for (let j = 0; j < 2; j++) { put('case', 13 + i * 1.05, -100 + j * 1.0, { yaw: 0.05 * (i - j) }); if (i !== 1 || j !== 0) put('case', 13 + i * 1.05, -100 + j * 1.0, { yaw: 0.1 * (j - i) + 0.1, level: 1 }); }
  for (let i = 0; i < 5; i++) put('drum', 17.5 + (i % 3) * 0.7, -97.5 + Math.floor(i / 3) * 0.9);
  for (let i = 0; i < 6; i++) put('ammo', 12.5 + r() * 5, -103.2 + r() * 1.6);
  put('plank', 15.2, -98.6, { yaw: 0.4, tilt: 0.25, level: 1.6 });
  put('flimsy', 20, -99.5); put('flimsy', 19.4, -100.2); put('kitbag', 12, -96.5, { yaw: 1.2 }); put('kitbag', 11.3, -97.4, { yaw: 0.2 });
  // a second dump on the west side: drums upright and on their sides round an open case, as a stores party left them
  for (let i = 0; i < 4; i++) put('drum', -19 - (i % 2) * 0.8, -92 + Math.floor(i / 2) * 0.9);
  for (let i = 0; i < 3; i++) put('drumSide', -22.5 + r() * 2, -94 + r() * 3, { yaw: r() * 3 });
  for (let i = 0; i < 4; i++) put('flimsy', -16 + r() * 3, -90 + r() * 3);
  put('case', -24.5, -89.5, { tilt: 0.12 }); put('case', -24.8, -91.2, { yaw: 0.9 }); put('ammo', -22, -90.4);
  // round the lorry: what was thrown off it and left
  for (const w of WRECKS2) {
    const n = w.kind === 'truck' ? 11 : 6;
    for (let i = 0; i < n; i++) { const a = r() * Math.PI * 2, d = w.hl + 0.9 + r() * 5; put(w.kind === 'gun' ? (['ammo', 'ammo', 'case', 'helmet', 'kitbag'] as LitterKind[])[Math.floor(r() * 5)] : (['case', 'ammo', 'drum', 'drumSide', 'flimsy', 'kitbag', 'plank'] as LitterKind[])[Math.floor(r() * 7)], w.x + Math.cos(a) * d, w.z + Math.sin(a) * d); }
  }
  // cases broken open at the dune foot on the east side, planks, a few helmets and kitbags along the track to the lorry
  for (let i = 0; i < 5; i++) put(i % 2 ? 'case' : 'plank', 112 + r() * 14, -118 + r() * 10, { tilt: (r() - 0.5) * 0.4 });
  for (let i = 0; i < 38; i++) { const t = r(), x = -6 + t * 100, z = -116 + t * 30 + (r() - 0.5) * 12; put((['helmet', 'kitbag', 'ammo', 'flimsy', 'helmet'] as LitterKind[])[Math.floor(r() * 5)], x, z); }
  for (let i = 0; i < 16; i++) put((['helmet', 'kitbag', 'ammo', 'plank'] as LitterKind[])[Math.floor(r() * 4)], -150 + r() * 120, -112 + r() * 14);
  // the tide mark: planks and a drum or two the sea moved about
  for (let i = 0; i < 40; i++) { const x = (r() - 0.5) * 560, z = -(70 + r() * 40) + 0; if (bed(x, z) > 0.8 && bed(x, z) < 1.7) put((['plank', 'plank', 'drumSide', 'case'] as LitterKind[])[Math.floor(r() * 4)], x, z); }
  return out;
}

// ---- barbed wire (concertina on screw pickets), as chunks of thin instances ----------------------------------------------------------------------------------------------------------------------
interface Line { pts: Array<[number, number]>; gaps: Array<[number, number]> }
/** the wire runs along the foot of the foredune: a long line west of the road, a shorter one east of the mole's landward end, broken (cut and trampled) where the assault comes along the dune foot */
function wireLines(): Line[] {
  const z = (x: number) => -141 + 5 * Math.sin(x * 0.018) - 0.4 * (8 * Math.sin(x * 0.004) + 4 * Math.sin(x * 0.011 + 1.3));
  const run = (a: number, b: number): Array<[number, number]> => { const o: Array<[number, number]> = []; for (let x = a; x <= b; x += 6) o.push([x, z(x)]); return o; };
  return [{ pts: run(-300, -34), gaps: [] }, { pts: run(-8, 128), gaps: [[20, 29]] }];
}
function buildWire(scene: BABYLON.Scene, lines: Line[]): BABYLON.Mesh[] {
  const mat = new BABYLON.PBRMaterial('wire-steel', scene); mat.albedoColor = new BABYLON.Color3(0.11, 0.1, 0.09); mat.metallic = 0.7; mat.roughness = 0.55; mat.backFaceCulling = false;
  // one bay: a concertina of 9 loops on the line and a picket at each end, 3.6 m long along x
  const parts: BABYLON.Mesh[] = [];
  for (let i = 0; i < 9; i++) { const t = BABYLON.MeshBuilder.CreateTorus('loop', { diameter: 0.84, thickness: 0.03, tessellation: 10 }, scene); t.rotation.z = Math.PI / 2; t.position.set(-1.6 + i * 0.4, 0.43, 0); parts.push(t); }
  for (let i = 0; i < 5; i++) { const t = BABYLON.MeshBuilder.CreateTorus('loop2', { diameter: 0.6, thickness: 0.026, tessellation: 8 }, scene); t.rotation.z = Math.PI / 2; t.position.set(-1.4 + i * 0.7, 0.86, 0); parts.push(t); }
  for (const x of [-1.8, 1.8]) { const c = BABYLON.MeshBuilder.CreateCylinder('picket', { diameter: 0.07, height: 1.4, tessellation: 5 }, scene); c.position.set(x, 0.62, 0); parts.push(c); }
  for (const y of [0.1, 0.8, 1.15]) { const c = BABYLON.MeshBuilder.CreateCylinder('strand', { diameter: 0.025, height: 3.6, tessellation: 3 }, scene); c.rotation.z = Math.PI / 2; c.position.set(0, y, 0); parts.push(c); }
  const bay = BABYLON.Mesh.MergeMeshes(parts, true)!; bay.name = 'wire-bay'; bay.material = mat; bay.setEnabled(false);
  const r = rng(77), CH = 80, chunks = new Map<number, number[]>(), q = new BABYLON.Quaternion(), s1 = new BABYLON.Vector3(1, 1, 1), mx = new BABYLON.Matrix();
  for (const ln of lines) {
    // bays end to end along the polyline by arc length
    const cum = [0]; for (let i = 1; i < ln.pts.length; i++) cum.push(cum[i - 1]! + Math.hypot(ln.pts[i]![0] - ln.pts[i - 1]![0], ln.pts[i]![1] - ln.pts[i - 1]![1]));
    const at = (d: number): [number, number] => { let i = 1; while (i < cum.length - 1 && cum[i]! < d) i++; const t = (d - cum[i - 1]!) / Math.max(1e-6, cum[i]! - cum[i - 1]!); return [ln.pts[i - 1]![0] + (ln.pts[i]![0] - ln.pts[i - 1]![0]) * t, ln.pts[i - 1]![1] + (ln.pts[i]![1] - ln.pts[i - 1]![1]) * t]; };
    for (let d = 0; d + 3.6 <= cum[cum.length - 1]!; d += 3.6) {
      const [x0, z0] = at(d), [x1, z1] = at(d + 3.6), x = (x0 + x1) / 2, zz = (z0 + z1) / 2, yaw = -Math.atan2(z1 - z0, x1 - x0);
      if (ln.gaps.some(([g0, g1]) => x > g0 && x < g1) || roadDist(x, zz) < 8) continue;
      const y0 = bed(x0, z0), y1 = bed(x1, z1), fallen = r() < 0.07, pitch = Math.atan2(y1 - y0, 3.6), roll = fallen ? 1.0 + 0.4 * r() : 0;
      BABYLON.Quaternion.RotationYawPitchRollToRef(yaw, 0, 0, q);
      const qp = BABYLON.Quaternion.RotationAxis(new BABYLON.Vector3(0, 0, 1), pitch), qr = BABYLON.Quaternion.RotationAxis(new BABYLON.Vector3(1, 0, 0), roll), qq = qr.multiply(qp).multiply(q);
      BABYLON.Matrix.ComposeToRef(s1, qq, new BABYLON.Vector3(x, (y0 + y1) / 2 - 0.05, zz), mx);
      const k = Math.floor((x + 400) / CH); let arr = chunks.get(k); if (!arr) chunks.set(k, arr = []); arr.push(...mx.asArray());
    }
  }
  // one merged mesh per chunk (the bay's vertices placed by each matrix): plain geometry, culled by chunk
  const out: BABYLON.Mesh[] = [], P = bay.getVerticesData(BABYLON.VertexBuffer.PositionKind)!, N = bay.getVerticesData(BABYLON.VertexBuffer.NormalKind)!, I = bay.getIndices()!, nv = P.length / 3;
  const v = new BABYLON.Vector3(), o = new BABYLON.Vector3(), m4 = new BABYLON.Matrix();
  for (const [k, arr] of chunks) {
    const n = arr.length / 16, pos = new Float32Array(n * nv * 3), nor = new Float32Array(n * nv * 3), idx = new Uint32Array(n * I.length);
    for (let i = 0; i < n; i++) {
      BABYLON.Matrix.FromArrayToRef(arr, i * 16, m4);
      for (let j = 0; j < nv; j++) {
        v.set(P[j * 3]!, P[j * 3 + 1]!, P[j * 3 + 2]!); BABYLON.Vector3.TransformCoordinatesToRef(v, m4, o); pos.set([o.x, o.y, o.z], (i * nv + j) * 3);
        v.set(N[j * 3]!, N[j * 3 + 1]!, N[j * 3 + 2]!); BABYLON.Vector3.TransformNormalToRef(v, m4, o); nor.set([o.x, o.y, o.z], (i * nv + j) * 3);
      }
      for (let j = 0; j < I.length; j++) idx[i * I.length + j] = I[j]! + i * nv;
    }
    const m = new BABYLON.Mesh('wire_c' + k, scene), vd = new BABYLON.VertexData(); vd.positions = pos; vd.normals = nor; vd.indices = idx; vd.applyToMesh(m, false);
    m.material = mat; m.isPickable = false; out.push(m);
  }
  bay.dispose();
  return out;
}

// ---- tracks pressed into the sand: tyre tracks of lorries, a trampled path ----------------------------------------------------------------------------------------------------------------------------
interface Track { pts: Array<[number, number]>; kind: 'tyre' | 'path' | 'drag' }
function trackList(): Track[] {
  const end = roadAt(roadFrom())(1);
  return [
    // the lorry came off the road's end, drove east across the beach and stopped where it stands; the second pair is its earlier trip to and from the water
    { kind: 'tyre', pts: [[end[0] + 2, end[1] + 1], [24, -112], [52, -102], [76, -94], [92, -88]] },
    { kind: 'tyre', pts: [[92, -88], [112, -66], [124, -40], [132, -20], [137, -3]] },
    { kind: 'tyre', pts: [[132, -20], [118, -44], [112, -64]] },
    // the gun's tractor came the other way, from the road to the foredune
    { kind: 'tyre', pts: [[end[0] - 3, end[1] + 1], [-46, -118], [-92, -114], [-122, -113]] },
    // many men, many boots: the path from the road's end along the high water mark to the east and a short one to the west
    { kind: 'path', pts: [[end[0] + 1, end[1] - 4], [14, -110], [36, -104], [60, -100], [86, -98], [116, -104]] },
    { kind: 'path', pts: [[end[0] - 4, end[1] - 2], [-40, -110], [-80, -112], [-112, -116]] },
    // a boat hauled up and hauled down again: one wide groove from the water's edge
    { kind: 'drag', pts: [[-44, -3], [-44, -20], [-47, -38], [-50, -56]] },
  ];
}
function buildTracks(scene: BABYLON.Scene, tracks: Track[]): BABYLON.Mesh {
  const pos: number[] = [], col: number[] = [], idx: number[] = [], nor: number[] = [], r = rng(99);
  const ribbon = (pts: Array<[number, number]>, half: number, tint: C3, alpha: number, tread: boolean, off = 0) => {
    // resample every 1.4 m, a wander of a few centimetres, the sand's height under each point
    const sm: Array<[number, number, number]> = []; let acc = 0;
    for (let i = 0; i + 1 < pts.length; i++) {
      const [ax, az] = pts[i]!, [bx, bz] = pts[i + 1]!, L = Math.hypot(bx - ax, bz - az), n = Math.max(1, Math.round(L / 1.4));
      for (let k = 0; k < n; k++) { const t = k / n; sm.push([ax + (bx - ax) * t, az + (bz - az) * t, acc + L * t]); } acc += L;
    }
    sm.push([...pts[pts.length - 1]!, acc] as [number, number, number]);
    const base = pos.length / 3, SEG = 5;
    for (let i = 0; i < sm.length; i++) {
      const a = sm[Math.max(0, i - 1)]!, b = sm[Math.min(sm.length - 1, i + 1)]!, dx = b[0] - a[0], dz = b[1] - a[1], l = Math.hypot(dx, dz) || 1, nx = -dz / l, nz = dx / l, w = (r() - 0.5) * 0.05;
      const fade = Math.min(1, sm[i]![2] / 6, (acc - sm[i]![2]) / 6);
      for (let j = 0; j < SEG; j++) {
        const f = (j / (SEG - 1)) * 2 - 1, cx = sm[i]![0] + nx * (f * half + off + w), cz = sm[i]![1] + nz * (f * half + off + w);
        pos.push(cx, bed(cx, cz) + 0.04, cz); nor.push(0, 1, 0);
        const cross = Math.pow(1 - Math.abs(f), 0.8), lug = tread ? 0.7 + 0.3 * Math.sin(sm[i]![2] * 5.2 + (j % 2) * 1.4) : 1;
        col.push(tint[0], tint[1], tint[2], alpha * cross * lug * Math.min(1, fade * 1.5 + 0.15) * (0.85 + 0.3 * r()));
      }
    }
    for (let i = 0; i + 1 < sm.length; i++) for (let j = 0; j < SEG - 1; j++) { const a = base + i * SEG + j, b = a + 1, c = a + SEG, d = c + 1; idx.push(a, b, c, b, d, c); }
  };
  for (const t of tracks) {
    if (t.kind === 'tyre') for (const s of [-0.9, 0.9]) ribbon(t.pts, 0.15, [0.23, 0.17, 0.11], 0.62, true, s);
    else if (t.kind === 'path') ribbon(t.pts, 0.75, [0.3, 0.23, 0.15], 0.3, false);
    else for (const s of [-0.45, 0.45]) ribbon(t.pts, 0.2, [0.27, 0.2, 0.13], 0.5, false, s);
  }
  const m = new BABYLON.Mesh('beach-tracks', scene), vd = new BABYLON.VertexData(); vd.positions = pos; vd.normals = nor; vd.colors = col; vd.indices = idx; vd.applyToMesh(m, false);
  const mat = new BABYLON.StandardMaterial('beach-tracks', scene); mat.specularColor = new BABYLON.Color3(0, 0, 0); mat.diffuseColor = new BABYLON.Color3(1, 1, 1); mat.transparencyMode = BABYLON.Material.MATERIAL_ALPHABLEND; mat.zOffset = -2; mat.backFaceCulling = false;
  m.hasVertexAlpha = true; m.useVertexColors = true; m.material = mat; m.isPickable = false; m.alphaIndex = 4;
  return m;
}

export class BeachKit {
  readonly ground = beachGround();
  readonly scatter: ScatterView;
  readonly litter: LitterView;
  readonly wrecks: WrecksView;
  readonly meshes: BABYLON.Mesh[] = [];
  ready = false;
  constructor(private scene: BABYLON.Scene, lib: AssetLibrary, world: World, lite = false) {
    this.scatter = new ScatterView(scene, { ground: this.ground, species: BEACH_SPECIES, cell: 40, radius: lite ? 150 : 210, cellsPerUpdate: lite ? 1 : 2, generators: { driftwood, wrack, shingle } });
    this.litter = new LitterView(scene, lib, layoutBeachLitter());
    this.wrecks = new WrecksView(scene, lib, world, WRECKS2);
  }
  async build() {
    this.meshes.push(...buildWire(this.scene, wireLines()), buildTracks(this.scene, trackList()));
    await Promise.all([this.litter.build(), this.wrecks.build()]);
    this.ready = true;
  }
  update(cam: BABYLON.Vector3) { this.scatter.update([cam.x, cam.y, cam.z]); }
}
void makeRock; void foredune; void TIDE;
