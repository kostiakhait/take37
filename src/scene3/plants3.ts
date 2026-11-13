// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import { hash2, subSeed, type MeshData, type Species } from '@ferret/terrain';

/**
 * Plants of the English plain, made in code in the shape `@ferret/terrain`'s `ScatterView` takes (a mesh of unit height with its base on y = 0 and vertex colours; the wind moves a plant by the height
 * of the vertex, `land/plant-material.ts`): four kinds of grass clump of different height and colour, dock and cow parsley, bramble, hawthorn, and the trees of a hedgerow (English oak, ash, field elm,
 * poplar). Each generator makes several variants; the scatter sizes them by the law of the species, so no two neighbours are alike.
 */
type C3 = [number, number, number];
export interface PlantData extends MeshData { colors: Float32Array }
const mix3 = (a: C3, b: C3, t: number): C3 => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];
const jit = (c: C3, k: number): C3 => [Math.max(0, c[0] * k), Math.max(0, c[1] * k), Math.max(0, c[2] * k)];

class B {
  pos: number[] = []; col: number[] = []; idx: number[] = []; own = new Map<number, C3>();
  vert(x: number, y: number, z: number, c: C3) { this.pos.push(x, y, z); this.col.push(c[0], c[1], c[2], 1); return this.pos.length / 3 - 1; }
  tri(a: number, b: number, c: number) { this.idx.push(a, b, c); }
  /** a blade: a tapering strip bent over (lean along (lx, lz) grows with height), width w at the foot */
  blade(x: number, z: number, h: number, w: number, ang: number, lean: number, c0: C3, c1: C3) {
    const ca = Math.cos(ang), sa = Math.sin(ang), lx = Math.cos(ang + 1.57) * lean * h, lz = Math.sin(ang + 1.57) * lean * h, seg = 3;
    let pa = this.vert(x - ca * w, 0, z - sa * w, c0), pb = this.vert(x + ca * w, 0, z + sa * w, c0);
    for (let i = 1; i <= seg; i++) {
      const t = i / seg, bend = t * t, ww = w * (1 - 0.85 * t), px = x + lx * bend, pz = z + lz * bend, c = mix3(c0, c1, t);
      if (i === seg) { const tip = this.vert(px, h * (1 - 0.18 * bend), pz, c); this.tri(pa, pb, tip); this.tri(pb, pa, tip); break; }
      const qa = this.vert(px - ca * ww, h * t * (1 - 0.18 * bend), pz - sa * ww, c), qb = this.vert(px + ca * ww, h * t * (1 - 0.18 * bend), pz + sa * ww, c);
      this.tri(pa, pb, qa); this.tri(pb, qb, qa); this.tri(qa, pb, pa); this.tri(qa, qb, pb); pa = qa; pb = qb;
    }
  }
  /** a leaf card at c: long axis ax, width axis bx; the normal n is the crown's */
  leaf(c: C3, ax: C3, bx: C3, l: number, w: number, n: C3, c0: C3, c1: C3) {
    const p = (t: number, s: number, up: number): C3 => [c[0] + ax[0] * l * t + bx[0] * w * s + n[0] * up, c[1] + ax[1] * l * t + bx[1] * w * s + n[1] * up, c[2] + ax[2] * l * t + bx[2] * w * s + n[2] * up];
    const a = this.vert(...p(0, 0, 0), c0), b = this.vert(...p(0.45, -1, 0.012), mix3(c0, c1, 0.5)), d = this.vert(...p(0.45, 1, 0.012), mix3(c0, c1, 0.5)), e = this.vert(...p(1, 0, 0), c1);
    this.tri(a, b, d); this.tri(b, e, d); this.tri(d, b, a); this.tri(d, e, b); for (const k of [a, b, d, e]) this.own.set(k, n);
  }
  tube(p: C3, q: C3, r0: number, r1: number, seg: number, c0: C3, c1: C3) {
    const dx = q[0] - p[0], dy = q[1] - p[1], dz = q[2] - p[2], l = Math.hypot(dx, dy, dz) || 1, ux = dx / l, uy = dy / l, uz = dz / l;
    let ax = 0, ay = 1, az = 0; if (Math.abs(uy) > 0.9) { ax = 1; ay = 0; }
    let bx = uy * az - uz * ay, by = uz * ax - ux * az, bz = ux * ay - uy * ax; const bl = Math.hypot(bx, by, bz) || 1; bx /= bl; by /= bl; bz /= bl;
    const cx = by * uz - bz * uy, cy = bz * ux - bx * uz, cz = bx * uy - by * ux, base = this.pos.length / 3;
    for (let s = 0; s < seg; s++) { const a = (s / seg) * Math.PI * 2, ca = Math.cos(a), sa = Math.sin(a), ox = bx * ca + cx * sa, oy = by * ca + cy * sa, oz = bz * ca + cz * sa; this.vert(p[0] + ox * r0, p[1] + oy * r0, p[2] + oz * r0, c0); this.vert(q[0] + ox * r1, q[1] + oy * r1, q[2] + oz * r1, c1); }
    for (let s = 0; s < seg; s++) { const a = base + s * 2, b = base + ((s + 1) % seg) * 2; this.tri(a, a + 1, b); this.tri(b, a + 1, b + 1); }
  }
  /** a lumpy leaf mass lit from above by its colour (dark under, light on top); normals point out of its middle */
  mass(c: C3, rx: number, ry: number, rz: number, seed: number, lump: number, dark: C3, light: C3, rings = 4, seg = 9) {
    const base = this.pos.length / 3;
    for (let i = 0; i <= rings; i++) {
      const th = (i / rings) * Math.PI, y = Math.cos(th), r = Math.sin(th);
      for (let s = 0; s < (i === 0 || i === rings ? 1 : seg); s++) {
        const a = (s / seg) * Math.PI * 2, k = 1 + lump * (hash2(i * 13 + s, 7, seed) - 0.5) * 2, t = Math.min(1, Math.max(0, (y + 1) / 2 + 0.2 * (hash2(i, s, seed + 3) - 0.5)));
        const v = this.vert(c[0] + Math.cos(a) * r * rx * k, c[1] + y * ry * k, c[2] + Math.sin(a) * r * rz * k, mix3(dark, light, t) as C3);
        const nx = Math.cos(a) * r / rx, ny = y / ry, nz = Math.sin(a) * r / rz, nl = Math.hypot(nx, ny, nz) || 1; this.own.set(v, [nx / nl, ny / nl, nz / nl]);
      }
    }
    const first = base + 1, last = base + 1 + (rings - 1) * seg;
    for (let s = 0; s < seg; s++) { this.tri(base, first + ((s + 1) % seg), first + s); this.tri(base, first + s, first + ((s + 1) % seg)); }
    for (let i = 0; i < rings - 2; i++) for (let s = 0; s < seg; s++) { const a = first + i * seg + s, b = first + i * seg + (s + 1) % seg, cc = a + seg, d = b + seg; this.tri(a, b, cc); this.tri(b, d, cc); this.tri(cc, b, a); this.tri(cc, d, b); }
    for (let s = 0; s < seg; s++) { this.tri(last, first + (rings - 2) * seg + s, first + (rings - 2) * seg + ((s + 1) % seg)); this.tri(last, first + (rings - 2) * seg + ((s + 1) % seg), first + (rings - 2) * seg + s); }
  }
  done(): PlantData {
    const pos = Float32Array.from(this.pos), idx = Uint32Array.from(this.idx), nor = new Float32Array(pos.length);
    for (let i = 0; i < idx.length; i += 3) {
      const a = idx[i]!, b = idx[i + 1]!, c = idx[i + 2]!, ux = pos[b * 3]! - pos[a * 3]!, uy = pos[b * 3 + 1]! - pos[a * 3 + 1]!, uz = pos[b * 3 + 2]! - pos[a * 3 + 2]!, vx = pos[c * 3]! - pos[a * 3]!, vy = pos[c * 3 + 1]! - pos[a * 3 + 1]!, vz = pos[c * 3 + 2]! - pos[a * 3 + 2]!;
      const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx; for (const k of [a, b, c]) { nor[k * 3]! += nx; nor[k * 3 + 1]! += ny; nor[k * 3 + 2]! += nz; }
    }
    for (let i = 0; i < nor.length; i += 3) { const l = Math.hypot(nor[i]!, nor[i + 1]!, nor[i + 2]!) || 1; nor[i]! /= l; nor[i + 1]! /= l; nor[i + 2]! /= l; }
    for (const [k, n] of this.own) { const l = Math.hypot(n[0], n[1], n[2]) || 1; nor[k * 3] = n[0] / l; nor[k * 3 + 1] = n[1] / l; nor[k * 3 + 2] = n[2] / l; }
    // grass blades are lit from above whichever way they face
    return { positions: pos, normals: nor, indices: idx, colors: Float32Array.from(this.col) };
  }
}

/** a clump of grass: `n` blades of height 0.55..1 round a centre, leaning over; `kind` sets the colours and the stiffness */
function clump(seed: number, variant: number, o: { n: number; spread: number; w: number; lean: [number, number]; foot: C3; tip: C3; heads?: boolean; hmin?: number }): PlantData {
  const s = subSeed(seed, 2100 + variant * 37), m = new B();
  for (let i = 0; i < o.n; i++) {
    const a = hash2(variant, i, s) * 6.283, r = o.spread * Math.sqrt(hash2(variant, 30 + i, s)), h = (o.hmin ?? 0.5) + (1 - (o.hmin ?? 0.5)) * hash2(variant, 60 + i, s), lean = o.lean[0] + (o.lean[1] - o.lean[0]) * hash2(variant, 90 + i, s), ang = hash2(variant, 120 + i, s) * 6.283;
    const t = hash2(variant, 150 + i, s), c0 = jit(o.foot, 0.8 + 0.3 * t), c1 = mix3(o.tip, jit(o.tip, 1.15), t);
    m.blade(Math.cos(a) * r, Math.sin(a) * r, h, o.w, ang, lean, c0, c1);
  }
  if (o.heads) for (let i = 0; i < Math.round(o.n / 5); i++) { // seed heads: a short bristle at the tip of a tall stalk
    const a = hash2(variant, 200 + i, s) * 6.283, r = o.spread * 0.8 * hash2(variant, 230 + i, s), x = Math.cos(a) * r, z = Math.sin(a) * r, h = 0.85 + 0.15 * hash2(variant, 260 + i, s);
    m.tube([x, 0, z], [x + 0.03, h, z + 0.02], 0.004, 0.003, 3, [0.4, 0.5, 0.2], [0.55, 0.55, 0.28]); m.tube([x + 0.03, h, z + 0.02], [x + 0.045, h + 0.14, z + 0.03], 0.014, 0.004, 4, [0.62, 0.58, 0.32], [0.72, 0.66, 0.4]);
  }
  return m.done();
}
export const meadowTuft = (seed: number, v: number) => clump(seed, v, { n: 34, spread: 0.2, w: 0.022, lean: [0.2, 0.6], foot: [0.16, 0.26, 0.07], tip: [0.46, 0.58, 0.2] });
export const longGrass = (seed: number, v: number) => clump(seed, v, { n: 46, spread: 0.24, w: 0.02, lean: [0.12, 0.5], foot: [0.2, 0.3, 0.08], tip: [0.62, 0.62, 0.28], heads: true, hmin: 0.62 });
export const rushTuft = (seed: number, v: number) => clump(seed, v, { n: 28, spread: 0.16, w: 0.016, lean: [0.1, 0.35], foot: [0.14, 0.24, 0.1], tip: [0.3, 0.46, 0.22], hmin: 0.7 });
export const driedTuft = (seed: number, v: number) => clump(seed, v, { n: 30, spread: 0.2, w: 0.02, lean: [0.25, 0.7], foot: [0.34, 0.28, 0.13], tip: [0.78, 0.68, 0.42] });

/** dock or burdock: a rosette of broad leaves low down and one tall seed spike */
export function dock(seed: number, variant: number): PlantData {
  const s = subSeed(seed, 2300 + variant * 31), m = new B();
  for (let i = 0; i < 9; i++) {
    const a = (i / 9) * 6.283 + hash2(variant, i, s) * 0.5, lift = 0.15 + 0.25 * hash2(variant, 10 + i, s), l = 0.3 + 0.2 * hash2(variant, 20 + i, s), ca = Math.cos(a), sa = Math.sin(a);
    m.leaf([ca * 0.03, 0.02, sa * 0.03], [ca * (1 - lift), lift * 1.2, sa * (1 - lift)], [-sa, 0, ca], l, 0.11, [0, 1, 0], [0.12, 0.22, 0.06], [0.3, 0.42, 0.14]);
  }
  m.tube([0, 0, 0], [0.02, 0.95, 0.01], 0.012, 0.005, 4, [0.3, 0.3, 0.12], [0.45, 0.35, 0.16]);
  for (let i = 0; i < 6; i++) { const y = 0.5 + i * 0.08, a = hash2(variant, 50 + i, s) * 6.283; m.tube([0.02 * y, y, 0], [0.02 * y + Math.cos(a) * 0.09, y + 0.05, Math.sin(a) * 0.09], 0.006, 0.003, 3, [0.45, 0.35, 0.16], [0.55, 0.3, 0.14]); }
  return m.done();
}
/** cow parsley (Queen Anne's lace): finely cut leaves low down and flat white umbels on tall stalks */
export function parsley(seed: number, variant: number): PlantData {
  const s = subSeed(seed, 2400 + variant * 31), m = new B();
  for (let i = 0; i < 6; i++) { const a = (i / 6) * 6.283 + hash2(variant, i, s), ca = Math.cos(a), sa = Math.sin(a); m.leaf([0, 0.02, 0], [ca * 0.8, 0.5, sa * 0.8], [-sa, 0, ca], 0.3, 0.07, [0, 1, 0], [0.12, 0.24, 0.07], [0.24, 0.42, 0.14]); }
  for (let k = 0; k < 4; k++) {
    const a = hash2(variant, 40 + k, s) * 6.283, r = 0.12 * hash2(variant, 50 + k, s), h = 0.7 + 0.3 * hash2(variant, 60 + k, s), x = Math.cos(a) * r, z = Math.sin(a) * r;
    m.tube([x * 0.3, 0, z * 0.3], [x, h, z], 0.01, 0.005, 4, [0.26, 0.4, 0.14], [0.4, 0.5, 0.22]);
    for (let u = 0; u < 7; u++) { const b = (u / 7) * 6.283, rr = 0.07; const px = x + Math.cos(b) * rr, pz = z + Math.sin(b) * rr; m.leaf([px, h + 0.04, pz], [Math.cos(b) * 0.4, 0.05, Math.sin(b) * 0.4], [-Math.sin(b), 0, Math.cos(b)], 0.07, 0.05, [0, 1, 0], [0.82, 0.84, 0.76], [0.97, 0.97, 0.94]); }
    m.leaf([x, h + 0.06, z], [1, 0, 0], [0, 0, 1], 0.07, 0.07, [0, 1, 0], [0.9, 0.9, 0.86], [0.97, 0.97, 0.94]);
  }
  return m.done();
}
/** bramble: arching canes with leaf cards and a few pink flowers */
export function bramble(seed: number, variant: number): PlantData {
  const s = subSeed(seed, 2500 + variant * 31), m = new B();
  for (let i = 0; i < 7; i++) {
    const a = hash2(variant, i, s) * 6.283, ca = Math.cos(a), sa = Math.sin(a), len = 0.6 + 0.5 * hash2(variant, 10 + i, s);
    let px = 0, py = 0.04, pz = 0;
    for (let k = 1; k <= 4; k++) {
      const t = k / 4, nx = ca * len * t, nz = sa * len * t, ny = 0.7 * Math.sin(Math.min(1, t * 1.25) * 2.2) * len * (1 - 0.5 * t);
      m.tube([px, py, pz], [nx, Math.max(0.02, ny), nz], 0.012, 0.01, 4, [0.3, 0.12, 0.08], [0.35, 0.2, 0.1]);
      for (let l = 0; l < 3; l++) { const b = hash2(variant, 100 + i * 9 + k * 3 + l, s) * 6.283; m.leaf([nx, Math.max(0.02, ny), nz], [Math.cos(b), 0.2, Math.sin(b)], [-Math.sin(b), 0, Math.cos(b)], 0.16, 0.08, [0, 1, 0], [0.12, 0.25, 0.08], [0.27, 0.42, 0.14]); }
      px = nx; py = Math.max(0.02, ny); pz = nz;
    }
  }
  return m.done();
}
/** hawthorn: a shrub of dense crooked twigs under a rounded crown of small leaf masses, a few cream blossoms; unit height 1 (scaled 2..5 m) */
export function hawthorn(seed: number, variant: number): PlantData {
  const s = subSeed(seed, 2600 + variant * 31), m = new B(), bark: C3 = [0.2, 0.15, 0.1];
  m.tube([0, 0, 0], [0.02, 0.35, 0.01], 0.05, 0.035, 5, bark, bark);
  const n = 7;
  for (let i = 0; i < n; i++) {
    const a = hash2(variant, i, s) * 6.283, d = 0.12 + 0.35 * hash2(variant, 10 + i, s), y = 0.35 + 0.45 * hash2(variant, 20 + i, s), r = 0.2 + 0.1 * hash2(variant, 30 + i, s);
    m.tube([0, 0.3, 0], [Math.cos(a) * d, y, Math.sin(a) * d], 0.025, 0.012, 4, bark, bark);
    m.mass([Math.cos(a) * d, y, Math.sin(a) * d], r, r * 0.75, r, s + i, 0.35, [0.09, 0.19, 0.06], [0.28, 0.42, 0.14], 3, 7);
  }
  m.mass([0, 0.7, 0], 0.32, 0.27, 0.32, s + 99, 0.3, [0.1, 0.2, 0.07], [0.3, 0.44, 0.15], 3, 8);
  for (let i = 0; i < 8; i++) { const a = hash2(variant, 60 + i, s) * 6.283, d = 0.2 + 0.3 * hash2(variant, 70 + i, s); m.leaf([Math.cos(a) * d, 0.45 + 0.4 * hash2(variant, 80 + i, s), Math.sin(a) * d], [1, 0.3, 0], [0, 0, 1], 0.1, 0.1, [0, 1, 0], [0.85, 0.82, 0.72], [0.95, 0.93, 0.86]); }
  return m.done();
}
/** a broadleaf tree of unit height 1: a trunk that forks into limbs, crowns of leaf masses; `kind` sets the proportions and colours */
function tree(seed: number, variant: number, o: { crown: number; height: number; limbs: number; spread: number; trunk: number; bark: C3; dark: C3; light: C3; flat?: boolean; columnar?: boolean; lump: number; masses: number }): PlantData {
  const s = subSeed(seed, 2700 + variant * 41), m = new B();
  const tall = o.height, tw = o.trunk;
  m.tube([0, -0.02, 0], [0, tall * 0.34, 0], tw * 1.15, tw * 0.8, 7, jit(o.bark, 0.8), o.bark);
  for (let i = 0; i < o.limbs; i++) {
    const a = (i / o.limbs) * 6.283 + hash2(variant, i, s) * 0.8, up = o.columnar ? 0.8 : 0.35 + 0.35 * hash2(variant, 10 + i, s), reach = o.spread * (0.55 + 0.45 * hash2(variant, 20 + i, s)), top = tall * (o.columnar ? 0.95 : 0.55 + 0.35 * hash2(variant, 30 + i, s));
    const ex = Math.cos(a) * reach, ez = Math.sin(a) * reach, ey = top, y0 = tall * (0.3 + 0.1 * hash2(variant, 35 + i, s));
    m.tube([0, y0, 0], [ex * 0.5, (y0 + ey) / 2 + up * 0.05, ez * 0.5], tw * 0.6, tw * 0.4, 5, o.bark, o.bark); m.tube([ex * 0.5, (y0 + ey) / 2 + up * 0.05, ez * 0.5], [ex, ey, ez], tw * 0.4, tw * 0.15, 5, o.bark, o.bark);
    for (let k = 0; k < o.masses; k++) {
      const t = 0.5 + 0.55 * hash2(variant, 40 + i * 7 + k, s), ox = ex * t + (hash2(variant, 50 + i * 7 + k, s) - 0.5) * o.spread * 0.5, oz = ez * t + (hash2(variant, 60 + i * 7 + k, s) - 0.5) * o.spread * 0.5, oy = ey * (0.8 + 0.3 * t) + (hash2(variant, 70 + i * 7 + k, s) - 0.5) * 0.14;
      const rr = o.crown * (0.7 + 0.5 * hash2(variant, 80 + i * 7 + k, s));
      m.mass([ox, oy, oz], rr, rr * (o.flat ? 0.55 : o.columnar ? 1.6 : 0.8), rr, s + i * 11 + k, o.lump, o.dark, o.light, 3, 8);
    }
  }
  m.mass([0, tall * 0.86, 0], o.crown * 1.1, o.crown * (o.columnar ? 1.8 : 0.85), o.crown * 1.1, s + 77, o.lump, o.dark, o.light, 4, 9);
  return m.done();
}
const OAK = { crown: 0.2, height: 0.62, limbs: 5, spread: 0.46, trunk: 0.035, bark: [0.2, 0.16, 0.12] as C3, dark: [0.06, 0.15, 0.04] as C3, light: [0.2, 0.36, 0.1] as C3, lump: 0.32, masses: 3, flat: true };
export const oakTree = (seed: number, v: number) => tree(seed, v, OAK);
export const ashTree = (seed: number, v: number) => tree(seed, v, { crown: 0.17, height: 0.7, limbs: 5, spread: 0.34, trunk: 0.028, bark: [0.3, 0.28, 0.24], dark: [0.1, 0.2, 0.07], light: [0.32, 0.46, 0.16], lump: 0.4, masses: 3 });
export const elmTree = (seed: number, v: number) => tree(seed, v, { crown: 0.19, height: 0.72, limbs: 6, spread: 0.4, trunk: 0.04, bark: [0.22, 0.18, 0.14], dark: [0.07, 0.16, 0.05], light: [0.24, 0.38, 0.12], lump: 0.3, masses: 3 });
export const poplarTree = (seed: number, v: number) => tree(seed, v, { crown: 0.1, height: 0.8, limbs: 5, spread: 0.12, trunk: 0.022, bark: [0.3, 0.26, 0.2], dark: [0.1, 0.2, 0.07], light: [0.38, 0.5, 0.17], lump: 0.2, masses: 4, columnar: true });

export const GENERATORS3: Record<string, (seed: number, variant: number) => PlantData> = { 'meadow-tuft': meadowTuft, 'long-grass': longGrass, 'rush-tuft': rushTuft, 'dried-tuft': driedTuft, dock, parsley, bramble, hawthorn, oak: oakTree, ash: ashTree, elm: elmTree, poplar: poplarTree };

/** where what grows on the plain beyond the airfield (individuals per 100 m2 where a biome weighs 1); the airfield's own ground is the biome 'salt-flat' that none of them lists, its edges are dressed by hand (verges3.ts) */
const PLAIN = { meadow: 1, floodplain: 1, 'temperate-forest': 0.6, farmland: 0.4, steppe: 0.4 };
const on = (k: number) => Object.fromEntries(Object.entries(PLAIN).map(([b, w]) => [b, w * k]));
export const SMALL: Species[] = [
  { id: 'meadow-tuft', shape: 'meadow-tuft', biomes: on(5.5), size: [0.35, 0.9], exponent: 2, variants: 5, slope: [0, 0.9], dry: true, cluster: { wavelength: 11, lo: 0.2, hi: 0.5 } },
  { id: 'long-grass', shape: 'long-grass', biomes: on(2.6), size: [0.5, 1.2], exponent: 2, variants: 4, slope: [0, 0.9], dry: true, cluster: { wavelength: 17, lo: 0.4, hi: 0.65 } },
  { id: 'rush', shape: 'rush-tuft', biomes: { floodplain: 3, meadow: 0.5 }, size: [0.4, 1.1], exponent: 2, variants: 3, slope: [0, 0.4], dry: true, wetness: [0.55, 1], cluster: { wavelength: 9, lo: 0.3, hi: 0.6 } },
  { id: 'dried-tuft', shape: 'dried-tuft', biomes: on(1.4), size: [0.35, 0.8], exponent: 2, variants: 3, slope: [0, 0.9], dry: true, cluster: { wavelength: 23, lo: 0.5, hi: 0.75 } },
  { id: 'dock', shape: 'dock', biomes: on(0.35), size: [0.5, 1.3], exponent: 2, variants: 3, slope: [0, 0.6], dry: true, cluster: { wavelength: 14, lo: 0.5, hi: 0.75 } },
  { id: 'parsley', shape: 'parsley', biomes: on(0.5), size: [0.6, 1.3], exponent: 2, variants: 3, slope: [0, 0.6], dry: true, cluster: { wavelength: 26, lo: 0.55, hi: 0.8 } },
  { id: 'bramble', shape: 'bramble', biomes: on(0.12), size: [0.8, 1.8], exponent: 2, variants: 3, slope: [0, 0.8], dry: true, cluster: { wavelength: 30, lo: 0.6, hi: 0.8 } },
];
export const STONES3: Species[] = [
  { id: 'flint', shape: 'pebble', biomes: on(0.6), size: [0.08, 0.3], exponent: 2.2, buried: 0.35, variants: 6, slope: [0, 2] },
  { id: 'field-stone', shape: 'rock', biomes: on(0.03), size: [0.3, 0.9], exponent: 2.2, buried: 0.3, variants: 6, slope: [0, 1.6] },
];
