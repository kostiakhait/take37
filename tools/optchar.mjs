// node optchar.mjs in.glb out.glb [maxTex=1024]: web copy of a character glb (WebP textures downsized, meshopt geometry); the skinned glb keeps its skeleton and weights
// DROP=<regex> removes the meshes whose names match (unused parts)
import { createRequire } from 'node:module';
import os from 'node:os'; os.setPriority(0, os.constants.priority.PRIORITY_BELOW_NORMAL);
const require = createRequire('D:/REPO/ferret/tools/ue-export/package.json');
const { NodeIO } = require('@gltf-transform/core');
const { EXTMeshoptCompression, EXTTextureWebP, ALL_EXTENSIONS } = require('@gltf-transform/extensions');
const { reorder, quantize, textureCompress, prune, dedup } = require('@gltf-transform/functions');
const { MeshoptEncoder, MeshoptDecoder } = require('meshoptimizer');
const sharp = require('sharp'); sharp.concurrency(2);
const [inp, out, mt] = process.argv.slice(2); const max = +(mt ?? 1024);
await MeshoptEncoder.ready; await MeshoptDecoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.encoder': MeshoptEncoder, 'meshopt.decoder': MeshoptDecoder });
const doc = await io.read(inp);
for (const t of doc.getRoot().listTextures()) console.log(t.getName(), t.getMimeType(), t.getSize());
for (const m of doc.getRoot().listMeshes()) for (const p of m.listPrimitives()) console.log('mesh', m.getName(), p.getAttribute('POSITION').getCount(), p.getIndices()?.getCount());
if (process.env.DROP) { const re = new RegExp(process.env.DROP); for (const n of doc.getRoot().listNodes()) if (n.getMesh() && re.test(n.getMesh().getName())) { n.setMesh(null); console.log('dropped', n.getName()); } }
doc.createExtension(EXTTextureWebP).setRequired(false);
await doc.transform(
  textureCompress({ encoder: sharp, targetFormat: 'webp', quality: 85, resize: [max, max], slots: /^(?!normalTexture$)/ }),
  textureCompress({ encoder: sharp, targetFormat: 'webp', quality: 90, resize: [max, max], slots: /normalTexture$/ }),
  prune(),
  reorder({ encoder: MeshoptEncoder, target: 'size' }),
  quantize({ pattern: /^(NORMAL|COLOR)(_\d+)?$/, patternTargets: /^$/, quantizePosition: 16, quantizeTexcoord: 14, quantizeNormal: 8, quantizeColor: 8, cleanup: false }),
);
doc.createExtension(EXTMeshoptCompression).setRequired(true).setEncoderOptions({ method: EXTMeshoptCompression.EncoderMethod.FILTER });
await io.write(out, doc);
import fs from 'node:fs'; console.log(out, (fs.statSync(out).size / 1e6).toFixed(1), 'MB');
