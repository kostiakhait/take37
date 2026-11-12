// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// Builds the set scene (src/main.ts) with the Ferret engine's sources next to this repository, into D:/temp/take37/land/dist (not into the repository).
//   node tools/build_play.mjs           builds the playable scene 1 (src/play.ts) into D:/temp/take37/play/dist
//   node tools/serve_set.mjs [port]     serves the page, the art, the assets and the Ferret asset library
import { createRequire } from 'node:module';
import path from 'node:path';
import fs from 'node:fs';
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
fs.copyFileSync(nm('babylonjs-loaders/babylonjs.loaders.min.js'), path.join(OUT, 'lib', 'babylonjs.loaders.min.js'));
const tpl = fs.readFileSync(path.join(repo, 'src', 'play.template.html'), 'utf8');
fs.writeFileSync(path.join(OUT, 'index.html'), tpl.replace('<!--SCRIPTS-->', '<script src="lib/babylon.js"></script>\n<script src="lib/babylonjs.loaders.min.js"></script>\n<script>globalThis.FERRET_LIB = "/lib/ferret/";</script>\n<script src="main.js"></script>'));
console.log('built', stamp, 'into', OUT);
