// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
/**
 * The grove behind the dunes of scene 2: about 200 library spruces and bushes (borrowed from Ferret: spruce-tree, bush-1, bush-2), each model drawn by thin instances (one draw
 * per mesh of the model), placed by a seeded scatter on the ground of `shore.ts`, kept off the post's pad, the road and the beach.
 */
import type { AssetLibrary } from '@ferret/levels';
import { BASE, bed } from './shore';

export interface Placement { id: string; x: number; z: number; yaw: number; scale: number }
function rng(seed: number) { let s = seed >>> 0; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }

/** where the trees and the bushes stand: clumps in a band behind the dunes (z -430 .. -300 about the field's middle), a few lone trees on the dunes' back */
export function layoutGrove(seed = 1940, spruces = 150, bushes = 50): Placement[] {
  const r = rng(seed), out: Placement[] = [];
  const X = 300;
  const clumps: Array<[number, number, number]> = []; for (let i = 0; i < 9; i++) clumps.push([(r() * 2 - 1) * (X - 40), -300 - r() * 120, 28 + r() * 30]);
  const ok = (x: number, z: number, gap: number) => Math.abs(x) <= X && z < -285 && Math.hypot(x - BASE.x, z - BASE.z) > BASE.r + 40 && bed(x, z) > 3 && !out.some(p => Math.hypot(p.x - x, p.z - z) < gap);
  const tries = (n: number, id: (k: number) => string, scale: () => number, gap: number) => {
    let k = 0, guard = 0;
    while (k < n && guard++ < n * 80) {
      const c = clumps[Math.floor(r() * clumps.length)], a = r() * Math.PI * 2, d = Math.sqrt(r()) * c[2], x = c[0] + Math.cos(a) * d, z = c[1] + Math.sin(a) * d;
      if (!ok(x, z, gap)) continue; out.push({ id: id(k), x, z, yaw: r() * Math.PI * 2, scale: scale() }); k++;
    }
  };
  tries(spruces, () => 'spruce-tree', () => 0.75 + r() * 0.6, 5.5);
  tries(bushes, k => (k % 2 ? 'bush-1' : 'bush-2'), () => 0.8 + r() * 0.7, 3);
  return out;
}

/** target heights in metres by model (the model is scaled so that its own height times the placement's scale gives these) */
const HEIGHT: Record<string, number> = { 'spruce-tree': 11, 'bush-1': 1.6, 'bush-2': 1.6 };

export class Grove {
  readonly meshes: BABYLON.Mesh[] = [];
  readonly counts: Record<string, number> = {};
  constructor(private scene: BABYLON.Scene, private lib: AssetLibrary, readonly placements: Placement[]) {}
  async build(): Promise<void> {
    const ids = [...new Set(this.placements.map(p => p.id))];
    await Promise.all(ids.map(id => this.kind(id, this.placements.filter(p => p.id === id))));
  }
  private async kind(id: string, list: Placement[]) {
    const holder = new BABYLON.TransformNode('grove-' + id, this.scene);
    const m = await this.lib.model(id, { parent: holder }); const inst = await m.model.ready; if (!inst) throw new Error(id + ': no model');
    holder.computeWorldMatrix(true);
    const src = inst.root.getChildMeshes(false).filter(x => x.getTotalVertices() > 0 || (x instanceof BABYLON.InstancedMesh && x.sourceMesh.getTotalVertices() > 0));
    for (const x of src) x.computeWorldMatrix(true);
    // the model's own size: its height over the lowest point; the model stands on y = 0 at its foot
    let lo = Infinity, hi = -Infinity; for (const x of src) { x.refreshBoundingInfo?.(); const b = x.getBoundingInfo().boundingBox; lo = Math.min(lo, b.minimumWorld.y); hi = Math.max(hi, b.maximumWorld.y); }
    const k = (HEIGHT[id] ?? 5) / Math.max(0.1, hi - lo);
    this.counts[id] = list.length;
    for (const x of src) {
      const base = x instanceof BABYLON.InstancedMesh ? x.sourceMesh : (x as BABYLON.Mesh);
      const copy = base.clone('g_' + id + '_' + x.name, null, true)!; copy.position.setAll(0); copy.rotationQuaternion = null; copy.rotation.setAll(0); copy.scaling.setAll(1); copy.setEnabled(true); copy.isPickable = false; copy.alwaysSelectAsActiveMesh = true;
      const local = x.computeWorldMatrix(true).clone(), buf = new Float32Array(list.length * 16), tmp = new BABYLON.Matrix();
      list.forEach((p, i) => {
        const s = k * p.scale, P = BABYLON.Matrix.Compose(new BABYLON.Vector3(s, s, s), BABYLON.Quaternion.FromEulerAngles(0, p.yaw, 0), new BABYLON.Vector3(p.x, bed(p.x, p.z) - lo * s - 0.15, p.z));
        local.multiplyToRef(P, tmp); tmp.copyToArray(buf, i * 16);
      });
      copy.thinInstanceSetBuffer('matrix', buf, 16, true); copy.thinInstanceRefreshBoundingInfo(true);
      this.meshes.push(copy);
    }
    holder.setEnabled(false);
  }
}
