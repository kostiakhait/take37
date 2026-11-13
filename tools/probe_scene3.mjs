// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// Runs a script in the page of scene 3 (window.__scene3 is in scope as `s`) and prints what it returns as JSON: node tools/probe_scene3.mjs <script.js> [query]
import { createRequire } from 'node:module';
import { spawn, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const PORT = 4394, DIST = 'D:/temp/take37/s3/dist', here = path.dirname(fileURLToPath(import.meta.url)), repo = path.resolve(here, '..');
const code = fs.readFileSync(process.argv[2], 'utf8'), query = process.argv[3] ?? '';
const low = (pid) => { try { spawnSync('powershell', ['-NoProfile', '-Command', `(Get-Process -Id ${pid}).PriorityClass='BelowNormal'`]); } catch { /* none */ } };
const srv = spawn('node', [path.join(repo, 'tools', 'serve_scene3.mjs'), String(PORT)], { env: { ...process.env, TAKE37_OUT: DIST }, stdio: 'ignore', windowsHide: true }); low(srv.pid);
const require = createRequire('D:/REPO/ferret/package.json'); const { chromium } = require('@playwright/test');
let br;
try {
  await new Promise((r) => setTimeout(r, 1500));
  br = await chromium.launch({ args: ['--use-angle=d3d11', '--force_high_performance_gpu', '--ignore-gpu-blocklist', '--enable-gpu-rasterization', '--enable-webgl'] });
  spawnSync('powershell', ['-NoProfile', '-File', path.join(repo, 'tools', 'low_priority.ps1')]);
  const pg = await br.newPage({ viewport: { width: 1600, height: 900 } });
  pg.on('pageerror', (e) => console.log('pageerror', String(e).slice(0, 400)));
  pg.on('console', (m) => { const t = m.text(); if (m.type() === 'error' || m.type() === 'warning') console.log(m.type(), t.slice(0, 300)); });
  pg.setDefaultTimeout(300000);
  await pg.goto(`http://localhost:${PORT}/?clean=1&${query}`);
  await pg.waitForFunction(() => window.ferretReady || window.ferretError, null, { timeout: 300000 });
  console.log(JSON.stringify(await pg.evaluate(`(async () => { const s = window.__scene3; ${code} })()`), null, 1));
} finally { try { await br?.close(); } catch { /* none */ } spawnSync('taskkill', ['/T', '/F', '/PID', String(srv.pid)]); }
