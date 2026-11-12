// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// The breakable shop fronts of the street (plans/BUILDINGS-DESTRUCTION.md). A converted building keeps its shell as one mesh (art/street/shopfront_parts.py) and its shop windows, door, transom, sign board and
// awning are parts of their own; here each part is a thing of the engine's destruction module with the material it is made of, and the module decides what a car or a blast does to it:
//   window pane, transom   glass (annealed 6 mm / 4 mm): Roark plate stress against the modulus of rupture, a crack star, then shards;
//   door glass             tempered glass: all or nothing, small blunt cells;     door leaf  oak bar: bending between hinge and latch, splinters;
//   sign board             plywood board on its backing: bending over the span between the fixings, splinters;
//   awning                 sheet aluminium and canvas: crush zone and dent lattice, bolted to the wall by links that snap at the force the bolts hold; the section that comes off falls as a body.
// No walls here: the house walls stay whole (owner's order). Pure data and the module, no Babylon (the picture is shopfronts-view.ts).
import { blastAt } from '@ferret/physics-explosions';
import type { Quat, Vec3 } from '@ferret/destruction/types';
import type { Vehicle } from '@ferret/destruction/vehicle';
import { linkHolds } from '@ferret/destruction/assembly';
import { toGame, type Box, type V3 } from './layout';
import { nodeBounds, type GLtf } from './glbinfo';
import type { Car, Sim } from './sim';

export type ShopKind = 'ShopWindow' | 'ShopTransom' | 'ShopDoorLeaf' | 'ShopDoorGlass' | 'ShopSign' | 'ShopAwning';
export interface ShopPartDef {
  /** `<kind>_<building>_<index>`, also the name of the node in the scene */ id: string; kind: ShopKind; building: string;
  /** bounds of the part's mesh, game frame */ box: Box;
}
export interface ShopBuildingDef {
  id: string;
  /** bounds of the shell, game frame */ box: Box;
  /** the unit vector out of the front, horizontal (x or z) */ out: V3;
}
export interface ShopDefs { buildings: ShopBuildingDef[]; parts: ShopPartDef[] }

/** where a part is: centre, the axes along the front, up and out of the front, and the full size along them (m) */
export interface ShopFrame { at: Vec3; u: Vec3; up: Vec3; out: Vec3; size: Vec3 }
export interface ShopState { def: ShopPartDef; thing: string; part: string; frame: ShopFrame; state: 'whole' | 'gone' | 'fell'; hits: number }

type HullFn = (v: Vehicle, b: Box) => { normal: Vec3; depth: number; point: Vec3 } | null;
const dot = (a: Vec3, b: Vec3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const mul = (a: Vec3, k: number): Vec3 => [a[0] * k, a[1] * k, a[2] * k];
const add = (a: Vec3, b: Vec3): Vec3 => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const mid = (b: Box): Vec3 => [(b.min[0] + b.max[0]) / 2, (b.min[1] + b.max[1]) / 2, (b.min[2] + b.max[2]) / 2];

/** the rotation of the part frame (x = u, y = up, z = out) as a quaternion */
export function frameQuat(u: Vec3, up: Vec3, out: Vec3): Quat {
  const m00 = u[0], m10 = u[1], m20 = u[2], m01 = up[0], m11 = up[1], m21 = up[2], m02 = out[0], m12 = out[1], m22 = out[2];
  const tr = m00 + m11 + m22;
  if (tr > 0) { const s = Math.sqrt(tr + 1) * 2; return [(m21 - m12) / s, (m02 - m20) / s, (m10 - m01) / s, s / 4]; }
  if (m00 > m11 && m00 > m22) { const s = Math.sqrt(1 + m00 - m11 - m22) * 2; return [s / 4, (m01 + m10) / s, (m02 + m20) / s, (m21 - m12) / s]; }
  if (m11 > m22) { const s = Math.sqrt(1 + m11 - m00 - m22) * 2; return [(m01 + m10) / s, s / 4, (m12 + m21) / s, (m02 - m20) / s]; }
  const s = Math.sqrt(1 + m22 - m00 - m11) * 2; return [(m02 + m20) / s, (m12 + m21) / s, s / 4, (m10 - m01) / s];
}

/** a cars's closing speed with the facade must be over this for a pane to feel it (m/s) */
const MIN_SPEED = 1.2;
/** half the width of a car's front, m */
const CAR_HALF_WIDTH = 0.95;
/** a blast below this overpressure does nothing to a part (Pa) */
const MIN_OVERPRESSURE = 600;

export class ShopSim {
  readonly parts = new Map<string, ShopState>();
  /** the unit vector out of the front of the building a part belongs to */
  private readonly outOf = new Map<string, V3>();
  private fallId = 300000;
  /** `false`: the sim ignores the shop fronts (A/B runs): nothing is hit */
  enabled = true;
  readonly counts = { glassBroken: 0, doorsBroken: 0, signsBroken: 0, awningsHit: 0, awningsFell: 0 };

  constructor(private readonly sim: Sim, readonly defs: ShopDefs, private readonly hull: HullFn) {
    for (const b of defs.buildings) this.outOf.set(b.id, b.out);
    for (const d of defs.parts) this.define(d);
  }

  /** the unit vectors of a part's frame from the front it faces */
  private frameOf(d: ShopPartDef): ShopFrame {
    const out = this.outOf.get(d.building)!, up: Vec3 = [0, 1, 0];
    // u x up = out: for out = +z u = +x; -z: -x; +x: -z; -x: +z
    const u: Vec3 = out[2] > 0.5 ? [1, 0, 0] : out[2] < -0.5 ? [-1, 0, 0] : out[0] > 0.5 ? [0, 0, -1] : [0, 0, 1];
    const ext: Vec3 = [d.box.max[0] - d.box.min[0], d.box.max[1] - d.box.min[1], d.box.max[2] - d.box.min[2]];
    const along = Math.abs(u[0]) > 0.5 ? ext[0] : ext[2], thick = Math.abs(out[0]) > 0.5 ? ext[0] : ext[2];
    return { at: mid(d.box), u, up, out: [out[0], 0, out[2]], size: [Math.max(0.05, along), Math.max(0.05, ext[1]), Math.max(0.004, thick)] };
  }

  private define(d: ShopPartDef) {
    const ds = this.sim.ds, f = this.frameOf(d), q = frameQuat(f.u, f.up, f.out);
    let thing = d.id, part = 'glass';
    const frame = (id: string) => { ds.thing(id).frame = { position: [...f.at] as Vec3, rotation: q }; };
    switch (d.kind) {
      case 'ShopWindow':        // plate glass 6 mm in a frame, one pane between two mullions
        ds.defineThing({ id: thing, root: 'glass', parts: [{ id: 'glass', substance: 'glass-annealed', size: [f.size[0], f.size[1], 0.006], thickness: 0.006 }] });
        frame(thing); break;
      case 'ShopTransom':       // 4 mm over the door
        ds.defineThing({ id: thing, root: 'glass', parts: [{ id: 'glass', substance: 'glass-annealed', size: [f.size[0], f.size[1], 0.004], thickness: 0.004 }] });
        frame(thing); break;
      case 'ShopDoorLeaf': case 'ShopDoorGlass': {
        thing = `${d.building}:ShopDoor`; part = d.kind === 'ShopDoorLeaf' ? 'leaf' : 'glass';
        const mate = [...this.parts.values()].find((p) => p.thing === thing);
        if (!mate) { this.registerPart(d, thing, part, f); return; }          // the other half of the door comes next
        // both halves known: the leaf (oak; stiles, rails and a panel make about half of its bounds) is the root, the glass a pane in it held by its putty
        const lf = mate.part === 'leaf' ? mate.frame : f, gf = mate.part === 'leaf' ? f : mate.frame, rel = sub3(gf.at, lf.at);
        ds.defineThing({
          id: thing, root: 'leaf',
          parts: [
            { id: 'leaf', substance: 'wood-oak', size: [lf.size[0], lf.size[1], Math.max(0.045, lf.size[2])], fill: 0.45, grain: [0, 1, 0], at: [0, 0, 0] },
            { id: 'glass', substance: 'glass-tempered', glass: 'tempered', size: [gf.size[0], gf.size[1], 0.006], thickness: 0.006, at: [dot(rel, lf.u), dot(rel, lf.up), dot(rel, lf.out)] },
          ],
          links: [{ part: 'glass', to: 'leaf', kind: 'glue', tensile: 4e6, area: 0.004, count: 1 }],
        });
        ds.thing(thing).frame = { position: [...lf.at] as Vec3, rotation: frameQuat(lf.u, lf.up, lf.out) };
        this.registerPart(d, thing, part, f); return;
      }
      case 'ShopSign': {        // a 20 mm plywood board on its backing: nailed along its length, so it spans only the gap between fixings
        ds.defineThing({ id: thing, root: 'board', parts: [{ id: 'board', substance: 'plywood', size: [f.size[0], f.size[1], 0.02], grain: [1, 0, 0] }] });
        const p = ds.thing(thing).assembly.get('board').part; p.damage['wood.support0'] = Math.max(0, f.size[0] / 2 - 0.3); p.damage['wood.support1'] = Math.min(f.size[0], f.size[0] / 2 + 0.3);
        frame(thing); part = 'board'; break;
      }
      case 'ShopAwning': {      // canvas on a steel frame: a crush zone and dents; four M10 bolts hold a section to the wall
        const m = Math.max(4, f.size[0] * f.size[2] * 4.5);   // about 4.5 kg per m^2 of plan: canvas, valance, arms
        ds.defineThing({
          id: thing, root: 'wall',
          parts: [
            { id: 'wall', kind: 'rigid', size: [0.2, 0.2, 0.2], mass: 5000, at: [0, f.size[1] / 2, -f.size[2] / 2] },
            { id: 'awning', substance: 'aluminium-sheet', thickness: 0.002, size: f.size, mass: m, at: [0, 0, 0] },
          ],
          links: [{ part: 'awning', to: 'wall', kind: 'bolt', holds: linkHolds(400e6, 58e-6, 4) }],
        });
        frame(thing); part = 'awning'; break;
      }
    }
    this.registerPart(d, thing, part, f);
  }
  private registerPart(d: ShopPartDef, thing: string, part: string, frame: ShopFrame) { this.parts.set(d.id, { def: d, thing, part, frame, state: 'whole', hits: 0 }); }

  /** the building box of the sim's statics that a shop front belongs to (the wall a car hits) */
  owns(b: Box): boolean {
    for (const d of this.defs.buildings) { const c = mid(d.box); if (c[0] > b.min[0] - 0.6 && c[0] < b.max[0] + 0.6 && c[2] > b.min[2] - 0.6 && c[2] < b.max[2] + 0.6) return true; }
    return false;
  }
  buildingOf(b: Box): string | null {
    for (const d of this.defs.buildings) { const c = mid(d.box); if (c[0] > b.min[0] - 0.6 && c[0] < b.max[0] + 0.6 && c[2] > b.min[2] - 0.6 && c[2] < b.max[2] + 0.6) return d.id; }
    return null;
  }

  /** the region in which a car touches a part: the part's bounds, and for what sits behind the face of the building (glass, door, sign) the 0.45 m in front of it, where the car's hood is when it stands at the wall */
  private slab(s: ShopState): Box {
    const b = s.def.box, o = s.frame.out, k = s.def.kind === 'ShopAwning' ? 0.05 : 0.45;
    const lo: V3 = [...b.min] as V3, hi: V3 = [...b.max] as V3;
    for (const a of [0, 2] as const) { if (o[a] > 0.5) hi[a] += k; else if (o[a] < -0.5) lo[a] -= k; }
    return { min: lo, max: hi };
  }

  private gone(s: ShopState, how: 'broken' | 'fell', at: Vec3, depth: number) {
    s.state = how === 'fell' ? 'fell' : 'gone';
    const k = s.def.kind;
    if (k === 'ShopWindow' || k === 'ShopTransom' || k === 'ShopDoorGlass') this.counts.glassBroken++; else if (k === 'ShopDoorLeaf') this.counts.doorsBroken++; else if (k === 'ShopSign') this.counts.signsBroken++;
    this.sim.emit({ t: this.sim.t, type: 'prop', id: s.thing + ':' + s.part, kind: k, at, how: 'broken', depth });
  }

  /** one hit on a part through the module; what broke is marked and announced. Returns the module's result (or null when the part was already off). */
  private strike(s: ShopState, pt: Vec3, dir: Vec3, speed: number, otherMass: number, area: number, cause: string | null, depth: number) {
    if (s.state !== 'whole') return null;
    const ds = this.sim.ds, d = ds.thing(s.thing);
    s.hits++;
    const r = ds.contact(s.thing, { point: pt, normal: dir, speed, otherMass, restitution: 0.2, area, step: this.sim.tick });
    if (!r) return null;
    // the module picks the part under the point (a door is a leaf with a pane in it): every part of the thing that is off now is marked
    for (const o of this.parts.values()) {
      if (o.thing !== s.thing || o.state !== 'whole') continue;
      const ap = d.assembly.get(o.part);
      if (!(ap.part.broken || !ap.attached)) continue;
      if (o.def.kind === 'ShopAwning') { this.fall(o, dir, speed); this.gone(o, 'fell', o.frame.at, depth); } else this.gone(o, 'broken', pt, depth);
      if (cause) this.sim.markActive(s.thing, depth);
    }
    if (s.state === 'whole' && s.def.kind === 'ShopAwning') this.counts.awningsHit++;
    return r;
  }

  /** the section of awning that came off its bolts falls as a body (the sim's debris; the view carries the mesh) */
  private fall(s: ShopState, dir: Vec3, speed: number) {
    const f = s.frame, sz = f.size, half: Vec3 = [Math.abs(f.u[0]) * sz[0] / 2 + Math.abs(f.out[0]) * sz[2] / 2, sz[1] / 2, Math.abs(f.u[2]) * sz[0] / 2 + Math.abs(f.out[2]) * sz[2] / 2];
    const m = this.sim.ds.thing(s.thing).assembly.get('awning').part.mass, v = Math.min(8, speed * 0.4);
    const vel = add(mul(f.out, Math.min(3, v * 0.3) + 0.4), [dir[0] * 0.2 * v, 0.3, dir[2] * 0.2 * v]);   // the free edge drops outward, the blow adds a little along its direction
    this.sim.debris.push({ id: this.fallId++, ref: s.def.id, pos: [...f.at] as Vec3, vel, rot: [0, 0, 0, 1], ang: [dir[2] * 0.8, 0, -dir[0] * 0.8], half, mass: m, resting: false, age: 0, kind: 'awning' });
    this.counts.awningsFell++;
  }

  /** a car presses on the face of a converted building (the sim's wall contact): the panes, the door glass and the transom in front of the car feel its closing speed `sp` */
  wallHit(c: Car, b: Box, pt: Vec3, sp: number): boolean {
    if (!this.enabled) return false;
    const bid = this.buildingOf(b); if (!bid) return false;
    if (!(sp > MIN_SPEED)) return true;
    const depth = this.sim.depthOf(c.id);
    for (const s of this.parts.values()) {
      if (s.def.building !== bid || s.state !== 'whole') continue;
      if (s.def.kind === 'ShopSign' || s.def.kind === 'ShopAwning') continue;   // above the car or in the recess; they are met by `collideCar` and blasts
      // the car's front is about 1.9 m wide: every pane whose span along the front is within its half width of the contact point takes the blow (the wall stops the car in one step, so the hull test alone would give the pane under the very corner)
      const lo = Math.min(dot(s.def.box.min, s.frame.u), dot(s.def.box.max, s.frame.u)), hi = Math.max(dot(s.def.box.min, s.frame.u), dot(s.def.box.max, s.frame.u)), at = dot(pt, s.frame.u);
      if (at < lo - CAR_HALF_WIDTH || at > hi + CAR_HALF_WIDTH) continue;
      const o = s.frame.out, p: Vec3 = [Math.max(s.def.box.min[0], Math.min(s.def.box.max[0], pt[0])), Math.max(s.def.box.min[1] + 0.05, Math.min(s.def.box.max[1] - 0.05, Math.max(pt[1], 0.6))), Math.max(s.def.box.min[2], Math.min(s.def.box.max[2], pt[2]))];
      this.strike(s, p, mul(o, -1), sp, c.veh.mass, 0.5, c.id, depth);
    }
    return true;
  }

  /** every step, for each car: a tall vehicle meets the awning and the sign in front of the wall (a tanker's cab, a car thrown up on the walk); the car loses what the part takes */
  collideCar(c: Car) {
    if (!this.enabled) return;
    const v = c.veh, p = v.pos;
    for (const s of this.parts.values()) {
      if (s.state !== 'whole' || (s.def.kind !== 'ShopAwning' && s.def.kind !== 'ShopSign')) continue;
      const b = s.def.box;
      if (p[0] < b.min[0] - 8 || p[0] > b.max[0] + 8 || p[2] < b.min[2] - 8 || p[2] > b.max[2] + 8) continue;
      const k = this.hull(v, this.slab(s)); if (!k) continue;
      const o = s.frame.out, vn = -dot(v.velocityAt(k.point), o);
      if (!(vn > MIN_SPEED)) continue;
      const kp: Vec3 = [Math.max(b.min[0], Math.min(b.max[0], k.point[0])), Math.max(b.min[1], Math.min(b.max[1], k.point[1])), Math.max(b.min[2], Math.min(b.max[2], k.point[2]))];
      const r = this.strike(s, kp, mul(o, -1), vn, v.mass, 0.6, c.id, this.sim.depthOf(c.id));
      if (r && s.state !== 'whole') {
        const L = r.outcome.ledger, absorbed = L.crush + L.fracture + L.heat + L.sound, vAfter = Math.sqrt(Math.max(0, vn * vn - (2 * absorbed) / v.mass));
        v.applyImpulse(mul(o, -v.mass * Math.max(0, vn - vAfter) * 0.98), k.point);
      }
    }
  }

  /** the blast wave of `tnt` kg at `at`: each part gets the impulse of the wave over its area as the speed it is pushed to, and the module turns that into damage by the part's material */
  blast(at: Vec3, tnt: number, depth: number) {
    if (!this.enabled) return;
    for (const s of this.parts.values()) {
      if (s.state !== 'whole') continue;
      const c = s.frame.at, r = Math.hypot(c[0] - at[0], c[1] - at[1], c[2] - at[2]);
      if (r < 1.5 || r > 160) continue;
      const bl = blastAt(r, tnt); if (bl.overpressure < MIN_OVERPRESSURE) continue;
      const thing = this.sim.ds.thing(s.thing), mass = thing.assembly.get(s.part).part.mass, A = s.frame.size[0] * s.frame.size[s.def.kind === 'ShopAwning' ? 2 : 1];
      const v = (bl.impulse * A) / mass, dir: Vec3 = [(c[0] - at[0]) / r, (c[1] - at[1]) / r, (c[2] - at[2]) / r];
      const n = Math.hypot(...dir) || 1;
      const b = s.def.box, cp: Vec3 = [Math.max(b.min[0], Math.min(b.max[0], c[0])), Math.max(b.min[1], Math.min(b.max[1], c[1])), Math.max(b.min[2], Math.min(b.max[2], c[2]))];
      this.strike(s, cp, [dir[0] / n, dir[1] / n, dir[2] / n], Math.min(60, v), mass * 40, Math.min(1.5, A), 'blast', depth);
    }
  }
}
const sub3 = (a: Vec3, b: Vec3): Vec3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];

/** the buildings of the street that have their shop front converted: the node of the street glb, and the file with the shell and the parts */
export const SHOP_BUILDINGS: { bld: string; url: string }[] = [{ bld: 'Bld_R_107_18', url: '/art/street/shops/shop_18.glb' }];

/** the bounds of the shell and of every part of the converted buildings in the game's frame, read off the JSON of the street and of the shop files (no mesh is loaded) */
export function parseShops(street: GLtf, files: { bld: string; json: GLtf }[]): ShopDefs {
  const sb = nodeBounds(street), out: ShopDefs = { buildings: [], parts: [] };
  for (const f of files) {
    const bi = street.nodes.findIndex((n) => n.name === f.bld); if (bi < 0) continue;
    const m = sb[bi]!.world, fb = nodeBounds(f.json);
    // the front of the building: its local +X through the node's matrix, into the game frame (z mirrored)
    const ox = m[0]!, oz = -m[2]!, ol = Math.hypot(ox, oz) || 1;
    const out3: V3 = Math.abs(ox) > Math.abs(oz) ? [Math.sign(ox), 0, 0] : [0, 0, Math.sign(oz)]; void ol;
    f.json.nodes.forEach((n, i) => {
      const nm = n.name ?? '';
      const b = fb[i]!; if (!(b.max[0] > b.min[0] || b.max[1] > b.min[1] || b.max[2] > b.min[2])) return;
      if (nm === 'Shell_LOD0') out.buildings.push({ id: f.bld, box: toGame(b.min, b.max, m), out: out3 });
      const mm = nm.match(/^Part_(Shop[A-Za-z]+)_(.+)$/);
      if (mm) out.parts.push({ id: `${f.bld}:${mm[1]}_${mm[2]}`, kind: mm[1] as ShopKind, building: f.bld, box: toGame(b.min, b.max, m) });
    });
  }
  return out;
}
