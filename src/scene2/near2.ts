// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
/**
 * The near view of the soldiers (PLAN-DUNKIRK D4): the library's own British figures (`examples/dynamo-troops`: Tommies in battledress, greatcoats and caps, and officers, all on the
 * Customizer's 87-bone skeleton) take the place of the cheap instanced men for the few dozen nearest to the camera. A pool of figures is built once; each frame the nearest men
 * that fit in it are given a figure, which stands or walks with the library's own clips (`Idle`, `Walk_Fwd` of cc-clips), at the pace the crowd simulation gives the man.
 * A figure stays with its man while he stays near; the men the pool does not reach, and the whole crowd at a distance, are drawn by `FarCrowd` (baked pictures of the figures, dots beyond).
 */
import type { AssetLibrary, LibraryCharacter } from '@ferret/levels';
import type { Soldier } from '@dunkirk/crowd-sim';
import { clipFor, poseKeys, type Posture } from '@ferret/ai';
import { sampleRot, fingerCurl } from '@ferret/micromotion';

/** which figure a man is: most are Tommies; one in about thirty is an officer */
export function figureOf(s: Soldier): string {
  if (s.figure) return s.figure;
  if (s.id % 29 === 7) return s.id % 2 ? 'officer-1' : 'officer-2';
  if (s.variant === 1) return `tommy-coat-${1 + (s.id % 4)}`;
  if (s.variant === 3) return `tommy-cap-${1 + (s.id % 2)}`;
  return `tommy-${1 + (s.id % 3)}`;
}
/** the pool is built of these in turn: interleaved so that the first n slots of any pool hold each figure in proportion (scene 2 passes its own counts: the figures it uses) */
export function poolIds(counts: Record<string, number>): string[] {
  const ids = Object.keys(counts), total = ids.reduce((a, k) => a + counts[k]!, 0), got: Record<string, number> = {}, out: string[] = [];
  for (let i = 1; i <= total; i++) {
    let best = ids[0]!, lag = -Infinity;
    for (const k of ids) { const l = counts[k]! * i / total - (got[k] ?? 0); if (l > lag) { lag = l; best = k; } }
    got[best] = (got[best] ?? 0) + 1; out.push(best);
  }
  return out;
}
/** the kit a figure is (what is on his head and back): a figure may stand in for another only of the same kit, so a man in a helmet is never drawn bareheaded */
export function kitOf(id: string): string {
  const b = id.replace(/-lod1$/, '');
  if (/^tommy-[123]$/.test(b)) return 'battledress-helmet';
  if (/^tommy-coat-[12]$/.test(b)) return 'greatcoat-cap';
  if (/^tommy-coat-[34]$/.test(b)) return 'greatcoat-helmet';
  if (/^sailor-[123]$/.test(b)) return 'sailor-cap';
  if (/^sailor-[45]$/.test(b)) return 'sailor-helmet';
  return b.replace(/-\d+$/, '');
}

const CLIPS = ['Idle', 'Idle_01', 'Idle_02', 'Idle_03', 'Talking_01', 'Talking_02', 'Talking_03', 'Talking_04', 'Pose_Sitting_Male', 'M_Neutral_Crouch_Idle_Loop', 'Death_Backward', 'Walk_Fwd', 'Jog_Fwd'];

/** seconds a figure takes to fade in or out */
const FADE = 0.5;
/** a lying man's stir: how far back into Death_Backward it reaches (the `from` of `clipFor`'s stir) and its pace, rad/s */
const STIR_FROM = 0.82, STIR_RATE = 1.6;
/** the depth offset of a hat (factor and units): it is drawn a little in front of the scalp the library's figures keep under it (-4 still let it through) */
const HAT_Z = -12;

interface Slot {
  id: string; character: LibraryCharacter | null; node: BABYLON.TransformNode | null; groups: Record<string, BABYLON.AnimationGroup>;
  owner: number; cur: string; ready: boolean; t: number;
  /** the man the figure is with (kept while it fades out), how opaque the figure is now (0..1), whether it is going away */
  man?: Soldier; alpha?: number; leaving?: boolean; meshes?: BABYLON.AbstractMesh[];
  /** the weight each clip is drawn with now (a change of posture is a slow cross-fade, not a cut) */
  w: Record<string, number>;
  /** the transform nodes of the figure by bone name (found once) */
  bones?: Map<string, BABYLON.TransformNode>;
  /** the sign each hand joint bends to bring the finger toward the wrist and the arm toward the body, found once from the figure's own geometry */
  signs?: Record<string, number>;
  /** a lying man's stir: seconds into the swing (0 when none) */
  stir?: number;
  /** how much of the micro-motion's gestures the figure takes now (1 on his feet, less as he goes down: an arm gesture made for standing is not drawn on a lying man) */
  microW?: number;
}

/** what we last wrote into a bone's rotation: if the animation has not rewritten it since (a bone no clip drives), we start again from what was there before we touched it, so offsets never pile up frame on frame */
const WROTE = new WeakMap<BABYLON.TransformNode, { base: BABYLON.Quaternion; out: BABYLON.Quaternion }>();
function fresh(n: BABYLON.TransformNode) {
  if (!n.rotationQuaternion) n.rotationQuaternion = BABYLON.Quaternion.FromEulerAngles(n.rotation.x, n.rotation.y, n.rotation.z);
  const w = WROTE.get(n); if (w && n.rotationQuaternion.equals(w.out)) n.rotationQuaternion.copyFrom(w.base); else WROTE.set(n, { base: n.rotationQuaternion.clone(), out: n.rotationQuaternion.clone() });
}
function done(n: BABYLON.TransformNode) { const w = WROTE.get(n); if (w && n.rotationQuaternion) w.out.copyFrom(n.rotationQuaternion); }
function refresh(n: BABYLON.TransformNode) { n.computeWorldMatrix(true); for (const c of n.getChildTransformNodes(false)) c.computeWorldMatrix(true); }

export class NearCrowd {
  readonly size: number;
  slots: Slot[] = [];
  /** the ids of the men drawn by a figure this frame (the cheap crowd skips them) */
  readonly owned = new Set<number>();
  /** figures built so far */
  get ready(): number { return this.slots.filter(s => s.ready).length; }
  /** `suffix` '-lod1' draws the library's reduced figures (about 9 000 triangles, 512 px textures, no teeth and eyes) for the second ring round the camera */
  private readonly ids: string[];
  constructor(private scene: BABYLON.Scene, private lib: AssetLibrary, counts: Record<string, number>, readonly suffix = '') {
    this.ids = poolIds(counts); const size = this.ids.length; this.size = size;
    // the micro-motion: after the clips have posed the figure this frame, the man's gestures, gaze and breath are added to the bones as small rotations
    scene.onBeforeRenderObservable.add(() => this.applyMicro());
    for (let i = 0; i < size; i++) this.slots.push({ id: '', character: null, node: null, groups: {}, owner: -1, cur: '', ready: false, t: 0, w: {} });
  }
  /** build the figures, a few at a time (the first of each kind fetches the file, the rest are copies of it) */
  async build(parallel = 3): Promise<void> {
    let next = 0;
    const worker = async () => {
      for (;;) {
        const i = next++; if (i >= this.slots.length) return;
        const s = this.slots[i], id = this.ids[i % this.ids.length] + this.suffix; s.id = id;
        try {
          const c = await this.lib.character(id, { compatibleClips: true });
          const inst = await c.model.ready; if (!inst) throw new Error('did not load');
          const bound = await this.lib.bindClips(c, { map: Object.fromEntries(CLIPS.map(k => [k, 'cc-clips/' + k])) });
          s.character = c; s.node = inst.root as unknown as BABYLON.TransformNode; s.groups = bound.groups;
          for (const m of s.node.getChildMeshes()) { m.alwaysSelectAsActiveMesh = true; m.isPickable = false; }
          // the library's figures cut the hair inside a hat away (examples/dynamo-troops/checks/build_figures.mjs); the scalp still touches the hat's crown, so the hat
          // is drawn with a depth offset and wins there
          for (const m of s.node.getChildMeshes()) if (/helmet|cap|hat|beret/i.test(m.name.slice(m.name.lastIndexOf('/') + 1)) && m.material) { m.material.zOffset = HAT_Z; m.material.zOffsetUnits = HAT_Z; }
          for (const g of Object.values(bound.groups)) { g.stop(); for (const ta of g.targetedAnimations) ta.animation.enableBlending = false; }
          s.node.setEnabled(false); s.ready = true;
        } catch (e) { console.warn('near figure', id, e); }
      }
    };
    await Promise.all(Array.from({ length: Math.min(parallel, this.slots.length) }, worker));
  }

  /** each frame: give the nearest men a figure and pose it */
  /** at most this many figures drawn at once (each is about 100 000 triangles) */
  maxActive = 24;
  update(list: Soldier[], cam0: BABYLON.Vector3, range: number, look?: BABYLON.Vector3, dt = 1 / 60, taken?: (id: number) => boolean) {
    // the men nearest the camera that are in front of it (the ones right behind it are out of frame and wait)
    const cam = cam0;
    this.owned.clear();
    const live = this.slots.filter(s => s.ready); if (!live.length) return;
    const r2 = range * range, keep2 = (range * 1.3) ** 2, d2 = (m: Soldier) => { const dx = m.x - cam.x, dz = m.z - cam.z, q = dx * dx + dz * dz; return look && dx * look.x + dz * look.z < -1.5 && q > 16 ? q + 1e5 : q; };
    // a figure is not cut in or out: it fades in over FADE seconds while the cheap man is still drawn, and fades out the same way after the cheap man is back;
    // a man keeps his figure a little beyond the range he got it at, and a nearer man takes a figure from a far one only when he is clearly nearer (no flicker at the edge)
    const held = new Set<number>();
    for (const s of live) {
      if (s.owner < 0) continue;
      held.add(s.owner);
      if (!s.leaving && (!s.man || s.man.state === 'aboard' || d2(s.man) > keep2 || taken?.(s.owner))) s.leaving = true;
    }
    const cand: { m: Soldier; d: number }[] = [];
    for (const m of list) { if (m.state === 'aboard' || held.has(m.id) || taken?.(m.id)) continue; const d = d2(m); if (d < r2) cand.push({ m, d }); }
    cand.sort((a, b) => a.d - b.d);
    const active = () => live.filter(s => s.owner >= 0 && !s.leaving);
    for (const { m, d } of cand) {
      let free = live.filter(s => s.owner < 0);
      if (active().length >= this.maxActive || !free.length) {
        // the farthest man with a figure gives it up if this one is clearly nearer
        const far = active().reduce<Slot | null>((w, s) => (!w || d2(s.man!) > d2(w.man!) ? s : w), null);
        if (!far || d2(far.man!) < d * 1.6) break;
        far.leaving = true; break;
      }
      const want = figureOf(m) + this.suffix, kit = kitOf(want);
      // his own figure, or one of the same kit (another face); never another kit: a man without a figure of his kit free stays in the ring behind
      let k = free.findIndex(s => s.id === want); if (k < 0) k = free.findIndex(s => kitOf(s.id) === kit); if (k < 0) continue;
      const s = free.splice(k, 1)[0]; s.owner = m.id; s.man = m; s.alpha = 0; s.leaving = false; for (const g of Object.values(s.groups)) g.stop(); s.w = {}; s.stir = 0;
      s.meshes = s.node ? s.node.getChildMeshes() : [];
      const sc = 0.96 + ((m.id * 0.618) % 1) * 0.09; if (s.node) s.node.scaling.setAll(sc);
    }
    for (const s of live) {
      if (s.owner < 0) { s.node?.setEnabled(false); if (Object.keys(s.w).length) { for (const g of Object.values(s.groups)) g.stop(); s.w = {}; } continue; }
      const m = s.man; if (!m || !s.node) continue;
      s.alpha = Math.min(1, Math.max(0, (s.alpha ?? 0) + (s.leaving ? -dt : dt) / FADE));
      if (s.leaving && s.alpha <= 0) { s.owner = -1; s.leaving = false; s.man = undefined; s.node.setEnabled(false); for (const g of Object.values(s.groups)) g.stop(); s.w = {}; continue; }
      for (const x of s.meshes ?? []) x.visibility = s.alpha;
      if (s.alpha >= 1 && !s.leaving) this.owned.add(m.id);
      s.node.setEnabled(true);
      // a lying or sitting man is a little lower or higher than his ground: the clips carry the height; a man on the ground keeps his feet on it
      s.node.position.set(m.x, m.y, m.z);
      s.node.rotation.y = m.heading;
      s.t += dt;
      // what to draw: walking or jogging at his pace; standing still, his posture cross-faded with standing by how far he is into it (sitting down takes seconds)
      const want: Record<string, number> = {}, frame: Record<string, { from: number; to: number; ping: boolean }> = {};
      let ratio = 1;
      const put = (p: Posture, w: number) => {
        if (w <= 0.001) return;
        // a standing man keeps one idle clip (his weight shifts and glances are the micro-motion's, not a cross-fade to another clip); a lying man stirs within his clip
        const c = clipFor({ ...m.ps, posture: p, to: null, fidgetKind: p === 'lie' && m.ps.fidgetKind === 'stir' && !m.ps.to ? 'stir' : 'none' }, m.id); want[c.clip] = (want[c.clip] ?? 0) + w;
        if (c.from > 0 || c.pingPong) frame[c.clip] = { from: c.from, to: c.to, ping: c.pingPong };
      };
      let upright = 1;
      if (m.speed > 0.2) { want[m.speed > 2.4 ? 'Jog_Fwd' : 'Walk_Fwd'] = 1; ratio = Math.min(1.5, Math.max(0.45, m.speed / 1.35)); }
      else {
        // a change of posture is a chain of poses (stand, crouch, sit, lie): he lowers through them and rises back through them
        upright = 0;
        for (const kp of poseKeys(m.ps)) { put(kp.posture, kp.weight); if (kp.posture === 'stand' || kp.posture === 'talk') upright += kp.weight; }
      }
      s.microW = upright;
      // the weights follow at a walking pace (a third of a second), so a start or a stop is not a cut either
      const rate = Object.keys(s.w).length ? Math.min(1, dt * 3) : 1;            // a figure just given to a man starts in his pose
      for (const name of new Set([...Object.keys(s.w), ...Object.keys(want)])) {
        const g = s.groups[name]; if (!g) continue;
        const cur = s.w[name] ?? 0, tgt = want[name] ?? 0, w = Math.abs(tgt - cur) < 0.01 ? tgt : cur + (tgt - cur) * rate + Math.sign(tgt - cur) * Math.min(Math.abs(tgt - cur), dt * 0.25);   // a linear floor under the rate: the exponential's long tail would leave a sliver of the old clip
        if (w <= 0.001) { if (g.isStarted) g.stop(); delete s.w[name]; continue; }
        if (!g.isStarted) {
          const span = g.to - g.from, f = frame[name];
          if (f) { g.start(false, 1, g.from + span * f.from, g.from + span * f.to); g.pause(); }
          else g.start(true, 1, g.from + ((m.id * 0.37) % 1) * span, g.to);
        }
        g.weight = w; s.w[name] = w;
        const f = frame[name];
        if (f) {
          // a held pose at the end of its clip; a stir swings back from the end and returns to it: it starts at the end frame, and when the stir is over the swing
          // under way is finished, so the pose never jumps to the middle of the clip or back from it
          const span = g.to - g.from, b = g.from + span * f.to, back = span * (1 - STIR_FROM);
          const was = s.stir ?? 0;
          if (f.ping || was > 0) {
            const now = was + dt, cyc = (x: number) => Math.floor(x * STIR_RATE / (2 * Math.PI));
            s.stir = !f.ping && cyc(now) > cyc(was) ? 0 : now;
          }
          const u = s.stir ? 0.5 + 0.5 * Math.cos(s.stir * STIR_RATE) : 1;
          // with its weight: a paused group is not animated, so without it the held pose would not take part in the blend (standing would blend with the bones'
          // rest values while he goes down, and the lying pose would land all at once when standing's weight ran out: a 100 degree turn of the pelvis in one frame)
          g.goToFrame(b - back * (1 - u), true);
        }
        else if (name === 'Walk_Fwd' || name === 'Jog_Fwd') g.speedRatio = ratio;
      }
    }
  }
  private applyMicro() {
    for (const s of this.slots) {
      const m = s.man; if (!m || !s.node || s.owner < 0 || !s.ready) continue;
      // by the joint's own name: the library's instances name their nodes '<figure>/<joint>' (tommy-1/head), the micro-motion and the hands ask for 'head'
      if (!s.bones) { s.bones = new Map(); for (const t of s.node.getChildTransformNodes(false)) s.bones.set(t.name.slice(t.name.lastIndexOf('/') + 1), t); s.signs = {}; }
      for (const n of s.bones.values()) fresh(n);
      this.relaxHands(s, m);
      const P = m.micro; if (!P) continue;
      const put = (bone: string, ax: 'pitch' | 'yaw' | 'roll', rad: number) => {
        const n = s.bones!.get(bone); if (!n || Math.abs(rad) < 1e-5) return;
        const q = n.rotationQuaternion!;
        const d = ax === 'pitch' ? BABYLON.Quaternion.RotationAxis(BABYLON.Axis.X, rad) : ax === 'yaw' ? BABYLON.Quaternion.RotationAxis(BABYLON.Axis.Y, rad) : BABYLON.Quaternion.RotationAxis(BABYLON.Axis.Z, rad);
        n.rotationQuaternion = q.multiply(d); done(n);
      };
      const o = P.out, mirror = P.profile.handedness === 'right';
      const gw = s.microW ?? 1;
      if (gw > 0.001) for (const g of o.gestures) for (const r of sampleRot(g.g, g.u, g.amp, mirror)) put(r.bone, r.axis, r.rad * gw);
      const gz = o.gaze;
      put('head', 'yaw', gz.head.yaw * 0.5); put('head', 'pitch', -gz.head.pitch * 0.5);
      put('neck_02', 'yaw', gz.head.yaw * 0.3); put('neck_01', 'yaw', gz.head.yaw * 0.2);
      put('spine_05', 'yaw', gz.chest.yaw * 0.4);
      const br = 0.016 * Math.sin(P.t * (1.2 + 2 * o.arousal)); put('spine_03', 'pitch', -br); put('spine_04', 'pitch', -br * 0.8);
    }
  }
  /** the hands at rest as a living man's: the arms a little in toward the body, the fingers each curled a little its own way (the module's `fingerCurl`); never spread like a stiff doll's */
  private relaxHands(s: Slot, m: Soldier) {
    const B = s.bones!, sg = s.signs!, t = performance.now() / 1000, seed = m.id;
    const pos = (n: string) => { const x = B.get(n); if (!x) return null; x.computeWorldMatrix(true); return x.getAbsolutePosition().clone(); };
    const spin = (n: BABYLON.TransformNode, axis: BABYLON.Vector3, a: number) => { fresh(n); n.rotate(axis, a, BABYLON.Space.WORLD); done(n); refresh(n); };
    const probe = (n: BABYLON.TransformNode, axis: BABYLON.Vector3, a: number, measure: () => number) => { const w = WROTE.get(n); const keep = n.rotationQuaternion?.clone(); n.rotate(axis, a, BABYLON.Space.WORLD); refresh(n); const v = measure(); if (keep) n.rotationQuaternion!.copyFrom(keep); refresh(n); void w; return v; };
    s.node!.computeWorldMatrix(true);
    const centre = s.node!.getAbsolutePosition();
    for (const side of ['l', 'r'] as const) {
      // the arm: in toward the body about the figure's forward axis, as far as 9 degrees; the sign is the one that brings the hand nearer the body's centre line
      const up = B.get('upperarm_' + side), hand = pos('hand_' + side);
      if (up && hand) {
        const fwd = BABYLON.Vector3.TransformNormal(BABYLON.Axis.Z, s.node!.getWorldMatrix()).normalize(), ang = 0.16;
        const key = 'arm' + side;
        if (sg[key] === undefined) {
          const d0 = Math.hypot(hand.x - centre.x, hand.z - centre.z), d1 = probe(up, fwd, 0.05, () => { const h = pos('hand_' + side)!; return Math.hypot(h.x - centre.x, h.z - centre.z); });
          sg[key] = d1 < d0 ? 1 : -1;
        }
        spin(up, fwd, sg[key]! * ang);
      }
      // the fingers: about the axis across the hand, toward the wrist
      const idx = pos('index_01_' + side), pin = pos('pinky_01_' + side), wrist = pos('hand_' + side);
      if (!idx || !pin || !wrist) continue;
      const across = idx.subtract(pin).normalize();
      ['index', 'middle', 'ring', 'pinky', 'thumb'].forEach((f, fi) => {
        const chain = [1, 2, 3].map(k => B.get(`${f}_0${k}_${side}`)).filter(Boolean) as BABYLON.TransformNode[]; if (!chain.length) return;
        const curl = fingerCurl(seed, t, fi, side === 'l' ? 0 : 1, 0.3), key = 'f' + f + side;
        if (sg[key] === undefined) {
          const tip = () => { const n = chain[chain.length - 1]!; n.computeWorldMatrix(true); return n.getAbsolutePosition().clone(); };
          const d0 = BABYLON.Vector3.Distance(tip(), wrist), d1 = probe(chain[0]!, across, 0.15, () => BABYLON.Vector3.Distance(tip(), wrist));
          sg[key] = d1 < d0 ? 1 : -1;
        }
        chain.forEach((n, k) => spin(n, across, sg[key]! * [0.5, 0.7, 0.5][k]! * curl * (f === 'thumb' ? 0.5 : 1)));
      });
    }
  }
  dispose() { for (const s of this.slots) s.character?.dispose(); }
}
