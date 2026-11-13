// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// Renders fixed views of scene 3 on the NVIDIA card into D:/temp/take37/s3/shots/<label>/ : node tools/shots_scene3.mjs <label> <views.json> [query]
// Own server (port 4393) for D:/temp/take37/s3/dist, BelowNormal, one browser, everything closed in finally.
import { createRequire } from 'node:module';
import { spawn, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const label = process.argv[2] ?? 'shots', PORT = +(process.env.S3_PORT ?? 4393), DIST = 'D:/temp/take37/s3/dist', OUT = `D:/temp/take37/s3/shots/${label}`;
const here = path.dirname(fileURLToPath(import.meta.url)), repo = path.resolve(here, '..');
fs.mkdirSync(OUT, { recursive: true });
const views = JSON.parse(fs.readFileSync(process.argv[3] ?? path.join(repo, 'tools', 'views_scene3.json'), 'utf8'));
const query = process.argv[4] ?? '';
const low = (pid) => { try { spawnSync('powershell', ['-NoProfile', '-Command', `(Get-Process -Id ${pid}).PriorityClass='BelowNormal'`]); } catch { /* none */ } };
const srv = spawn('node', [path.join(repo, 'tools', 'serve_scene3.mjs'), String(PORT)], { env: { ...process.env, TAKE37_OUT: DIST }, stdio: 'ignore', windowsHide: true });
low(srv.pid);
const require = createRequire('D:/REPO/ferret/package.json');
const { chromium } = require('@playwright/test');
let br;
const report = { label, renderer: null, console: [], shots: [] };
try {
  await new Promise((r) => setTimeout(r, 2000));
  br = await chromium.launch({ args: ['--use-angle=d3d11', '--force_high_performance_gpu', '--ignore-gpu-blocklist', '--enable-gpu-rasterization', '--enable-webgl'] });
  const bpid = 0;
  spawnSync('powershell', ['-NoProfile', '-File', path.join(repo, 'tools', 'low_priority.ps1'), '-procId', String(bpid ?? 0)]);
  const pg = await br.newPage({ viewport: { width: views.width ?? 1600, height: views.height ?? 900 } });
  pg.on('pageerror', (e) => report.console.push('pageerror ' + String(e).slice(0, 400)));
  pg.on('console', (m) => { const t = m.text(); if (m.type() !== 'log' && !/Babylon.js v|Parallel shader/.test(t)) report.console.push(m.type() + ' ' + t.slice(0, 400)); });
  pg.setDefaultTimeout(300000);
  const t0 = Date.now();
  await pg.goto(`http://localhost:${PORT}/?clean=1&${query}`);
  await pg.waitForFunction(() => window.ferretReady || window.ferretError, null, { timeout: 300000 });
  report.loadSeconds = Math.round((Date.now() - t0) / 1000);
  report.err = await pg.evaluate(() => window.ferretError ?? null);
  if (report.err) throw new Error(report.err);
  report.renderer = await pg.evaluate(() => __scene3.renderer());
  if (!/NVIDIA/.test(report.renderer)) throw new Error('not the NVIDIA card: ' + report.renderer);
  for (const v of views.shots) {
    await pg.evaluate(async ([v]) => { const s = __scene3; if (v.weather) s.setWeather(v.weather); if (v.pre) await eval(v.pre); if (v.view) await s.goto(v.view); else { const o = v.rel ? s.FIELD_LEVEL : 0; await s.free([v.p[0], v.p[1] + o, v.p[2]], [v.t[0], v.t[1] + o, v.t[2]], v.fov ?? 0.95); } }, [v]);
    await pg.waitForTimeout(v.wait ?? 2500);
    await pg.screenshot({ path: `${OUT}/${v.name}.png` });
    report.shots.push(v.name);
  }
  if (views.stats) report.stats = await pg.evaluate(() => (window.__scene3.statsFull ?? window.__scene3.stats)());
} finally {
  try { await br?.close(); } catch { /* none */ }
  spawnSync('taskkill', ['/T', '/F', '/PID', String(srv.pid)]);
  fs.writeFileSync(`${OUT}/report.json`, JSON.stringify(report, null, 1));
  console.log(JSON.stringify(report));
}
