// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// Flies the Mustang off the runway of scene 3 with the engine Aeroplane (tools/flight3), cockpit frames and the measured log into D:/temp/take37/s3/shots/<label>/ : node tools/flight_scene3.mjs <label> <views.json> [query]
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
  // the flight test: the Mustang's take-off run on the field's real ground (the engine's Aeroplane, the airwar P-51D spec), frames from the cockpit and from outside
  await pg.exposeFunction('__shot', async (name) => { await pg.screenshot({ path: `${OUT}/${name}.png` }); report.shots.push(name); });
  report.flight = {};
  for (const [name, o] of Object.entries(views.flights ?? {})) {
    const r = await pg.evaluate(async ([o]) => {
      const s = __scene3; if (o.weather) s.setWeather(o.weather);
      if (o.camStart) { await s.free(o.camStart.p, o.camStart.t, o.camStart.fov ?? 0.95); }
      const opt = { ...o, shot: async (n) => { await window.__shot((o.prefix ?? 'f') + '_' + n); } };
      const res = await s.takeoff(opt);
      const t0 = performance.now(); let n = 0; await new Promise((res2) => { const f = () => { if (++n >= 60) res2(); else requestAnimationFrame(f); }; requestAnimationFrame(f); }); const msAir = (performance.now() - t0) / 60;
      return { log: { ...res.log, samples: res.log.samples.filter((x, i) => i % 20 === 0) }, endN: res.endN, endE: res.endE, altitude: res.altitude, msFrameAirborne: msAir };
    }, [o]);
    report.flight[name] = r;
  }
  if (views.stats) report.stats = await pg.evaluate(() => (window.__scene3.statsFull ?? window.__scene3.stats)());
} finally {
  try { await br?.close(); } catch { /* none */ }
  spawnSync('taskkill', ['/T', '/F', '/PID', String(srv.pid)]);
  fs.writeFileSync(`${OUT}/report.json`, JSON.stringify(report, null, 1));
  console.log(JSON.stringify(report));
}
