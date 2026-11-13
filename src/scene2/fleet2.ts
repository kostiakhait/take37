// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
/**
 * The roadstead fleet of scene 2 (stage 2): library vessels (borrowed from Ferret: fletcher, sundowner, lucy-lavers, princess-elizabeth), each an instance with its own livery,
 * scale and trim, lying at anchor on the sea of the field (the Dunkirk sample's `SeaModel`, the same sums the water shader draws), and the paddle steamer as a separate
 * object at her place at the mole's east face. Placement is a pure function of the seed (`layoutFleet`), no Babylon. No mechanics: no firing, sinking, steering.
 */
import type { AssetLibrary, LibraryModel } from '@ferret/levels';
import type { World } from '@ferret/core';
import { Perspective, type PerspectiveLevel } from '@ferret/perspective';
import { perspectiveOf } from '@dunkirk/wrecks-view';
import type { SeaModel } from '@dunkirk/sea-model';
import { CAGE_Z, FACE_E, MOLE, bed, TIDE } from './shore';

export type VesselKind = 'destroyer' | 'yacht' | 'boat' | 'steamer';
export interface Livery { name: string; hull: [number, number, number]; upper: [number, number, number] }
export interface VesselPlan { id: string; kind: VesselKind; model: string; x: number; z: number; heading: number; scale: number; trim: number; swing: number; livery: Livery }

const rgb = (r: number, g: number, b: number): [number, number, number] => [r / 255, g / 255, b / 255];
/** the paints (tints multiplied into the model's own colours; a share of 1 keeps the library's paint) */
export const LIVERIES: Record<VesselKind, Livery[]> = {
  destroyer: [{ name: 'haze grey', hull: rgb(190, 196, 202), upper: rgb(205, 210, 214) }, { name: 'dark grey', hull: rgb(120, 126, 134), upper: rgb(150, 156, 162) }],
  yacht: [{ name: 'white', hull: rgb(255, 255, 255), upper: rgb(255, 255, 255) }, { name: 'cream', hull: rgb(235, 220, 180), upper: rgb(250, 240, 215) }, { name: 'navy', hull: rgb(60, 80, 125), upper: rgb(235, 235, 235) }, { name: 'dark green', hull: rgb(60, 105, 80), upper: rgb(235, 232, 220) }],
  boat: [{ name: 'black', hull: rgb(70, 72, 78), upper: rgb(200, 200, 200) }, { name: 'khaki', hull: rgb(170, 160, 115), upper: rgb(200, 195, 165) }, { name: 'rust red', hull: rgb(150, 70, 55), upper: rgb(235, 225, 210) }, { name: 'grey', hull: rgb(140, 148, 155), upper: rgb(230, 232, 235) }, { name: 'blue', hull: rgb(70, 100, 150), upper: rgb(240, 240, 240) }, { name: 'white', hull: rgb(250, 250, 250), upper: rgb(255, 255, 255) }],
  steamer: [{ name: 'library', hull: [1, 1, 1], upper: [1, 1, 1] }],
};
const MODEL: Record<VesselKind, string> = { destroyer: 'fletcher', yacht: 'sundowner', boat: 'lucy-lavers', steamer: 'princess-elizabeth' };
/** the length of each model, m (the library's READMEs) and the draught the keel needs under it */
export const SIZE: Record<VesselKind, { length: number; beam: number; draft: number }> = {
  destroyer: { length: 114.7, beam: 12.1, draft: 5.2 }, yacht: { length: 15.84, beam: 3.81, draft: 1.52 }, boat: { length: 10.82, beam: 3.12, draft: 0.7 }, steamer: { length: 61.2, beam: 7.3, draft: 1.69 },
};
/** the bow of every vessel at anchor points into the wind (the wind blows towards 235 degrees, so the bows look the other way) */
const INTO_WIND = Math.atan2(-Math.cos(235 * Math.PI / 180), -Math.sin(235 * Math.PI / 180));
/** the steamer's places along the east face: she comes in from the mole's end, so the end cage first, then the middle one; her middle is a little landward of the cage so her bow is at the cage's side */
export const STEAMER_PLACE = { end: { z: CAGE_Z.end - 28 }, middle: { z: CAGE_Z.middle - 28 }, heading: Math.PI, idle: { x: 120, z: 330 } };

function rng(seed: number) { let s = seed >>> 0; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }

/** where each vessel lies: destroyers 350-500 m out on both flanks, yachts and boats 80-300 m round the mole's end in water deep enough at low tide, clear of the steamer's berth and approach */
export function layoutFleet(seed = 37): VesselPlan[] {
  const r = rng(seed), out: VesselPlan[] = [];
  const lowWater = -TIDE.amplitude;
  const free = (x: number, z: number, rad: number) => !out.some(v => Math.hypot(v.x - x, v.z - z) < rad + SIZE[v.kind].length * 0.5 * v.scale);
  const deep = (x: number, z: number, need: number) => lowWater - bed(x, z) > need + 1.2;
  const clear = (x: number, z: number) => Math.abs(x - MOLE.x) > 22 || z > MOLE.z1 + 400 || z < MOLE.rampFrom;
  const berthZone = (x: number, z: number) => x > -2 && x < 45 && z > MOLE.z0 && z < MOLE.z1 + 260;       // the steamer's berth and her way in from the end
  const make = (id: string, kind: VesselKind, x: number, z: number, scale: number, livery: Livery): VesselPlan => ({ id, kind, model: MODEL[kind], x, z, heading: INTO_WIND + (r() - 0.5) * 0.5, scale, trim: (r() * 4 - 2) * Math.PI / 180, swing: r() * 6.28, livery });
  // the destroyers on the flanks: one west, one east, 350-500 m from the shore
  const d1 = make('destroyer1', 'destroyer', -230 - r() * 40, 380 + r() * 40, 1, LIVERIES.destroyer[0]); out.push(d1);
  out.push(make('destroyer2', 'destroyer', 260 + r() * 40, 430 + r() * 60, 1, LIVERIES.destroyer[1]));
  const place = (n: number, kind: 'yacht' | 'boat', pick: (i: number) => Livery) => {
    for (let i = 0; i < n; i++) {
      for (let tries = 0; tries < 400; tries++) {
        const a = r() * Math.PI * 2, d = 80 + r() * 220, x = MOLE.x + Math.cos(a) * d * 1.2, z = MOLE.z1 + Math.sin(a) * d, s = 0.9 + r() * 0.25;
        if (z < 20 || Math.abs(x) > 300 || !clear(x, z) || berthZone(x, z) || !deep(x, z, SIZE[kind].draft * s) || !free(x, z, 14 + SIZE[kind].length * 0.5 * s)) continue;
        out.push(make(`${kind}${i + 1}`, kind, x, z, s, pick(i))); break;
      }
    }
  };
  place(4, 'yacht', i => LIVERIES.yacht[i % 4]);
  place(6, 'boat', i => LIVERIES.boat[i % 6]);
  return out;
}

const LADDER: PerspectiveLevel[] = [{ kind: 'full', minPx: 3 }, { kind: 'point', minPx: 0 }];
const POINT: Record<VesselKind, [number, number, number]> = { destroyer: [0.3, 0.32, 0.34], yacht: [0.6, 0.6, 0.58], boat: [0.3, 0.3, 0.28], steamer: [0.07, 0.07, 0.08] };

interface View { plan: VesselPlan; node: BABYLON.TransformNode; hull: BABYLON.TransformNode; model: LibraryModel | null; ready: boolean; pitch: number; roll: number; y: number; paddle: BABYLON.TransformNode[]; spin: BABYLON.TransformNode[]; half: number }

/** a repainted copy of a model's materials: the hull and the upper works are given the livery's paint (by the material's name: M_hull, M_grey, M_navy, M_green are the hull; M_white, M_deck the upper works) */
const HULL = /^m_(hull|grey|navy|green)$/, UPPER = /^m_(white|deck)$/;
function repaint(meshes: BABYLON.AbstractMesh[], lv: Livery, tag: string, kind: VesselKind, report?: Set<string>): BABYLON.AbstractMesh[] {
  const seen = new Map<BABYLON.Material, BABYLON.Material>(), out: BABYLON.AbstractMesh[] = [];
  for (let m of meshes) {
    // an instance cannot take its own material: it becomes a clone of its source (the geometry stays shared)
    if (m instanceof BABYLON.InstancedMesh && lv.name !== 'library') {
      const src = m.sourceMesh, c = src.clone(`${m.name}.${tag}`, m.parent, true)!; c.position.copyFrom(m.position); if (m.rotationQuaternion) c.rotationQuaternion = m.rotationQuaternion.clone(); else c.rotation.copyFrom(m.rotation); c.scaling.copyFrom(m.scaling); c.setEnabled(m.isEnabled(false));
      m.dispose(); m = c;
    }
    out.push(m);
    const mat = m.material; if (!mat) continue;
    report?.add(`${mat.name}|${mat.getClassName()}`);
    if (lv.name === 'library') continue;
    const n = mat.name.toLowerCase(), tint = HULL.test(n) || (kind === 'boat' && n === 'm_red') ? lv.hull : UPPER.test(n) ? lv.upper : null;
    if (!tint) continue;
    let c = seen.get(mat);
    if (!c) { c = mat.clone(`${mat.name}.${tag}`)!; seen.set(mat, c); const p = c as BABYLON.PBRMaterial; if (p.albedoTexture) p.albedoColor = new BABYLON.Color3(tint[0], tint[1], tint[2]); else p.albedoColor = new BABYLON.Color3(tint[0], tint[1], tint[2]); }
    m.material = c;
  }
  return out;
}

export class FleetView2 {
  readonly views: View[] = [];
  readonly materials = new Set<string>();
  /** called when a vessel's model is in and placed: the people module reads her deck off the meshes */
  onModel?: (plan: VesselPlan, node: BABYLON.TransformNode, meshes: BABYLON.AbstractMesh[]) => void;
  constructor(readonly scene: BABYLON.Scene, private lib: AssetLibrary, private world: World, readonly sea: SeaModel, readonly plans: VesselPlan[]) { perspectiveOf(world, scene); }

  /** load every model once (the library caches) and then each instance */
  async build(steamerAt: 'end' | 'middle' | 'idle' = 'end'): Promise<void> {
    const all: VesselPlan[] = [...this.plans, { id: 'steamer', kind: 'steamer', model: MODEL.steamer, x: 0, z: 0, heading: STEAMER_PLACE.heading, scale: 1, trim: 0, swing: 0, livery: LIVERIES.steamer[0] }];
    await Promise.all(all.map(p => this.add(p, steamerAt)));
  }
  private async add(plan: VesselPlan, steamerAt: 'end' | 'middle' | 'idle') {
    const node = new BABYLON.TransformNode('v_' + plan.id, this.scene), hull = new BABYLON.TransformNode('vh_' + plan.id, this.scene);
    hull.parent = node; hull.rotation.y = Math.PI / 2; node.rotationQuaternion = null; node.setEnabled(false); node.scaling.setAll(plan.scale);
    const v: View = { plan, node, hull, model: null, ready: false, pitch: 0, roll: 0, y: 0, paddle: [], spin: [], half: SIZE[plan.kind].beam / 2 };
    this.views.push(v);
    const m = await this.lib.model(plan.model, { parent: hull }); v.model = m;
    const inst = await m.model.ready; if (!inst) return;
    const meshes = repaint(inst.root.getChildMeshes(false), plan.livery, plan.id, plan.kind, this.materials);
    const find = (n: string) => inst.root.getChildTransformNodes(false).filter(t => t.name === n || t.name.startsWith(n + '_'));
    v.spin = find('Propeller'); v.paddle = [...find('Paddle_P'), ...find('Paddle_S')];
    for (const p of [...v.spin, ...v.paddle]) p.rotationQuaternion = null;
    if (plan.kind === 'steamer') {
      // her width over the paddle boxes, read off the model, puts her side against the fenders
      node.rotation.y = STEAMER_PLACE.heading; node.computeWorldMatrix(true); for (const t of node.getChildTransformNodes(false)) t.computeWorldMatrix(true);
      let lo = Infinity, hi = -Infinity; for (const mm of meshes) { if (mm.getTotalVertices() === 0) continue; const b = mm.getBoundingInfo().boundingBox; lo = Math.min(lo, b.minimumWorld.x); hi = Math.max(hi, b.maximumWorld.x); }
      const cx = (lo + hi) / 2, half = (hi - lo) / 2; v.half = half;
      plan.x = FACE_E + 0.5 + half - (cx - node.position.x); plan.z = steamerAt === 'idle' ? STEAMER_PLACE.idle.z : STEAMER_PLACE[steamerAt].z;
      if (steamerAt === 'idle') plan.x = STEAMER_PLACE.idle.x;
    }
    this.pose(v, 0, 0);
    node.setEnabled(true); node.computeWorldMatrix(true);
    for (const t of node.getChildTransformNodes(false)) t.computeWorldMatrix(true);
    this.onModel?.(plan, node, meshes);
    const e = this.world.spawn('vessel_' + plan.id, { node, tags: ['vessel'] }); e.add(Perspective, { ladder: LADDER, color: POINT[plan.kind], fade: 0.5 }); v.ready = true;
  }
  /** float: the vessel's draught follows the swell and the tide under her length and beam, damped; she swings a little on her anchor */
  private pose(v: View, time: number, dt: number) {
    const p = v.plan, sz = SIZE[p.kind], swing = p.kind === 'steamer' ? 0 : 0.05 * Math.sin(time * 0.11 + p.swing);
    const hd = p.heading + swing, s = Math.sin(hd), c = Math.cos(hd), L = sz.length * 0.4 * p.scale, B = sz.beam * 0.4 * p.scale;
    const h = (dx: number, dz: number) => this.sea.height(p.x + dx, p.z + dz, time);
    const hb = h(s * L, c * L), hs = h(-s * L, -c * L), hp = h(-c * B, s * B), hq = h(c * B, -s * B), hc = h(0, 0);
    const pitch = Math.atan2(hb - hs, 2 * L) + p.trim, roll = Math.atan2(hp - hq, 2 * B);
    const k = dt > 0 ? Math.min(1, dt * 2.5) : 1;
    v.pitch += (pitch - v.pitch) * k; v.roll += (roll - v.roll) * k; v.y += (hc - v.y) * (dt > 0 ? Math.min(1, dt * 4) : 1);
    v.node.position.set(p.x, v.y, p.z); v.node.rotation.set(-v.pitch, hd, v.roll);
  }
  update(time: number, dt: number) {
    for (const v of this.views) {
      if (!v.ready) continue;
      this.pose(v, time, dt);
      for (const t of v.paddle) t.rotation.z = 0;
    }
  }
}
