// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import { hash2 } from '@ferret/terrain';
import { FIELD } from './config';
import { fieldInfo, fieldBand } from './fields3';
import { PERIMETER, PAVED, HANGARS, FUEL, NISSEN, TOWER, PARKED, inRect, onPavement } from './layout3';
import { GENERATORS3, type PlantData } from './plants3';

/**
 * The hand-placed vegetation: the hedgerows on the borders of the fields (hawthorn and bramble along the line, a tree every few tens of metres, taller where the hedge is old), the boundary hedge and
 * tree line round the airfield, the grass of the airfield's edges (long grass along the fence, the ditches, the hangars' walls and the dispersal's edge, clumps and thistles in the field), and the
 * lone trees of the fields. The module's scatter is a density per biome, flat with distance; this is set by human logic: things grow where they are not cut. Thin instances in tiles of 500 m, each
 * switched on within its own draw distance, drawn with the land's plant material (the wind moves them).
 */
type Kind = 'hedge' | 'oak' | 'ash' | 'elm' | 'poplar' | 'bramble' | 'dock' | 'parsley' | 'long' | 'dried' | 'tuft' | 'rush';
const TILE = 500;
/** how far each kind is drawn (m) */
const RANGE: Record<Kind, number> = { hedge: 1500, oak: 3200, ash: 3200, elm: 3200, poplar: 3200, bramble: 400, dock: 260, parsley: 260, long: 380, dried: 380, tuft: 300, rush: 260 };

export interface VergeStats { instances: Record<string, number>; tilesOn: number; meshesOn: number }

export class Verges {
  private sources = new Map<Kind, PlantData[]>();
  private meshes = new Map<string, BABYLON.Mesh[]>();               // "kind|ti|tj" -> one mesh per variant
  private lists = new Map<string, number[][]>();                      // "kind|ti|tj" -> per variant matrices
  private cols = new Map<string, number[][]>();
  private counts: Record<string, number> = {};
  constructor(private scene: BABYLON.Scene, private mat: BABYLON.Material, private ground: (x: number, z: number) => number, seed = 1944) {
    const mk = (kind: Kind, gen: string, n: number) => this.sources.set(kind, Array.from({ length: n }, (_, v) => GENERATORS3[gen]!(seed, v)));
    mk('hedge', 'hawthorn', 4); mk('oak', 'oak', 3); mk('ash', 'ash', 3); mk('elm', 'elm', 3); mk('poplar', 'poplar', 2); mk('bramble', 'bramble', 3); mk('dock', 'dock', 3); mk('parsley', 'parsley', 3);
    mk('long', 'long-grass', 4); mk('dried', 'dried-tuft', 3); mk('tuft', 'meadow-tuft', 4); mk('rush', 'rush-tuft', 3);
  }
  private add(kind: Kind, x: number, z: number, size: number, yaw: number, tint: number, o: { stretch?: number; sink?: number; y?: number } = {}) {
    const vs = this.sources.get(kind)!, n = vs.length, v = Math.min(n - 1, Math.floor(hash2(Math.floor(x * 3.1), Math.floor(z * 3.1), 91) * n)), ti = Math.floor(x / TILE), tj = Math.floor(z / TILE), key = `${kind}|${ti}|${tj}`;
    let l = this.lists.get(key); if (!l) { l = vs.map(() => []); this.lists.set(key, l); this.cols.set(key, vs.map(() => [])); }
    const y = (o.y ?? this.ground(x, z)) - (o.sink ?? 0.05) * size, sy = size * (o.stretch ?? 1);
    const m = BABYLON.Matrix.Compose(new BABYLON.Vector3(size * 1.0, sy, size * 1.0), BABYLON.Quaternion.RotationYawPitchRoll(yaw, (hash2(Math.floor(z), Math.floor(x), 92) - 0.5) * 0.06, 0), new BABYLON.Vector3(x, y, z));
    l[v]!.push(...m.toArray()); const t = tint, c = this.cols.get(key)![v]!; c.push(t * (0.94 + 0.12 * hash2(Math.floor(x), 3, 93)), t, t * (0.9 + 0.16 * hash2(7, Math.floor(z), 94)), 1);
    this.counts[kind] = (this.counts[kind] ?? 0) + 1;
  }

  /** the hedgerows of the plain: points of a 5 m grid within 3 m of a border between two fields that keep a hedge; none near the airfield or its pavements */
  hedgerows(half = 2300) {
    const STEP = 5, r = (a: number, b: number, s: number) => hash2(Math.floor(a * 7.3), Math.floor(b * 7.3), s);
    for (let gz = -half; gz <= half; gz += STEP) for (let gx = -half; gx <= half; gx += STEP) {
      const x = gx + (r(gx, gz, 11) - 0.5) * STEP, z = gz + (r(gx, gz, 12) - 0.5) * STEP;
      if (fieldBand(x, z) < 16) continue;
      const { cell, border } = fieldInfo(x, z); if (!cell.hedge || border > 2.6) continue;
      // the hedge is thinner at the field's gateway (a gap every ~90 m)
      const gap = hash2(Math.floor((x + z) / 90), Math.floor((x - z) / 90), 13) < 0.1; if (gap) continue;
      const g = this.ground(x, z); if (g < 2.5) continue;
      const old = hash2(cell.id & 0xfff, cell.id >>> 12, 14), s = 2.2 + 1.6 * r(x, z, 15) + 1.4 * old;
      this.add('hedge', x, z, s, r(x, z, 16) * 6.283, 0.88 + 0.28 * r(x, z, 17), { stretch: 0.85 + 0.4 * old });
      if (r(x, z, 18) < 0.26) this.add('bramble', x + (r(x, z, 19) - 0.5) * 4, z + (r(x, z, 20) - 0.5) * 4, 0.8 + r(x, z, 21), r(x, z, 22) * 6.283, 0.9);
      if (r(x, z, 23) < 0.035 + 0.05 * old) {                                   // a hedgerow tree: oak most often, ash, field elm
        const k = r(x, z, 24), kind: Kind = k < 0.5 ? 'oak' : k < 0.8 ? 'ash' : 'elm', h = 11 + 8 * r(x, z, 25);
        this.add(kind, x, z, h, r(x, z, 26) * 6.283, 0.86 + 0.26 * r(x, z, 27), { sink: 0.0 });
      }
    }
  }
  /** lone trees and small copses in the fields (a few per square kilometre, off the borders), and the copse's undergrowth */
  copses(half = 2300) {
    const C = 230, ci = Math.floor(half / C);
    for (let j = -ci; j <= ci; j++) for (let i = -ci; i <= ci; i++) {
      const h = hash2(i, j, 31); if (h > 0.17) continue;
      const cx = (i + 0.2 + 0.6 * hash2(i, j, 32)) * C, cz = (j + 0.2 + 0.6 * hash2(i, j, 33)); const zz = cz * C;
      if (fieldBand(cx, zz) < 40 || this.ground(cx, zz) < 4) continue;
      const wood = h < 0.04, n = wood ? 14 + Math.floor(14 * hash2(i, j, 34)) : 1;
      for (let k = 0; k < n; k++) {
        const a = hash2(i, j * 31 + k, 35) * 6.283, d = wood ? 6 + 28 * Math.sqrt(hash2(i, j * 31 + k, 36)) : 0, x = cx + Math.cos(a) * d, z = zz + Math.sin(a) * d, kk = hash2(i, j * 31 + k, 37);
        const kind: Kind = kk < 0.45 ? 'oak' : kk < 0.7 ? 'ash' : kk < 0.9 ? 'elm' : 'poplar';
        this.add(kind, x, z, 10 + 9 * hash2(i, j * 31 + k, 38), hash2(i, j * 31 + k, 39) * 6.283, 0.84 + 0.3 * hash2(i, j * 31 + k, 40), { sink: 0 });
        if (wood) this.add('hedge', x + (hash2(i, k, 41) - 0.5) * 8, z + (hash2(k, i, 42) - 0.5) * 8, 2 + 2 * hash2(i, k, 43), hash2(i, k, 44) * 6.283, 0.9);
      }
    }
  }
  /** the boundary of the airfield: a hedge just outside the fence all round with a tree line (oaks, ashes, elms; poplars on the east side by the road), a gap at the gate */
  boundary() {
    const [ax, az] = FIELD.from, [bx, bz] = FIELD.to, R = PERIMETER.hedge, ring: Array<[number, number, number]> = [];
    for (let z = az; z <= bz; z += 3.2) ring.push([bx + R, z, 0]);
    for (let i = 0; i <= 60; i++) { const a = (i / 60) * Math.PI; ring.push([bx + Math.cos(a) * R, bz + Math.sin(a) * R, 0]); }
    for (let z = bz; z >= az; z -= 3.2) ring.push([bx - R, z, 1]);
    for (let i = 0; i <= 60; i++) { const a = Math.PI + (i / 60) * Math.PI; ring.push([ax + Math.cos(a) * R, az + Math.sin(a) * R, 1]); }
    let n = 0;
    for (const [x, z, west] of ring) {
      n++; if (Math.abs(x - PERIMETER.gate.x) < 14 && Math.abs(z - PERIMETER.gate.z) < 14) continue;
      const u = hash2(n, 3, 51), x2 = x + (u - 0.5) * 2.4, z2 = z + (hash2(n, 4, 52) - 0.5) * 2.4;
      this.add('hedge', x2, z2, 2.6 + 1.8 * hash2(n, 5, 53), hash2(n, 6, 54) * 6.283, 0.86 + 0.3 * hash2(n, 7, 55), { stretch: 1.0 });
      if (hash2(n, 8, 56) < 0.3) this.add('bramble', x2 + (hash2(n, 9, 57) - 0.5) * 3, z2 + (hash2(n, 10, 58) - 0.5) * 3, 1 + hash2(n, 11, 59), hash2(n, 12, 60) * 6.283, 0.9);
      if (n % 9 === 0 && hash2(n, 13, 61) < 0.8) { const k = hash2(n, 14, 62), kind: Kind = !west && k < 0.4 ? 'poplar' : k < 0.5 ? 'oak' : k < 0.75 ? 'ash' : 'elm'; this.add(kind, x2, z2, kind === 'poplar' ? 17 + 6 * hash2(n, 15, 63) : 12 + 8 * hash2(n, 15, 63), hash2(n, 16, 64) * 6.283, 0.84 + 0.3 * hash2(n, 17, 65), { sink: 0 }); }
    }
    // a belt of poplars and oaks behind the hangars (east) and a copse near the south-west corner
    for (let i = 0; i < 26; i++) this.add(i % 3 === 0 ? 'oak' : 'poplar', 328 + 5 * hash2(i, 1, 71), 250 + i * 8.6 + 3 * hash2(i, 2, 72), (i % 3 === 0 ? 13 : 20) + 5 * hash2(i, 3, 73), hash2(i, 4, 74) * 6.283, 0.86 + 0.26 * hash2(i, 5, 75), { sink: 0 });
  }
  /** the grass of the airfield: kept short on the field, long where the mower does not reach (fence line, ditch banks, hangars' and huts' walls, the dispersal's and apron's edge, round parked aircraft's wheels) */
  verges() {
    const rnd = (a: number, b: number, s: number) => hash2(Math.floor(a * 5.1), Math.floor(b * 5.1), s);
    const along = (x0: number, z0: number, x1: number, z1: number, step: number, wid: number, tag: number, kinds: Kind[]) => {
      const L = Math.hypot(x1 - x0, z1 - z0), n = Math.floor(L / step);
      for (let i = 0; i < n; i++) {
        const t = (i + rnd(i, tag, 1)) / n, x = x0 + (x1 - x0) * t + (rnd(i, tag, 2) - 0.5) * wid, z = z0 + (z1 - z0) * t + (rnd(i, tag, 3) - 0.5) * wid;
        if (onPavement(x, z, 0.4) || HANGARS.some(h => inRect({ x0: h.cx - h.depth / 2, x1: h.cx + h.depth / 2, z0: h.cz - h.span / 2, z1: h.cz + h.span / 2 }, x, z, 0.3))) continue;
        const k = kinds[Math.floor(rnd(i, tag, 4) * kinds.length)]!, big = k === 'dock' || k === 'parsley' || k === 'bramble';
        this.add(k, x, z, big ? 0.9 + 0.7 * rnd(i, tag, 5) : 0.7 + 0.8 * rnd(i, tag, 5), rnd(i, tag, 6) * 6.283, 0.84 + 0.3 * rnd(i, tag, 7), { sink: 0.04 });
      }
    };
    const R = PERIMETER.radius, [ax, az] = FIELD.from, [bx, bz] = FIELD.to;
    // along the fence on the inside (both long sides) and round the ends: dense long grass with docks and parsley
    for (const sx of [-1, 1]) along(40 + sx * (R - 1.5), az, 40 + sx * (R - 1.5), bz, 1.1, 2.6, 100 + sx, ['long', 'long', 'dried', 'dock', 'parsley', 'tuft']);
    for (let i = 0; i < 24; i++) { const a0 = (i / 24) * Math.PI, a1 = ((i + 1) / 24) * Math.PI; for (const [cz, s] of [[bz, 1], [az, -1]] as const) { const r = R - 1.5; along(40 + Math.cos(a0) * r, cz + s * Math.sin(a0) * r, 40 + Math.cos(a1) * r, cz + s * Math.sin(a1) * r, 1.2, 2.4, 200 + i * s, ['long', 'long', 'dried', 'dock', 'tuft']); } }
    // the ditch banks (outside the fence; the ditch lines are at x = 40 +- (inner + 14))
    for (const sx of [-1, 1]) along(40 + sx * (FIELD.inner + 14), az + 20, 40 + sx * (FIELD.inner + 14), bz - 20, 1.0, 4.5, 300 + sx, ['rush', 'rush', 'long', 'dock', 'parsley', 'bramble']);
    // the pavements' edges: a ragged line of tufts, a few docks growing out of the cracks
    const edge = (x0: number, x1: number, z0: number, z1: number, tag: number) => { along(x0, z0, x0, z1, 1.6, 1.4, tag, ['tuft', 'tuft', 'long', 'dried']); along(x1, z0, x1, z1, 1.6, 1.4, tag + 1, ['tuft', 'tuft', 'long', 'dried']); along(x0, z0, x1, z0, 2.0, 1.2, tag + 2, ['tuft', 'long']); along(x0, z1, x1, z1, 2.0, 1.2, tag + 3, ['tuft', 'long']); };
    edge(PAVED.runway.x0 - 0.6, PAVED.runway.x1 + 0.6, PAVED.runway.z0, PAVED.runway.z1, 400);
    edge(PAVED.taxi.x0 - 0.7, PAVED.taxi.x1 + 0.7, PAVED.taxi.z0, PAVED.taxi.z1, 410); edge(PAVED.dispersal.x0, PAVED.dispersal.x1 + 0.7, PAVED.dispersal.z0 - 0.5, PAVED.dispersal.z1 + 0.5, 420);
    edge(PAVED.apron.x0, PAVED.apron.x1 + 0.7, PAVED.apron.z0 - 0.5, PAVED.apron.z1 + 0.5, 430);
    // walls of the buildings
    for (const h of HANGARS) { const x0 = h.cx - h.depth / 2, x1 = h.cx + h.depth / 2, z0 = h.cz - h.span / 2, z1 = h.cz + h.span / 2; along(x1 + 0.5, z0, x1 + 0.5, z1, 1.0, 1.4, 500 + h.cx, ['long', 'dock', 'parsley', 'dried']); along(x0, z0 - 0.6, x1, z0 - 0.6, 1.2, 1.2, 510 + h.cz, ['long', 'dock', 'dried']); along(x0, z1 + 0.6, x1, z1 + 0.6, 1.2, 1.2, 520 + h.cz, ['long', 'dock', 'dried']); }
    for (const n of NISSEN) { const w = n.yaw === 0 ? 4 : n.len / 2, d = n.yaw === 0 ? n.len / 2 : 4; along(n.cx - w - 0.5, n.cz - d, n.cx - w - 0.5, n.cz + d, 1.2, 1.2, 600 + n.cz, ['long', 'dried', 'dock']); along(n.cx + w + 0.5, n.cz - d, n.cx + w + 0.5, n.cz + d, 1.2, 1.2, 610 + n.cz, ['long', 'dried', 'dock']); }
    void TOWER; void FUEL; void PARKED;
    // clumps and thistles out on the field: a hundred and fifty patches of 5-12 tufts, away from the pavements
    for (let i = 0; i < 260; i++) {
      const cx = 40 + (rnd(i, 1, 81) * 2 - 1) * (R - 10), cz = az + rnd(i, 2, 82) * (bz - az); if (onPavement(cx, cz, 14)) continue;
      const n = 4 + Math.floor(8 * rnd(i, 3, 83)), kind: Kind = rnd(i, 4, 84) < 0.5 ? 'long' : rnd(i, 4, 85) < 0.5 ? 'dock' : 'dried';
      for (let k = 0; k < n; k++) { const a = rnd(i, k, 86) * 6.283, d = 4 * Math.sqrt(rnd(i, k, 87)); this.add(kind, cx + Math.cos(a) * d, cz + Math.sin(a) * d, 0.7 + 0.9 * rnd(i, k, 88), a * 3, 0.85 + 0.3 * rnd(i, k, 89), { sink: 0.04 }); }
    }
    // a tidy scatter of short tufts over the whole field, thin (the mown ground is the shader's)
    for (let i = 0; i < 4200; i++) {
      const x = 40 + (rnd(i, 7, 90) * 2 - 1) * (R - 6), z = az + rnd(i, 8, 91) * (bz - az); if (onPavement(x, z, 6)) continue;
      this.add('tuft', x, z, 0.45 + 0.5 * rnd(i, 9, 92), rnd(i, 10, 93) * 6.283, 0.8 + 0.3 * rnd(i, 11, 94), { sink: 0.04 });
    }
  }

  /** make the instance buffers of the tile `key` once (a mesh per variant sharing the source's geometry) */
  private realise(key: string): BABYLON.Mesh[] {
    let ms = this.meshes.get(key); if (ms) return ms;
    const [kind] = key.split('|') as [Kind], vs = this.sources.get(kind)!, l = this.lists.get(key)!, c = this.cols.get(key)!; ms = [];
    vs.forEach((data, v) => {
      if (!l[v]!.length) return;
      const m = new BABYLON.Mesh(`v-${key}-${v}`, this.scene), vd = new BABYLON.VertexData(); vd.positions = data.positions; vd.normals = data.normals; vd.indices = Array.from(data.indices); vd.colors = data.colors; vd.applyToMesh(m);
      m.material = this.mat; m.isPickable = false; m.alwaysSelectAsActiveMesh = false; m.thinInstanceSetBuffer('matrix', new Float32Array(l[v]!), 16, true); m.thinInstanceSetBuffer('instanceColor', new Float32Array(c[v]!), 4, true); m.thinInstanceRefreshBoundingInfo(true);
      m.setEnabled(false); ms!.push(m);
    });
    this.meshes.set(key, ms); return ms;
  }
  /** switch the tiles within each kind's range on and the others off (call every few frames) */
  update(cx: number, cz: number): VergeStats {
    let tiles = 0, on = 0;
    for (const key of this.lists.keys()) {
      const [kind, ti, tj] = key.split('|') as [Kind, string, string], x0 = +ti * TILE, z0 = +tj * TILE, d = Math.hypot(Math.max(x0 - cx, 0, cx - x0 - TILE), Math.max(z0 - cz, 0, cz - z0 - TILE)), want = d < RANGE[kind];
      if (want) { for (const m of this.realise(key)) { if (!m.isEnabled()) m.setEnabled(true); on++; } tiles++; }
      else { const ms = this.meshes.get(key); if (ms) for (const m of ms) if (m.isEnabled()) m.setEnabled(false); }
    }
    return { instances: { ...this.counts }, tilesOn: tiles, meshesOn: on };
  }
  allMeshes(): BABYLON.Mesh[] { return [...this.meshes.values()].flat(); }
  get total() { return Object.values(this.counts).reduce((a, b) => a + b, 0); }
}
