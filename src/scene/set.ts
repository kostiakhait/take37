// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import { createGame, type Game } from '@ferret/game';
import { AssetCache, AssetStore, PersistentCache, detectBackend } from '@ferret/assets';
import { AssetLibrary, LevelService, RuntimeAssets, defaultLibraryUrl, installPackages } from '@ferret/levels';
import { detectLevelTier } from '@ferret/platform';
import { FlowService } from '@ferret/flow';
import { CloudField, CloudView } from '@ferret/clouds';
import { ScatterView, TerrainView, type Ground } from '@ferret/terrain';
import { GrassView, WeatherService, cloudFieldFor, terrainGround } from '@ferret/weather';
import { PLATFORM, STREET, platformEdgeDistance } from '../config/stage';
import { WEATHER, weatherPreset, type WeatherPreset } from '../config/weather';
import { DIRT_ROADS, LOOKS, makeLandscape } from '../land/relief';
import { GENERATORS, OAKS, SHRUBS, STONES } from '../land/plants';
import { plantMaterial } from '../land/plant-material';
import { terrainMaterial } from '../land/terrain-material';
import { buildPowerLines, type LineSpec } from '../land/powerline';
import { SkyDome, lookOf, type Look } from '../weather/sky';
import { WindField, applyWindSway, attachBakedWind, type SwayRule } from '../weather/wind-sway';
import { Litter } from '../weather/litter';
import { Flag, stripesTexture } from '../weather/flags';

/**
 * The film set: the street of `art/street`, the gas station, the flat platform they stand on, the Californian hills round it out to the horizon, and the weather over all of it.
 * `buildSet` makes the scene and returns what a game or a test needs: the cameras, the weather, the ground query and `settle` (build everything planned, for stills).
 */
export interface SetHandle {
  game: Game; scene: BABYLON.Scene; weather: WeatherService; camera: BABYLON.UniversalCamera; ground: Ground;
  groundAt(x: number, z: number): number; terrain: TerrainView; wind: WindField; look(): Look; preset: WeatherPreset; presetName: string;
  renderer(): { vendor: string; renderer: string; version: string };
  setHour(h: number): void; setWeather(name: string): void;
  views(): Record<string, { position: [number, number, number]; target: [number, number, number]; fov?: number }>;
  goto(view: string): Promise<void>; settle(frames?: number): Promise<void>;
  stats(): Record<string, number | string>;
}

const base = (name: string) => name.replace(/_LOD[01]$/, '');
const split = (url: string) => { const i = url.lastIndexOf('/'); return [url.slice(0, i + 1), url.slice(i + 1)] as const; };

/** a 1 m lattice of the land's height, filled on demand (the grass, the litter and the flags ask thousands of times a frame; the relief itself is a pure function of (x, z)) */
function cachedHeight(g: Ground) {
  const cell = new Map<number, number>(), K = 2, key = (i: number, j: number) => (i + 20000) * 40000 + (j + 20000);
  const at = (i: number, j: number) => { const k = key(i, j); let v = cell.get(k); if (v === undefined) { v = g.relief.height(i * K, j * K); cell.set(k, v); } return v; };
  return (x: number, z: number) => {
    const u = x / K, v = z / K, i = Math.floor(u), j = Math.floor(v), fu = u - i, fv = v - j;
    return (at(i, j) * (1 - fu) + at(i + 1, j) * fu) * (1 - fv) + (at(i, j + 1) * (1 - fu) + at(i + 1, j + 1) * fu) * fv;
  };
}

export async function buildSet(canvas: HTMLCanvasElement, q: URLSearchParams, progress: (p: number, text: string) => void = () => {}): Promise<SetHandle> {
  const game = createGame({ canvas, storageKey: 'take37-set', input: { actions: {}, bindings: { keyboard: {}, gamepad: {}, touch: {}, console: {} } as never } });
  const { world, scene, engine } = game;
  const lite = q.get('lite') === '1';
  const asked = weatherPreset(q.get('weather') ?? undefined);
  let presetName = asked.name, preset = asked.preset;
  let hour = q.has('hour') ? +q.get('hour')! : preset.hour;

  // ---- the land and the weather: the weather asks the landscape what the ground is ----
  progress(0.04, 'Landscape');
  const landscape = makeLandscape(), ground = landscape.ground, groundAt = cachedHeight(ground);
  world.addService(new FlowService());
  const weather: WeatherService = world.addService(new WeatherService({
    state: preset.base, seed: 1987, area: [-3000, -3000, 3000, 3000], sea: false,
    ground: terrainGround(ground, () => weather.state, { reference: [300, 0] }),
  }));
  weather.set(preset.base, preset.state);

  // ---- the asset library: the ground textures ----
  progress(0.08, 'Asset library');
  const assets = new AssetCache(scene), levels = world.addService(new LevelService()), mount = installPackages(levels, assets);
  const store = new AssetStore({ cache: new PersistentCache(await detectBackend()), base: location.href });
  const runtime = world.addService(new RuntimeAssets({ store, models: mount.assets, mount }));
  const lib = world.addService(new AssetLibrary({ store, mount, assets: runtime, policy: { allowUnsigned: true }, tier: detectLevelTier({ override: q.get('tier'), screen: game.platform.screen() }).tier }));
  await lib.open(defaultLibraryUrl());
  const tex = { grass: (await lib.texture('ground-grass-textures')).basecolor!, soil: (await lib.texture('soil-textures')).basecolor!, rock: (await lib.texture('rock-slate-textures')).basecolor! };

  // ---- scene settings: tone mapping, anti-aliasing, fog ----
  scene.fogMode = BABYLON.Scene.FOGMODE_EXP2;
  const ip = scene.imageProcessingConfiguration;
  ip.toneMappingEnabled = true; ip.toneMappingType = BABYLON.ImageProcessingConfiguration.TONEMAPPING_ACES; ip.exposure = 1.0; ip.contrast = 1.08;
  const camera = new BABYLON.UniversalCamera('eye', new BABYLON.Vector3(30, 1.25, -1.7), scene);
  camera.minZ = 0.5; camera.maxZ = 32000; camera.fov = 0.95; camera.speed = 0.6; camera.angularSensibility = 2500;
  camera.keysUp = [87]; camera.keysDown = [83]; camera.keysLeft = [65]; camera.keysRight = [68]; camera.keysUpward = [69]; camera.keysDownward = [81];
  camera.attachControl(canvas, true); scene.activeCamera = camera; game.display.trackCamera(camera);
  if (!lite) {
    const pipe = new BABYLON.DefaultRenderingPipeline('post', true, scene, [camera]);
    pipe.samples = 4; pipe.fxaaEnabled = true; pipe.bloomEnabled = true; pipe.bloomThreshold = 0.85; pipe.bloomWeight = 0.18; pipe.bloomKernel = 48; pipe.sharpenEnabled = true; pipe.sharpen.edgeAmount = 0.2;
    pipe.imageProcessingEnabled = true;
  }

  // ---- sky, sun, light ----
  const dome = new SkyDome(scene);
  const hemi = new BABYLON.HemisphericLight('sky-light', new BABYLON.Vector3(0, 1, 0), scene);
  const sun = new BABYLON.DirectionalLight('sun', new BABYLON.Vector3(-0.3, -0.8, -0.4), scene);
  sun.shadowMinZ = 1; sun.shadowMaxZ = 900;
  let shadow: BABYLON.CascadedShadowGenerator | null = null;
  if (!lite) {
    shadow = new BABYLON.CascadedShadowGenerator(2048, sun);
    shadow.numCascades = 4; shadow.lambda = 0.82; shadow.shadowMaxZ = 650; shadow.stabilizeCascades = true; shadow.usePercentageCloserFiltering = true; shadow.filteringQuality = BABYLON.ShadowGenerator.QUALITY_MEDIUM;
    shadow.bias = 0.0006; shadow.normalBias = 0.02; shadow.depthClamp = true; shadow.autoCalcDepthBounds = false; shadow.transparencyShadow = false;
  }

  // ---- terrain ----
  progress(0.15, 'Terrain');
  const first = lookOf(weather.state, { ...preset, hour });
  const terrain = new TerrainView(scene, {
    ground, cell: 1, levels: 10, radius: 26000, split: 1.5, buildsPerUpdate: 3, buildMs: 8, looks: LOOKS, water: false,
    sun: first.sunDir, sunColor: first.sunColor, ambient: first.hemiSky, haze: first.hazeColor, hazeDensity: first.hazeDensity,
    material: (sc) => terrainMaterial(sc, tex),
  });

  // ---- wind: the field everything reads ----
  const wind = new WindField(scene, weather);
  const sway = applyWindSway(scene, wind, []);

  // ---- the street ----
  progress(0.25, 'Street');
  const [sdir, sfile] = split('/art/street/street_level.glb');
  const street = await BABYLON.SceneLoader.ImportMeshAsync('', sdir, sfile, scene);
  /** the loader turns a glTF about the vertical (a right-handed file in a left-handed scene); the art is authored with the street along +x and its y as the world's z, so only the mirror stays */
  const upright = (r: BABYLON.AbstractMesh | BABYLON.TransformNode | undefined) => { const root = r?.parent ?? r; if (root && (root as BABYLON.TransformNode).name === '__root__') (root as BABYLON.TransformNode).rotationQuaternion = BABYLON.Quaternion.Identity(); };
  upright(street.meshes[0]);
  const bakedTrees = await attachBakedWind(scene, '/art/street/street_level.glb').catch(() => 0);   // wind data of the street trees (art/street/TREES.md), 0 while the file has none
  const nodes = new Map<string, BABYLON.TransformNode>(); for (const n of street.transformNodes) nodes.set(n.name, n);
  for (const m of street.meshes) if (m.name === 'Ground') m.dispose();                       // the land is the terrain's now: one ground, flat under the set
  const lods = new Map<string, { hi?: BABYLON.AbstractMesh; lo?: BABYLON.AbstractMesh }>();
  for (const m of street.meshes) { const mm = m.name.match(/_LOD([01])$/); if (!mm) continue; const e = lods.get(base(m.name)) ?? {}; if (mm[1] === '0') e.hi = m; else e.lo = m; lods.set(base(m.name), e); }
  const lodDistance = (name: string) => name.startsWith('Bld_') ? 180 : name.startsWith('StreetTree') ? 110 : 70;
  for (const m of street.meshes) { m.computeWorldMatrix(true); m.isPickable = false; m.receiveShadows = true; if (m.getTotalVertices() > 0) m.alwaysSelectAsActiveMesh = false; }
  progress(0.5, 'Gas station');
  const [gdir, gfile] = split('/art/gas-station/gas_station_lite.glb');
  const gas = await BABYLON.SceneLoader.ImportMeshAsync('', gdir, gfile, scene).catch(() => null);
  const anchor = nodes.get('GasStation_Anchor');
  if (gas && anchor) {
    const r = gas.meshes[0]; if (r && !r.getTotalVertices()) { r.parent = anchor; r.position.setAll(0); r.rotationQuaternion = BABYLON.Quaternion.Identity(); r.scaling.set(1, 1, 1); }
    for (const m of gas.meshes) { m.isPickable = false; m.receiveShadows = true; }
  }
  const casters = [...street.meshes, ...(gas?.meshes ?? [])];
  const lodUpdate = () => {
    const c = camera.globalPosition;
    for (const [name, e] of lods) {
      if (!e.hi || !e.lo) continue;
      const bs = e.hi.getBoundingInfo().boundingSphere.centerWorld, d = Math.hypot(bs.x - c.x, bs.y - c.y, bs.z - c.z), near = d < lodDistance(name);
      if (e.hi.isEnabled() !== near) { e.hi.setEnabled(near); e.lo.setEnabled(!near); }
    }
  };
  lodUpdate();
  if (shadow) for (const m of casters) if (m.getTotalVertices() > 0 && !/Road_|Ground|Wires/.test(m.name)) shadow.addShadowCaster(m, false);

  // ---- wind on the street: trees, wires, awnings ----
  progress(0.62, 'Wind');
  for (const m of scene.materials) {
    if (m instanceof BABYLON.PBRMaterial) {
      if (/^leaves$/.test(m.name)) sway.add(m, { kind: 'tree', flutter: 1, gain: 1, weightsFromColor: false });
      else if (/^bark$/.test(m.name)) sway.add(m, { kind: 'tree', flutter: 0, gain: 1, weightsFromColor: false });
      else if (/^cable$/.test(m.name)) sway.add(m, { kind: 'cable', top: 10.0, sag: 0.9, gain: 1 });
      else if (/^awn_/.test(m.name)) sway.add(m, { kind: 'awning', gain: 1 });
    }
  }

  // ---- vegetation: oaks far out, bushes and straw tufts near, stones, and grass in the walk of the camera ----
  progress(0.7, 'Vegetation');
  const oaks = new ScatterView(scene, { ground, species: OAKS, cell: 128, radius: lite ? 700 : 1600, cellsPerUpdate: 2, generators: GENERATORS });
  const bushes = new ScatterView(scene, { ground, species: SHRUBS, cell: 48, radius: lite ? 100 : 200, cellsPerUpdate: 2, generators: GENERATORS });
  const stones = new ScatterView(scene, { ground, species: STONES, cell: 64, radius: lite ? 120 : 260, cellsPerUpdate: 1, tint: [1.02, 0.95, 0.84] });
  const plantMat = plantMaterial(scene, wind);
  for (const v of [oaks, bushes]) (v as unknown as { mat: BABYLON.Material }).mat = plantMat;
  const roadDistance = (x: number, z: number) => {
    let best = 1e9;
    for (const r of DIRT_ROADS) { const p = r.points; for (let i = 0; i + 1 < p.length; i++) { const ax = p[i][0], az = p[i][1], bx = p[i + 1][0], bz = p[i + 1][1], dx = bx - ax, dz = bz - az, l2 = dx * dx + dz * dz, u = Math.max(0, Math.min(1, ((x - ax) * dx + (z - az) * dz) / l2)); best = Math.min(best, Math.hypot(x - ax - dx * u, z - az - dz * u) - r.width / 2); } }
    return best;
  };
  const grass = new GrassView(scene, weather, {
    count: lite ? 5000 : 14000, radius: lite ? 22 : 30, height: 0.62, stiffness: 0.3, ground: groundAt, base: [0.34, 0.27, 0.11], tip: [0.78, 0.66, 0.36],
    density: (x, z) => Math.min(1, Math.max(0, platformEdgeDistance(x, z) / 8)) * Math.min(1, Math.max(0, roadDistance(x, z) / 1.5)) * 0.95,
  });

  // ---- power lines, flags, litter ----
  progress(0.8, 'Details');
  const metal = new BABYLON.PBRMaterial('pylon-steel', scene); metal.albedoColor = new BABYLON.Color3(0.5, 0.52, 0.54); metal.metallic = 0.7; metal.roughness = 0.5; metal.backFaceCulling = false;
  const woodMat = new BABYLON.PBRMaterial('pole-wood', scene); woodMat.albedoColor = new BABYLON.Color3(0.22, 0.17, 0.12); woodMat.metallic = 0; woodMat.roughness = 0.9;
  const wireMat = new BABYLON.PBRMaterial('hv-wire', scene); wireMat.albedoColor = new BABYLON.Color3(0.12, 0.12, 0.13); wireMat.metallic = 0.6; wireMat.roughness = 0.45; wireMat.backFaceCulling = false;
  const lines: LineSpec[] = [
    { kind: 'pylon', route: [[-2300, 1500], [-1200, 1180], [-200, 1020], [900, 1120], [1900, 1420], [3000, 1700]], span: 300 },
    { kind: 'wood', route: DIRT_ROADS[0].points.slice(0, 7).map(([x, z]) => [x, z + 7] as [number, number]), span: 55 },
    { kind: 'wood', route: DIRT_ROADS[2].points.slice(0, 7).map(([x, z]) => [x, z - 7] as [number, number]), span: 55 },
  ];
  const power = buildPowerLines(scene, lines, groundAt, { steel: metal, wood: woodMat, wire: wireMat });
  sway.add(wireMat, { kind: 'cable-uv', gain: 1.4 });
  if (shadow) for (const m of [power.poles]) shadow.addShadowCaster(m, false);
  const flagMat = new BABYLON.PBRMaterial('flag', scene); flagMat.albedoTexture = stripesTexture(scene); flagMat.roughness = 0.85; flagMat.metallic = 0; flagMat.backFaceCulling = false; flagMat.twoSidedLighting = true;
  const poleMat = new BABYLON.PBRMaterial('flagpole', scene); poleMat.albedoColor = new BABYLON.Color3(0.72, 0.72, 0.7); poleMat.metallic = 0.8; poleMat.roughness = 0.35;
  const flags = ([[128, 8.7], [262, -8.7], [412, 8.7], [533, -20]] as const).map(([x, z]) => new Flag(scene, wind, { x, z, ground: 0.15, pole: 7.5, w: 2.4, h: 1.4 }, flagMat, poleMat));
  if (shadow) for (const f of flags) shadow.addShadowCaster(f.pole, false);
  const litter = new Litter(scene, wind, { count: lite ? 120 : 280, radius: 55, ground: (x, z) => (Math.abs(z) < STREET.halfWidth && x > STREET.x0 && x < STREET.x1 ? 0 : groundAt(x, z)) });

  // ---- clouds ----
  const cloudField = new CloudField({ ...cloudFieldFor(weather.state), seed: 37 });
  const clouds = new CloudView(scene, cloudField, { tier: lite ? 'low' : 'high' });

  // ---- the look follows the weather and the hour ----
  let look = first;
  const applyLook = () => {
    look = lookOf(weather.state, { ...preset, hour });
    scene.clearColor = new BABYLON.Color4(look.hazeColor[0], look.hazeColor[1], look.hazeColor[2], 1);
    scene.fogColor = new BABYLON.Color3(look.hazeColor[0], look.hazeColor[1], look.hazeColor[2]); scene.fogDensity = look.fogDensity;
    dome.set(look);
    hemi.diffuse = new BABYLON.Color3(...look.hemiSky); hemi.groundColor = new BABYLON.Color3(...look.hemiGround); hemi.intensity = look.hemiIntensity;
    sun.direction = new BABYLON.Vector3(-look.sunDir[0], -look.sunDir[1], -look.sunDir[2]); sun.diffuse = new BABYLON.Color3(...look.sunColor); sun.intensity = look.sunIntensity;
    terrain.setLight(look.sunDir, [look.sunColor[0] * look.sunIntensity * 0.24, look.sunColor[1] * look.sunIntensity * 0.24, look.sunColor[2] * look.sunIntensity * 0.24],
      [look.hemiSky[0] * look.hemiIntensity * 0.42, look.hemiSky[1] * look.hemiIntensity * 0.42, look.hemiSky[2] * look.hemiIntensity * 0.42], look.hazeColor);
    terrain.setHaze(look.hazeColor, look.hazeDensity);
    plantMat.light(look.sunDir, [look.sunColor[0] * look.sunIntensity * 0.22, look.sunColor[1] * look.sunIntensity * 0.22, look.sunColor[2] * look.sunIntensity * 0.22], [look.hemiSky[0] * look.hemiIntensity * 0.42, look.hemiSky[1] * look.hemiIntensity * 0.42, look.hemiSky[2] * look.hemiIntensity * 0.42], look.hazeColor, look.hazeDensity);
    grass.setLight([look.sunColor[0] * (0.25 + 0.5 * look.day), look.sunColor[1] * (0.25 + 0.5 * look.day), look.sunColor[2] * (0.25 + 0.5 * look.day)], look.hazeColor, look.fogDensity);
    clouds.setSun(look.sunDir); const tint = 0.35 + 0.65 * look.day; clouds.setTint(tint * (1 + 0.3 * (1 - look.day)), tint, tint * (0.95 - 0.2 * (1 - look.day)));
    cloudField.setCover(weather.state.cloudCover);
  };
  applyLook();

  // ---- the views ----
  const view = (x: number, y: number, z: number, tx: number, ty: number, tz: number, fov?: number) => ({ position: [x, y, z] as [number, number, number], target: [tx, ty, tz] as [number, number, number], fov });
  const hillCamera = () => {
    // the highest ground 700 to 1300 m south-west of the set that looks across it: the eye 3 m above it, looking at the middle of the street
    let best: [number, number, number] = [-600, 80, -700];
    for (let a = -2.5; a <= -0.6; a += 0.12) for (let r = 700; r <= 1300; r += 60) { const x = 300 + Math.cos(a) * r, z = Math.sin(a) * r, h = groundAt(x, z); if (h > best[1]) best = [x, h, z]; }
    return view(best[0], best[1] + 3, best[2], 300, 8, 0, 0.7);
  };
  const views = () => ({
    cab: view(30, 1.25, -1.7, 160, 1.6, -1.7),
    cabMid: view(300, 1.25, -1.7, 520, 2.0, -1.7),
    sunsetFromEnd: view(540, 1.5, -1.7, 380, 5, 0, 0.9),
    street: view(-30, 5.5, -3.5, 120, 4, 0, 0.85),
    hill: hillCamera(),
    air: view(-260, 120, 260, 300, 5, 0, 0.85),
    ground: view(-70, 1.7, 40, -400, 20, 120, 0.85),
  });
  const aim = (cam: BABYLON.UniversalCamera, p: [number, number, number], t: [number, number, number], fov?: number) => {
    cam.position.set(...p); cam.setTarget(new BABYLON.Vector3(...t)); if (fov) cam.fov = fov;
  };

  // ---- each frame ----
  let lastLook = 0;
  const settleOnce = (frames: number) => new Promise<void>((res) => { let n = 0; const o = scene.onAfterRenderObservable.add(() => { if (++n >= frames) { scene.onAfterRenderObservable.remove(o); res(); } }); });
  let lodAt = 0;
  scene.onBeforeRenderObservable.add(() => {
    const dt = Math.min(0.1, engine.getDeltaTime() / 1000), t = world.time, c = camera.globalPosition, cp: [number, number, number] = [c.x, c.y, c.z];
    terrain.update(cp); oaks.update(cp); bushes.update(cp); stones.update(cp); grass.update(); clouds.update(cp, t);
    if (t - lastLook > 0.5) { lastLook = t; applyLook(); }
    if (t - lodAt > 0.2) { lodAt = t; lodUpdate(); }
    for (const f of flags) f.update(dt);
    litter.update(dt, c.x, c.z);
  });

  const api: SetHandle = {
    game, scene, weather, camera, ground, groundAt, terrain, wind, look: () => look, get preset() { return preset; }, get presetName() { return presetName; },
    renderer() {
      const gl = (engine as BABYLON.Engine)._gl as WebGL2RenderingContext, ext = gl.getExtension('WEBGL_debug_renderer_info');
      return { vendor: ext ? String(gl.getParameter(ext.UNMASKED_VENDOR_WEBGL)) : String(gl.getParameter(gl.VENDOR)), renderer: ext ? String(gl.getParameter(ext.UNMASKED_RENDERER_WEBGL)) : String(gl.getParameter(gl.RENDERER)), version: String(gl.getParameter(gl.VERSION)) };
    },
    setHour(h) { hour = h; applyLook(); },
    setWeather(name) { const w = weatherPreset(name); presetName = w.name; preset = w.preset; hour = preset.hour; weather.set(preset.base, preset.state); applyLook(); },
    views,
    async goto(name) {
      const v = views()[name as keyof ReturnType<typeof views>]; if (!v) throw new Error(`no view ${name}`);
      aim(camera, v.position, v.target, v.fov);
      const cp = v.position;
      // build everything the view needs, then let the wind and the litter run a moment
      for (let i = 0; i < 400; i++) { const s = terrain.prime(cp); oaks.prime(cp); bushes.prime(cp); stones.prime(cp); if (s.pending === 0) break; }
      lodUpdate(); grass.update();
      await settleOnce(24);
    },
    settle: (frames = 30) => settleOnce(frames),
    stats() {
      const s = terrain.stats();
      return { chunks: s.chunks, triangles: s.triangles, levels: JSON.stringify(s.levels), oaks: oaks.count(), bushes: bushes.count(), stones: stones.count(), grass: grass.drawn, litter: litter.airborne, sway: sway.materials, bakedTrees, meshes: scene.meshes.length, active: scene.getActiveMeshes().length, fps: Math.round(engine.getFps()) };
    },
  };
  progress(0.9, 'Terrain');
  { const v0 = views().cab; aim(camera, v0.position, v0.target, v0.fov); }
  void WEATHER; void power;
  game.start();
  progress(1, 'Ready');
  return api;
}
