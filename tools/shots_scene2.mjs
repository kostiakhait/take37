// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// Renders fixed views of scene 2 on the NVIDIA card into D:/temp/take37/s2/shots/<label>/ : node tools/shots_scene2.mjs <label> [views.json]
// Own server (port 4392) for D:/temp/take37/s2/dist, BelowNormal, one browser, everything closed in finally.
import { createRequire } from 'node:module';
import { spawn, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const label = process.argv[2] ?? 'shots', PORT = 4392, DIST = 'D:/temp/take37/s2/dist', OUT = `D:/temp/take37/s2/shots/${label}`;
const repo = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\//, '')), '..');
fs.mkdirSync(OUT, { recursive: true });
const views = JSON.parse(fs.readFileSync(process.argv[3] ?? path.join(repo, 'tools', 'views_scene2.json'), 'utf8'));
const low = (pid) => { try { spawnSync('powershell', ['-NoProfile', '-Command', `(Get-Process -Id ${pid}).PriorityClass='BelowNormal'`]); } catch { /* none */ } };
const srv = spawn('node', [path.join(repo, 'tools', 'serve_set.mjs'), String(PORT)], { env: { ...process.env, TAKE37_OUT: DIST }, stdio: 'ignore', windowsHide: true });
low(srv.pid);
const require = createRequire('D:/REPO/ferret/package.json');
const { chromium } = require('@playwright/test');
let br;
const report = { label, renderer: null, console: [], shots: [] };
try {
  await new Promise((r) => setTimeout(r, 2000));
  br = await chromium.launch({ args: ['--use-angle=d3d11', '--force_high_performance_gpu', '--ignore-gpu-blocklist', '--enable-gpu-rasterization', '--enable-webgl'] });
  spawnSync('powershell', ['-NoProfile', '-File', path.join(repo, 'tools', 'low_priority.ps1')]);
  const pg = await br.newPage({ viewport: { width: 1600, height: 900 } });
  pg.on('pageerror', (e) => report.console.push('pageerror ' + String(e).slice(0, 300)));
  pg.on('console', (m) => { const t = m.text(); if (m.type() !== 'log' && !/Babylon.js v|Parallel shader/.test(t)) report.console.push(m.type() + ' ' + t.slice(0, 300)); });
  pg.setDefaultTimeout(240000);
  const t0 = Date.now();
  await pg.goto(`http://localhost:${PORT}/?lite=1&clean=1&rung=${views.rung ?? 0}&t=${views.t ?? 0}`);
  await pg.waitForFunction(() => window.ferretReady || window.ferretError, null, { timeout: 240000 });
  report.loadSeconds = Math.round((Date.now() - t0) / 1000);
  report.renderer = await pg.evaluate(() => __scene2.renderer());
  if (!/NVIDIA/.test(report.renderer)) throw new Error('not the NVIDIA card: ' + report.renderer);
  await pg.waitForTimeout(6000);
  await pg.evaluate(() => __scene2.pause(true));
  for (const v of views.shots) {
    await pg.evaluate(([p, t, f, tm]) => { if (tm !== null) __scene2.setTime(tm); __scene2.free(p, t, f); }, [v.p, v.t, v.fov ?? 0.95, v.time ?? null]);
    await pg.waitForTimeout(v.wait ?? 2500);
    await pg.screenshot({ path: `${OUT}/${v.name}.png` });
    report.shots.push(v.name);
  }
  report.materials = await pg.evaluate(() => [...__scene2.fleet.materials]);
  report.plans = await pg.evaluate(() => __scene2.fleet.plans.map((p) => `${p.id} ${p.livery.name} x${p.x.toFixed(0)} z${p.z.toFixed(0)} s${p.scale.toFixed(2)} trim${(p.trim * 57.3).toFixed(1)}`));
  // the frame: 3 runs of 6 s on the player's start view and on a view over the fleet, unpaused (mean frame time and the slowest second)
  report.frames = [];
  for (const [n, p, t] of [['start', [0, 1.8, -130], [0, 4, 180]], ['fleet', [60, 14, 120], [-40, 4, 420]], ['start', [0, 1.8, -130], [0, 4, 180]]]) {
    await pg.evaluate(([p, t]) => { __scene2.pause(false); __scene2.free(p, t, 0.95); }, [p, t]);
    await pg.waitForTimeout(1500);
    const r = await pg.evaluate(() => new Promise((res) => { const ts = []; let last = performance.now(); const f = () => { const n = performance.now(); ts.push(n - last); last = n; if (ts.length < 360 && n - ts.reduce((a, b) => a, 0) > 0) requestAnimationFrame(f); else res(ts); }; requestAnimationFrame(f); setTimeout(() => res(ts), 8000); }));
    const mean = r.reduce((a, b) => a + b, 0) / r.length, sorted = [...r].sort((a, b) => a - b);
    report.frames.push({ view: n, frames: r.length, meanMs: +mean.toFixed(1), p95Ms: +sorted[Math.floor(sorted.length * 0.95)].toFixed(1), maxMs: +sorted[sorted.length - 1].toFixed(1) });
  }
  report.fps = await pg.evaluate(() => __scene2.engine.getFps());
} finally {
  try { await br?.close(); } catch { /* none */ }
  spawnSync('taskkill', ['/T', '/F', '/PID', String(srv.pid)]);
  fs.writeFileSync(`${OUT}/report.json`, JSON.stringify(report, null, 1));
  console.log(JSON.stringify(report));
}
