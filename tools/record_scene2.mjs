// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// Records a short walk of scene 2 with the engine's own recording tool (captureFrames of @ferret/media: frame by frame on simulated time, encoded in the browser into WebM):
// the player's start, up the mole past both cages, over the fleet, back to the post. Own server (4392), BelowNormal, one browser closed in finally.
//   node tools/record_scene2.mjs [seconds] [width] [height] [fps]      -> D:/temp/take37/s2/video/scene2_walk_<local time>.webm
import { createRequire } from 'node:module';
import { spawn, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const [seconds, width, height, fps] = [process.argv[2], process.argv[3], process.argv[4], process.argv[5]].map((x) => (x ? +x : undefined));
const repo = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\//, '')), '..'), PORT = 4392, DIST = 'D:/temp/take37/s2/dist';
const p2 = (n) => String(n).padStart(2, '0'), d = new Date(), stamp = `${d.getFullYear()}${p2(d.getMonth() + 1)}${p2(d.getDate())}${p2(d.getHours())}${p2(d.getMinutes())}`;   // local time
fs.mkdirSync('D:/temp/take37/s2/video', { recursive: true });
const out = `D:/temp/take37/s2/video/scene2_walk_${stamp}.webm`;
const srv = spawn('node', [path.join(repo, 'tools', 'serve_set.mjs'), String(PORT)], { env: { ...process.env, TAKE37_OUT: DIST }, stdio: 'ignore', windowsHide: true });
spawnSync('powershell', ['-NoProfile', '-Command', `(Get-Process -Id ${srv.pid}).PriorityClass='BelowNormal'`]);
const require = createRequire('D:/REPO/ferret/package.json');
const { chromium } = require('@playwright/test');
let br;
try {
  await new Promise((r) => setTimeout(r, 2000));
  br = await chromium.launch({ args: ['--use-angle=d3d11', '--force_high_performance_gpu', '--ignore-gpu-blocklist', '--enable-gpu-rasterization', '--enable-webgl'] });
  spawnSync('powershell', ['-NoProfile', '-File', path.join(repo, 'tools', 'low_priority.ps1')]);
  const pg = await br.newPage({ viewport: { width: 1280, height: 720 } });
  pg.on('pageerror', (e) => console.log('pageerror', String(e).slice(0, 300)));
  pg.setDefaultTimeout(1800000);
  await pg.goto(`http://localhost:${PORT}/?lite=0&clean=1&rung=0&t=0`, { waitUntil: 'commit', timeout: 120000 });
  await pg.waitForFunction(() => window.ferretReady || window.ferretError, null, { timeout: 300000 });
  const renderer = await pg.evaluate(() => __scene2.renderer());
  if (!/NVIDIA/.test(renderer)) throw new Error('not the NVIDIA card: ' + renderer);
  await pg.waitForFunction(() => document.getElementById('splash') === null, null, { timeout: 180000 }).catch(() => {});
  // the full figures come in last: wait until the near ring is built
  await pg.waitForFunction(() => __scene2.near.ready >= __scene2.near.slots.length, null, { timeout: 180000 }).catch(() => {});
  await pg.waitForTimeout(3000);
  const t0 = Date.now();
  const info = await pg.evaluate((o) => __scene2.record(o), { seconds, width, height, fps });
  console.log('recorded', JSON.stringify(info), ((Date.now() - t0) / 1000).toFixed(0), 's');
  const fd = fs.openSync(out, 'w');
  for (let off = 0; off < info.bytes; off += 3 << 20) {
    const b64 = await pg.evaluate(async ([o, n]) => { const b = new Uint8Array(await window.__capture.slice(o, o + n).arrayBuffer()); let s = ''; for (let i = 0; i < b.length; i += 0x8000) s += String.fromCharCode(...b.subarray(i, i + 0x8000)); return btoa(s); }, [off, 3 << 20]);
    fs.writeSync(fd, Buffer.from(b64, 'base64'));
  }
  fs.closeSync(fd);
  console.log('video', out, fs.statSync(out).size, 'bytes', renderer);
} finally {
  try { await br?.close(); } catch { /* none */ }
  spawnSync('taskkill', ['/T', '/F', '/PID', String(srv.pid)]);
}
