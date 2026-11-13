// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import type { AssetLibrary, LibraryCharacter } from '@ferret/levels';
import { Walkers, FieldSupport, newWalker, type Walker } from '@ferret/physics';
import { MicroSession, sampleRot, type PersonState } from '@ferret/micromotion';

/**
 * The people of the field: a handful of the library's figures (Tommies, an officer, a sailor) standing about their work. Each stands on the ground by the engine's `Walkers` (a field support of the scene's ground: nobody is set at a height by hand),
 * plays the library's idle clip, and has a micro-motion person (`MicroSession`, the 'bystander' profile and a seed of his own): gaze, breath and gestures are added to his bones after the clip has posed him, as the Dunkirk sample does it.
 */
export interface CrewSpec { id: string; figure: string; x: number; z: number; /** radians, 0 = +z, positive toward +x */ facing: number }
export const CREW: CrewSpec[] = [
  { id: 'guard1', figure: 'tommy-1', x: 321, z: 566, facing: Math.PI * 1.05 },
  { id: 'guard2', figure: 'tommy-2', x: 327, z: 562, facing: Math.PI * 0.95 },
  { id: 'duty', figure: 'officer-1', x: 190, z: 262, facing: -Math.PI / 2 },
  { id: 'mech1', figure: 'tommy-3', x: 214, z: 390, facing: Math.PI / 2 },
  { id: 'mech2', figure: 'tommy-coat-1', x: 212, z: 394, facing: Math.PI / 2 + 0.6 },
  { id: 'fuel', figure: 'sailor-2', x: 270, z: 452, facing: Math.PI },
  { id: 'runwayman', figure: 'tommy-cap-1', x: 112, z: 120, facing: 0.4 },
];
const CLIPS = ['Idle', 'Idle_01', 'Idle_02', 'Talking_01', 'Walk_Fwd'];

interface Person { spec: CrewSpec; c: LibraryCharacter | null; node: BABYLON.TransformNode | null; w: Walker; bones: Map<string, BABYLON.TransformNode>; state: PersonState | null; groups: Record<string, BABYLON.AnimationGroup> }

export class Crew {
  readonly walkers: Walkers; readonly micro = new MicroSession(); readonly people: Person[] = [];
  private shadow: BABYLON.ShadowGenerator | null;
  constructor(private scene: BABYLON.Scene, private lib: AssetLibrary, ground: (x: number, z: number) => number, shadow: BABYLON.ShadowGenerator | null) {
    this.walkers = new Walkers([new FieldSupport('ground', ground)]); this.shadow = shadow;
    scene.onBeforeRenderObservable.add(() => this.frame());
  }
  async build(list: CrewSpec[] = CREW) {
    await Promise.all(list.map(async (spec, i) => {
      const p: Person = { spec, c: null, node: null, w: newWalker(), bones: new Map(), state: null, groups: {} };
      this.people.push(p);
      try {
        const c = await this.lib.character(spec.figure, { compatibleClips: true }); const inst = await c.model.ready; if (!inst) throw new Error('no model');
        const bound = await this.lib.bindClips(c, { map: Object.fromEntries(CLIPS.map(k => [k, 'cc-clips/' + k])) });
        p.c = c; p.node = inst.root as unknown as BABYLON.TransformNode; p.groups = bound.groups;
        this.walkers.place(p.w, spec.x, 1e4, spec.z); for (let k = 0; k < 8; k++) this.walkers.step(p.w, 1 / 30);
        p.node.rotationQuaternion = null; p.node.position.set(p.w.x, p.w.y, p.w.z); p.node.rotation.y = spec.facing;
        for (const m of p.node.getChildMeshes()) { m.isPickable = false; m.alwaysSelectAsActiveMesh = true; if (this.shadow) this.shadow.addShadowCaster(m); }
        for (const g of Object.values(bound.groups)) for (const ta of g.targetedAnimations) ta.animation.enableBlending = false;
        const idle = bound.groups['Idle'] ?? Object.values(bound.groups)[0]; if (idle) { idle.start(true, 1, idle.from + ((i * 0.37) % 1) * (idle.to - idle.from), idle.to); idle.weight = 1; }
        for (const t of p.node.getChildTransformNodes(false)) p.bones.set(t.name.slice(t.name.lastIndexOf('/') + 1), t);
        p.state = this.micro.spawn(spec.id, 'bystander', 100 + i * 17, { pos: [spec.x, p.w.y, spec.z], facing: spec.facing });
      } catch (e) { console.warn('crew', spec.id, e); }
    }));
  }
  private frame() {
    const dt = Math.min(0.05, this.scene.getEngine().getDeltaTime() / 1000); this.micro.step(dt);
    for (const p of this.people) {
      if (!p.node || !p.state) continue;
      this.walkers.step(p.w, dt); p.node.position.set(p.w.x, p.w.y, p.w.z);
      const o = p.state.out, put = (bone: string, ax: 'pitch' | 'yaw' | 'roll', rad: number) => {
        const n = p.bones.get(bone); if (!n || Math.abs(rad) < 1e-5) return; const q = n.rotationQuaternion ?? BABYLON.Quaternion.Identity();
        n.rotationQuaternion = q.multiply(BABYLON.Quaternion.RotationAxis(ax === 'pitch' ? BABYLON.Axis.X : ax === 'yaw' ? BABYLON.Axis.Y : BABYLON.Axis.Z, rad));
      };
      const mirror = p.state.profile.handedness === 'right';
      for (const g of o.gestures) for (const r of sampleRot(g.g, g.u, g.amp, mirror)) put(r.bone, r.axis, r.rad);
      put('head', 'yaw', o.gaze.head.yaw * 0.5); put('head', 'pitch', -o.gaze.head.pitch * 0.5); put('neck_02', 'yaw', o.gaze.head.yaw * 0.3); put('spine_05', 'yaw', o.gaze.chest.yaw * 0.4);
      const br = 0.016 * Math.sin(p.state.t * (1.2 + 2 * o.arousal)); put('spine_03', 'pitch', -br);
    }
  }
}
