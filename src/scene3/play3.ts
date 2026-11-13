// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import { createGame } from '@ferret/game';
import { AssetCache, AssetStore, PersistentCache, detectBackend } from '@ferret/assets';
import { AssetLibrary, LevelService, RuntimeAssets, defaultLibraryUrl, installPackages } from '@ferret/levels';
import { detectLevelTier } from '@ferret/platform';
import { FlowService } from '@ferret/flow';
import { CloudField, CloudView } from '@ferret/clouds';
import { ScatterView, TerrainView } from '@ferret/terrain';
import { GrassView, WeatherService, cloudFieldFor, terrainGround } from '@ferret/weather';
import { Lakes } from './water3';
import { Forest } from '@zeppelin/world/forest';
import { SkyDome, lookOf, type Look } from '../weather/sky';
import { WindField } from '../weather/wind-sway';
import type { WeatherPreset } from '../config/weather';
import { COAST_KM, SITE, WEATHERS, RUNWAY, TAXI, type Weather3 } from './config';
import { makeLandscape, LOOKS, FIELD_LEVEL } from './ground3';
import { terrainMaterial } from './terrain3';
import { Mats } from './mats3';
import { buildSurfaces } from './surfaces3';
import { buildBuildings } from './buildings3';
import { AircraftModel, makeAeroplane, wingOf, perspectiveOf } from './aircraft3';
import { TakeoffRun, type TakeoffOptions } from './flight3';
import { PARKED } from './layout3';
import { buildProps } from './props3';
import { Crew } from './people3';
import { makePoliceDrive, policeBody, loadPoliceInfos } from './police3';
import { plantMaterial } from '../land/plant-material';
import { GENERATORS3, SMALL, STONES3 } from './plants3';
import { STONE_GENERATORS } from '../land/plants';
import { Verges } from './verges3';
import { onPavement } from './layout3';
import { fieldBand } from './fields3';

/**
 * Scene 3 of TAKE 37, the airfield. The page builds the field (ground, sky, weather, the sea over the coast) and offers a free camera and named views for the stills:
 * `?weather=day|sunset`, `?view=<name>`, `?lite=1`, `?clean=1`. `window.__scene3` is the handle the shot tool and the flight test drive.
 */
const $ = (id: string) => document.getElementById(id)!;
const q = new URLSearchParams(location.search);
type V3 = [number, number, number];
const splash = {
  set(p: number, text: string) { const b = document.getElementById('splashbar'), t = document.getElementById('splashtxt'); if (b) b.style.width = Math.round(p * 100) + '%'; if (t) t.textContent = text; },
  hide() { const e = document.getElementById('splash'); if (e) { e.classList.add('gone'); setTimeout(() => e.remove(), 900); } },
};
const presetOf = (w: Weather3): { preset: WeatherPreset; state: Record<string, number> } => ({
  preset: { description: w.description, base: w.base, state: {}, hour: w.hour, sunRoll: w.sunRoll, visibilityKm: w.visibilityKm, cumulus: w.cumulus },
  state: { wind: w.wind, windDir: w.windDir, gustiness: 0.25, cloudCover: w.cover, convection: 0.3, temperature: 17 },
});

async function main() {
  $('splashver').textContent = String((globalThis as { __TAKE37_BUILD__?: string }).__TAKE37_BUILD__ ?? '');
  if (BABYLON.MeshoptCompression) BABYLON.MeshoptCompression.Configuration.decoder = { url: new URL('lib/meshopt_decoder.js', location.href).href };
  splash.set(0.05, 'Landscape');
  const canvas = $('c') as HTMLCanvasElement;
  const game = createGame({ canvas, storageKey: 'take37-scene3', input: { actions: {}, bindings: { keyboard: {}, gamepad: {}, touch: {}, console: {} } as never } });
  const { world, scene, engine } = game;
  const lite = q.get('lite') === '1';
  let weatherName = q.get('weather') && WEATHERS[q.get('weather')!] ? q.get('weather')! : 'day';
  let w3 = WEATHERS[weatherName]!, pv = presetOf(w3);
  const landscape = makeLandscape(), ground = landscape.ground;
  const groundAt = (await import('./ground3')).groundOf();
  world.addService(new FlowService());
  const weather: WeatherService = world.addService(new WeatherService({
    state: pv.preset.base, seed: 1944, area: [-3000, -3000, 3000, 3000], sea: false, ground: terrainGround(ground, () => weather.state, { reference: [0, 0] }),
  }));
  weather.set(pv.preset.base, pv.state as never);

  splash.set(0.1, 'Asset library');
  const assets = new AssetCache(scene), levels = world.addService(new LevelService()), mount = installPackages(levels, assets);
  const store = new AssetStore({ cache: new PersistentCache(await detectBackend()), base: location.href });
  const runtime = world.addService(new RuntimeAssets({ store, models: mount.assets, mount }));
  const lib = world.addService(new AssetLibrary({ store, mount, assets: runtime, policy: { allowUnsigned: true }, tier: detectLevelTier({ override: q.get('tier'), screen: game.platform.screen() }).tier }));
  await lib.open(defaultLibraryUrl());
  const tex = async (id: string) => (await lib.texture(id)).basecolor!;
  const ttex = { grass: await tex('ground-grass-textures'), soil: await tex('soil-textures'), rock: await tex('rock-slate-textures'), gravel: await tex('cobble-stone-pebble-floor-12-textures') };

  scene.fogMode = BABYLON.Scene.FOGMODE_EXP2;
  const ip = scene.imageProcessingConfiguration;
  ip.toneMappingEnabled = true; ip.toneMappingType = BABYLON.ImageProcessingConfiguration.TONEMAPPING_ACES; ip.exposure = 1.0; ip.contrast = 1.08;
  const camera = new BABYLON.UniversalCamera('eye', new BABYLON.Vector3(0, FIELD_LEVEL + 1.7, RUNWAY.z1 - 20), scene);
  camera.minZ = 0.3; camera.maxZ = 32000; camera.fov = 0.95; camera.speed = 0.6; camera.angularSensibility = 2500;
  camera.keysUp = [87]; camera.keysDown = [83]; camera.keysLeft = [65]; camera.keysRight = [68]; camera.keysUpward = [69]; camera.keysDownward = [81];
  camera.attachControl(canvas, true); scene.activeCamera = camera; game.display.trackCamera(camera);
  if (!lite) {
    const pipe = new BABYLON.DefaultRenderingPipeline('post', true, scene, [camera]);
    pipe.samples = 4; pipe.fxaaEnabled = false; pipe.bloomEnabled = true; pipe.bloomThreshold = 0.9; pipe.bloomWeight = 0.14; pipe.bloomKernel = 32; pipe.bloomScale = 0.5; pipe.sharpenEnabled = false; pipe.imageProcessingEnabled = true;
  }
  const dome = new SkyDome(scene);
  const hemi = new BABYLON.HemisphericLight('sky-light', new BABYLON.Vector3(0, 1, 0), scene);
  const sun = new BABYLON.DirectionalLight('sun', new BABYLON.Vector3(-0.3, -0.8, -0.4), scene);
  sun.shadowMinZ = 1; sun.shadowMaxZ = 700;
  let shadow: BABYLON.CascadedShadowGenerator | null = null;
  if (!lite && q.get('shadows') !== '0') {
    shadow = new BABYLON.CascadedShadowGenerator(2048, sun);
    shadow.numCascades = 3; shadow.lambda = 0.8; shadow.shadowMaxZ = 500; shadow.stabilizeCascades = true; shadow.usePercentageCloserFiltering = true; shadow.filteringQuality = BABYLON.ShadowGenerator.QUALITY_MEDIUM;
    shadow.bias = 0.0006; shadow.normalBias = 0.02; shadow.depthClamp = true; shadow.autoCalcDepthBounds = false; shadow.transparencyShadow = false;
    shadow.getShadowMap()!.refreshRate = 3;
  }

  splash.set(0.2, 'Terrain');
  const first = lookOf(weather.state, pv.preset);
  const mat = terrainMaterial(scene, ttex);
  const terrain = new TerrainView(scene, {
    ground, cell: 1, levels: 12, radius: 80000, split: 1.5, buildsPerUpdate: 3, buildMs: 8, looks: LOOKS, water: false,
    sun: first.sunDir, sunColor: first.sunColor, ambient: first.hemiSky, haze: first.hazeColor, hazeDensity: first.hazeDensity, material: () => mat,
  });
  const wind = new WindField(scene, weather);
  const clock = () => world.time;
  const sea = new Lakes(scene, { skyTop: first.skyTop, skyHorizon: first.skyHorizon, sunDir: first.sunDir, sunColor: first.sunColor, clock });
  // ---- vegetation: the plain's scatter (the engine's ScatterView), the airfield's hand-placed hedges and verges, near grass blades ----
  const plantMat = plantMaterial(scene, wind), rockMat = plantMaterial(scene, wind, 0);
  const small = new ScatterView(scene, { ground, species: SMALL, cell: 48, radius: lite ? 90 : 160, cellsPerUpdate: 2, generators: GENERATORS3 });
  const stones = new ScatterView(scene, { ground, species: STONES3, generators: STONE_GENERATORS, cell: 64, radius: lite ? 100 : 200, cellsPerUpdate: 1, tint: [1.02, 0.96, 0.86] });
  (small as unknown as { mat: BABYLON.Material }).mat = plantMat; (stones as unknown as { mat: BABYLON.Material }).mat = rockMat;
  const verges = new Verges(scene, plantMat, groundAt);
  const tv = performance.now(); verges.hedgerows(lite ? 1800 : 2300); verges.copses(lite ? 1800 : 2300); verges.boundary(); verges.verges(); const vergeMs = Math.round(performance.now() - tv);
  const forest = new Forest(scene, { scale: 1, perFrame: lite ? 8 : 5 });
  const grass = new GrassView(scene, weather, {
    count: lite ? 6000 : 16000, radius: lite ? 22 : 32, height: 0.34, stiffness: 0.3, ground: groundAt, base: [0.14, 0.24, 0.06], tip: [0.42, 0.55, 0.2],
    density: (x, z) => (onPavement(x, z, 1.2) ? 0 : Math.min(1, Math.max(0, fieldBand(x, z) + 16) / 10) * 0.9 + 0.35 * (1 - Math.min(1, Math.max(0, fieldBand(x, z) + 16) / 10))),
  });
  const cloudField = new CloudField({ ...cloudFieldFor(weather.state), seed: 37 });
  const clouds = new CloudView(scene, cloudField, { tier: lite ? 'low' : 'high' });

  let look: Look = first;
  const applyLook = () => {
    look = lookOf(weather.state, pv.preset);
    const hz = look.hazeColor, v3 = (a: number[], k = 1) => new BABYLON.Vector3(a[0] * k, a[1] * k, a[2] * k);
    scene.clearColor = new BABYLON.Color4(hz[0], hz[1], hz[2], 1); scene.fogColor = new BABYLON.Color3(hz[0], hz[1], hz[2]); scene.fogDensity = look.fogDensity;
    dome.set(look);
    hemi.diffuse = new BABYLON.Color3(...look.hemiSky); hemi.groundColor = new BABYLON.Color3(...look.hemiGround); hemi.intensity = look.hemiIntensity;
    sun.direction = new BABYLON.Vector3(-look.sunDir[0], -look.sunDir[1], -look.sunDir[2]); sun.diffuse = new BABYLON.Color3(...look.sunColor); sun.intensity = look.sunIntensity;
    const sc = look.sunColor.map(c => c * look.sunIntensity * 0.36) as V3, am = look.hemiSky.map(c => c * look.hemiIntensity * 0.3) as V3;
    terrain.setLight(look.sunDir, sc, am, look.hazeColor); terrain.setHaze(look.hazeColor, look.hazeDensity);
    mat.setVector3('skyColor', v3(look.skyHorizon)); mat.setFloat('exposure', 0.85);
    sea.setLight(look.sunDir, look.sunColor); sea.setFog(new BABYLON.Color3(hz[0], hz[1], hz[2]), look.fogDensity); sea.setWind(weather.state.wind, weather.state.windDir);
    plantMat.light(look.sunDir, look.sunColor.map(c => c * look.sunIntensity * 0.22) as V3, look.hemiSky.map(c => c * look.hemiIntensity * 0.42) as V3, look.hazeColor, look.hazeDensity);
    rockMat.light(look.sunDir, look.sunColor.map(c => c * look.sunIntensity * 0.22) as V3, look.hemiSky.map(c => c * look.hemiIntensity * 0.42) as V3, look.hazeColor, look.hazeDensity);
    grass.setLight(look.sunColor.map(c => c * (0.25 + 0.5 * look.day)) as V3, look.hazeColor, look.fogDensity);
    clouds.setSun(look.sunDir); const tint = 0.35 + 0.65 * look.day; clouds.setTint(tint * (1 + 0.3 * (1 - look.day)), tint, tint * (0.95 - 0.2 * (1 - look.day)));
    cloudField.setCover(weather.state.cloudCover);
  };
  applyLook();

  // ---- views ----
  const view = (x: number, y: number, z: number, tx: number, ty: number, tz: number, fov = 0.95) => ({ position: [x, y, z] as V3, target: [tx, ty, tz] as V3, fov });
  const L = FIELD_LEVEL, SHORE = COAST_KM * 1000;
  const views = (): Record<string, { position: V3; target: V3; fov: number }> => ({
    overview: view(-260, L + 400, 780, 90, L, 20, 0.9),
    threshold: view(2, L + 1.8, RUNWAY.z1 - 30, 0, L + 3, RUNWAY.z0, 0.95),
    taxiway: view(TAXI.x - 40, L + 2.2, 330, TAXI.x + 10, L + 2, 40, 0.95),
    sea: view(SHORE - 900, 90, 0, SHORE + 20000, 20, 3000, 0.95),
    coast: view(SHORE - 6000, 700, -1500, SHORE + 3000, 0, 0, 1.0),
    alt400: view(-500, L + 400, 150, 1200, L + 50, 200, 0.95),
    alt2k: view(-1800, L + 2000, 400, 8000, 200, 1000, 1.0),
    alt10k: view(-4000, 10000, -12000, 22000, 300, 4000, 1.05),
    runwayLow: view(0, L + 1.7, RUNWAY.z1 - 12, 0, L + 1.5, RUNWAY.z0, 0.95),
    numerals: view(0, L + 9, RUNWAY.z1 + 10, 0, L, RUNWAY.z1 - 50, 1.0),
    gate: view(300, L + 3, 520, 308, L + 1.5, 560, 0.95),
    hangars: view(150, L + 4, 330, 240, L + 4, 372, 0.95),
    hangar1: view(188, L + 2.4, 300, 222, L + 4, 326, 0.9),
    hangar2: view(190, L + 2.4, 392, 218, L + 3.5, 372, 0.9),
    hangar3: view(194, L + 2.4, 440, 220, L + 3, 416, 0.9),
    tower: view(206, L + 2.4, 280, 176, L + 5, 246, 0.9),
    fuel: view(250, L + 3.5, 420, 292, L + 1.5, 472, 0.95),
    nissen: view(236, L + 2, 190, 268, L + 1.5, 240, 0.95),
    windsock: view(20, L + 4.5, -70, 52, L + 7.0, -90, 0.9),
    pad: view(0, L + 1.8, 380, 0, L + 0.5, 330, 0.95),
  });
  const aim = (p: V3, t: V3, fov?: number) => { camera.position.set(...p); camera.setTarget(new BABYLON.Vector3(...t)); if (fov) camera.fov = fov; };
  const settleOnce = (frames: number) => new Promise<void>((res) => { let n = 0; const o = scene.onAfterRenderObservable.add(() => { if (++n >= frames) { scene.onAfterRenderObservable.remove(o); res(); } }); });
  let frame = 0, vergeAt = -1, scatterAt = -1, scatterTurn = 0; let lastLook = 0, terrainAt = -1, terrainPending = 1; let terrainPos: V3 = [1e9, 0, 0];
  scene.onBeforeRenderObservable.add(() => {
    const t = world.time, c = camera.globalPosition, cp: V3 = [c.x, c.y, c.z]; sea.update(cp);
    const moved = Math.hypot(cp[0] - terrainPos[0], cp[1] - terrainPos[1], cp[2] - terrainPos[2]);
    if (moved > 6 || (terrainPending > 0 && t - terrainAt > 0.4) || t - terrainAt > 3) { terrainAt = t; terrainPos = cp; terrainPending = terrain.update(cp).pending; }
    if (t - lastLook > 0.5) { lastLook = t; applyLook(); }
    if (++frame % 3 === 0) grass.update();
    forest.update(cp);
    if (t - vergeAt > 0.4) { vergeAt = t; verges.update(cp[0], cp[2]); }
    if (t - scatterAt > 0.3) { scatterAt = t; if (scatterTurn++ % 2) small.update(cp); else stones.update(cp); }
  });
  splash.set(0.5, 'Pavements');
  const mats = new Mats(lib, scene);
  const surfaces = await buildSurfaces(scene, mats, groundAt);
  splash.set(0.55, 'Buildings');
  const buildings = await buildBuildings(scene, mats);
  if (shadow) for (const m of [...surfaces.shadowCasters, ...buildings.casters]) shadow.addShadowCaster(m);
  scene.onBeforeRenderObservable.add(() => buildings.windsock.update(weather.state.windDir, weather.state.wind, world.time));
  splash.set(0.58, 'Aircraft');
  perspectiveOf(world, scene);
  const parked: AircraftModel[] = [];
  const aeroplaneFor = makeAeroplane('p51d', groundAt);
  for (const a of PARKED) {
    const am = new AircraftModel(scene, lib, a.model, a.id, a.id === 'mustang' ? { wingX: wingOf(aeroplaneFor) } : {});
    parked.push(am);
    void am.ready.then(() => { am.setProps(true); am.place(a.x, a.z, a.yaw, groundAt); for (const g of am.gear) g.setEnabled(true); if (shadow) for (const m of am.meshes) shadow.addShadowCaster(m); am.far(world, [0.35, 0.37, 0.33], 'parked'); }).catch(e => console.warn('aircraft', a.id, e));
  }
  await Promise.all(parked.map(p => p.ready.catch(() => null)));
  splash.set(0.59, 'Props and people');
  const props = await buildProps(scene, lib, mats, groundAt, shadow);
  const crew = new Crew(scene, lib, groundAt, shadow); await crew.build();
  // the police car: the game's car sim on this ground, driven along the access road; stepped by hand through `police.run` (the shot tool) or by `?police=1` in real time
  const fetchBytes = async (url: string) => { const r = await fetch(url); if (!r.ok) throw new Error(url + ' ' + r.status); return r.arrayBuffer(); };
  const policeInfos = await loadPoliceInfos(fetchBytes);
  const pd = makePoliceDrive(policeInfos, groundAt); const pbody = await policeBody(scene, pd.car, shadow); pbody.update(0);
  let policeLive = q.get('police') === '1'; let pAcc = 0;
  scene.onBeforeRenderObservable.add(() => { if (!policeLive) return; pAcc += Math.min(0.05, engine.getDeltaTime() / 1000); while (pAcc >= 1 / 60) { pd.step(1 / 60); pAcc -= 1 / 60; } pbody.update(1 / 60); });
  const police = { drive: pd, body: pbody, live(on: boolean) { policeLive = on; }, run(seconds: number) { const n = Math.round(seconds * 60); for (let i = 0; i < n && !pd.arrived; i++) pd.step(1 / 60); pbody.update(1 / 60); return { x: pd.car.veh.pos[0], z: pd.car.veh.pos[2], speed: Math.hypot(pd.car.veh.vel[0], pd.car.veh.vel[2]), arrived: pd.arrived }; }, reset() { pd.reset(); pbody.update(0); } };
  splash.set(0.6, 'Building the land');
  const api = {
    game, scene, engine, camera, weather, ground, groundAt, terrain, look: () => look, sea, lib, shadow, sun, wind, mat, tex: ttex, COAST_KM, SITE, FIELD_LEVEL,
    renderer() { const gl = (engine as BABYLON.Engine)._gl as WebGL2RenderingContext, ext = gl.getExtension('WEBGL_debug_renderer_info'); return ext ? String(gl.getParameter(ext.UNMASKED_RENDERER_WEBGL)) : String(gl.getParameter(gl.RENDERER)); },
    setWeather(name: string) { if (!WEATHERS[name]) throw new Error('no weather ' + name); weatherName = name; w3 = WEATHERS[name]!; pv = presetOf(w3); weather.set(pv.preset.base, pv.state as never); applyLook(); },
    views, aim, mats, surfaces, buildings, forest, parked, props, crew, police,
    /** the Mustang's take-off run from the runway's south end on the field's real ground; the model follows the flight model each frame; `cockpit` puts the camera at the pilot's eye */
    async takeoff(o: Partial<TakeoffOptions> & { cockpit?: boolean; shotAt?: number[]; shot?: (name: string) => Promise<void> } = {}) {
      const plane = makeAeroplane('p51d', groundAt), model = new AircraftModel(scene, lib, 'mustang', 'flight-mustang', { wingX: wingOf(plane) });
      await model.ready; model.holder.setEnabled(true); if (shadow) for (const m of model.meshes) shadow.addShadowCaster(m);
      const run = new TakeoffRun(plane, { startNorth: -(RUNWAY.z1 - 30), climbTo: FIELD_LEVEL + 300, ...o }); const eyeAt = model.eye ?? [0.2, 1.1, 0];
      const pose = () => {
        model.pose(plane, 1 / 60); model.holder.computeWorldMatrix(true);
        if (o.cockpit) { const e = BABYLON.Vector3.TransformCoordinates(new BABYLON.Vector3(eyeAt[0], eyeAt[1], eyeAt[2]), model.holder.getWorldMatrix()), f = BABYLON.Vector3.TransformNormal(new BABYLON.Vector3(1, 0, 0), model.holder.getWorldMatrix()); camera.position.copyFrom(e); camera.setTarget(e.add(f)); model.setCanopy(false); }
      };
      pose(); const shots = [...(o.shotAt ?? [])]; let acc = 0;
      for (;;) {
        const more = run.step(); acc += run.t > 0 ? 1 : 0;
        if (acc % 2 === 0) { pose(); }
        if (shots.length && run.t >= shots[0]!) { shots.shift(); pose(); await settleOnce(2); await o.shot?.('t' + run.t.toFixed(1)); }
        if (!more) break;
        if (acc % 8 === 0) await new Promise(r => requestAnimationFrame(() => r(null)));
      }
      pose(); return { log: run.log, endN: plane.pos[0], endE: plane.pos[1], altitude: plane.altitude, plane, model };
    }, verges, small, stones, grass, vergeMs,
    async goto(name: string) {
      const v = views()[name]; if (!v) throw new Error('no view ' + name);
      api.free(v.position, v.target, v.fov);
    },
    async free(p: V3, t: V3, fov = 0.95) {
      aim(p, t, fov);
      for (let i = 0; i < 600; i++) { const s = terrain.prime(p); small.prime(p); stones.prime(p); if (s.pending === 0) break; }
      verges.update(p[0], p[2]); grass.update();
      await settleOnce(20);
    },
    settle: (n = 20) => settleOnce(n),
    stats() { const s = terrain.stats(); return { chunks: s.chunks, triangles: s.triangles, fps: Math.round(engine.getFps()), draws: 0 }; },
  };
  (window as unknown as Record<string, unknown>).__scene3 = api;
  engine.runRenderLoop(() => scene.render());
  void weatherName;
  const v0 = views().overview; aim(v0.position, v0.target, v0.fov);
  for (let i = 0; i < 600; i++) { const s = terrain.prime(v0.position); if (s.pending === 0) break; }
  splash.set(1, 'Ready'); splash.hide();
  (window as unknown as Record<string, unknown>).ferretReady = true;
}
main().catch((e) => { console.error(e); (window as unknown as Record<string, unknown>).ferretError = String(e?.stack ?? e); const t = document.getElementById('splashtxt'); if (t) t.textContent = 'Error: ' + (e?.message ?? e); });
