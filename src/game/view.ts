// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// The picture of scene 1: the sim's cars, props and debris drawn with the art's models in the Babylon scene of the set; fire, smoke and blasts from the engine's vfx; the first-person camera of the police cab and the set cameras.
// VIEW FILE: it reads the sim and never writes to it.
import { VfxSystem, VfxBabylonView, FULL_CATALOG } from '@ferret/vfx';
import { FxDirector } from './fx';
import { qRot } from '@ferret/destruction/vehicle';
import { DentCage } from '@ferret/destruction/view-dents';
import { ShardView, type MeshData, type ShardHost } from '@ferret/destruction/view-shards';
import type { DebrisPiece } from '@ferret/destruction/debris';
import { CAR_KINDS, SET_CAMERAS, type KindId, type SetCamera } from './config';
import type { Take } from './take';
import { POLICE_CAB } from './carspec';
import { assignPaint, paintLook, whitePaint, paintOf, preparePaintInstances, paintInstance, PAINTED } from './paint';
import type { Car, Debris, SimEvent, Prop } from './sim';
import type { NodeInfo } from '@ferret/destruction/autoparts';
import { BabylonBackend, Perspective, PerspectiveService, type PerspectiveLevel } from '@ferret/perspective';
import type { Entity, World } from '@ferret/core';

type V3 = [number, number, number];
const split = (url: string) => { const i = url.lastIndexOf('/'); return [url.slice(0, i + 1), url.slice(i + 1)] as const; };
const upright = (root: BABYLON.TransformNode | BABYLON.AbstractMesh | null | undefined) => { if (root) (root as BABYLON.TransformNode).rotationQuaternion = BABYLON.Quaternion.Identity(); };

interface Pack { full?: BABYLON.AssetContainer; lod?: BABYLON.AssetContainer; damaged?: BABYLON.AssetContainer }
interface WheelVis { node: BABYLON.TransformNode; mesh: BABYLON.TransformNode | null; restN: BABYLON.Quaternion; restM: BABYLON.Quaternion; steer: boolean; angle: number }
interface Look { root: BABYLON.TransformNode; nodes: Map<string, BABYLON.TransformNode>; wheels: Map<string, WheelVis> }
interface DentVis { cage: DentCage; sum: number }
interface CarVis { dents: Map<string, DentVis>; frameNo: number; car: Car; root: BABYLON.TransformNode; full: Look | null; lod: Look | null; dam: Look | null; hidden: Set<string>; shown: 0 | 1; near: boolean; infoByName: Map<string, NodeInfo>; spin: Map<string, number>; damSrc: BABYLON.AssetContainer | null; entity: Entity | null; fullRep: { setState(s: 'on', mix: number): void } | null; reduced: BABYLON.InstancedMesh[] }
/** the rungs of a far car by its size on the screen (pixels of the bounding sphere): its own parts, the kind's reduced model, a point */
const CAR_LADDER: PerspectiveLevel[] = [{ kind: 'full', minPx: 300 }, { kind: 'mesh', minPx: 4 }, { kind: 'point', minPx: 0 }];
/** a standing car (parked, the tanker): its own parts and the merged model are the same geometry, so its parts are made only when it is touched */
const STILL_LADDER: PerspectiveLevel[] = [{ kind: 'mesh', minPx: 4 }, { kind: 'point', minPx: 0 }];

export interface ViewCamera { mode: 'cab' | 'set'; set?: SetCamera }
/** the side of a car a hit came in on (car frame: front +x, left +z, top +y) */
export type HitSide = 'front' | 'rear' | 'left' | 'right' | 'top';
const HIT_SIDES: HitSide[] = ['front', 'rear', 'left', 'right', 'top'];

export class GameView {
  readonly vfx = new VfxSystem();
  readonly fx: FxDirector;
  private skyLight: BABYLON.HemisphericLight | null = null; private skyBase = 1; private flashing = false; private skyColor = BABYLON.Color3.White();
  private vfxView!: VfxBabylonView;
  private packs = new Map<KindId, Pack>();
  private cars = new Map<string, CarVis>();
  private debris = new Map<number, BABYLON.TransformNode | BABYLON.Mesh>();
  private props = new Map<string, { node: BABYLON.TransformNode; w0: BABYLON.Matrix; moved: boolean }>();
  private infos: Partial<Record<KindId, NodeInfo[]>> = {};
  private shadow: BABYLON.ShadowGenerator | null;
  private lookYaw = 0; private lookPitch = 0; private back = 0;
  private camQ = BABYLON.Quaternion.Identity(); private camInit = false;
  private metal: BABYLON.PBRMaterial; private cloth: BABYLON.PBRMaterial;
  private eventQueue: SimEvent[] = [];
  /** the pieces of the module's breaks (shards of glass, splinters, chips, torn bits of sheet) drawn as instances; their fall and fade are the module's (ds.advance) */
  private shards: { view: ShardView; pieces: DebrisPiece[]; rot: BABYLON.Quaternion[]; ang: V3[]; ds: { pieceAt(p: DebrisPiece): [number, number, number] | null } }[] = [];
  private unlisten: (() => void) | null = null;
  private pieceMats = new Map<string, BABYLON.Material>();
  shardStats = { sets: 0, pieces: 0, prototypes: 0 };
  view: ViewCamera = { mode: 'cab' };

  constructor(readonly scene: BABYLON.Scene, readonly camera: BABYLON.UniversalCamera, private propNodes: Map<string, BABYLON.TransformNode>, private stationNodes: Map<string, BABYLON.TransformNode>, shadow: BABYLON.ShadowGenerator | null = null) {
    this.vfx.registerAll(FULL_CATALOG as never);
    this.fx = new FxDirector(this.vfx);
    this.vfxView = new VfxBabylonView(scene, this.vfx, camera, { soft: false /* soft particles need a depth pass of the whole scene every frame (about a second a frame here) */, supports: ['particles', 'impostor', 'dot'], parts: { maxLights: 6, groundHeight: () => 0, candelaScale: 1 / 40000, maxLightIntensity: 0.55, steadyLights: true /* the six effect lights stay on (dark while unused): a light switched on or off changed every lit material's shader, and while the street's hundreds of shaders recompiled nothing of the street or the cars was drawn */ } } as never);
    const hemi = scene.lights.find((l) => l instanceof BABYLON.HemisphericLight) as BABYLON.HemisphericLight | undefined;
    if (hemi) { this.skyLight = hemi; this.skyBase = hemi.intensity; this.skyColor = hemi.diffuse.clone(); }
    // the effects' lights (up to six) must reach the street's materials: the default of a material is four lights in all
    const lights = (m: BABYLON.Material) => { const a = m as unknown as { maxSimultaneousLights?: number }; if (typeof a.maxSimultaneousLights === 'number' && a.maxSimultaneousLights < 8) a.maxSimultaneousLights = 8; };
    scene.materials.forEach(lights); scene.onNewMaterialAddedObservable.add(lights);
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
      // the art's cab materials are near black (albedo 0.00-0.09); a cab in daylight is lit by the windows: a fill (emissive) per material, so that pillars, seats and the headliner can be seen
      const fill: [RegExp, number, number, number][] = [[/headliner/i, 0.30, 0.32, 0.36], [/^M_interior/i, 0.15, 0.15, 0.19], [/carpet/i, 0.09, 0.09, 0.11], [/dash/i, 0.12, 0.12, 0.14], [/seat/i, 0.14, 0.13, 0.12], [/^M_seal|^M_gap|^M_black|^M_well|^M_under/i, 0.07, 0.07, 0.08]];
      for (const c of [pack.full, pack.lod, pack.damaged]) for (const m of c?.materials ?? []) if (m instanceof BABYLON.PBRMaterial && (k === 'police' || k === 'corvette')) { const f = fill.find((x) => x[0].test(m.name)); if (f) { m.emissiveColor = new BABYLON.Color3(f[1], f[2], f[3]); m.emissiveIntensity = 1; } }
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
    paintLook(root, this.paints.get(parent.name.replace(/^car:/, '')));   // the car's own body colour (paint.ts); the parent is the car's root 'car:<id>'
    return { root, nodes, wheels };
  }

  private makeCar(car: Car): CarVis {
    const root = new BABYLON.TransformNode('car:' + car.id, this.scene), pack = this.packs.get(car.kind) ?? {};
    root.rotationQuaternion = BABYLON.Quaternion.Identity();
    const infoByName = new Map((this.infos[car.kind] ?? []).map((n) => [n.name, n] as const));
    // the player's car and Vincent's are always the full model; every other car is drawn by the engine's perspective module while nobody has touched it
    const ladderd = !!this.persp && car.role !== 'player' && car.role !== 'vincent' && !!this.reducedOf(car.kind);
    const own = car.role === 'player' ? pack.full : pack.lod ?? pack.full;   // every car but the player's is drawn from its reduced file (same parts, a quarter of the triangles)
    const full = ladderd && car.role !== 'traffic' ? null : this.instantiate(own, root), lod = car.role === 'player' && pack.lod ? this.instantiate(pack.lod, root) : null;
    const vis: CarVis = { car, root, full, lod, dam: null, hidden: new Set(), shown: 0, near: true, infoByName, spin: new Map(), dents: new Map(), frameNo: 0, damSrc: null, entity: null, fullRep: null, reduced: [] };
    if (ladderd) this.ladder(vis);
    return vis;
  }

  // ---- far cars through @ferret/perspective: the full model near (made when first needed), the kind's reduced model (merged, an instance per car) farther, a point far ----
  private persp: { service: PerspectiveService; backend: BabylonBackend; world: World } | null = null;
  /** the world whose frame runs the perspective service (play.ts gives it once); without it every car is drawn in full */
  usePerspective(world: World) {
    const service = world.hasService('perspective') ? world.service<PerspectiveService>('perspective') : world.addService(new PerspectiveService({ backend: new BabylonBackend(this.scene), budget: { maxFull: 10 } }));
    this.persp = { service, backend: service.backend as BabylonBackend, world };
  }
  private reduced = new Map<KindId, { meshes: BABYLON.Mesh[]; radius: number } | null>();
  /** the palette index of each car's body colour in the current take (paint.ts) */
  private paints = new Map<string, number>();
  /** the kind's reduced model (its *_lod1, cut to a quarter of the triangles by the build) as merged meshes in the car's frame: one per set of vertex attributes, a material per part kept */
  private reducedOf(kind: KindId): { meshes: BABYLON.Mesh[]; radius: number } | null {
    if (this.reduced.has(kind)) return this.reduced.get(kind)!;
    const pack = this.packs.get(kind), src = pack?.lod ?? pack?.full;
    if (!src) { this.reduced.set(kind, null); return null; }
    const inst = src.instantiateModelsToScene((n) => 'reduced-src:' + n, false, { doNotInstantiate: true });
    const root = inst.rootNodes[0] as BABYLON.TransformNode;
    upright(root); root.position.setAll(0); root.computeWorldMatrix(true);
    const groups = new Map<string, BABYLON.Mesh[]>();
    for (const m of root.getChildMeshes(false)) {
      if (!(m instanceof BABYLON.Mesh) || !m.material || m.getTotalVertices() === 0) continue;
      m.makeGeometryUnique(); m.setParent(null); m.bakeCurrentTransformIntoVertices();
      const sig = (PAINTED.includes(kind) && paintOf(m.material) ? 'paint|' : '') + (m.getVerticesDataKinds() ?? []).slice().sort().join(',');   // the body paint merged apart: it takes its colour per instance
      (groups.get(sig) ?? groups.set(sig, []).get(sig)!).push(m);
    }
    root.dispose(false, false);
    const meshes: BABYLON.Mesh[] = []; let radius = 0;
    for (const [sig, list] of groups) {
      let out: BABYLON.Mesh[] = list;
      const paint = sig.startsWith('paint|') ? whitePaint(list[0]!.material!) : null;
      try { const merged = BABYLON.Mesh.MergeMeshes(list, true, true, undefined, false, !paint); if (merged) out = [merged]; } catch { out = list; }
      if (paint) for (const m of out) { m.material = paint; preparePaintInstances(m); }
      for (const m of out) {
        m.name = `reduced:${kind}`; m.isPickable = false; m.receiveShadows = true;
        m.refreshBoundingInfo(); const bs = m.getBoundingInfo().boundingSphere; radius = Math.max(radius, bs.radius + bs.center.length());
        m.position.y = -10000;   // kept enabled (the instances draw from it) but out of sight, far under the ground
        meshes.push(m);
      }
    }
    const r = { meshes, radius }; this.reduced.set(kind, r); return r;
  }
  private ladder(vis: CarVis) {
    const P = this.persp!, red = this.reducedOf(vis.car.kind)!, pack = this.packs.get(vis.car.kind) ?? {};
    vis.reduced = red.meshes.map((m) => { const i = m.createInstance(`car-reduced:${vis.car.id}`); paintInstance(i, this.paints.get(vis.car.id)); i.parent = vis.root; i.position.setAll(0); i.isPickable = false; this.shadow?.addShadowCaster(i, false); return i; });
    vis.root.computeWorldMatrix(true);
    const e = P.world.spawn('car-' + vis.car.id, { node: vis.root, tags: ['car'] });
    if (vis.full) vis.fullRep = P.backend.represent(e, 'full', vis.full.root);
    void pack;
    P.backend.represent(e, 'mesh', vis.reduced);
    e.add(Perspective, { ladder: vis.full ? CAR_LADDER : STILL_LADDER, radius: red.radius, color: [0.18, 0.18, 0.19], fade: 0 });   // switched at once: the dithered cross-fade compiles a shader variant of every material of the car the first time, a stall while driving
    vis.entity = e;
  }
  /** a touched car leaves the module for good: its own parts from now on (the dents and the parts that come off need them).
   *  The entity is only taken out of the world, never destroyed: Entity.destroy() disposes its node, and that node is the car's own root (every model of the car is under it).
   *  The module's rungs switch meshes off one by one (isVisible and enabled per mesh); the full rung is put back 'on', which gives each mesh back what it had. */
  private unladder(vis: CarVis) {
    const e = vis.entity;
    if (e) {
      const per = e.get(Perspective); if (per) e.remove(per);
      vis.fullRep?.setState('on', 1);
      e.world.removeEntity(e);
    }
    vis.entity = null; vis.fullRep = null;
    for (const i of vis.reduced) i.dispose(); vis.reduced = [];
    if (!vis.full) { const pk = this.packs.get(vis.car.kind); vis.full = this.instantiate(pk?.lod ?? pk?.full, vis.root); }
    if (vis.full) vis.full.root.setEnabled(true);
  }

  // ---- wrecked models: the place where pre-baked wrecked variants plug in ----
  /** the energy of the hits each car took, by the side of the car they came in on (J); read from the sim's impact events */
  private hitSides = new Map<string, Record<HitSide, number>>();
  /** wrecked variants of a kind by the side that took the hits and the least damage (Car.damage, 0..1 and more) they are for; none are registered yet */
  private variants = new Map<KindId, { side: HitSide; minDamage: number; model: BABYLON.AssetContainer }[]>();
  /** give a kind a pre-baked wrecked variant: shown on a wrecked car of the kind whose hits came mostly on `side`, once its damage is at least `minDamage` (the variant with the highest such threshold wins) */
  registerDamaged(kind: KindId, side: HitSide, minDamage: number, model: BABYLON.AssetContainer) {
    const list = this.variants.get(kind) ?? []; list.push({ side, minDamage, model }); this.variants.set(kind, list);
  }
  /** the side of the car's hits so far with the most energy, and the energies by side (for the checks and for choosing a variant) */
  hitSideOf(carId: string): { side: HitSide | null; energy: Record<HitSide, number> } {
    const e = this.hitSides.get(carId) ?? { front: 0, rear: 0, left: 0, right: 0, top: 0 };
    let side: HitSide | null = null, best = 0;
    for (const s of HIT_SIDES) if (e[s] > best) { best = e[s]; side = s; }
    return { side, energy: { ...e } };
  }
  /** the wrecked model of a car: a registered variant for its side and damage when there is one, else the kind's single *_damaged model */
  private damagedModel(c: Car): BABYLON.AssetContainer | undefined {
    const list = this.variants.get(c.kind), side = list?.length ? this.hitSideOf(c.id).side : null;
    if (list && side) { let pick: { minDamage: number; model: BABYLON.AssetContainer } | null = null; for (const v of list) if (v.side === side && c.damage >= v.minDamage && (!pick || v.minDamage > pick.minDamage)) pick = v; if (pick) return pick.model; }
    return this.packs.get(c.kind)?.damaged;
  }
  private noteHit(car: Car, at: V3, energy: number) {
    const l = car.veh.toLocal(at), h = car.veh.hull(), hx = h.size[0] / 2, hy = h.size[1] / 2, hz = h.size[2] / 2;
    const dx = (l[0] - h.center[0]) / hx, dy = (l[1] - h.center[1]) / hy, dz = (l[2] - h.center[2]) / hz;
    // the car frame: +x forward, +y up, +z to the left
    const side: HitSide = dy > Math.max(Math.abs(dx), Math.abs(dz)) ? 'top' : Math.abs(dx) >= Math.abs(dz) ? (dx > 0 ? 'front' : 'rear') : (dz > 0 ? 'left' : 'right');
    const e = this.hitSides.get(car.id) ?? { front: 0, rear: 0, left: 0, right: 0, top: 0 };
    e[side] += energy; this.hitSides.set(car.id, e);
  }

  /** a new take: the old cars and effects go, the new sim's cars appear */
  startTake(take: Take) {
    for (const v of this.cars.values()) { v.entity?.destroy(); v.root.dispose(); }
    this.cars.clear(); this.hitSides.clear();
    for (const d of this.debris.values()) d.dispose();
    this.debris.clear();
    for (const [, p] of this.props) { p.node.unfreezeWorldMatrix(); p.node.setEnabled(true); if (p.moved) { p.node.freezeWorldMatrix(p.w0); } p.moved = false; }
    this.fx.reset();
    for (const sh of this.shards) sh.view.dispose();
    this.shards = []; this.unlisten?.();
    const ds = take.scene.sim.ds;
    this.unlisten = ds.listen((name, p) => { if (name === 'destruction:hit') this.addShards(ds, p); });
    this.paints = assignPaint(take.scene.sim.cars, take.scene.seed);
    for (const car of take.scene.sim.cars) this.cars.set(car.id, this.makeCar(car));
    this.lookYaw = this.lookPitch = 0; this.camInit = false;
    if (!this.culled) { this.culled = true; this.cullSmall(); }
  }

  /** small static things (the pumps' nozzles and hoses, bins, news boxes, signs, lamps) are not drawn where they are under about three pixels: a draw call each costs the frame far more than they show */
  private culled = false;
  private cullSmall() {
    const k = 900 / (2 * Math.tan(this.camera.fov / 2)) / 3;   // the distance at which one metre of size is three pixels high
    for (const m of this.scene.meshes) {
      if (!(m instanceof BABYLON.Mesh) || m.hasThinInstances || m.skeleton || m.getTotalVertices() === 0) continue;
      let r: BABYLON.Node | null = m; while (r?.parent) r = r.parent;
      if (/^(car:|reduced|terrain|skydome|scatter|merged|surround)/.test(r?.name ?? '') || /^(reduced|merged)/.test(m.name)) continue;
      const size = m.getBoundingInfo().boundingSphere.radiusWorld * 2;
      if (size <= 0 || size > 4) continue;
      m.addLODLevel(Math.max(60, size * k), null);
    }
  }

  // ---- the frame ----
  /** one frame: place everything from the sim, run the effects, move the camera. `look` is the free look of the head (radians per second of input, already integrated by the caller) */
  frame(take: Take, dt: number, head: { yaw: number; pitch: number; back: boolean }) {
    const sim = take.scene.sim, cam = this.camera.globalPosition;
    this.events(take);
    // cars
    for (const vis of this.cars.values()) this.placeCar(vis, dt, cam);
    this.debrisFrame(sim.debris);
    this.shardFrame(sim.ds, dt);
    this.propsFrame(take);
    this.fx.frame(take, dt, [cam.x, cam.y, cam.z]);
    // camera
    this.placeCamera(take, dt, head);
    const t0 = performance.now();
    this.vfxView.draw({ cameraPosition: [cam.x, cam.y, cam.z], fov: this.camera.fov, heightPx: this.scene.getEngine().getRenderHeight(), tier: 'high', dt, night: 0 } as never);
    this.fx.endFrame(performance.now() - t0);
    // the warm flash of a blast lights the whole street for a moment (the sky light, warmer and brighter)
    if (this.skyLight) {
      const f = this.fx.flashLevel(dt), L = this.skyLight;
      if (f > 0.002) { if (!this.flashing) { this.flashing = true; this.skyBase = L.intensity; this.skyColor.copyFrom(L.diffuse); } L.intensity = this.skyBase * (1 + f * 0.35); BABYLON.Color3.LerpToRef(this.skyColor, new BABYLON.Color3(1, 0.62, 0.34), Math.min(0.5, f * 0.8), L.diffuse); }
      else if (this.flashing) { this.flashing = false; L.intensity = this.skyBase; L.diffuse.copyFrom(this.skyColor); }
    }
  }
  push(evs: SimEvent[]) { for (const e of evs) this.eventQueue.push(e); }
  /** fixed steps of the effects (the caller runs this once per sim step) */
  stepFx(dt: number) { const t0 = this.fx.beginStep(); this.vfx.step(dt); this.fx.endStep(t0); }

  private placeCar(vis: CarVis, dt: number, cam: BABYLON.Vector3) {
    const c = vis.car, v = c.veh, p = v.toWorld([0, 0, 0]), q = v.rot;
    vis.root.position.set(p[0], p[1], p[2]);
    (vis.root.rotationQuaternion as BABYLON.Quaternion).set(q[0], q[1], q[2], q[3]);
    const d = Math.hypot(p[0] - cam.x, p[2] - cam.z);
    // a car under the perspective module: the module shows its rung; once touched it leaves the module and is drawn below like the player's
    if (vis.entity) {
      const intact = !(c.hitAt > -90 || c.damage > 0 || c.wrecked || c.shown !== 0 || v.bodies.length > 0);
      if (intact) return;
      this.unladder(vis);
    }
    const damSrc = c.shown === 1 ? this.damagedModel(c) : undefined, wantDam = !!damSrc;
    if (damSrc && vis.damSrc !== damSrc) {
      // the wrecked model (or another wrecked variant): parts that have already come off stay off on it too
      vis.dam?.root.dispose(); vis.dam = this.instantiate(damSrc, vis.root); vis.damSrc = damSrc;
      for (const k of [...vis.dents.keys()]) if (k.startsWith('d:')) vis.dents.delete(k);
      if (vis.dam) for (const id of vis.hidden) for (const n of [vis.dam.nodes.get(id), id.startsWith('Door_') ? vis.dam.nodes.get(id + '_shell') : undefined]) n?.setEnabled(false);
    }
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
  /** the material of a piece by what broke: glass is clear, wood brown, concrete grey, sheet metal dark */
  private pieceMat(id: string, part: string): BABYLON.Material {
    const key = /^Facade/.test(id) ? 'brick' : /glass|window|pane|booth/i.test(part) || /PhoneBooth/.test(id) ? 'glass' : /Bench|Sawhorse|Pole|ShopDoor|ShopSign/.test(id) && !/glass/i.test(part) ? 'wood' : /Planter/.test(id) ? 'concrete' : /Bin|Cone|NewsBox|TrashBags/.test(id) ? 'plastic' : 'metal';
    let m = this.pieceMats.get(key);
    if (!m) {
      const p = new BABYLON.PBRMaterial('piece-' + key, this.scene); p.metallic = 0; p.roughness = 0.6; p.backFaceCulling = false;
      if (key === 'glass') { p.albedoColor = new BABYLON.Color3(0.72, 0.85, 0.88); p.alpha = 0.55; p.roughness = 0.08; p.environmentIntensity = 1.2; }
      else if (key === 'wood') p.albedoColor = new BABYLON.Color3(0.36, 0.22, 0.1);
      else if (key === 'brick') p.albedoColor = new BABYLON.Color3(0.45, 0.2, 0.14);
      else if (key === 'concrete') p.albedoColor = new BABYLON.Color3(0.45, 0.44, 0.42);
      else if (key === 'plastic') p.albedoColor = new BABYLON.Color3(0.8, 0.35, 0.1);
      else { p.albedoColor = new BABYLON.Color3(0.22, 0.22, 0.24); p.metallic = 0.7; p.roughness = 0.45; }
      this.pieceMats.set(key, p); m = p;
    }
    return m;
  }
  private addShards(ds: unknown, p: { id: string; part: string; pieces: unknown[]; plan: { pieces: DebrisPiece[] } | null; origin: V3 }) {
    if (!p.plan || p.plan.pieces.length === 0) return;
    const mat = this.pieceMat(p.id, p.part), scene = this.scene, shadow = this.shadow;
    if (mat === this.pieceMats.get('glass')) this.fx.glass([p.origin[0], Math.max(0.4, p.origin[1]), p.origin[2]], /^Window/.test(p.id) ? 2.2 : /booth/i.test(p.id) ? 1.5 : 0.9);
    const host: ShardHost = {
      makeMesh: (name, data: MeshData) => {
        const m = new BABYLON.Mesh(name, scene); const vd = new BABYLON.VertexData();
        vd.positions = data.positions; vd.normals = data.normals; vd.indices = data.indices; vd.applyToMesh(m);
        m.material = mat; m.isPickable = false; m.setEnabled(false); m.alwaysSelectAsActiveMesh = true;
        return {
          createInstance: (n: string) => {
            const i = m.createInstance(n); i.isPickable = false; i.rotationQuaternion = BABYLON.Quaternion.Identity();
            return { position: i.position, scaling: i.scaling, setRotation: (x: number, y: number, z: number, w: number) => i.rotationQuaternion!.set(x, y, z, w), setEnabled: (on: boolean) => i.setEnabled(on), dispose: () => i.dispose() };
          },
          dispose: () => m.dispose(),
        };
      },
    };
    const pieces = p.plan.pieces, view = new ShardView(host, pieces.map((q) => q.spec), p.origin, 'shard' + this.shards.length);
    void shadow;
    this.shards.push({ view, pieces, rot: pieces.map(() => BABYLON.Quaternion.Identity()), ang: pieces.map((q) => [...q.spec.angular] as V3), ds: ds as never });
    this.shardStats.sets++; this.shardStats.pieces += pieces.length; this.shardStats.prototypes += view.stats.prototypes;
    if (this.shards.length > 160) this.shards.shift()!.view.dispose();
  }
  private shardFrame(_ds: unknown, dt: number) {
    for (let k = this.shards.length - 1; k >= 0; k--) {
      const sh = this.shards[k]!; let alive = 0;
      sh.pieces.forEach((q, i) => {
        if (q.gone) { sh.view.hide(i); return; }
        alive++;
        const at = sh.ds.pieceAt(q); if (!at) return;
        const w = sh.ang[i]!, wl = Math.hypot(w[0], w[1], w[2]);
        if (!q.sleeping && wl > 1e-6) {
          const dq = BABYLON.Quaternion.RotationAxis(new BABYLON.Vector3(w[0] / wl, w[1] / wl, w[2] / wl), wl * dt);
          sh.rot[i] = dq.multiply(sh.rot[i]!);
          if (at[1] <= 0.06) { w[0] *= 0.9; w[1] *= 0.9; w[2] *= 0.9; }
        }
        sh.view.place(i, at[0], at[1], at[2], [sh.rot[i]!.x, sh.rot[i]!.y, sh.rot[i]!.z, sh.rot[i]!.w]);
        sh.view.fade(i, q.scale);
      });
      if (alive === 0) { sh.view.dispose(); this.shards.splice(k, 1); }
    }
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
    const sim = take.scene.sim;
    for (const e of q) {
      if (e.type === 'impact') for (const id of [e.a, e.b]) { const c = sim.car(id); if (c) this.noteHit(c, e.at as V3, e.energy); }
      this.fx.handle(e, take);
    }
  }

  // ---- the camera ----
  /** the camera of this phase: the cab by default; during a verdict the set camera that saw the take's big moment */
  setView(v: ViewCamera) { this.view = v; this.camInit = false; }
  private placeCamera(take: Take, dt: number, head: { yaw: number; pitch: number; back: boolean }) {
    const cam = this.camera;
    const sk = this.fx.shake(dt, this.view.mode === 'set' ? 0.45 : 1);
    if (this.view.mode === 'set' && this.view.set) {
      const s = this.view.set;
      cam.position.set(s.pos[0] + sk.p[0], s.pos[1] + sk.p[1], s.pos[2] + sk.p[2]); cam.fov = s.fov;
      const f = new BABYLON.Vector3(s.target[0] - s.pos[0], s.target[1] - s.pos[1], s.target[2] - s.pos[2]).normalize();
      // follow the action a little: aim at the player's car or the villain's, whichever the sim says matters, within the frame
      const t = take.scene.vincent.veh.pos, p = take.scene.player.veh.pos, near = Math.abs(t[0] - s.target[0]) < Math.abs(p[0] - s.target[0]) ? t : p;
      const aim = new BABYLON.Vector3(near[0] - s.pos[0], near[1] + 1 - s.pos[1], near[2] - s.pos[2]);
      const want = f;
      cam.rotationQuaternion = lookQuat(want, BABYLON.Vector3.Up()).multiply(BABYLON.Quaternion.RotationYawPitchRoll(sk.r[0], sk.r[1], sk.r[2])); return;
    }
    const car = take.scene.player, v = car.veh;
    const driver = v.toWorld(POLICE_CAB.eye);   // the driver's eyes in the police cab (carspec.ts)
    cam.fov = 1.05; cam.minZ = 0.1;
    const fwd = qRot(v.rot, [1, 0, 0]), up = qRot(v.rot, [0, 1, 0]);
    // the body's attitude, smoothed, with the roll and the pitch toned down (a head does not follow every bump)
    const flat = Math.atan2(fwd[2], fwd[0]);
    const target = BABYLON.Quaternion.FromLookDirectionLH(new BABYLON.Vector3(Math.cos(flat), 0, Math.sin(flat)), BABYLON.Vector3.Up());
    const bodyQ = lookQuat(new BABYLON.Vector3(fwd[0], fwd[1] * 0.7, fwd[2]).normalize(), new BABYLON.Vector3(up[0] * 0.4, 1, up[2] * 0.4).normalize());
    void target;
    if (!this.camInit) { this.camQ.copyFrom(bodyQ); this.camInit = true; } else BABYLON.Quaternion.SlerpToRef(this.camQ, bodyQ, Math.min(1, dt * 14), this.camQ);
    this.back += ((head.back ? Math.PI : 0) - this.back) * Math.min(1, dt * 12);
    const q = this.camQ.multiply(BABYLON.Quaternion.RotationYawPitchRoll(head.yaw + this.back + sk.r[0], -head.pitch + sk.r[1], sk.r[2]));
    cam.rotationQuaternion = q;
    cam.position.set(driver[0] + sk.p[0], driver[1] + sk.p[1], driver[2] + sk.p[2]);
  }
  /** can a camera at `p` see the point `t` (no tree, post or building in the way)? one ray against the scene's meshes, the cars and the ground aside */
  private clearView(p: V3, t: V3, slack = 1.5): boolean {
    const o = new BABYLON.Vector3(...p), d = new BABYLON.Vector3(t[0] - p[0], t[1] - p[1], t[2] - p[2]), len = d.length(); if (len < 2) return true;
    const ray = new BABYLON.Ray(o, d.scale(1 / len), len);
    const hit = this.scene.pickWithRay(ray, (m) => m.isEnabled() && m.getTotalVertices() > 0 && !/terrain|chunk|sky|dome|^car:|piece|debris|surround/i.test(m.name) && !this.isCarMesh(m));
    return !hit?.hit || hit.distance > len - slack;
  }
  private isCarMesh(m: BABYLON.Node): boolean { for (let n: BABYLON.Node | null = m; n; n = n.parent) if (n.name.startsWith('car:') || n.name.startsWith('debris')) return true; return false; }
  /** the set camera for the verdict: the one that saw the best moment if it can see the action, else the nearest that can; each also from higher up (a crane); the ray test settles it */
  bestSetCamera(take: Take): SetCamera {
    const items = [...take.spec.items].filter((i) => i.camera).sort((a, b) => b.points - a.points);
    const focus: V3 = items[0]?.at ? [items[0].at[0], Math.max(1, items[0].at[1]), items[0].at[2]] : (() => { const p = take.scene.vincent.veh.pos; return [p[0], p[1] + 1, p[2]] as V3; })();
    const pref = items[0]?.camera, list: SetCamera[] = [];
    const ordered = [...SET_CAMERAS].sort((a, b) => (a.id === pref ? -1e9 : Math.hypot(a.pos[0] - focus[0], a.pos[2] - focus[2])) - (b.id === pref ? -1e9 : Math.hypot(b.pos[0] - focus[0], b.pos[2] - focus[2])));
    for (const c of ordered) for (const up of [0, 3, 7]) list.push({ ...c, pos: [c.pos[0], c.pos[1] + up, c.pos[2]] });
    // a frame is clean when the view is open to the action and to its sides (rays to five points across and one above it), and nothing stands in the first 8 m of the view cone (a trunk or post beside the lens)
    const score = (c: SetCamera): number => {
      const d = Math.hypot(c.pos[0] - focus[0], c.pos[2] - focus[2]); if (d <= 6 || d >= 330) return -1;
      const fx = (focus[0] - c.pos[0]) / d, fz = (focus[2] - c.pos[2]) / d, px = -fz, pz = fx; let ok = 0, n = 0;
      for (const o of [-4, -2, 0, 2, 4]) { n++; if (this.clearView(c.pos, [focus[0] + px * o, focus[1], focus[2] + pz * o])) ok++; }
      n++; if (this.clearView(c.pos, [focus[0], focus[1] + 2, focus[2]])) ok++;
      const half = c.fov * 0.5 * 1.3;
      for (const a of [-half, 0, half]) { n++; const ca = Math.cos(a), sa = Math.sin(a); if (this.clearView(c.pos, [c.pos[0] + (fx * ca - fz * sa) * 9, c.pos[1] + (focus[1] - c.pos[1]) / d * 9, c.pos[2] + (fx * sa + fz * ca) * 9], 0.5)) ok++; }
      return ok / n;
    };
    let best: SetCamera | null = null, bs = -1;
    for (const c of list) { const q = score(c); if (q >= 1) return { ...c, target: focus }; if (q > bs) { bs = q; best = c; } }
    if (best && bs > 0.5) return { ...best, target: focus };
    return { ...SET_CAMERAS[0]!, pos: [focus[0] - 30, 8, 14], target: focus };
  }
  dispose() { this.vfxView.dispose?.(); }
  get stats() { return { cars: this.cars.size, fx: this.vfx.count, particles: this.vfx.particles, flames: this.fx.stats.effects, fxMs: this.fx.stats.fxMs, drawMs: this.fx.stats.drawMs, level: this.fx.stats.level }; }
}

/** the camera orientation for a forward and an up (left-handed, as the scene) */
function lookQuat(forward: BABYLON.Vector3, up: BABYLON.Vector3): BABYLON.Quaternion {
  const z = forward.normalize(), x = BABYLON.Vector3.Cross(up, z).normalize(), y = BABYLON.Vector3.Cross(z, x);
  const m = new BABYLON.Matrix(); BABYLON.Matrix.FromXYZAxesToRef(x, y, z, m);
  return BABYLON.Quaternion.FromRotationMatrix(m);
}
