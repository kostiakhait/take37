// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import { Pilot, type Aeroplane } from '@ferret/physics-vehicles';

/**
 * The take-off run of the Mustang on this field: the engine's `Aeroplane` (the sample's own P-51D spec) on the field's real ground query, a pilot of simple rules (full throttle, the rudder keeps the heading and the line,
 * the stick is eased back at rotation speed, the gear comes up after lift-off, then a climb). It measures what the brief asks: the roll to lift-off, the lift-off speed, the climb, and the contacts' state.
 * Frames: the flight model is north/east/down; the runway runs toward north (scene -z); `lineE` is the runway's centre in east (0).
 */
export interface TakeoffLog { rollM: number; liftOffIAS: number; liftOffTAS: number; liftOffT: number; maxLateral: number; altitudeAfter: number[]; crashed: boolean; samples: Array<{ t: number; ias: number; alt: number; n: number; e: number; pitch: number; ground: boolean }> }
export interface TakeoffOptions { startNorth: number; lineE?: number; headingDeg?: number; rotateAt?: number; dt?: number; maxT?: number; climbTo?: number; onFrame?: (t: number) => void }

export class TakeoffRun {
  readonly pilot: Pilot;
  log: TakeoffLog = { rollM: 0, liftOffIAS: 0, liftOffTAS: 0, liftOffT: 0, maxLateral: 0, altitudeAfter: [], crashed: false, samples: [] };
  t = 0; private lifted = false; private n0 = 0; private gearUpAt = -1; private o: Required<Omit<TakeoffOptions, 'onFrame'>> & { onFrame?: (t: number) => void };
  private yawI = 0; private air = 0;
  constructor(readonly plane: Aeroplane, o: TakeoffOptions) {
    this.o = { lineE: 0, headingDeg: 0, rotateAt: 42, dt: 1 / 120, maxT: 90, climbTo: 300, ...o };
    this.pilot = new Pilot(plane); plane.park(o.startNorth, this.o.lineE, this.o.headingDeg); this.n0 = o.startNorth;
    plane.controls.gearDown = true; plane.controls.flaps = 0;
  }
  /** one step of the pilot and the flight model (returns false when the run is over) */
  step(): boolean {
    const p = this.plane, o = this.o, dt = o.dt, r = p.out, ias = r.indicatedAirspeed, hdgErr = ((r.heading - o.headingDeg + 540) % 360) - 180, lat = p.pos[1] - o.lineE;
    // rudder: keeps the heading and the line (positive yaw = right; east is right of a northward run)
    this.yawI += hdgErr * dt;
    const yaw = Math.max(-1, Math.min(1, -(0.06 * hdgErr + 0.015 * lat + 0.01 * this.yawI + (this.lifted ? 0 : 0))));
    const pitchCmd = ias < o.rotateAt && !this.lifted ? 0 : (this.lifted ? this.climbPitch(r) : 0.28);
    this.pilot.update({ pitch: pitchCmd, roll: Math.max(-1, Math.min(1, -0.04 * r.roll)), yaw, throttle: 1, flaps: 0, brake: 0, gearDown: !(this.lifted && this.t > this.gearUpAt) }, dt);
    p.step(dt); this.t += dt; o.onFrame?.(this.t);
    this.log.maxLateral = Math.max(this.log.maxLateral, Math.abs(p.pos[1] - o.lineE));
    if (!p.out.onGround) this.air += dt; else this.air = 0;
    if (!this.lifted && this.air > 0.4 && this.t > 1) { this.lifted = true; this.log.rollM = p.pos[0] - this.n0; this.log.liftOffIAS = p.out.indicatedAirspeed; this.log.liftOffTAS = p.out.trueAirspeed; this.log.liftOffT = this.t; this.gearUpAt = this.t + 2.5; }
    if (Math.floor(this.t * 10) !== Math.floor((this.t - dt) * 10)) this.log.samples.push({ t: +this.t.toFixed(1), ias: +p.out.indicatedAirspeed.toFixed(1), alt: +(p.altitude - 0).toFixed(1), n: +(p.pos[0] - this.n0).toFixed(1), e: +p.pos[1].toFixed(2), pitch: +p.out.pitch.toFixed(1), ground: p.out.onGround });
    if (p.crashed || p.status === 'destroyed') { this.log.crashed = true; (this.log as { wreck?: string | null }).wreck = p.wreck; return false; }
    return this.t < o.maxT && !(this.lifted && p.altitude > o.climbTo);
  }
  private climbPitch(r: { pitch: number; indicatedAirspeed: number }) { const want = r.indicatedAirspeed > 80 ? 12 : 10; return Math.max(-0.3, Math.min(0.35, 0.06 * (want - r.pitch))); }
  run(): TakeoffLog { while (this.step()); return this.log; }
}
