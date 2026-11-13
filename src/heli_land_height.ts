// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
/**
 * The ground of the helicopter scene: the Zeppelin sample's zone exactly as it is (the 100 x 100 km height function, biomes, lakes, the airfield's flat site), with one addition: the mountain ring is opened to the east
 * into a coast and the sea (the epilogue's sunset sea), about 36 km from the airfield. This module stands in for `./height` of the sample's world files at build time (tools/build_heliview.mjs); the sample is not edited.
 */
import { groundHeight as zGround, groundColour as zColour, LAKES as zLAKES, type Lake, type RGB } from '/D:/REPO/ferret/examples/zeppelin/src/world/height';
export * from '/D:/REPO/ferret/examples/zeppelin/src/world/height';

const sm = (a: number, b: number, x: number) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
/** x of the shoreline at z (m) */
export const coastX = (z: number) => 36000 + 1400 * Math.sin(z / 5200 + 0.7) + 700 * Math.sin(z / 1700 + 2.1);
const open = (x: number, z: number) => sm(25000, 33500, x) * (1 - sm(24000, 31000, Math.abs(z)));

export function groundHeight(x: number, z: number): number {
  const base = zGround(x, z), w = open(x, z);
  if (w <= 0) return base;
  const d = coastX(z) - x;               // metres inland of the shore
  const target = d > 0 ? Math.min(base, d * 0.012 + 0.6 * sm(0, 600, d) + 0) : Math.max(-90, d * 0.02);
  return base + (target - base) * w;
}
export function groundColour(x: number, z: number, h: number, slope: number): RGB {
  const c = zColour(x, z, h, slope), w = open(x, z);
  if (w > 0.05 && h < 9) { const k = sm(9, 1.5, h) * Math.min(1, w * 3); return [c[0] + (0.76 - c[0]) * k, c[1] + (0.70 - c[1]) * k, c[2] + (0.54 - c[2]) * k]; }
  return c;
}

/** the sample's lakes plus a row of big discs along the open coast at the sea's level: the forest's and the sites' rules keep trees and buildings off ground lower than 4 m inside a lake's disc, which is what keeps them out of the surf */
export const LAKES: Lake[] = [...zLAKES, ...Array.from({ length: 9 }, (_, i) => ({ x: 52000, z: -32000 + i * 8000, r: 14000, level: -0.3 }))];
