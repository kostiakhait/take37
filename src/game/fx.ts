// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// The look of every impact and fire of scene 1, in the manner of a 1987 action film: the sim's events (impact, scrape, detach, wreck, spill, ignite, burning, out, blast, collapse, prop) and the cars' own state (slip of the tyres,
// a car sliding on its side) are turned into effects of the engine's vfx module (@ferret/vfx), its catalogue where it has the thing and the definitions of fx-defs.ts where it has not; the size of each follows the number the
// physics gives (joules, kilograms of TNT, watts of fire). The camera shake and the warm flash on the street also come from those numbers. The module's governor keeps the effects inside a budget of milliseconds.
// VIEW FILE: it reads the sim and never writes to it. No Babylon here but the one scene light the flash touches (passed in as a small interface).
import { Governor, type VfxSystem, type VfxHandle } from '@ferret/vfx';
import { qRot } from '@ferret/destruction/vehicle';
import { TAKE37_FX } from './fx-defs';
import type { Take } from './take';
import type { Car, Debris, SimEvent } from './sim';

type V3 = [number, number, number];
const clamp = (v: number, a: number, b: number) => Math.max(a, Math.min(b, v));
/** the fuel in kilograms of petrol whose blast (2 per cent of its heat) is this much TNT, see fire.ts BLAST_YIELD: 43.7e6 * 0.02 / 4.184e6 J per kg */
const PETROL_PER_TNT = 4.184e6 / (0.02 * 43.7e6);
const POOL_FLUX = 2.4e6;

interface Flame { handles: VfxHandle[]; main: VfxHandle | null; kind: string; heat: number; at: number; what: string }

export interface FxStats { fxMs: number; drawMs: number; particles: number; effects: number; level: string; skipped: number }

export class FxDirector {
  private flames = new Map<string, Flame>();
  private follow = new Map<number, (out: V3) => boolean>();
  private nextEnt = 1;
  private warned = new Set<string>();
  /** shake of the camera, 0..1 (squared when applied) and the warm flash of a blast on the whole street, 0..1 */
  trauma = 0; flash = 0; private warm = 0;
  private phase: [number, number, number, number, number, number] = [0, 1.7, 3.1, 4.3, 5.9, 7.7];
  private seenDebris = new Set<number>();
  private blastWhat = new Map<string, string>();
  private skidAt = new Map<string, number>();
  private scrapeAt = new Map<string, number>();
  private last = new Map<string, number>();
  /** the governor may be switched off for a check that wants every particle (take37.view.fx.govOn = false) */
  govOn = true;
  readonly gov = new Governor({ targetMs: 7, maxParticles: 14000, downAfter: 12, upAfter: 240 });
  stats: FxStats = { fxMs: 0, drawMs: 0, particles: 0, effects: 0, level: 'full', skipped: 0 };
  private msStep = 0; private emaMs = 0;
  /** every spawn by name that the game made, for the checks */
  readonly spawned = new Map<string, number>();
  private camera: V3 = [0, 0, 0];
  private simT = 0;

  constructor(readonly vfx: VfxSystem) {
    vfx.registerAll(TAKE37_FX as never);
    vfx.host = {
      groundHeight: () => 0,
      attachment: (a: { entity: number }, out: V3) => { const f = this.follow.get(a.entity); return f ? f(out) : false; },
    } as never;
  }

  reset() {
    for (const f of this.flames.values()) for (const h of f.handles) this.vfx.stop(h as never);
    this.flames.clear(); this.follow.clear(); this.seenDebris.clear(); this.blastWhat.clear(); this.skidAt.clear(); this.scrapeAt.clear(); this.last.clear();
    this.trauma = 0; this.flash = 0; this.warm = 0;
  }

  /** every effect name this director can spawn, for the first-use shader warm-up (view.ts): the game's own definitions and the catalogue ones it asks for */
  warmNames(): string[] {
    const own = TAKE37_FX.map((d) => d.name), cat = ['impact.metal', 'blast.secondary', 'dust.collapse', 'electric.short-circuit', 'electric.arc', 'water.fountain', 'impact.wood', 'fire.vehicle', 'fire.pool-petrol', 'fire.torch', 'fire.building', 'fire.jet', 'fire.ruins', 'smoke.chimney', 'blast.fuel-air', 'blast.vessel', 'blast.he-ground', 'rocket.small'];
    return [...own, ...cat].filter((n) => this.vfx.has(n));
  }

  // ---- spawning ----
  has(name: string) { return this.vfx.has(name); }
  spawn(name: string, at: V3, params: Record<string, number> = {}, o: { direction?: V3; attach?: (out: V3) => boolean; delay?: number } = {}): VfxHandle | null {
    if (!this.vfx.has(name)) { if (!this.warned.has(name)) { console.warn('vfx not registered', name); this.warned.add(name); } return null; }
    try {
      let attach: { entity: number } | undefined;
      if (o.attach) { const id = this.nextEnt++; this.follow.set(id, o.attach); attach = { entity: id }; }
      const h = this.vfx.spawn(name, { at, params, ...(o.direction ? { direction: o.direction } : {}), ...(attach ? { attach } : {}), ...(o.delay ? { delay: o.delay } : {}) } as never);
      this.spawned.set(name, (this.spawned.get(name) ?? 0) + 1);
      return h;
    } catch (e) { if (!this.warned.has(name)) { console.warn('vfx spawn', name, String(e).slice(0, 300)); this.warned.add(name); } return null; }
  }
  /** a spawn that the budget may refuse: far from the camera, or while the effects are over their budget and this is a small one */
  private near(at: V3, within: number) { return Math.hypot(at[0] - this.camera[0], at[2] - this.camera[2]) < within; }
  private cheap(name: string, at: V3, params: Record<string, number>, within = 260, o: { direction?: V3; attach?: (out: V3) => boolean } = {}): VfxHandle | null {
    if (!this.near(at, within) || (this.vfx.count > 150 && this.gov.level > 1)) { this.stats.skipped++; return null; }
    return this.spawn(name, at, params, o);
  }
  private every(key: string, dt: number): boolean { const t = this.last.get(key) ?? -1e9; if (this.simT - t < dt) return false; this.last.set(key, this.simT); return true; }

  // ---- events ----
  handle(e: SimEvent, take: Take) {
    const sim = take.scene.sim, p = take.scene.player.veh.pos;
    const dPlayer = (at: V3) => Math.hypot(at[0] - p[0], at[2] - p[2]);
    switch (e.type) {
      case 'impact': {
        // car against car or against the street: the harder the work, the more sparks, the flash, the dust and the shake (only the player's neighbourhood shakes the cab)
        const at: V3 = [e.at[0], Math.max(0.25, e.at[1]), e.at[2]], E = Math.max(2000, e.energy);
        this.cheap('take37.sparks', at, { energy: E }, 300);
        if (E > 12e3) this.cheap('take37.dirt-kick', [at[0], 0.1, at[2]], { energy: E });
        if (e.speed > 9 && E > 60e3) this.cheap('impact.metal', at, { energy: Math.min(2e5, E) }, 200);
        if (E > 250e3) this.cheap('blast.secondary', at, { tnt: clamp(E / 4.184e6 * 6, 0.15, 3) }, 120);
        this.addTrauma(clamp(Math.sqrt(E / 700e3), 0, 0.85), dPlayer(at), 70, e.a === take.scene.player.id || e.b === take.scene.player.id ? 1 : 0.6);
        this.flash = Math.max(this.flash, clamp(E / 3e6, 0, 0.25) * clamp(1 - dPlayer(at) / 90, 0, 1));
        break;
      }
      case 'scrape': {
        const key = e.car; if (!this.every('scr' + key, 0.07)) break;
        this.cheap('take37.scrape', [e.at[0], Math.max(0.1, e.at[1]), e.at[2]], { speed: e.speed }, 180, { direction: e.dir });
        this.addTrauma(clamp(e.speed / 60, 0, 0.3), dPlayer(e.at), 40, 0.4);
        break;
      }
      case 'detach': {
        const at: V3 = [e.at[0], e.at[1] + 0.6, e.at[2]];
        this.cheap('take37.sparks', at, { energy: 25e3 }, 220);
        break;
      }
      case 'wreck': {
        // a car that is finished: dark smoke from the engine in proportion to the crush work it took (Car.damage, 1 = the work that makes a wreck), and the engine's own small flame when its tank has been opened
        // (the fire world's leak), not by chance: a wreck with a whole tank only smokes
        const car = sim.cars.find((c) => c.id === e.car); if (!car) break;
        const eng = (out: V3) => { const w = car.veh.toWorld([car.kind === 'tanker' ? 3.5 : 1.55, 0.85, 0]); out[0] = w[0]; out[1] = w[1]; out[2] = w[2]; return true; };
        const leaking = take.scene.fire.store(car.id)?.leaking ?? false;
        if (car.kind !== 'tanker' && !this.flames.has('engine:' + car.id)) {
          if (leaking) {
            const h = this.spawn('fire.vehicle', car.veh.toWorld([1.55, 0.85, 0]) as V3, { heat: 8e5, D: 1.0 }, { attach: eng });
            if (h) this.flames.set('engine:' + car.id, { handles: [h], main: h, kind: 'engine', heat: 8e5, at: sim.t, what: 'car' });
          } else {
            const h = this.spawn('smoke.chimney', car.veh.toWorld([1.55, 0.85, 0]) as V3, { heat: clamp(1.5e4 * car.damage, 1.5e4, 8e4), D: 0.6 }, { attach: eng });
            if (h) this.flames.set('engine:' + car.id, { handles: [h], main: h, kind: 'smoke', heat: 2e4, at: sim.t, what: 'car' });
          }
        }
        this.cheap('take37.piece-trail', car.veh.toWorld([1.55, 0.85, 0]) as V3, { glowing: leaking ? 0.6 : 0.2 }, 300, { attach: eng });
        break;
      }
      case 'spill': {
        const at: V3 = [e.at[0], 0.03, e.at[2]];
        const d = clamp(2 * Math.sqrt(e.kg / (740 * Math.PI * 0.01)), 0.8, 28);   // a film 1 cm deep
        this.cheap('take37.spill', at, { size: d * (e.id.includes('tank') ? 0.6 : 0.4) }, 320);
        break;
      }
      case 'ignite': this.ignite(e, take); break;
      case 'burning': this.burning(e); break;
      case 'out': this.out(e.id, e.what, take); break;
      case 'blast': this.blast(e, take, dPlayer(e.at)); break;
      case 'collapse': {
        this.spawn('dust.collapse', [e.at[0], 0.2, e.at[2]], { size: 7 });
        this.cheap('take37.flash', [e.at[0], 2, e.at[2]], { tnt: 4 }, 300);
        this.cheap('take37.sparks', [e.at[0], 3, e.at[2]], { energy: 800e3 }, 300);
        this.addTrauma(0.7, dPlayer(e.at), 140, 1);
        break;
      }
      case 'prop': this.propBroken(e); break;
    }
  }

  private addTrauma(amount: number, dist: number, reach: number, k = 1) { this.trauma = Math.min(1, Math.max(this.trauma, amount * k * clamp(1 - dist / (reach * 2.2), 0, 1) + Math.min(0.2, this.trauma * 0.1))); }

  private propBroken(e: Extract<SimEvent, { type: 'prop' }>) {
    const at: V3 = [e.at[0], Math.max(0.2, e.at[1]), e.at[2]], k = e.kind;
    if (e.how !== 'broken' && e.how !== 'fell' && e.how !== 'knocked') return;
    if (k === 'Window') { this.cheap('take37.glitter', at, { size: 2.2 }, 260); this.cheap('take37.dirt-kick', [at[0], 0.1, at[2]], { energy: 6000 }, 200); return; }
    if (k === 'Facade') { this.spawn('dust.collapse', [at[0], 0.3, at[2]], { size: 5 }); this.cheap('take37.dirt-kick', [at[0], 0.2, at[2]], { energy: 400e3 }, 400); this.cheap('take37.sparks', at, { energy: 200e3 }, 300); return; }
        if (k === 'PhoneBooth') { this.cheap('take37.glitter', at, { size: 1.6 }, 240); this.cheap('electric.short-circuit', at, {}, 160); return; }
    if (/Pole|TrafficLight|Lamp/.test(k)) { this.cheap('electric.short-circuit', [at[0], Math.max(at[1], 4), at[2]], {}, 220); this.cheap('electric.arc', [at[0], 3.5, at[2]], { length: 2.5, current: 4000 }, 160); this.cheap('take37.sparks', [at[0], 3.5, at[2]], { energy: 120e3 }, 220); this.cheap('take37.dirt-kick', [at[0], 0.1, at[2]], { energy: 40e3 }, 220); return; }
    if (k === 'Hydrant') { this.cheap('water.fountain', [at[0], 0.15, at[2]], { pressure: 400e3 }, 200); this.cheap('take37.dirt-kick', [at[0], 0.1, at[2]], { energy: 20e3 }, 200); return; }
    if (/Bench|Sawhorse|Crate|Fence|Sign/.test(k)) { this.cheap('impact.wood', at, { energy: 12e3 }, 200); return; }
    this.cheap('take37.dirt-kick', [at[0], 0.1, at[2]], { energy: 15e3 }, 220);
    this.cheap('take37.sparks', at, { energy: 15e3 }, 200);
  }

  /** the glass of a car or a window bursts (the module's pieces fly; this is the light they throw back) */
  glass(origin: V3, size: number) { this.cheap('take37.glitter', origin, { size }, 260); }

  // ---- fire ----
  private carOf(take: Take, id: string): Car | undefined { return take.scene.sim.cars.find((c) => c.id === id || id.startsWith(c.id + '.')); }
  private ignite(e: Extract<SimEvent, { type: 'ignite' }>, take: Take) {
    if (this.flames.has(e.id)) return;
    const car = this.carOf(take, e.id), at = e.at;
    const handles: VfxHandle[] = [];
    let main: VfxHandle | null = null, kind = '', heat = Math.max(2e5, e.power);
    const local: V3 | null = car ? (car.veh.toLocal(at) as V3) : null;
    const pos = (dy = 0) => (out: V3) => { if (car && local) { const w = car.veh.toWorld(local); out[0] = w[0]; out[1] = w[1] + dy; out[2] = w[2]; } else { out[0] = at[0]; out[1] = at[1] + dy; out[2] = at[2]; } return true; };
    const ground = Math.max(0.05, at[1] - 1);
    if (e.what === 'tanker') {
      const P = clamp(heat, 5e6, 5e7), D = clamp(2 * Math.sqrt(P / POOL_FLUX / Math.PI), 3, 9);
      kind = 'fire.pool-petrol'; heat = P;
      main = this.spawn('fire.pool-petrol', [at[0], 0.6, at[2]], { heat: P, D }, { attach: pos(-1.3) });
    } else if (e.what === 'car') {
      kind = 'fire.vehicle'; heat = clamp(heat, 1.5e6, 6e6);
      main = this.spawn('fire.vehicle', [at[0], Math.max(0.2, at[1] - 0.2), at[2]], { heat, D: 2 }, { attach: pos(-0.1) });
      const D = clamp(2 * Math.sqrt(heat / POOL_FLUX / Math.PI), 1.2, 3.2);
      const pool = this.spawn('fire.pool-petrol', [at[0], 0.04, at[2]], { heat: heat * 0.5, D });
      if (pool) handles.push(pool);
    } else if (e.what === 'pump') {
      const P = clamp(heat, 2e6, 3e7); kind = 'fire.pool-petrol'; heat = P;
      main = this.spawn('fire.pool-petrol', [at[0], ground, at[2]], { heat: P, D: clamp(2 * Math.sqrt(P / POOL_FLUX / Math.PI), 1.2, 4) });
      const jet = this.spawn('fire.torch', [at[0], at[1] + 0.3, at[2]], { heat: 6e5, D: 0.3 }); if (jet) handles.push(jet);
    } else if (e.what === 'canopy') {
      kind = 'fire.building'; heat = Math.max(8e6, e.power * 60);
      main = this.spawn('fire.building', [at[0], at[1] + 0.3, at[2]], { heat, D: 5 });
    } else if (e.what === 'propane') {
      kind = 'fire.jet'; heat = 6e6;
      main = this.spawn('fire.jet', [at[0], at[1], at[2]], { heat, length: 9 }, { direction: [0.35, 0.8, 0.2] });
    } else { kind = 'fire.vehicle'; main = this.spawn('fire.vehicle', [at[0], at[1], at[2]], { heat }); }
    if (main) handles.unshift(main);
    this.flames.set(e.id, { handles, main, kind, heat, at: e.t, what: e.what });
    this.flash = Math.max(this.flash, e.what === 'tanker' ? 0.4 : 0.15);
    // the whoosh of fuel catching: a small flash and a roll of sparks
    this.cheap('take37.flash', [at[0], at[1], at[2]], { tnt: e.what === 'tanker' ? 3 : e.what === 'canopy' ? 1.2 : 0.4 }, 300);
  }
  private burning(e: Extract<SimEvent, { type: 'burning' }>) {
    const f = this.flames.get(e.id); if (!f?.main) return;
    // the fire grows over its first seconds (a car fire takes a while to take hold) and then follows the fuel's burning power
    const age = e.t - f.at, grow = f.what === 'canopy' ? clamp(0.25 + age / 12, 0.25, 1.4) : clamp(0.35 + age / 6, 0.35, 1), now = clamp(e.power * (f.what === 'tanker' || f.what === 'pump' ? 1 : 1) * grow, 2e5, f.kind === 'fire.pool-petrol' && f.what === 'tanker' ? 1.1e8 : 1e9);
    const heat = f.what === 'canopy' ? Math.max(f.heat * 0.25, f.heat * grow) : f.what === 'car' ? clamp(now, 1e6, 6e6) : now;
    if (Math.abs(heat - f.heat) / f.heat > 0.12) { this.vfx.setParam(f.main, 'heat', heat); f.heat = heat; }
  }
  private out(id: string, what: string, take: Take) {
    const f = this.flames.get(id); if (!f) return;
    for (const h of f.handles) this.vfx.stop(h);
    this.flames.delete(id);
    // what is left smoulders: a wreck gives thin dark smoke and glowing embers for a long time
    const car = this.carOf(take, id);
    if (what === 'car' || what === 'tanker') {
      const at = car ? (car.veh.pos as V3) : [0, 0, 0] as V3;
      const pos = (out: V3) => { if (!car) return false; const w = car.veh.toWorld([0.6, 0.5, 0]); out[0] = w[0]; out[1] = w[1]; out[2] = w[2]; return true; };
      const h = this.spawn('fire.ruins', [at[0], at[1], at[2]], { D: what === 'tanker' ? 3 : 1.8 }, { attach: pos }); if (h) this.flames.set('ruins:' + id, { handles: [h], main: h, kind: 'ruins', heat: 4000, at: take.scene.sim.t, what });
      const s = this.spawn('smoke.chimney', [at[0], at[1] + 0.5, at[2]], { heat: what === 'tanker' ? 9e4 : 2.5e4, D: what === 'tanker' ? 1.6 : 0.8 }, { attach: pos }); if (s) this.flames.get('ruins:' + id)?.handles.push(s);
    } else if (what === 'pump' || what === 'canopy') {
      const at = f.handles.length ? null : null; void at;
    }
  }

  // ---- blasts ----
  private blast(e: Extract<SimEvent, { type: 'blast' }>, take: Take, dist: number) {
    this.blastWhat.set(e.id, e.what);
    const tnt = Math.max(0.5, e.tnt), at: V3 = [e.at[0], Math.max(0.5, e.at[1]), e.at[2]];
    const mid: V3 = [at[0], Math.max(1.2, at[1]), at[2]];
    if (e.what === 'tanker') {
      this.spawn(this.vfx.has('take37.fireball') ? 'take37.fireball' : 'blast.fuel-air', [at[0], 0.3, at[2]], { fuel: clamp(tnt * PETROL_PER_TNT, 40, 5000) });
      this.spawn('take37.flash', [at[0], 1.5, at[2]], { tnt: clamp(tnt, 2, 800) });
    } else if (e.what === 'propane' || e.what === 'pump') {
      this.spawn('blast.vessel', mid, { tnt: clamp(tnt, 0.3, 200), hot: 1 });
      this.spawn('take37.flash', mid, { tnt: clamp(tnt * 0.6, 1, 120) });
    } else {
      this.spawn('blast.he-ground', [at[0], 0.3, at[2]], { tnt: clamp(tnt, 0.5, 400) });
      this.spawn('take37.flash', mid, { tnt: clamp(tnt, 1, 200) });
    }
    // the shock, the flash on the street and the shake: scaled by the TNT and the distance (the cab shakes up to about 400 m)
    const base = clamp(Math.log10(1 + tnt) / 1.9, 0.15, 1);
    this.addTrauma(base, dist, 190);
    this.flash = Math.max(this.flash, clamp(Math.log10(1 + tnt) / 2.2, 0.1, 1) * clamp(1.15 - dist / 500, 0.15, 1));
    void take;
  }

  /** shake offsets of the camera for this frame: position in metres and a turn in radians (yaw, pitch, roll); `scale` is smaller for a set camera than for the cab */
  shake(dt: number, scale = 1): { p: V3; r: V3 } {
    this.trauma = Math.max(0, this.trauma - dt * 0.55);
    const s = this.trauma * this.trauma * scale;
    if (s < 1e-4) return { p: [0, 0, 0], r: [0, 0, 0] };
    for (let i = 0; i < 6; i++) this.phase[i] = (this.phase[i]! + dt * (18 + i * 5)) % 1000;
    const n = (i: number) => Math.sin(this.phase[i]! * 1.7) * 0.6 + Math.sin(this.phase[i]! * 4.1 + i) * 0.4;
    return { p: [n(0) * 0.28 * s, n(1) * 0.2 * s, n(2) * 0.28 * s], r: [n(3) * 0.06 * s, n(4) * 0.05 * s, n(5) * 0.09 * s] };
  }
  /** the warm flash of a blast: 0..1, decays in about a second and a half; the caller lifts the scene's sky light by it */
  flashLevel(dt: number): number { this.flash = Math.max(0, this.flash - dt * 0.9); return this.flash; }

  // ---- every frame ----
  frame(take: Take, dt: number, cam: V3) {
    const sim = take.scene.sim; this.camera = cam; this.simT = sim.t;
    // flames of cars and of the tanker follow through the attachment; a fire effect far away is thinned by the ladder; nothing else to do per flame here
    const cars = sim.cars;
    for (const c of cars) {
      const v = c.veh; if (v.sleeping && c.role === 'parked') continue;
      const d = Math.hypot(v.pos[0] - cam[0], v.pos[2] - cam[2]); if (d > 150) continue;
      const sp = Math.hypot(v.vel[0], v.vel[2]);
      const f = qRot(v.rot, [1, 0, 0]), s = qRot(v.rot, [0, 0, 1]);
      // tyre slip: the wheel's rim speed against the car's speed along the wheel, and the sideways speed at the patch
      const k = this.skidAt.get(c.id) ?? 0; let any = 0;
      if (this.simT - k > 0.05 && sp > 2.5) {
        for (const w of v.wheels) {
          if (!w.attached || !w.onGround || w.load < 800) continue;
          const patch = v.toWorld([w.mount[0], w.mount[1] - w.spec.radius, w.mount[2]]);
          const vc = v.velocityAt(patch), vl = vc[0] * f[0] + vc[2] * f[2], vt = vc[0] * s[0] + vc[2] * s[2];
          const rim = w.spin * w.spec.radius, lock = Math.abs(vl) > 4 ? clamp((Math.abs(vl) - Math.abs(rim)) / Math.abs(vl), 0, 1) : 0;
          const amount = clamp(Math.max(Math.abs(vt) - 2.2, 0) / 6 + (lock > 0.55 ? (lock - 0.4) * 0.9 : 0) + (Math.abs(rim - vl) > 9 && Math.abs(vl) < 10 ? 0.5 : 0), 0, 1);
          if (amount > 0.12) { any = 1; this.cheap('take37.tyre-smoke', [patch[0], 0.06, patch[2]], { amount, speed: sp }, 170); }
        }
        if (any) this.skidAt.set(c.id, this.simT);
      }
      // a car on its side or its roof, or one with its wheels gone, drags metal over the road
      const low = v.tilt() > 1.0 || v.wheels.filter((w) => !w.attached).length >= 2;
      if (low && sp > 4 && this.every('sl' + c.id, 0.08)) {
        const at = v.toWorld([0, -0.3, 0]); const dir: V3 = [-v.vel[0], 0.3, -v.vel[2]];
        this.cheap('take37.scrape', [at[0], 0.12, at[2]], { speed: sp }, 170, { direction: dir });
        this.addTrauma(clamp(sp / 80, 0, 0.25), Math.hypot(at[0] - take.scene.player.veh.pos[0], at[2] - take.scene.player.veh.pos[2]), 40, 0.5);
      }
      // a burning car on the move leaves a trail of sparks and burning bits: only a brake-less burning wreck keeps rolling
    }
    // pieces in flight: thrown parts of cars and fragments of tanks get a trail
    const live = new Set<number>();
    for (const d of sim.debris) {
      live.add(d.id);
      if (this.seenDebris.has(d.id)) continue;
      this.seenDebris.add(d.id);
      if (d.kind === 'matthew' || (!d.node && d.kind !== 'shell') || this.vfx.count > 130) continue;
      const burningOwner = this.flames.has(d.ref) || [...this.flames.keys()].some((k) => k.startsWith(d.ref + '.'));
      const shell = d.kind === 'shell', hot = shell || burningOwner || sim.rng.chance(0.3);
      if (!hot) continue;
      const attach = this.piece(d);
      if (!this.near(d.pos as V3, 320)) continue;
      this.spawn('take37.piece-trail', [d.pos[0], d.pos[1], d.pos[2]], { glowing: shell || burningOwner ? 1 : 0.5 }, { attach });
      if (shell && /propane|Propane/.test(d.ref + (this.blastWhat.get(d.ref) ?? ''))) this.spawn('rocket.small', [d.pos[0], d.pos[1], d.pos[2]], { heat: 2.5e7, D: 0.08 }, { attach, direction: [d.vel[0], d.vel[1], d.vel[2]] });
      else if (shell && burningOwner === false && sim.rng.chance(0.5)) this.spawn('fire.torch', [d.pos[0], d.pos[1], d.pos[2]], { heat: 8e3, D: 0.12 }, { attach });
    }
    for (const id of [...this.follow.keys()]) { /* entries stay while their effect runs; trimmed below */ void id; }
    if (this.follow.size > 400) { const ks = [...this.follow.keys()]; for (let i = 0; i < ks.length - 200; i++) this.follow.delete(ks[i]!); }
    void live;
  }
  private piece(d: Debris): (out: V3) => boolean {
    return (out) => { out[0] = d.pos[0]; out[1] = d.pos[1]; out[2] = d.pos[2]; return true; };
  }

  // ---- budget ----
  beginStep() { return performance.now(); }
  endStep(t0: number) { this.msStep += performance.now() - t0; }
  /** after the frame's draw: feed the governor with what the effects cost this frame (the fixed steps and the draw) */
  endFrame(drawMs: number) {
    const total = this.msStep + drawMs; this.emaMs += (total - this.emaMs) * 0.1;
    const parts = this.vfx.particles;
    if (this.govOn) { if (this.gov.update(total, parts)) this.gov.apply(this.vfx); } else if (this.gov.level !== 0) { this.gov.reset(); this.gov.apply(this.vfx); }
    this.stats = { fxMs: +this.msStep.toFixed(2), drawMs: +drawMs.toFixed(2), particles: parts, effects: this.vfx.count, level: this.gov.step.name, skipped: this.stats.skipped };
    this.msStep = 0;
  }
}
