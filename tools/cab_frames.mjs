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
process.on('exit', () => { try { spawnSync('taskkill', ['/T', '/F', '/PID', String(srv.pid)]); } catch { /* gone */ } });   // the server never outlives the run
const require = createRequire('D:/REPO/ferret/package.json');
const { chromium } = require('@playwright/test');
const br = await chromium.launch({ args: ['--use-angle=d3d11', '--force_high_performance_gpu', '--ignore-gpu-blocklist', '--enable-gpu-rasterization', '--enable-webgl'] });
const low = (pid = 0) => { const r = spawnSync('powershell', ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', path.join(here, 'low_priority.ps1'), '-procId', String(pid)], { encoding: 'utf8' }); console.log((r.stdout || '').trim()); };
low(srv.pid); low(process.pid);   // the owner's rule: every process of the run at BelowNormal (the browser's processes too)
// the owner's rule: one Playwright browser at a time, and it is closed (with the server) whatever happens: finally, and on a timeout of the whole run
const stop = async () => { try { await Promise.race([br.close(), new Promise((r) => setTimeout(r, 15000))]); } catch { /* closed */ }
  // whatever is left of this run's own browser (a child of this node process): killed by its PID
  try { const o = spawnSync('powershell', ['-NoProfile', '-Command', `Get-CimInstance Win32_Process -Filter "ParentProcessId=${process.pid}" | Where-Object { $_.CommandLine -like '*ms-playwright*' } | ForEach-Object { $_.ProcessId }`], { encoding: 'utf8' }); for (const l of o.stdout.split(/\s+/).filter(Boolean)) spawnSync('taskkill', ['/T', '/F', '/PID', l]); } catch { /* gone */ }
  try { spawnSync('taskkill', ['/T', '/F', '/PID', String(srv.pid)]); } catch { /* gone */ } };
const guard = setTimeout(async () => { console.log('run timed out'); await stop(); process.exit(5); }, 30 * 60 * 1000);
try {
  const pg = await br.newPage({ viewport: { width: 1600, height: 900 } });
  pg.on('pageerror', (e) => console.log('[pageerror]', String(e).slice(0, 300)));
  pg.setDefaultTimeout(600000);
  const HOUR = process.argv.find((a) => a.startsWith('--hour='))?.slice(7);   // time of day of the scene (hour), default as the game has it
  await pg.goto(`http://localhost:${PORT}/?lite=1&auto=1&fresh=1&clean=1${HOUR ? '&hour=' + HOUR : ''}`);
  await pg.addStyleTag({ content: '#hud, #hud *, #hud2, #hud2 * { visibility: hidden !important; }' });   // the frames show the car, not the interface (the game's HUD and the pause caption)
  await pg.waitForFunction(() => window.take37Ready || window.take37Error, null, { timeout: 900000 });
  console.log('renderer', JSON.stringify(await pg.evaluate(() => take37.renderer())), 'error', await pg.evaluate(() => window.take37Error ?? null));
  const shot = async (n) => { await pg.waitForTimeout(1500); await pg.screenshot({ path: `${OUT}/${n}.png` }); console.log('shot', n); };
  // the head: an extra turn of the cab camera after the game has placed it (yaw + right, pitch + down, radians; fov when given), as a turned head would see it
  await pg.evaluate(() => { const v = take37.view, sc = v.scene; window.__head = null; sc.onBeforeRenderObservable.add(() => { const h = window.__head; if (!h || v.view.mode !== 'cab') return; const c = v.camera; c.rotationQuaternion = c.rotationQuaternion.multiply(BABYLON.Quaternion.RotationYawPitchRoll(h.yaw, h.pitch, 0)); if (h.fov) c.fov = h.fov; }); });
  const head = (yaw, pitch = 0, fov = 0) => pg.evaluate(([yaw, pitch, fov]) => { window.__head = { yaw, pitch, fov }; }, [yaw, pitch, fov]);
  const P = +(process.argv.find((a) => a.startsWith('--pitch='))?.slice(8) ?? 0), D = Math.PI / 180;   // a proposed fixed pitch of the cab camera (degrees down), 0 = as the game has it
  await pg.evaluate(() => take37.setPaused(true));
  await head(0, P * D); await shot('1_sit');
  await pg.evaluate(() => take37.advance(60, { gas: true })); await shot('2_go');
  await pg.evaluate(() => take37.advance(40, { gas: true, steer: 1 })); await shot('3_steer_left');
  await pg.evaluate(() => take37.advance(80, { gas: true, steer: -1 })); await shot('4_steer_right');
  await pg.evaluate(() => take37.advance(30, {}));
  await head(-60 * D, P * D); await shot('5_head_left60');
  await head(60 * D, P * D); await shot('6_head_right60');
  // close: the left A-pillar, the left and right outside mirrors, the inside mirror (aims in degrees from the eye: yaw, pitch down, vertical field of view)
  const close = JSON.parse(process.argv.find((a) => a.startsWith('--close='))?.slice(8) ?? '[["7_pillar",-30,-5,26],["8_mirror_left",-39,8,20],["9_mirror_right",60,6,14],["10_mirror_inside",40,-6,24]]');
  for (const [n, y, p, f] of close) { await head(y * D, p * D, f * D); await shot(n); }
} finally {
  clearTimeout(guard);
  await stop();
}
