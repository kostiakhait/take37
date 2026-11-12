// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// Numbers of scene 1 in one place: the budget, the cars, the controls, the hidden score weights, the set cameras.

export const BUDGET_START = 15_000_000;
export const TAKE_COST = 1_000_000;
/** the take time limit, s (a take that runs on without a result is spoiled) */
export const TAKE_LIMIT = 240;
/** the street: x of the end line (a car that crosses it has reached the end of the street) and the extent of the set */
export const STREET_END_X = 612;
export const SET_BOUNDS = { x0: -34, x1: 640, halfWidth: 24 };
export const FIXED_DT = 1 / 60;
export const SUBSTEPS = 4;

export type KindId = 'police' | 'corvette' | 'sedan' | 'pickup' | 'minivan' | 'hatchback' | 'coupe' | 'wagon' | 'tanker';
export interface CarKind {
  id: KindId;
  /** glb of the full model, the reduced model and the one for a wreck (art/ or assets/borrowed, as the server mounts them) */
  glb: string; lod1?: string; damaged?: string;
  /** kg, the whole car */ mass: number;
  /** acceleration at low speed, in g */ accel: number;
  /** drag area Cd x A, m^2 */ cdA: number;
  /** m/s: where the engine runs out of power (gearing) */ vmax: number;
  /** the crush work, J, that makes it a wreck (about 55 km/h into a wall) */ wreckJ: number;
  /** litres of fuel in the tank */ fuelL: number;
}
export const CAR_KINDS: Record<KindId, CarKind> = {
  police: { id: 'police', glb: '/assets/borrowed/crown_victoria_cpd87.glb', lod1: '/assets/borrowed/crown_victoria_cpd87_lod1.glb', mass: 1850, accel: 0.52, cdA: 0.85, vmax: 52, wreckJ: 160e3, fuelL: 70 },
  corvette: { id: 'corvette', glb: '/assets/borrowed/corvette_c4_87_conv.glb', lod1: '/assets/borrowed/corvette_c4_87_conv_lod1.glb', mass: 1500, accel: 0.62, cdA: 0.62, vmax: 62, wreckJ: 130e3, fuelL: 70 },
  sedan: { id: 'sedan', glb: '/art/cars/sedan/sedan87.glb', lod1: '/art/cars/sedan/sedan87_lod1.glb', damaged: '/art/cars/sedan/sedan87_damaged.glb', mass: 1450, accel: 0.3, cdA: 0.75, vmax: 42, wreckJ: 110e3, fuelL: 60 },
  pickup: { id: 'pickup', glb: '/art/cars/pickup/pickup87.glb', lod1: '/art/cars/pickup/pickup87_lod1.glb', damaged: '/art/cars/pickup/pickup87_damaged.glb', mass: 1900, accel: 0.28, cdA: 1.1, vmax: 40, wreckJ: 150e3, fuelL: 90 },
  minivan: { id: 'minivan', glb: '/art/cars/minivan/minivan86.glb', lod1: '/art/cars/minivan/minivan86_lod1.glb', damaged: '/art/cars/minivan/minivan86_damaged.glb', mass: 1750, accel: 0.26, cdA: 0.95, vmax: 40, wreckJ: 130e3, fuelL: 75 },
  hatchback: { id: 'hatchback', glb: '/art/cars/hatchback/hatchback85.glb', lod1: '/art/cars/hatchback/hatchback85_lod1.glb', damaged: '/art/cars/hatchback/hatchback85_damaged.glb', mass: 1000, accel: 0.3, cdA: 0.68, vmax: 40, wreckJ: 80e3, fuelL: 45 },
  coupe: { id: 'coupe', glb: '/art/cars/coupe/coupe84.glb', lod1: '/art/cars/coupe/coupe84_lod1.glb', damaged: '/art/cars/coupe/coupe84_damaged.glb', mass: 1250, accel: 0.36, cdA: 0.7, vmax: 46, wreckJ: 100e3, fuelL: 55 },
  wagon: { id: 'wagon', glb: '/art/cars/wagon/wagon82.glb', lod1: '/art/cars/wagon/wagon82_lod1.glb', damaged: '/art/cars/wagon/wagon82_damaged.glb', mass: 1600, accel: 0.27, cdA: 0.9, vmax: 40, wreckJ: 120e3, fuelL: 70 },
  tanker: { id: 'tanker', glb: '/art/tanker/tanker_1987.glb', lod1: '/art/tanker/tanker_1987_lod1.glb', mass: 14000, accel: 0.12, cdA: 6, vmax: 24, wreckJ: 3e6, fuelL: 34000 },
};
export const TRAFFIC_KINDS: KindId[] = ['sedan', 'pickup', 'minivan', 'hatchback', 'coupe', 'wagon'];

/** the actions of the playable part, with a binding per device (the Controls table of PLAN.md section 5) */
export const ACTIONS = {
  steer: { kind: 'axis2' }, look: { kind: 'axis2' },
  gas: { kind: 'button' }, brake: { kind: 'button' }, handbrake: { kind: 'button' }, jump: { kind: 'button' }, lookback: { kind: 'button' },
  horn: { kind: 'button' }, siren: { kind: 'button' }, cut: { kind: 'button' }, pause: { kind: 'button' }, accept: { kind: 'button' },
} as const;
export const BINDINGS = {
  keyboard: {
    gas: [{ key: 'KeyW', label: 'W' }, { key: 'ArrowUp' }], brake: [{ key: 'KeyS', label: 'S' }, { key: 'ArrowDown' }],
    steer: [{ axisKeys: ['KeyA', 'KeyD', 'KeyW', 'KeyS'] as [string, string, string, string] }, { axisKeys: ['ArrowLeft', 'ArrowRight', 'KeyW', 'KeyS'] as [string, string, string, string] }],
    handbrake: [{ key: 'Space', label: 'Space' }], jump: [{ key: 'KeyE', label: 'E' }], lookback: [{ key: 'KeyC', label: 'C' }],
    look: [{ mouseLook: true as const, sensitivity: 1 }], horn: [{ key: 'KeyH', label: 'H' }], siren: [{ key: 'KeyQ', label: 'Q' }],
    cut: [{ key: 'KeyR', label: 'R' }], pause: [{ key: 'Escape', label: 'Esc' }], accept: [{ key: 'Enter', label: 'Enter' }],
  },
  gamepad: {
    gas: [{ pad: 7, label: 'RT' }], brake: [{ pad: 6, label: 'LT' }], steer: [{ padAxes: [0, 1] as [number, number], deadzone: 0.12 }], look: [{ padAxes: [2, 3] as [number, number], deadzone: 0.15 }],
    handbrake: [{ pad: 0, label: 'A' }], jump: [{ pad: 2, label: 'X' }], lookback: [{ pad: 3, label: 'Y' }], horn: [{ pad: 10, label: 'LS' }], siren: [{ pad: 4, label: 'LB' }],
    cut: [{ pad: 8, label: 'Back' }], pause: [{ pad: 9, label: 'Start' }], accept: [{ pad: 0, label: 'A' }],
  },
};

/** weights of the hidden score (the player never sees it) */
export const SCORE = {
  wreckMoving: 100, wreckParked: 60, wreckPolice: 40, wreckVincent: 300,
  /** points per ln(1 + TNT kg) of a blast: sized by the physics of the blast */ blastPerLn: 400,
  /** points per MW-second of fire above 1 MW */ firePerMWs: 4,
  tankerBurnt: 2500, tankerBlast: 1500, pumpBurnt: 350, canopyDown: 600, propane: 500, stationBurnt: 4000, hydrant: 80, prop: 4,
  /** each link of a chain reaction multiplies by this more */ chain: 0.5,
  /** the take is a wrap when its score passes this */ wrapAt: 450,
};

export interface SetCamera { id: string; label: string; pos: [number, number, number]; target: [number, number, number]; fov: number; weight: number }
/** the set cameras along the street, game frame (the player lane is z = -1.7); `edward` is the operator camera, a little off the road at the first block */
export const SET_CAMERAS: SetCamera[] = [
  { id: 'edward', label: 'Edward', pos: [58, 1.6, 7.2], target: [150, 1.2, -1.7], fov: 0.5, weight: 1.35 },
  { id: 'crane', label: 'Crane', pos: [200, 7.5, 7.5], target: [260, 1.2, -1.7], fov: 0.62, weight: 1 },
  { id: 'mid', label: 'Mid street', pos: [340, 2.2, -7.5], target: [430, 1.2, -1.7], fov: 0.58, weight: 1 },
  { id: 'tele', label: 'Long lens', pos: [440, 2.0, 7.8], target: [540, 1.5, -4], fov: 0.3, weight: 1.15 },
  { id: 'station', label: 'Station', pos: [506, 4.2, -5], target: [560, 1.5, -20], fov: 0.7, weight: 1.2 },
  { id: 'end', label: 'End of street', pos: [606, 3.0, 6], target: [540, 1.5, -6], fov: 0.6, weight: 1 },
];
export const FRAME = { aspect: 1.85, margin: 0.92, minDist: 4, maxDist: 320 };
