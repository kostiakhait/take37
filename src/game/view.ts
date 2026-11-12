// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// The picture of scene 1: the sim's cars, props and debris drawn with the art's models in the Babylon scene of the set; fire, smoke and blasts from the engine's vfx; the first-person camera of the police cab and the set cameras.
// VIEW FILE: it reads the sim and never writes to it.
import { VfxSystem, VfxBabylonView, FULL_CATALOG } from '@ferret/vfx';
import { qRot } from '@ferret/destruction/vehicle';
import { DentCage } from '@ferret/destruction/view-dents';
import { CAR_KINDS, SET_CAMERAS, type KindId, type SetCamera } from './config';
import type { Take } from './take';
import type { Car, Debris, SimEvent, Prop } from './sim';
import type { NodeInfo } from '@ferret/destruction/autoparts';

type V3 = [number, number, number];
const split = (url: string) => { const i = url.lastIndexOf('/'); return [url.slice(0, i + 1), url.slice(i + 1)] as const; };
const upright = (root: BABYLON.TransformNode | BABYLON.AbstractMesh | null | undefined) => { if (root) (root as BABYLON.TransformNode).rotationQuaternion = BABYLON.Quaternion.Identity(); };

interface Pack { full?: BABYLON.AssetContainer; lod?: BABYLON.AssetContainer; damaged?: BABYLON.AssetContainer }
interface WheelVis { node: BABYLON.TransformNode; mesh: BABYLON.TransformNode | null; restN: BABYLON.Quaternion; restM: BABYLON.Quaternion; steer: boolean; angle: number }
interface Look { root: BABYLON.TransformNode; nodes: Map<string, BABYLON.TransformNode>; wheels: Map<string, WheelVis> }
interface DentVis { cage: DentCage; sum: number }
interface CarVis { dents: Map<string, DentVis>; frameNo: number; car: Car; root: BABYLON.TransformNode; full: Look | null; lod: Look | null; dam: Look | null; hidden: Set<string>; shown: 0 | 1; near: boolean; infoByName: Map<string, NodeInfo>; spin: Map<string, number> }
interface Flame { handle: { id: number }; heat: number; kind: string }

export interface ViewCamera { mode: 'cab' | 'set'; set?: SetCamera }

export class GameView {
  readonly vfx = new VfxSystem();
  private vfxView!: VfxBabylonView;
  private packs = new Map<KindId, Pack>();
  private cars = new Map<string, CarVis>();
  private debris = new Map<number, BABYLON.TransformNode | BABYLON.Mesh>();
  private props = new Map<string, { node: BABYLON.TransformNode; w0: BABYLON.Matrix; moved: boolean }>();
  private flames = new Map<string, Flame>();
  private infos: Partial<Record<KindId, NodeInfo[]>> = {};
  private shadow: BABYLON.ShadowGenerator | null;
  private lookYaw = 0; private lookPitch = 0; private back = 0;
  private camQ = BABYLON.Quaternion.Identity(); private camInit = false;
  private metal: BABYLON.PBRMaterial; private cloth: BABYLON.PBRMaterial;
  private eventQueue: SimEvent[] = [];
  view: ViewCamera = { mode: 'cab' };
  private shake = 0;

  constructor(readonly scene: BABYLON.Scene, readonly camera: BABYLON.UniversalCamera, private propNodes: Map<string, BABYLON.TransformNode>, private stationNodes: Map<string, BABYLON.TransformNode>, shadow: BABYLON.ShadowGenerator | null = null) {
    this.vfx.registerAll(FULL_CATALOG as never);
    this.vfx.host = { groundHeight: () => 0 } as never;
    this.vfxView = new VfxBabylonView(scene, this.vfx, camera, { soft: true, supports: ['particles', 'impostor', 'dot'] } as never);
    this.shadow = shadow;
    this.metal = new BABYLON.PBRMaterial('debris-metal', scene); this.metal.albedoColor = new BABYLON.Color3(0.16, 0.16, 0.17); this.metal.metallic = 0.7; this.metal.roughness = 0.55;
    this.cloth = new BABYLON.PBRMaterial('debris-cloth', scene); this.cloth.albedoColor = new BABYLON.Color3(0.12, 0.2, 0.42); this.cloth.metallic = 0; this.cloth.roughness = 0.9;
  }

  /** load the models of the kinds (full, reduced, damaged) as containers to instantiate from; returns the node infos' source is read by the caller */
  async loadModels(kinds: KindId[], progress: (n: number, of: number, what: string) => void = () => {}) {
    let i = 0;
    for (const k of kinds) {
      const spec = CAR_KINDS[k], pack: Pack = {};
      progress(i++, kinds.length, k);
      const load = async (url: string | undefined) => { if (!url) return undefined; const [d, f] = split(url); try { return await BABYLON.SceneLoader.LoadAssetContainerAsync(d, f, this.scene); } catch (e) { console.warn('model not loaded', url, e); return undefined; } };
      pack.full = await load(spec.glb); pack.lod = await load(spec.lod1); pack.damaged = await load(spec.damaged);
      for (const c of [pack.full, pack.lod, pack.damaged]) for (const m of c?.materials ?? []) if (/glass/i.test(m.name) && m instanceof BABYLON.PBRMaterial) { m.alpha = 0.22; m.transparencyMode = BABYLON.Material.MATERIAL_ALPHABLEND; m.backFaceCulling = false; m.needDepthPrePass = false; }
      this.packs.set(k, pack);
    }
  }
  setInfos(infos: Partial<Record<KindId, NodeInfo[]>>) { this.infos = infos; }

  private instantiate(c: BABYLON.AssetContainer | undefined, parent: BABYLON.TransformNode): Look | null {
    if (!c) return null;
    const inst = c.instantiateModelsToScene((n) => n, false, { doNotInstantiate: true });
    const root = inst.rootNodes[0] as BABYLON.TransformNode; if (!root) return null;
    upright(root); root.parent = parent;
    const nodes = new Map<string, BABYLON.TransformNode>(), wheels = new Map<string, WheelVis>();
    for (const n of root.getDescendants(false)) if (n instanceof BABYLON.TransformNode) nodes.set(n.name, n);
    for (const [name, n] of nodes) {
      const m = name.match(/^Wheel_([A-Z0-9]+)$/); if (!m) continue;
      const mesh = nodes.get(name + '_mesh') ?? null;
      wheels.set(name, { node: n, mesh, restN: (n.rotationQuaternion ?? BABYLON.Quaternion.Identity()).clone(), restM: mesh ? (mesh.rotationQuaternion ?? BABYLON.Quaternion.Identity()).clone() : BABYLON.Quaternion.Identity(), steer: /^Wheel_F/.test(name), angle: 0 });
      n.rotationQuaternion = wheels.get(name)!.restN.clone(); if (mesh) mesh.rotationQuaternion = wheels.get(name)!.restM.clone();
    }
    for (const mesh of root.getChildMeshes()) { mesh.isPickable = false; mesh.receiveShadows = true; mesh.alwaysSelectAsActiveMesh = false; this.shadow?.addShadowCaster(mesh, false); }
    return { root, nodes, wheels };
  }

  private makeCar(car: Car): CarVis {
    const root = new BABYLON.TransformNode('car:' + car.id, this.scene), pack = this.packs.get(car.kind) ?? {};
    const full = this.instantiate(pack.full, root), lod = pack.lod ? this.instantiate(pack.lod, root) : null;
    const infoByName = new Map((this.infos[car.kind] ?? []).map((n) => [n.name, n] as const));
    const vis: CarVis = { car, root, full, lod, dam: null, hidden: new Set(), shown: 0, near: true, infoByName, spin: new Map(), dents: new Map(), frameNo: 0 };
    root.rotationQuaternion = BABYLON.Quaternion.Identity();
    return vis;
  }

  /** a new take: the old cars and effects go, the new sim's cars appear */
  startTake(take: Take) {
    for (const v of this.cars.values()) v.root.dispose();
    this.cars.clear();
    for (const d of this.debris.values()) d.dispose();
    this.debris.clear();
    for (const [, p] of this.props) { p.node.unfreezeWorldMatrix(); p.node.setEnabled(true); if (p.moved) { p.node.freezeWorldMatrix(p.w0); } p.moved = false; }
    for (const f of this.flames.values()) this.vfx.stop(f.handle as never);
    this.flames.clear();
    for (const car of take.scene.sim.cars) this.cars.set(car.id, this.makeCar(car));
    this.lookYaw = this.lookPitch = 0; this.camInit = false;
  }

  // ---- the frame ----
  /** one frame: place everything from the sim, run the effects, move the camera. `look` is the free look of the head (radians per second of input, already integrated by the caller) */
  frame(take: Take, dt: number, head: { yaw: number; pitch: number; back: boolean }) {
    const sim = take.scene.sim, cam = this.camera.globalPosition;
    this.events(take);
    // cars
    for (const vis of this.cars.values()) this.placeCar(vis, dt, cam);
    this.debrisFrame(sim.debris);
    this.propsFrame(take);
    this.flameFrame(take);
    // camera
    this.placeCamera(take, dt, head);
    this.vfxView.draw({ cameraPosition: [cam.x, cam.y, cam.z], fov: this.camera.fov, heightPx: this.scene.getEngine().getRenderHeight(), tier: 'high', dt, night: 0 } as never);
  }
  push(evs: SimEvent[]) { for (const e of evs) this.eventQueue.push(e); }
  /** fixed steps of the effects (the caller runs this once per sim step) */
  stepFx(dt: number) { this.vfx.step(dt); }

  private placeCar(vis: CarVis, dt: number, cam: BABYLON.Vector3) {
    const c = vis.car, v = c.veh, p = v.toWorld([0, 0, 0]), q = v.rot;
    vis.root.position.set(p[0], p[1], p[2]);
    (vis.root.rotationQuaternion as BABYLON.Quaternion).set(q[0], q[1], q[2], q[3]);
    const d = Math.hypot(p[0] - cam.x, p[2] - cam.z);
    const wantDam = c.shown === 1 && !!this.packs.get(c.kind)?.damaged;
    if (wantDam && !vis.dam) { vis.dam = this.instantiate(this.packs.get(c.kind)!.damaged, vis.root); }
    const useFull = d < 110 || c.role === 'player' || !vis.lod;
    if (vis.full) vis.full.root.setEnabled(!wantDam && useFull); if (vis.lod) vis.lod.root.setEnabled(!wantDam && !useFull);
    if (vis.dam) vis.dam.root.setEnabled(wantDam);
    const look = wantDam ? vis.dam : useFull ? vis.full : vis.lod;
    if (!look) return;
    // the wheels: steering and rolling; a wheel that came off is not drawn
    const steer = c.ctl.steer * 0.5 / (1 + Math.pow(Math.hypot(v.vel[0], v.vel[2]) / 14, 2)) * 1.6;
    for (const w of v.wheels) {
      const vw = look.wheels.get(w.spec.id); if (!vw) continue;
      vw.node.setEnabled(w.attached);
      vw.angle += -w.spin * dt;
      const sq = vw.steer ? BABYLON.Quaternion.RotationAxis(BABYLON.Axis.Y, steer) : BABYLON.Quaternion.Identity();
      vw.node.rotationQuaternion = sq.multiply(vw.restN);
      if (vw.mesh) vw.mesh.rotationQuaternion = BABYLON.Quaternion.RotationAxis(BABYLON.Axis.Z, vw.angle).multiply(vw.restM);
    }
    if (d < 120 && ((vis.frameNo++ + vis.car.id.length) % 6 === 0)) this.dent(vis, look);
    // parts that have come off
    for (const b of v.bodies) { if (vis.hidden.has(b.id)) continue; vis.hidden.add(b.id); for (const l of [vis.full, vis.lod, vis.dam]) { const n = l?.nodes.get(b.id); if (n) n.setEnabled(false); if (b.id.startsWith('Door_')) { const s = l?.nodes.get(b.id + '_shell'); if (s) s.setEnabled(false); } } }
  }

  /** the dents of the parts' meshes: the part's lattice (the engine's `dents`, offsets in the game frame) applied to the vertices of the part's own mesh through the engine's cage; the file's z is mirrored, so the lattice is mirrored too */
  private dent(vis: CarVis, look: Look) {
    const asm = vis.car.veh.assembly;
    for (const [id, ap] of asm.parts) {
      const lat = ap.part.dents; if (!lat) continue;
      let sum = 0; for (let i = 0; i < lat.length; i++) sum += Math.abs(lat[i]!);
      const meshes = this.partMeshes(look, id); if (!meshes.length) continue;
      const out = new Float32Array(lat.length), [nx, ny, nz] = [5, 3, 3];
      for (let k = 0; k < nz; k++) for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) { const a = ((k * ny + j) * nx + i) * 3, b = (((nz - 1 - k) * ny + j) * nx + i) * 3; out[b] = lat[a]!; out[b + 1] = lat[a + 1]!; out[b + 2] = -lat[a + 2]!; }
      for (const m of meshes) {
        const key = (look === vis.dam ? 'd:' : look === vis.lod ? 'l:' : 'f:') + id + ':' + m.uniqueId, have = vis.dents.get(key);
        if (have && Math.abs(have.sum - sum) < 1e-4) continue;
        let cage = have?.cage;
        if (!cage) {
          m.makeGeometryUnique(); m.refreshBoundingInfo(true);
          const bb = m.getBoundingInfo().boundingBox, mn = bb.minimum, mx = bb.maximum;
          cage = new DentCage(m as never, { size: [Math.max(0.05, mx.x - mn.x), Math.max(0.05, mx.y - mn.y), Math.max(0.05, mx.z - mn.z)], center: [(mn.x + mx.x) / 2, (mn.y + mx.y) / 2, (mn.z + mx.z) / 2] });
        }
        cage.apply(out); vis.dents.set(key, { cage, sum });
      }
    }
  }
  /** the one drawn mesh of a part (a node by its name: the first mesh under it); parts that are only meshes of the body are not dented */
  private partMeshes(look: Look, id: string): BABYLON.Mesh[] {
    const n = look.nodes.get(id); if (!n) return [];
    const own = n instanceof BABYLON.Mesh && n.getTotalVertices() > 0 ? [n] : [];
    return [...own, ...n.getChildMeshes(true).filter((m): m is BABYLON.Mesh => m instanceof BABYLON.Mesh && m.getTotalVertices() > 0 && !/Glass/.test(m.name))];
  }

  // ---- debris: parts of cars, props flying, the jumper, fragments ----
  private debrisFrame(list: Debris[]) {
    const live = new Set<number>();
    for (const d of list) {
      live.add(d.id);
      const prop = this.props.get(d.ref) ?? this.captureProp(d.ref);
      if (prop) { this.moveProp(prop, d); continue; }
      let n = this.debris.get(d.id);
      if (!n) { n = this.makeDebris(d); this.debris.set(d.id, n); }
      n.position.set(d.pos[0], d.pos[1], d.pos[2]);
      (n.rotationQuaternion ?? (n.rotationQuaternion = BABYLON.Quaternion.Identity())).set(d.rot[0], d.rot[1], d.rot[2], d.rot[3]);
    }
    for (const [id, n] of this.debris) if (!live.has(id)) { n.dispose(); this.debris.delete(id); }
  }
  private makeDebris(d: Debris): BABYLON.TransformNode | BABYLON.Mesh {
    const pivot = new BABYLON.TransformNode('debris' + d.id, this.scene); pivot.rotationQuaternion = BABYLON.Quaternion.Identity();
    const vis = d.node ? this.cars.get(d.ref) : undefined;
    const src = vis ? [vis.full, vis.lod, vis.dam].map((l) => l?.nodes.get(d.node!)).find((n) => !!n) : undefined;
    if (src) {
      const info = vis!.infoByName.get(d.node!), c = info ? [(info.min[0] + info.max[0]) / 2, (info.min[1] + info.max[1]) / 2, (info.min[2] + info.max[2]) / 2] : [0, 0, 0];
      const mirror = new BABYLON.TransformNode('m', this.scene); mirror.parent = pivot; mirror.scaling.set(1, 1, -1); mirror.position.set(-c[0]!, -c[1]!, -c[2]!);
      const copy = src.clone('copy', null, false)!; copy.parent = mirror; copy.setEnabled(true);
      for (const m of copy.getChildMeshes()) { m.isPickable = false; this.shadow?.addShadowCaster(m, false); }
      return pivot;
    }
    const m = BABYLON.MeshBuilder.CreateBox('piece' + d.id, { width: d.half[0] * 2, height: d.half[1] * 2, depth: d.half[2] * 2 }, this.scene);
    m.material = d.kind === 'matthew' ? this.cloth : this.metal; m.isPickable = false; m.parent = pivot; this.shadow?.addShadowCaster(m, false);
    return pivot;
  }
  private captureProp(id: string) {
    const node = this.propNodes.get(id) ?? this.stationNodes.get(id); if (!node) return null;
    node.computeWorldMatrix(true);
    const e = { node, w0: node.getWorldMatrix().clone(), moved: false };
    this.props.set(id, e); return e;
  }
  private moveProp(p: { node: BABYLON.TransformNode; w0: BABYLON.Matrix; moved: boolean }, d: Debris) {
    // the thing at its start (world matrix w0), carried to where the sim has its box: about the box centre at rest, turned by d.rot, moved to d.pos
    const base = this.propBase.get(d.ref); if (!base) return;
    const R = new BABYLON.Matrix(); new BABYLON.Quaternion(d.rot[0], d.rot[1], d.rot[2], d.rot[3]).toRotationMatrix(R);
    const D = BABYLON.Matrix.Translation(-base[0], -base[1], -base[2]).multiply(R).multiply(BABYLON.Matrix.Translation(d.pos[0], d.pos[1], d.pos[2]));
    p.node.freezeWorldMatrix(p.w0.multiply(D)); p.moved = true;
  }
  private propBase = new Map<string, V3>();
  private propsFrame(take: Take) {
    for (const pr of take.scene.sim.props as Prop[]) {
      if (!this.propBase.has(pr.id)) { const b = pr.def.box; this.propBase.set(pr.id, [(b.min[0] + b.max[0]) / 2, b.min[1] + (b.max[1] - b.min[1]) / 2, (b.min[2] + b.max[2]) / 2]); }
      if (pr.state === 'gone') { const e = this.props.get(pr.id) ?? this.captureProp(pr.id); if (e) e.node.setEnabled(false); }
    }
  }

  // ---- fire, smoke, blasts ----
  private events(take: Take) {
    const q = this.eventQueue; this.eventQueue = [];
    for (const e of q) {
      if (e.type === 'blast') {
        const name = e.what === 'tanker' ? 'blast.fuel-air' : e.what === 'propane' || e.what === 'pump' ? 'blast.vessel' : 'blast.he-ground';
        this.spawn(name, e.at, { tnt: Math.max(0.5, e.tnt) });
        this.shake = Math.max(this.shake, Math.min(1, Math.log10(1 + e.tnt) / 2.2) * Math.max(0.05, 1 - Math.hypot(e.at[0] - take.scene.player.veh.pos[0], e.at[2] - take.scene.player.veh.pos[2]) / 160));
      } else if (e.type === 'collapse') this.spawn('dust.collapse', e.at, {});
      else if (e.type === 'ignite' || e.type === 'burning') this.fire(e.id, e.what, e.at, e.power);
      else if (e.type === 'out') this.stopFire(e.id);
      else if (e.type === 'impact' && e.speed > 6) this.spawn('electric.short-circuit', e.at, {});
    }
  }
  private spawn(name: string, at: V3, params: Record<string, number>) { if (!this.vfx.has(name)) { if (!this.warned.has(name)) { console.warn('vfx not registered', name); this.warned.add(name); } return null; } try { return this.vfx.spawn(name, { at, params } as never); } catch (e) { if (!this.warned.has(name)) { console.warn('vfx spawn', name, e); this.warned.add(name); } return null; } }
  private warned = new Set<string>();
  private fire(id: string, what: string, at: V3, power: number) {
    const cur = this.flames.get(id), heat = Math.max(2e5, power);
    if (!cur) { const kind = what === 'tanker' ? 'fire.vehicle' : what === 'car' ? 'fire.vehicle' : 'fire.vehicle'; const h = this.spawn(kind, [at[0], Math.max(0, at[1] - 0.3), at[2]], { heat }); if (h) this.flames.set(id, { handle: h, heat, kind }); return; }
    if (Math.abs(heat - cur.heat) / cur.heat > 0.15) { this.vfx.setParam(cur.handle as never, 'heat', heat); cur.heat = heat; }
  }
  private stopFire(id: string) { const f = this.flames.get(id); if (f) { this.vfx.stop(f.handle as never); this.flames.delete(id); } }
  private flameFrame(_take: Take) { /* flames follow their store through the 'burning' events (position at each event) */ }

  // ---- the camera ----
  /** the camera of this phase: the cab by default; during a verdict the set camera that saw the take's big moment */
  setView(v: ViewCamera) { this.view = v; this.camInit = false; }
  private placeCamera(take: Take, dt: number, head: { yaw: number; pitch: number; back: boolean }) {
    const cam = this.camera;
    this.shake = Math.max(0, this.shake - dt * 0.8);
    if (this.view.mode === 'set' && this.view.set) {
      const s = this.view.set;
      cam.position.set(s.pos[0], s.pos[1], s.pos[2]); cam.fov = s.fov;
      const f = new BABYLON.Vector3(s.target[0] - s.pos[0], s.target[1] - s.pos[1], s.target[2] - s.pos[2]).normalize();
      // follow the action a little: aim at the player's car or the villain's, whichever the sim says matters, within the frame
      const t = take.scene.vincent.veh.pos, p = take.scene.player.veh.pos, near = Math.abs(t[0] - s.target[0]) < Math.abs(p[0] - s.target[0]) ? t : p;
      const aim = new BABYLON.Vector3(near[0] - s.pos[0], near[1] + 1 - s.pos[1], near[2] - s.pos[2]);
      const want = aim.length() > 4 && aim.normalize().dot(f) > 0.8 ? aim : f;
      cam.rotationQuaternion = lookQuat(want, BABYLON.Vector3.Up()); return;
    }
    const car = take.scene.player, v = car.veh;
    const driver = v.toWorld([0.25, 1.12, 0.38]);
    cam.fov = 1.05; cam.minZ = 0.1;
    const fwd = qRot(v.rot, [1, 0, 0]), up = qRot(v.rot, [0, 1, 0]);
    // the body's attitude, smoothed, with the roll and the pitch toned down (a head does not follow every bump)
    const flat = Math.atan2(fwd[2], fwd[0]);
    const target = BABYLON.Quaternion.FromLookDirectionLH(new BABYLON.Vector3(Math.cos(flat), 0, Math.sin(flat)), BABYLON.Vector3.Up());
    const bodyQ = lookQuat(new BABYLON.Vector3(fwd[0], fwd[1] * 0.7, fwd[2]).normalize(), new BABYLON.Vector3(up[0] * 0.4, 1, up[2] * 0.4).normalize());
    void target;
    if (!this.camInit) { this.camQ.copyFrom(bodyQ); this.camInit = true; } else BABYLON.Quaternion.SlerpToRef(this.camQ, bodyQ, Math.min(1, dt * 14), this.camQ);
    this.back += ((head.back ? Math.PI : 0) - this.back) * Math.min(1, dt * 12);
    const q = this.camQ.multiply(BABYLON.Quaternion.RotationYawPitchRoll(head.yaw + this.back, -head.pitch, 0));
    cam.rotationQuaternion = q;
    const sh = this.shake * 0.05;
    cam.position.set(driver[0] + (Math.random() - 0.5) * sh, driver[1] + (Math.random() - 0.5) * sh, driver[2] + (Math.random() - 0.5) * sh);
  }
  /** the set camera that saw the best moment of the take, for the verdict */
  bestSetCamera(take: Take): SetCamera {
    const items = [...take.spec.items].filter((i) => i.camera).sort((a, b) => b.points - a.points);
    const id = items[0]?.camera;
    return SET_CAMERAS.find((c) => c.id === id) ?? SET_CAMERAS[0]!;
  }
  dispose() { this.vfxView.dispose?.(); }
  get stats() { return { cars: this.cars.size, fx: this.vfx.count, particles: this.vfx.particles, flames: this.flames.size }; }
}

/** the camera orientation for a forward and an up (left-handed, as the scene) */
function lookQuat(forward: BABYLON.Vector3, up: BABYLON.Vector3): BABYLON.Quaternion {
  const z = forward.normalize(), x = BABYLON.Vector3.Cross(up, z).normalize(), y = BABYLON.Vector3.Cross(z, x);
  const m = new BABYLON.Matrix(); BABYLON.Matrix.FromXYZAxesToRef(x, y, z, m);
  return BABYLON.Quaternion.FromRotationMatrix(m);
}
