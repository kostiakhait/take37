// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import type { RayCaster, RayHit } from '@ferret/destruction/vehicle';
import { buildRoadCar } from '../game/carspec';
import { glbJson, nodeInfos } from '../game/glbinfo';
import { Sim, type Car } from '../game/sim';
import type { Layout } from '../game/layout';
import { CAR_KINDS } from '../game/config';
import { ROAD, CAR_STOP } from './layout3';
import { FIELD_LEVEL } from './ground3';

/**
 * The police car's drive onto the field: the game's own car simulation (`src/game/sim.ts`: the engine's wheeled assembly with ray-cast wheels, springs, a drivetrain; the police cab's build from `carspec.ts`) on this scene's real ground,
 * following the access road from the far end to its stop beside the Mustang. A small driver steers to the next point of the road and brakes for the stop. The sim has no street here (an empty layout); its ground is the scene's height function.
 */
type V3 = [number, number, number];
const EMPTY: Layout = { statics: [], props: [], slots: [], spawns: { pursuit: [0, 0, 0], player: [0, 0, 0] }, station: { parts: [], fireAnchors: [], fireNodes: [], lot: { min: [0, 0, 0], max: [0, 0, 0] }, origin: [0, 0, 0] }, road: { half: 0, walkTo: 0, walkH: 0 } };

class FieldGround implements RayCaster {
  constructor(private h: (x: number, z: number) => number) {}
  height(x: number, z: number) { return this.h(x, z); }
  cast(o: V3, d: V3, maxDistance: number): RayHit | null {
    if (d[1] > -1e-6) return null;
    const hh = this.h(o[0], o[2]), t0 = (o[1] - hh) / -d[1], px = o[0] + d[0] * t0, pz = o[2] + d[2] * t0, h = this.h(px, pz), t = (o[1] + 0 - h) / -d[1];
    if (t < -1.5 || t > maxDistance) return null;
    const e = 0.6, nx = this.h(px - e, pz) - this.h(px + e, pz), nz = this.h(px, pz - e) - this.h(px, pz + e), l = Math.hypot(nx, 2 * e, nz);
    return { distance: t, normal: [nx / l, 2 * e / l, nz / l], grip: 1 };
  }
}

export async function loadPoliceInfos(bytes: (url: string) => Promise<ArrayBuffer>) { return nodeInfos(glbJson(await bytes(CAR_KINDS.police.glb))); }

export interface PoliceDrive { sim: Sim; car: Car; route: Array<[number, number]>; arrived: boolean; step(dt: number): void; reset(): void; distance(): number }

/** the route: the access road's points smoothed by the same spline the road ribbon is built with (so the car is on the ribbon) */
export function routePoints(): Array<[number, number]> {
  const pts: Array<[number, number]> = [];
  for (let i = 0; i + 1 < ROAD.length; i++) {
    const p0 = ROAD[Math.max(0, i - 1)]!, p1 = ROAD[i]!, p2 = ROAD[i + 1]!, p3 = ROAD[Math.min(ROAD.length - 1, i + 2)]!, n = Math.max(2, Math.round(Math.hypot(p2[0] - p1[0], p2[1] - p1[1]) / 4));
    for (let k = 0; k < n; k++) { const t = k / n, t2 = t * t, t3 = t2 * t, f = (a: number, b: number, c: number, d: number) => 0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3); pts.push([f(p0[0], p1[0], p2[0], p3[0]), f(p0[1], p1[1], p2[1], p3[1])]); }
  }
  pts.push(ROAD[ROAD.length - 1]!); return pts;
}

export function makePoliceDrive(infos: ReturnType<typeof nodeInfos>, ground: (x: number, z: number) => number, cruise = 14): PoliceDrive {
  const sim = new Sim(EMPTY, 3); (sim as unknown as { ground: RayCaster }).ground = new FieldGround(ground);
  const route = routePoints(), build = buildRoadCar('police', infos), yaw0 = Math.atan2(-(route[1]![1] - route[0]![1]), route[1]![0] - route[0]![0]);
  const car = sim.addCar('police', 'player', build, [route[0]![0], ground(route[0]![0], route[0]![1]) + 0.9, route[0]![1]], yaw0); car.occupied = true;
  let idx = 1, arrived = false;
  const total = route.reduce((a, p, i) => (i ? a + Math.hypot(p[0] - route[i - 1]![0], p[1] - route[i - 1]![1]) : 0), 0);
  const drive = (c: Car) => {
    const p = c.veh.pos, rot = c.veh.rot as [number, number, number, number], [qx, qy, qz, qw] = rot;
    const fx = 1 - 2 * (qy * qy + qz * qz), fz = 2 * (qx * qz - qy * qw), fl = Math.hypot(fx, fz) || 1, speed = c.veh.vel[0] * fx / fl + c.veh.vel[2] * fz / fl;
    while (idx < route.length - 1 && Math.hypot(route[idx]![0] - p[0], route[idx]![1] - p[2]) < 7) idx++;
    // look a little ahead along the route, steer to it (positive steer = left; left of the nose is (fz, -fx))
    const j = Math.min(route.length - 1, idx + 2), dx = route[j]![0] - p[0], dz = route[j]![1] - p[2], dl = Math.hypot(dx, dz) || 1;
    const err = ((dx / dl) * (fz / fl) + (dz / dl) * (-fx / fl)), ahead = (dx / dl) * (fx / fl) + (dz / dl) * (fz / fl);
    const want = Math.atan2(err, ahead);
    c.ctl.steer += Math.max(-0.1, Math.min(0.1, Math.max(-1, Math.min(1, want * 1.6)) - c.ctl.steer));
    const remain = Math.hypot(CAR_STOP.x - p[0], CAR_STOP.z - p[2]);
    const target = idx >= route.length - 2 ? Math.max(0, Math.min(cruise, remain * 0.35)) : Math.min(cruise, 5 + Math.max(0, remain - 20) * 0.2);
    const turn = Math.abs(want) > 0.5 ? 6 : cruise, vt = Math.min(target, turn), e = vt - speed;
    if (remain < 2.5) { arrived = true; c.ctl.throttle = 0; c.ctl.brake = 1; } else if (e >= 0) { c.ctl.throttle = Math.min(1, e * 0.5); c.ctl.brake = 0; } else { c.ctl.throttle = 0; c.ctl.brake = Math.min(1, -e * 0.3); }
  };
  car.drive = (c) => drive(c);
  void FIELD_LEVEL;
  return {
    sim, car, route, get arrived() { return arrived; }, step(dt: number) { sim.step(dt); }, distance() { return total; },
    reset() { idx = 1; arrived = false; car.veh.place([route[0]![0], ground(route[0]![0], route[0]![1]) + 0.9, route[0]![1]], [0, Math.sin(yaw0 / 2), 0, Math.cos(yaw0 / 2)] as never); },
  };
}

/** the car's body drawn from the cab's own glb (wheels turn and steer as the sim says); the node names are the art's */
export async function policeBody(scene: BABYLON.Scene, car: Car, shadow: BABYLON.ShadowGenerator | null): Promise<{ update(dt: number): void; root: BABYLON.TransformNode }> {
  const url = CAR_KINDS.police.glb, i = url.lastIndexOf('/'), cont = await BABYLON.SceneLoader.LoadAssetContainerAsync(url.slice(0, i + 1), url.slice(i + 1), scene);
  const inst = cont.instantiateModelsToScene((n) => n, false, { doNotInstantiate: true }), top = inst.rootNodes[0] as BABYLON.TransformNode, holder = new BABYLON.TransformNode('car:police', scene);
  top.rotationQuaternion = BABYLON.Quaternion.Identity(); top.parent = holder; holder.rotationQuaternion = new BABYLON.Quaternion();
  const nodes = new Map<string, BABYLON.TransformNode>(); for (const n of top.getDescendants(false)) if (n instanceof BABYLON.TransformNode) nodes.set(n.name, n);
  const wheels = new Map<string, { node: BABYLON.TransformNode; mesh: BABYLON.TransformNode | null; restN: BABYLON.Quaternion; restM: BABYLON.Quaternion; steer: boolean; angle: number }>();
  for (const [name, n] of nodes) { const m = name.match(/^Wheel_([A-Z0-9]+)$/); if (!m) continue; const mesh = nodes.get(name + '_mesh') ?? null; wheels.set(name, { node: n, mesh, restN: (n.rotationQuaternion ?? BABYLON.Quaternion.Identity()).clone(), restM: mesh ? (mesh.rotationQuaternion ?? BABYLON.Quaternion.Identity()).clone() : BABYLON.Quaternion.Identity(), steer: /^Wheel_F/.test(name), angle: 0 }); }
  for (const mesh of top.getChildMeshes()) { mesh.isPickable = false; mesh.receiveShadows = true; shadow?.addShadowCaster(mesh, false); }
  return {
    root: holder,
    update(dt: number) {
      const p = car.veh.pos, q = car.veh.rot as [number, number, number, number], v = car.veh.vel;
      holder.position.set(p[0], p[1], p[2]); holder.rotationQuaternion!.set(q[0], q[1], q[2], q[3]);
      const steer = car.ctl.steer * 0.5 / (1 + Math.pow(Math.hypot(v[0], v[2]) / 14, 2)) * 1.6;
      for (const w of car.veh.wheels) { const vw = wheels.get(w.spec.id); if (!vw) continue; vw.angle += -w.spin * dt; vw.node.rotationQuaternion = (vw.steer ? BABYLON.Quaternion.RotationAxis(BABYLON.Axis.Y, steer) : BABYLON.Quaternion.Identity()).multiply(vw.restN); if (vw.mesh) vw.mesh.rotationQuaternion = BABYLON.Quaternion.RotationAxis(BABYLON.Axis.Z, vw.angle).multiply(vw.restM); }
    },
  };
}
