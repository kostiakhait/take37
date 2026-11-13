// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
/**
 * The prisoners of scene 2 (stage 4): Arnold and Emily in their cages. Both are the game's own characters (the MetaHuman base, skinned glb with the 1185-joint skeleton) and live by
 * the micro-motion module (@ferret/micromotion): the sim gives breath, weight shifts, head turns and fidgets, `poseFrame` puts them on the skeleton by world-frame rotations and two-bone
 * IK, and the hands are held by props of the profile ("bars": both hands on the cage's bars; "knees": the forearms resting on the knees). Arnold squats on his heels, almost still;
 * Emily stands gripping the bars and tightens her hands now and then. They stand on the cage's platform as walkers (a `GridSupport` in the cage's frame): the platform carries them
 * when the cage rolls, and nobody's height is set by hand.
 */
import { GridSupport, Walkers, newWalker, type Walker } from '@ferret/physics';
import { newPerson, poseFrame, frameOf, profile, stepPerson, type MicroProfile, type PersonState, type PoseLike, type RigLike } from '@ferret/micromotion';
import { CAGE } from './cage';

export type Who = 'arnold' | 'emily';
/** a skeleton as plain data: joints parents-first with local rest rotation (xyzw) and translation, m */
export interface JointData { name: string; parent: number; q: [number, number, number, number]; t: [number, number, number] }

const qmul = (a: ArrayLike<number>, b: ArrayLike<number>): [number, number, number, number] => [
  a[3]! * b[0]! + a[0]! * b[3]! + a[1]! * b[2]! - a[2]! * b[1]!, a[3]! * b[1]! - a[0]! * b[2]! + a[1]! * b[3]! + a[2]! * b[0]!,
  a[3]! * b[2]! + a[0]! * b[1]! - a[1]! * b[0]! + a[2]! * b[3]!, a[3]! * b[3]! - a[0]! * b[0]! - a[1]! * b[1]! - a[2]! * b[2]!];
const qrot = (q: ArrayLike<number>, v: ArrayLike<number>): [number, number, number] => {
  const x = q[0]!, y = q[1]!, z = q[2]!, w = q[3]!, tx = 2 * (y * v[2]! - z * v[1]!), ty = 2 * (z * v[0]! - x * v[2]!), tz = 2 * (x * v[1]! - y * v[0]!);
  return [v[0]! + w * tx + (y * tz - z * ty), v[1]! + w * ty + (z * tx - x * tz), v[2]! + w * tz + (x * ty - y * tx)];
};

/** the rest rotation the skeleton's root had before it was moved down to its children (the MetaHuman root is turned 90 degrees, its Z is up): the pose layer wants a y-up root */
export type RootFix = [number, number, number, number];
const conj = (q: ArrayLike<number>): [number, number, number, number] => [-q[0]!, -q[1]!, -q[2]!, q[3]!];
/** the rig the pose layer wants, from the skeleton's rest pose; a turned root is made identity and its turn given to its children (the world rest pose does not change) */
export function rigOf(joints0: JointData[]): RigLike & { rootFix: RootFix } {
  const R: RootFix = joints0[0]!.parent < 0 ? [...joints0[0]!.q] as RootFix : [0, 0, 0, 1];
  const joints = joints0.map((j, i) => (i === 0 ? { ...j, q: [0, 0, 0, 1] as JointData['q'] } : j.parent === 0 ? { ...j, q: qmul(R, j.q), t: qrot(R, j.t) } : j));
  const n = joints.length, names = joints.map((j) => j.name), index = new Map(names.map((nm, i) => [nm, i]));
  const parent = Int16Array.from(joints.map((j) => j.parent)), restQ = new Float32Array(4 * n), wq = new Float32Array(4 * n), tLocal = new Float32Array(3 * n), restWorld = new Float32Array(3 * n);
  for (let i = 0; i < n; i++) {
    const j = joints[i]!;
    restQ.set(j.q, 4 * i); tLocal.set(j.t, 3 * i);
    if (j.parent < 0) { wq.set(j.q, 4 * i); restWorld.set(j.t, 3 * i); continue; }
    const pq = wq.subarray(4 * j.parent, 4 * j.parent + 4), w = qmul(pq, j.q), r = qrot(pq, j.t);
    wq.set(w, 4 * i);
    restWorld.set([restWorld[3 * j.parent]! + r[0], restWorld[3 * j.parent + 1]! + r[1], restWorld[3 * j.parent + 2]! + r[2]], 3 * i);
  }
  return { n, names, index, parent, restQ, restWorldQ: wq, tLocal, restWorld, legScale: 1, rootFix: R };
}

/** the hand targets of a prop are from the shoulder in the figure's frame (left +x, forward +z, up +y), metres at the reference arm length */
export interface PrisonerSpec {
  who: Who; file: string; profile: MicroProfile; seatHeight: number; sit: number; prop: string; propLo: number; propHi: number; place: [number, number]; face: number;
  /** a squat (the module's seat puts the feet forward, as on a chair): the feet's offset from the seat's target, m (x out, y up, z forward), and the trunk's lean forward, rad */
  feet?: [number, number, number]; lean?: number;
}

export function emilyProfile(): MicroProfile {
  const p = profile('bystander'); p.name = 'emily-caged'; p.role = 'prisoner';
  // the bars of the cage in front of her, at her shoulder height, a little wider than her shoulders: both hands round them
  p.props = { bars: { hand: 'both', socket: 'hand_l', rest: [[0.09, -0.1, 0.46], [0.09, -0.1, 0.46]], use: [[0.11, -0.07, 0.47], [0.11, -0.07, 0.47]] } };
  p.repertoire = { 'look-around': 3, 'shift-weight': 2 };
  p.temperament = { energy: 0.3, nervousness: 0.75, expansiveness: 0.2, dominance: 0.1, focus: 0.3, mood: 0.1 };
  p.interests = { action: 2, player: 2, actor: 1 };
  p.maxStill = 5;
  return p;
}
export function arnoldProfile(): MicroProfile {
  const p = profile('bystander'); p.name = 'arnold-caged'; p.role = 'prisoner';
  // on his heels, forearms on his knees
  p.props = { knees: { hand: 'both', socket: 'hand_l', rest: [[-0.045, -0.49, 0.38], [-0.045, -0.49, 0.38]], use: [[-0.03, -0.47, 0.4], [-0.03, -0.47, 0.4]] } };
  p.repertoire = { 'look-around': 2 };
  p.temperament = { energy: 0.1, nervousness: 0.3, expansiveness: 0.1, dominance: 0.05, focus: 0.6, mood: 0.15 };
  p.interests = { action: 1.5, player: 1.5 };
  p.maxStill = 8;
  return p;
}

/** a frame for the walkers from a node's world matrix */
function frameOfNode(node: BABYLON.TransformNode) {
  const inv = new BABYLON.Matrix(), v = new BABYLON.Vector3();
  return {
    toLocal(p: [number, number, number]): [number, number, number] { node.getWorldMatrix().invertToRef(inv); v.set(p[0], p[1], p[2]); const r = BABYLON.Vector3.TransformCoordinates(v, inv); return [r.x, r.y, r.z]; },
    toWorld(p: [number, number, number]): [number, number, number] { v.set(p[0], p[1], p[2]); const r = BABYLON.Vector3.TransformCoordinates(v, node.getWorldMatrix()); return [r.x, r.y, r.z]; },
  };
}

export class Prisoner {
  readonly P: PersonState;
  root: BABYLON.TransformNode;
  ready = false;
  private rig: (RigLike & { rootFix: RootFix }) | null = null;
  private nodes: BABYLON.TransformNode[] = [];
  private pose: PoseLike | null = null;
  private w: Walker = newWalker();
  private t = 0;
  /** the nodes of the figure placed on the cage's platform by the walker */
  constructor(readonly spec: PrisonerSpec, private cage: BABYLON.TransformNode, private walkers: Walkers, private grid: GridSupport, private scene: BABYLON.Scene) {
    this.root = new BABYLON.TransformNode('prisoner_' + spec.who, scene); this.root.parent = cage;
    this.P = newPerson(spec.who, spec.profile, spec.who === 'arnold' ? 3737 : 9191, { external: true });
    this.P.posture = spec.sit > 0.5 ? 'sit' : 'stand'; this.P.trans = null as never;
  }
  async load(url: string) {
    const slash = url.lastIndexOf('/');
    const c = await BABYLON.SceneLoader.LoadAssetContainerAsync(url.slice(0, slash + 1), url.slice(slash + 1), this.scene);
    c.addAllToScene();
    const top = c.meshes[0]!; top.parent = this.root;
    for (const m of c.meshes) { m.isPickable = false; m.alwaysSelectAsActiveMesh = true; }
    const sk = c.skeletons[0]; if (!sk) throw new Error('prisoner glb has no skeleton: ' + url);
    const nodes = sk.bones.map((b) => b.getTransformNode()!);
    const joints: JointData[] = nodes.map((n, i) => {
      const q = n.rotationQuaternion ?? BABYLON.Quaternion.FromEulerVector(n.rotation), p = nodes.indexOf(n.parent as BABYLON.TransformNode);
      if (p >= i) throw new Error('joint order: parent after child at ' + n.name);
      return { name: n.name.slice(n.name.lastIndexOf('/') + 1), parent: p, q: [q.x, q.y, q.z, q.w], t: [n.position.x, n.position.y, n.position.z] };
    });
    this.nodes = nodes; this.rig = rigOf(joints);
    const pi = this.rig.index.get('pelvis')!;
    this.pose = { q: new Float32Array(this.rig.restQ), pelvis: [this.rig.tLocal[3 * pi]!, this.rig.tLocal[3 * pi + 1]!, this.rig.tLocal[3 * pi + 2]!] };
    // he stands on the platform: dropped a little above it, the physics lands him (the platform's top is a cell of the grid in the cage's frame)
    this.walkers.mount(this.w, this.grid, [this.spec.place[0], CAGE.platformTop + 0.05, this.spec.place[1]]);
    this.ready = true;
  }
  update(dt: number) {
    if (!this.ready || !this.rig || !this.pose) return;
    this.t += dt;
    const sp = this.spec;
    // the platform carries him and holds him (gravity, the supports): the cage's frame gives the place, the walker the height
    this.walkers.step(this.w, dt, 0, 0, true);
    const l = this.w.local ?? [sp.place[0], CAGE.platformTop, sp.place[1]];
    this.root.position.set(l[0], l[1], l[2]); this.root.rotation.y = sp.face;
    stepPerson(this.P, dt, { targets: [{ id: 'player', pos: [0, 1.6, -30], tags: ['player', 'action'], loud: 0.2, speed: 1 }], take: 'idle' } as never);
    const out = this.P.out;
    out.sit = sp.sit; out.props = { ...out.props, [sp.prop]: sp.propLo + (sp.propHi - sp.propLo) * (0.5 + 0.5 * Math.sin(this.t * 0.35 + (sp.who === 'emily' ? 1.3 : 0))) * (0.6 + 0.4 * Math.sin(this.t * 1.7)) };
    // rest pose, then the module's pose
    this.pose.q.set(this.rig.restQ);
    const pi = this.rig.index.get('pelvis')!; this.pose.pelvis = [this.rig.tLocal[3 * pi]!, this.rig.tLocal[3 * pi + 1]!, this.rig.tLocal[3 * pi + 2]!];
    const f = frameOf(out, sp.profile, { lod: 'near', time: this.P.t, seed: this.P.seed, seatHeight: sp.seatHeight });
    if (sp.feet) { f.feet.l = [...sp.feet]; f.feet.r = [...sp.feet]; }
    if (sp.lean) for (const b of ['spine_01', 'spine_02', 'spine_03']) f.rot.push({ bone: b, axis: 0, rad: sp.lean });
    poseFrame(this.rig, this.pose, f);
    // back to the nodes: the root keeps its own rest turn, its children take theirs back from the y-up frame the pose layer worked in
    const q = this.pose.q, R = this.rig.rootFix, Ri = conj(R);
    for (let i = 1; i < this.nodes.length; i++) {
      const n = this.nodes[i]!; let x = q[4 * i]!, y = q[4 * i + 1]!, z = q[4 * i + 2]!, w = q[4 * i + 3]!;
      if (this.rig.parent[i] === 0) { const r = qmul(Ri, [x, y, z, w]); x = r[0]; y = r[1]; z = r[2]; w = r[3]; }
      (n.rotationQuaternion ??= new BABYLON.Quaternion()).set(x, y, z, w);
    }
    const pp = qrot(Ri, this.pose.pelvis); this.nodes[pi]!.position.set(pp[0], pp[1], pp[2]);
  }
}

export interface Prisoners { arnold: Prisoner; emily: Prisoner; walkers: Walkers }
/** both prisoners: Arnold in the middle cage, Emily in the cage at the end; each cage gets a platform grid in its own frame */
export function makePrisoners(scene: BABYLON.Scene, cages: { middle: BABYLON.TransformNode; end: BABYLON.TransformNode }, water: () => number): Prisoners {
  const mk = (cage: BABYLON.TransformNode, name: string) => {
    const g = new GridSupport(name, 0.25, [0, 0], frameOfNode(cage));
    const half = CAGE.width / 2 - 0.06;
    for (let x = -half; x <= half; x += 0.25) for (let z = -half; z <= half; z += 0.25) g.add(x, CAGE.platformTop, z, true);
    return g;
  };
  const gA = mk(cages.middle, 'cage-middle'), gE = mk(cages.end, 'cage-end');
  const walkers = new Walkers([gA, gE], { water });
  const arnold = new Prisoner({ who: 'arnold', file: 'arnold', profile: arnoldProfile(), seatHeight: 0.2, sit: 1, prop: 'knees', propLo: 0, propHi: 1, place: [0.1, -0.15], face: Math.PI + 0.35, feet: [0.04, 0, -0.34], lean: 0.2 }, cages.middle, walkers, gA, scene);
  const emily = new Prisoner({ who: 'emily', file: 'emily', profile: emilyProfile(), seatHeight: 0.47, sit: 0, prop: 'bars', propLo: 0, propHi: 1, place: [0.0, -0.64], face: Math.PI }, cages.end, walkers, gE, scene);
  return { arnold, emily, walkers };
}
