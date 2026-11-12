// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import { buildSet } from './scene/set';
import { InputService } from '@ferret/input';
import { glbJson, nodeInfos } from './game/glbinfo';
import { parseLayout, type Layout } from './game/layout';
import { Take, type PlayerInput } from './game/take';
import { GameView } from './game/view';
import { Hud, HUD_CSS } from './game/hud';
import { CabAudio } from './game/audio';
import { ACTIONS, BINDINGS, CAR_KINDS, FIXED_DT, type KindId } from './game/config';
import { qRot } from '@ferret/destruction/vehicle';
import type { KindInfos } from './game/scene1';

/**
 * Scene 1 of TAKE 37, the playable part: the set (src/scene/set.ts) with the full gas station, the cars, the chase, the destruction and the take flow.
 * Address options: set.ts options (`?weather=`, `?hour=`, `?lite=1`), `?seed=N` (the take's variations), `?auto=1` (no briefing wait, for the runs), `?clean=1`.
 */
const $ = (id: string) => document.getElementById(id)!;
const q = new URLSearchParams(location.search);
const splash = {
  set(p: number, text: string) { const b = document.getElementById('splashbar'), t = document.getElementById('splashtxt'); if (b) b.style.width = Math.round(p * 100) + '%'; if (t) t.textContent = text; },
  hide() { const e = document.getElementById('splash'); if (e) { e.classList.add('gone'); setTimeout(() => e.remove(), 900); } },
};
const win = window as unknown as Record<string, unknown>;

async function bytes(url: string): Promise<ArrayBuffer> { const r = await fetch(url); if (!r.ok) throw new Error(url + ' ' + r.status); return r.arrayBuffer(); }

/**
 * The set's own loader reads the street and a light gas station. Two things are adjusted from outside, without touching it: the light station is not loaded (the game's full one stands in its place), and the
 * street's destructible props are kept out of the merge by the set (they are renamed under a node the set leaves alone) so that the game can move them.
 */
function prepareLoader(propNodes: Map<string, BABYLON.TransformNode>) {
  const orig = BABYLON.SceneLoader.ImportMeshAsync.bind(BABYLON.SceneLoader) as (...a: unknown[]) => Promise<BABYLON.ISceneLoaderAsyncResult>;
  (BABYLON.SceneLoader as unknown as { ImportMeshAsync: unknown }).ImportMeshAsync = async (...a: unknown[]) => {
    const file = String(a[2] ?? '');
    if (/gas_station_lite/.test(file)) return { meshes: [], particleSystems: [], skeletons: [], animationGroups: [], transformNodes: [], geometries: [], lights: [], spriteManagers: [] } as unknown as BABYLON.ISceneLoaderAsyncResult;
    const r = await orig(...a);
    if (/street_level/.test(file)) for (const n of r.transformNodes) if (/^DEST_[A-Za-z]+_\d+$/.test(n.name)) { propNodes.set(n.name, n); n.name = 'StreetTree_' + n.name; }
    return r;
  };
}

async function main() {
  $('splashver').textContent = (globalThis as { __TAKE37_BUILD__?: string }).__TAKE37_BUILD__ ?? '';
  const propNodes = new Map<string, BABYLON.TransformNode>(), stationNodes = new Map<string, BABYLON.TransformNode>();
  prepareLoader(propNodes);
  const set = await buildSet($('c') as HTMLCanvasElement, q, (p, t) => splash.set(p * 0.6, t));
  const { scene, camera } = set;
  camera.detachControl();

  // ---- the art's data: layout of the street and the station, the nodes of every car ----
  splash.set(0.62, 'Layout');
  const [street, cols, gasBuf] = await Promise.all([bytes('/art/street/street_level.glb'), bytes('/art/street/street_colliders.glb'), bytes('/art/gas-station/gas_station.glb')]);
  const layout: Layout = parseLayout(street, cols, gasBuf);
  const infos: KindInfos = {};
  const kinds = Object.keys(CAR_KINDS) as KindId[];
  for (const k of kinds) infos[k] = nodeInfos(glbJson(await bytes(CAR_KINDS[k].glb)));

  // ---- the full gas station on the street, turned away from the road (as the layout has it) ----
  splash.set(0.68, 'Gas station');
  const anchor = new BABYLON.TransformNode('GasStation_Game', scene);
  anchor.position.set(layout.station.origin[0], layout.station.origin[1], layout.station.origin[2]);
  anchor.rotationQuaternion = BABYLON.Quaternion.RotationAxis(BABYLON.Axis.Y, Math.PI / 2);
  const gas = await BABYLON.SceneLoader.ImportMeshAsync('', '/art/gas-station/', 'gas_station.glb', scene);
  const groot = gas.meshes[0]!.parent ?? gas.meshes[0]!; (groot as BABYLON.TransformNode).rotationQuaternion = BABYLON.Quaternion.Identity(); groot.parent = anchor;
  for (const m of gas.meshes.slice()) if (/^COL_/.test(m.name)) m.dispose();
  const sun = scene.getLightByName('sun') as BABYLON.DirectionalLight | null;
  for (const m of gas.meshes) if (!m.isDisposed()) { m.isPickable = false; m.receiveShadows = true; if (m.getTotalVertices() > 0) sun?.getShadowGenerator()?.addShadowCaster(m, false); }
  for (const n of gas.transformNodes) stationNodes.set(n.name, n);
  for (const m of gas.meshes) stationNodes.set(m.name, m as unknown as BABYLON.TransformNode);

  // ---- the game ----
  const view = new GameView(scene, camera, propNodes, stationNodes);
  view.setInfos(infos);
  const total = kinds.length;
  await view.loadModels(kinds, (i, n, what) => splash.set(0.72 + 0.26 * i / n, 'Cars: ' + what));
  const mem = new Map<string, string>();
  const store = { get: (k: string) => { try { return localStorage.getItem(k); } catch { return mem.get(k) ?? null; } }, set: (k: string, v: string) => { try { localStorage.setItem(k, v); } catch { mem.set(k, v); } } };
  if (q.get('fresh') === '1') for (const k of ['take37.budget', 'take37.takes', 'take37.scene1.best']) { try { localStorage.removeItem(k); } catch { /* none */ } }
  const take = new Take(layout, infos, store);
  const input = new InputService({ actions: ACTIONS as never, bindings: BINDINGS as never });
  input.attach($('c'));
  const hudRoot = document.createElement('div'); hudRoot.id = 'hud2'; document.body.appendChild(hudRoot);
  const style = document.createElement('style'); style.textContent = HUD_CSS; document.head.appendChild(style);
  const hud = new Hud(hudRoot), audio = new CabAudio();
  addEventListener('keydown', () => audio.start()); addEventListener('pointerdown', () => audio.start());

  const seed = q.has('seed') ? +q.get('seed')! : 0;
  const begin = () => { take.begin(seed); view.startTake(take); view.setView({ mode: 'cab' }); verdictShown = false; if (q.get('auto') === '1') take.phaseT = 99; };
  let verdictShown = false, paused = false, acc = 0, yaw = 0, pitch = 0, idle = 0;
  if (take.phase !== 'over') begin();

  const inp: PlayerInput = { gas: false, brake: false, steer: 0, handbrake: false, jump: false, cut: false, horn: false, siren: false };
  let sirenOn = false;
  scene.onBeforeRenderObservable.add(() => {
    const dt = Math.min(0.1, scene.getEngine().getDeltaTime() / 1000);
    input.update();
    if (!paused) acc += dt;
    while (acc >= FIXED_DT) {
      acc -= FIXED_DT;
      input.fixedUpdate();
      if (input.pressed('pause') && take.phase === 'play') { paused = !paused; if (paused) { acc = 0; break; } }
      if (input.pressed('accept') && (take.phase === 'choice' || take.phase === 'over')) { if (take.phase === 'over') { for (const k of ['take37.budget', 'take37.takes']) store.set(k, ''); take.budget = 15_000_000; take.takeNo = 0; } begin(); }
      if (input.pressed('siren')) sirenOn = !sirenOn;
      const st = input.axis('steer'), lk = input.axis('look');
      inp.gas = input.down('gas'); inp.brake = input.down('brake'); inp.steer = -st.x; inp.handbrake = input.down('handbrake');
      inp.jump = input.pressed('jump'); inp.cut = input.pressed('cut'); inp.horn = input.down('horn'); inp.siren = sirenOn;
      const pad = input.kind === 'gamepad';
      yaw += pad ? lk.x * 2.4 * FIXED_DT : lk.x; pitch += pad ? lk.y * 1.6 * FIXED_DT : lk.y;
      idle = Math.abs(lk.x) + Math.abs(lk.y) > 0.001 ? 0 : idle + FIXED_DT;
      if (idle > 1.2) { yaw *= 0.97; pitch *= 0.97; }
      yaw = Math.max(-2.0, Math.min(2.0, yaw)); pitch = Math.max(-0.7, Math.min(0.7, pitch));
      take.step(inp); take.siren = sirenOn; view.stepFx(FIXED_DT);
      const evs = take.takeEvents(); view.push(evs);
      for (const e of evs) { const at = (e as { at?: number[] }).at; if (at) audio.hear(e, Math.hypot(at[0]! - take.player.veh.pos[0], at[2]! - take.player.veh.pos[2])); }
    }
    if (take.phase === 'verdict' && !verdictShown) { verdictShown = true; view.setView({ mode: 'set', set: view.bestSetCamera(take) }); }
    const car = take.player, f = qRot(car.veh.rot, [1, 0, 0]), v = car.veh.vel[0] * f[0] + car.veh.vel[2] * f[2];
    view.frame(take, dt, { yaw, pitch, back: input.down('lookback') });
    audio.update(v, car.ctl.throttle, inp.horn, sirenOn, take.t);
    hud.update(take, v, paused, (a) => input.prompt(a));
  });

  win.take37 = Object.assign(set, { take, view, layout, input, paused: () => paused, stationNodes, propNodes, begin, setPaused: (p: boolean) => { paused = p; } });
  win.take37Ready = true;
  void total;
  splash.hide();
}
main().catch((e) => { console.error(e); win.take37Error = String((e as Error)?.stack ?? e); });
