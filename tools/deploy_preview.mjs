// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// One command: builds the playable scene into D:/temp/take37/deploy/dist and uploads only the changed files to https://take37.i-lion.net (ssh + tar to the nginx root, no git).
//   node tools/deploy_preview.mjs [--no-build] [--record]
//   --no-build  upload what is already in the stage
//   --record    (re)writes tools/deploy_files.json from the requests of the page in Chromium (the list of what the page loads)
// The host is read from D:/temp/take37/deploy/host.json {"host": "...", "user": "ubuntu", "key": "E:/.ssh/id_rsa"} (written when the server was created; holds no secrets).
// What is published: the build output, and the art/assets/ferret-library files named in tools/deploy_files.json (the files the page really requests). No sources.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawnSync, spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url)), repo = path.resolve(here, '..');
const FERRET = process.env.FERRET_DIR ?? 'D:/REPO/ferret', ROOT = 'D:/temp/take37/deploy', OUT = process.env.TAKE37_OUT ?? `${ROOT}/dist`, STAGE = `${ROOT}/site`;
const REMOTE_ROOT = '/var/www/take37';
const args = new Set(process.argv.slice(2));
const run = (cmd, a, o = {}) => { const r = spawnSync(cmd, a, { stdio: 'inherit', ...o }); if (r.status !== 0) throw new Error(`${cmd} ${a.join(' ')} failed (${r.status})`); };

// 1. build (BelowNormal priority: the build is heavy)
if (!args.has('--no-build')) {
  fs.mkdirSync(OUT, { recursive: true });
  run('powershell', ['-NoProfile', '-Command', `$env:TAKE37_OUT='${OUT}'; $p = Start-Process node -ArgumentList '${path.join(here, 'build_play.mjs').split(path.sep).join('/')}' -NoNewWindow -PassThru; $p.PriorityClass='BelowNormal'; $p.WaitForExit(); exit $p.ExitCode`]);
}

// 2. the mounts of tools/serve_set.mjs, in its order; a requested path is taken from the first mount that has it
const mounts = [['/art/', path.join(OUT, 'glb', 'art')], ['/assets/', path.join(OUT, 'glb', 'assets')], ['/art/', path.join(repo, 'art')], ['/assets/', path.join(repo, 'assets')], ['/lib/ferret-assets/', path.join(FERRET, 'lib', 'ferret-assets')], ['/lib/ferret/', path.join(FERRET, 'dist', 'lib', 'ferret')], ['/', OUT]];
const resolveUrl = (p) => { for (const [prefix, dir] of mounts) { if (!p.startsWith(prefix)) continue; const f = path.join(dir, p.slice(prefix.length)); if (fs.existsSync(f) && fs.statSync(f).isFile()) return f; } return null; };

const listFile = path.join(here, 'deploy_files.json');
if (args.has('--record')) {
  const { createRequire } = await import('node:module');
  const req = createRequire(path.join(FERRET, 'package.json'));
  let chromium; try { ({ chromium } = req('playwright')); } catch { ({ chromium } = req('@playwright/test')); }
  const http = await import('node:http');
  const srv = spawn('node', [path.join(here, 'serve_set.mjs'), '4391'], { env: { ...process.env, TAKE37_OUT: OUT }, stdio: 'ignore' });
  await new Promise((r) => setTimeout(r, 1500));
  const b = await chromium.launch({ args: ['--use-angle=d3d11', '--force_high_performance_gpu', '--ignore-gpu-blocklist'] });
  const pg = await b.newPage(); const seen = new Set();
  pg.on('request', (rq) => { const u = new URL(rq.url()); if (u.host === 'localhost:4391') seen.add(decodeURIComponent(u.pathname)); });
  await pg.goto('http://localhost:4391/'); await pg.waitForFunction(() => globalThis.take37Ready === true, null, { timeout: 600000 });
  await pg.waitForTimeout(5000); await b.close(); srv.kill();
  fs.writeFileSync(listFile, JSON.stringify([...seen].sort(), null, 1)); console.log('recorded', seen.size, 'urls');
}
const urls = JSON.parse(fs.readFileSync(listFile, 'utf8')).map((u) => (u === '/' ? '/index.html' : u));
// the page loads more files after ready (damaged cars etc.): index.html, main.js, lib/* are always included
const files = new Map();
for (const u of urls) { const f = resolveUrl(u); if (f) files.set(u.slice(1), f); else console.warn('missing for', u); }
for (const f of ['index.html', 'main.js']) if (fs.existsSync(path.join(OUT, f))) files.set(f, path.join(OUT, f));

// 3. diff against the server by size + sha1 of the files (remote manifest), upload the changed ones as one tar stream
const cfg = JSON.parse(fs.readFileSync(`${ROOT}/host.json`, 'utf8'));
const ssh = ['-i', cfg.key, '-o', 'StrictHostKeyChecking=accept-new', '-o', 'BatchMode=yes', `${cfg.user}@${cfg.host}`];
const sha = (f) => crypto.createHash('sha1').update(fs.readFileSync(f)).digest('hex');
const rem = spawnSync('ssh', [...ssh, `cd ${REMOTE_ROOT} 2>/dev/null && find . -type f -print0 | xargs -0 -r sha1sum || true`], { encoding: 'utf8', maxBuffer: 1 << 28 });
const remote = new Map(); for (const l of (rem.stdout ?? '').split('\n')) { const m = /^([0-9a-f]{40})\s+\.\/(.+)$/.exec(l); if (m) remote.set(m[2], m[1]); }
const changed = [...files].filter(([rel, f]) => remote.get(rel) !== sha(f));
console.log(`${files.size} files in the site, ${changed.length} changed`);
if (changed.length) {
  fs.rmSync(STAGE, { recursive: true, force: true });
  for (const [rel, f] of changed) { const d = path.join(STAGE, rel); fs.mkdirSync(path.dirname(d), { recursive: true }); fs.linkSync ? (() => { try { fs.linkSync(f, d); } catch { fs.copyFileSync(f, d); } })() : fs.copyFileSync(f, d); }
  fs.writeFileSync(`${STAGE}/.list`, changed.map(([r]) => r).join('\n'));
  const tar = spawn('tar', ['-C', STAGE, '-cf', '-', '-T', `${STAGE}/.list`], { stdio: ['ignore', 'pipe', 'inherit'] });
  const up = spawn('ssh', [...ssh, `sudo mkdir -p ${REMOTE_ROOT} && sudo chown -R ${cfg.user} ${REMOTE_ROOT} && tar -C ${REMOTE_ROOT} -xf -`], { stdio: ['pipe', 'inherit', 'inherit'] });
  tar.stdout.pipe(up.stdin);
  const code = await new Promise((r) => up.on('close', r));
  if (code !== 0) throw new Error('upload failed');
}
console.log('deployed to https://take37.i-lion.net/');
