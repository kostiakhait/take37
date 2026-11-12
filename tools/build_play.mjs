// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// Builds the set scene (src/main.ts) with the Ferret engine's sources next to this repository, into D:/temp/take37/land/dist (not into the repository).
//   node tools/build_play.mjs           builds the playable scene 1 (src/play.ts) into D:/temp/take37/play/dist
//   node tools/serve_set.mjs [port]     serves the page, the art, the assets and the Ferret asset library
import { createRequire } from 'node:module';
import path from 'node:path';
import fs from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url)), repo = path.resolve(here, '..');
const FERRET = process.env.FERRET_DIR ?? 'D:/REPO/ferret', OUT = process.env.TAKE37_OUT ?? 'D:/temp/take37/play/dist';
const require = createRequire(path.join(FERRET, 'package.json'));
const { build } = require('esbuild');
const pkgs = fs.readdirSync(path.join(FERRET, 'packages')).filter((p) => fs.existsSync(path.join(FERRET, 'packages', p, 'src', 'index.ts')));
const alias = Object.fromEntries(pkgs.map((p) => [`@ferret/${p}`, path.join(FERRET, 'packages', p, 'src', 'index.ts')]));
// the destruction module's road-vehicle files are imported by subpath (they are not in its index)
for (const f of ['vehicle', 'autoparts', 'crush', 'glass', 'assembly', 'part', 'types', 'view-dents', 'service', 'debris', 'energy', 'view-shards', 'style', 'material', 'rng', 'wood', 'stone', 'fracture', 'motion', 'capability']) alias[`@ferret/destruction/${f}`] = path.join(FERRET, 'packages', 'destruction', 'src', `${f}.ts`);
const p2 = (n) => String(n).padStart(2, '0'), d = new Date();
const stamp = `${d.getFullYear()}${p2(d.getMonth() + 1)}${p2(d.getDate())}${p2(d.getHours())}${p2(d.getMinutes())}`;      // the machine's local time

fs.mkdirSync(path.join(OUT, 'lib'), { recursive: true });
await build({
  entryPoints: [path.join(repo, 'src', 'play.ts')], outfile: path.join(OUT, 'main.js'), bundle: true, format: 'iife', alias, keepNames: true, target: ['es2020'],
  sourcemap: true, logLevel: 'warning', legalComments: 'none', define: { __FERRET_BUILD__: JSON.stringify(stamp), __TAKE37_BUILD__: JSON.stringify(stamp) },
  banner: { js: `globalThis.__TAKE37_BUILD__ = ${JSON.stringify(stamp)};` },
});
const nm = (p) => path.join(FERRET, 'node_modules', p);
fs.copyFileSync(nm('babylonjs/babylon.js'), path.join(OUT, 'lib', 'babylon.js'));
fs.copyFileSync(path.join(FERRET, 'node_modules', '.pnpm', '@babylonjs+core@9.33.1', 'node_modules', '@babylonjs', 'core', 'assets', 'meshopt', 'meshopt_decoder.js'), path.join(OUT, 'lib', 'meshopt_decoder.js'));
fs.copyFileSync(nm('babylonjs-loaders/babylonjs.loaders.min.js'), path.join(OUT, 'lib', 'babylonjs.loaders.min.js'));
const tpl = fs.readFileSync(path.join(repo, 'src', 'play.template.html'), 'utf8');
// the early download list (tools/preload.js): street, colliders, station, then the cars as the game's config names them (police, Corvette, tanker first), the wrecked variants after ready
const cfg = fs.readFileSync(path.join(repo, 'src', 'game', 'config.ts'), 'utf8'), urls = (key) => [...cfg.matchAll(new RegExp(String.raw`\b${key}\s*:\s*'([^']+)'`, 'g'))].map((m) => m[1]);
const order = (u) => (/borrowed|tanker/.test(u) ? 0 : 1);
const now = ['/art/street/street_level.glb', '/art/street/street_colliders.glb', '/art/gas-station/gas_station.glb', ...[...urls('glb'), ...urls('lod1')].sort((a, b) => order(a) - order(b))];
const preload = fs.readFileSync(path.join(here, 'preload.js'), 'utf8').replace('__LIST__', [...new Set(now), '|', ...urls('damaged')].join(','));
fs.writeFileSync(path.join(OUT, 'index.html'), tpl.replace('<!--SCRIPTS-->', '<script>' + preload + '</script>\n<script src="lib/babylon.js"></script>\n<script src="lib/babylonjs.loaders.min.js"></script>\n<script>globalThis.FERRET_LIB = "/lib/ferret/";</script>\n<script src="main.js"></script>'));
// compressed copies of the glb files (meshopt geometry, WebP textures) next to the page; the server puts them before the repository's art
const oz = spawnSync('node', [path.join(here, 'optimize_glb.mjs'), path.join(OUT, 'glb')], { stdio: 'inherit' });
if (oz.status !== 0) throw new Error('optimize_glb failed');
console.log('built', stamp, 'into', OUT);
