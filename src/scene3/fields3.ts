// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import { fbm, hash2, noise2 } from '@zeppelin/height';
import { FIELD, SITE } from './config';

/**
 * The patchwork of fields round the airfield: irregular polygons (the cells of a jittered point lattice about 230 m apart, a wandering border by a domain warp, neighbours merged into one big field
 * now and then), each with its crop and its own colour. Pure functions of (x, z): the ground picture paints them (a map over the near 16 km), the hedgerows and the trees follow their borders.
 */
export type Crop = 'pasture' | 'wheat' | 'barley' | 'stubble' | 'ploughed' | 'rape' | 'fallow' | 'hay';
export const CROPS: Crop[] = ['pasture', 'wheat', 'barley', 'stubble', 'ploughed', 'rape', 'fallow', 'hay'];
/** the colour of each crop seen from a distance (sRGB 0..1) and the kind code the ground shader reads (0..1: pasture .1, standing corn .3, stubble/hay .5, ploughed .7, rape .9) */
export const CROP_LOOK: Record<Crop, { rgb: [number, number, number]; kind: number }> = {
  pasture: { rgb: [0.27, 0.40, 0.15], kind: 0.1 }, wheat: { rgb: [0.55, 0.49, 0.21], kind: 0.3 }, barley: { rgb: [0.62, 0.55, 0.26], kind: 0.3 }, stubble: { rgb: [0.55, 0.47, 0.28], kind: 0.5 },
  ploughed: { rgb: [0.31, 0.22, 0.15], kind: 0.7 }, rape: { rgb: [0.60, 0.58, 0.14], kind: 0.9 }, fallow: { rgb: [0.33, 0.39, 0.18], kind: 0.1 }, hay: { rgb: [0.50, 0.46, 0.25], kind: 0.5 },
};
/** the direction of the crop rows on a field is the lattice's: the shader draws rows along this axis, per field offset by the hash in the map's blue */
export const LATTICE = { angle: 0.31, size: 230 };

const sx = (x: number) => x + SITE.x, sz = (z: number) => z + SITE.z;   // the sample's frame
export interface FieldCell { id: number; crop: Crop; hedge: boolean; /** the point that owns the field */ px: number; pz: number }
const cache = new Map<number, FieldCell>();

const S = LATTICE.size;
const warp = (X: number, Z: number): [number, number] => [X + 38 * (fbm(X / 260, Z / 260, 2, 701) - 0.5), Z + 38 * (fbm(X / 260 + 9, Z / 260 + 4, 2, 702) - 0.5)];
/** the point of lattice cell (i, j), and the field it belongs to (a cell may join its neighbour's field) */
function seed(i: number, j: number) {
  const px = (i + 0.12 + 0.76 * hash2(i, j, 703)) * S, pz = (j + 0.12 + 0.76 * hash2(i, j, 704)) * S;
  let oi = i, oj = j; const m = hash2(i, j, 705);
  if (m < 0.16) oi = i + 1; else if (m < 0.30) oj = j + 1; else if (m < 0.38) { oi = i - 1; oj = j - 1; }   // some cells are one field with a neighbour
  return { px, pz, id: (oi + 4000) * 10007 + (oj + 4000) };
}
function cellOf(id: number): FieldCell {
  let c = cache.get(id);
  if (!c) {
    const iu = Math.floor(id / 10007) - 4000, iv = (id % 10007) - 4000, r = hash2(iu, iv, 706), s = seed(iu, iv);
    // the mix of a mixed-farming plain: grass for stock about a third, corn a third, the rest stubble, plough, rape, fallow, hay
    const crop: Crop = r < 0.30 ? 'pasture' : r < 0.46 ? 'wheat' : r < 0.58 ? 'barley' : r < 0.69 ? 'stubble' : r < 0.80 ? 'ploughed' : r < 0.86 ? 'rape' : r < 0.93 ? 'fallow' : 'hay';
    c = { id, crop, hedge: hash2(iu, iv, 707) < (crop === 'pasture' ? 0.92 : 0.78), px: s.px, pz: s.pz };
    cache.set(id, c);
  }
  return c;
}
/** the field at a point and the distance to the nearest border with another field (m, close to exact: half the gap between the nearest seed and the nearest seed of another field) */
export function fieldInfo(x: number, z: number): { cell: FieldCell; border: number } {
  const [X, Z] = warp(sx(x), sz(z)), ci = Math.floor(X / S), cj = Math.floor(Z / S);
  let d1 = 1e18, id1 = 0, d2 = 1e18, p1x = 0, p1z = 0;
  const near: Array<{ d: number; id: number; px: number; pz: number }> = [];
  for (let j = cj - 1; j <= cj + 1; j++) for (let i = ci - 1; i <= ci + 1; i++) { const s = seed(i, j); near.push({ d: Math.hypot(X - s.px, Z - s.pz), id: s.id, px: s.px, pz: s.pz }); }
  near.sort((a, b) => a.d - b.d); d1 = near[0]!.d; id1 = near[0]!.id; p1x = near[0]!.px; p1z = near[0]!.pz;
  for (const n of near) if (n.id !== id1) { d2 = n.d; break; }
  void p1x; void p1z;
  return { cell: cellOf(id1), border: Math.max(0, (d2 - d1) / 2) };
}
export const fieldAt = (x: number, z: number) => fieldInfo(x, z).cell;
export const borderDistance = (x: number, z: number) => fieldInfo(x, z).border;
/** the distance from the field's axis beyond the flat part (negative inside the airfield): fields begin outside the airfield's boundary band */
export function fieldBand(x: number, z: number): number {
  const [ax, az] = FIELD.from, [bx, bz] = FIELD.to, dz = bz - az, t = Math.min(1, Math.max(0, (z - az) / dz));
  return Math.hypot(x - ax - (bx - ax) * t, z - az - dz * t) - FIELD.inner;
}
export { noise2 };

/** the colour of a field at a point: the crop's colour with slow variation, in sRGB 0..1, and the kind code */
export function fieldColour(x: number, z: number): { rgb: [number, number, number]; kind: number; crop: Crop; border: number } {
  const { cell, border } = fieldInfo(x, z), look = CROP_LOOK[cell.crop], X = sx(x), Z = sz(z);
  const k = 0.84 + 0.3 * fbm(X / 48, Z / 48, 2, 711) + 0.1 * (noise2(X / 6, Z / 6, 712) - 0.5), t = hash2(cell.id & 0xffff, cell.id >>> 16, 713), tint = 0.9 + 0.2 * t;
  return { rgb: [Math.min(1, look.rgb[0] * k * tint), Math.min(1, look.rgb[1] * k), Math.min(1, look.rgb[2] * k * (2 - tint))], kind: look.kind, crop: cell.crop, border };
}
