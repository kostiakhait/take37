// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import { ROCKS, hash2, makeRock, subSeed, type MeshData, type Species } from '@ferret/terrain';

/**
 * Plants of the Californian hills, made in code in the shape `@ferret/terrain`'s `ScatterView` takes: a mesh of unit height with its base on y = 0 and vertex colours. The wind moves a
 * plant by the height of the vertex (`wind-sway.ts`), so the crown of an oak bends and its trunk does not.
 */
type C3 = [number, number, number];
export interface PlantData extends MeshData { colors: Float32Array }

class Mesh {
  pos: number[] = []; col: number[] = []; idx: number[] = [];
  /** vertices that keep a normal of their own (leaf cards shade as a volume: the normal points out of the crown, not along the card) */
  own = new Map<number, C3>();
  /** a leaf card (a diamond of two triangles with a kink along its middle) at `c`, its long axis along `ax`, its width axis along `bx`; the normal `n` is the crown's, `c0` at the base and `c1` at the tip */
  leaf(c: C3, ax: C3, bx: C3, l: number, w: number, n: C3, c0: C3, c1: C3) {
    const p = (t: number, s: number, up: number): C3 => [c[0] + ax[0] * l * t + bx[0] * w * s + n[0] * up, c[1] + ax[1] * l * t + bx[1] * w * s + n[1] * up, c[2] + ax[2] * l * t + bx[2] * w * s + n[2] * up];
    const a = this.vert(...p(0, 0, 0), c0), b = this.vert(...p(0.42, -1, 0.012), mix3(c0, c1, 0.45)), d = this.vert(...p(0.42, 1, 0.012), mix3(c0, c1, 0.45)), e = this.vert(...p(1, 0, 0), c1);
    this.tri(a, b, d); this.tri(b, e, d);
    for (const k of [a, b, d, e]) this.own.set(k, n);
  }
  vert(x: number, y: number, z: number, c: C3): number { this.pos.push(x, y, z); this.col.push(c[0], c[1], c[2], 1); return this.pos.length / 3 - 1; }
  tri(a: number, b: number, c: number) { this.idx.push(a, b, c); }
  tube(p: C3, q: C3, r0: number, r1: number, seg: number, c0: C3, c1: C3) {
    const dx = q[0] - p[0], dy = q[1] - p[1], dz = q[2] - p[2], l = Math.hypot(dx, dy, dz) || 1, ux = dx / l, uy = dy / l, uz = dz / l;
    let ax = 0, ay = 1, az = 0; if (Math.abs(uy) > 0.9) { ax = 1; ay = 0; }
    let bx = uy * az - uz * ay, by = uz * ax - ux * az, bz = ux * ay - uy * ax; const bl = Math.hypot(bx, by, bz) || 1; bx /= bl; by /= bl; bz /= bl;
    const cx = by * uz - bz * uy, cy = bz * ux - bx * uz, cz = bx * uy - by * ux, base = this.pos.length / 3;
    for (let s = 0; s < seg; s++) {
      const a = (s / seg) * Math.PI * 2, ca = Math.cos(a), sa = Math.sin(a), ox = bx * ca + cx * sa, oy = by * ca + cy * sa, oz = bz * ca + cz * sa;
      this.vert(p[0] + ox * r0, p[1] + oy * r0, p[2] + oz * r0, c0); this.vert(q[0] + ox * r1, q[1] + oy * r1, q[2] + oz * r1, c1);
    }
    for (let s = 0; s < seg; s++) { const a = base + s * 2, b = base + ((s + 1) % seg) * 2; this.tri(a, a + 1, b); this.tri(b, a + 1, b + 1); }
  }
  /** a lumpy leaf mass: a subdivided octahedron with hash displacement, lit from above by its colour (dark under, light on top) */
  mass(c: C3, rx: number, ry: number, rz: number, seed: number, lump: number, dark: C3, light: C3, rings = 4, seg = 8) {
    const base = this.pos.length / 3;
    for (let i = 0; i <= rings; i++) {
      const v = i / rings, th = v * Math.PI, y = Math.cos(th), r = Math.sin(th);
      for (let s = 0; s < (i === 0 || i === rings ? 1 : seg); s++) {
        const a = (s / seg) * Math.PI * 2, k = 1 + lump * (hash2(i * 13 + s, 7, seed) - 0.5) * 2, t = Math.min(1, Math.max(0, (y + 1) / 2 + 0.15 * (hash2(i, s, seed + 3) - 0.5)));
        this.vert(c[0] + Math.cos(a) * r * rx * k, c[1] + y * ry * k, c[2] + Math.sin(a) * r * rz * k, [dark[0] + (light[0] - dark[0]) * t, dark[1] + (light[1] - dark[1]) * t, dark[2] + (light[2] - dark[2]) * t]);
      }
    }
    const ring = (i: number) => (i === 0 || i === rings ? [base + (i === 0 ? 0 : this.ringStart(base, rings, seg))] : null);
    void ring;
    // vertex layout: 1 pole, rings 1..rings-1 of seg vertices, 1 pole
    const first = base + 1, last = base + 1 + (rings - 1) * seg;
    for (let s = 0; s < seg; s++) this.tri(base, first + ((s + 1) % seg), first + s);
    for (let i = 0; i < rings - 2; i++) for (let s = 0; s < seg; s++) { const a = first + i * seg + s, b = first + i * seg + (s + 1) % seg, cc = a + seg, d = b + seg; this.tri(a, b, cc); this.tri(b, d, cc); }
    for (let s = 0; s < seg; s++) this.tri(last, first + (rings - 2) * seg + s, first + (rings - 2) * seg + ((s + 1) % seg));
  }
  private ringStart(base: number, rings: number, seg: number) { return 1 + (rings - 1) * seg; }
  done(): PlantData {
    const pos = Float32Array.from(this.pos), idx = Uint32Array.from(this.idx), nor = new Float32Array(pos.length);
    for (let i = 0; i < idx.length; i += 3) {
      const a = idx[i], b = idx[i + 1], c = idx[i + 2], ux = pos[b * 3] - pos[a * 3], uy = pos[b * 3 + 1] - pos[a * 3 + 1], uz = pos[b * 3 + 2] - pos[a * 3 + 2], vx = pos[c * 3] - pos[a * 3], vy = pos[c * 3 + 1] - pos[a * 3 + 1], vz = pos[c * 3 + 2] - pos[a * 3 + 2];
      const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx; for (const k of [a, b, c]) { nor[k * 3] += nx; nor[k * 3 + 1] += ny; nor[k * 3 + 2] += nz; }
    }
    for (let i = 0; i < nor.length; i += 3) { const l = Math.hypot(nor[i], nor[i + 1], nor[i + 2]) || 1; nor[i] /= l; nor[i + 1] /= l; nor[i + 2] /= l; }
    for (const [k, n] of this.own) { const l = Math.hypot(n[0], n[1], n[2]) || 1; nor[k * 3] = n[0] / l; nor[k * 3 + 1] = n[1] / l; nor[k * 3 + 2] = n[2] / l; }
    // the normals of a leaf mass point away from its middle, not along the faces: a canopy lit as one soft mass, not a heap of facets
    return { positions: pos, normals: nor, indices: idx, colors: Float32Array.from(this.col) };
  }
}

const BARK: C3 = [0.22, 0.17, 0.12], BARK_HI: C3 = [0.34, 0.28, 0.2];

/**
 * A coast live oak of the dry hills: a short, very thick trunk that forks near the ground into heavy, crooked limbs, under a broad low mound of dense dark-green leaf masses that nearly
 * touches the ground (the crown is wider than the tree is tall); unit height, the crown about 1.7 wide. Some limbs show through the lower crown.
 */
export function oak(seed: number, variant: number): PlantData {
  const s = subSeed(seed, 900 + variant * 53), m = new Mesh();
  const lean = 0.12 * (hash2(variant, 1, s) - 0.5);
  m.tube([0, 0, 0], [lean * 0.5, 0.1, 0.01], 0.105, 0.085, 9, BARK, BARK);
  const limbs = 3 + Math.floor(3 * hash2(variant, 2, s)), crown: C3[] = [];
  for (let i = 0; i < limbs; i++) {
    const a = (i / limbs) * 6.283 + hash2(variant, 3 + i, s) * 1.3, up = 0.16 + 0.16 * hash2(variant, 9 + i, s), reach = 0.5 + 0.34 * hash2(variant, 15 + i, s), bend = 0.25 * (hash2(variant, 21 + i, s) - 0.5);
    const base: C3 = [lean * 0.5, 0.09, 0.01], mid: C3 = [Math.cos(a) * reach * 0.45, 0.1 + up * 0.7, Math.sin(a) * reach * 0.45], tip: C3 = [Math.cos(a + bend) * reach, 0.1 + up + 0.2, Math.sin(a + bend) * reach];
    m.tube(base, mid, 0.07, 0.05, 7, BARK, BARK_HI); m.tube(mid, tip, 0.05, 0.022, 6, BARK_HI, BARK_HI);
    crown.push(tip);
    const a2 = a + 0.9 * (hash2(variant, 40 + i, s) - 0.5) * 2, t2: C3 = [mid[0] + Math.cos(a2) * 0.28, mid[1] + 0.2, mid[2] + Math.sin(a2) * 0.28];
    m.tube(mid, t2, 0.03, 0.012, 5, BARK_HI, BARK_HI); crown.push(t2);
  }
  // the crown: leaf cards in a mound of masses, as the street trees' crowns are made of sprig cards: an olive-green evergreen with sunlit tops, dark hollows inside, a ragged outline
  // (colours are sRGB in the vertex colour and are squared by the plant shader, so the greens sit well above the dark of the old domes)
  const dark: C3 = [0.14, 0.2, 0.07], mid: C3 = [0.25, 0.33, 0.1], light: C3 = [0.42, 0.49, 0.16], dry: C3 = [0.52, 0.47, 0.19];
  const n = 40 + Math.floor(8 * hash2(variant, 5, s)), tone = 0.85 + 0.18 * hash2(variant, 6, s), mound: C3 = [lean * 0.4, 0.42, 0];
  for (let i = 0; i < n; i++) {
    const k = hash2(variant, 100 + i, s), a = hash2(variant, 200 + i, s) * 6.283, r = (0.2 + 0.8 * Math.sqrt(hash2(variant, 300 + i, s))) * 0.88;
    const dome = Math.sqrt(Math.max(0, 1 - (r / 0.98) ** 2)), y = 0.2 + 0.62 * dome * (0.55 + 0.45 * hash2(variant, 400 + i, s)), tier = Math.min(1, Math.max(0, (y - 0.18) / 0.6));
    const c = crown[i % crown.length], cx = Math.cos(a) * r + c[0] * 0.18, cz = Math.sin(a) * r + c[2] * 0.18, size = 0.18 + 0.12 * k;
    const lo = mix3(dark, mid, 0.25 + tier * 0.5), hi = mix3(mid, light, 0.2 + 0.8 * tier);
    for (let j = 0; j < 17; j++) {
      // a point on a lumpy ball round the mass's heart; the card stands along the outward direction with a random twist, so the outline breaks into tufts
      const u = hash2(variant * 31 + i, 500 + j, s) * 6.283, v = hash2(variant * 31 + i, 600 + j, s) * 2 - 1, rr = Math.sqrt(1 - v * v), shell = 0.45 + 0.55 * Math.sqrt(hash2(variant * 31 + i, 700 + j, s));
      const dx = Math.cos(u) * rr, dy = v, dz = Math.sin(u) * rr;
      const px = cx + dx * size * 1.25 * shell, py = y + dy * size * 0.85 * shell, pz = cz + dz * size * 1.25 * shell;
      const nx = px - mound[0], ny = (py - mound[1]) * 1.5 + 0.35, nz = pz - mound[2], nl = Math.hypot(nx, ny, nz) || 1, nn: C3 = [nx / nl, ny / nl, nz / nl];
      const t = hash2(variant * 31 + i, 800 + j, s), tw = hash2(variant * 31 + i, 900 + j, s) * 6.283;
      // long axis: the outward direction bent by a random tilt; width axis: perpendicular to it
      let ax: C3 = [dx + Math.cos(tw) * 0.7, dy * 0.6 + 0.2 + Math.sin(tw) * 0.5, dz + Math.sin(tw) * 0.7]; const al = Math.hypot(...ax) || 1; ax = [ax[0] / al, ax[1] / al, ax[2] / al];
      let bx: C3 = [ax[1] * nn[2] - ax[2] * nn[1], ax[2] * nn[0] - ax[0] * nn[2], ax[0] * nn[1] - ax[1] * nn[0]]; const bl = Math.hypot(...bx) || 1; bx = [bx[0] / bl, bx[1] / bl, bx[2] / bl];
      const base = t < 0.06 ? dry : mix3(lo, hi, 0.25 + 0.75 * hash2(variant * 31 + i, 1000 + j, s)), tip = mix3(base, light, 0.35), sc = tone;
      m.leaf([px, py, pz], ax, bx, 0.115 * (0.8 + 0.5 * t), 0.058 * (0.8 + 0.5 * t), nn, [base[0] * sc, base[1] * sc, base[2] * sc], [tip[0] * sc, tip[1] * sc, tip[2] * sc]);
    }
  }
  return m.done();
}
const mix3 = (a: C3, b: C3, t: number): C3 => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];

/** a dry chaparral / sagebrush bush: a hummock of grey-olive masses, a few dry stems showing at its foot */
export function sage(seed: number, variant: number): PlantData {
  const s = subSeed(seed, 1100 + variant * 29), m = new Mesh();
  const dark: C3 = [0.28, 0.29, 0.14], light: C3 = [0.6, 0.58, 0.34];   // grey-olive, lit enough to read as a bush and not a black blob at 100 m
  for (let i = 0; i < 9; i++) {
    const a = hash2(variant, i, s) * 6.283, r = 0.28 * Math.sqrt(hash2(variant, 20 + i, s)), y = 0.26 + 0.22 * (1 - r / 0.3) + 0.06 * hash2(variant, 40 + i, s);
    m.mass([Math.cos(a) * r, y, Math.sin(a) * r], 0.2, 0.17, 0.2, s + i, 0.3, dark, mix3(dark, light, 0.4 + 0.6 * hash2(variant, 60 + i, s)), 3, 7);
  }
  for (let i = 0; i < 4; i++) { const a = hash2(variant, 80 + i, s) * 6.283; m.tube([Math.cos(a) * 0.06, 0, Math.sin(a) * 0.06], [Math.cos(a) * 0.12, 0.26, Math.sin(a) * 0.12], 0.014, 0.008, 4, BARK, BARK_HI); }
  return m.done();
}

/** a tussock of dry grass in straw colours: crossed blades that lean over; unit height */
export function strawTuft(seed: number, variant: number): PlantData {
  const s = subSeed(seed, 1300 + variant * 31), m = new Mesh(), n = 22;
  for (let i = 0; i < n; i++) {
    const a = hash2(variant, i, s) * 6.283, r = 0.22 * hash2(variant, 30 + i, s), h = 0.55 + 0.45 * hash2(variant, 60 + i, s), w = 0.028, lean = 0.2 + 0.45 * hash2(variant, 90 + i, s), ang = hash2(variant, 120 + i, s) * 6.283;
    const ca = Math.cos(ang), sa = Math.sin(ang), x = Math.cos(a) * r, z = Math.sin(a) * r, tx = Math.cos(ang + 1.57) * lean * h, tz = Math.sin(ang + 1.57) * lean * h;
    const t = hash2(variant, 150 + i, s), c0: C3 = [0.42 + 0.1 * t, 0.34 + 0.08 * t, 0.15], c1: C3 = [0.86, 0.74 + 0.08 * t, 0.42 + 0.1 * t];
    const mid = h * 0.55, mx = x + tx * 0.25, mz = z + tz * 0.25;
    const a0 = m.vert(x - ca * w, 0, z - sa * w, c0), b0 = m.vert(x + ca * w, 0, z + sa * w, c0), a1 = m.vert(mx - ca * w * 0.7, mid, mz - sa * w * 0.7, mix3(c0, c1, 0.5)), b1 = m.vert(mx + ca * w * 0.7, mid, mz + sa * w * 0.7, mix3(c0, c1, 0.5)), tip = m.vert(x + tx, h, z + tz, c1);
    m.tri(a0, b0, a1); m.tri(b0, b1, a1); m.tri(a1, b1, tip); m.tri(a0, a1, b0); m.tri(b0, a1, b1); m.tri(a1, tip, b1);
  }
  return m.done();
}

/** the generators handed to the scatter view */
export const GENERATORS: Record<string, (seed: number, variant: number) => PlantData> = { oak, sage, 'straw-tuft': strawTuft };

/** stones of the cheapest honest meshes: a pebble 80 faces, a rock 320, a boulder 1280 (thousands of them stand in view) */
export const STONE_GENERATORS: Record<string, (seed: number, variant: number) => MeshData> = {
  pebble: (seed, v) => makeRock(seed + 6, v, 0.4, 1),
  rock: (seed, v) => makeRock(seed + 4, v, 0.55, 2),
  boulder: (seed, v) => makeRock(seed + 7, v, 0.85, 3),
};

/** where what grows (individuals per 100 m2 where a biome weighs 1) */
export const OAKS: Species[] = [
  // rare, in loose groves on the lower slopes and in the gullies; the size is the height, 7 to 16 m, few large
  { id: 'oak', shape: 'oak', biomes: { steppe: 0.045, savanna: 0.045, meadow: 0.08 }, size: [5, 12], exponent: 2.6, variants: 6, slope: [0, 0.5], dry: true, cluster: { wavelength: 420, lo: 0.42, hi: 0.72 }, layers: { 'desert-pavement': 0, rock: 0, scree: 0 } },
];
export const SHRUBS: Species[] = [
  { id: 'sage', shape: 'sage', biomes: { steppe: 0.55, savanna: 0.5 }, size: [0.7, 2.4], exponent: 2.4, variants: 5, slope: [0, 0.8], dry: true, cluster: { wavelength: 60, lo: 0.34, hi: 0.7 }, layers: { 'desert-pavement': 0.05 } },
  { id: 'straw-tuft', shape: 'straw-tuft', biomes: { steppe: 6, savanna: 5 }, size: [0.35, 0.9], exponent: 2, variants: 4, slope: [0, 0.9], dry: true, cluster: { wavelength: 14, lo: 0.2, hi: 0.5 }, layers: { rock: 0, scree: 0.1, 'desert-pavement': 0.04 } },
];
export const STONES: Species[] = [
  { id: 'pebble', shape: 'pebble', biomes: { steppe: 1.4, 'rock-desert': 6, cliffs: 8 }, size: [0.08, 0.3], exponent: 2.2, buried: 0.35, variants: 6, slope: [0, 2] },
  { id: 'rock', shape: 'rock', biomes: { steppe: 0.25, 'rock-desert': 1.2, cliffs: 4 }, size: [0.3, 1.2], exponent: 2.2, buried: 0.3, variants: 6, cluster: { wavelength: 90, lo: 0.4, hi: 0.7 }, slope: [0, 1.6] },
  { id: 'boulder', shape: 'boulder', biomes: { steppe: 0.02, 'rock-desert': 0.1, cliffs: 1.2 }, size: [1.2, 5], exponent: 2.4, buried: 0.25, variants: 5, cluster: { wavelength: 180, lo: 0.4, hi: 0.7 }, slope: [0, 2] },
];
void ROCKS;
