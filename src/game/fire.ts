// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// Fuel, fire and blast of scene 1 on the engine's physics (no Babylon): a leaking store feeds a pool fire (heat release = leak rate x heat of combustion), the radiation of a fire (point source, flux q = chi P / 4 pi r^2,
// flame contact inside the pool) heats the walls of other stores in a HeatNetwork (steel and aluminium lose strength with temperature), a gas volume in each tank takes heat from its wall (links: gasInPart), a shell that
// gives way is a blast (vesselTnt, blastAt, gurneyVelocity) whose overpressure and impulse throw and break what stands within range and whose fireball sets alight whatever leaks. Chain reactions come out of these laws.
import { HeatNetwork, HeatLibrary, EXAMPLE_HEAT_MATERIALS, type Part } from '@ferret/physics-heat';
import { GasVolume } from '@ferret/physics-media';
import { gasInPart } from '@ferret/physics-links';
import { blastAt, vesselTnt, gurneyVelocity, TNT_JOULES_PER_KG } from '@ferret/physics-explosions';
import type { Vec3 } from '@ferret/destruction/types';
import type { StrikeResult } from '@ferret/destruction/vehicle';
import type { Car, Prop, Sim } from './sim';
import type { Box } from './layout';
import { CAR_KINDS } from './config';

/** heat of combustion of petrol, J/kg; the share of the burning that is heat release; the radiated share of it */
export const PETROL_HC = 43.7e6, COMBUSTION_EFFICIENCY = 0.8, RADIATED = 0.3;
/** heat release per square metre of a burning pool, W/m2 (petrol: regression rate 0.055 kg/m2s x HC) */
export const POOL_FLUX = 2.4e6;
/** flux on a wall engulfed in flame, W/m2 */
export const ENGULF_FLUX = 120e3;
/** the piloted ignition flux of a fuel surface, W/m2 (the usual 12.5 kW/m2) and the dose that sets a car alight without a leak */
export const IGNITE_FLUX = 12.5e3, CAR_IGNITE_FLUX = 25e3, CAR_IGNITE_TIME = 5;
/** the share of a burst tank's fuel that makes the blast wave (a BLEVE and vapour cloud blast: a few per cent of the combustion energy) */
export const BLAST_YIELD = 0.02;
/** fireball radius of a burst of fuel mass M, kg (the usual 2.9 M^0.32 law) and its duration, s */
export const fireballRadius = (m: number) => 2.9 * Math.pow(m, 0.32);
export const fireballTime = (m: number) => 0.45 * Math.cbrt(m);
/** each pump is fed from the underground tanks through a line: what can leak out of a broken pump, kg, and its rate, kg/s (an assumption of the set, see MOCKUPS.md) */
export const PUMP_LINE_KG = 600, PUMP_LEAK = 0.6;

type What = 'car' | 'tanker' | 'pump' | 'propane' | 'canopy' | 'column';
export interface Store {
  id: string; what: What; owner: string; at: () => Vec3; /** the extent of a station part (for the distance to a fire and the flame reaching it) */ box?: Box;
  fuelKg: number; leakMax: number; leaking: boolean; burning: boolean; ignitedAt: number; igniteIn: number; spark: boolean;
  /** burning power now, W */ power: number; burnLeft: number;
  /** the heat part of the wall and the gas inside */ wall?: Part; gas?: GasVolume; tankVolume: number; shellMass: number;
  exposed: number; failK: number; exploded: boolean; dose: number; blastKg: number; /** the chain depth of the fire */ depth: number;
  /** a burnt-out thing */ out: boolean; bursting?: boolean;
}

export class FireWorld {
  readonly net = new HeatNetwork();
  private readonly lib = new HeatLibrary(EXAMPLE_HEAT_MATERIALS);
  readonly stores: Store[] = [];
  private links: ReturnType<typeof gasInPart>[] = [];
  /** the total power of fires burning now, W */
  fires = 0;

  constructor(private sim: Sim) {
    sim.onStrike = (c, s, at, other, speed) => this.struck(c, s, other, speed);
    sim.onStep.push((dt) => this.step(dt));
  }

  private add(s: Partial<Store> & { id: string; what: What; owner: string; at: () => Vec3; fuelKg: number }): Store {
    const st: Store = { leakMax: 0, leaking: false, burning: false, ignitedAt: -1, igniteIn: -1, spark: false, power: 0, burnLeft: 0, tankVolume: 0, shellMass: 0, exposed: 0, failK: Infinity, exploded: false, dose: 0, blastKg: 0, depth: 0, out: false, ...s };
    this.stores.push(st); return st;
  }
  store(id: string) { return this.stores.find((s) => s.id === id); }

  /** every car carries its tank */
  registerCar(c: Car) {
    if (c.kind === 'tanker') return this.registerTanker(c);
    this.add({ id: c.id, what: 'car', owner: c.id, at: () => c.veh.pos, fuelKg: c.fuelKg, leakMax: 0.12 });
  }
  /** five compartments along the trailer, each with an aluminium shell, a heat part and its gas over the fuel */
  private registerTanker(c: Car) {
    const n = 5, total = CAR_KINDS.tanker.fuelL * 0.74, ullage = 0.06;
    for (let i = 0; i < n; i++) {
      const off = -3.5 - i * 1.8, volume = (CAR_KINDS.tanker.fuelL / 1000 / n) * (1 + ullage / (1 - ullage));
      const shell = 190, st = this.add({ id: `${c.id}.tank${i}`, what: 'tanker', owner: c.id, at: () => c.veh.toWorld([off, 1.9, 0]), fuelKg: total / n, leakMax: 9, tankVolume: volume, shellMass: shell, exposed: 8, failK: 640, blastKg: total / n });
      st.wall = this.net.addPart({ name: st.id, mass: shell, material: this.lib.get('aluminium'), T: 293.15, area: 9, h: 10, ambient: 293.15 });
      st.gas = new GasVolume({ moles: (101325 * volume * ullage) / (8.314 * 293.15), temperature: 293.15, volume: volume * ullage });
      this.links.push(gasInPart(st.gas, st.wall, this.net, 40));
    }
  }
  /** the station: pumps with their line, the propane cage, the canopy and its columns */
  registerStation() {
    for (const p of this.sim.props) {
      const s = p.station; if (!s) continue;
      const at = (): Vec3 => { const b = p.def.box; return [(b.min[0] + b.max[0]) / 2, (b.min[1] + b.max[1]) / 2, (b.min[2] + b.max[2]) / 2]; };
      const before = this.stores.length;
      if (/^Pump_/.test(p.id)) this.add({ id: p.id, what: 'pump', owner: p.id, at, fuelKg: s.fuelL * 0.74 + PUMP_LINE_KG, leakMax: PUMP_LEAK });
      else if (s.explosive) {
        const st = this.add({ id: p.id, what: 'propane', owner: p.id, at, fuelKg: 180, leakMax: 0.3, shellMass: 40, exposed: 4, failK: 700, blastKg: 180, tankVolume: 0.5 });
        st.wall = this.net.addPart({ name: p.id, mass: 40, material: this.lib.get('steel'), T: 293.15, area: 4, h: 10, ambient: 293.15 });
        st.gas = new GasVolume({ moles: 60, temperature: 293.15, volume: 0.5, molarMass: 0.044, gamma: 1.13 }); this.links.push(gasInPart(st.gas, st.wall, this.net, 15));
      } else if (p.id === 'Canopy') this.add({ id: p.id, what: 'canopy', owner: p.id, at, fuelKg: 260, leakMax: 0.1 });
      else if (/^CanopyColumn/.test(p.id)) { const st = this.add({ id: p.id, what: 'column', owner: p.id, at, fuelKg: 0, shellMass: 200, exposed: 4.3, failK: 750 }); st.wall = this.net.addPart({ name: p.id, mass: 200, material: this.lib.get('steel'), T: 293.15, area: 6, h: 10, ambient: 293.15 }); }
      for (let i = before; i < this.stores.length; i++) this.stores[i]!.box = p.def.box;
    }
  }

  /** a hit that opens a tank: a car crushed at its rear or flanks, a tanker shell, a pump knocked off its base */
  private struck(c: Car, s: StrikeResult, other: string, speed: number) {
    const j = s.ledger.crush + s.ledger.fracture;
    for (const st of this.stores) {
      if (st.owner !== c.id || st.leaking) continue;
      if (st.what === 'car' && j > 35e3) this.rupture(st, speed, j);
    }
    if (c.kind === 'tanker' && j > 150e3) {
      const lp = c.veh.toLocal(s.events[0]?.point ?? c.veh.pos);
      let best: Store | null = null, bd = 1e9;
      for (const st of this.stores) if (st.owner === c.id) { const d = Math.abs(c.veh.toLocal(st.at())[0] - lp[0]); if (d < bd) { bd = d; best = st; } }
      if (best && !best.leaking) this.rupture(best, speed, j);
    }
    void other;
  }
  rupture(st: Store, speed: number, joules: number) {
    st.leaking = true;
    this.sim.emit({ t: this.sim.t, type: 'spill', id: st.id, at: st.at(), kg: st.fuelKg });
    // sparks of the scraping metal: the more work, the likelier, and a little later
    const p = Math.min(0.4, joules / 600e3) + (speed > 22 ? 0.25 : 0);
    if (st.what !== 'car' || this.sim.rng.chance(p)) { st.spark = true; st.igniteIn = this.sim.rng.range(0.3, 2.5); }
    st.depth = this.sim.depthOf(this.sim.cars.find((c) => c.id === st.owner)?.hitBy ?? null);
  }
  ignite(st: Store, depth = 0) {
    if (st.burning || st.out) return;
    st.burning = true; st.ignitedAt = this.sim.t; st.depth = depth;
    const leak = st.leaking ? st.leakMax : st.what === 'canopy' ? 0.1 : st.what === 'car' ? 0.08 : 0.02;
    st.power = COMBUSTION_EFFICIENCY * Math.min(leak, st.fuelKg) * PETROL_HC;
    st.burnLeft = st.what === 'canopy' ? 140 : 1e9;
    if (st.what === 'canopy' || st.what === 'car') st.leaking = st.leaking || st.fuelKg > 0;
    this.sim.markActive(st.owner, depth);
    this.sim.emit({ t: this.sim.t, type: 'ignite', id: st.id, at: st.at(), power: st.power, what: st.what, depth });
  }

  /** the heat flux of a fire on a store, W/m2: inside the pool and in the flame (the flame is as high as Heskestad's law gives: 0.235 P^0.4 - 1.02 D, P in kW) it is the engulfing flux; further out the radiated share spread over the sphere to the nearest point of the store */
  private flux(from: Vec3, power: number, st: Store): number {
    const c = st.at(), b = st.box;
    const near: Vec3 = b ? [Math.max(b.min[0], Math.min(b.max[0], from[0])), Math.max(b.min[1], Math.min(b.max[1], from[1])), Math.max(b.min[2], Math.min(b.max[2], from[2]))] : c;
    const radius = Math.sqrt(Math.max(0, power) / POOL_FLUX / Math.PI), flameH = Math.max(0, 0.235 * Math.pow(power / 1e3, 0.4) - 1.02 * 2 * radius);
    const dh = Math.hypot(near[0] - from[0], near[2] - from[2]), dv = near[1] - from[1];
    if (dh < radius * 1.6 + 1 && dv < flameH && dv > -2) return ENGULF_FLUX;
    const r = Math.max(1.5, Math.hypot(dh, dv));
    return (RADIATED * power) / (4 * Math.PI * r * r);
  }

  step(dt: number) {
    const sim = this.sim;
    // knocked pumps leak, a fallen column drops the canopy
    for (const st of this.stores) {
      const pr = sim.prop(st.owner);
      if (st.what === 'pump' && pr && pr.state !== 'whole' && !st.leaking) this.rupture(st, 6, 40e3);
      if (st.what === 'propane' && pr && pr.state !== 'whole' && !st.leaking) { st.leaking = true; }
    }
    // the canopy comes down when its columns are gone (two of three): it crushes what stands under it, the pumps' lines tear
    const canopy = sim.prop('Canopy');
    if (canopy && canopy.state === 'whole') {
      const cols = sim.props.filter((p) => /^CanopyColumn/.test(p.id)), gone = cols.filter((p) => p.state !== 'whole').length;
      if (cols.length && gone >= Math.min(2, cols.length)) {
        const depth = this.chainDepth(this.stores.filter((x) => x.burning)) + 1;
        sim.throwProp(canopy, [0, -1, 0], 'Canopy', 'fell', depth);
        sim.emit({ t: sim.t, type: 'collapse', id: 'Canopy', at: [(canopy.def.box.min[0] + canopy.def.box.max[0]) / 2, canopy.def.box.min[1], (canopy.def.box.min[2] + canopy.def.box.max[2]) / 2], depth });
        const cb = canopy.def.box;
        for (const p of this.stores) if (p.what === 'pump' && p.box && p.box.max[0] > cb.min[0] && p.box.min[0] < cb.max[0] && p.box.max[2] > cb.min[2] && p.box.min[2] < cb.max[2]) {
          const pp = sim.prop(p.owner); if (pp && pp.state === 'whole') sim.throwProp(pp, [0, 0, 0], 'Canopy', 'broken', depth + 1);
          if (!p.leaking) this.rupture(p, 8, 60e3);
          if (burningAny(this.stores) && !p.burning) { p.spark = true; p.igniteIn = sim.rng.range(0.3, 1.5); p.depth = depth + 1; }
        }
      }
    }
    // spark ignition after its delay
    for (const st of this.stores) if (st.spark && !st.burning && st.igniteIn >= 0) { st.igniteIn -= dt; if (st.igniteIn <= 0) this.ignite(st, st.depth); }
    // fires: burn the fuel, radiate onto the others
    this.fires = 0;
    const burning = this.stores.filter((s) => s.burning && !s.out);
    for (const f of burning) {
      const leak = f.leaking ? f.leakMax : f.what === 'canopy' ? 0.1 : 0.05;
      const burnt = Math.min(f.fuelKg, leak * dt);
      f.fuelKg -= burnt; f.power = COMBUSTION_EFFICIENCY * (burnt / dt) * PETROL_HC;
      if (f.what === 'canopy') f.burnLeft -= dt;
      this.fires += f.power;
      sim.emit({ t: sim.t, type: 'burning', id: f.id, at: f.at(), power: f.power, what: f.what, dt });
      if (f.fuelKg <= 0 || f.burnLeft <= 0) { f.out = true; f.burning = false; f.power = 0; sim.emit({ t: sim.t, type: 'out', id: f.id, what: f.what }); }
    }
    for (const t of this.stores) {
      if (t.out || t.exploded) continue;
      let q = 0; const at = t.at();
      for (const f of burning) { if (f === t) continue; q += this.flux(f.at(), f.power, t); }
      if (t.wall) { t.wall.power = Math.min(q, ENGULF_FLUX) * t.exposed; if (t.burning && t.what === 'propane') t.wall.power += 0.5 * ENGULF_FLUX * t.exposed; /* its own leak fire plays on the cylinders (thin walls, a rack of small cylinders) */ }
      if (!t.burning) {
        const doseLimit = t.what === 'pump' ? 40e3 : CAR_IGNITE_FLUX, doseTime = t.what === 'pump' ? 3 : CAR_IGNITE_TIME, doses = t.what === 'car' || t.what === 'canopy' || t.what === 'pump';
        if (t.leaking && q > IGNITE_FLUX) this.ignite(t, this.chainDepth(burning) + 1);
        else if (doses && q > doseLimit) { t.dose += dt; if (t.dose > doseTime) { if (t.what === 'pump') t.leaking = true; this.ignite(t, this.chainDepth(burning) + 1); } } else t.dose = Math.max(0, t.dose - dt);
        if (t.what === 'car' && q > 60e3) t.leaking = true;
      }
    }
    // the walls warm, the gas takes heat, the shell fails at its temperature or by pressure
    this.net.step(dt);
    for (const l of this.links) l.step(dt, undefined as never, []);
    for (const t of this.stores) {
      if (t.exploded || t.out || !t.wall) continue;
      if (t.what === 'column') { if (t.wall.T > t.failK) this.dropColumn(t); continue; }
      const gp = t.gas ? t.gas.pressure : 101325;
      const hot = t.wall.T > t.failK, over = t.what === 'propane' && gp > 18e5 * (t.wall.T > 500 ? 0.2 : 1) && t.wall.T > 450;
      if (hot || over) this.burst(t, gp);
    }
    // a propane cylinder cage knocked over and burning blows by its own rule: handled above through the wall
  }
  private chainDepth(fires: Store[]): number { let d = 0; for (const f of fires) d = Math.max(d, f.depth); return d; }
  private dropColumn(t: Store) {
    t.exploded = true;
    const pr = this.sim.prop(t.owner); if (pr && pr.state === 'whole') this.sim.throwProp(pr, [0, 0, 0], t.owner, 'fell', this.chainDepth(this.stores.filter((s) => s.burning)) + 1);
  }

  /** a shell gives way: the blast of the vessel and of the fuel, fragments thrown, the fireball lights what leaks */
  private burst(t: Store, pressure: number) {
    t.exploded = true;
    const sim = this.sim, at = t.at();
    const fuelTnt = (BLAST_YIELD * t.fuelKg * PETROL_HC) / TNT_JOULES_PER_KG;
    const gasTnt = t.gas ? vesselTnt(pressure, t.gas.volume, t.gas.gamma) : 0;
    const tnt = Math.max(1, fuelTnt + gasTnt);
    const depth = Math.max(t.depth, this.chainDepth(this.stores.filter((s) => s.burning)));
    sim.markActive(t.owner, depth);
    sim.emit({ t: sim.t, type: 'blast', id: t.id, at, tnt, depth, what: t.what });
    const fb = fireballRadius(Math.max(t.fuelKg, 20));
    // fragments of the shell: Gurney speed from the charge and the casing, thrown as debris
    const vg = Math.min(220, gurneyVelocity(t.shellMass, tnt, 'cylinder'));
    for (let i = 0; i < 10; i++) {
      const a = sim.rng.range(0, Math.PI * 2), e = sim.rng.range(0.2, 0.9), sp = vg * sim.rng.range(0.2, 0.7);
      sim.debris.push({ id: 100000 + sim.debris.length, ref: t.id, pos: [at[0], at[1] + 1, at[2]], vel: [Math.cos(a) * sp * Math.cos(e), sp * Math.sin(e) + 5, Math.sin(a) * sp * Math.cos(e)], rot: [0, 0, 0, 1], ang: [sim.rng.range(-8, 8), sim.rng.range(-8, 8), sim.rng.range(-8, 8)], half: [0.5, 0.05, 0.4], mass: t.shellMass / 10, resting: false, age: 0, kind: 'shell' });
    }
    // what the blast does to cars, props and stores
    for (const c of sim.cars) {
      const p = c.veh.pos, r = Math.hypot(p[0] - at[0], p[1] - at[1], p[2] - at[2]);
      if (r < 1) continue;
      const b = blastAt(r, tnt), area = c.kind === 'tanker' ? 20 : 5.5;
      const dv = Math.min(60, (b.impulse * area) / c.veh.mass);
      if (dv < 0.2) continue;
      const dir: Vec3 = [(p[0] - at[0]) / r, 0.35, (p[2] - at[2]) / r];
      const l = Math.hypot(...dir);
      c.veh.wake(); c.veh.applyImpulse([dir[0] / l * dv * c.veh.mass, dir[1] / l * dv * c.veh.mass, dir[2] / l * dv * c.veh.mass]);
      const s = c.veh.strike({ point: [p[0] - dir[0] / l * 2, p[1], p[2] - dir[2] / l * 2], normal: [dir[0] / l, 0, dir[2] / l], speed: Math.min(dv, 30), otherMass: 1e6, restitution: 0.1, step: sim.tick, entity: sim.cars.indexOf(c) });
      c.hitBy = t.id; c.hitAt = sim.t;
      for (const d of s.detached) sim.emit({ t: sim.t, type: 'detach', car: c.id, part: d, at: [...p] as Vec3 });
    }
    for (const pr of sim.props) {
      if (pr.state !== 'whole') continue;
      const bc = pr.def.box, c: Vec3 = [(bc.min[0] + bc.max[0]) / 2, (bc.min[1] + bc.max[1]) / 2, (bc.min[2] + bc.max[2]) / 2];
      const r = Math.hypot(c[0] - at[0], c[1] - at[1], c[2] - at[2]); if (r < 1) continue;
      const b = blastAt(r, tnt), limit = pr.def.cls === 'knock' ? 3000 : pr.id === 'Canopy' ? 8000 : 14000;
      if (b.overpressure > limit) {
        const dv = Math.min(40, (b.impulse * 1.2 * Math.max(0.2, (bc.max[1] - bc.min[1]) * (bc.max[2] - bc.min[2]))) / pr.def.mass);
        sim.throwProp(pr, [(c[0] - at[0]) / r * dv, 2 + dv * 0.3, (c[2] - at[2]) / r * dv], t.id, pr.def.cls === 'knock' ? 'knocked' : 'broken', depth + 1);
      }
    }
    for (const s of this.stores) {
      if (s === t || s.out) continue;
      const p = s.at(), r = Math.hypot(p[0] - at[0], p[1] - at[1], p[2] - at[2]);
      if (r < fb && (s.leaking || s.what === 'pump' || s.what === 'canopy' || s.what === 'car')) { if (s.what === 'pump') s.leaking = true; this.ignite(s, depth + 1); }
      if (s.wall && r < fb) s.wall.power = ENGULF_FLUX * s.exposed;
    }
    t.out = true; t.burning = false; t.fuelKg = 0; t.power = 0;
    // the pool of the burst fuel lights the neighbours' walls: the remaining compartments leak and burn
    for (const s of this.stores) if (s.owner === t.owner && s !== t && !s.exploded) { s.leaking = true; this.ignite(s, depth + 1); }
    sim.emit({ t: sim.t, type: 'out', id: t.id, what: t.what });
  }
}
const burningAny = (st: Store[]) => st.some((x) => x.burning && !x.out);
export type { Prop };
