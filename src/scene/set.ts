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
import { GENERATORS, OAKS, SHRUBS, STONES, STONE_GENERATORS } from '../land/plants';
import { plantMaterial } from '../land/plant-material';
import { buildSurround } from '../land/surround';
import { terrainMaterial } from '../land/terrain-material';
import { pinTerrain } from '../land/terrain-cache';
import { ROADS_BOX, roadsTexture } from '../land/roads-map';
import { buildPowerLines, type LineSpec } from '../land/powerline';
import { SkyDome, lookOf, type Look } from '../weather/sky';
import { WindField, applyWindSway, type SwayRule } from '../weather/wind-sway';
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
  /** builds the terrain and the vegetation round the camera, then starts the render loop (a no-op the second time) */
  start(): void;
  stats(): Record<string, number | string>;
  /** the sun's cascaded shadow generator (null in the light picture), for a game to add its own casters */
  shadow: BABYLON.CascadedShadowGenerator | null;
  /** with `keepProps`: the `DEST_<Kind>_<NNN>` nodes of the street, whole and with their level of detail switching (name to node) */
  propNodes: Map<string, BABYLON.TransformNode>;
  /** the street's loaded meshes and nodes, as the loader gave them (merged parts are gone) */
  street: BABYLON.ISceneLoaderAsyncResult;
}

/** what a game may ask of the set while it is built */
export interface SetOptions {
  /** `'lite'` (default): the light gas station of `art/gas-station`; `'none'`: no station, the game places its own at `GasStation_Anchor` */
  gas?: 'none' | 'lite';
  /** the `DEST_*` props of the street stay separate nodes (not merged into the cells), with their level of detail kept */
  keepProps?: boolean;
  /** called with the street's loaded result before anything is merged or moved: a game may rename, hide or take nodes here */
  onStreetLoaded?: (street: BABYLON.ISceneLoaderAsyncResult, scene: BABYLON.Scene) => void;
  /** the render loop is not started when the set is built: the game loads more (the cars, the layout) and calls `start()` when it is done, so that the loading is not slowed by drawing frames nobody sees */
  deferStart?: boolean;
}

/** the most time `start()` spends building the land before the first frame; what is left is built by the frames (a chunk budget each) while the splash is still up */
const PRIME_MS = 3000;
/** the most time `start()` spends on the land of the other places the game looks from (the rest was built while the page loaded) */
const PINS_MS = 12000;
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

/**
 * The flat roofs of the street ('tar' in the glb: a near-black factor, no texture) as a weathered built-up roof: mid-grey tar-and-gravel with a speckle, darker patched strips, pale lime streaks and
 * a warm tint; the glb's vertex colour (0.4 to 0.7) still varies it from one roof to the next. The texture is periodic, so the glb's metre UVs tile it without a seam.
 */
function roofMaterial(scene: BABYLON.Scene) {
  const S = 256, tex = new BABYLON.DynamicTexture('roof-gravel', { width: S, height: S }, scene, true), ctx = tex.getContext() as CanvasRenderingContext2D, img = ctx.createImageData(S, S);
  const hash = (x: number, y: number, s: number) => { let h = (x * 374761393 + y * 668265263 + s * 2147483647) | 0; h = (h ^ (h >>> 13)) * 1274126177 | 0; return ((h ^ (h >>> 16)) >>> 0) / 4294967296; };
  const noise = (u: number, v: number, n: number, s: number) => {   // periodic value noise with n cells across the tile
    const x = u * n, y = v * n, i = Math.floor(x), j = Math.floor(y), fx = x - i, fy = y - j, sx = fx * fx * (3 - 2 * fx), sy = fy * fy * (3 - 2 * fy);
    const a = hash(i % n, j % n, s), b = hash((i + 1) % n, j % n, s), c = hash(i % n, (j + 1) % n, s), d = hash((i + 1) % n, (j + 1) % n, s);
    return (a * (1 - sx) + b * sx) * (1 - sy) + (c * (1 - sx) + d * sx) * sy;
  };
  for (let y = 0; y < S; y++) for (let x = 0; x < S; x++) {
    const u = x / S, v = y / S, speck = hash(x, y, 1), grit = hash(x >> 1, y >> 1, 2);
    const patch = noise(u, v, 4, 3), mid = noise(u, v, 16, 4), strip = Math.abs(((u * 4) % 1) - 0.5) < 0.012 ? 1 : 0;   // darker patched strips every quarter of the tile
    let l = 0.46 + 0.22 * (speck - 0.5) + 0.16 * (grit - 0.5) + 0.2 * (mid - 0.5) + 0.22 * (patch - 0.5);
    if (speck > 0.965) l += 0.2;   // pale chips of gravel
    if (patch < 0.3) l -= 0.1;     // old wet tar
    l -= strip * 0.14;
    const k = (y * S + x) * 4, c = Math.max(0, Math.min(1, l)) * 255;
    img.data[k] = c * 1.03; img.data[k + 1] = c * 0.99; img.data[k + 2] = c * 0.92; img.data[k + 3] = 255;
  }
  ctx.putImageData(img, 0, 0); tex.update(true); tex.wrapU = tex.wrapV = BABYLON.Texture.WRAP_ADDRESSMODE; tex.anisotropicFilteringLevel = 4;
  for (const m of scene.materials) if (m instanceof BABYLON.PBRMaterial && m.name === 'tar') { m.albedoTexture = tex; m.albedoColor = new BABYLON.Color3(1, 1, 1); m.roughness = 0.92; m.metallic = 0; }
}

export async function buildSet(canvas: HTMLCanvasElement, q: URLSearchParams, progress: (p: number, text: string) => void = () => {}, options: SetOptions = {}): Promise<SetHandle> {
  // the geometry of the glb files is meshopt-compressed (tools/optimize_glb.mjs): the decoder is served with the page
  if (BABYLON.MeshoptCompression) BABYLON.MeshoptCompression.Configuration.decoder = { url: new URL('lib/meshopt_decoder.js', location.href).href };
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
    pipe.samples = 4; pipe.fxaaEnabled = false; pipe.bloomEnabled = true; pipe.bloomThreshold = 0.88; pipe.bloomWeight = 0.16; pipe.bloomKernel = 32; pipe.bloomScale = 0.5; pipe.sharpenEnabled = false;
    pipe.imageProcessingEnabled = true;
  }

  // ---- sky, sun, light ----
  const dome = new SkyDome(scene);
  const hemi = new BABYLON.HemisphericLight('sky-light', new BABYLON.Vector3(0, 1, 0), scene);
  const sun = new BABYLON.DirectionalLight('sun', new BABYLON.Vector3(-0.3, -0.8, -0.4), scene);
  sun.shadowMinZ = 1; sun.shadowMaxZ = 500;
  let shadow: BABYLON.CascadedShadowGenerator | null = null;
  if (!lite && q.get('shadows') !== '0') {
    shadow = new BABYLON.CascadedShadowGenerator(2048, sun);
    shadow.numCascades = 3; shadow.lambda = 0.8; shadow.shadowMaxZ = 320; shadow.stabilizeCascades = true; shadow.usePercentageCloserFiltering = true; shadow.filteringQuality = BABYLON.ShadowGenerator.QUALITY_MEDIUM;
    shadow.bias = 0.0006; shadow.normalBias = 0.02; shadow.depthClamp = true; shadow.autoCalcDepthBounds = false; shadow.transparencyShadow = false;
    shadow.getShadowMap()!.refreshRate = 3;   // the cascades are redrawn every third frame
  }

  // ---- terrain ----
  progress(0.15, 'Terrain');
  const first = lookOf(weather.state, { ...preset, hour });
  const terrain = new TerrainView(scene, {
    ground, cell: 1, levels: 10, radius: 26000, split: 1.5, buildsPerUpdate: 3, buildMs: 8, looks: LOOKS, water: false,
    sun: first.sunDir, sunColor: first.sunColor, ambient: first.hemiSky, haze: first.hazeColor, hazeDensity: first.hazeDensity,
    material: (sc) => terrainMaterial(sc, tex, { tex: roadsTexture(sc), box: ROADS_BOX }),
  });
  const pins = pinTerrain(terrain);   // the land of every place the game looks from is built ahead and kept (src/land/terrain-cache.ts)

  // ---- wind: the field everything reads ----
  const wind = new WindField(scene, weather);
  const sway = applyWindSway(scene, wind, []);

  // ---- the street ----
  progress(0.25, 'Street');
  const [sdir, sfile] = split('/art/street/street_level.glb');
  const preMeshes = new Set<BABYLON.AbstractMesh>(scene.meshes);
  const street = await BABYLON.SceneLoader.ImportMeshAsync('', sdir, sfile, scene);
  /** the loader turns a glTF about the vertical (a right-handed file in a left-handed scene); the art is authored with the street along +x and its y as the world's z, so only the mirror stays */
  const upright = (r: BABYLON.AbstractMesh | BABYLON.TransformNode | undefined) => { const root = r?.parent ?? r; if (root && (root as BABYLON.TransformNode).name === '__root__') (root as BABYLON.TransformNode).rotationQuaternion = BABYLON.Quaternion.Identity(); };
  upright(street.meshes[0]);
  for (const m of street.meshes.slice()) if (/^COL_/.test(m.name)) m.dispose();   // collision stand-ins are not drawn
  options.onStreetLoaded?.(street, scene);
  if (q.get('roof') !== 'glb') roofMaterial(scene);   // ?roof=glb shows the glb's own tar for comparison
  const nodes = new Map<string, BABYLON.TransformNode>(); for (const n of street.transformNodes) nodes.set(n.name, n);
  for (const m of street.meshes) if (m.name === 'Ground') m.dispose();                       // the land is the terrain's now: one ground, flat under the set
  for (const m of street.meshes) { m.computeWorldMatrix(true); m.isPickable = false; m.receiveShadows = true; if (m.getTotalVertices() > 0) m.alwaysSelectAsActiveMesh = false; }
  progress(0.5, 'Gas station');
  const [gdir, gfile] = split('/art/gas-station/gas_station_lite.glb');
  const gas = options.gas === 'none' ? null : await BABYLON.SceneLoader.ImportMeshAsync('', gdir, gfile, scene).catch(() => null);
  const anchor = nodes.get('GasStation_Anchor');
  if (gas && anchor) {
    const r = gas.meshes[0]; if (r && !r.getTotalVertices()) { r.parent = anchor; r.position.setAll(0); r.rotationQuaternion = BABYLON.Quaternion.Identity(); r.scaling.set(1, 1, 1); }
    for (const m of gas.meshes.slice()) if (/^COL_/.test(m.name)) m.dispose();
    for (const m of gas.meshes) { m.isPickable = false; m.receiveShadows = true; }
  }

  // ---- fewer, larger draws: the street's thousand parts are merged by cell (80 m along the street), level of detail and material; the swaying trees are merged too, their pivots in the world's frame ----
  progress(0.55, 'Merging');
  const lodOf = (n: BABYLON.Node | null): { base: string; lod: number } | null => { for (; n; n = n.parent) { const mm = n.name.match(/_LOD([01])$/); if (mm) return { base: base(n.name), lod: +mm[1] }; } return null; };
  /** the leaves and the bark carry the baked wind of the model: their pivots are put in world space when merged */
  const isSway = (m: BABYLON.AbstractMesh) => !!m.material && /^(leaf_|leaves$|bark)/.test(m.material.name) && m.isVerticesDataPresent(BABYLON.VertexBuffer.UV5Kind);
  const interiorMaterial = /^(int_|shelfgoods|wincontent|fluor_int|interiors)/;
  // every placement is brought up to date parents first (the street's root was turned above), then each instance's world matrix is read
  const depth = (n: BABYLON.Node) => { let d = 0; for (let p = n.parent; p; p = p.parent) d++; return d; };
  for (const n of [...street.transformNodes, ...street.meshes, ...(gas ? [...gas.transformNodes, ...gas.meshes] : [])].sort((a, b) => depth(a) - depth(b))) (n as BABYLON.TransformNode).computeWorldMatrix(true);
  // the loader makes instances of repeated parts; each becomes a plain mesh sharing the geometry (placed by its world matrix) so that it can be merged like the rest
  type Part = { mesh: BABYLON.Mesh; l: { base: string; lod: number } | null; name: string; from?: BABYLON.AbstractMesh };
  const parts: Part[] = [];
  const underProp = (n: BABYLON.Node | null) => { for (; n; n = n.parent) if (/^DEST_/.test(n.name)) return true; return false; };
  const propNodes = new Map<string, BABYLON.TransformNode>();
  const propLods = new Map<string, { hi?: BABYLON.TransformNode; lo?: BABYLON.TransformNode }>();
  if (options.keepProps) {
    for (const n of [...street.transformNodes, ...street.meshes]) {
      if (/^DEST_.*\d$/.test(n.name)) propNodes.set(n.name, n as BABYLON.TransformNode);
      const mm = n.name.match(/^(DEST_.*)_LOD([01])$/);
      if (mm) { const e = propLods.get(mm[1]) ?? {}; if (mm[2] === '0') e.hi = n as BABYLON.TransformNode; else e.lo = n as BABYLON.TransformNode; propLods.set(mm[1], e); }
    }
  }
  for (const m of scene.meshes.slice()) {
    if (preMeshes.has(m) || m.isDisposed() || m.getTotalVertices() === 0) continue;
    if (options.keepProps && underProp(m)) { m.isPickable = false; m.receiveShadows = true; continue; }
    if (m instanceof BABYLON.InstancedMesh) {
      const src = m.sourceMesh; m.computeWorldMatrix(true);
      const c = src.clone(`${m.name}_part`, null, true); c.parent = null; c.setEnabled(true); if (isSway(src)) c.makeGeometryUnique();
      const sc = new BABYLON.Vector3(), q = new BABYLON.Quaternion(), pos = new BABYLON.Vector3(); m.getWorldMatrix().decompose(sc, q, pos);
      c.scaling.copyFrom(sc); c.rotationQuaternion = q; c.position.copyFrom(pos); c.computeWorldMatrix(true);
      parts.push({ mesh: c, l: lodOf(m), name: m.name, from: m });
    } else if (m instanceof BABYLON.Mesh && !m.hasThinInstances) { m.computeWorldMatrix(true); parts.push({ mesh: m, l: lodOf(m), name: m.name }); }
  }
  for (const { mesh: m } of parts) {
    if (!m.isVerticesDataPresent(BABYLON.VertexBuffer.UV5Kind)) continue;
    if (!isSway(m)) { for (const k of [BABYLON.VertexBuffer.UV2Kind, BABYLON.VertexBuffer.UV3Kind, BABYLON.VertexBuffer.UV4Kind, BABYLON.VertexBuffer.UV5Kind]) if (m.isVerticesDataPresent(k)) m.removeVerticesData(k); continue; }
    // the pivot of a branch (uv4.y, uv5.xy) goes from the mesh's space to the world's
    const w = m.computeWorldMatrix(true), u4 = m.getVerticesData(BABYLON.VertexBuffer.UV4Kind)!.slice(), u5 = m.getVerticesData(BABYLON.VertexBuffer.UV5Kind)!.slice(), v = new BABYLON.Vector3();
    for (let i = 0; i < u4.length / 2; i++) { BABYLON.Vector3.TransformCoordinatesFromFloatsToRef(u4[i * 2 + 1], u5[i * 2], u5[i * 2 + 1], w, v); u4[i * 2 + 1] = v.x; u5[i * 2] = v.y; u5[i * 2 + 1] = v.z; }
    m.setVerticesData(BABYLON.VertexBuffer.UV4Kind, u4, false, 2); m.setVerticesData(BABYLON.VertexBuffer.UV5Kind, u5, false, 2);
  }
  const sides = new Map<string, number>();
  for (const { l } of parts) if (l) sides.set(l.base, (sides.get(l.base) ?? 0) | (1 << l.lod));
  const groups = new Map<string, BABYLON.Mesh[]>();
  for (const { mesh: m, l, name } of parts) {
    const paired = !!l && sides.get(l.base) === 3, c = m.getBoundingInfo().boundingSphere.centerWorld;
    const cls = interiorMaterial.test(m.material?.name ?? '') ? 'i' : l && /^Bld_/.test(l.base) ? 'b' : 'p', cast = /Road_|Ground|Wires/.test(name) ? 'n' : 'c';
    const key = [paired ? l!.lod : 'x', paired || cls === 'i' ? cls : '-', cast, Math.floor(c.x / 80), 0, m.material?.uniqueId ?? 0].join('|');
    const g = groups.get(key); if (g) g.push(m); else groups.set(key, [m]);
  }
  type Cell = { mesh: BABYLON.Mesh; lod: number; limit: number };
  const cells: Cell[] = [], castable: BABYLON.AbstractMesh[] = [];
  let mergeFailed = 0;
  for (const [key, list] of groups) {
    const [lodS, cls, cast] = key.split('|'); let merged: BABYLON.Mesh | null = list[0];
    if (list.length > 1) { try { merged = BABYLON.Mesh.MergeMeshes(list, true, true, undefined, false, false) ?? null; } catch { merged = null; mergeFailed++; } }
    if (!merged) continue;
    merged.name = `merged_${key}`; merged.isPickable = false; merged.receiveShadows = true; merged.alwaysSelectAsActiveMesh = false; merged.computeWorldMatrix(true); merged.freezeWorldMatrix(); merged.doNotSyncBoundingInfo = true;
    if (lodS !== 'x') cells.push({ mesh: merged, lod: +lodS, limit: cls === 'b' ? 130 : cls === 'i' ? 40 : 45 });
    if (cast === 'c' && !/^(int_|shelfgoods|wincontent|fluor_int|interiors|windecals|wallart|shopsigns|glass|paint_dark$)/.test(merged.material?.name ?? '')) castable.push(merged);
  }
  for (const { from } of parts) if (from && !from.isDisposed()) from.dispose();
  for (const m of street.meshes.concat(gas?.meshes ?? [])) if (!m.isDisposed() && m.getTotalVertices() === 0 && m instanceof BABYLON.Mesh && m.getChildren().every(c => c.isDisposed())) m.dispose();   // the emptied parents of the merged parts
  const casters: BABYLON.AbstractMesh[] = [...castable];
  if (options.keepProps) for (const m of scene.meshes) if (!preMeshes.has(m) && !m.isDisposed() && m.getTotalVertices() > 0 && underProp(m)) casters.push(m);
  const boxDistance = (m: BABYLON.AbstractMesh, c: BABYLON.Vector3) => { const b = m.getBoundingInfo().boundingBox.minimumWorld, t = m.getBoundingInfo().boundingBox.maximumWorld; return Math.hypot(Math.max(b.x - c.x, 0, c.x - t.x), Math.max(b.y - c.y, 0, c.y - t.y), Math.max(b.z - c.z, 0, c.z - t.z)); };
  const lodUpdate = () => {
    const c = camera.globalPosition;
    for (const e of propLods.values()) { if (!e.hi || !e.lo) continue; const pos = e.hi.getAbsolutePosition(), near = Math.hypot(pos.x - c.x, pos.y - c.y, pos.z - c.z) < 70; if (e.hi.isEnabled() !== near) { e.hi.setEnabled(near); e.lo.setEnabled(!near); } }
    for (const k of cells) { const near = boxDistance(k.mesh, c) < k.limit, on = k.lod === 0 ? near : !near; if (k.mesh.isEnabled() !== on) k.mesh.setEnabled(on); }
  };
  lodUpdate();
  if (shadow) for (const m of casters) shadow.addShadowCaster(m, false);

  // ---- wind on the street: trees, wires, awnings ----
  progress(0.62, 'Wind');
  for (const m of scene.materials) {
    if (m instanceof BABYLON.PBRMaterial) {
      if (/^(leaf_|leaves$)/.test(m.name)) sway.add(m, { kind: 'tree', flutter: 1, gain: 1, weightsFromColor: false });
      else if (/^bark/.test(m.name)) sway.add(m, { kind: 'tree', flutter: 0, gain: 1, weightsFromColor: false });
      else if (/^cable$/.test(m.name)) sway.add(m, { kind: 'cable', top: 10.0, sag: 0.9, gain: 1 });
      else if (/^awn_/.test(m.name)) sway.add(m, { kind: 'awning', gain: 1 });
    }
  }

  // ---- vegetation: oaks far out, bushes and straw tufts near, stones, and grass in the walk of the camera ----
  progress(0.7, 'Vegetation');
  const oaks = new ScatterView(scene, { ground, species: OAKS, cell: 128, radius: lite ? 700 : 1600, cellsPerUpdate: 2, generators: GENERATORS });
  const bushes = new ScatterView(scene, { ground, species: SHRUBS, cell: 48, radius: lite ? 100 : 200, cellsPerUpdate: 2, generators: GENERATORS });
  const stones = new ScatterView(scene, { ground, species: STONES, generators: STONE_GENERATORS, cell: 64, radius: lite ? 120 : 260, cellsPerUpdate: 1, tint: [1.02, 0.95, 0.84] });
  // ---- while the page loads (the downloads and the decoding leave the main thread idle) the land round the first view is built in slices, so that `start()` finds most of it done ----
  let started = false, warmed = false, first_done = false;
  const warm = () => {
    if (started || warmed) return;
    const c = camera.globalPosition, p: [number, number, number] = [c.x, c.y, c.z], t0 = performance.now();
    if (!first_done) { do { const st = terrain.update(p); oaks.update(p); bushes.update(p); stones.update(p); if (st.pending === 0) { first_done = true; break; } } while (performance.now() - t0 < 12); }
    else if (pins.warm(12)) warmed = true;   // then the land of the other places the game looks from
    if (!warmed) setTimeout(warm, 4);
  };
  setTimeout(warm, 0);

  const plantMat = plantMaterial(scene, wind);
  for (const v of [oaks, bushes]) (v as unknown as { mat: BABYLON.Material }).mat = plantMat;
  /** the dirt roads as segments with their boxes (a metre-wide test against the near ones only): the grass asks thousands of times a frame */
  const segs = DIRT_ROADS.flatMap(r => r.points.slice(0, -1).map((a, i) => { const b = r.points[i + 1]; return { ax: a[0], az: a[1], dx: b[0] - a[0], dz: b[1] - a[1], l2: (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2, half: r.width / 2, x0: Math.min(a[0], b[0]) - 40, x1: Math.max(a[0], b[0]) + 40, z0: Math.min(a[1], b[1]) - 40, z1: Math.max(a[1], b[1]) + 40 }; }));
  const roadDistance = (x: number, z: number) => {
    let best = 1e9;
    for (const s of segs) { if (x < s.x0 || x > s.x1 || z < s.z0 || z > s.z1) continue; const u = Math.max(0, Math.min(1, ((x - s.ax) * s.dx + (z - s.az) * s.dz) / s.l2)); best = Math.min(best, Math.hypot(x - s.ax - s.dx * u, z - s.az - s.dz * u) - s.half); }
    return best;
  };
  const rockMat = plantMaterial(scene, wind, 0);
  const surround = buildSurround(scene, rockMat, plantMat, { seed: 1987, ground: groundAt, roadDistance });
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
    terrain.setLight(look.sunDir, [look.sunColor[0] * look.sunIntensity * 0.36, look.sunColor[1] * look.sunIntensity * 0.36, look.sunColor[2] * look.sunIntensity * 0.36],
      [look.hemiSky[0] * look.hemiIntensity * 0.3, look.hemiSky[1] * look.hemiIntensity * 0.3, look.hemiSky[2] * look.hemiIntensity * 0.3], look.hazeColor);
    terrain.setHaze(look.hazeColor, look.hazeDensity);
    plantMat.light(look.sunDir, [look.sunColor[0] * look.sunIntensity * 0.22, look.sunColor[1] * look.sunIntensity * 0.22, look.sunColor[2] * look.sunIntensity * 0.22], [look.hemiSky[0] * look.hemiIntensity * 0.42, look.hemiSky[1] * look.hemiIntensity * 0.42, look.hemiSky[2] * look.hemiIntensity * 0.42], look.hazeColor, look.hazeDensity);
    rockMat.light(look.sunDir, [look.sunColor[0] * look.sunIntensity * 0.22, look.sunColor[1] * look.sunIntensity * 0.22, look.sunColor[2] * look.sunIntensity * 0.22], [look.hemiSky[0] * look.hemiIntensity * 0.42, look.hemiSky[1] * look.hemiIntensity * 0.42, look.hemiSky[2] * look.hemiIntensity * 0.42], look.hazeColor, look.hazeDensity);
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
    sunsetFromEnd: view(540, 1.5, 2.5, 380, 5, 0, 0.9),
    street: view(-48, 8.5, -0.5, 120, 5, 0, 0.85),
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
  let frame = 0, lodAt = 0, terrainAt = -1; let terrainPos: [number, number, number] = [1e9, 0, 0];
  scene.onBeforeRenderObservable.add(() => {
    const dt = Math.min(0.1, engine.getDeltaTime() / 1000), t = world.time, c = camera.globalPosition, cp: [number, number, number] = [c.x, c.y, c.z];
    const tm = <R,>(_k: string, f: () => R): R => f();
    if (t - terrainAt > 0.25 || Math.hypot(cp[0] - terrainPos[0], cp[1] - terrainPos[1], cp[2] - terrainPos[2]) > 2) { terrainAt = t; terrainPos = cp; tm('terrain', () => terrain.update(cp)); } tm('oaks', () => oaks.update(cp)); tm('bushes', () => bushes.update(cp)); tm('stones', () => stones.update(cp)); if (++frame % 3 === 0) tm('grass', () => grass.update());   // the wave texture is solved on the CPU: a third of the frames are enough for a wave that slow tm('clouds', () => clouds.update(cp, t));
    if (t - lastLook > 0.5) { lastLook = t; tm('look', applyLook); }
    if (t - lodAt > 0.2) { lodAt = t; tm('lod', lodUpdate); }
    tm('flags', () => { for (const f of flags) f.update(dt); });
    tm('litter', () => litter.update(dt, c.x, c.z));
  });

  const api: SetHandle = {
    game, scene, weather, camera, ground, groundAt, terrain, wind, look: () => look, get preset() { return preset; }, get presetName() { return presetName; },
    renderer() {
      const gl = (engine as BABYLON.Engine)._gl as WebGL2RenderingContext, ext = gl.getExtension('WEBGL_debug_renderer_info');
      return { vendor: ext ? String(gl.getParameter(ext.UNMASKED_VENDOR_WEBGL)) : String(gl.getParameter(gl.VENDOR)), renderer: ext ? String(gl.getParameter(ext.UNMASKED_RENDERER_WEBGL)) : String(gl.getParameter(gl.RENDERER)), version: String(gl.getParameter(gl.VERSION)) };
    },
    setHour(h) { hour = h; applyLook(); },
    setWeather(name) { const w = weatherPreset(name); presetName = w.name; preset = w.preset; hour = preset.hour; weather.set(preset.base, preset.state); applyLook(); },
    views, shadow, propNodes, street,
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
    start() { if (started) return; started = true; const cp = camera.globalPosition, p: [number, number, number] = [cp.x, cp.y, cp.z]; const t0 = performance.now(); for (let i = 0; i < 400 && performance.now() - t0 < PRIME_MS; i++) { const s = terrain.update(p); oaks.update(p); bushes.update(p); stones.update(p); if (s.pending === 0) break; } lodUpdate(); const tp = performance.now(); while (performance.now() - tp < PINS_MS && !warmed) { if (pins.warm(50)) warmed = true; } { const c0 = camera.globalPosition; terrain.update([c0.x, c0.y, c0.z]); } game.start(); },
    stats() {
      const s = terrain.stats();
      return { chunks: s.chunks, triangles: s.triangles, levels: JSON.stringify(s.levels), oaks: oaks.count(), surround: surround.count, pinned: pins.built + '/' + pins.total + ' ' + pins.ms + 'ms', bushes: bushes.count(), stones: stones.count(), grass: grass.drawn, litter: litter.airborne, sway: sway.materials, bakedTrees: scene.meshes.filter(m => m.isVerticesDataPresent(BABYLON.VertexBuffer.UV5Kind)).length, mergeFailed, merged: cells.length + castable.length, meshes: scene.meshes.length, active: scene.getActiveMeshes().length, fps: Math.round(engine.getFps()) };
    },
  };
  scene.onBeforeRenderObservable.add(() => { if (!warmed && started) { if (pins.warm(5)) warmed = true; const c0 = camera.globalPosition; terrain.update([c0.x, c0.y, c0.z]); } });   // the view of the camera is put back at once
  progress(0.9, 'Terrain');
  { const v0 = views().cab; aim(camera, v0.position, v0.target, v0.fov); }
  void WEATHER; void power;
  if (!options.deferStart) api.start();
  progress(1, 'Ready');
  return api;
}
