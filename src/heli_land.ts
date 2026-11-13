// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
/**
 * The field of scene 3 as a check: the Zeppelin sample's land (100 x 100 km, terrain quadtree around the camera, forest scatter, lakes, sites, the airfield's flat strip) with a coast and the sea (airwar's Sea) opened to the east,
 * the R22 standing on the strip. Address: `?cam=ground|close|walk|alt400|alt2k|alt10k|coast|sea|runway`, `?hour=` (clock), `?lite=1`, `?clean=1`; `window.land` has `ready`, `metrics()`, `camAt(x,y,z,tx,ty,tz)`.
 */
import { AIRFIELD, Terrain, addLakes } from '/D:/REPO/ferret/examples/zeppelin/src/world/terrain';
import { Forest } from '/D:/REPO/ferret/examples/zeppelin/src/world/forest';
import { SITES } from '/D:/REPO/ferret/examples/zeppelin/src/world/sites';
import { skyCube, skyDome } from '/D:/REPO/ferret/examples/zeppelin/src/look';
import { Sea } from '/D:/REPO/ferret/examples/airwar/src/world/sea';
import { groundHeight, coastX } from './heli_land_height';

declare const BABYLON: typeof import('@babylonjs/core');
const q = new URLSearchParams(location.search);
const win = window as unknown as Record<string, unknown>;

async function main() {
  const lite = q.get('lite') === '1';
  const canvas = document.getElementById('c') as HTMLCanvasElement;
  const engine = new BABYLON.Engine(canvas, true, { preserveDrawingBuffer: true, stencil: true });
  const gl = engine._gl as WebGL2RenderingContext, dbg = gl.getExtension('WEBGL_debug_renderer_info');
  const renderer = dbg ? String(gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL)) : 'unknown';
  const scene = new BABYLON.Scene(engine);
  const hour = parseFloat(q.get('hour') ?? '11'), sunset = hour >= 17.5;
  // the sun: high in the south-west by day; at sunset low in the west, so the flight east over the sea has the sun behind it
  const elev = sunset ? 0.12 : Math.max(0.25, Math.sin(Math.PI * (hour - 6) / 14) * 1.05);
  const toSun: [number, number, number] = sunset ? [-Math.cos(elev) * 0.97, Math.sin(elev), 0.2] : [-0.4, elev, 0.5].map((v, i, a) => v / Math.hypot(a[0]!, a[1]!, a[2]!)) as [number, number, number];
  const cover = 0.3;
  scene.fogMode = BABYLON.Scene.FOGMODE_EXP2; scene.fogDensity = sunset ? 0.000028 : 0.000022; scene.fogColor = sunset ? new BABYLON.Color3(0.82, 0.6, 0.45) : new BABYLON.Color3(0.7, 0.8, 0.92);
  scene.clearColor = new BABYLON.Color4(...(scene.fogColor.asArray() as [number, number, number]), 1);
  scene.imageProcessingConfiguration.toneMappingEnabled = true; scene.imageProcessingConfiguration.exposure = sunset ? 0.9 : 1.0;
  const hemi = new BABYLON.HemisphericLight('sky', new BABYLON.Vector3(0.1, 1, 0.2), scene); hemi.intensity = sunset ? 0.45 : 0.8; hemi.groundColor = new BABYLON.Color3(0.35, 0.4, 0.3);
  const sun = new BABYLON.DirectionalLight('sun', new BABYLON.Vector3(-toSun[0], -toSun[1], -toSun[2]), scene); sun.intensity = sunset ? 1.4 : 1.8; sun.diffuse = sunset ? new BABYLON.Color3(1, 0.68, 0.42) : new BABYLON.Color3(1, 0.97, 0.9);
  const dome = skyDome(scene, toSun, cover); void dome;
  scene.environmentTexture = skyCube(scene, toSun, cover); scene.environmentIntensity = sunset ? 0.7 : 1.0;
  const shadows = new BABYLON.ShadowGenerator(2048, sun); shadows.usePercentageCloserFiltering = true; shadows.bias = 0.0008; shadows.normalBias = 0.02; shadows.darkness = 0.35; sun.autoUpdateExtends = false; sun.shadowFrustumSize = 60; sun.shadowMinZ = 1; sun.shadowMaxZ = 400;

  const t0 = performance.now();
  const terrain = new Terrain(scene, { perFrame: 4, shadows: !lite });
  addLakes(scene);
  const forest = new Forest(scene, { scale: 1, perFrame: 6 });
  let simT = 0;
  const sea = new Sea(scene, { skyTop: [0.20, 0.42, 0.82], skyHorizon: [0.80, 0.87, 0.95], sunDir: toSun, sunColor: sunset ? [1, 0.7, 0.45] : [1, 0.95, 0.85], clock: () => simT });
  sea.setWind(6, 250); sea.setLight(toSun, sunset ? [1, 0.7, 0.45] : [1, 0.95, 0.85]); sea.setFog(scene.fogColor, scene.fogDensity);

  // the airfield strip (as the sample lays it: 70 x 1300 m, heading AIRFIELD.heading) with the R22 on it
  const strip = BABYLON.MeshBuilder.CreateGround('runway', { width: 70, height: 1300 }, scene);
  strip.position.set(AIRFIELD.x, AIRFIELD.elevation + 0.35, AIRFIELD.z); strip.rotation.y = AIRFIELD.heading;
  const sm = new BABYLON.StandardMaterial('sm', scene); sm.specularColor = new BABYLON.Color3(0.05, 0.05, 0.05); sm.diffuseColor = new BABYLON.Color3(0.30, 0.29, 0.27); sm.zOffset = -2; strip.material = sm; strip.receiveShadows = true;
  const res = await BABYLON.SceneLoader.ImportMeshAsync('', '/assets/borrowed/', q.get('lod') === '1' ? 'r22_lod1.glb' : 'r22.glb', scene);
  const holder = new BABYLON.TransformNode('r22', scene); res.meshes[0]!.parent = holder;
  holder.position.set(AIRFIELD.x + Math.sin(AIRFIELD.heading) * 40, AIRFIELD.elevation + 0.4, AIRFIELD.z + Math.cos(AIRFIELD.heading) * 40); holder.rotationQuaternion = BABYLON.Quaternion.RotationAxis(BABYLON.Axis.Y, AIRFIELD.heading - Math.PI / 2);
  for (const m of res.meshes) { if (m.name.startsWith('Collider_')) m.setEnabled(false); else if ((m as BABYLON.Mesh).getTotalVertices?.() > 0) { shadows.addShadowCaster(m); m.receiveShadows = true; } }
  for (const n of [...scene.transformNodes, ...scene.meshes]) if ((n.metadata as { gltf?: { extras?: { state?: string } } } | null)?.gltf?.extras?.state === 'damaged') n.setEnabled(false);
  if (q.get('dbg') === 'noshadow') for (const m of res.meshes) m.receiveShadows = false;
  if (q.get('dbg') === 'noenv') for (const m of res.meshes) { const mm = m.material as BABYLON.PBRMaterial | null; if (mm) mm.environmentIntensity = 0; }
  if (q.get('dbg') === 'nocol') for (const m of res.meshes) m.useVertexColors = false;
  const spinN = scene.getTransformNodeByName('Rotor_Spin'); let spin = 0; const spinOn = q.get('spin') === '1';
  const blurDiscs = ['Rotor_Disc', 'TailRotor_Disc'].map((n) => scene.getTransformNodeByName(n) ?? scene.getMeshByName(n));
  for (const d of blurDiscs) d?.setEnabled(false);
  const q0 = spinN?.rotationQuaternion?.clone();
  const hp = holder.position;

  const cam = new BABYLON.FreeCamera('cam', new BABYLON.Vector3(0, 0, 0), scene); cam.minZ = 0.1; cam.maxZ = 120000; cam.fov = 0.9; cam.attachControl(canvas, true);
  const camAt = (x: number, y: number, z: number, tx: number, ty: number, tz: number, fov = 0.9) => { cam.position.set(x, y, z); cam.setTarget(new BABYLON.Vector3(tx, ty, tz)); cam.fov = fov; };
  const dir = [Math.sin(AIRFIELD.heading), Math.cos(AIRFIELD.heading)] as const, side = [Math.cos(AIRFIELD.heading), -Math.sin(AIRFIELD.heading)] as const;
  const at = (a: number, s: number) => [hp.x + dir[0] * a + side[0] * s, hp.z + dir[1] * a + side[1] * s] as const;
  const gy = hp.y;
  const presets: Record<string, () => void> = {
    ground: () => { const [x, z] = at(-14, 9); camAt(x, gy + 1.7, z, hp.x, gy + 1.3, hp.z, 0.8); },
    close: () => { const [x, z] = at(-3, 4.5); camAt(x, gy + 1.5, z, hp.x, gy + 1.2, hp.z, 0.9); },
    walk: () => { const [x, z] = at(-9, -6); camAt(x, gy + 1.6, z, hp.x, gy + 1.3, hp.z, 0.85); },
    runway: () => { const [x, z] = at(-120, 6); camAt(x, gy + 2.2, z, hp.x + dir[0] * 400, gy + 20, hp.z + dir[1] * 400, 0.9); },
    alt400: () => { const [x, z] = at(-500, 150); camAt(x, gy + 400, z, hp.x + 1200, gy + 50, hp.z + 200, 0.95); },
    alt2k: () => { const [x, z] = at(-1800, 400); camAt(x, gy + 2000, z, hp.x + 8000, 200, hp.z + 1000, 1.0); },
    alt10k: () => camAt(AIRFIELD.x - 4000, 10000, AIRFIELD.z - 12000, AIRFIELD.x + 22000, 300, AIRFIELD.z + 4000, 1.05),
    coast: () => { const z = -3000; camAt(coastX(z) - 6000, 700, z - 1500, coastX(z) + 3000, 0, z, 1.0); },
    sea: () => { const z = -3000; camAt(coastX(z) - 900, 90, z, coastX(z) + 20000, 20, z + 3000, 0.95); },
  };
  (presets[q.get('cam') ?? 'ground'] ?? presets.ground!)();
  win.__cam = cam;

  // measurements: milliseconds the terrain, the forest and the sea cost per frame (their update calls), the whole frame, the chunks and the trees
  const acc = { terrain: 0, forest: 0, sea: 0, frames: 0, worst: 0 };
  scene.onBeforeRenderObservable.add(() => {
    simT += engine.getDeltaTime() / 1000;
    const p: [number, number, number] = [cam.position.x, cam.position.y, cam.position.z];
    let t = performance.now(); terrain.update(p); const a = performance.now() - t; t = performance.now(); forest.update(p); const b = performance.now() - t; t = performance.now(); sea.update(p); const c = performance.now() - t;
    acc.terrain += a; acc.forest += b; acc.sea += c; acc.frames++; acc.worst = Math.max(acc.worst, a + b + c);
    if (spinN && q0 && spinOn) { spin += engine.getDeltaTime() / 1000 * 6; spinN.rotationQuaternion = q0.multiply(BABYLON.Quaternion.RotationAxis(BABYLON.Axis.Y, spin)); }
  });
  win.land = {
    renderer, ready: false, camAt, preset: (n: string) => (presets[n] ?? presets.ground!)(), reset: () => { acc.terrain = acc.forest = acc.sea = acc.frames = acc.worst = 0; },
    metrics: () => ({ renderer, fps: engine.getFps(), frames: acc.frames, terrainMs: acc.terrain / Math.max(1, acc.frames), forestMs: acc.forest / Math.max(1, acc.frames), seaMs: acc.sea / Math.max(1, acc.frames), worstUpdateMs: acc.worst, chunks: terrain.stats, settled: terrain.settled, trees: forest.count, activeMeshes: scene.getActiveMeshes().length, drawCalls: engine.drawCalls ?? null, sites: SITES.length, loadMs: Math.round(performance.now() - t0) }),
    ground: groundHeight, coastX,
  };
  if (q.get('clean') === '1') document.body.classList.add('clean');
  engine.runRenderLoop(() => scene.render());
  window.addEventListener('resize', () => engine.resize());
  // let the quadtree and the forest settle behind the first frames
  const t1 = performance.now(); while (!terrain.settled && performance.now() - t1 < 1) { /* one frame at a time is done by the loop */ }
  (win.land as { ready: boolean }).ready = true;
  document.getElementById('hud')!.textContent = `R22 field  ${renderer}  ${(globalThis as { __BUILD__?: string }).__BUILD__ ?? ''}`;
}
main().catch((e) => { console.error(e); win.landError = String(e); });
