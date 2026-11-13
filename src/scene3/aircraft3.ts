// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import type { AssetLibrary, LibraryModel } from '@ferret/levels';
import { Aeroplane } from '@ferret/physics-vehicles';
import { Perspective, BabylonBackend, PerspectiveService, type PerspectiveLevel } from '@ferret/perspective';
import type { World } from '@ferret/core';
import SPEC_JSON from '@airwar/spec';

/**
 * Aircraft on the field. A library model is put in a holder (nose on +X, up on +Y, the left wing on +Z, as the flight model's body frame is) and either stands where it is put (the parked ones) or is posed
 * from an `Aeroplane` each frame (the Mustang). The model of the library loads with its nose on -X: it is turned half a round about its up axis, as the Dunkirk sample does. Craft that may be far are
 * entities with a `Perspective` ladder [full, point], so a far one is a dot and grows into the model by its size on the screen.
 */
type Vec3 = [number, number, number];
export const SPEC = (SPEC_JSON as { aircraft: Record<string, never> }).aircraft as Record<string, never>;
const LADDER: PerspectiveLevel[] = [{ kind: 'full', minPx: 3 }, { kind: 'point', minPx: 0 }];

export function perspectiveOf(world: World, scene: BABYLON.Scene): PerspectiveService {
  if (world.hasService('perspective')) return world.service<PerspectiveService>('perspective');
  return world.addService(new PerspectiveService({ backend: new BabylonBackend(scene) }));
}

const rotateBy = (q: [number, number, number, number], v: Vec3): Vec3 => {
  const [x, y, z, w] = q, tx = 2 * (y * v[2] - z * v[1]), ty = 2 * (z * v[0] - x * v[2]), tz = 2 * (x * v[1] - y * v[0]);
  return [v[0] + w * tx + (y * tz - z * ty), v[1] + w * ty + (z * tx - x * tz), v[2] + w * tz + (x * ty - y * tx)];
};
/** the flight model's frame (north, east, down) to the scene's (x = -east, y = up, z = -north) */
export const toScene = (p: Vec3): Vec3 => [-p[1], -p[2], -p[0]];

export class AircraftModel {
  readonly holder: BABYLON.TransformNode;
  root: BABYLON.TransformNode | null = null;
  model: LibraryModel | null = null;
  props: BABYLON.TransformNode[] = []; gear: BABYLON.TransformNode[] = []; canopy: BABYLON.TransformNode[] = [];
  /** the pilot's eye in the holder frame (forward, up, side), from the gunsight glass; null when the model has none */
  eye: Vec3 | null = null;
  /** the lowest point of the model above the holder's origin (negative: below), when the model is level */
  bottom = 0;
  ready: Promise<void>;
  private spin = 0;
  meshes: BABYLON.AbstractMesh[] = [];
  constructor(readonly scene: BABYLON.Scene, readonly lib: AssetLibrary, readonly id: string, readonly name: string, o: { wingX?: number } = {}) {
    this.holder = new BABYLON.TransformNode(name, scene); this.holder.rotationQuaternion = new BABYLON.Quaternion(); this.holder.setEnabled(false);
    this.ready = (async () => {
      const m = await lib.model(id, { parent: this.holder }); this.model = m;
      const inst = await m.model.ready; if (!inst) throw new Error(id + ': no model');
      this.root = inst.root as unknown as BABYLON.TransformNode;
      const all = [...this.root.getChildTransformNodes(false), ...this.root.getChildMeshes(false)] as BABYLON.TransformNode[], by = (re: RegExp) => all.filter(n => re.test(n.name.slice(n.name.lastIndexOf('/') + 1).replace(/_\d+$/, '')));
      this.props = by(/^(Prop|Propeller|Prop_[LR\d])$/); this.gear = by(/^(MainGear|TailGear|MainLeg|MainWheel|TailWheel|TailStrut)/); this.canopy = by(/^(Canopy|Windshield)$/);
      for (const p of this.props) p.rotationQuaternion = null;
      this.root.rotationQuaternion = null; this.root.rotation.y = Math.PI;                  // nose first: the library's models have the nose on -X
      this.holder.computeWorldMatrix(true); this.root.computeWorldMatrix(true);
      this.meshes = this.root.getChildMeshes(); for (const x of this.meshes) { x.isPickable = false; x.alwaysSelectAsActiveMesh = true; x.refreshBoundingInfo({}); }
      if (o.wingX !== undefined) {
        const wing = this.meshes.find(x => /^Wing/.test(x.name.slice(x.name.lastIndexOf('/') + 1)));
        if (wing) { wing.computeWorldMatrix(true); const cw = wing.getBoundingInfo().boundingBox.centerWorld, inv = this.holder.getWorldMatrix().clone().invert(), cl = BABYLON.Vector3.TransformCoordinates(cw, inv); this.root.position.set(o.wingX - cl.x, -cl.y, 0); }
        const g = this.meshes.find(x => /GunsightGlass/.test(x.name)); if (g) { this.root.computeWorldMatrix(true); g.computeWorldMatrix(true); g.refreshBoundingInfo({}); const c = BABYLON.Vector3.TransformCoordinates(g.getBoundingInfo().boundingBox.centerWorld, this.holder.getWorldMatrix().clone().invert()); this.eye = [c.x - 0.4, c.y + 0.12, c.z]; }
      }
      const b = this.root.getHierarchyBoundingVectors(true, m => !/Shadow/i.test(m.name)); this.holder.computeWorldMatrix(true);
      this.bottom = b.min.y - this.holder.position.y;
      this.holder.setEnabled(true);
    })();
  }
  /** a pose from a flight model: the position and the body's axes (nose, up, right) in the scene's frame */
  pose(p: Aeroplane, dt = 0) {
    const q = p.q as [number, number, number, number], R = (v: Vec3) => rotateBy(q, v), pos = toScene(p.pos as Vec3), f = toScene(R([1, 0, 0])), up = toScene(R([0, 0, -1])), right = toScene(R([0, 1, 0]));
    const m = BABYLON.Matrix.FromValues(f[0], f[1], f[2], 0, up[0], up[1], up[2], 0, -right[0], -right[1], -right[2], 0, 0, 0, 0, 1);
    BABYLON.Quaternion.FromRotationMatrixToRef(m, this.holder.rotationQuaternion!); this.holder.position.set(pos[0], pos[1], pos[2]);
    const rpm = p.engines.length && p.controls.throttle[0] > 0.02 ? 20 + 60 * p.controls.throttle[0] : 6; this.spin += rpm * dt;
    this.props.forEach((n, i) => { n.rotationQuaternion = BABYLON.Quaternion.RotationAxis(BABYLON.Axis.X, this.spin * (i % 2 ? -1 : 1)); });
    const down = p.controls.gearDown && !p.gearCollapsed; for (const n of this.gear) n.setEnabled(down);
  }
  /** stand level on the ground at (x, z), heading `deg` (0 = nose toward -z, 90 = toward +x) */
  place(x: number, z: number, deg: number, ground: (x: number, z: number) => number, pitchDeg = 0) {
    const h = (deg * Math.PI) / 180;
    // nose on +X in the holder: a turn about up by (pi/2 - heading) puts it toward (sin h, -cos h)
    this.holder.rotationQuaternion = BABYLON.Quaternion.RotationYawPitchRoll(Math.PI / 2 - h, 0, pitchDeg * Math.PI / 180 * -1);
    this.holder.position.set(x, ground(x, z) - this.bottom, z);
  }
  setCanopy(show: boolean) { for (const n of this.canopy) n.setEnabled(show); }
  setProps(show: boolean) { for (const n of this.props) n.setEnabled(show); }
  /** make it an entity of the perspective service (it must be ready) */
  far(world: World, color: [number, number, number], tag = 'aircraft') {
    this.holder.computeWorldMatrix(true);
    const e = world.spawn(this.name, { node: this.holder, tags: [tag] }); e.add(Perspective, { ladder: LADDER, color, fade: 0.5 }); return e;
  }
}

/** the flight model of a kind of the sample, on this scene's ground (the sample's own spec file; the ground in the flight model's frame: north, east) */
export function makeAeroplane(kind: string, ground: (x: number, z: number) => number, wind: (p: Vec3) => Vec3 = () => [0, 0, 0]): Aeroplane {
  const LOAD: Record<string, { positive: number; negative: number }> = { p51d: { positive: 8, negative: -4 }, b17g: { positive: 3.5, negative: -1.4 }, bf109g6: { positive: 8, negative: -4 } };
  return new Aeroplane(SPEC[kind] as never, { ground: (n: number, e: number) => ground(-e, -n), surface: (n: number, e: number) => (ground(-e, -n) < 0.3 ? 'water' : 'land'), wind, loadLimit: LOAD[kind] } as never);
}
/** where the model's wing is along the body, from the flight model's strips, to put the model's wing there */
export function wingOf(p: Aeroplane): number { const s = (p as unknown as { strips?: { name: string; at: Vec3 }[] }).strips?.find(q => q.name === 'wingL1'); return s ? s.at[0] : 0; }
