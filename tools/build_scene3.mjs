// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// Builds scene 3 (src/scene3/play3.ts, the airfield) with the Ferret engine's sources next to this repository into D:/temp/take37/s3/dist (own entry; the other scenes' builds are not touched).
//   node tools/build_scene3.mjs         then: TAKE37_OUT=D:/temp/take37/s3/dist node tools/serve_set.mjs 4393
// The air war sample's modules are `@airwar/world/<name>`, `@airwar/game/<name>`; where one of its world modules imports `./height` it gets src/scene3/height3.ts (the same names in this scene's frame).
import { createRequire } from 'node:module';
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url)), repo = path.resolve(here, '..');
const FERRET = process.env.FERRET_DIR ?? 'D:/REPO/ferret', OUT = process.env.TAKE37_OUT ?? 'D:/temp/take37/s3/dist';
const require = createRequire(path.join(FERRET, 'package.json'));
const { build } = require('esbuild');
const pkgs = fs.readdirSync(path.join(FERRET, 'packages')).filter((p) => fs.existsSync(path.join(FERRET, 'packages', p, 'src', 'index.ts')));
const alias = Object.fromEntries(pkgs.map((p) => [`@ferret/${p}`, path.join(FERRET, 'packages', p, 'src', 'index.ts')]));
for (const f of ['vehicle', 'autoparts', 'crush', 'glass', 'assembly', 'part', 'types', 'view-dents', 'service', 'debris', 'energy', 'view-shards', 'style', 'material', 'rng', 'wood', 'stone', 'fracture', 'motion', 'capability']) alias[`@ferret/destruction/${f}`] = path.join(FERRET, 'packages', 'destruction', 'src', `${f}.ts`);
const ZEP = path.join(FERRET, "examples", "zeppelin", "src", "world").split(path.sep).join("/");
const HELI_HEIGHT = process.env.HELI_HEIGHT ?? 'D:/REPO/take37/src/heli_land_height.ts';   // the helicopter agent's land: the Zeppelin zone with the coast opened to the east (one source)
const AIR = path.join(FERRET, 'examples', 'airwar', 'src').replace(/\\/g, '/'), DUNK = path.join(FERRET, 'examples', 'dunkirk', 'src').replace(/\\/g, '/');
const airwar = { name: 'airwar', setup(b) {
  b.onResolve({ filter: /^@airwar\/height-world$/ }, () => ({ path: path.join(AIR, 'world', 'height.ts') }));
  b.onResolve({ filter: /^@zeppelin\/world\// }, (a) => ({ path: path.join(ZEP, a.path.slice(16) + '.ts') }));
  b.onResolve({ filter: /^\.\/(height|sites)$/ }, (a) => (a.importer.split(path.sep).join('/').startsWith(ZEP) ? { path: path.join(repo, 'src', 'scene3', a.path === './height' ? 'height3.ts' : 'sites3.ts') } : undefined));
  b.onResolve({ filter: /^@zeppelin\/height$/ }, () => ({ path: HELI_HEIGHT }));
  b.onResolve({ filter: /^\/D:\// }, (a) => ({ path: a.path.slice(1) + '.ts' }));
  b.onResolve({ filter: /^@airwar\/spec$/ }, () => ({ path: path.join(FERRET, 'examples', 'airwar', 'spec', 'spec.json') }));
  b.onResolve({ filter: /^@airwar\/(world|game)\// }, (a) => ({ path: path.join(AIR, a.path.slice(8) + '.ts') }));
  b.onResolve({ filter: /^@dunkirk\// }, (a) => ({ path: path.join(DUNK, a.path.slice(9) + '.ts') }));
  b.onResolve({ filter: /^\.\/height$/ }, (a) => (a.importer.replace(/\\/g, '/').startsWith(AIR + '/world') ? { path: path.join(repo, 'src', 'scene3', 'height3.ts') } : undefined));
} };
const p2 = (n) => String(n).padStart(2, '0'), d = new Date();
const stamp = `${d.getFullYear()}${p2(d.getMonth() + 1)}${p2(d.getDate())}${p2(d.getHours())}${p2(d.getMinutes())}`;      // the machine's local time
fs.mkdirSync(path.join(OUT, 'lib'), { recursive: true });
await build({
  entryPoints: [path.join(repo, 'src', 'scene3', 'play3.ts')], outfile: path.join(OUT, 'main.js'), bundle: true, format: 'iife', alias, keepNames: true, target: ['es2020'],
  sourcemap: true, logLevel: 'warning', legalComments: 'none', plugins: [airwar], loader: { '.json': 'json' }, define: { __FERRET_BUILD__: JSON.stringify(stamp), __TAKE37_BUILD__: JSON.stringify(stamp) },
  banner: { js: `globalThis.__TAKE37_BUILD__ = ${JSON.stringify(stamp)};` },
});
const nm = (p) => path.join(FERRET, 'node_modules', p);
fs.copyFileSync(nm('babylonjs/babylon.js'), path.join(OUT, 'lib', 'babylon.js'));
fs.copyFileSync(path.join(FERRET, 'node_modules', '.pnpm', '@babylonjs+core@9.33.1', 'node_modules', '@babylonjs', 'core', 'assets', 'meshopt', 'meshopt_decoder.js'), path.join(OUT, 'lib', 'meshopt_decoder.js'));
fs.copyFileSync(nm('babylonjs-loaders/babylonjs.loaders.min.js'), path.join(OUT, 'lib', 'babylonjs.loaders.min.js'));
const tpl = fs.readFileSync(path.join(repo, 'src', 'scene3', 'play3.template.html'), 'utf8');
fs.writeFileSync(path.join(OUT, 'index.html'), tpl.replace('<!--SCRIPTS-->', '<script src="lib/babylon.js"></script>\n<script src="lib/babylonjs.loaders.min.js"></script>\n<script>globalThis.FERRET_LIB = "/lib/ferret/";</script>\n<script src="main.js"></script>'));
// the airwar sample's glb files (the playable P-51D and the trees) next to the page
fs.mkdirSync(path.join(OUT, 'airwar'), { recursive: true });
for (const f of ['aircraft/mustang.glb', 'aircraft/mustang_lod1.glb', 'trees/spruce.glb', 'trees/spruce.json']) { const d2 = path.join(OUT, 'airwar', f); fs.mkdirSync(path.dirname(d2), { recursive: true }); fs.copyFileSync(path.join(FERRET, 'examples', 'airwar', 'assets', f), d2); }
fs.mkdirSync(path.join(OUT, 'assets', 'trees'), { recursive: true }); for (const f of ['spruce.glb', 'spruce.json']) fs.copyFileSync(path.join(FERRET, 'examples', 'zeppelin', 'assets', 'trees', f), path.join(OUT, 'assets', 'trees', f));
fs.mkdirSync(path.join(OUT, 'assets', 'borrowed'), { recursive: true }); for (const f of ['crown_victoria_cpd87.glb', 'crown_victoria_cpd87_lod1.glb']) fs.copyFileSync(path.join(repo, 'assets', 'borrowed', f), path.join(OUT, 'assets', 'borrowed', f));
console.log('built', stamp, 'into', OUT);
