// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// Cab frames from the real first-person camera: sitting, steering left and right, looking back (C). Own build and port; Chromium on the NVIDIA card (checked).
//   node tools/cab_frames.mjs <label> [--nobuild]      output D:/temp/take37/cab/<label>/
import { createRequire } from 'node:module';
import { spawn, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const label = process.argv[2] ?? 'frames', DIST = 'D:/temp/take37/cab/dist', PORT = 4500, OUT = `D:/temp/take37/cab/${label}`;
fs.mkdirSync(OUT, { recursive: true });
if (!process.argv.includes('--nobuild')) { const b = spawnSync('node', [path.join(here, 'build_play.mjs')], { env: { ...process.env, TAKE37_OUT: DIST }, encoding: 'utf8' }); console.log((b.stdout + b.stderr).trim().split('\n').slice(-2).join(' | ')); if (b.status !== 0) process.exit(3); }
const srv = spawn('node', [path.join(here, 'serve_set.mjs'), String(PORT)], { env: { ...process.env, TAKE37_OUT: DIST }, stdio: 'ignore', windowsHide: true });
await new Promise((r) => setTimeout(r, 2500));
const require = createRequire('D:/REPO/ferret/package.json');
const { chromium } = require('@playwright/test');
const br = await chromium.launch({ args: ['--use-angle=d3d11', '--force_high_performance_gpu', '--ignore-gpu-blocklist', '--enable-gpu-rasterization', '--enable-webgl'] });
const low = (pid = 0) => { const r = spawnSync('powershell', ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', path.join(here, 'low_priority.ps1'), '-procId', String(pid)], { encoding: 'utf8' }); console.log((r.stdout || '').trim()); };
low(srv.pid); low(process.pid);   // the owner's rule: every process of the run at BelowNormal (the browser's processes too)
const pg = await br.newPage({ viewport: { width: 1600, height: 900 } });
pg.on('pageerror', (e) => console.log('[pageerror]', String(e).slice(0, 300)));
pg.setDefaultTimeout(600000);
await pg.goto(`http://localhost:${PORT}/?lite=1&auto=1&fresh=1`);
await pg.waitForFunction(() => window.take37Ready || window.take37Error, null, { timeout: 900000 });
console.log('renderer', JSON.stringify(await pg.evaluate(() => take37.renderer())), 'error', await pg.evaluate(() => window.take37Error ?? null));
const shot = async (n) => { await pg.waitForTimeout(1500); await pg.screenshot({ path: `${OUT}/${n}.png` }); console.log('shot', n); };
await pg.evaluate(() => take37.setPaused(true));
if (process.argv.includes('--backonly')) { await pg.evaluate(() => take37.advance(120, { gas: true })); }
else {
await shot('1_sit');
await pg.evaluate(() => take37.advance(60, { gas: true })); await shot('2_go');
await pg.evaluate(() => take37.advance(40, { gas: true, steer: 1 })); await shot('3_steer_a');
await pg.evaluate(() => take37.advance(80, { gas: true, steer: -1 })); await shot('4_steer_b');
}
await pg.evaluate(() => take37.advance(60, {}));
// look back: the key C held (sent to the canvas, which owns the input); the view turns the head over 0.3 s
await pg.evaluate(() => { const c = document.getElementById('c'); c.focus(); for (const t of [c, window, document]) t.dispatchEvent(new KeyboardEvent('keydown', { code: 'KeyC', key: 'c', bubbles: true })); });
await pg.evaluate(() => take37.setPaused(false)); await pg.waitForTimeout(1500); await pg.evaluate(() => take37.setPaused(true));   // the input's buttons are read in the fixed steps: they must run
await pg.waitForTimeout(300); console.log('head turned', await pg.evaluate(() => take37.view.back?.toFixed?.(2)));
await shot('5_back');
await pg.evaluate(() => { const c = document.getElementById('c'); for (const t of [c, window, document]) t.dispatchEvent(new KeyboardEvent('keyup', { code: 'KeyC', key: 'c', bubbles: true })); });
await br.close(); srv.kill();
