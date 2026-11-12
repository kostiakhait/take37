// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// The flow of scene 1: briefing, clapperboard, the chase, the end of the take ("Cut!" or "That's a wrap"), the director's reaction, the budget, the best take. Pure (storage is passed in).
import { BUDGET_START, TAKE_COST, TAKE_LIMIT, STREET_END_X, SET_BOUNDS, SCORE, FIXED_DT } from './config';
import { buildScene1, type KindInfos, type Scene1 } from './scene1';
import { Spectacle, type Clip, type FrameShot } from './scoring';
import { qRot } from '@ferret/destruction/vehicle';
import type { Layout } from './layout';
import type { Car } from './sim';

export type Phase = 'brief' | 'clapper' | 'play' | 'verdict' | 'choice' | 'over';
export type Verdict = 'cut' | 'wrap';
export interface PlayerInput { gas: boolean; brake: boolean; steer: number; handbrake: boolean; jump: boolean; cut: boolean; horn: boolean; siren: boolean }
export interface Storage { get(k: string): string | null; set(k: string, v: string): void }
export interface BestTake { take: number; points: number; clips: Clip[]; shots: FrameShot[]; time: number }

export interface Outcome { verdict: Verdict; reason: string; text: string; points: number }

export class Take {
  budget = BUDGET_START;
  takeNo = 0;
  phase: Phase = 'brief';
  phaseT = 0;
  /** play time of this take, s */ t = 0;
  scene!: Scene1; spec!: Spectacle;
  outcome: Outcome | null = null;
  best: BestTake | null = null;
  /** matthew has left the car */ out = false; outAt = -1;
  /** a body that jumped */ matthewDebris = -1;
  private calmSince = -1; private thresholdAt = -1;
  siren = false; horn = false;

  constructor(private layout: Layout, private infos: KindInfos, private store: Storage) {
    try { const b = store.get('take37.scene1.best'); if (b) this.best = JSON.parse(b) as BestTake; const bu = store.get('take37.budget'); if (bu) this.budget = +bu; const n = store.get('take37.takes'); if (n) this.takeNo = +n; } catch { /* a first run */ }
    if (this.budget <= 0) this.phase = 'over';
  }

  /** the next take: costs a take's budget, builds the street with the take's variations */
  begin(seedOffset = 0) {
    this.takeNo++; this.budget -= TAKE_COST;
    this.persist();
    this.scene = buildScene1(this.layout, this.infos, this.takeNo * 31 + 7 + seedOffset);
    this.spec = new Spectacle(this.scene.sim);
    this.t = 0; this.outcome = null; this.out = false; this.outAt = -1; this.matthewDebris = -1; this.calmSince = -1; this.thresholdAt = -1;
    this.phase = 'brief'; this.phaseT = 0;
  }
  private persist() { try { this.store.set('take37.budget', String(this.budget)); this.store.set('take37.takes', String(this.takeNo)); } catch { /* storage may be blocked */ } }
  get player(): Car { return this.scene.player; }

  /** the player's wish to the car */
  private drivePlayer(inp: PlayerInput) {
    const c = this.scene.player;
    if (!c.occupied || c.wrecked && !c.occupied) { c.ctl.throttle = 0; c.ctl.brake = 0; c.ctl.steer = 0; return; }
    const fwd = qRot(c.veh.rot, [1, 0, 0]), v = c.veh.vel[0] * fwd[0] + c.veh.vel[2] * fwd[2];
    c.ctl.steer = inp.steer;
    if (inp.handbrake) { c.ctl.throttle = 0; c.ctl.brake = 1; return; }
    if (inp.gas && !inp.brake) { c.ctl.throttle = 1; c.ctl.brake = 0; }
    else if (inp.brake && !inp.gas) { if (v > 1.0) { c.ctl.brake = 1; c.ctl.throttle = 0; } else { c.ctl.brake = 0; c.ctl.throttle = -1; } }
    else { c.ctl.throttle = 0; c.ctl.brake = 0; }
  }
  private jumpOut() {
    const c = this.scene.player, sim = this.scene.sim; if (!c.occupied) return;
    c.occupied = false; c.ejected = true; this.out = true; this.outAt = this.t;
    c.ctl.throttle = 0; c.ctl.brake = 0; c.ctl.steer = 0;
    const seat = c.veh.toWorld([0.2, 1.1, 0.4]), side = qRot(c.veh.rot, [0, 0, 1]);
    sim.debris.push({ id: 999001, ref: 'matthew', pos: seat, vel: [c.veh.vel[0] + side[0] * 4, c.veh.vel[1] + 3.5, c.veh.vel[2] + side[2] * 4], rot: [0, 0, 0, 1], ang: [3, 0.5, 2], half: [0.25, 0.25, 0.25], mass: 80, resting: false, age: 0, kind: 'matthew' });
    this.matthewDebris = 999001;
  }

  /** one fixed step of the whole take */
  step(inp: PlayerInput, dt = FIXED_DT) {
    this.phaseT += dt;
    this.horn = inp.horn;
    if (this.phase === 'brief') { if (this.phaseT > 4.5) { this.phase = 'clapper'; this.phaseT = 0; } return; }
    if (this.phase === 'clapper') { if (this.phaseT > 2.4) { this.phase = 'play'; this.phaseT = 0; } this.scene.sim.step(dt); this.scene.sim.drain(); return; }
    if (this.phase === 'verdict') { this.runWorld(dt); if (this.phaseT > 9) { this.phase = this.budget <= 0 ? 'over' : 'choice'; this.phaseT = 0; } return; }
    if (this.phase !== 'play') { this.runWorld(dt); return; }
    this.t += dt;
    if (inp.jump && !this.out) this.jumpOut();
    this.drivePlayer(inp);
    this.runWorld(dt);
    this.judge(inp);
  }
  private runWorld(dt: number) {
    const sim = this.scene.sim; sim.step(dt);
    const ev = sim.drain(); this.spec.consume(ev); this.pending.push(...ev);
  }
  /** events of the last steps for the view (sparks, flames, sounds): taken and cleared by the caller */
  pending: import('./sim').SimEvent[] = [];
  takeEvents() { const e = this.pending; this.pending = []; return e; }

  private judge(inp: PlayerInput) {
    const s = this.scene, p = s.player.veh.pos, vin = s.vincent.veh.pos;
    const points = this.spec.total;
    if (points >= SCORE.wrapAt && this.thresholdAt < 0) this.thresholdAt = this.t;
    // calm: nothing scored for a while after the big moment
    const calm = this.t - this.spec.lastAt > 7 && this.spec.lastAt > 0;
    if (this.thresholdAt >= 0 && (calm || this.t - this.thresholdAt > 40)) return this.finish('wrap', 'spectacle');
    if (inp.cut) return this.finish(points >= SCORE.wrapAt ? 'wrap' : 'cut', 'self');
    const outside = (x: number, z: number) => x < SET_BOUNDS.x0 || x > SET_BOUNDS.x1 || Math.abs(z) > SET_BOUNDS.halfWidth;
    if (outside(p[0], p[2]) && !this.out) return this.finish('cut', 'left');
    if (p[0] > STREET_END_X || vin[0] > STREET_END_X) return this.finish(points >= SCORE.wrapAt ? 'wrap' : 'cut', 'end');
    if (this.t > TAKE_LIMIT) return this.finish(points >= SCORE.wrapAt ? 'wrap' : 'cut', 'time');
  }

  private finish(verdict: Verdict, reason: string) {
    const pts = this.spec.total;
    this.outcome = { verdict, reason, points: pts, text: directorSays(verdict, reason, this.spec, this.scene) };
    this.phase = 'verdict'; this.phaseT = 0;
    if (verdict === 'wrap' && (!this.best || pts > this.best.points)) {
      this.best = { take: this.takeNo, points: Math.round(pts), clips: this.spec.clips, shots: this.spec.shots.filter((x) => x.factor > 0), time: this.t };
      try { this.store.set('take37.scene1.best', JSON.stringify(this.best)); } catch { /* storage may be blocked */ }
    }
    this.persist();
  }
  /** the take ends by hand (for tests and the pause menu) */
  forceFinish(verdict: Verdict, reason: string) { this.finish(verdict, reason); }
  /** "another take" */
  again() { if (this.budget > 0) this.begin(); else this.phase = 'over'; }
}

/** the director's reaction, text only (the voice comes later); never a number */
export function directorSays(verdict: Verdict, reason: string, spec: Spectacle, s: Scene1): string {
  if (verdict === 'cut') {
    if (reason === 'left') return 'CUT! Where are you going?! That is the end of the set, Matthew, the street is behind you! Again!';
    if (reason === 'end') return spec.wrecks === 0 ? 'CUT! You drove the whole street and broke NOTHING! This is a car chase, not a Sunday drive! Again!' : 'CUT! A scratch here, a dent there... I can get that from a parking lot! Where is the spectacle? Again!';
    if (reason === 'time') return 'CUT! Time! The sun is going down, the crew is asleep and nothing has blown up! Again!';
    return spec.wrecks === 0 ? 'CUT! Nothing happened! Matthew, I pay you to wreck things! Again!' : 'CUT! Not enough! The audience will yawn! More cars, more fire! Again!';
  }
  const big = spec.tankerBurnt && spec.stationBurnt;
  if (big) return 'THAT\'S A WRAP! The tanker, the station, the whole block! Arnold, did you see that?! The studio will be in tears! Print it!';
  if (spec.tankerBurnt) return 'THAT\'S A WRAP! A burning tanker! Now THIS is cinema! Print it, and somebody call the fire brigade!';
  if (spec.total > 3000) return 'That\'s a wrap! Fire, wrecks, the whole street! Good, Matthew. Very good. Do not tell Arnold I said so.';
  void s;
  return 'That\'s a wrap. It will do. I will hide the weak part in the middle. But the tanker and the station are right there, Matthew!';
}
