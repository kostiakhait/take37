// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// A static server for the set scene: the built page (D:/temp/take37/s3/dist), /art and /assets of this repository, and the Ferret asset library and WebAssembly files.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { brotliOf, brotliable } from './brotli.mjs';

const here = path.dirname(fileURLToPath(import.meta.url)), repo = path.resolve(here, '..');
const FERRET = process.env.FERRET_DIR ?? 'D:/REPO/ferret', OUT = process.env.TAKE37_OUT ?? 'D:/temp/take37/s3/dist', port = +(process.argv[2] ?? 4393);
const mounts = [['/art/', path.join(OUT, 'glb', 'art')], ['/assets/', path.join(OUT, 'glb', 'assets')], ['/art/', path.join(repo, 'art')], ['/assets/', path.join(repo, 'assets')], ['/lib/ferret-assets/', path.join(FERRET, 'lib', 'ferret-assets')], ['/lib/ferret/', path.join(FERRET, 'dist', 'lib', 'ferret')], ['/', OUT]];
const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.json': 'application/json', '.wasm': 'application/wasm', '.glb': 'model/gltf-binary', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.ferret': 'application/octet-stream', '.map': 'application/json', '.ktx2': 'image/ktx2' };
http.createServer((req, res) => {
  const p = decodeURIComponent(new URL(req.url, 'http://x').pathname).replace(/\/$/, '/index.html');
  for (const [prefix, dir] of mounts) {
    if (!p.startsWith(prefix)) continue;
    const file = path.join(dir, p.slice(prefix.length));
    if (!file.startsWith(path.resolve(dir))) continue;
    if (!fs.existsSync(file) || !fs.statSync(file).isFile()) continue;
    const st = fs.statSync(file), etag = `"${st.size.toString(36)}-${Math.floor(st.mtimeMs).toString(36)}"`;   // a reload revalidates and gets a 304 for the unchanged glb files
    if (req.headers['if-none-match'] === etag) { res.writeHead(304, { ETag: etag, 'Cache-Control': 'no-cache' }).end(); return; }
    const head = { 'Content-Type': types[path.extname(file)] ?? 'application/octet-stream', 'Cache-Control': 'no-cache', ETag: etag };
    let src = file;
    if (process.env.TAKE37_BR === '1' && /\bbr\b/.test(req.headers['accept-encoding'] ?? '') && brotliable(file)) { src = brotliOf(file); head['Content-Encoding'] = 'br'; head.Vary = 'Accept-Encoding'; }   // as the preview server does (nginx brotli_static)
    const size = fs.statSync(src).size, rg = /^bytes=(\d*)-(\d*)$/.exec(req.headers.range ?? '');
    head['Accept-Ranges'] = 'bytes';
    // a Range request (the engine's asset store reads the big packages in blocks) gets just those bytes, as nginx would give them
    if (rg && !head['Content-Encoding'] && (rg[1] || rg[2])) {
      const a = rg[1] ? +rg[1] : Math.max(0, size - +rg[2]), b = rg[1] && rg[2] ? Math.min(size - 1, +rg[2]) : size - 1;
      if (a > b || a >= size) { res.writeHead(416, { 'Content-Range': `bytes */${size}` }).end(); return; }
      head['Content-Range'] = `bytes ${a}-${b}/${size}`; head['Content-Length'] = b - a + 1; res.writeHead(206, head);
      fs.createReadStream(src, { start: a, end: b }).pipe(res); return;
    }
    head['Content-Length'] = size; res.writeHead(200, head);
    fs.createReadStream(src).pipe(res); return;
  }
  res.writeHead(404).end('not found');
}).listen(port, () => console.log(`scene 3 on http://localhost:${port}/`));
