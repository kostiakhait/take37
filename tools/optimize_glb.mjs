// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// Shrinks the game's glb files for the page: the geometry with EXT_meshopt_compression (positions and uvs stay float and exact, normals are octahedral 8 bit, so node names, accessor bounds and the
// sway pivots in the extra uv sets read the same as in the source), the PNG and JPEG textures as WebP (EXT_texture_webp, which the loader reads already), textures over `maxTex` px halved.
// The sources are never changed: the compressed copies go under <out>/art, <out>/assets, which the server puts before the repository's folders.
//   node tools/optimize_glb.mjs <outDir> [--force]
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url)), repo = path.resolve(here, '..');
const FERRET = process.env.FERRET_DIR ?? 'D:/REPO/ferret';
const require = createRequire(path.join(FERRET, 'tools', 'ue-export', 'package.json'));
const { NodeIO } = require('@gltf-transform/core');
const { EXTMeshoptCompression, EXTTextureWebP, ALL_EXTENSIONS } = require('@gltf-transform/extensions');
const { reorder, quantize, textureCompress } = require('@gltf-transform/functions');
const { MeshoptEncoder, MeshoptDecoder } = require('meshoptimizer');
const sharp = require('sharp');

const outDir = process.argv[2]; const force = process.argv.includes('--force');
if (!outDir) throw new Error('usage: optimize_glb.mjs <outDir> [--force]');
sharp.concurrency(2);
const walk = (dir) => fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => e.isDirectory() ? (e.name === '__pycache__' || e.name === 'reference' ? [] : walk(path.join(dir, e.name))) : e.name.endsWith('.glb') ? [path.join(dir, e.name)] : []);
const only = process.env.ONLY ? new RegExp(process.env.ONLY) : null;
const files = [...walk(path.join(repo, 'art')), ...walk(path.join(repo, 'assets'))].filter((f) => !/street_kit\.glb$/.test(f) && (!only || only.test(f)));
await MeshoptEncoder.ready; await MeshoptDecoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.encoder': MeshoptEncoder, 'meshopt.decoder': MeshoptDecoder });
let before = 0, after = 0, done = 0, kept = 0;
for (const src of files) {
  const rel = path.relative(repo, src), dst = path.join(outDir, rel);
  before += fs.statSync(src).size;
  if (!force && fs.existsSync(dst) && fs.statSync(dst).mtimeMs >= fs.statSync(src).mtimeMs && fs.statSync(dst).mtimeMs >= fs.statSync(fileURLToPath(import.meta.url)).mtimeMs) { after += fs.statSync(dst).size; kept++; continue; }
  const t0 = Date.now(), doc = await io.read(src);
  doc.createExtension(EXTTextureWebP).setRequired(false);
  await doc.transform(
    textureCompress({ encoder: sharp, targetFormat: 'webp', quality: 88, resize: undefined, slots: /^(?!normalTexture$)/ }),
    textureCompress({ encoder: sharp, targetFormat: 'webp', quality: 92, slots: /normalTexture$/ }),
    reorder({ encoder: MeshoptEncoder, target: 'size' }),
    quantize({ pattern: process.env.QALL ? /^(POSITION|NORMAL|COLOR|TEXCOORD_0)$/ : /^(NORMAL|COLOR)(_\d+)?$/, patternTargets: /^$/, quantizePosition: 16, quantizeTexcoord: 14, quantizeNormal: 8, quantizeColor: 8, cleanup: false }),
  );
  doc.createExtension(EXTMeshoptCompression).setRequired(true).setEncoderOptions({ method: EXTMeshoptCompression.EncoderMethod.FILTER });
  fs.mkdirSync(path.dirname(dst), { recursive: true });
  await io.write(dst, doc);
  after += fs.statSync(dst).size; done++;
  console.log(`${rel}: ${(fs.statSync(src).size / 1e6).toFixed(1)} -> ${(fs.statSync(dst).size / 1e6).toFixed(1)} MB, ${((Date.now() - t0) / 1000).toFixed(1)} s`);
}
console.log(`glb: ${files.length} files, ${(before / 1e6).toFixed(0)} -> ${(after / 1e6).toFixed(0)} MB (${done} made, ${kept} up to date)`);
