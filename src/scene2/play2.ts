// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import { createGame } from '@ferret/game';
import { FERRET_BUILD } from '@ferret/core';
import { detectLevelTier } from '@ferret/platform';
import { createSkyProbe } from '@ferret/levels';
import { SeaView } from '@dunkirk/sea';
import { BeachView } from '@dunkirk/beach';
import { MoleView } from '@dunkirk/mole';
import { SkyDome } from '@dunkirk/sky';
import { DuneView } from '@dunkirk/dunes';
import { LADDER, fogDensity, waveList, windNow, type Weather } from '@dunkirk/weather';
import { AssetCache, AssetStore, PersistentCache, detectBackend } from '@ferret/assets';
import { AssetLibrary, LevelService, RuntimeAssets, defaultLibraryUrl, installPackages } from '@ferret/levels';
import { SeaModel } from '@dunkirk/sea-model';
import { FleetView2, layoutFleet } from './fleet2';
import { CAGE, buildCage, cageMaterials } from './cage';
import { buildPost, buildRoad } from './base';
import { Grove, layoutGrove } from './grove';
import { BeachKit } from './beachkit';
import { FarCrowd } from '@dunkirk/far-crowd';
import { NearCrowd } from './near2';
import { People, crewPlan, layoutAshore, layoutAssault } from './people';
import { makePrisoners } from './prisoners';
import { captureFrames } from '@ferret/media';
import { CAGE_Z, MOLE, bed, deckHeight, tide, onMole } from './shore';

/**
 * Scene 2 of TAKE 37 (the secret base), the field. Stage 1: the beach, the sea with its surf and tide, the mole (250 m), the dunes, the weather ladder. The pieces are the
 * Dunkirk sample's (borrowed from Ferret; shore.ts is its shore with the mole 250 m long, a 600 m field and a steeper sea bed).
 * Address options: `?rung=N` (weather rung 0..5), `?lite=1`, `?t=SECONDS` (game clock, sets the tide and the waves), `?clean=1`.
 */
const $ = (id: string) => document.getElementById(id)!;
const DEG = Math.PI / 180;
type V3 = [number, number, number];
const q = new URLSearchParams(location.search);
const splash = {
  set(p: number, text: string) { const b = document.getElementById('splashbar'), t = document.getElementById('splashtxt'); if (b) b.style.width = Math.round(p * 100) + '%'; if (t) t.textContent = text; },
  hide() { const e = document.getElementById('splash'); if (e) { e.classList.add('gone'); setTimeout(() => e.remove(), 900); } },
};
function lookOf(w: Weather) {
  const h = w.haze, L = w.light;
  const top: V3 = [h[0] * 0.74, h[1] * 0.8, h[2] * 0.92], hor: V3 = [h[0], h[1], h[2]];
  return { top, hor, sunDir: [-0.35, -0.5, 0.45] as V3, sunColor: [1.0, 0.93, 0.8] as V3, L, fog: fogDensity(w.visibility) };
}

async function main() {
  { const v = document.getElementById('splashver'); if (v) v.textContent = String((globalThis as { __TAKE37_BUILD__?: string }).__TAKE37_BUILD__ ?? FERRET_BUILD); }
  splash.set(0.1, 'The field');
  const canvas = $('c') as HTMLCanvasElement;
  const game = createGame({ canvas, storageKey: 'take37-scene2', input: { actions: {}, bindings: {} }, touchControls: false });
  const { scene, engine } = game;
  const lite = (() => { const p = q.get('lite'); if (p) return p !== '0'; const c = detectLevelTier({ override: q.get('tier'), screen: game.platform.screen() }); return game.platform.kind === 'beroun' || c.tier !== 'desktop'; })();
  const weather = LADDER[Math.min(LADDER.length - 1, Math.max(0, +(q.get('rung') ?? 0)))];
  let clock = +(q.get('t') ?? 0), paused = false;
  const TIDE_PHASE = 0.9;

  scene.clearColor = new BABYLON.Color4(0.6, 0.62, 0.64, 1);
  scene.fogMode = BABYLON.Scene.FOGMODE_EXP2;
  const hemi = new BABYLON.HemisphericLight('sky', new BABYLON.Vector3(0.1, 1, 0.15), scene);
  const sun = new BABYLON.DirectionalLight('sun', new BABYLON.Vector3(-0.35, -0.5, 0.45).normalize(), scene);
  scene.imageProcessingConfiguration.toneMappingEnabled = true; scene.imageProcessingConfiguration.exposure = 1.0;
  const cam = new BABYLON.FreeCamera('cam', new BABYLON.Vector3(0, 2, -130), scene);
  cam.minZ = 0.3; cam.maxZ = 6000; cam.fov = 0.95; scene.activeCamera = cam;
  const skyDome = new SkyDome(scene);
  const sea = new SeaView(scene, { radius: 2600, rings: lite ? 110 : 170, sectors: lite ? 150 : 220 });
  sea.setReflection(createSkyProbe(scene, [skyDome.mesh], { size: 128, every: 30 }));
  const beach = new BeachView(scene, lite ? 2 : 4);
  const mole = new MoleView(scene);
  const dunes = new DuneView(scene, lite);

  const applyLook = () => {
    const w = weather, k = lookOf(w), wv = windNow(w, 0);
    sea.setWaves(waveList(w, 3).map(a => ({ wavelength: a.wavelength, amplitude: a.amplitude, steepness: a.steepness, direction: a.direction })));
    sea.setLook({ skyTop: k.top, skyHorizon: k.hor, sunDir: k.sunDir, sunColor: k.sunColor, light: k.L, fogColor: k.hor, fogDensity: k.fog, rain: w.rain });
    const gnd: V3 = [0.35 * (0.4 + 0.6 * k.L), 0.33 * (0.4 + 0.6 * k.L), 0.28 * (0.4 + 0.6 * k.L)];
    const amb: V3 = [k.hor[0] * 0.95, k.hor[1] * 0.95, k.hor[2] * 0.95];
    beach.setLook({ sunDir: k.sunDir, sunColor: k.sunColor.map(c => c * (1 - 0.6 * w.cover)) as V3, sky: amb, ground: gnd, light: k.L, fogColor: k.hor, fogDensity: k.fog, rain: w.rain });
    skyDome.setLook({ top: k.top, horizon: k.hor, sunDir: k.sunDir, sunColor: k.sunColor, cover: w.cover, light: k.L, wind: [Math.cos(235 * DEG) * wv, Math.sin(235 * DEG) * wv] });
    scene.clearColor = new BABYLON.Color4(k.hor[0], k.hor[1], k.hor[2], 1);
    scene.fogDensity = k.fog; scene.fogColor = new BABYLON.Color3(k.hor[0], k.hor[1], k.hor[2]);
    hemi.intensity = 0.55 + 0.5 * k.L; hemi.diffuse = new BABYLON.Color3(amb[0] * 1.2, amb[1] * 1.2, amb[2] * 1.2); hemi.groundColor = new BABYLON.Color3(...gnd);
    sun.intensity = (1 - 0.8 * w.cover) * 2.0 * k.L; sun.diffuse = new BABYLON.Color3(...k.sunColor);
  };
  applyLook();

  // ---- the library and the fleet (stage 2) ----
  splash.set(0.3, 'The fleet');
  const assets = new AssetCache(scene);
  const levels = game.world.addService(new LevelService());
  const mount = installPackages(levels, assets);
  const store = new AssetStore({ cache: new PersistentCache(await detectBackend()), base: location.href });
  const runtime = game.world.addService(new RuntimeAssets({ store, models: mount.assets, mount }));
  const tierChoice = detectLevelTier({ override: q.get('tier'), screen: game.platform.screen() });
  const lib = game.world.addService(new AssetLibrary({ store, mount, assets: runtime, policy: { allowUnsigned: true }, tier: tierChoice.tier }));
  await lib.open(q.get('lib') ?? defaultLibraryUrl());
  const seaModel = new SeaModel(waveList(weather, 3));
  const fleet = new FleetView2(scene, lib, game.world, seaModel, layoutFleet(+(q.get('seed') ?? 37)));
  // the cages on the mole (one in the middle, one at the end), the villain's post, the road, the grove
  const cageMats = cageMaterials(scene);
  const cages = (['middle', 'end'] as const).map(k => { const c = buildCage(scene, 'cage_' + k, cageMats); c.position.set(-0.2, deckHeight(CAGE_Z[k]), CAGE_Z[k]); return c; });
  const post = buildPost(scene);
  const road = buildRoad(scene, { x: post.gate.x + 1.5, z: post.gate.z });
  const grove = new Grove(scene, lib, layoutGrove());
  const groveBuilt = grove.build();
  // the beach's driftwood, wire, stores, tracks, abandoned lorry (beachkit.ts)
  const kit = new BeachKit(scene, lib, game.world, lite);
  const kitBuilt = kit.build();
  // ---- the people (stage 4): ~50 on the engine's Walkers; the rings of figures: full near the camera, the library's reduced ones next, baked pictures of the perspective ladder far ----
  splash.set(0.5, 'The people');
  const people = new People(scene, () => seaModel.level);
  people.setCrew(crewPlan([...fleet.plans.map(p => p.id), 'steamer']));
  fleet.onModel = (plan, node, meshes) => people.addCraft(plan.id, node, meshes, plan.model, plan.kind === 'destroyer' ? 1.4 : plan.kind === 'steamer' ? 1.1 : 0.6);
  const overLog: Array<{ craft: string; x: number; y: number; z: number; t: number }> = [];
  { const prev = people.decks.onOverboard; people.decks.onOverboard = s => { const v = fleet.views.reduce((b, w) => (Math.hypot(w.node.position.x - s.x, w.node.position.z - s.z) < Math.hypot(b.node.position.x - s.x, b.node.position.z - s.z) ? w : b)); overLog.push({ craft: v.plan.id, x: s.x, y: s.y, z: s.z, t: clock }); prev?.(s); }; }
  for (const p of [...layoutAshore(), ...layoutAssault(+(q.get('seed') ?? 37))]) people.add(p);
  const FULL = { 'tommy-1': 3, 'tommy-2': 2, 'tommy-3': 2, 'sailor-1': 2, 'sailor-4': 2 }, MID = { 'tommy-1': 5, 'tommy-2': 4, 'tommy-3': 4, 'sailor-1': 4, 'sailor-4': 3 };
  const near = new NearCrowd(scene, lib, FULL); near.maxActive = lite ? 8 : 11;
  const mid = new NearCrowd(scene, lib, MID, '-lod1'); mid.maxActive = 20;
  const far = new FarCrowd(scene, lib);
  const midBuilt = mid.build(3), farBuilt = far.build();
  void midBuilt.then(() => near.build(lite ? 2 : 3));
  const crowdBuilt = Promise.all([midBuilt, farBuilt]);
  // the prisoners (Arnold on his heels in the middle cage, Emily at the bars of the end cage)
  const prisoners = makePrisoners(scene, { middle: cages[0], end: cages[1] }, () => seaModel.level);
  const prisonersBuilt = Promise.all([prisoners.arnold.load(), prisoners.emily.load()]);
  const fleetBuilt = fleet.build((q.get('steamer') as 'end' | 'middle' | 'idle' | null) ?? 'end');

  // the observer camera of the stage (drag to look, W A S D, Q / E, Shift); the player's own controls are not part of the field
  const keys = new Set<string>();
  const fly = { p: [0, 1.8, -130] as V3, yaw: 0, pitch: 0, fov: 0.95, speed: 12 };
  const KEYMAP: Record<string, string> = { KeyW: 'w', KeyA: 'a', KeyS: 's', KeyD: 'd', KeyQ: 'q', KeyE: 'e', ShiftLeft: 'shift', ShiftRight: 'shift' };
  addEventListener('keydown', e => { const k = KEYMAP[e.code]; if (k) keys.add(k); });
  addEventListener('keyup', e => { const k = KEYMAP[e.code]; if (k) keys.delete(k); });
  addEventListener('blur', () => keys.clear());
  let drag: { x: number; y: number } | null = null;
  canvas.addEventListener('pointerdown', e => { drag = { x: e.clientX, y: e.clientY }; canvas.focus(); });
  addEventListener('pointermove', e => { if (!drag) return; if (e.buttons === 0) { drag = null; return; } fly.yaw += (e.clientX - drag.x) * 0.004; fly.pitch = Math.min(1.5, Math.max(-1.5, fly.pitch - (e.clientY - drag.y) * 0.004)); drag = { x: e.clientX, y: e.clientY }; });
  addEventListener('pointerup', () => { drag = null; });
  const floor = (x: number, z: number, level: number) => Math.max(bed(x, z), level + 0.6, onMole(x, z) ? deckHeight(z) : -1e9) + 1.6;

  /** one step of everything that lives (the clock, the camera, the sea, the fleet, the people, the world); drawing is separate so the recorder can step by 1/fps and draw */
  const step = (dt: number) => {
    if (!paused) clock += dt;
    const level = tide(clock, TIDE_PHASE); seaModel.level = level;
    const sp = (keys.has('shift') ? 4.5 : 1) * fly.speed * dt, cy = Math.cos(fly.yaw), sy = Math.sin(fly.yaw), cp = Math.cos(fly.pitch), spf = Math.sin(fly.pitch);
    const mv = (keys.has('w') ? 1 : 0) - (keys.has('s') ? 1 : 0), st = (keys.has('d') ? 1 : 0) - (keys.has('a') ? 1 : 0), ud = (keys.has('e') ? 1 : 0) - (keys.has('q') ? 1 : 0);
    const nx = fly.p[0] + (sy * cp * mv + cy * st) * sp, nz = fly.p[2] + (cy * cp * mv - sy * st) * sp, ny = fly.p[1] + (spf * mv + ud) * sp;
    fly.p = [nx, Math.max(ny, floor(nx, nz, level)), nz];
    cam.position.copyFromFloats(fly.p[0], fly.p[1], fly.p[2]);
    cam.setTarget(new BABYLON.Vector3(fly.p[0] + sy * cp, fly.p[1] + spf, fly.p[2] + cy * cp)); cam.fov = fly.fov;
    const c = cam.globalPosition;
    dunes.update(c); kit.update(c);
    skyDome.update(clock); sea.update(clock, level, c); beach.update(c, Math.min(2600, weather.visibility * 2.6 + 400)); beach.tick(c, level, clock);
    fleet.update(clock, paused ? 0 : dt);
    {
      const pdt = paused ? 0 : dt;
      people.update(pdt); prisoners.arnold.update(pdt); prisoners.emily.update(pdt);
      const look = cam.getForwardRay(1).direction, all = people.list;
      near.update(all, c, lite ? 25 : 35, look, dt);
      if (mid.slots.length) mid.update(all, c, 140, look, dt, id => near.owned.has(id));
      far.update(all, cam, 1500, s => near.owned.has(s.id) || mid.owned.has(s.id), cam.fov, engine.getRenderHeight(), weather.visibility);
    }
    game.world.advance(dt);
  };
  engine.runRenderLoop(() => { step(Math.min(0.1, engine.getDeltaTime() / 1000)); scene.render(); });

  // ---- the recording (the engine's captureFrames, frame by frame on simulated time into WebM): a walk from the player's start up the mole past both cages, over the fleet and back to the post ----
  interface Key { t: number; p: V3; look: V3; fov?: number }
  const WALK: Key[] = [
    { t: 0, p: [0, 1.8, -130], look: [0, 5, 60] }, { t: 4, p: [0, 1.8, -130], look: [0, 5, 60] },
    { t: 12, p: [0, 5.95, -40], look: [0, 5.5, 60] }, { t: 18, p: [0.8, 5.95, 20], look: [-0.2, 5.0, 55] },
    { t: 22, p: [2.3, 5.75, 45], look: [-0.2, 5.0, 55], fov: 0.75 }, { t: 27, p: [2.0, 5.55, 50], look: [-0.2, 4.9, 55], fov: 0.65 },
    { t: 33, p: [1.0, 5.95, 130], look: [0, 5.2, 175] }, { t: 36, p: [2.3, 5.75, 166], look: [-0.2, 5.0, 175], fov: 0.75 }, { t: 41, p: [2.0, 5.55, 168], look: [-0.2, 4.9, 175], fov: 0.65 },
    { t: 44, p: [0, 6.4, 172], look: [90, 3, 400] }, { t: 48, p: [0, 7, 172], look: [-200, 4, 360] }, { t: 52, p: [0, 7, 172], look: [-40, 3, 250] },
    { t: 58, p: [4, 9, 40], look: [-40, 3, -150] }, { t: 66, p: [-5, 6, -120], look: [-60, 4.5, -195] },
    { t: 72, p: [-35, 5.5, -170], look: [-64, 4.5, -198], fov: 0.9 }, { t: 78, p: [-48, 5, -190], look: [-70, 4, -196], fov: 0.9 },
  ];
  const camAt = (t: number): Key => {
    let i = 0; while (i < WALK.length - 2 && t > WALK[i + 1]!.t) i++;
    const a = WALK[i]!, b = WALK[i + 1]!, k = Math.min(1, Math.max(0, (t - a.t) / (b.t - a.t))), e = k * k * (3 - 2 * k), m = (x: V3, y: V3): V3 => [x[0] + (y[0] - x[0]) * e, x[1] + (y[1] - x[1]) * e, x[2] + (y[2] - x[2]) * e];
    return { t, p: m(a.p, b.p), look: m(a.look, b.look), fov: (a.fov ?? 0.95) + ((b.fov ?? 0.95) - (a.fov ?? 0.95)) * e };
  };
  const record = async (o: { seconds?: number; fps?: number; width?: number; height?: number; supersample?: number } = {}) => {
    paused = false;
    const cap = await captureFrames(engine, scene, null, {
      fps: o.fps ?? 24, seconds: o.seconds ?? WALK[WALK.length - 1]!.t, width: o.width ?? 1280, height: o.height ?? 720, supersample: o.supersample ?? 1, format: 'webm',
      advance: dt => step(dt), render: () => scene.render(),
      beforeFrame: (_i, t) => { const k = camAt(t); const d = [k.look[0] - k.p[0], k.look[1] - k.p[1], k.look[2] - k.p[2]]; fly.p = [k.p[0], k.p[1], k.p[2]]; fly.yaw = Math.atan2(d[0], d[2]); fly.pitch = Math.atan2(d[1], Math.hypot(d[0], d[2])); fly.fov = k.fov ?? 0.95; },
    });
    (globalThis as unknown as { __capture: Blob }).__capture = cap.blob!;
    return { frames: cap.frames, fps: cap.fps, width: cap.width, height: cap.height, mime: cap.mime, bytes: cap.blob!.size, durationMs: cap.durationMs };
  };
  (globalThis as unknown as { __scene2: unknown }).__scene2 = { record, overLog, kit, kitBuilt, scene, engine, cam, fleet, fleetBuilt, people, prisoners, near, mid, far, crowdBuilt, prisonersBuilt, cages, post, road, grove, groveBuilt, CAGE, beach, sea, mole, dunes, fly, MOLE, bed, tide,
    /** who stands in which cage, read off the scene (the shot tools write it into their report and fail when it is wrong) */
    identity: () => ({ arnold: { cage: cages.indexOf(prisoners.arnold.root.parent as BABYLON.TransformNode) === 0 ? 'middle' : 'end', file: prisoners.arnold.file }, emily: { cage: cages.indexOf(prisoners.emily.root.parent as BABYLON.TransformNode) === 1 ? 'end' : 'middle', file: prisoners.emily.file } }),
    seaLevel: () => seaModel.level, seaModel,
    setTime: (t: number) => { clock = t; }, pause: (p: boolean) => { paused = p; },
    free: (p: V3, t: V3, fov = 0.95) => { fly.p = [p[0], p[1], p[2]]; const d = [t[0] - p[0], t[1] - p[1], t[2] - p[2]]; fly.yaw = Math.atan2(d[0], d[2]); fly.pitch = Math.atan2(d[1], Math.hypot(d[0], d[2])); fly.fov = fov; },
    renderer: () => { try { const gl = (engine as unknown as { _gl: WebGLRenderingContext })._gl; const x = gl.getExtension('WEBGL_debug_renderer_info'); return x ? String(gl.getParameter(x.UNMASKED_RENDERER_WEBGL)) : String(gl.getParameter(gl.RENDERER)); } catch { return '?'; } } };
  Object.assign(globalThis, { ferretGame: game, ferretReady: true });
  splash.set(1, 'Ready');
  const warm = () => { if ((beach.settled && fleet.views.every(v => v.ready) && grove.meshes.length > 0 && kit.ready && people.decks.waiting === 0 && mid.ready > 0 && far.ready > 0 && prisoners.arnold.ready && prisoners.emily.ready) || performance.now() > 60000) splash.hide(); else requestAnimationFrame(warm); };
  warm();
}
main().catch(e => { console.error(e); (globalThis as unknown as { ferretError: string }).ferretError = String(e?.message ?? e); const t = document.getElementById('splashtxt'); if (t) t.textContent = 'Error: ' + (e?.message ?? e); });
