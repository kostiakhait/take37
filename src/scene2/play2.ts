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
import { MOLE, bed, deckHeight, tide, onMole } from './shore';

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

  engine.runRenderLoop(() => {
    const dt = Math.min(0.1, engine.getDeltaTime() / 1000);
    if (!paused) clock += dt;
    const level = tide(clock, TIDE_PHASE);
    const sp = (keys.has('shift') ? 4.5 : 1) * fly.speed * dt, cy = Math.cos(fly.yaw), sy = Math.sin(fly.yaw), cp = Math.cos(fly.pitch), spf = Math.sin(fly.pitch);
    const mv = (keys.has('w') ? 1 : 0) - (keys.has('s') ? 1 : 0), st = (keys.has('d') ? 1 : 0) - (keys.has('a') ? 1 : 0), ud = (keys.has('e') ? 1 : 0) - (keys.has('q') ? 1 : 0);
    const nx = fly.p[0] + (sy * cp * mv + cy * st) * sp, nz = fly.p[2] + (cy * cp * mv - sy * st) * sp, ny = fly.p[1] + (spf * mv + ud) * sp;
    fly.p = [nx, Math.max(ny, floor(nx, nz, level)), nz];
    cam.position.copyFromFloats(fly.p[0], fly.p[1], fly.p[2]);
    cam.setTarget(new BABYLON.Vector3(fly.p[0] + sy * cp, fly.p[1] + spf, fly.p[2] + cy * cp)); cam.fov = fly.fov;
    const c = cam.globalPosition;
    dunes.update(c);
    skyDome.update(clock); sea.update(clock, level, c); beach.update(c, Math.min(2600, weather.visibility * 2.6 + 400)); beach.tick(c, level, clock);
    game.world.advance(dt);
    scene.render();
  });

  (globalThis as unknown as { __scene2: unknown }).__scene2 = { scene, engine, cam, beach, sea, mole, dunes, fly, MOLE, bed, tide,
    setTime: (t: number) => { clock = t; }, pause: (p: boolean) => { paused = p; },
    free: (p: V3, t: V3, fov = 0.95) => { fly.p = [p[0], p[1], p[2]]; const d = [t[0] - p[0], t[1] - p[1], t[2] - p[2]]; fly.yaw = Math.atan2(d[0], d[2]); fly.pitch = Math.atan2(d[1], Math.hypot(d[0], d[2])); fly.fov = fov; },
    renderer: () => { try { const gl = (engine as unknown as { _gl: WebGLRenderingContext })._gl; const x = gl.getExtension('WEBGL_debug_renderer_info'); return x ? String(gl.getParameter(x.UNMASKED_RENDERER_WEBGL)) : String(gl.getParameter(gl.RENDERER)); } catch { return '?'; } } };
  Object.assign(globalThis, { ferretGame: game, ferretReady: true });
  splash.set(1, 'Ready');
  const warm = () => { if (beach.settled || performance.now() > 60000) splash.hide(); else requestAnimationFrame(warm); };
  warm();
}
main().catch(e => { console.error(e); (globalThis as unknown as { ferretError: string }).ferretError = String(e?.message ?? e); const t = document.getElementById('splashtxt'); if (t) t.textContent = 'Error: ' + (e?.message ?? e); });
