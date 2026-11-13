// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import { Landscape, LAYER_LOOK, type BiomeZone, type LayerLook, type ReliefOp } from '@ferret/terrain';
import { groundHeight as sampleHeight } from '@zeppelin/height';
import { FIELD, SITE } from './config';

/**
 * The ground of scene 3 (`@ferret/terrain`): the landscape of the Zeppelin sample (100 x 100 km: plain, lakes, farmland, forest, a ring of mountains), read at SITE + local and laid in as one `import` grid of the sample's own ground (its plain, its hills
 * inland, its coast and sea bed), finer relief over it, then the airfield: one `set` of a constant level under a mask of the distance to the field's axis, so the ground is the field's
 * level exactly within `FIELD.inner` of the axis and eases into the countryside over `FIELD.ramp`. Drainage ditches are cut along the field's boundary.
 * The height is a pure function of (seed, x, z): the picture, the aeroplane's wheels, the people and the scatter read the same ground.
 */
let fn: ((x: number, z: number) => number) | null = null;
/** the cached ground height of the landscape, set when `makeLandscape` has run */
export const groundOf = (): ((x: number, z: number) => number) => { if (!fn) throw new Error('the landscape of scene 3 is not made yet'); return fn; };

/** the field's level: the sample's ground at the site, rounded to a metre, plus a little so the field is not in a hollow */
export const FIELD_LEVEL = Math.round(sampleHeight(SITE.x + 40, SITE.z) + 1.2);

export const LOOKS: Record<string, LayerLook> = {
  ...LAYER_LOOK,
  grass: { color: [0.30, 0.42, 0.17], rough: 0.95, grain: 0.8 },
  soil: { color: [0.36, 0.28, 0.19], rough: 0.95, grain: 0.7 },
  gravel: { color: [0.52, 0.49, 0.43], rough: 0.95, grain: 0.8 },
  rock: { color: [0.40, 0.38, 0.34], rough: 0.9, grain: 0.8 },
  sand: { color: [0.70, 0.64, 0.48], rough: 0.95, grain: 0.5 },
  'wet-sand': { color: [0.52, 0.47, 0.36], rough: 0.4, grain: 0.4 },
  marram: { color: [0.52, 0.55, 0.32], rough: 0.95, grain: 0.7 },
  shingle: { color: [0.55, 0.52, 0.46], rough: 0.95, grain: 0.9 },
  'salt-crust': { color: [0.30, 0.43, 0.17], rough: 0.95, grain: 0.7 }, 'salt-polygons': { color: [0.32, 0.44, 0.18], rough: 0.95, grain: 0.7 },
  'field-green': { color: [0.34, 0.50, 0.18], rough: 0.95, grain: 0.8 }, 'field-gold': { color: [0.66, 0.56, 0.24], rough: 0.95, grain: 0.8 }, 'field-earth': { color: [0.34, 0.24, 0.15], rough: 0.95, grain: 0.7 },
};

const STEP = 200, HALF = 30000, X1 = 72000, NX = (HALF + X1) / STEP + 1, NZ = (HALF * 2) / STEP + 1;

const lineMask = (points: Array<[number, number]>, inner: number, outer: number, invert = false) => ({ kind: 'line', points, inner, outer, invert }) as never;

export function reliefOps(): ReliefOp[] {
  const heights: number[] = new Array(NX * NZ);
  for (let j = 0; j < NZ; j++) for (let i = 0; i < NX; i++) heights[j * NX + i] = sampleHeight(SITE.x + (-HALF + i * STEP), SITE.z + (-HALF + j * STEP));
  const fieldFar = (extra: number) => [lineMask([FIELD.from, FIELD.to], FIELD.inner + extra, FIELD.inner + extra + 420, true)];
  const ops: ReliefOp[] = [
    // the sample's Channel: plain, hills inland, coast and sea bed
    { op: 'import', origin: [-HALF, -HALF], step: STEP, nx: NX, ny: NZ, heights, edge: 3000 } as ReliefOp,
    // fields and lanes: low swells and the hump of old ridge and furrow, away from the field
    { op: 'noise', kind: 'fbm', amplitude: 2.4, wavelength: 220, octaves: 3, damp: 0.2, mask: fieldFar(40) } as ReliefOp,
    { op: 'noise', kind: 'fbm', amplitude: 0.45, wavelength: 26, octaves: 3, mask: fieldFar(40) } as ReliefOp,
    { op: 'noise', kind: 'fbm', amplitude: 0.1, wavelength: 6, octaves: 2, mask: fieldFar(40) } as ReliefOp,
    // the field: a constant level, exact within `inner` of the axis
    { op: 'import', origin: [-1500, -1500], step: 3000, nx: 2, ny: 2, heights: [FIELD_LEVEL, FIELD_LEVEL, FIELD_LEVEL, FIELD_LEVEL], edge: 0, blend: 'set',
      mask: [lineMask([FIELD.from, FIELD.to], FIELD.inner, FIELD.inner + FIELD.ramp)] } as ReliefOp,
  ];
  // drainage ditches cut a little way outside the flat of the field (1.1 m wide at the bottom, 3 m at the top), along its two long sides
  const ditch = (x: number): ReliefOp => ({ op: 'import', origin: [-1500, -1500], step: 3000, nx: 2, ny: 2, heights: [-0.9, -0.9, -0.9, -0.9], edge: 0, blend: 'add',
    mask: [lineMask([[x, FIELD.from[1] + 20], [x, FIELD.to[1] - 20]], 0.8, 2.6)] } as ReliefOp);
  ops.push(ditch(FIELD.from[0] - FIELD.inner - 14), ditch(FIELD.from[0] + FIELD.inner + 14));
  return ops;
}

/** the biome of the field: the one no species of the plain lists (the field is mown; its edges are dressed by hand, verges3.ts), looking like meadow grass */
export function zones(): BiomeZone[] {
  const [ax, az] = FIELD.from, [bx, bz] = FIELD.to, r = FIELD.inner + 6, poly: Array<[number, number]> = [];
  for (let i = 0; i <= 24; i++) { const a = -Math.PI / 2 + (i / 24) * Math.PI; poly.push([bx + Math.cos(a) * r, bz + Math.sin(a) * r]); }
  for (let i = 0; i <= 24; i++) { const a = Math.PI / 2 + (i / 24) * Math.PI; poly.push([ax + Math.cos(a) * r, az + Math.sin(a) * r]); }
  return [{ biome: 'salt-flat', feather: 14, polygon: poly }];
}

export function makeLandscape(): Landscape {
  const l = new Landscape({
    spec: { version: 1, seed: 1944, seaLevel: 0, relief: reliefOps() } as never,
    climate: { fixed: { temperature: 11, moisture: 0.58 } },
    zones: zones(),
  });
  fn = cached(l);
  return l;
}

/** a 2 m lattice of the height, filled on demand and interpolated (the grass, the people and the wheels ask thousands of times a frame; the relief is a pure function of (x, z)) */
function cached(l: Landscape) {
  const g = l.ground, cell = new Map<number, number>(), K = 2, key = (i: number, j: number) => (i + 40000) * 80000 + (j + 40000);
  const at = (i: number, j: number) => { const k = key(i, j); let v = cell.get(k); if (v === undefined) { v = g.relief.height(i * K, j * K); cell.set(k, v); } return v; };
  return (x: number, z: number) => {
    const u = x / K, v = z / K, i = Math.floor(u), j = Math.floor(v), fu = u - i, fv = v - j;
    return (at(i, j) * (1 - fu) + at(i + 1, j) * fu) * (1 - fv) + (at(i, j + 1) * (1 - fu) + at(i + 1, j + 1) * fu) * fv;
  };
}
