// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import type { AssetLibrary } from '@ferret/levels';
import { AircraftModel } from './aircraft3';
import { Geo, Frame, box, rnd } from './geo3';
import { Mats } from './mats3';
import { sandbagTexture } from './textures3';
import { FIELD_LEVEL } from './ground3';

/**
 * Props of the field from the library (lorry, the twin Bofors, the 25-pounder) and made in the scene: sandbag rings round the gun sites (the sandbag texture is drawn in code), crate stacks of the library's crate materials.
 * Library models are put with `AircraftModel.place` (a holder: the model's nose on +X, standing on the ground).
 */
export interface PropSpec { id: string; model: string; x: number; z: number; yaw: number }
export const LIB_PROPS: PropSpec[] = [
  { id: 'bedford1', model: 'bedford-qld', x: 212, z: 520, yaw: 90 },
  { id: 'bedford2', model: 'bedford-qld', x: 262, z: 436, yaw: 180 },
  { id: 'bofors1', model: 'bofors-twin-mk1', x: 150, z: -180, yaw: 0 },
  { id: 'bofors2', model: 'bofors-twin-mk1', x: 206, z: 560, yaw: 120 },
  { id: 'gun25', model: 'qf-25pdr', x: 300, z: 340, yaw: 270 },
];
const L = FIELD_LEVEL;

export async function buildProps(scene: BABYLON.Scene, lib: AssetLibrary, mats: Mats, ground: (x: number, z: number) => number, shadow: BABYLON.ShadowGenerator | null): Promise<{ models: AircraftModel[]; meshes: BABYLON.Mesh[] }> {
  const models: AircraftModel[] = [], meshes: BABYLON.Mesh[] = [], r = rnd(91);
  for (const p of LIB_PROPS) {
    const m = new AircraftModel(scene, lib, p.model, p.id); models.push(m);
    void m.ready.then(() => { m.place(p.x, p.z, p.yaw, ground); if (shadow) for (const x of m.meshes) shadow.addShadowCaster(x); }).catch(e => console.warn('prop', p.id, e));
  }
  await Promise.all(models.map(m => m.ready.catch(() => null)));
  // sandbag rings (a wall 1 m high, 0.5 m thick, round the gun)
  const sb = new BABYLON.PBRMaterial('sandbags', scene); sb.albedoTexture = sandbagTexture(scene); sb.roughness = 0.95; sb.metallic = 0; sb.backFaceCulling = false; sb.environmentIntensity = 0.3;
  const g = new Geo();
  for (const [cx, cz, rad] of [[150, -180, 4.6], [206, 560, 4.6]] as Array<[number, number, number]>) {
    const n = 22, gy = ground(cx, cz) - L;
    for (let i = 0; i < n; i++) {
      const a0 = (i / n) * Math.PI * 2, a1 = ((i + 1) / n) * Math.PI * 2; if (a0 > 5.4 && a0 < 6.0) continue;
      const f = new Frame(cx + Math.cos((a0 + a1) / 2) * rad, 0, cz + Math.sin((a0 + a1) / 2) * rad, -(a0 + a1) / 2 + Math.PI / 2);
      box(g, f, -(rad * Math.PI / n) - 0.02, rad * Math.PI / n + 0.02, gy, gy + 1.0, -0.28, 0.28, [1, 1, 1], [1.2, 0.8], [1.2, 0.8]);
    }
  }
  for (let i = 1; i < g.pos.length; i += 3) g.pos[i]! += L;
  const sm = g.mesh(scene, 'sandbag-rings', sb); if (sm) { meshes.push(sm); if (shadow) shadow.addShadowCaster(sm); }
  // crates: stacks of the library's crate materials by the hangars, the tower and the huts
  const crate = [await mats.get('crate-wood-270', { rough: 0.9 }), await mats.get('crate-wood-271', { rough: 0.9 }), await mats.get('crate-wood-274', { rough: 0.9 })];
  const spots: Array<Array<[number, number]>> = [[[206, 440], [214, 270], [292, 392]], [[210, 446], [160, 250], [296, 398]], [[203, 435], [180, 222], [288, 388]]];
  for (let k = 0; k < 3; k++) {
    const gc = new Geo();
    for (const [cx, cz] of spots[k]!) {
      const yaw = r() * 0.6 - 0.3, f = new Frame(cx, 0, cz, yaw), gy = ground(cx, cz) - L;
      box(gc, f, -0.6, 0.6, gy, gy + 0.9, -0.5, 0.5, [1, 1, 1], [1.2, 1.2], [1.2, 1.2]);
      if (r() < 0.8) box(gc, f, -0.5, 0.5, gy + 0.9, gy + 1.7, -0.4, 0.4, [0.95, 0.95, 0.95], [1.2, 1.2], [1.2, 1.2]);
      box(gc, new Frame(cx + 1.4, 0, cz + 0.3, yaw + 0.5), -0.4, 0.4, gy, gy + 0.6, -0.4, 0.4, [0.9, 0.9, 0.9], [1.2, 1.2], [1.2, 1.2]);
    }
    for (let i = 1; i < gc.pos.length; i += 3) gc.pos[i]! += L;
    const cm = gc.mesh(scene, 'crates' + k, crate[k]!); if (cm) { meshes.push(cm); if (shadow) shadow.addShadowCaster(cm); }
  }
  return { models, meshes };
}
