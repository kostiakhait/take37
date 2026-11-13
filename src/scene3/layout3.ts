// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import { FIELD, RUNWAY, TAXI, SPOTS } from './config';

/**
 * The plan of the airfield in the local frame (x east of the centre of the runway, z toward France = south, the sea toward -z). The one place that says where things stand: the pavement
 * meshes, the wear painted on the grass, the buildings, the props, the people and the police car's route all read it. Metres; yaw in degrees, 0 = nose toward -z (north, the take-off direction),
 * 90 = nose toward +x, 180 = nose toward +z.
 */
export type Rect = { x0: number; x1: number; z0: number; z1: number };
export const rect = (cx: number, cz: number, w: number, d: number): Rect => ({ x0: cx - w / 2, x1: cx + w / 2, z0: cz - d / 2, z1: cz + d / 2 });

/** radii (m) of the rounded junctions: concave fillets where a link meets the runway or the taxiway, where the dispersal and the apron meet the taxiway, convex roundings of the free corners; the taxi's lead-on curves */
export const FILLET = { link: 14, apron: 12, corner: 9, lead: 28 };

/** the paved surfaces: concrete runway, the taxiway of tarmac and its links, the dispersal apron along it and the hangar apron */
export const PAVED = {
  runway: { x0: -RUNWAY.half, x1: RUNWAY.half, z0: RUNWAY.z0, z1: RUNWAY.z1 } as Rect,
  taxi: { x0: TAXI.x - TAXI.half, x1: TAXI.x + TAXI.half, z0: TAXI.z0, z1: TAXI.z1 } as Rect,
  links: TAXI.links.map(z => ({ x0: RUNWAY.half - 0.5, x1: TAXI.x - TAXI.half + 0.5, z0: z - 6, z1: z + 6 }) as Rect),
  /** the dispersal: a wide hard apron along the taxiway's east side where the aircraft stand */
  dispersal: { x0: TAXI.x + TAXI.half - 0.5, x1: TAXI.x + TAXI.half + 28, z0: -160, z1: 262 } as Rect,
  /** the hangar apron (in front of the hangars) and the road onto it */
  apron: { x0: TAXI.x + TAXI.half - 0.5, x1: 232, z0: 292, z1: 500 } as Rect,
};

/** hangars: doors face west (toward the apron); `span` runs along z, `depth` along x */
export interface Hangar { id: string; kind: 'arch' | 'gable'; cx: number; cz: number; span: number; depth: number; eave: number; ridge: number }
export const HANGARS: Hangar[] = [
  { id: 'H1', kind: 'arch', cx: 240, cz: 326, span: 38, depth: 44, eave: 4.6, ridge: 11.5 },
  { id: 'H2', kind: 'arch', cx: 232, cz: 372, span: 27, depth: 32, eave: 3.8, ridge: 8.4 },
  { id: 'H3', kind: 'gable', cx: 228, cz: 416, span: 17, depth: 24, eave: 4.2, ridge: 6.8 },
];
/** the control tower (a two-storey watch office with a glazed visual control room), the fuel store, huts */
export const TOWER = { cx: 176, cz: 246, yaw: 270 };
export const FUEL = { cx: 288, cz: 470, w: 38, d: 34 };
export const NISSEN: Array<{ cx: number; cz: number; yaw: number; len: number }> = [
  { cx: 268, cz: 258, yaw: 0, len: 22 }, { cx: 268, cz: 236, yaw: 0, len: 18 }, { cx: 268, cz: 216, yaw: 0, len: 14 }, { cx: 262, cz: 400, yaw: 90, len: 16 },
];
/** the aircraft that stand on the dispersal, nose toward -z by default; the Mustang is the player's */
export interface Parked { id: string; model: string; x: number; z: number; yaw: number; tag?: string; scaleTo?: number }
export const PARKED: Parked[] = [
  { id: 'spit1', model: 'spitfire-mk1', x: 108, z: -118, yaw: -14 },
  { id: 'hurr1', model: 'hurricane-mk1', x: 111, z: -78, yaw: 9 },
  { id: 'hurr2', model: 'hurricane-mk1', x: 109, z: -40, yaw: -6 },
  { id: 'avenger', model: 'avenger', x: 114, z: 4, yaw: 12 },
  { id: 'mustang', model: 'mustang', x: SPOTS.mustang.x - 17, z: 170, yaw: 0, tag: 'player' },
  { id: 'spit2', model: 'spitfire-mk1', x: 108, z: 214, yaw: 10 },
  { id: 'b17', model: 'b17g', x: 222, z: 82, yaw: 270, tag: 'far' },
];
/** the helicopter's place on the runway, kept clear for the other agent's model */
export const R22_SPOT = { x: SPOTS.r22.x, z: SPOTS.r22.z, yaw: SPOTS.r22.yaw, pad: SPOTS.r22.pad };

/** the airfield's fence: a stadium round the flat (radius from the axis), the gate on the east side; the ditch and the hedgerow lie outside it */
export const PERIMETER = { radius: FIELD.inner - 22, hedge: FIELD.inner + 2, ditch: FIELD.inner + 14, gate: { x: 40 + FIELD.inner - 22, z: 560 } };
/** the access road from the gate: where the police car comes from (far end first) and where it stops by the Mustang; the walk from its door to the wing */
export const ROAD: Array<[number, number]> = [[760, 880], [640, 790], [520, 700], [418, 632], [352, 585], [PERIMETER.gate.x, PERIMETER.gate.z], [262, 548], [200, 520], [168, 488], [146, 440], [140, 380], [138, 300], [136, 230], [134, 186]];
export const CAR_STOP = { x: 131, z: 177, yaw: 0 };
export const WALK: Array<[number, number]> = [[CAR_STOP.x - 2.1, CAR_STOP.z - 0.6], [124, 175], [119.5, 172.5]];

/** edge lights and markers: the runway's edge posts every 60 m, the taxiway's blue lights */
export const EDGE_STEP = 60;

export const inRect = (r: Rect, x: number, z: number, pad = 0) => x >= r.x0 - pad && x <= r.x1 + pad && z >= r.z0 - pad && z <= r.z1 + pad;
export const onPavement = (x: number, z: number, pad = 0) => inRect(PAVED.runway, x, z, pad) || inRect(PAVED.taxi, x, z, pad) || inRect(PAVED.dispersal, x, z, pad) || inRect(PAVED.apron, x, z, pad) || PAVED.links.some(r => inRect(r, x, z, pad));
