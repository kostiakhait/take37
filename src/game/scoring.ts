// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// The hidden score: what the sim reports, valued by physics (blast size, fire power, chain depth) and multiplied by being in frame of the set cameras. Stunts in frame are kept as clips (data for the trailer).
import { SCORE, SET_CAMERAS, FRAME, type SetCamera } from './config';
import type { SimEvent, Sim } from './sim';
import type { Box } from './layout';

type V3 = [number, number, number];
export interface ScoreItem { t: number; kind: string; base: number; chain: number; frame: number; camera: string | null; points: number; at: V3 }
export interface Clip { start: number; end: number; camera: string; points: number; kinds: string[]; at: V3 }
export interface FrameShot { t: number; camera: string; at: V3; kind: string; factor: number }

const sub = (a: V3, b: V3): V3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const dot = (a: V3, b: V3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a: V3, b: V3): V3 => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const norm = (a: V3): V3 => { const l = Math.hypot(...a) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };

/** is the segment from a to b blocked by a solid box (a building between the lens and the thing)? */
function blocked(a: V3, b: V3, boxes: Box[]): boolean {
  for (const bx of boxes) {
    let t0 = 0, t1 = 1, ok = true;
    for (let d = 0; d < 3 && ok; d++) {
      const dd = b[d]! - a[d]!;
      if (Math.abs(dd) < 1e-9) { if (a[d]! < bx.min[d]! || a[d]! > bx.max[d]!) ok = false; continue; }
      let u0 = (bx.min[d]! - a[d]!) / dd, u1 = (bx.max[d]! - a[d]!) / dd; if (u0 > u1) [u0, u1] = [u1, u0];
      t0 = Math.max(t0, u0); t1 = Math.min(t1, u1); if (t0 > t1) ok = false;
    }
    if (ok) return true;
  }
  return false;
}

/** how well a camera sees a point: 0 not at all, up to 1 at the centre of the picture (distance, frustum, buildings in between) */
export function seen(cam: SetCamera, p: V3, buildings: Box[]): number {
  const f = norm(sub(cam.target, cam.pos)), r = norm(cross(f, [0, 1, 0])), u = cross(r, f), d = sub(p, cam.pos), z = dot(d, f);
  if (z < FRAME.minDist || z > FRAME.maxDist) return 0;
  const th = Math.tan(cam.fov / 2), x = dot(d, r) / (z * th * FRAME.aspect), y = dot(d, u) / (z * th);
  const m = Math.max(Math.abs(x), Math.abs(y));
  if (m > FRAME.margin) return 0;
  if (blocked([cam.pos[0], cam.pos[1], cam.pos[2]], [p[0], Math.max(p[1], 0.8), p[2]], buildings)) return 0;
  return 1 - 0.4 * m;
}

export class Spectacle {
  items: ScoreItem[] = [];
  clips: Clip[] = [];
  shots: FrameShot[] = [];
  total = 0;
  private seenTanker = false; private pumpsBurnt = new Set<string>(); private stationDone = false; private canopyDown = false; private fireAcc = new Map<string, number>(); private fireGot = new Map<string, number>();
  /** the time of the last scored thing, s */ lastAt = -99;

  constructor(private sim: Sim, readonly cameras: SetCamera[] = SET_CAMERAS) {}

  /** the frame factor of a point: the best camera's weight and centring, a little more for every further camera that sees it; 0 when no camera does */
  frame(p: V3): { factor: number; camera: string | null } {
    let best = 0, bestCam: string | null = null, n = 0;
    for (const c of this.cameras) { const s = seen(c, p, this.sim.statics); if (s <= 0) continue; n++; const v = s * c.weight; if (v > best) { best = v; bestCam = c.id; } }
    return { factor: best > 0 ? best + 0.25 * (n - 1) : 0, camera: bestCam };
  }

  private add(t: number, kind: string, base: number, depth: number, at: V3) {
    if (base <= 0) return;
    const chain = 1 + SCORE.chain * depth, f = this.frame(at), points = base * chain * f.factor;
    this.items.push({ t, kind, base, chain, frame: f.factor, camera: f.camera, points, at });
    this.shots.push({ t, camera: f.camera ?? '-', at, kind, factor: f.factor });
    this.total += points;
    if (points > 0) { this.lastAt = t; this.clip(t, f.camera!, points, kind, at); }
  }
  private clip(t: number, camera: string, points: number, kind: string, at: V3) {
    const last = this.clips[this.clips.length - 1];
    if (last && t - last.end < 3.5 + 2) { last.end = t + 3; last.points += points; if (!last.kinds.includes(kind)) last.kinds.push(kind); if (last.camera !== camera && points > last.points * 0.5) last.camera = camera; return; }
    this.clips.push({ start: Math.max(0, t - 2), end: t + 3, camera, points, kinds: [kind], at });
  }

  /** feed the events of a step */
  consume(events: SimEvent[]) {
    for (const e of events) {
      switch (e.type) {
        case 'wreck': {
          const base = e.role === 'parked' ? SCORE.wreckParked : e.role === 'player' ? SCORE.wreckPolice : e.role === 'vincent' ? SCORE.wreckVincent : SCORE.wreckMoving;
          this.add(e.t, `wreck:${e.role}:${e.kind}`, base, e.depth, e.at); break;
        }
        case 'prop': this.add(e.t, `prop:${e.kind}`, e.kind === 'Hydrant' ? SCORE.hydrant : e.how === 'knocked' ? SCORE.prop : SCORE.prop * 3, e.depth, e.at);
          if (e.id === 'Canopy' && !this.canopyDown) { this.canopyDown = true; this.add(e.t, 'canopy-down', SCORE.canopyDown, e.depth, e.at); this.stationCheck(e.t, e.at); } break;
        case 'blast': this.add(e.t, `blast:${e.what}`, SCORE.blastPerLn * Math.log(1 + e.tnt) + (e.what === 'tanker' ? SCORE.tankerBlast : e.what === 'propane' ? SCORE.propane : 0), e.depth, e.at); break;
        case 'ignite':
          if (e.what === 'tanker' && !this.seenTanker) { this.seenTanker = true; this.add(e.t, 'tanker-burning', SCORE.tankerBurnt, e.depth, e.at); }
          if (e.what === 'pump' && !this.pumpsBurnt.has(e.id)) { this.pumpsBurnt.add(e.id); this.add(e.t, 'pump-burning', SCORE.pumpBurnt, e.depth, e.at); this.stationCheck(e.t, e.at); }
          if (e.what === 'canopy') this.stationCheck(e.t, e.at);
          break;
        case 'burning': {
          const mw = e.power / 1e6, cap = e.what === 'tanker' ? 1200 : e.what === 'car' ? 90 : 250, got = this.fireGot.get(e.id) ?? 0;
          if (mw > 1 && got < cap) { const a = (this.fireAcc.get(e.id) ?? 0) + SCORE.firePerMWs * (mw - 1) * e.dt; if (a >= 4) { this.add(e.t, 'fire', a, 0, e.at); this.fireGot.set(e.id, got + a); this.fireAcc.set(e.id, 0); } else this.fireAcc.set(e.id, a); }
          break;
        }
        default: break;
      }
    }
  }
  private stationCheck(t: number, at: V3) {
    if (this.stationDone) return;
    if (this.pumpsBurnt.size >= 4 && (this.canopyDown || this.pumpsBurnt.size >= 6)) { this.stationDone = true; this.add(t, 'station-burnt', SCORE.stationBurnt, 0, at); }
  }
  /** the points that came from the take's wrecks and fires by kind, for the director's reaction */
  has(kind: string): boolean { return this.items.some((i) => i.kind.startsWith(kind) && i.points > 0); }
  get tankerBurnt() { return this.has('tanker-burning') || this.has('blast:tanker'); }
  get stationBurnt() { return this.stationDone; }
  get wrecks() { return this.items.filter((i) => i.kind.startsWith('wreck') && i.points > 0).length; }
}
