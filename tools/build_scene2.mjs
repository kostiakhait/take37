// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// Builds scene 2 (src/scene2/play2.ts) with the Ferret engine's sources next to this repository into D:/temp/take37/s2/dist (own entry; scene 1's build is not touched).
//   node tools/build_scene2.mjs         then: TAKE37_OUT=D:/temp/take37/s2/dist node tools/serve_set.mjs 4392
import { createRequire } from 'node:module';
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url)), repo = path.resolve(here, '..');
const FERRET = process.env.FERRET_DIR ?? 'D:/REPO/ferret', OUT = process.env.TAKE37_OUT ?? 'D:/temp/take37/s2/dist';
const require = createRequire(path.join(FERRET, 'package.json'));
const { build } = require('esbuild');
const pkgs = fs.readdirSync(path.join(FERRET, 'packages')).filter((p) => fs.existsSync(path.join(FERRET, 'packages', p, 'src', 'index.ts')));
const alias = Object.fromEntries(pkgs.map((p) => [`@ferret/${p}`, path.join(FERRET, 'packages', p, 'src', 'index.ts')]));
const DUNK = path.join(FERRET, 'examples', 'dunkirk', 'src').replace(/\\/g, '/');
// the sample's modules as `@dunkirk/<name>`; its `./shore` is replaced by this game's own (mole 250 m, 600 m field, steeper bed)
const shoreOverride = { name: 'scene2-shore', setup(b) {
  b.onResolve({ filter: /^@dunkirk\// }, (a) => ({ path: path.join(DUNK, a.path.slice(9) + '.ts') }));
  b.onResolve({ filter: /^\.\/shore$/ }, (a) => (a.importer.replace(/\\/g, '/').startsWith(DUNK) ? { path: path.join(repo, 'src', 'scene2', 'shore.ts') } : undefined));
} };
const p2 = (n) => String(n).padStart(2, '0'), d = new Date();
const stamp = `${d.getFullYear()}${p2(d.getMonth() + 1)}${p2(d.getDate())}${p2(d.getHours())}${p2(d.getMinutes())}`;      // the machine's local time
fs.mkdirSync(path.join(OUT, 'lib'), { recursive: true });
await build({
  entryPoints: [path.join(repo, 'src', 'scene2', 'play2.ts')], outfile: path.join(OUT, 'main.js'), bundle: true, format: 'iife', alias, keepNames: true, target: ['es2020'],
  sourcemap: true, logLevel: 'warning', legalComments: 'none', plugins: [shoreOverride], define: { __FERRET_BUILD__: JSON.stringify(stamp), __TAKE37_BUILD__: JSON.stringify(stamp) },
  banner: { js: `globalThis.__TAKE37_BUILD__ = ${JSON.stringify(stamp)};` },
});
const nm = (p) => path.join(FERRET, 'node_modules', p);
fs.copyFileSync(nm('babylonjs/babylon.js'), path.join(OUT, 'lib', 'babylon.js'));
fs.copyFileSync(path.join(FERRET, 'node_modules', '.pnpm', '@babylonjs+core@9.33.1', 'node_modules', '@babylonjs', 'core', 'assets', 'meshopt', 'meshopt_decoder.js'), path.join(OUT, 'lib', 'meshopt_decoder.js'));
fs.copyFileSync(nm('babylonjs-loaders/babylonjs.loaders.min.js'), path.join(OUT, 'lib', 'babylonjs.loaders.min.js'));
const tpl = fs.readFileSync(path.join(repo, 'src', 'scene2', 'play2.template.html'), 'utf8');
fs.writeFileSync(path.join(OUT, 'index.html'), tpl.replace('<!--SCRIPTS-->', '<script src="lib/babylon.js"></script>\n<script src="lib/babylonjs.loaders.min.js"></script>\n<script>globalThis.FERRET_LIB = "/lib/ferret/";</script>\n<script src="main.js"></script>'));
console.log('built', stamp, 'into', OUT);
