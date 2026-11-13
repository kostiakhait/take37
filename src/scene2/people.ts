// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
/**
 * The people of scene 2 (stage 4), about fifty, all on the engine's Walkers (ferret-physics-walkers): nobody is put at a height, nobody stands in the air or under a deck. The sand and the
 * mole's deck are one `FieldSupport`, the post's barrack, tower and fence are its walls, the decks of the craft are `GridSupport`s read off the models and carried with them (the sample's
 * `Decks`, borrowed from Ferret). Each man has a posture (engine posture AI) and a micro-motion person (@ferret/micromotion); the figures are drawn by the near and middle rings
 * (`near2.ts`, the library's own Tommies and sailors) and, far away, by the baked pictures of the perspective ladder (`FarCrowd`).
 *
 * Who is where (the owner's distribution): 30 henchmen in khaki (battledress): 13 on the decks of destroyers, yachts and boats, 14 at the post and on the road, 3 on the beach off the
 * runner's line; NOBODY on the mole. 20 sailors: 8 on the paddle steamer, 12 a distant assault group on the dunes' foot (never approached by the camera). Arnold and Emily are in
 * the cages (prisoners.ts).
 */
import { FieldSupport, Walkers, newWalker, type Walker } from '@ferret/physics';
import { newPosture, stepPosture } from '@ferret/ai';
import { newPerson, profile, stepPerson, type PersonState } from '@ferret/micromotion';
import { Decks } from '@dunkirk/decks';
import type { Soldier } from '@dunkirk/crowd-sim';
import { BASE, MOLE, bed, onMole, walkHeight } from './shore';
import { POST, roadAt } from './base';

export type Role = 'henchman' | 'sailor';
interface Brain {
  s: Soldier; w: Walker; role: Role; group: string;
  /** post: stands at his place; patrol: walks between points (ping-pong) and rests at each; swim: makes for the shore */
  kind: 'post' | 'patrol' | 'swim';
  pts: Array<[number, number]>; i: number; dir: 1 | -1; rest: number; speed: number; face?: number; stuck: number;
}
export interface PersonPlan { group: string; role: Role; kind: 'post' | 'patrol'; figure: string; x: number; z: number; face: number; pts?: Array<[number, number]>; speed?: number }

const TOMMIES = ['tommy-1', 'tommy-2', 'tommy-3'], SAILORS = ['sailor-1', 'sailor-4'];
const fig = (role: Role, n: number) => (role === 'henchman' ? TOMMIES : SAILORS)[n % (role === 'henchman' ? 3 : 2)]!;

/** a man at his post or on his round: stands, shifts his weight, looks about, a word with the next man; no sitting or lying */
const PROFILE = (() => { const p = profile('bystander'); p.name = 'scene2-guard'; p.role = 'guard'; p.anchors.radius = 0.2; delete (p.repertoire as Record<string, number>)['check-watch']; delete (p.repertoire as Record<string, number>).pace; return p; })();

/** the ashore people: at the post (gate 2, barrack door 1, tower 1, fence round 2), on the road (two pairs walking, two pairs standing) and off the runner's line on the beach (3) */
export function layoutAshore(): PersonPlan[] {
  const out: PersonPlan[] = [];
  const g = (group: string, kind: 'post' | 'patrol', n: number, x: number, z: number, face: number, pts?: Array<[number, number]>, speed = 1.15) => out.push({ group, role: 'henchman', kind, figure: fig('henchman', n), x, z, face, pts, speed });
  const cx = BASE.x, cz = BASE.z, hx = POST.halfX;
  // the post
  g('gate', 'post', 0, cx + hx - 2.5, cz + 3.2, Math.PI * 0.8); g('gate', 'post', 1, cx + hx - 2.6, cz - 3.2, -Math.PI * 0.8);
  g('barrack', 'post', 2, POST.barrack.x + 4, POST.barrack.z - POST.barrack.d / 2 - 2.2, 0.4);
  g('tower', 'post', 0, POST.tower.x, POST.tower.z - 4.2, Math.PI);
  g('fence', 'patrol', 1, cx - 18, cz - 13, 0, [[cx - 18, cz - 13], [cx + 14, cz - 13]], 1.1);
  g('fence', 'patrol', 2, cx - 17, cz + 12, 0, [[cx - 17, cz + 12], [cx - 17, cz - 2], [cx + 12, cz + 12]], 1.0);
  // the road: pairs walking back and forth (0.2-0.4 and 0.5-0.75 along it) and pairs standing at the roadside
  const road = roadAt({ x: cx + hx + 1.5, z: cz }), at = (t: number, off = 0): [number, number] => { const [x, z] = road(t), [x2, z2] = road(t + 0.01); const dx = x2 - x, dz = z2 - z, l = Math.hypot(dx, dz) || 1; return [x - dz / l * off, z + dx / l * off]; };
  for (const [name, a, b] of [['road1', 0.2, 0.38], ['road2', 0.52, 0.72]] as const) for (let k = 0; k < 2; k++) {
    const p0 = at(a, 0.9 - k * 1.8), p1 = at(b, 0.9 - k * 1.8); g(name, 'patrol', k + (name === 'road1' ? 0 : 2), p0[0], p0[1], Math.atan2(p1[0] - p0[0], p1[1] - p0[1]), [p0, p1], 1.15);
  }
  for (const [name, t] of [['road3', 0.12], ['road4', 0.43]] as const) for (let k = 0; k < 2; k++) {
    const p = at(t, 3.0 + k * 1.1), q = at(t, 3.0 + (1 - k) * 1.1); g(name, 'post', k + 1, p[0], p[1], Math.atan2(q[0] - p[0], q[1] - p[1]) + (k ? 0.3 : -0.3));
  }
  // the beach, off the runner's line (the mole's axis is x = 0): above the high-water line
  g('beach', 'post', 0, -46, -118, 0.8); g('beach', 'post', 1, 52, -125, -2.2); g('beach', 'post', 2, 55.5, -124, 1.0);
  return out;
}
/** the 12 sailors of the assault: a loose file that advances along the dunes' foot from the east, halts and falls back (waves), never nearer than about 250 m to the mole */
export function layoutAssault(seed = 5): PersonPlan[] {
  const out: PersonPlan[] = [], route: Array<[number, number]> = [[285, -128], [235, -140], [190, -152], [150, -150]];
  let a = seed | 0; const r = () => { a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  for (let i = 0; i < 12; i++) {
    const ox = (r() - 0.5) * 22, oz = (r() - 0.5) * 12, pts = route.map(([x, z], k) => [x + ox + k * (r() - 0.5) * 4, z + oz] as [number, number]);
    out.push({ group: 'assault', role: 'sailor', kind: 'patrol', figure: fig('sailor', i), x: pts[0][0], z: pts[0][1], face: Math.atan2(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]), pts, speed: 1.35 + r() * 0.35 });
  }
  return out;
}

/** how many men aboard each craft, and of which role (the keys are the fleet's plan ids): destroyers 3 each, yachts 1 each, the first three boats 1 each, the steamer's 8 sailors */
export function crewPlan(ids: string[]): Record<string, { n: number; role: Role }> {
  const out: Record<string, { n: number; role: Role }> = {};
  for (const id of ids) {
    if (id.startsWith('destroyer')) out[id] = { n: 3, role: 'henchman' };
    else if (id.startsWith('yacht')) out[id] = { n: 1, role: 'henchman' };
    else if (/^boat[123]$/.test(id)) out[id] = { n: 1, role: 'henchman' };
    else if (id === 'steamer') out[id] = { n: 8, role: 'sailor' };
  }
  return out;
}

let nextId = 1;
export class People {
  readonly walkers: Walkers;
  readonly decks: Decks;
  readonly brains: Brain[] = [];
  /** everybody this frame (ashore and aboard), world places: feed to the near, middle and far rings */
  readonly list: Soldier[] = [];
  level = 0;
  /** the deck people who have been dressed (their figure set) by deck key */
  private dressed = new Set<string>();
  private crew = new Map<string, { n: number; role: Role }>();
  /** men who went over the side and now swim for the shore */
  overboard = 0;
  /** the hulls afloat: each craft's footprint in its own frame (from its model's boxes), its node and the world-to-node matrix of this frame */
  private hulls: Array<{ node: BABYLON.TransformNode; lo: [number, number]; hi: [number, number]; inv: BABYLON.Matrix }> = [];
  private inHull(x: number, z: number): boolean {
    const v = new BABYLON.Vector3();
    for (const h of this.hulls) { v.set(x, h.node.getAbsolutePosition().y, z); const p = BABYLON.Vector3.TransformCoordinates(v, h.inv); if (p.x > h.lo[0] && p.x < h.hi[0] && p.z > h.lo[1] && p.z < h.hi[1]) return true; }
    return false;
  }
  /** how long reading each deck off its model took, ms (for the load time) */
  readonly readMs: Record<string, number> = {};

  constructor(scene: BABYLON.Scene, private water: () => number) {
    // the ground: the sand and sea bed with the mole's deck on it; the walls: the barrack, the tower and the fence of the post (the posts are solid, the gate is open)
    // the sea is level everywhere except inside a hull: a boat's cockpit floor may lie below the water outside (the model's lowest floor), but the water does not come in over the side
    this.walkers = new Walkers([new FieldSupport('ground', (x, z) => walkHeight(x, z), (x, z) => solidAt(x, z))], { water: (x: number, z: number) => (this.inHull(x, z) ? null : this.water()) });
    this.decks = new Decks(scene, this.walkers);
    this.decks.onOverboard = s => this.adopt(s);
  }

  private soldier(role: Role, figure: string, group: string): Soldier {
    const id = nextId++;
    const s: Soldier = { id, x: 0, y: 0, z: 0, heading: 0, state: 'wait', route: [], slot: -1, speed: 0, phase: (id * 0.37) % 6.28, variant: 0, hx: 0, hz: 0, idle: 0, ps: newPosture(id, 'stand'), figure };
    s.micro = newPerson(`${group}-${id}`, PROFILE, id * 7919, { external: true });
    return s;
  }
  /** a man from the ashore or assault plan: he is dropped a little above the ground and the physics lands him */
  add(p: PersonPlan) {
    const s = this.soldier(p.role, p.figure, p.group), w = newWalker();
    this.walkers.place(w, p.x, walkHeight(p.x, p.z) + 0.4, p.z);
    s.x = w.x; s.y = w.y; s.z = w.z; s.heading = p.face;
    this.brains.push({ s, w, role: p.role, group: p.group, kind: p.kind, pts: p.pts ?? [], i: 0, dir: 1, rest: 2 + (s.id * 3) % 7, speed: p.speed ?? 1.15, face: p.face, stuck: 0 });
  }
  /** a man who went over the side (the deck module hands him over with his body): he swims for the shore and stands up in the shallows */
  private adopt(s: Soldier) {
    if (!s.w) return;
    this.overboard++;
    this.brains.push({ s, w: s.w, role: 'henchman', group: 'overboard', kind: 'swim', pts: [[s.x * 0.5, -40]], i: 0, dir: 1, rest: 0, speed: 1.2, stuck: 0 });
  }
  /** the craft: read the deck off the model (called when the model is drawn) and put its crew on it */
  addCraft(key: string, node: BABYLON.TransformNode, meshes: BABYLON.AbstractMesh[], model: string, spacing = 0.72) {
    const c = this.crew.get(key); if (!c) return;
    const t0 = performance.now();
    this.decks.add(key, node, meshes, c.n, false, model, spacing);
    this.readMs[key] = Math.round(performance.now() - t0);
    node.computeWorldMatrix(true);
    const inv = node.getWorldMatrix().clone().invert(), lo: [number, number] = [Infinity, Infinity], hi: [number, number] = [-Infinity, -Infinity];
    for (const m of meshes) { if (!m.getTotalVertices()) continue; m.computeWorldMatrix(true); for (const c of m.getBoundingInfo().boundingBox.vectorsWorld) { const p = BABYLON.Vector3.TransformCoordinates(c, inv); lo[0] = Math.min(lo[0], p.x); lo[1] = Math.min(lo[1], p.z); hi[0] = Math.max(hi[0], p.x); hi[1] = Math.max(hi[1], p.z); } }
    // the hull proper: the middle of the footprint (the bow and stern rise and narrow; rigging and rails do not count)
    const cx = (lo[0] + hi[0]) / 2, cz = (lo[1] + hi[1]) / 2, sx = (hi[0] - lo[0]) * 0.36, sz = (hi[1] - lo[1]) * 0.36;
    this.hulls.push({ node, lo: [cx - sx, cz - sz], hi: [cx + sx, cz + sz], inv });
  }
  setCrew(plan: Record<string, { n: number; role: Role }>) { this.crew = new Map(Object.entries(plan)); }

  /** dress the deck people of a craft as its role says (henchmen in khaki battledress, the steamer's sailors in their caps), once */
  private dress() {
    const decks = (this.decks as unknown as { decks: Map<string, { crew: Array<{ s: Soldier }> }> }).decks;
    for (const [key, d] of decks) {
      if (this.dressed.has(key)) continue;
      const c = this.crew.get(key); if (!c) continue;
      d.crew.forEach((b, i) => { b.s.figure = fig(c.role, b.s.id + i); b.s.variant = 0; });
      this.dressed.add(key);
    }
  }

  update(dt: number, aboard: (key: string) => number = () => 0) {
    if (dt <= 0) return;
    this.dress();
    for (const h of this.hulls) h.node.getWorldMatrix().invertToRef(h.inv);
    this.decks.update(dt, aboard);
    for (const b of this.brains) this.stepBrain(b, dt);
    this.list.length = 0;
    for (const b of this.brains) this.list.push(b.s);
    for (const s of this.decks.people) this.list.push(s);
  }

  private stepBrain(b: Brain, dt: number) {
    const s = b.s, w = b.w;
    const r0 = stepPosture(s.ps, dt, 'walk');
    void r0;
    const upright = (s.ps.posture === 'stand' || s.ps.posture === 'talk') && !s.ps.to;
    let mx = 0, mz = 0, moving = 0;
    if (b.kind === 'swim') {
      // afloat: strokes toward the shallows; once he stands on the sand he is a man on the beach and stands
      const t = b.pts[0]!, dx = t[0] - w.x, dz = t[1] - w.z, d = Math.hypot(dx, dz);
      if (!w.swim && w.depth < 0.5 && !w.air && d < 40) { b.kind = 'post'; b.pts = []; }
      else if (d > 0.1) { const st = Math.min(d, b.speed * dt); mx = dx / d * st; mz = dz / d * st; moving = b.speed * 0.6; s.heading = Math.atan2(dx, dz); }
    } else if (b.kind === 'patrol' && b.pts.length > 1 && upright) {
      if (b.rest > 0) b.rest -= dt;
      else {
        const t = b.pts[b.i]!, dx = t[0] - w.x, dz = t[1] - w.z, d = Math.hypot(dx, dz);
        if (d < 0.35) {
          const n = b.i + b.dir; if (n < 0 || n >= b.pts.length) b.dir = (b.dir === 1 ? -1 : 1); b.i = Math.min(b.pts.length - 1, Math.max(0, b.i + b.dir)); b.rest = 3 + (s.id * 5) % 9;
        } else { const st = Math.min(d, b.speed * dt); mx = dx / d * st; mz = dz / d * st; moving = b.speed; const want = Math.atan2(dx, dz); let da = want - s.heading; da = Math.atan2(Math.sin(da), Math.cos(da)); s.heading += da * Math.min(1, dt * 5); }
      }
    } else if (b.face !== undefined && !moving) {
      let da = b.face - s.heading; da = Math.atan2(Math.sin(da), Math.cos(da)); s.heading += da * Math.min(1, dt * 2);
    }
    const r = this.walkers.step(w, dt, mx, mz, b.kind !== 'swim');
    if (r.blocked && moving) { b.stuck += dt; if (b.stuck > 1.5) { b.stuck = 0; b.rest = 2; if (b.kind === 'patrol') b.i = (b.i + b.dir + b.pts.length) % b.pts.length; } } else b.stuck = 0;
    s.x = w.x; s.y = w.y; s.z = w.z; s.speed = moving; s.phase += moving * dt * 4.2;
    const P: PersonState | undefined = s.micro;
    if (P) { P.pos = [s.x, s.y, s.z]; P.facing = s.heading; stepPerson(P, dt, { targets: [], take: 'idle' }); }
  }

  /** a check over the whole crowd: nobody in the air, nobody on the mole, nobody below the surface under his feet; returns the faults found */
  probe(): string[] {
    const bad: string[] = [];
    for (const s of this.list) {
      const ground = Math.max(walkHeight(s.x, s.z), -1e9);
      if (onMole(s.x, s.z) && s.y > -50 && !this.onDeck(s)) bad.push(`man ${s.id} on the mole (${s.x.toFixed(1)}, ${s.z.toFixed(1)})`);
      if (Number.isNaN(s.y) || s.y < ground - 6 && !this.onDeck(s)) bad.push(`man ${s.id} far below the ground (${s.y.toFixed(2)})`);
    }
    for (const b of this.brains) if (b.w.air && b.kind !== 'swim') bad.push(`man ${b.s.id} (${b.group}) in the air at ${b.s.y.toFixed(2)}`);
    return bad;
  }
  private onDeck(s: Soldier) { return s.id >= 1_000_000; }
}

/** the post's solid things for the walkers: the barrack, the tower's legs and the fence (the gate is open): a top 1.6 m above the pad (a wall: above a step, within a man's reach), or null where there is nothing */
function solidAt(x: number, z: number): number | null {
  const g = BASE.h, B = POST.barrack, T = POST.tower, cx = BASE.x, cz = BASE.z, hx = POST.halfX, hz = POST.halfZ, gw = POST.gate / 2;
  if (Math.abs(x - B.x) < B.w / 2 + 0.25 && Math.abs(z - B.z) < B.d / 2 + 0.25) return g + 1.6;
  if (Math.abs(x - T.x) < 1.1 && Math.abs(z - T.z) < 1.1) return g + 1.6;
  const t = 0.3;
  const onX = Math.abs(x - cx) <= hx + t, onZ = Math.abs(z - cz) <= hz + t;
  if (onX && (Math.abs(z - (cz - hz)) < t || Math.abs(z - (cz + hz)) < t)) return g + 1.6;
  if (onZ && Math.abs(x - (cx - hx)) < t) return g + 1.6;
  if (onZ && Math.abs(x - (cx + hx)) < t && Math.abs(z - cz) > gw) return g + 1.6;
  return null;
}
void bed; void MOLE;
