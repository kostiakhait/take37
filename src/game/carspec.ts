// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// A car of the game as an engine wheeled assembly (@ferret/destruction vehicle + autoparts): parts, crush zones, ray-cast wheels. Pure (no Babylon).
import { buildCar, carVehicle, type CarBlock } from '@ferret/destruction/autoparts';
import { Vehicle, GRAVITY } from '@ferret/destruction/vehicle';
import { Assembly } from '@ferret/destruction/assembly';
import { makePart } from '@ferret/destruction/part';
import { makeCrushZone, crushModel } from '@ferret/destruction/crush';
import { glassModel } from '@ferret/destruction/glass';
import { linkHolds } from '@ferret/destruction/assembly';
import type { NodeInfo } from '@ferret/destruction/autoparts';
import type { Vec3 } from '@ferret/destruction/types';
import { CAR_KINDS, type KindId } from './config';

export interface CarBuild { veh: Vehicle; block: CarBlock | null; kind: KindId; length: number; width: number; height: number; wheelRadius: number }

/** a road car from the bounds of its nodes (glbinfo.nodeInfos) */
export function buildRoadCar(kind: KindId, infos: NodeInfo[]): CarBuild {
  const k = CAR_KINDS[kind];
  const block = buildCar({ name: kind, mass: k.mass, nodes: infos });
  const r = block.wheels[0]!.radius, drivers = block.wheels.filter((w) => w.drive).length;
  // torque at the driven wheels for the acceleration the kind is given (the engine's own default is a quarter of g)
  const driveTorque = (k.accel * GRAVITY * k.mass * r) / drivers;
  const veh = carVehicle(block, { brittle: glassModel }, { driveTorque });
  const L = block.layout;
  return { veh, block, kind, length: L.bodyMax[0] - L.bodyMin[0], width: L.bodyMax[2] - L.bodyMin[2], height: L.bodyMax[1], wheelRadius: r };
}

/**
 * The fuel tanker as one assembly: the tractor and the loaded semitrailer are one chassis box (its true length and width from the model), six wheel rays (steer axle and two drive axles under the tractor
 * and the trailer tandem). The tank is a part of its own so that it can be struck and lose its fuel (fire.ts).
 */
export function buildTanker(infos: NodeInfo[]): CarBuild {
  const k = CAR_KINDS.tanker;
  const all = infos.find((n) => n.name === 'Tanker') ?? infos.reduce((a, n) => ({ ...a, min: [Math.min(a.min[0], n.min[0]), 0, Math.min(a.min[2], n.min[2])] as Vec3, max: [Math.max(a.max[0], n.max[0]), Math.max(a.max[1], n.max[1]), Math.max(a.max[2], n.max[2])] as Vec3 }), { name: 'x', min: [1e9, 0, 1e9] as Vec3, max: [-1e9, 0, -1e9] as Vec3 });
  const size: Vec3 = [all.max[0] - all.min[0], all.max[1] - 0.35, all.max[2] - all.min[2]];
  const asm = new Assembly('Chassis');
  const tankLoad = 26000, dry = k.mass;                    // fuel 34 m3 x 0.74 = about 25 t plus the truck 14 t
  const mass = dry + tankLoad;
  const chassis = makePart({ id: 'Chassis', substance: 'steel-sheet', size, thickness: 0.006, mass });
  const cx = (all.min[0] + all.max[0]) / 2;
  asm.add(chassis, [cx - 0.5, 1.0, 0]);
  const wheels: { id: string; mount: Vec3; radius: number; width: number; steer: boolean; drive: boolean }[] = [];
  const hw = 1.0;
  const axles: [string, number, boolean, boolean][] = [['F', 2.0, true, false], ['R1', -1.8, false, true], ['T1', -8.0, false, false], ['T2', -9.4, false, false]];
  for (const [n, x, steer, drive] of axles) for (const [s, z] of [['L', -hw], ['R', hw]] as [string, number][]) {
    const id = `Wheel_${n}${s}`;
    asm.add(makePart({ id, kind: 'rigid', size: [1.05, 1.05, 0.3], mass: 90 }), [x, 0.52, z]);
    asm.join(id, 'Chassis', 'bolt', linkHolds(800e6, 84.3e-6, 10));
    wheels.push({ id, mount: [x, 0, z], radius: 0.52, width: 0.3, steer, drive });
  }
  const zone = (id: string, axis: Vec3, w: number, h: number, d: number) => makeCrushZone({ id, axis, width: w, height: h, dMax: d, thickness: 0.006, yieldStrength: 250e6 });
  const veh = new Vehicle({
    assembly: asm, chassis: 'Chassis', wheels, centers: { Chassis: [cx, 0.35 + size[1] / 2, 0] }, model: crushModel,
    zones: { Chassis: [zone('front', [-1, 0, 0], size[2], size[1], 1.4), zone('rear', [1, 0, 0], size[2], size[1], 1.0), zone('left', [0, 0, 1], size[0], size[1], 0.35), zone('right', [0, 0, -1], size[0], size[1], 0.35), zone('roof', [0, -1, 0], size[0], size[2], 0.2)] },
    driveTorque: (k.accel * GRAVITY * mass * 0.52) / 2,
  });
  return { veh, block: null, kind: 'tanker', length: size[0], width: size[2], height: all.max[1], wheelRadius: 0.52 };
}

/**
 * The police cab (assets/borrowed/crown_victoria_cpd87.glb, art/cars/police): where the driver's eyes are and where the steering wheel is, in the car's frame (x forward, y up, z toward the driver's side).
 * The wheel is the node 'SteeringWheel': its origin is the hub on the column axis, it turns about `axis` (from the dash toward the driver).
 */
export const POLICE_CAB = {
  eye: [-0.15, 1.13, 0.37] as Vec3,
  /** where the head goes when the driver looks back (C): toward the middle and up, over the bench's back; the eye itself sits 0.2 m in front of the head restraint, which fills a straight turn of the head (not yet used by view.ts) */
  lookBackEye: [-0.10, 1.20, 0.10] as Vec3,
  wheel: { node: 'SteeringWheel', hub: [0.25, 0.80, 0.37] as Vec3, axis: [-0.6691, 0.7431, 0] as Vec3, radius: 0.19, lock: 3.0 * Math.PI },
};
