// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import { Landscape, LAYER_LOOK, type BiomeZone, type LayerLook, type ReliefOp } from '@ferret/terrain';
import { PLATFORM, platformEdgeDistance } from '../config/stage';

/**
 * The land round the set: a dry, golden, rolling plain of the Californian kind, a flat platform under the street, and ranges far away. Everything is a description
 * (`@ferret/terrain`): the height is a pure function of (seed, x, z), so the picture, the collision and every query agree, and no file is needed.
 */

/** dirt roads: polylines (x, z) that leave the platform's ends and climb the hills; width in metres */
export const DIRT_ROADS: Array<{ name: string; width: number; points: Array<[number, number]> }> = [
  { name: 'west', width: 5.5, points: [[-70, 6], [-140, 14], [-230, 30], [-340, -10], [-470, -70], [-620, -20], [-780, 90], [-980, 210], [-1200, 260], [-1450, 400], [-1750, 470]] },
  { name: 'west-north', width: 4.2, points: [[-230, 30], [-250, 120], [-290, 260], [-300, 420], [-240, 600], [-120, 800], [60, 960], [300, 1180], [520, 1420]] },
  { name: 'east', width: 5.5, points: [[678, -6], [760, -12], [880, 18], [1010, 80], [1180, 60], [1380, 130], [1620, 300], [1900, 380], [2300, 360]] },
  { name: 'east-south', width: 4.2, points: [[900, 24], [940, -80], [1010, -250], [1150, -430], [1330, -560], [1500, -800], [1720, -1000]] },
  { name: 'south-ranch', width: 3.6, points: [[240, -70], [250, -150], [220, -260], [260, -420], [380, -560], [520, -690], [700, -820]] },
];

/** a closed polygon round a polyline: `half` metres each side */
function around(points: Array<[number, number]>, half: number): Array<[number, number]> {
  const left: Array<[number, number]> = [], right: Array<[number, number]> = [];
  for (let i = 0; i < points.length; i++) {
    const a = points[Math.max(0, i - 1)], b = points[Math.min(points.length - 1, i + 1)], dx = b[0] - a[0], dz = b[1] - a[1], l = Math.hypot(dx, dz) || 1, nx = -dz / l, nz = dx / l;
    left.push([points[i][0] + nx * half, points[i][1] + nz * half]); right.push([points[i][0] - nx * half, points[i][1] - nz * half]);
  }
  return [...left, ...right.reverse()];
}

/** how the layers look here: dry gold grass, pale baked soil, tan road dirt, warm grey rock */
export const LOOKS: Record<string, LayerLook> = {
  ...LAYER_LOOK,
  'dry-grass': { color: [0.6, 0.46, 0.21], rough: 0.95, grain: 0.7 },
  soil: { color: [0.52, 0.4, 0.28], rough: 0.95, grain: 0.6 },
  gravel: { color: [0.62, 0.55, 0.45], rough: 0.95, grain: 0.8 },
  rock: { color: [0.42, 0.37, 0.31], rough: 0.9, grain: 0.8 },
  scree: { color: [0.46, 0.4, 0.33], rough: 0.9, grain: 0.9 },
  'desert-pavement': { color: [0.66, 0.54, 0.4], rough: 0.95, grain: 0.7 },
  // the ranges are dry: what the climate calls snow above 1650 m is bare pale rock here
  snow: { color: [0.3, 0.26, 0.22], rough: 0.9, grain: 0.7 },
  sand: { color: [0.72, 0.6, 0.42], rough: 0.95, grain: 0.5 },
  // the lot under the set is packed earth, not salt
  'salt-crust': { color: [0.6, 0.48, 0.3], rough: 0.95, grain: 0.6 },
  'salt-polygons': { color: [0.57, 0.45, 0.28], rough: 0.95, grain: 0.7 },
};

const ramp = PLATFORM.rampWidth;
/**
 * The platform: one `set` of a constant level (a grid of four equal heights that covers the set) under a mask of the distance to the street axis, so the ground is the platform's level
 * exactly within `halfWidth` of the axis (a stadium), and eases to the hills over `rampWidth` with no step at the edge.
 */
const platformOp = (): ReliefOp => ({
  op: 'import', origin: [-400, -400], step: 1600, nx: 2, ny: 2, heights: [PLATFORM.level, PLATFORM.level, PLATFORM.level, PLATFORM.level], edge: 0, blend: 'set',
  mask: [{ kind: 'line', points: [PLATFORM.from, PLATFORM.to], inner: PLATFORM.halfWidth, outer: PLATFORM.halfWidth + ramp }],
} as ReliefOp);

/** the relief: broad hills, a second hill system that grows with distance, erosion, far ranges, then the platform on top, flat and at one level */
export function reliefOps(): ReliefOp[] {
  const [ax, az] = PLATFORM.from, [bx, bz] = PLATFORM.to;
  const mid: [number, number] = [(ax + bx) / 2, (az + bz) / 2];
  const ops: ReliefOp[] = [
    { op: 'noise', kind: 'fbm', amplitude: 62, wavelength: 1150, octaves: 4, offset: 0.5, damp: 0.3, warp: { amplitude: 300, wavelength: 800 } },
    { op: 'noise', kind: 'fbm', amplitude: 26, wavelength: 420, octaves: 3, offset: 0, damp: 0.4 },
    { op: 'noise', kind: 'fbm', amplitude: 70, wavelength: 2600, octaves: 4, offset: 0.05, damp: 0.5, mask: [{ kind: 'radial', center: mid, inner: 500, outer: 3200, invert: true }] },
    { op: 'noise', kind: 'ridged', amplitude: 260, wavelength: 5200, octaves: 4, sharpness: 1.6, offset: 0, mask: [{ kind: 'radial', center: mid, inner: 3500, outer: 9000, invert: true }] },
    // ranges on the skyline: north is the great one, a lower one east, a long blue ridge west and south
    { op: 'shape', shape: 'range', points: [[-13000, 13500], [-5000, 12200], [3000, 13000], [11000, 11500], [17000, 12500]], width: 4200, height: 1150, ruggedness: 0.9 },
    { op: 'shape', shape: 'range', points: [[19000, -9000], [20500, 0], [19500, 9000]], width: 3600, height: 900, ruggedness: 0.8 },
    { op: 'shape', shape: 'range', points: [[-19000, 10000], [-20500, 0], [-18500, -9500]], width: 3800, height: 1000, ruggedness: 0.8 },
    { op: 'shape', shape: 'range', points: [[-12000, -15500], [0, -17000], [14000, -15000]], width: 3200, height: 650, ruggedness: 0.7 },
    { op: 'erode', step: 48, iterations: 8, strength: 0.7, talus: 36, block: 64, border: 16, mask: [{ kind: 'radial', center: mid, inner: 1400, outer: 2800 }] },
    // fine relief: gullies and humps a person walks over
    { op: 'noise', kind: 'fbm', amplitude: 3.2, wavelength: 140, octaves: 4, damp: 0.2 },
    { op: 'noise', kind: 'fbm', amplitude: 0.35, wavelength: 18, octaves: 3 },
  ];
  ops.push(platformOp());
  return ops;
}

export function dirtRoadZones(): BiomeZone[] {
  return DIRT_ROADS.map((r) => ({ biome: 'rock-desert', feather: 1.6, polygon: around(r.points, r.width / 2) }));
}

/** the platform as a ground zone: packed earth of the lot (a biome no plant belongs to), a little wider than the flat part so the plants thin out before the edge */
function platformZone(): BiomeZone {
  const [ax, az] = PLATFORM.from, [bx, bz] = PLATFORM.to, r = PLATFORM.halfWidth + 10, poly: Array<[number, number]> = [];
  for (let i = 0; i <= 24; i++) { const a = -Math.PI / 2 + (i / 24) * Math.PI; poly.push([bx + Math.cos(a) * r, bz + Math.sin(a) * r]); }
  for (let i = 0; i <= 24; i++) { const a = Math.PI / 2 + (i / 24) * Math.PI; poly.push([ax + Math.cos(a) * r, az + Math.sin(a) * r]); }
  return { biome: 'salt-flat', feather: 12, polygon: poly };
}

export function makeLandscape(): Landscape {
  return new Landscape({
    spec: { version: 1, seed: 1987, seaLevel: -1e6, relief: reliefOps() } as never,
    climate: { fixed: { temperature: 18, moisture: 0.3 } },
    zones: [platformZone(), ...dirtRoadZones()],
  });
}

/** whether a place is on the flat platform */
export const insidePlatform = (x: number, z: number) => platformEdgeDistance(x, z) <= 0;
