// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026

/**
 * Small geometry builder for the airfield's own constructions (pavements, buildings, fences): vertices in world metres, UVs in metres over the texture's tile (so a brick is a brick on every wall),
 * one `Geo` per material, merged into one mesh each. `Frame` places local coordinates (x along the building's width, z along its depth, y up) in the world with a yaw.
 */
export type V3 = [number, number, number];
export type RGB = [number, number, number];
export const WHITE: RGB = [1, 1, 1];

export class Geo {
  pos: number[] = []; nor: number[] = []; uv: number[] = []; col: number[] = []; idx: number[] = [];
  get vertices() { return this.pos.length / 3; }
  /** a quad of four corners (counter-clockwise seen from the side the normal points to), a normal, uvs (u, v in tiles) and a colour */
  quad(p: V3[], n: V3, uv: [number, number][], c: RGB = WHITE) {
    const b = this.pos.length / 3;
    for (let i = 0; i < 4; i++) { this.pos.push(p[i]![0], p[i]![1], p[i]![2]); this.nor.push(n[0], n[1], n[2]); this.uv.push(uv[i]![0], uv[i]![1]); this.col.push(c[0], c[1], c[2], 1); }
    this.idx.push(b, b + 1, b + 2, b, b + 2, b + 3);
  }
  tri(p: V3[], n: V3, uv: [number, number][], c: RGB = WHITE) {
    const b = this.pos.length / 3;
    for (let i = 0; i < 3; i++) { this.pos.push(p[i]![0], p[i]![1], p[i]![2]); this.nor.push(n[0], n[1], n[2]); this.uv.push(uv[i]![0], uv[i]![1]); this.col.push(c[0], c[1], c[2], 1); }
    this.idx.push(b, b + 1, b + 2);
  }
  /** a strip of quads along two edge polylines (left and right, equal length), uv.x across 0..1, uv.y by `vOf(i)` */
  strip(left: V3[], right: V3[], vOf: (i: number) => number, c: RGB | ((i: number, side: 0 | 1) => RGB) = WHITE, width = 1) {
    const b = this.pos.length / 3;
    for (let i = 0; i < left.length; i++) {
      const l = left[i]!, r = right[i]!, cl = typeof c === 'function' ? c(i, 0) : c, cr = typeof c === 'function' ? c(i, 1) : c;
      this.pos.push(l[0], l[1], l[2], r[0], r[1], r[2]); this.nor.push(0, 1, 0, 0, 1, 0); this.uv.push(0, vOf(i), width, vOf(i)); this.col.push(cl[0], cl[1], cl[2], 1, cr[0], cr[1], cr[2], 1);
    }
    for (let i = 0; i + 1 < left.length; i++) { const a = b + i * 2; this.idx.push(a, a + 2, a + 1, a + 1, a + 2, a + 3); }
  }
  merge(o: Geo, f: Frame) {
    const b = this.pos.length / 3;
    for (let i = 0; i < o.pos.length; i += 3) { const w = f.p(o.pos[i]!, o.pos[i + 1]!, o.pos[i + 2]!); this.pos.push(w[0], w[1], w[2]); const n = f.d(o.nor[i]!, o.nor[i + 1]!, o.nor[i + 2]!); this.nor.push(n[0], n[1], n[2]); }
    this.uv.push(...o.uv); this.col.push(...o.col); for (const k of o.idx) this.idx.push(b + k);
  }
  mesh(scene: BABYLON.Scene, name: string, mat: BABYLON.Material, o: { colors?: boolean; freeze?: boolean } = {}): BABYLON.Mesh | null {
    if (!this.idx.length) return null;
    const m = new BABYLON.Mesh(name, scene), vd = new BABYLON.VertexData();
    vd.positions = this.pos; vd.normals = this.nor; vd.uvs = this.uv; vd.indices = this.idx; if (o.colors !== false) vd.colors = this.col; vd.applyToMesh(m);
    m.material = mat; m.useVertexColors = o.colors !== false; m.isPickable = false; m.receiveShadows = true;
    m.refreshBoundingInfo(); if (o.freeze !== false) { m.freezeWorldMatrix(); m.doNotSyncBoundingInfo = true; }
    return m;
  }
}

/** local (x, y, z) to world with a yaw about the vertical (radians, 0 = local z along world z, positive turns toward +x) and an origin */
export class Frame {
  private c: number; private s: number;
  constructor(readonly ox: number, readonly oy: number, readonly oz: number, readonly yaw = 0) { this.c = Math.cos(yaw); this.s = Math.sin(yaw); }
  p(x: number, y: number, z: number): V3 { return [this.ox + x * this.c + z * this.s, this.oy + y, this.oz - x * this.s + z * this.c]; }
  d(x: number, y: number, z: number): V3 { return [x * this.c + z * this.s, y, -x * this.s + z * this.c]; }
}

/** a box in a frame: all six faces (bottom optional); uvs in metres over (tileU, tileV) of the wall and (tileTop) of the roof */
export function box(g: Geo, f: Frame, x0: number, x1: number, y0: number, y1: number, z0: number, z1: number, c: RGB = WHITE, tile: [number, number] = [4, 4], topTile: [number, number] = tile, o: { bottom?: boolean; top?: boolean } = {}) {
  const P = (x: number, y: number, z: number) => f.p(x, y, z), D = (x: number, y: number, z: number) => f.d(x, y, z);
  const wu = (a: number, b: number) => [a / tile[0], b / tile[0]], hv = (a: number, b: number) => [a / tile[1], b / tile[1]];
  const wall = (a: V3, b: V3, n: V3, len: number, xo: number) => g.quad([a, b, [b[0], b[1] + (y1 - y0), b[2]], [a[0], a[1] + (y1 - y0), a[2]]], n, [[xo / tile[0], y0 / tile[1]], [(xo + len) / tile[0], y0 / tile[1]], [(xo + len) / tile[0], y1 / tile[1]], [xo / tile[0], y1 / tile[1]]], c);
  void wu; void hv;
  wall(P(x0, y0, z0), P(x1, y0, z0), D(0, 0, -1), x1 - x0, x0); wall(P(x1, y0, z0), P(x1, y0, z1), D(1, 0, 0), z1 - z0, z0); wall(P(x1, y0, z1), P(x0, y0, z1), D(0, 0, 1), x1 - x0, -x1); wall(P(x0, y0, z1), P(x0, y0, z0), D(-1, 0, 0), z1 - z0, -z1);
  if (o.top !== false) g.quad([P(x0, y1, z0), P(x0, y1, z1), P(x1, y1, z1), P(x1, y1, z0)], D(0, 1, 0), [[x0 / topTile[0], z0 / topTile[1]], [x0 / topTile[0], z1 / topTile[1]], [x1 / topTile[0], z1 / topTile[1]], [x1 / topTile[0], z0 / topTile[1]]], c);
  if (o.bottom) g.quad([P(x0, y0, z0), P(x1, y0, z0), P(x1, y0, z1), P(x0, y0, z1)], D(0, -1, 0), [[0, 0], [1, 0], [1, 1], [0, 1]], c);
}

/** a vertical cylinder (or a cone) of `sides` facets, base at y0 and top at y1 with radii r0, r1 */
export function cylinder(g: Geo, f: Frame, cx: number, cz: number, y0: number, y1: number, r0: number, r1: number, sides: number, c: RGB = WHITE, tile = 2, caps = true) {
  const ring = (y: number, r: number, a: number): V3 => f.p(cx + Math.cos(a) * r, y, cz + Math.sin(a) * r);
  for (let i = 0; i < sides; i++) {
    const a0 = (i / sides) * Math.PI * 2, a1 = ((i + 1) / sides) * Math.PI * 2, am = (a0 + a1) / 2, slope = (r0 - r1) / Math.max(1e-6, y1 - y0), nl = Math.hypot(1, slope);
    const n = f.d(Math.cos(am) / nl, slope / nl, Math.sin(am) / nl), u0 = (a0 / (Math.PI * 2)) * (Math.PI * 2 * Math.max(r0, r1)) / tile, u1 = (a1 / (Math.PI * 2)) * (Math.PI * 2 * Math.max(r0, r1)) / tile;
    g.quad([ring(y0, r0, a0), ring(y0, r0, a1), ring(y1, r1, a1), ring(y1, r1, a0)], n, [[u0, 0], [u1, 0], [u1, (y1 - y0) / tile], [u0, (y1 - y0) / tile]], c);
  }
  if (caps && r1 > 0) for (let i = 0; i < sides; i++) { const a0 = (i / sides) * Math.PI * 2, a1 = ((i + 1) / sides) * Math.PI * 2; g.tri([f.p(cx, y1, cz), ring(y1, r1, a1), ring(y1, r1, a0)], f.d(0, 1, 0), [[0.5, 0.5], [0.5 + 0.5 * Math.cos(a1), 0.5 + 0.5 * Math.sin(a1)], [0.5 + 0.5 * Math.cos(a0), 0.5 + 0.5 * Math.sin(a0)]], c); }
}

/** a horizontal cylinder along the local x axis from x0 to x1 at height yc and z = cz, radius r (a tank, a pipe, a drum on its side) */
export function pipe(g: Geo, f: Frame, x0: number, x1: number, yc: number, cz: number, r: number, sides: number, c: RGB = WHITE, tile = 2) {
  const ring = (x: number, a: number): V3 => f.p(x, yc + Math.sin(a) * r, cz + Math.cos(a) * r);
  for (let i = 0; i < sides; i++) {
    const a0 = (i / sides) * Math.PI * 2, a1 = ((i + 1) / sides) * Math.PI * 2, am = (a0 + a1) / 2, n = f.d(0, Math.sin(am), Math.cos(am));
    g.quad([ring(x0, a0), ring(x1, a0), ring(x1, a1), ring(x0, a1)], n, [[0, (a0 * r) / tile], [(x1 - x0) / tile, (a0 * r) / tile], [(x1 - x0) / tile, (a1 * r) / tile], [0, (a1 * r) / tile]], c);
  }
}

/** a vertical post from the ground at (x, z) up h with a square section w */
export const post = (g: Geo, f: Frame, x: number, z: number, y0: number, h: number, w: number, c: RGB = WHITE) => box(g, f, x - w / 2, x + w / 2, y0, y0 + h, z - w / 2, z + w / 2, c, [2, 2]);

export const mix3 = (a: RGB, b: RGB, k: number): RGB => [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k];
/** a seeded generator (mulberry32) */
export const rnd = (seed: number) => { let s = seed >>> 0 || 1; return () => { s = (s + 0x6d2b79f5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; };
