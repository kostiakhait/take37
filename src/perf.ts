// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// The performance overlay and the render-scale governor. Loaded by src/loading.ts, so no other file has to call it.
//   ?perf=1        the overlay (top right): fps, frame ms (mean / p95 / worst of the last 120 frames), CPU ms of the render call, GPU ms (when the browser gives timer queries), draw calls, active meshes,
//                  triangles, the game's own costs (take.step, view.frame, view.stepFx, ms per frame) and a budget table with a red mark for every line that is over its budget
//   ?gov=1         the governor: when the p95 frame time stays over 20 ms the render scale drops (hardware scaling up to 1.5), when it stays under 13 ms it comes back (default on in the page, ?gov=0 off)
//   window.take37Perf.snapshot()   the same numbers as an object, for scripts and tests;  .toggle('shadows'|'post'|'terrain'|'vfx'|'props', on?)  switches a cost off to measure it (A/B in one run);
//   window.take37Perf.budget       the budget table (edit a value to change the line)
// Everything reads the scene through window.take37 (set by src/play.ts when the page is ready).

interface Snapshot { fps: number; ms: { mean: number; p95: number; worst: number }; cpuRender: number; gpu: number | null; drawCalls: number; activeMeshes: number; triangles: number; meshes: number; materials: number; textures: number; scale: number; game: Record<string, number> }

export const BUDGET: Record<string, number> = { 'frame p95 ms': 16.7, 'cpu render ms': 8, 'gpu ms': 12, 'draw calls': 1500, 'triangles (k)': 2500, 'take.step ms': 2, 'view.frame ms': 2, 'view.stepFx ms': 1.5, 'meshes': 2500 };

const q = new URLSearchParams(location.search);
const win = window as unknown as Record<string, unknown>;

function install(): void {
  const t37 = win.take37 as { scene: BABYLON.Scene; take: { step: (...a: unknown[]) => unknown }; view: { frame: (...a: unknown[]) => unknown; stepFx: (...a: unknown[]) => unknown }; shadow?: BABYLON.CascadedShadowGenerator | null; propNodes?: unknown } | undefined;
  if (!t37?.scene) return;
  const scene = t37.scene, engine = scene.getEngine();
  const inst = new BABYLON.SceneInstrumentation(scene);
  inst.captureFrameTime = true; inst.captureRenderTime = true;
  try { if (engine.getCaps().timerQuery) inst.captureGPUFrameTime = true; } catch { /* no timer queries */ }
  const frames: number[] = [], cost: Record<string, number[]> = { 'take.step': [], 'view.frame': [], 'view.stepFx': [] }, acc: Record<string, number> = { 'take.step': 0, 'view.frame': 0, 'view.stepFx': 0 };
  const wrap = (obj: Record<string, unknown>, name: string, key: string) => { const f = obj[name] as (...a: unknown[]) => unknown; obj[name] = function (this: unknown, ...a: unknown[]) { const t = performance.now(); const r = f.apply(this, a); acc[key]! += performance.now() - t; return r; }; };
  wrap(t37.take as unknown as Record<string, unknown>, 'step', 'take.step'); wrap(t37.view as unknown as Record<string, unknown>, 'frame', 'view.frame'); wrap(t37.view as unknown as Record<string, unknown>, 'stepFx', 'view.stepFx');
  scene.onAfterRenderObservable.add(() => {
    frames.push(engine.getDeltaTime()); if (frames.length > 120) frames.shift();
    for (const k of Object.keys(acc)) { cost[k]!.push(acc[k]!); if (cost[k]!.length > 120) cost[k]!.shift(); acc[k] = 0; }
  });
  const pct = (a: number[], p: number) => { if (!a.length) return 0; const s = [...a].sort((x, y) => x - y); return s[Math.min(s.length - 1, Math.floor(s.length * p))]!; };
  const mean = (a: number[]) => (a.length ? a.reduce((x, y) => x + y, 0) / a.length : 0);
  const snapshot = (): Snapshot => ({
    fps: Math.round(engine.getFps()), ms: { mean: +mean(frames).toFixed(1), p95: +pct(frames, 0.95).toFixed(1), worst: +Math.max(0, ...frames).toFixed(1) },
    cpuRender: +inst.renderTimeCounter.lastSecAverage.toFixed(2) || +inst.renderTimeCounter.current.toFixed(2),
    gpu: inst.captureGPUFrameTime ? +(inst.gpuFrameTimeCounter.lastSecAverage / 1e6).toFixed(2) : null,
    drawCalls: inst.drawCallsCounter.current, activeMeshes: scene.getActiveMeshes().length, triangles: Math.round(scene.getActiveIndices() / 3), meshes: scene.meshes.length, materials: scene.materials.length, textures: scene.textures.length,
    scale: engine.getHardwareScalingLevel(), game: Object.fromEntries(Object.entries(cost).map(([k, v]) => [k, +mean(v).toFixed(2)])),
  });
  // ---- switches to measure what a cost is ----
  const saved: Record<string, unknown> = {};
  const toggle = (what: string, on?: boolean): boolean => {
    const cur = saved[what] === undefined; const want = on ?? !cur;   // cur: the cost is on
    if (want === cur) return cur;
    if (what === 'shadows') { const sg = t37.shadow; if (sg) { const sm = sg.getShadowMap()!; if (!want) { saved[what] = sm.refreshRate; sm.refreshRate = 0; sm.renderList = []; } else { sm.refreshRate = saved[what] as number; delete saved[what]; } } }
    else if (what === 'post') { const p = scene.postProcessRenderPipelineManager.supportedPipelines[0]; if (p) { if (!want) { saved[what] = true; scene.postProcessRenderPipelineManager.detachCamerasFromRenderPipeline(p.name, scene.activeCamera!); } else { scene.postProcessRenderPipelineManager.attachCamerasToRenderPipeline(p.name, scene.activeCamera!); delete saved[what]; } } }
    else if (what === 'terrain' || what === 'props' || what === 'vfx') {
      const re = what === 'terrain' ? /terrain|chunk|ground/i : what === 'props' ? /^(DEST_|Prop)/ : /vfx|fire|smoke|flame|spark/i;
      for (const m of scene.meshes) if (re.test(m.name)) m.setEnabled(want);
      if (!want) saved[what] = true; else delete saved[what];
    }
    return want;
  };
  win.take37Perf = { snapshot, toggle, budget: BUDGET, frames };

  // ---- the governor: render scale by the frame time ----
  const gov = q.get('gov') !== '0'; let over = 0, under = 0;
  const gi = setInterval(() => {
    if (!gov || document.hidden) return;
    const p = pct(frames, 0.95), lvl = engine.getHardwareScalingLevel();
    if (frames.length < 60) return;
    if (p > 20) { over++; under = 0; } else if (p < 13) { under++; over = 0; } else { over = under = 0; }
    if (over >= 3 && lvl < 1.5) { engine.setHardwareScalingLevel(Math.min(1.5, +(lvl + 0.125).toFixed(3))); over = 0; frames.length = 0; }
    if (under >= 6 && lvl > 1) { engine.setHardwareScalingLevel(Math.max(1, +(lvl - 0.125).toFixed(3))); under = 0; frames.length = 0; }
  }, 1000);
  void gi;

  // ---- the overlay ----
  if (q.get('perf') !== '1') return;
  const el = document.createElement('pre');
  el.style.cssText = 'position:fixed;right:8px;top:8px;z-index:50;margin:0;padding:6px 8px;background:rgba(10,12,20,.72);color:#dfe6ee;font:11px/1.35 ui-monospace,Consolas,monospace;border-radius:6px;pointer-events:none;white-space:pre';
  document.body.appendChild(el);
  setInterval(() => {
    const s = snapshot(), line = (name: string, v: number | null, unit = '') => { const b = BUDGET[name]; const bad = v !== null && b !== undefined && v > b; return `${bad ? '!' : ' '} ${name.padEnd(15)} ${v === null ? 'n/a' : String(v).padStart(7)}${unit}  / ${b ?? ''}`; };
    el.textContent = [`fps ${s.fps}   scale ${s.scale}`, line('frame p95 ms', s.ms.p95), `  mean ${s.ms.mean}  worst ${s.ms.worst}`, line('cpu render ms', s.cpuRender), line('gpu ms', s.gpu), line('draw calls', s.drawCalls), line('triangles (k)', Math.round(s.triangles / 1000)), line('meshes', s.meshes),
      `  active ${s.activeMeshes}  mats ${s.materials}  tex ${s.textures}`, line('take.step ms', s.game['take.step']!), line('view.frame ms', s.game['view.frame']!), line('view.stepFx ms', s.game['view.stepFx']!)].join('\n');
  }, 500);
}

const wait = setInterval(() => { if (win.take37Ready === true) { clearInterval(wait); try { install(); } catch (e) { console.warn('perf overlay not installed', e); } } }, 250);
