// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// The simulation of scene 1 (no Babylon): cars on the engine's wheeled assembly (ray-cast wheels, crush zones, parts that come off), the street's solid things, props that are knocked or broken,
// debris, damage and wrecks, and a stream of events for the score, the take and the view. The fixed step is 1/60 s with 4 sub-steps for the wheels.
import { Vehicle, hullContact, qAxisAngle, qRot, qConj, RESTING_SPEED, CAR_CONTACT_AREA, type RayCaster, type RayHit, type StrikeResult } from '@ferret/destruction/vehicle';
import { DestructionService, type HitResult } from '@ferret/destruction/service';
import { newLedger } from '@ferret/destruction/energy';
import type { Vec3, Quat } from '@ferret/destruction/types';
import { CAR_KINDS, SUBSTEPS, type KindId } from './config';
import type { CarBuild } from './carspec';
import type { Box, Layout, PropDef } from './layout';
import { Rng } from './rng';
import { ShopSim } from './shopfronts';
import { blastAt } from '@ferret/physics-explosions';
import { gridBlock, flingPieces } from '@ferret/destruction/fracture';
import type { PieceSpec } from '@ferret/destruction/types';

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
export interface Debris { id: number; ref: string; pos: Vec3; vel: Vec3; rot: Quat; ang: Vec3; half: Vec3; mass: number; resting: boolean; age: number; node?: string; kind: string; /** a held piece of a broken roof: the sim time it lets go, its place in the plan, whether it has struck the ground */ held?: number; piece?: number; hit?: boolean }
export interface Prop {
  def: PropDef; id: string; state: 'whole' | 'down' | 'gone'; capacityJ: number; knocked: boolean;
  /** station parts: what they are */ station?: { fuelL: number; burnable: boolean; explosive: boolean; supports?: string; lit: boolean };
}
export type SimEvent =
  | { t: number; type: 'impact'; a: string; b: string; at: Vec3; speed: number; energy: number }
  | { t: number; type: 'scrape'; car: string; at: Vec3; speed: number; dir: Vec3 }
  | { t: number; type: 'detach'; car: string; part: string; at: Vec3 }
  | { t: number; type: 'wreck'; car: string; role: Role; kind: KindId; at: Vec3; depth: number; cause: string | null }
  | { t: number; type: 'rubble'; id: string; at: Vec3; speed: number; mass: number; onto: string | null }
  | { t: number; type: 'prop'; id: string; kind: string; at: Vec3; how: 'knocked' | 'broken' | 'fell'; depth: number }
  | { t: number; type: 'blast'; id: string; at: Vec3; tnt: number; depth: number; what: string }
  | { t: number; type: 'ignite'; id: string; at: Vec3; power: number; what: string; depth: number }
  | { t: number; type: 'burning'; id: string; at: Vec3; power: number; what: string; dt: number }
  | { t: number; type: 'out'; id: string; what: string }
  | { t: number; type: 'spill'; id: string; at: Vec3; kg: number }
  | { t: number; type: 'collapse'; id: string; at: Vec3; depth: number };

const G = 9.81;
/** the share of the energy of two meeting cars that the spin of one of them may hold after the hit (the rest is crushed metal, heat and the other motion) */
const SPIN_SHARE = 0.4;
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
    // a ray that starts under the floor (a car pushed down by a contact or thrown into the kerb) still finds the floor above it, at a negative distance: the springs and the hull push the car up out of it. Without this the car fell for ever, a few thousand metres, and was gone from the street
    if (t < -1.5 || t > maxDistance) return null;
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
  /** the converted buildings' shop fronts (windows, door, sign, awning) as things of the destruction module; null when no building is converted */
  shops: ShopSim | null = null;
  /** the engine's destruction module: every hit on a car, a prop or a station part goes through it (crush, glass, wood, stone; the pieces that fly come from it) */
  readonly ds: DestructionService;
  /** the entity ids that became active (wreck, blast, fire) with the chain depth and the time: the chain reactions */
  readonly active = new Map<string, { depth: number; t: number }>();
  /** extra hooks: the fire module sees each hit */
  onStrike: ((car: Car, s: StrikeResult, at: Vec3, other: string, speed: number) => void) | null = null;
  onStep: ((dt: number) => void)[] = [];

  constructor(readonly layout: Layout, seed: number) {
    this.ground = new StreetGround(layout.road); this.statics = layout.statics; this.rng = new Rng(seed);
    this.ds = new DestructionService({ maxPieces: 400, maxBodies: 0 });
    this.ds.groundY = 0.03;
    // the film look: cars are physical in their energy but crumple a little deeper and throw more, bigger-and-smaller pieces that bounce and lie about; the street furniture takes the engine's hollywood preset
    this.ds.book.defineStyle({ name: 'film', crush: { depthScale: 1.25 }, fracture: { piecesScale: 3, sizeSpread: 0.5, burstScale: 2.5 }, debris: { bounce: 0.4, life: 14, gravityScale: 0.85 } });
    this.ds.scopes.setLevel('film');
    for (const p of layout.props) this.props.push({ def: p, id: p.id, state: 'whole', capacityJ: PROP_CAPACITY[p.kind] ?? 0, knocked: false });
    for (const s of layout.station.parts) {
      const cls: PropDef['cls'] = /^(Bin|NewsBox|IceChest|OilRack|TyreStack|AirStand|PropaneCage)/.test(s.id) ? 'knock' : 'anchored';
      const cap = /^CanopyColumn/.test(s.id) ? 250000 : /^Pump/.test(s.id) ? 7000 : /^Canopy$/.test(s.id) ? 1e12 : /^(Lamp|PriceSign|SignPost|VentPipes)/.test(s.id) ? 12000 : 3000;
      this.props.push({ def: { id: s.id, kind: s.id.replace(/_\d+$/, ''), mass: s.mass, box: s.box, cls }, id: s.id, state: 'whole', capacityJ: cap, knocked: false, station: { fuelL: s.fuelL, burnable: s.burnable, explosive: s.explosive, supports: s.supports, lit: s.lit } });
    }
    for (const pr of this.props) this.defineProp(pr);
    this.planCanopy(seed);
    if (layout.shops && layout.shops.parts.length > 0) this.shops = new ShopSim(this, layout.shops, hullVsBox);
  }

  /** a prop or a station part as a destructible thing of the module: one part of the material it is made of, in the style of the street furniture (hollywood) */
  private defineProp(pr: Prop) {
    const b = pr.def.box, size: Vec3 = [Math.max(0.05, b.max[0] - b.min[0]), Math.max(0.05, b.max[1] - b.min[1]), Math.max(0.05, b.max[2] - b.min[2])];
    const k = pr.def.kind;
    let substance = 'steel-sheet', thickness = 0, fill = 0.25;
    if (/^(Bench|Sawhorse|PicnicTable|CrateStack)/.test(k)) { substance = 'wood-oak'; fill = 0.5; }
    else if (k === 'UtilityPole') { substance = 'wood-pine'; fill = 0.8; }
    else if (k === 'PhoneBooth') { substance = 'glass-tempered'; thickness = 0.006; }
    else if (k === 'Planter') { substance = 'concrete'; fill = 0.7; }
    else if (/^(Cone|Bin|TrashBags|NewsBox|IceChest)/.test(k)) { substance = 'plastic-abs'; thickness = 0.003; }
    else if (/^RoadSign|^PriceSign|^SignPost/.test(k)) { substance = 'aluminium-sheet'; thickness = 0.002; }
    else if (k === 'Canopy') { substance = 'aluminium-sheet'; thickness = 0.002; fill = 0.1; }
    else if (/^(Hydrant|LampAcorn|TrafficLight|Meter|Mailbox|CanopyColumn|Pump|CrowdBarrier|PropaneCage|OilRack|TyreStack|AirStand|Lamp|VentPipes)/.test(k)) { substance = 'steel-sheet'; thickness = /^(CrowdBarrier|Pump|Mailbox|PropaneCage)/.test(k) ? 0.003 : 0; fill = thickness ? 0.15 : 0.35; }
    this.ds.defineThing({ id: pr.id, root: 'body', style: 'hollywood', parts: [{ id: 'body', substance, size, thickness, mass: pr.def.mass, fill }] });
    const d = this.ds.thing(pr.id); d.frame = { position: [(b.min[0] + b.max[0]) / 2, (b.min[1] + b.max[1]) / 2, (b.min[2] + b.max[2]) / 2], rotation: [0, 0, 0, 1] };
  }
  /** shop windows: the street art has them inside the merged building meshes, so the game lays 2.4 m panes of 6 mm tempered glass along the street face of every building box (ground floor, 0.4 to 2.6 m); a pane is made as a module thing at the first hit and the module decides what the car's energy does to it */
  private panes = new Map<string, boolean>();
  private breakWindow(c: Car, b: Box, pt: Vec3, speed: number) {
    const faceZ = (b.min[2] + b.max[2]) / 2 > 0 ? b.min[2] : b.max[2];
    if (Math.abs(pt[2] - faceZ) > 1.6 || pt[1] < 0.1 || pt[1] > 3.2 || pt[0] < b.min[0] + 0.5 || pt[0] > b.max[0] - 0.5) return;
    const idx = Math.floor((pt[0] - b.min[0]) / 2.6), cx = b.min[0] + idx * 2.6 + 1.3, id = `Window_${Math.round(b.min[0])}_${Math.round(faceZ * 10)}_${idx}`;
    if (this.panes.get(id) === false) return;
    if (!this.panes.has(id)) {
      this.ds.defineThing({ id, root: 'glass', parts: [{ id: 'glass', substance: 'glass-tempered', size: [2.4, 2.1, 0.006], thickness: 0.006, mass: 2.4 * 2.1 * 0.006 * 2500 }] });
      const d = this.ds.thing(id); d.frame = { position: [cx, 1.5, faceZ], rotation: [0.7071068, 0, 0, 0.7071068] }; this.panes.set(id, true);
    }
    const n: Vec3 = [0, 0, faceZ > 0 ? -1 : 1];
    const r = this.ds.contact(id, { point: [cx + Math.max(-1, Math.min(1, pt[0] - cx)), Math.max(0.5, Math.min(2.5, pt[1])), faceZ], normal: mul(n, -1), speed, otherMass: c.veh.mass, restitution: 0.2, area: 0.6, step: this.tick });
    if (r && r.outcome.broken) {
      this.panes.set(id, false);
      this.emit({ t: this.t, type: 'prop', id, kind: 'Window', at: [cx, 1.5, faceZ], how: 'broken', depth: this.depthOf(c.id) });
    }
  }
  /** the blast wave of `tnt` kg of TNT at `at` against the street buildings: where the overpressure on a facade is over what a brick wall bay of 0.3 m stands (about 30 kPa), a 3 x 3 m bay of the wall is made as a module thing (brick) and hit with the blast's impulse; the module breaks it into pieces that fly and fall (rubble). The street's visible mesh is one merged piece, so the hole itself cannot be cut (see engine-changes.txt); the pieces, the dust and the sound are real */
  private bays = 0;
  blastFacades(at: Vec3, tnt: number, depth: number) {
    this.shops?.blast(at, tnt, depth);
    let made = 0;
    for (const b of this.statics) {
      if (made >= 3 || this.bays >= 14) break;
      if (b.max[1] - b.min[1] < 4 || b.max[0] - b.min[0] < 6) continue;
      const nx = Math.max(b.min[0], Math.min(b.max[0], at[0])), nz = Math.max(b.min[2], Math.min(b.max[2], at[2]));
      const r = Math.hypot(nx - at[0], nz - at[2]); if (r < 3 || r > 70) continue;
      const bl = blastAt(r, tnt); if (bl.overpressure < 30e3) continue;
      const faceZ = (b.min[2] + b.max[2]) / 2 > 0 ? b.min[2] : b.max[2], id = `Facade_${Math.round(b.min[0])}_${Math.round(faceZ)}_${this.bays}`;
      const cx = Math.max(b.min[0] + 2, Math.min(b.max[0] - 2, at[0])), cy = 3.2;
      this.ds.defineThing({ id, root: 'wall', parts: [{ id: 'wall', substance: 'brick', size: [3, 3, 0.3], thickness: 0.3, mass: 3 * 3 * 0.3 * 1900 }] });
      const d = this.ds.thing(id); d.frame = { position: [cx, cy, faceZ], rotation: [0.7071068, 0, 0, 0.7071068] };
      const n: Vec3 = [0, 0, faceZ > 0 ? -1 : 1], speed = Math.min(40, 10 + bl.overpressure / 12e3);
      const res = this.ds.contact(id, { point: [cx, cy, faceZ], normal: mul(n, -1), speed, otherMass: 4000, restitution: 0.1, area: 2.5, step: this.tick });
      this.bays++; made++;
      this.emit({ t: this.t, type: 'prop', id, kind: 'Facade', at: [cx, cy, faceZ], how: 'broken', depth });
      void res;
    }
  }
  /** a hit on a prop through the module: the pieces it throws, and whether the material gave way (wood, glass, stone) */
  private propContact(pr: Prop, pt: Vec3, n: Vec3, speed: number, otherMass: number): HitResult | null {
    return this.ds.contact(pr.id, { point: pt, normal: mul(n, -1), speed, otherMass, restitution: 0.2, area: 0.25, step: this.tick });
  }
  /** a car takes a hit through the module (the part under the point crumples, glass breaks, parts come off and their pieces fly); the result has the shape of a vehicle strike, the ledger is the whole thing's work for this hit */
  strikeCar(c: Car, a: { point: Vec3; normal: Vec3; speed: number; otherMass: number; restitution: number; rigid?: boolean }): StrikeResult {
    const d = this.ds.thing(c.id), before = d.ledger;
    const r = this.ds.contact(c.id, { point: a.point, normal: a.normal, speed: a.speed, otherMass: a.otherMass, restitution: a.restitution, area: CAR_CONTACT_AREA, step: this.tick, rigidOther: a.rigid });
    c.veh.wake();
    if (!r) return { part: '', ledger: newLedger(0), stage: 'none', detached: [], events: [], load: 0 };
    const now = d.ledger, led = newLedger(now.input - before.input);
    led.crush = now.crush - before.crush; led.fracture = now.fracture - before.fracture; led.kinetic = now.kinetic - before.kinetic; led.heat = now.heat - before.heat; led.sound = now.sound - before.sound; led.residual = now.residual - before.residual;
    return { part: r.record.part, ledger: led, stage: r.outcome.stage, detached: r.detached, events: r.events, load: r.load };
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
    this.cars.push(c);
    this.ds.add({ id, assembly: c.veh.assembly, zones: c.veh.zones, vehicle: c.veh });
    return c;
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
    this.ds.advance(dt);
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
        // a car whose state is not a number (a numerical failure) must not meet the others: the contact would make every car it touches NaN too, and the whole street of cars vanished at once
        if (!finiteState(a) || !finiteState(b)) continue;
        const wasA = len(a.veh.vel), wasB = len(b.veh.vel);
        const r = this.collidePair(a, b);
        if (r && r.speed > 1.2) {
          a.hitBy = b.id; a.hitAt = this.t; b.hitBy = a.id; b.hitAt = this.t;
          const at = r.point, e = 0.5 * (a.veh.mass * b.veh.mass / (a.veh.mass + b.veh.mass)) * r.speed * r.speed;
          this.emit({ t: this.t, type: 'impact', a: a.id, b: b.id, at: [...at] as Vec3, speed: r.speed, energy: e });
          if (r.a) this.afterStrike(a, r.a, b.id, r.speed); if (r.b) this.afterStrike(b, r.b, a.id, r.speed);
          void wasA; void wasB;
        }
      }
      if (a.veh.sleeping) continue;
      this.collideStatics(a);
      this.collideProps(a);
      this.shops?.collideCar(a);
    }
  }
  /** two cars meet: the impulse at the contact (momentum conserved, both turn), the overlap pushed apart by the inverse masses, and, above the resting speed, each car takes the hit of its side through the module */
  private collidePair(a: Car, b: Car): { speed: number; point: Vec3; a?: StrikeResult; b?: StrikeResult } | null {
    const A = a.veh, B = b.veh, c = hullContact(A, B);
    if (!c) return null;
    const n = c.normal, vrel = sub(B.velocityAt(c.point), A.velocityAt(c.point)), vn = dot(vrel, n);
    const out: { speed: number; point: Vec3; a?: StrikeResult; b?: StrikeResult } = { speed: Math.max(0, -vn), point: c.point };
    const ia = 1 / A.mass, ib = 1 / B.mass, ra = sub(c.point, A.pos), rb = sub(c.point, B.pos);
    const ka = dot(cross(A.invInertia(cross(ra, n)), ra), n), kb = dot(cross(B.invInertia(cross(rb, n)), rb), n);
    if (vn < 0) {
      const restitution = 0.12, j = (-(1 + restitution) * vn) / (ia + ib + ka + kb), speed = -vn;
      const keA = this.kinetic(A), keB = this.kinetic(B);
      A.applyImpulse(mul(n, -j), c.point); B.applyImpulse(mul(n, j), c.point);
      this.limitSpin(A, keA + keB); this.limitSpin(B, keA + keB);
      if (speed > RESTING_SPEED) {
        out.a = this.strikeCar(a, { point: c.point, normal: mul(n, -1), speed, otherMass: B.mass, restitution });
        out.b = this.strikeCar(b, { point: c.point, normal: n, speed, otherMass: A.mass, restitution });
      }
    }
    const total = ia + ib;
    A.pos = sub(A.pos, mul(n, (c.depth * ia) / total)); B.pos = add(B.pos, mul(n, (c.depth * ib) / total));
    return out;
  }
  /** kinetic energy of a car, J: translation and rotation */
  private kinetic(v: Vehicle): number {
    const wb = qRot(qConj(v.rot), v.angVel), I = v.inertia;
    return 0.5 * v.mass * dot(v.vel, v.vel) + 0.5 * (I[0] * wb[0] * wb[0] + I[1] * wb[1] * wb[1] + I[2] * wb[2] * wb[2]);
  }
  /** a hit between rigid hulls puts all of an off-centre impulse into the spin; a real car crumples, and the work of that goes into the metal. The spin a car keeps after a hit holds at most this share of the two cars' energy before it */
  private limitSpin(v: Vehicle, before: number) {
    const wb = qRot(qConj(v.rot), v.angVel), I = v.inertia, er = 0.5 * (I[0] * wb[0] * wb[0] + I[1] * wb[1] * wb[1] + I[2] * wb[2] * wb[2]), budget = SPIN_SHARE * before;
    if (er > budget && er > 0) v.angVel = mul(v.angVel, Math.sqrt(budget / er));
  }
  private afterStrike(c: Car, s: StrikeResult, other: string, speed: number) {
    for (const id of s.detached) this.emit({ t: this.t, type: 'detach', car: c.id, part: id, at: [...c.veh.pos] as Vec3 });
    this.spawnDetached(c);
    this.onStrike?.(c, s, [...c.veh.pos] as Vec3, other, speed);
  }
  private seenDetached = new Map<string, number>();
  private scrapedAt = new Map<string, number>();
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
    if (vn >= 0) { const w = sub(vrel, mul(n, vn)), wl = len(w); if (wl > 3.5 && vn > -0.5 && this.t - (this.scrapedAt.get(c.id) ?? -1) > 0.06) { this.scrapedAt.set(c.id, this.t); this.emit({ t: this.t, type: 'scrape', car: c.id, at: [...pt] as Vec3, speed: wl, dir: [-w[0] / wl, 0.25, -w[2] / wl] }); } return 0; }
    const r = sub(pt, v.pos), rn = cross(r, n), k = dot(cross(v.invInertia(rn), r), n);
    const j = (-(1 + restitution) * vn) / (1 / v.mass + k);
    v.applyImpulse(mul(n, j), pt);
    const vt = sub(vrel, mul(n, vn)), vtl = len(vt);
    if (vtl > 1e-3) { const jt = Math.min(mu * j, (vtl * v.mass) / 2); v.applyImpulse(mul(vt, -jt / vtl), pt); }
    const speed = -vn;
    if (vtl > 3.5 && this.t - (this.scrapedAt.get(c.id) ?? -1) > 0.06) { this.scrapedAt.set(c.id, this.t); this.emit({ t: this.t, type: 'scrape', car: c.id, at: [...pt] as Vec3, speed: vtl, dir: [-vt[0] / vtl, 0.25, -vt[2] / vtl] }); }
    if (speed > 1.2) {
      const s = this.strikeCar(c, { point: pt, normal: n, speed, otherMass, restitution, rigid: otherId === 'building' });
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
      if (k) { const sp = this.resolveRigid(c, k.normal, k.depth, k.point, 'building'); if (this.shops?.wallHit(c, b, k.point, sp)) continue; if (sp > 2.5) this.breakWindow(c, b, k.point, sp); }
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
    // the module takes the hit on the prop first: the pieces it throws (splinters, shards, chips) and whether its material gave way (a bench's planks, a pane, a planter)
    const hr = this.propContact(pr, pt, n, vnn, mc);
    if (hr && (hr.outcome.broken || hr.detached.length > 0) && pr.state === 'whole') {
      const L = hr.outcome.ledger, absorbed = L.crush + L.fracture + L.heat + L.sound;
      const vAfter = Math.sqrt(Math.max(0, vn * vn - (2 * absorbed) / mc));
      v.applyImpulse(mul(n, mc * Math.max(0, vn - vAfter) * 0.98), pt);
      if (pr.def.cls === 'anchored') c.veh.pos = add(v.pos, mul(n, Math.min(depth, 0.3)));
      pr.state = 'gone'; pr.knocked = true;
      this.emit({ t: this.t, type: 'prop', id: pr.id, kind: pr.def.kind, at: mid(pr.def.box), how: 'broken', depth: depth0 });
      this.markActive(pr.id, depth0);
      return;
    }
    if (pr.def.cls === 'knock') {
      // a light thing is thrown: the momentum goes to it, the car loses what it takes
      const vp = ((1.3) * mc * vnn) / (mc + mp);
      const dir = mul(n, -1);
      v.applyImpulse(mul(n, mp * vp * 0.9), pt);
      this.throwProp(pr, add(mul(dir, vp), [this.rng.range(-1, 1), 1.5 + 0.2 * vp, this.rng.range(-1, 1)]), c.id, 'knocked', depth0);
      if (mp > 60 && E > 800) { const s = this.strikeCar(c, { point: pt, normal: n, speed: vn, otherMass: mp, restitution: 0.2 }); this.afterStrike(c, s, pr.id, vn); }
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
    const s = this.strikeCar(c, { point: pt, normal: n, speed: Math.min(vn, 4), otherMass: mp, restitution: 0.1 }); this.afterStrike(c, s, pr.id, vn);
    const vp = Math.min(vn * 0.6, 12);
    this.throwProp(pr, add(mul(mul(n, -1), vp), [0, 1 + 0.15 * vp, 0]), c.id, 'broken', depth0);
    void at;
  }
  /** a prop leaves its place as a body that flies, tumbles and lands */
  throwProp(pr: Prop, vel: Vec3, cause: string | null, how: 'knocked' | 'broken' | 'fell', depth: number) {
    if (pr.state !== 'whole') return;
    if (pr.id === 'Canopy' && this.canopy) { this.breakCanopy(pr, vel, cause, how, depth); return; }
    pr.state = 'down'; pr.knocked = true;
    const b = pr.def.box, half: Vec3 = [(b.max[0] - b.min[0]) / 2, (b.max[1] - b.min[1]) / 2, (b.max[2] - b.min[2]) / 2];
    const base: Vec3 = [mid(b)[0], b.min[1] + half[1], mid(b)[2]];
    const axis = cross([0, 1, 0], vel), al = len(axis) || 1;
    this.debris.push({ id: this.nextDebris++, ref: pr.id, pos: base, vel, rot: [0, 0, 0, 1], ang: mul(axis, (1.2 + 3 / Math.max(1, half[1] * 2)) / al * (how === 'broken' ? 1.5 : 2.5)), half, mass: pr.def.mass, resting: false, age: 0, kind: pr.def.kind });
    this.emit({ t: this.t, type: 'prop', id: pr.id, kind: pr.def.kind, at: base, how, depth });
    if (cause) this.markActive(pr.id, depth);
  }

  // ---- the roof of the station: pre-fractured into panels that tear loose, fall, tilt, slide and crush what stands under them ----
  /** the engine's pre-fracture of the roof slab (`gridBlock`, by seed): the panels' sizes, places and masses; null when the street has no canopy */
  canopy: { pieces: PieceSpec[]; centre: Vec3; seed: number } | null = null;
  private planCanopy(seed: number) {
    const pr = this.props.find((p) => p.id === 'Canopy'); if (!pr) return;
    const b = pr.def.box, size: Vec3 = [b.max[0] - b.min[0], b.max[1] - b.min[1], b.max[2] - b.min[2]];
    const r = gridBlock({ size, mass: pr.def.mass, budget: 1e9, fractureEnergy: 1e3, seed: (seed ^ 0xca909) >>> 0, maxPieces: 9 });
    if (r.pieces.length < 2) return;
    this.canopy = { pieces: r.pieces, centre: mid(b), seed: (seed ^ 0xca909) >>> 0 };
  }
  /** the roof lets go: each panel is a body of its own mass and size; those nearest a standing column hold a moment longer, the rest drop at once, tilting away from the support that is left */
  private breakCanopy(pr: Prop, vel: Vec3, cause: string | null, how: 'knocked' | 'broken' | 'fell', depth: number) {
    const plan = this.canopy!, c = plan.centre, rng = new Rng(plan.seed ^ 0x51);
    pr.state = 'down'; pr.knocked = true;
    const cols = this.props.filter((p) => /^CanopyColumn/.test(p.id) && p.state === 'whole').map((p) => mid(p.def.box));
    // the engine's scatter: the panels' kinetic energy is what the fall and the push give, spread from the roof's centre
    const m = pr.def.mass, push = Math.hypot(vel[0], vel[2]);
    const specs = plan.pieces.map((q) => ({ ...q, velocity: [0, 0, 0] as Vec3, angular: [0, 0, 0] as Vec3 }));
    flingPieces(specs, [0, 0, 0], [vel[0] * 0.3, 0.6, vel[2] * 0.3], 0.5 * m * (3 + 0.5 * push * push) * 0.35, plan.seed);
    specs.forEach((q, i) => {
      const at: Vec3 = [c[0] + q.offset[0], c[1] + q.offset[1], c[2] + q.offset[2]];
      let near = 99, toward: Vec3 = [0, 0, 0];
      for (const k of cols) { const d = Math.hypot(k[0] - at[0], k[2] - at[2]); if (d < near) { near = d; toward = [k[0] - at[0], 0, k[2] - at[2]]; } }
      const delay = cols.length ? 0.05 + rng.range(0, 0.3) + Math.max(0, 0.16 * (7 - near)) : rng.range(0, 0.35) + 0.05 * Math.hypot(q.offset[0], q.offset[2]);
      // the free edge drops: a turn about the horizontal axis across the way to the nearest standing support (or a seeded one when none is left)
      const dir: Vec3 = cols.length ? [toward[0] / (near || 1), 0, toward[2] / (near || 1)] : [Math.cos(i * 2.4), 0, Math.sin(i * 2.4)];
      const spin = rng.range(0.5, 1.6) * (cols.length ? 1 : 1.3), sgn = rng.chance(0.5) ? 1 : -1;
      const ang: Vec3 = [-dir[2] * spin * sgn + q.angular[0], rng.range(-0.4, 0.4) + q.angular[1], dir[0] * spin * sgn + q.angular[2]];
      this.debris.push({ id: this.nextDebris++, ref: 'Canopy#' + i, pos: at, vel: [q.velocity[0] + vel[0] * 0.2, q.velocity[1] + Math.max(0, vel[1]) * 0.2, q.velocity[2] + vel[2] * 0.2], rot: [0, 0, 0, 1], ang, half: [q.size[0] / 2, q.size[1] / 2, q.size[2] / 2], mass: q.mass, resting: false, age: 0, kind: 'canopy-piece', held: this.t + delay, piece: i });
    });
    this.emit({ t: this.t, type: 'prop', id: pr.id, kind: pr.def.kind, at: c, how, depth });
    if (cause) this.markActive(pr.id, depth);
  }
  /** a standing thing under a falling panel that it would hit: the tops of the pumps, the propane cage, the islands' fittings */
  private underPiece(d: Debris, hx: number, hz: number, low: number): Prop | null {
    for (const p of this.props) {
      if (p.state !== 'whole' || !/^(Pump|PropaneCage|IceChest|AirStand|OilRack|TyreStack|NewsBox|Bin|PriceSign|Lamp)/.test(p.id)) continue;
      const b = p.def.box;
      if (d.pos[0] + hx > b.min[0] && d.pos[0] - hx < b.max[0] && d.pos[2] + hz > b.min[2] && d.pos[2] - hz < b.max[2] && low < b.max[1] - 0.05 && d.pos[1] > b.min[1]) return p;
    }
    return null;
  }

  /** a body with a velocity under gravity: lands on the ground, bounces a little, slides to rest */
  private stepDebris(dt: number) {
    for (const d of this.debris) {
      if (d.resting) continue;
      if (d.held !== undefined && this.t < d.held) continue;       // a panel still hanging on its fixings
      d.age += dt;
      d.vel[1] -= G * dt;
      d.pos = add(d.pos, mul(d.vel, dt));
      const w = d.ang, wl = len(w);
      if (wl > 1e-6) { const q = qAxisAngle(mul(w, 1 / wl), wl * dt); d.rot = mulQ(q, d.rot); }
      // the lowest point of the oriented box
      const ax: Vec3[] = [qRot(d.rot, [1, 0, 0]), qRot(d.rot, [0, 1, 0]), qRot(d.rot, [0, 0, 1])];
      const reach = d.half[0] * Math.abs(ax[0]![1]) + d.half[1] * Math.abs(ax[1]![1]) + d.half[2] * Math.abs(ax[2]![1]);
      const gh = this.ground.height(d.pos[0], d.pos[2]);
      const roof = d.kind === 'canopy-piece';
      if (roof && d.vel[1] < 0) {
        // a panel comes down on a pump: the pump is knocked out from under it and the panel loses part of its speed
        const hx = d.half[0] * Math.abs(ax[0]![0]) + d.half[1] * Math.abs(ax[1]![0]) + d.half[2] * Math.abs(ax[2]![0]), hz = d.half[0] * Math.abs(ax[0]![2]) + d.half[1] * Math.abs(ax[1]![2]) + d.half[2] * Math.abs(ax[2]![2]);
        const hit = this.underPiece(d, hx, hz, d.pos[1] - reach);
        if (hit) {
          const sp = Math.abs(d.vel[1]);
          this.throwProp(hit, [d.vel[0] * 0.5 + this.rng.range(-1, 1), 1 + 0.3 * sp, d.vel[2] * 0.5 + this.rng.range(-1, 1)], 'Canopy', 'broken', 3);
          this.emit({ t: this.t, type: 'rubble', id: d.ref, at: [d.pos[0], hit.def.box.max[1], d.pos[2]], speed: sp, mass: d.mass, onto: hit.id });
          d.vel = mul(d.vel, 0.55); d.ang = add(d.ang, [this.rng.range(-0.8, 0.8), 0, this.rng.range(-0.8, 0.8)]);
        }
      }
      if (d.pos[1] - reach < gh + (roof ? 0.35 : 0)) {
        if (d.pos[1] - reach < gh) d.pos[1] = gh + reach; else if (roof && d.vel[1] < 0) d.vel[1] *= 0.5;
        if (roof && !d.hit && d.vel[1] < -1.5) { d.hit = true; this.emit({ t: this.t, type: 'rubble', id: d.ref, at: [d.pos[0], gh, d.pos[2]], speed: -d.vel[1], mass: d.mass, onto: null }); }
        if (d.vel[1] < 0 && d.pos[1] - reach < gh + 0.01) d.vel[1] *= roof ? (d.vel[1] > -2 ? 0 : -0.12) : -0.28;
        if (roof) {
          // a slab slides on its edge and settles flat: the face most nearly down is turned to the ground
          d.vel[0] *= 0.955; d.vel[2] *= 0.955; d.ang = mul(d.ang, 0.8);
          let k = 0; for (let i = 1; i < 3; i++) if (d.half[i]! < d.half[k]!) k = i;      // the thinnest face goes down: a panel lies flat, never on its end
          const a = mul(ax[k]!, Math.sign(ax[k]![1]) || 1), turn = cross(a, [0, 1, 0]), tl = len(turn);
          if (tl > 1e-4) d.rot = mulQ(qAxisAngle(mul(turn, 1 / tl), Math.asin(Math.min(1, tl)) * (1 - Math.exp(-11 * dt))), d.rot);
          if (len(d.vel) < 0.3 && wl < 0.5 && tl < 0.03) { d.resting = true; d.vel = [0, 0, 0]; d.ang = [0, 0, 0]; }
        } else {
          d.vel[0] *= 0.82; d.vel[2] *= 0.82; d.ang = mul(d.ang, 0.7);
          if (len(d.vel) < 0.35 && wl < 0.8) { d.resting = true; d.vel = [0, 0, 0]; d.ang = [0, 0, 0]; }
        }
      }
    }
  }

  private updateDamage() {
    for (const c of this.cars) {
      const k = CAR_KINDS[c.kind], led = this.ds.thing(c.id).ledger;
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

/** every number of a car's body state is finite */
function finiteState(c: Car): boolean {
  const v = c.veh;
  for (const a of [v.pos, v.vel, v.rot, v.angVel]) for (const x of a) if (!Number.isFinite(x)) return false;
  return true;
}

function mulQ(a: Quat, b: Quat): Quat {
  return [a[3] * b[0] + a[0] * b[3] + a[1] * b[2] - a[2] * b[1], a[3] * b[1] - a[0] * b[2] + a[1] * b[3] + a[2] * b[0], a[3] * b[2] + a[0] * b[1] - a[1] * b[0] + a[2] * b[3], a[3] * b[3] - a[0] * b[0] - a[1] * b[1] - a[2] * b[2]];
}
export { qConj };
