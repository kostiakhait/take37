// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
/**
 * The shore of the Dunkirk demo as one function of position and time (PLAN-DUNKIRK D1 and D2): the same for every peer, no Babylon. The ground mesh, the water
 * shader, the soldiers and the ship all read it, so the water meets the sand exactly and a soldier stands on what is drawn.
 *
 * World: x runs along the beach (east), z out to sea (north), y up; the mean sea level is y = 0 and the mean waterline is z = 0 (meandering by a few metres).
 * The beach is 2 km long (x -1000..1000), very flat (1:80 on the foreshore, 1:150 out to a bar and a trough, steepening to deep water), with dunes behind it. The mole
 * is a timber walkway on piles from the dunes at x = 0 out to z = 1040: its east face is the berth.
 */
/** the playing field of scene 2 is 600 m along the beach (x -300..300 about the mole's axis) */
export const BEACH_HALF = 300;
/** the mole: its walkway (half width, deck height above the mean sea level), its span along z, the fender line and the berth on its east side */
/** scene 2: the mole is 250 m long (z0 .. z1 = z0 + 250), the cages stand 125 m and 245 m from its landward end */
export const MOLE = { x: 0, half: 2.5, fender: 0.45, z0: -70, z1: 180, deck: 4.2, rampFrom: -110, pileSpacing: 4 };
export const CAGE_Z = { middle: MOLE.z0 + 125, end: MOLE.z0 + 245 };
/** the ship's centre line at the berth (m east of the mole axis), the berth's middle along z and its length; the bollards stand every 12 m on the deck's east edge */
export const BERTH = { x: MOLE.x + MOLE.half + MOLE.fender + 0.3 + 6.05, z: CAGE_Z.end - 10, length: 118, bollardSpacing: 12 };
/** the tide: half the range (m) and the period (s); a mean level of 0 */
export const TIDE = { amplitude: 1.2, period: 1500 };
/** the water's reference depth for shoaling (deeper than this the waves are as they are in the open sea), m */
export const DEEP = 12;

export const smoothstep = (a: number, b: number, x: number) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
const hash = (ix: number, iz: number) => { let h = (ix * 374761393 + iz * 668265263) | 0; h = (h ^ (h >>> 13)) * 1274126177 | 0; return ((h ^ (h >>> 16)) >>> 0) / 4294967296; };
/** value noise, 0..1 */
export function noise2(x: number, z: number): number {
  const ix = Math.floor(x), iz = Math.floor(z), fx = x - ix, fz = z - iz, ux = fx * fx * (3 - 2 * fx), uz = fz * fz * (3 - 2 * fz);
  return (hash(ix, iz) * (1 - ux) + hash(ix + 1, iz) * ux) * (1 - uz) + (hash(ix, iz + 1) * (1 - ux) + hash(ix + 1, iz + 1) * ux) * uz;
}
export const fbm = (x: number, z: number) => 0.55 * noise2(x, z) + 0.28 * noise2(x * 2.07 + 5.3, z * 2.07 + 1.7) + 0.17 * noise2(x * 4.3 + 9.1, z * 4.3 + 3.1);

/** how far the waterline meanders from z = 0 at x, m */
export const wobble = (x: number) => 8 * Math.sin(x * 0.004) + 4 * Math.sin(x * 0.011 + 1.3);

/** the sand and sea bed along the shore-normal coordinate u (u > 0 seaward), m above the mean sea level: no dunes (those are the land's own business) */
export function profile(u: number): number {
  if (u >= 0) {
    // scene 2: gentle for the first 60 m (the surf and the swash), then steeper, so the mole's end (u = 180) stands in 5 m of water and the steamer floats alongside at low tide
    const base = u <= 60 ? -u / 60 : u <= 180 ? -1 - (u - 60) / 30 : -5 - (u - 180) / 20;
    return base + 0.25 * Math.exp(-(((u - 30) / 15) ** 2));
  }
  return u >= -150 ? -u / 80 : 1.875 + (-150 - u) / 200;
}
/** the height of the sand or of the sea bed at (x, z), m: the beach, the bed, and behind the foreshore the dunes */
export function bed(x: number, z: number): number {
  const u = z + wobble(x), p = profile(u);
  // scene 2: the dunes rise right behind the high-water line so that they are read from where the player starts (up to about 11 m)
  if (u > -170) return p;
  const ramp = smoothstep(-170, -270, u), swell = 0.5 + 0.5 * Math.sin(x * 0.006 + u * 0.004);
  return p + ramp * (2.0 + 9.0 * fbm(x * 0.012, z * 0.012) * (0.6 + 0.4 * swell));
}

/** the tide at game time t (s): m above the mean sea level; `phase` (radians) sets where in the cycle the game starts */
export function tide(t: number, phase = 0): number { return TIDE.amplitude * Math.sin(2 * Math.PI * t / TIDE.period + phase); }
/** the still-water depth over the bed at (x, z), m (negative: dry) */
export const depthAt = (x: number, z: number, level: number) => level - bed(x, z);

/**
 * What a wave's amplitude becomes in water of depth `d` (Green's law, then breaking): the amplitude rises as (DEEP / d)^(1/4) in shallow water, and is held by
 * the depth: a wave of height H breaks at H = 0.8 d (amplitude 0.4 d), softly. In depth 0 nothing is left.
 */
export function shoalAmplitude(d: number, a: number): number {
  if (d <= 0.02) return 0;
  const shoal = Math.min(1.9, Math.max(1, (DEEP / d) ** 0.25)), ae = a * shoal, cap = 0.42 * d;
  return ae / (1 + (ae / cap) ** 4) ** 0.25;
}
/** how close the wave of amplitude `a` is to breaking at depth d: 0 deep, 1 at the break (the picture turns white water by this) */
export function breaking(d: number, a: number): number {
  if (d <= 0.02) return 1;
  const shoal = Math.min(1.9, Math.max(1, (DEEP / d) ** 0.25));
  return Math.min(1, (a * shoal) / (0.42 * d));
}

// ---- the mole ----------------------------------------------------------------------------------------------------------
/** the deck's height above the mean sea level: constant on the mole, and on the ramp that leads up to it from the dunes */
export function deckHeight(z: number): number {
  if (z >= MOLE.z0) return MOLE.deck;
  const g = bed(MOLE.x, MOLE.rampFrom);
  return g + (MOLE.deck - g) * smoothstep(MOLE.rampFrom, MOLE.z0, z);
}
export const onMole = (x: number, z: number) => Math.abs(x - MOLE.x) <= MOLE.half && z >= MOLE.rampFrom && z <= MOLE.z1;
/** the height a walker stands at: the deck on the mole and its ramp, the sand or the sea bed elsewhere */
export function walkHeight(x: number, z: number): number { return onMole(x, z) ? Math.max(deckHeight(z), bed(x, z)) : bed(x, z); }
/** x of the mole's east face (the fender line) and of its west face */
export const FACE_E = MOLE.x + MOLE.half + MOLE.fender, FACE_W = MOLE.x - MOLE.half - MOLE.fender;

/**
 * The swell that bounces back from the mole's faces (the image of the incident sea in the wall: the water at the mirrored point), as a share of the incident
 * height: strongest at the face, gone within about 70 m, only along the mole's span, and weaker in shallow water (the beach takes it).
 */
export function reflectionAt(x: number, z: number): { mirror: number; weight: number } {
  const east = x > FACE_E, west = x < FACE_W;
  if (!east && !west) return { mirror: x, weight: 0 };
  const face = east ? FACE_E : FACE_W, dist = Math.abs(x - face);
  const along = smoothstep(MOLE.rampFrom + 40, MOLE.rampFrom + 140, z) * (1 - smoothstep(MOLE.z1 - 40, MOLE.z1 + 10, z));
  const w = 0.6 * Math.exp(-dist / 55) * along;
  return { mirror: 2 * face - x, weight: w };
}

// ---- the sand's look ---------------------------------------------------------------------------------------------------
/** how wet the sand is at (x, z) now, 0 dry .. 1 saturated: under the water level, and a damp band above it the swash has just left */
export function wetness(x: number, z: number, level: number, swash = 0.35): number {
  const h = bed(x, z);
  if (h <= level) return 1;
  return Math.max(0, 1 - (h - level) / (0.35 + swash));
}
