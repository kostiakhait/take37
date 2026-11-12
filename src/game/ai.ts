// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// Drivers: the villain's AI (a route down the street with variations per take, weaves between traffic, may cut through the station forecourt) and the traffic's (cruise, follow, stop). Pure.
import { qRot } from '@ferret/destruction/vehicle';
import type { Car, Sim } from './sim';
import type { Rng } from './rng';

export const STEER = { kp: 0.7, kd: 0.9 };
const STEER_KP = 0.7, STEER_KD = 0.9;
const clamp = (v: number, a: number, b: number) => Math.max(a, Math.min(b, v));
const wrap = (a: number) => { while (a > Math.PI) a -= 2 * Math.PI; while (a < -Math.PI) a += 2 * Math.PI; return a; };
export const LANES = { player: -1.7, oncoming: 1.7 };

/** the heading of a car on the ground plane, rad from +x toward +z */
export const headingOf = (c: Car) => { const f = qRot(c.veh.rot, [1, 0, 0]); return Math.atan2(f[2], f[0]); };
const speedOf = (c: Car) => { const f = qRot(c.veh.rot, [1, 0, 0]); return c.veh.vel[0] * f[0] + c.veh.vel[2] * f[2]; };

/** steer and pedals toward a point at a speed (pure pursuit); the gain is the steering per radian of heading error */
export function pursue(c: Car, tx: number, tz: number, speed: number, brakeFirst = 0): void {
  // pure pursuit: the curvature that takes the car through the target point, as a wheel angle (bicycle model), then as the steering fraction the sim allows at this speed
  const p = c.veh.pos, h = headingOf(c), dx = tx - p[0], dz = tz - p[2], ld = Math.max(4, Math.hypot(dx, dz));
  const alpha = wrap(Math.atan2(dz, dx) - h), wheelbase = c.build.block ? c.build.block.layout.frontAxle - c.build.block.layout.rearAxle : 3.4;
  const delta = Math.atan((2 * wheelbase * Math.sin(alpha)) / ld);
  const v0 = Math.hypot(c.veh.vel[0], c.veh.vel[2]), limit = 1 / (1 + Math.pow(v0 / 14, 2)), rate = -c.veh.angVel[1];
  const want = clamp(delta / (0.5 * limit) - STEER_KD * rate * 0.3, -1, 1);
  c.ctl.steer += clamp(want - c.ctl.steer, -0.08, 0.08);
  const v = speedOf(c), e = speed - v;
  if (e >= 0) { c.ctl.throttle = clamp(e * 0.6, 0, 1); c.ctl.brake = 0; }
  else { c.ctl.throttle = 0; c.ctl.brake = clamp(-e * 0.25 + brakeFirst, 0, 1); }
}

/** keep a lane at a speed along +x: the lane error asks for a small heading (a few degrees), the steering follows the heading; stable at speed (a cascade, no long look-ahead) */
export function holdLane(c: Car, laneZ: number, speed: number): void {
  const h = headingOf(c), v = speedOf(c), hDes = clamp((laneZ - c.veh.pos[2]) * 0.07, -0.11, 0.11);
  const gain = 1.2 * 25 / Math.max(v, 10);
  c.ctl.steer += clamp(clamp(gain * (hDes - h), -1, 1) - c.ctl.steer, -0.08, 0.08);
  const e = speed - v;
  if (e >= 0) { c.ctl.throttle = clamp(e * 0.6, 0, 1); c.ctl.brake = 0; } else { c.ctl.throttle = 0; c.ctl.brake = clamp(-e * 0.25, 0, 1); }
}

/** the gap to the nearest thing ahead in a lane (m), seen from a car heading `dir` along the street; cars (any state) and solid things count */
export function gapAhead(c: Car, sim: Sim, laneZ: number, dir: 1 | -1, look: number, width = 2.3): { gap: number; speed: number; who: string } {
  const p = c.veh.pos; let gap = look, speed = 99, who = '';
  for (const o of sim.cars) {
    if (o === c) continue;
    const ahead = (o.veh.pos[0] - p[0]) * dir - (c.build.length / 2 + o.build.length / 2);
    if (ahead < -1 || ahead > gap) continue;
    if (Math.abs(o.veh.pos[2] - laneZ) > (width + o.build.width) / 2 - 0.05) continue;
    if (o.role === 'parked' && !o.wrecked && Math.abs(o.veh.pos[2]) > 3.8 && Math.abs(laneZ) < 3) continue;
    gap = Math.max(0, ahead); speed = speedOf(o) * dir * (dir === 1 ? 1 : 1) * 0 + (o.veh.vel[0] * dir); who = o.id;
  }
  for (const pr of sim.props) {
    if (pr.state !== 'whole' || pr.def.cls !== 'anchored' && pr.def.mass < 20) continue;
    const b = pr.def.box, ahead = ((dir === 1 ? b.min[0] : b.max[0]) - p[0]) * dir - c.build.length / 2;
    if (ahead < -1 || ahead > gap) continue;
    if (b.max[2] < laneZ - width / 2 || b.min[2] > laneZ + width / 2) continue;
    if (pr.def.cls === 'knock' && pr.def.mass < 20) continue;
    gap = Math.max(0, ahead); speed = 0; who = pr.id;
  }
  return { gap, speed, who };
}

/** traffic: holds its lane at a cruise speed, slows behind what is ahead, stops for a wreck */
export function trafficDriver(dir: 1 | -1, laneZ: number, cruise: number) {
  return (c: Car, sim: Sim) => {
    if (c.wrecked) { c.ctl.throttle = 0; c.ctl.brake = 0.3; return; }
    const g = gapAhead(c, sim, laneZ, dir, 40 + cruise * 1.5), v = speedOf(c);
    let target = cruise;
    if (g.gap < 40 + cruise) { const allow = Math.max(0, g.gap - 6); const vmaxSafe = Math.sqrt(Math.max(0, g.speed * g.speed * 0 + 2 * 6 * allow)); target = Math.min(cruise, Math.max(vmaxSafe, 0)); }
    pursue(c, c.veh.pos[0] + dir * (7 + 0.4 * v), laneZ + (c.veh.pos[2] - laneZ) * 0, target);
  };
}

export interface VincentPlan {
  /** base cruise speed, m/s */ speed: number;
  /** weave: x positions where he jinks to the other lane, and the quick lane changes' sharpness */ jinks: number[];
  /** the station forecourt route is taken this take */ viaStation: boolean;
  /** x at which he turns into the forecourt */ turnAt: number;
}
export function planVincent(rng: Rng, station: { origin: [number, number, number]; lot: { min: number[]; max: number[] } }): VincentPlan {
  const jinks: number[] = [];
  let x = 70 + rng.range(0, 60);
  while (x < 500) { jinks.push(x); x += rng.range(55, 110); }
  return { speed: rng.range(22, 27), jinks, viaStation: rng.chance(0.5), turnAt: station.lot.min[0] - 14 };
}

/** the villain: down the street in the left lane (he drives like it), weaving round what is ahead, jinking at planned places; a take may send him through the station forecourt */
export function vincentDriver(plan: VincentPlan, station: { islandsX: number[]; frontZ: number; backZ: number; exitX: number }) {
  let lane = LANES.player, laneNow = LANES.player, jinkIdx = 0, jinkUntil = 0, phase: 'street' | 'in' | 'down' | 'across' | 'up' | 'out' = 'street', laneClock = 0;
  const wp: Record<string, [number, number]> = {};
  return (c: Car, sim: Sim, dt: number) => {
    if (c.wrecked) { c.ctl.throttle = 0; c.ctl.brake = 0.2; return; }
    const p = c.veh.pos, v = speedOf(c);
    laneClock -= dt;
    if (phase === 'street') {
      // the route through the forecourt: in at the first gap, down between the islands, across, up the other lane, out
      if (plan.viaStation && p[0] > plan.turnAt && station.islandsX.length >= 2) {
        phase = 'in'; wp.in = [station.islandsX[0]! + 7.5 - 8, station.frontZ - 2]; wp.down = [station.islandsX[0]! + 7, station.backZ + 6]; wp.across = [station.islandsX[1]! - 7, station.backZ + 6]; wp.up = [station.islandsX[1]! - 7, station.frontZ - 3]; wp.out = [station.exitX, -1.7];
      }
      if (jinkIdx < plan.jinks.length && p[0] > plan.jinks[jinkIdx]!) { jinkIdx++; if (laneFree(c, sim, -lane, v)) { jinkUntil = sim.t + 1.8; lane = -lane; laneClock = 1.8; } }
      const gh = gapAhead(c, sim, lane, 1, 110);
      const closing = Math.max(0, v - Math.max(0, gh.speed));
      if (laneClock <= 0) {
        // lane choice: the freer lane wins when what is ahead is closing fast (a gap this much longer is needed to leave the lane he holds)
        const need = gh.gap < 28 + 4.5 * closing || (lane > 0 && gh.gap < 40 + 8 * closing);
        if (need) {
          const other = gapAhead(c, sim, -lane, 1, 400), ttc = (g: { gap: number; speed: number }) => g.gap / Math.max(0.5, v - g.speed);
          // from the oncoming lane he goes back as soon as that is the safer lane; into it only when it is clear for long enough
          const back = lane > 0 && ttc(other) > 1.2 * ttc(gh);
          if (back || (laneFree(c, sim, -lane, v) && other.gap > gh.gap + 15)) { lane = -lane; laneClock = 2.4; } else laneClock = 0.15;
        }
        else laneClock = 0.2;
      }
      const gz = gapAhead(c, sim, p[2], 1, 110), g = gz.gap < gh.gap ? gz : gh;
      let target = plan.speed * (sim.t < jinkUntil ? 0.92 : 1);
      if (g.gap < 110) target = Math.min(target, Math.max(0, g.speed) + Math.sqrt(2 * 5 * Math.max(0, g.gap - 10)));
      laneNow += clamp(lane - laneNow, -2.2 * dt, 2.2 * dt);
      holdLane(c, laneNow, target);
      return;
    }
    const goals: Record<string, [number, number, string]> = { in: [...wp.in!, 'down'], down: [...wp.down!, 'across'], across: [...wp.across!, 'up'], up: [...wp.up!, 'out'], out: [...wp.out!, 'street'] };
    const [gx, gz, next] = goals[phase]!;
    const d = Math.hypot(gx - p[0], gz - p[2]);
    if (d < 6) { phase = next as typeof phase; if (phase === 'street') { lane = LANES.player; jinkIdx = plan.jinks.length; } }
    pursue(c, gx, gz, phase === 'across' ? 9 : 13);
  };
}
/** the lane is clear far enough ahead for a lane change at this speed: the distance the two cars close in about five seconds */
function laneFree(c: Car, sim: Sim, laneZ: number, v: number): boolean {
  const g = gapAhead(c, sim, laneZ, 1, 400);
  return g.gap > 20 + 7 * Math.max(0, Math.max(v, 24) - g.speed);
}
function oncomingBlock(c: Car, sim: Sim, laneZ: number): boolean {
  const look = (Math.max(0, speedOf(c)) + 12) * 3;
  // a car coming the other way in that lane within 45 m, closing
  for (const o of sim.cars) { if (o === c || Math.abs(o.veh.pos[2] - laneZ) > 2) continue; const d = o.veh.pos[0] - c.veh.pos[0]; if (d > -8 && d < look && o.veh.vel[0] < -2) return true; }
  return false;
}
