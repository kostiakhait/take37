// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// Builds the R22 viewer (src/heli_view.ts) with the Ferret engine's sources next to this repository into D:/temp/take37/heli/view/dist and serves it with the models:
//   node tools/build_heliview.mjs            builds
//   node tools/build_heliview.mjs serve 4380 serves the page, /assets and /art of this repository and the engine's lib (Havok wasm)
import { createRequire } from 'node:module';
import path from 'node:path';
import fs from 'node:fs';
import http from 'node:http';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url)), repo = path.resolve(here, '..');
const FERRET = process.env.FERRET_DIR ?? 'D:/REPO/ferret', OUT = process.env.HELI_OUT ?? 'D:/temp/take37/heli/view/dist';
const require = createRequire(path.join(FERRET, 'package.json'));
if (process.argv[2] === 'serve') {
  const port = +(process.argv[3] ?? 4380);
  const mounts = [['/assets/', path.join(repo, 'assets')], ['/assets/', path.join(FERRET, 'examples', 'zeppelin', 'assets')], ['/art/', path.join(repo, 'art')], ['/lib/ferret/', path.join(FERRET, 'dist', 'lib', 'ferret')], ['/', OUT]];
  const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.wasm': 'application/wasm', '.glb': 'model/gltf-binary', '.png': 'image/png', '.map': 'application/json' };
  http.createServer((req, res) => {
    const p = decodeURIComponent(new URL(req.url, 'http://x').pathname).replace(/\/$/, '/index.html');
    for (const [prefix, dir] of mounts) {
      if (!p.startsWith(prefix)) continue;
      const file = path.join(dir, p.slice(prefix.length));
      if (!fs.existsSync(file) || !fs.statSync(file).isFile()) continue;
      res.writeHead(200, { 'Content-Type': types[path.extname(file)] ?? 'application/octet-stream', 'Cache-Control': 'no-cache' });
      fs.createReadStream(file).pipe(res); return;
    }
    res.writeHead(404).end('not found');
  }).listen(port, () => console.log('heli viewer on http://localhost:' + port + '/'));
} else {
  const { build } = require('esbuild');
  const pkgs = fs.readdirSync(path.join(FERRET, 'packages')).filter((p) => fs.existsSync(path.join(FERRET, 'packages', p, 'src', 'index.ts')));
  const alias = Object.fromEntries(pkgs.map((p) => [`@ferret/${p}`, path.join(FERRET, 'packages', p, 'src', 'index.ts')]));
  const p2 = (n) => String(n).padStart(2, '0'), d = new Date();
  const stamp = `${d.getFullYear()}${p2(d.getMonth() + 1)}${p2(d.getDate())}${p2(d.getHours())}${p2(d.getMinutes())}`;      // the machine's local time
  fs.mkdirSync(path.join(OUT, 'lib'), { recursive: true });
  await build({ entryPoints: [path.join(repo, process.env.HELI_ENTRY ?? 'src/heli_view.ts')], outfile: path.join(OUT, 'main.js'), bundle: true, format: 'iife', alias, keepNames: true, target: ['es2020'], sourcemap: true, logLevel: 'warning', legalComments: 'none',
    external: ['@babylonjs/core', '@babylonjs/havok'], banner: { js: `globalThis.__BUILD__=${JSON.stringify(stamp)};` }, nodePaths: [path.join(FERRET, 'node_modules')], plugins: [{ name: 'hk', setup(b) { b.onResolve({ filter: /^\.\/height$/ }, (a) => (a.importer.split(path.sep).join('/').includes('zeppelin/src/world') ? { path: path.join(repo, 'src', 'heli_land_height.ts') } : undefined)); b.onResolve({ filter: /^\/D:\// }, (a) => ({ path: a.path.slice(1) + '.ts' })); b.onResolve({ filter: /^@babylonjs\/havok$/ }, () => ({ path: path.join(FERRET, 'node_modules', '@babylonjs', 'havok', 'lib', 'esm', 'HavokPhysics_es.js') })); } }] });
  const nm = (p) => path.join(FERRET, 'node_modules', p);
  fs.copyFileSync(nm('babylonjs/babylon.js'), path.join(OUT, 'lib', 'babylon.js'));
  fs.copyFileSync(nm('babylonjs-loaders/babylonjs.loaders.min.js'), path.join(OUT, 'lib', 'babylonjs.loaders.min.js'));
  fs.writeFileSync(path.join(OUT, 'index.html'), `<!doctype html><html><head><meta charset="utf-8"><title>R22 viewer</title><style>html,body{margin:0;height:100%;background:#14161f;overflow:hidden}#c{position:fixed;inset:0;width:100%;height:100%;outline:none}#hud{position:fixed;left:8px;top:8px;padding:4px 8px;background:rgba(10,12,20,.55);color:#e8ecf5;font:12px ui-monospace,Consolas,monospace;border-radius:6px}body.clean #hud{display:none}</style></head><body><canvas id="c"></canvas><div id="hud"></div><script src="lib/babylon.js"></script><script src="lib/babylonjs.loaders.min.js"></script><script>globalThis.FERRET_LIB="/lib/ferret/";</script><script src="main.js"></script></body></html>`);
  console.log('built', stamp, 'into', OUT);
}
