// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// The simulation of scene 1 (no Babylon): cars on the engine's wheeled assembly (ray-cast wheels, crush zones, parts that come off), the street's solid things, props that are knocked or broken,
// debris, damage and wrecks, and a stream of events for the score, the take and the view. The fixed step is 1/60 s with 4 sub-steps for the wheels.
import { Vehicle, collideCars, hullContact, qAxisAngle, qRot, qConj, type RayCaster, type RayHit, type StrikeResult } from '@ferret/destruction/vehicle';
import type { Vec3, Quat } from '@ferret/destruction/types';
import { CAR_KINDS, SUBSTEPS, type KindId } from './config';
import type { CarBuild } from './carspec';
import type { Box, Layout, PropDef } from './layout';
import { Rng } from './rng';

export type Role = 'player' | 'vincent' | 'traffic' | 'parked' | 'tanker';
export interface Controls { throttle: number; brake: number; steer: number }

export interface Car {
  id: string; kind: KindId; role: Role; build: CarBuild; veh: Vehicle;
  /** what the driver (the player's input or an AI) asks for; `steer` is -1 right .. +1 left */ ctl: Controls;
  /** an AI that fills `ctl` each step */ drive?: (car: Car, sim: Sim, dt: number) => void;
  /** accumulated crush and fracture work over what makes it a wreck, 0..1 and more */ damage: number;
  wrecked: boolean; /** the model that shows it: 0 whole, 1 damaged */ shown: 0 | 1;
  /** who last hit it, and when */ hitBy: string | null; hitAt: number;
  /** it started moving by itself or was parked */ parkedAt?: Vec3; occupied: boolean; ejected: boolean;
  fuelKg: number;
}
export interface Debris { id: number; ref: string; pos: Vec3; vel: Vec3; rot: Quat; ang: Vec3; half: Vec3; mass: number; resting: boolean; age: number; node?: string; kind: string }
export interface Prop {
  def: PropDef; id: string; state: 'whole' | 'down' | 'gone'; capacityJ: number; knocked: boolean;
  /** station parts: what they are */ station?: { fuelL: number; burnable: boolean; explosive: boolean; supports?: string; lit: boolean };
}
export type SimEvent =
  | { t: number; type: 'impact'; a: string; b: string; at: Vec3; speed: number; energy: number }
  | { t: number; type: 'detach'; car: string; part: string; at: Vec3 }
  | { t: number; type: 'wreck'; car: string; role: Role; kind: KindId; at: Vec3; depth: number; cause: string | null }
  | { t: number; type: 'prop'; id: string; kind: string; at: Vec3; how: 'knocked' | 'broken' | 'fell'; depth: number }
  | { t: number; type: 'blast'; id: string; at: Vec3; tnt: number; depth: number; what: string }
  | { t: number; type: 'ignite'; id: string; at: Vec3; power: number; what: string; depth: number }
  | { t: number; type: 'burning'; id: string; at: Vec3; power: number; what: string; dt: number }
  | { t: number; type: 'out'; id: string; what: string }
  | { t: number; type: 'spill'; id: string; at: Vec3; kg: number }
  | { t: number; type: 'collapse'; id: string; at: Vec3; depth: number };

const G = 9.81;
/** energy that a prop of this kind absorbs at its base before it gives way, J (a cast-iron hydrant's bolts, a pole's section, a post's weld) */
const PROP_CAPACITY: Record<string, number> = { Hydrant: 9000, UtilityPole: 40000, LampAcorn: 14000, TrafficLight: 16000, PhoneBooth: 4500, Meter: 1800, Mailbox: 2600 };

const dot = (a: Vec3, b: Vec3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const sub = (a: Vec3, b: Vec3): Vec3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const add = (a: Vec3, b: Vec3): Vec3 => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const mul = (a: Vec3, k: number): Vec3 => [a[0] * k, a[1] * k, a[2] * k];
const len = (a: Vec3) => Math.hypot(a[0], a[1], a[2]);
const cross = (a: Vec3, b: Vec3): Vec3 => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const mid = (b: Box): Vec3 => [(b.min[0] + b.max[0]) / 2, (b.min[1] + b.max[1]) / 2, (b.min[2] + b.max[2]) / 2];

/** the ground of the set: the road, the sidewalk step, the forecourt; every ray finds a flat floor at the height under its start */
export class StreetGround implements RayCaster {
  constructor(private road: Layout['road']) {}
  height(_x: number, z: number): number { const a = Math.abs(z); return a > this.road.half && a <= this.road.walkTo ? this.road.walkH : 0; }
  cast(o: Vec3, d: Vec3, maxDistance: number): RayHit | null {
    if (d[1] > -1e-6) return null;
    const h = this.height(o[0], o[2]), t = (o[1] - h) / -d[1];
    if (t < 0 || t > maxDistance) return null;
    return { distance: t, normal: [0, 1, 0], grip: Math.abs(o[2]) > this.road.walkTo + 6 ? 0.7 : 1 };
  }
}

/** a car's hull box in the world against an axis-aligned box: the separating axes test; the normal points from the box to the car */
export function hullVsBox(v: Vehicle, b: Box): { normal: Vec3; depth: number; point: Vec3 } | null {
  const h = v.hull(), c = v.toWorld(h.center);
  const ax: Vec3[] = [qRot(v.rot, [1, 0, 0]), qRot(v.rot, [0, 1, 0]), qRot(v.rot, [0, 0, 1])];
  const e: Vec3 = [h.size[0] / 2, h.size[1] / 2, h.size[2] / 2], bc = mid(b), be: Vec3 = [(b.max[0] - b.min[0]) / 2, (b.max[1] - b.min[1]) / 2, (b.max[2] - b.min[2]) / 2];
  const d = sub(c, bc);
  const unit: Vec3[] = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
  const axes: Vec3[] = [...unit, ...ax];
  for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) { const x = cross(unit[i]!, ax[j]!); const l = len(x); if (l > 1e-6) axes.push(mul(x, 1 / l)); }
  let best = Infinity, bestAxis: Vec3 = [0, 1, 0];
  for (const a of axes) {
    const ra = e[0] * Math.abs(dot(ax[0]!, a)) + e[1] * Math.abs(dot(ax[1]!, a)) + e[2] * Math.abs(dot(ax[2]!, a));
    const rb = be[0] * Math.abs(a[0]) + be[1] * Math.abs(a[1]) + be[2] * Math.abs(a[2]);
    const dist = dot(d, a), ov = ra + rb - Math.abs(dist);
    if (ov <= 0) return null;
    if (ov < best) { best = ov; bestAxis = dist >= 0 ? a : mul(a, -1); }
  }
  // the contact point: the car's hull corner deepest against the normal
  let pt: Vec3 = c, m = Infinity;
  for (let i = 0; i < 8; i++) {
    const p = v.toWorld([h.center[0] + (i & 1 ? 0.5 : -0.5) * h.size[0], h.center[1] + (i & 2 ? 0.5 : -0.5) * h.size[1], h.center[2] + (i & 4 ? 0.5 : -0.5) * h.size[2]]);
    const s = dot(p, bestAxis); if (s < m) { m = s; pt = p; }
  }
  return { normal: bestAxis, depth: best, point: pt };
}

export class Sim {
  t = 0; tick = 0;
  cars: Car[] = []; props: Prop[] = []; debris: Debris[] = []; events: SimEvent[] = [];
  readonly ground: StreetGround;
  readonly rng: Rng;
  /** things that stand in the way and are not props: the buildings */
  statics: Box[];
  private nextDebris = 1;
  /** the entity ids that became active (wreck, blast, fire) with the chain depth and the time: the chain reactions */
  readonly active = new Map<string, { depth: number; t: number }>();
  /** extra hooks: the fire module sees each hit */
  onStrike: ((car: Car, s: StrikeResult, at: Vec3, other: string, speed: number) => void) | null = null;
  onStep: ((dt: number) => void)[] = [];

  constructor(readonly layout: Layout, seed: number) {
    this.ground = new StreetGround(layout.road); this.statics = layout.statics; this.rng = new Rng(seed);
    for (const p of layout.props) this.props.push({ def: p, id: p.id, state: 'whole', capacityJ: PROP_CAPACITY[p.kind] ?? 0, knocked: false });
    for (const s of layout.station.parts) {
      const cls: PropDef['cls'] = /^(Bin|NewsBox|IceChest|OilRack|TyreStack|AirStand|PropaneCage)/.test(s.id) ? 'knock' : 'anchored';
      const cap = /^CanopyColumn/.test(s.id) ? 250000 : /^Pump/.test(s.id) ? 7000 : /^Canopy$/.test(s.id) ? 1e12 : /^(Lamp|PriceSign|SignPost|VentPipes)/.test(s.id) ? 12000 : 3000;
      this.props.push({ def: { id: s.id, kind: s.id.replace(/_\d+$/, ''), mass: s.mass, box: s.box, cls }, id: s.id, state: 'whole', capacityJ: cap, knocked: false, station: { fuelL: s.fuelL, burnable: s.burnable, explosive: s.explosive, supports: s.supports, lit: s.lit } });
    }
  }

  emit(e: SimEvent) { this.events.push(e); }
  drain(): SimEvent[] { const e = this.events; this.events = []; return e; }
  car(id: string) { return this.cars.find((c) => c.id === id); }
  prop(id: string) { return this.props.find((p) => p.id === id); }

  addCar(id: string, role: Role, build: CarBuild, origin: Vec3, yaw: number): Car {
    const k = CAR_KINDS[build.kind];
    const c: Car = { id, kind: build.kind, role, build, veh: build.veh, ctl: { throttle: 0, brake: 0, steer: 0 }, damage: 0, wrecked: false, shown: 0, hitBy: null, hitAt: -99, occupied: false, ejected: false, fuelKg: k.fuelL * 0.74 };
    c.veh.place(origin, qAxisAngle([0, 1, 0], yaw));
    if (role === 'parked') { c.parkedAt = origin; c.ctl.brake = 0; }
    this.cars.push(c); return c;
  }

  /** the chain depth of an effect caused by `cause` now: one more than the cause if it was itself active in the last seconds, else 0 */
  depthOf(cause: string | null): number {
    if (!cause) return 0;
    const a = this.active.get(cause);
    return a && this.t - a.t < 8 ? a.depth + 1 : 0;
  }
  markActive(id: string, depth: number) { this.active.set(id, { depth, t: this.t }); }

  step(dt: number) {
    this.t += dt; this.tick++;
    const sub = dt / SUBSTEPS;
    for (const c of this.cars) {
      const v = c.veh;
      if (c.drive) c.drive(c, this, dt);
      if (c.role === 'parked' && !c.wrecked) { const sp = len(v.vel); c.ctl.brake = sp > 0.05 || len(v.angVel) > 0.05 ? 1 : 0; if (sp < 0.05) c.ctl.brake = 0; }
      else if (c.wrecked) c.ctl.brake = 0.5, c.ctl.throttle = 0;
      this.drivingForces(c, dt);
      for (let i = 0; i < SUBSTEPS; i++) { v.controls = { throttle: c.ctl.throttle * this.powerFactor(c), brake: c.ctl.brake, steer: c.ctl.steer * this.steerLimit(c) }; v.step(sub, this.ground); }
    }
    this.collide();
    this.stepDebris(dt);
    for (const h of this.onStep) h(dt);
    this.updateDamage();
  }

  private powerFactor(c: Car): number {
    const k = CAR_KINDS[c.kind], fwd = qRot(c.veh.rot, [1, 0, 0]), v = dot(c.veh.vel, fwd);
    if (c.ctl.throttle >= 0) return Math.max(0, 1 - Math.pow(Math.max(0, v) / k.vmax, 3)) * Math.min(1, Math.max(0.5, 1.1 - 0.04 * Math.max(0, v - 5))) * (1 / (1 + 14 * Math.max(0, Math.abs(c.veh.angVel[1]) - 0.08)));
    return Math.max(0, 1 - Math.pow(Math.max(0, -v) / 8, 2)) * 0.6;
  }
  /** the steering lock shrinks with speed (the lateral grip, not the wheel, is what a driver can use) */
  private steerLimit(c: Car): number { const v = len(c.veh.vel); return 1 / (1 + Math.pow(v / 14, 2)); }

  /** air drag, rolling resistance and engine braking as forces on the body; they keep the car's speed finite */
  private drivingForces(c: Car, _dt: number) {
    const v = c.veh, sp = len(v.vel), k = CAR_KINDS[c.kind];
    if (v.sleeping || sp < 0.15) return;
    const F = 0.5 * 1.2 * k.cdA * sp * sp + 0.012 * v.mass * G + (c.ctl.throttle <= 0 ? 0.015 * v.mass * G : 0);
    v.pushForce(mul(v.vel, -F / sp));
  }

  // ---- contacts ----
  private collide() {
    const cs = this.cars;
    for (let i = 0; i < cs.length; i++) {
      const a = cs[i]!;
      if (a.veh.sleeping && a.role === 'parked') { /* a sleeping car is woken by a hit on it */ }
      for (let j = i + 1; j < cs.length; j++) {
        const b = cs[j]!;
        if (a.veh.sleeping && b.veh.sleeping) continue;
        if (Math.abs(a.veh.pos[0] - b.veh.pos[0]) > 12 || Math.abs(a.veh.pos[2] - b.veh.pos[2]) > 12) continue;
        const wasA = len(a.veh.vel), wasB = len(b.veh.vel);
        const r = collideCars(a.veh, b.veh, this.tick, i, j, 0.12);
        if (r && r.speed > 1.2) {
          a.hitBy = b.id; a.hitAt = this.t; b.hitBy = a.id; b.hitAt = this.t;
          const at = r.a ? a.veh.pos : b.veh.pos, e = 0.5 * (a.veh.mass * b.veh.mass / (a.veh.mass + b.veh.mass)) * r.speed * r.speed;
          this.emit({ t: this.t, type: 'impact', a: a.id, b: b.id, at: [...at] as Vec3, speed: r.speed, energy: e });
          if (r.a) this.afterStrike(a, r.a, b.id, r.speed); if (r.b) this.afterStrike(b, r.b, a.id, r.speed);
          void wasA; void wasB;
        }
      }
      if (a.veh.sleeping) continue;
      this.collideStatics(a);
      this.collideProps(a);
    }
  }
  private afterStrike(c: Car, s: StrikeResult, other: string, speed: number) {
    for (const id of s.detached) this.emit({ t: this.t, type: 'detach', car: c.id, part: id, at: [...c.veh.pos] as Vec3 });
    this.spawnDetached(c);
    this.onStrike?.(c, s, [...c.veh.pos] as Vec3, other, speed);
  }
  private seenDetached = new Map<string, number>();
  private spawnDetached(c: Car) {
    const done = this.seenDetached.get(c.id) ?? 0, bodies = c.veh.bodies;
    for (let i = done; i < bodies.length; i++) {
      const b = bodies[i]!;
      this.debris.push({ id: this.nextDebris++, ref: c.id, node: b.id, pos: [...b.position] as Vec3, vel: add(b.velocity, [this.rng.range(-1.5, 1.5), this.rng.range(1, 4), this.rng.range(-1.5, 1.5)]), rot: [...b.rotation] as Quat, ang: [this.rng.range(-6, 6), this.rng.range(-6, 6), this.rng.range(-6, 6)], half: [Math.max(0.05, b.size[0] / 2), Math.max(0.05, b.size[1] / 2), Math.max(0.05, b.size[2] / 2)], mass: b.mass, resting: false, age: 0, kind: 'part' });
    }
    this.seenDetached.set(c.id, bodies.length);
  }

  /** a car against a thing that does not move: impulse with infinite mass, friction, the car takes the hit's damage */
  private resolveRigid(c: Car, n: Vec3, depth: number, pt: Vec3, otherId: string, restitution = 0.1, otherMass = 1e6, mu = 0.5): number {
    const v = c.veh, vrel = v.velocityAt(pt), vn = dot(vrel, n);
    c.veh.pos = add(v.pos, mul(n, Math.min(depth, 0.6)));
    if (vn >= 0) return 0;
    const r = sub(pt, v.pos), rn = cross(r, n), k = dot(cross(v.invInertia(rn), r), n);
    const j = (-(1 + restitution) * vn) / (1 / v.mass + k);
    v.applyImpulse(mul(n, j), pt);
    const vt = sub(vrel, mul(n, vn)), vtl = len(vt);
    if (vtl > 1e-3) { const jt = Math.min(mu * j, (vtl * v.mass) / 2); v.applyImpulse(mul(vt, -jt / vtl), pt); }
    const speed = -vn;
    if (speed > 1.2) {
      const s = v.strike({ point: pt, normal: n, speed, otherMass: otherMass, restitution, step: this.tick, entity: this.cars.indexOf(c) });
      c.hitBy = otherId; c.hitAt = this.t;
      this.emit({ t: this.t, type: 'impact', a: c.id, b: otherId, at: [...pt] as Vec3, speed, energy: 0.5 * Math.min(v.mass, otherMass) * speed * speed });
      this.afterStrike(c, s, otherId, speed);
    }
    return speed;
  }
  private collideStatics(c: Car) {
    const p = c.veh.pos;
    for (const b of this.statics) {
      if (p[0] < b.min[0] - 6 || p[0] > b.max[0] + 6 || p[2] < b.min[2] - 6 || p[2] > b.max[2] + 6) continue;
      const k = hullVsBox(c.veh, b);
      if (k) this.resolveRigid(c, k.normal, k.depth, k.point, 'building');
    }
  }
  private collideProps(c: Car) {
    const p = c.veh.pos;
    for (const pr of this.props) {
      if (pr.state === 'gone') continue;
      const b = pr.def.box;
      if (p[0] < b.min[0] - 6 || p[0] > b.max[0] + 6 || p[2] < b.min[2] - 6 || p[2] > b.max[2] + 6) continue;
      if (pr.state === 'down' && pr.def.cls === 'knock') continue;
      if (pr.def.id === 'Canopy' && pr.state === 'whole') { if (b.min[1] > c.build.height + 0.2) continue; }
      const k = hullVsBox(c.veh, b);
      if (!k) continue;
      this.hitProp(c, pr, k.normal, k.depth, k.point);
    }
  }
  private hitProp(c: Car, pr: Prop, n: Vec3, depth: number, pt: Vec3) {
    const v = c.veh, vn = -dot(v.velocityAt(pt), n);
    if (vn <= 0.2 && pr.def.cls === 'anchored') { if (pr.state === 'whole') c.veh.pos = add(v.pos, mul(n, Math.min(depth, 0.3))); return; }
    const vnn = Math.max(vn, 0.4);
    const mc = v.mass, mp = pr.def.mass, at = mid(pr.def.box), cause = c.id, depth0 = this.depthOf(cause);
    const mu = (mc * mp) / (mc + mp), E = 0.5 * mu * vnn * vnn;
    if (pr.def.cls === 'knock') {
      // a light thing is thrown: the momentum goes to it, the car loses what it takes
      const vp = ((1.3) * mc * vnn) / (mc + mp);
      const dir = mul(n, -1);
      v.applyImpulse(mul(n, mp * vp * 0.9), pt);
      this.throwProp(pr, add(mul(dir, vp), [this.rng.range(-1, 1), 1.5 + 0.2 * vp, this.rng.range(-1, 1)]), c.id, 'knocked', depth0);
      if (mp > 60 && E > 800) { const s = v.strike({ point: pt, normal: n, speed: vn, otherMass: mp, restitution: 0.2, step: this.tick, entity: this.cars.indexOf(c) }); this.afterStrike(c, s, pr.id, vn); }
      return;
    }
    // anchored: the base holds up to its capacity; beyond it the thing gives way and the car loses that work
    if (E < pr.capacityJ) {
      this.resolveRigid(c, n, depth, pt, pr.id, 0.05, mp * 4, 0.5);
      return;
    }
    const vAfter = Math.sqrt(Math.max(0, vn * vn - (2 * pr.capacityJ) / mc));
    v.applyImpulse(mul(n, mc * (vn - vAfter) * 0.98), pt);
    c.veh.pos = add(v.pos, mul(n, Math.min(depth, 0.3)));
    const s = v.strike({ point: pt, normal: n, speed: Math.min(vn, 4), otherMass: mp, restitution: 0.1, step: this.tick, entity: this.cars.indexOf(c) }); this.afterStrike(c, s, pr.id, vn);
    const vp = Math.min(vn * 0.6, 12);
    this.throwProp(pr, add(mul(mul(n, -1), vp), [0, 1 + 0.15 * vp, 0]), c.id, 'broken', depth0);
    void at;
  }
  /** a prop leaves its place as a body that flies, tumbles and lands */
  throwProp(pr: Prop, vel: Vec3, cause: string | null, how: 'knocked' | 'broken' | 'fell', depth: number) {
    if (pr.state !== 'whole') return;
    pr.state = 'down'; pr.knocked = true;
    const b = pr.def.box, half: Vec3 = [(b.max[0] - b.min[0]) / 2, (b.max[1] - b.min[1]) / 2, (b.max[2] - b.min[2]) / 2];
    const base: Vec3 = [mid(b)[0], b.min[1] + half[1], mid(b)[2]];
    const axis = cross([0, 1, 0], vel), al = len(axis) || 1;
    this.debris.push({ id: this.nextDebris++, ref: pr.id, pos: base, vel, rot: [0, 0, 0, 1], ang: mul(axis, (1.2 + 3 / Math.max(1, half[1] * 2)) / al * (how === 'broken' ? 1.5 : 2.5)), half, mass: pr.def.mass, resting: false, age: 0, kind: pr.def.kind });
    this.emit({ t: this.t, type: 'prop', id: pr.id, kind: pr.def.kind, at: base, how, depth });
    if (cause) this.markActive(pr.id, depth);
  }

  /** a body with a velocity under gravity: lands on the ground, bounces a little, slides to rest */
  private stepDebris(dt: number) {
    for (const d of this.debris) {
      if (d.resting) continue;
      d.age += dt;
      d.vel[1] -= G * dt;
      d.pos = add(d.pos, mul(d.vel, dt));
      const w = d.ang, wl = len(w);
      if (wl > 1e-6) { const q = qAxisAngle(mul(w, 1 / wl), wl * dt); d.rot = mulQ(q, d.rot); }
      // the lowest point of the oriented box
      const ax: Vec3[] = [qRot(d.rot, [1, 0, 0]), qRot(d.rot, [0, 1, 0]), qRot(d.rot, [0, 0, 1])];
      const reach = d.half[0] * Math.abs(ax[0]![1]) + d.half[1] * Math.abs(ax[1]![1]) + d.half[2] * Math.abs(ax[2]![1]);
      const gh = this.ground.height(d.pos[0], d.pos[2]);
      if (d.pos[1] - reach < gh) {
        d.pos[1] = gh + reach;
        if (d.vel[1] < 0) d.vel[1] *= -0.28;
        d.vel[0] *= 0.82; d.vel[2] *= 0.82; d.ang = mul(d.ang, 0.7);
        if (len(d.vel) < 0.35 && wl < 0.8) { d.resting = true; d.vel = [0, 0, 0]; d.ang = [0, 0, 0]; }
      }
    }
  }

  private updateDamage() {
    for (const c of this.cars) {
      const k = CAR_KINDS[c.kind], led = c.veh.ledger;
      c.damage = (led.crush + led.fracture) / k.wreckJ;
      const out = c.veh.wheels.filter((w) => !w.attached).length;
      const rolled = c.veh.tilt() > 1.3 && len(c.veh.vel) < 6 && c.damage > 0.25;
      if (!c.wrecked && (c.damage >= 1 || out >= 2 || rolled)) {
        c.wrecked = true; c.shown = 1;
        const depth = this.depthOf(c.hitAt > this.t - 6 ? c.hitBy : null);
        this.markActive(c.id, depth);
        this.emit({ t: this.t, type: 'wreck', car: c.id, role: c.role, kind: c.kind, at: [...c.veh.pos] as Vec3, depth, cause: c.hitAt > this.t - 6 ? c.hitBy : null });
      }
    }
  }
}

function mulQ(a: Quat, b: Quat): Quat {
  return [a[3] * b[0] + a[0] * b[3] + a[1] * b[2] - a[2] * b[1], a[3] * b[1] - a[0] * b[2] + a[1] * b[3] + a[2] * b[0], a[3] * b[2] + a[0] * b[1] - a[1] * b[0] + a[2] * b[3], a[3] * b[3] - a[0] * b[0] - a[1] * b[1] - a[2] * b[2]];
}
export { qConj };
