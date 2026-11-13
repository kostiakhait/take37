// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// Stage 4 frames of scene 2: the people (post, road, beach, decks, steamer, cages, the distant assault), the physics probe and the load time.
//   node tools/shots_people.mjs <label>      -> D:/temp/take37/s2/shots/<label>/ (own server on 4392, BelowNormal, one browser closed in finally)
import { createRequire } from 'node:module';
import { spawn, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const label = process.argv[2] ?? 'people', PORT = 4392, DIST = 'D:/temp/take37/s2/dist', OUT = `D:/temp/take37/s2/shots/${label}`;
const repo = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\//, '')), '..');
fs.mkdirSync(OUT, { recursive: true });
const low = (pid) => { try { spawnSync('powershell', ['-NoProfile', '-Command', `(Get-Process -Id ${pid}).PriorityClass='BelowNormal'`]); } catch { /* none */ } };
const srv = spawn('node', [path.join(repo, 'tools', 'serve_set.mjs'), String(PORT)], { env: { ...process.env, TAKE37_OUT: DIST, TAKE37_BR: process.env.TAKE37_BR ?? '0' }, stdio: 'ignore', windowsHide: true });
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
  pg.setDefaultTimeout(300000);
  const t0 = Date.now();
  await pg.goto(`http://localhost:${PORT}/?lite=${process.env.LITE ?? '1'}&clean=1&rung=0&t=0`);
  await pg.waitForFunction(() => window.ferretReady || window.ferretError, null, { timeout: 300000 });
  report.readySeconds = Math.round((Date.now() - t0) / 1000);
  report.renderer = await pg.evaluate(() => __scene2.renderer());
  if (!/NVIDIA/.test(report.renderer)) throw new Error('not the NVIDIA card: ' + report.renderer);
  await pg.waitForFunction(() => document.getElementById('splash') === null, null, { timeout: 120000 }).catch(() => {});
  report.splashGoneSeconds = Math.round((Date.now() - t0) / 1000);
  await pg.waitForTimeout(8000);
  const info = await pg.evaluate(() => { const S = __scene2; return { plans: S.fleet.views.map((v) => [v.plan.id, v.plan.x, v.plan.z]), cages: S.cages.map((c) => [c.position.x, c.position.y, c.position.z]), readMs: S.people.readMs, vessels: S.fleet.views.map((v) => [v.plan.id, v.ready, v.node.isEnabled(), +v.node.position.x.toFixed(0), +v.node.position.y.toFixed(1), +v.node.position.z.toFixed(0), v.node.scaling.x]), decks: [...S.people.decks.decks.keys()], waiting: S.people.decks.waiting, people: S.people.list.length, near: S.near.ready, mid: S.mid.ready, far: S.far.ready }; });
  report.info = info;
  const plan = (id) => info.plans.find((p) => p[0] === id);
  const views = [
    ['01_post_gate', [-30, 7, -165], [-62, 4.5, -198], 0.95],
    ['02_post_inside', [-50, 7, -226], [-78, 4.5, -198], 0.95],
    ['03_road', [-5, 8, -120], [-35, 3, -170], 0.95],
    ['04_beach_flank', [-8, 3.5, -140], [-46, 1.5, -118], 0.8],
    ['05_cage_arnold', [2.2, 5.5, 45.5], [-0.2, 4.9, 55], 0.65],
    ['05b_cage_arnold_west', [-3.4, 5.2, 55], [-0.2, 4.9, 55], 0.7],
    ['06_cage_emily', [2.2, 5.6, 165.5], [-0.2, 5.0, 175], 0.65],
    ['06b_cage_emily_west', [-3.4, 5.4, 175], [-0.2, 5.1, 175], 0.7],
    ['07_assault_far', [0, 6, -125], [200, 2, -145], 0.5],
  ];
  const d1 = plan('destroyer1'), d2 = plan('destroyer2'), st = plan('steamer'), y1 = plan('yacht1'), b1 = plan('boat1');
  if (d1) views.push(['08_destroyer1', [d1[1] + 38, 20, d1[2] - 40], [d1[1], 7, d1[2]], 0.8]);
  if (d2) views.push(['09_destroyer2', [d2[1] - 40, 20, d2[2] - 40], [d2[1], 7, d2[2]], 0.8]);
  if (st) views.push(['10_steamer', [st[1] + 22, 12, st[2] - 24], [st[1], 5, st[2]], 0.9]);
  if (y1) views.push(['11_yacht1', [y1[1] + 16, 7, y1[2] - 16], [y1[1], 2.5, y1[2]], 0.8]);
  if (b1) views.push(['12_boat1', [b1[1] + 9, 5, b1[2] - 9], [b1[1], 1.5, b1[2]], 0.8]);
  views.push(['13_overview', [60, 14, 120], [-40, 4, 420], 0.95]);
  await pg.evaluate(() => __scene2.pause(false));
  const only = process.env.ONLY ? new RegExp(process.env.ONLY) : null;
  for (const [name, p, t, fov] of views) {
    if (only && !only.test(name)) continue;
    await pg.evaluate(([p, t, f]) => __scene2.free(p, t, f), [p, t, fov]);
    await pg.waitForTimeout(3000);
    await pg.screenshot({ path: `${OUT}/${name}.png` });
    report.shots.push(name);
  }
  // a few minutes of the running scene, probed every 5 s: nobody in the air, on the mole or below the ground
  report.probe = [];
  for (let i = 0; i < (process.env.PROBES !== undefined ? +process.env.PROBES : 12); i++) {
    await pg.waitForTimeout(5000);
    const bad = await pg.evaluate(() => __scene2.people.probe());
    if (bad.length) report.probe.push({ at: i * 5, bad: bad.slice(0, 8) });
  }
  report.stats = await pg.evaluate(() => { const S = __scene2; return { overLog: S.overLog, overboard: S.people.overboard, people: S.people.list.length, brains: S.people.brains.length, near: S.near.slots.filter((s) => s.owner >= 0).length, mid: S.mid.slots.filter((s) => s.owner >= 0).length, far: S.far.pictures + '/' + S.far.dots, fps: S.engine.getFps() }; });
} finally {
  try { await br?.close(); } catch { /* none */ }
  spawnSync('taskkill', ['/T', '/F', '/PID', String(srv.pid)]);
  fs.writeFileSync(`${OUT}/report.json`, JSON.stringify(report, null, 1));
  console.log(JSON.stringify(report).slice(0, 6000));
}
