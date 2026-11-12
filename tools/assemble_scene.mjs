// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// Assembles the scene 1 play build from the assets as they are now and renders a fixed set of views, so that each assembly can be compared with the last.
//   node tools/assemble_scene.mjs [label]
// Output: D:/temp/take37/assembly/<stamp>/ (own build, renders, manifest.json). Own build and own port, so the agents' builds and servers are left alone.
// Playwright on the discrete GPU (the renderer string is checked and written to the manifest), one worker.
import { createRequire } from 'node:module';
import { spawn, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url)), repo = path.resolve(here, '..');
const p2 = (n) => String(n).padStart(2, '0'), d = new Date();
const stamp = `${d.getFullYear()}${p2(d.getMonth() + 1)}${p2(d.getDate())}${p2(d.getHours())}${p2(d.getMinutes())}`;   // the machine's local time
const label = process.argv[2] ?? '';
const OUT = `D:/temp/take37/assembly/${stamp}`, DIST = 'D:/temp/take37/assembly/dist', PORT = 4381;
fs.mkdirSync(OUT, { recursive: true });
const log = (...a) => { const s = `${new Date().toTimeString().slice(0, 8)} ${a.join(' ')}`; console.log(s); fs.appendFileSync(`${OUT}/assemble.log`, s + '\n'); };

// ---- 1. the manifest: which version of each asset went into this assembly ----
const ASSETS = ['art/street/street_level.glb', 'art/street/street_colliders.glb', 'art/gas-station/gas_station.glb', 'art/tanker/tanker_1987.glb', 'art/tanker/tanker_1987_lod1.glb',
  'assets/borrowed/corvette_c4_87_conv.glb', 'assets/borrowed/crown_victoria_cpd87.glb', ...['coupe/coupe84', 'sedan/sedan87', 'pickup/pickup87', 'wagon/wagon82', 'minivan/minivan86', 'hatchback/hatchback85'].flatMap((c) => [`art/cars/${c}.glb`, `art/cars/${c}_damaged.glb`, `art/cars/${c}_lod1.glb`]),
  'src/play.ts', 'src/scene/set.ts', 'src/game/sim.ts', 'src/game/fire.ts', 'src/game/ai.ts', 'src/game/scene1.ts', 'src/game/take.ts', 'src/game/view.ts', 'MOCKUPS.md'];
const manifest = { stamp, label, assets: {}, mockups: null, renderer: null, shots: [], console: [] };
for (const a of ASSETS) { const f = path.join(repo, a); manifest.assets[a] = fs.existsSync(f) ? { bytes: fs.statSync(f).size, mtime: fs.statSync(f).mtime.toTimeString().slice(0, 5) } : 'MISSING'; }
const missing = Object.entries(manifest.assets).filter(([, v]) => v === 'MISSING').map(([k]) => k);
if (missing.length) { log('MISSING assets:', missing.join(', ')); fs.writeFileSync(`${OUT}/manifest.json`, JSON.stringify(manifest, null, 1)); process.exit(2); }

// ---- 2. build ----
log('build into', DIST);
const b = spawnSync('node', [path.join(here, 'build_play.mjs')], { env: { ...process.env, TAKE37_OUT: DIST }, encoding: 'utf8' });
log((b.stdout + b.stderr).trim().split('\n').slice(-3).join(' | '));
if (b.status !== 0) process.exit(3);

// ---- 3. serve (own port) ----
const srv = spawn('node', [path.join(here, 'serve_set.mjs'), String(PORT)], { env: { ...process.env, TAKE37_OUT: DIST }, stdio: 'ignore', windowsHide: true });
try { spawnSync('powershell', ['-NoProfile', '-Command', `(Get-Process -Id ${srv.pid}).PriorityClass='BelowNormal'`]); } catch { /* none */ }
await new Promise((r) => setTimeout(r, 2500));

// ---- 4. render the fixed views ----
const require = createRequire('D:/REPO/ferret/package.json');
const { chromium } = require('@playwright/test');
const br = await chromium.launch({ args: ['--use-angle=d3d11', '--force_high_performance_gpu', '--ignore-gpu-blocklist', '--enable-gpu-rasterization', '--enable-webgl'] });
const pg = await br.newPage({ viewport: { width: 1600, height: 900 } });
pg.on('pageerror', (e) => { manifest.console.push('pageerror ' + String(e).slice(0, 300)); log('[pageerror]', String(e).slice(0, 300)); });
pg.on('console', (m) => { const t = m.text(); if (m.type() !== 'log' && !/Babylon.js v|Parallel shader/.test(t)) manifest.console.push(m.type() + ' ' + t.slice(0, 300)); });
pg.setDefaultTimeout(300000);
const t0 = Date.now();
await pg.goto(`http://localhost:${PORT}/?lite=1&auto=1&fresh=1`);
await pg.waitForFunction(() => window.take37Ready || window.take37Error, null, { timeout: 600000 });
manifest.loadSeconds = Math.round((Date.now() - t0) / 1000);
const err = await pg.evaluate(() => window.take37Error ?? null);
manifest.renderer = await pg.evaluate(() => take37.renderer());
log('ready in', manifest.loadSeconds, 's, error:', err, 'renderer:', JSON.stringify(manifest.renderer));
if (err || !/NVIDIA/.test(JSON.stringify(manifest.renderer))) { log('STOP: page error or not the NVIDIA card'); fs.writeFileSync(`${OUT}/manifest.json`, JSON.stringify(manifest, null, 1)); await br.close(); srv.kill(); process.exit(4); }

const shot = async (name, note = '') => { await pg.waitForTimeout(1200); const f = `${OUT}/${name}.png`; await pg.screenshot({ path: f }); manifest.shots.push({ name, note }); log('shot', name, note); };
const setCam = (id, pos, target, fov = 0.9) => pg.evaluate(([id, pos, target, fov]) => { take37.setPaused(true); take37.view.setView({ mode: 'set', set: { id, label: id, pos, target, fov, weight: 1 } }); }, [id, pos, target, fov]);
const cab = () => pg.evaluate(() => { take37.view.setView({ mode: 'cab' }); });
const adv = (n) => pg.evaluate((n) => take37.advance(n), n);
const state = () => pg.evaluate(() => { const t = take37.take; return { ph: t.phase, t: +t.t.toFixed(1), v: +t.scene.player.v?.toFixed?.(1), score: t.scene.score ?? null }; }).catch(() => null);

// the cab at the start, the clapperboard
await pg.evaluate(() => take37.setPaused(true));
await shot('01_cab_start', 'police cab at the start, clapperboard');
await adv(60 * 4); await shot('02_cab_go', 'after the clapperboard');
// the street from fixed points: along the street, the block with shops, the end of the street, the station and the tanker
const views = [['03_street_low', [0, 1.7, -3], [150, 3, -2], 0.9], ['04_street_mid', [250, 1.7, -3], [350, 3, -2], 0.9], ['05_street_far_end', [440, 1.7, -3], [560, 3, -2], 0.9],
  ['06_station_from_road', [470, 1.8, -3], [565, 3, -30], 0.9], ['07_station_corner', [520, 2.5, -4], [575, 3, -32], 1.0], ['08_station_high', [560, 22, 30], [565, 1, -30], 0.9], ['09_overview_high', [200, 90, 40], [260, 0, 0], 0.9]];
for (const [n, p, t, f] of views) { await setCam(n, p, t, f); await shot(n, 'fixed camera'); }
// the chase on the autopilot: the cab, the Corvette ahead, the first wreck frames
await cab(); await pg.evaluate(() => { take37.autopilot(true, 22); take37.setPaused(true); });
for (const [i, n] of [[1, 60 * 5], [2, 60 * 6], [3, 60 * 7]]) { await adv(n); await shot(`10_chase_${i}`, `autopilot, state ${JSON.stringify(await state())}`); }
await pg.evaluate(() => take37.autopilot(false));
manifest.endState = await state();
fs.writeFileSync(`${OUT}/manifest.json`, JSON.stringify(manifest, null, 1));
log('done:', manifest.shots.length, 'renders in', OUT, '; console messages:', manifest.console.length);
await br.close(); srv.kill();
