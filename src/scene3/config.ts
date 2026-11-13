// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import { AIRFIELD, coastX } from '@zeppelin/height';

/**
 * Scene 3, the airfield: every number that places it and shapes it, in one file.
 *
 * The world round it is the air war sample's Channel (examples/airwar: ground, farmland, villages, trees, the sea). Local frame of the scene: metres, x east of the airfield's centre, z toward
 * France as in the sample (the sea is toward -z), y up from the sea level. The runway runs along z; take-off is toward the sea (toward -z, heading 000).
 */

/** the airfield's centre in the Zeppelin zone's own frame: the sample's own airfield site. The land is the helicopter agent's (src/heli_land_height.ts): the zone as it is, with its mountain ring opened to the east into a coast and the sea. */
export const SITE = { x: AIRFIELD.x, z: AIRFIELD.z };
/** how far the airfield lies from the shore, km, measured along its own parallel (east). OPEN QUESTION (owner has not decided); the helicopter land puts the shore at x = 36 km and this is what that gives. */
export const COAST_KM = Math.round((coastX(SITE.z) - SITE.x) / 100) / 10;

/** the runway: concrete, 1100 m by 36 m, along z, threshold 36 (the take-off run is toward -z) */
export const RUNWAY = { z0: -550, z1: 550, half: 18, name: '36' };
/** the parallel taxiway on the east side, its links to the runway (z), and the hard standing along it */
export const TAXI = { x: 96, half: 6.5, z0: -518, z1: 518, links: [-512, -250, 20, 300, 512] as number[] };
/** the field (mown grass, dead flat): a stadium round the line, then the ramp into the countryside */
export const FIELD = { from: [40, -640] as [number, number], to: [40, 640] as [number, number], inner: 290, ramp: 260 };
/** where the Mustang stands (nose to the taxiway's north), the R22's place on the runway, the police car's gate and the walk */
export const SPOTS = {
  mustang: { x: TAXI.x + 28, z: 170, yaw: 180 },
  r22: { x: 0, z: 330, yaw: 0, pad: 9 },
  gate: { x: 330, z: 640 },
};

export interface Weather3 { name: string; description: string; base: string; hour: number; wind: number; windDir: number; cover: number; cumulus: number; visibilityKm: number; /** turns the sun's path about the vertical, degrees */ sunRoll: number }
export const WEATHERS: Record<string, Weather3> = {
  day: { name: 'day', description: 'fair day, light cloud, a fresh breeze', base: 'fair', hour: 13.4, wind: 5.5, windDir: 215, cover: 0.3, cumulus: 0.8, visibilityKm: 30, sunRoll: 135 },
  sunset: { name: 'sunset', description: 'clear evening, a low sun over the sea', base: 'clear', hour: 18.9, wind: 3.5, windDir: 215, cover: 0.12, cumulus: 0.3, visibilityKm: 34, sunRoll: 135 },
};
