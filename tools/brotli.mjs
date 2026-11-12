// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// Brotli copies of the files the page loads, cached by content (D:/temp/take37/brcache/<sha1>-<quality>.br), for the preview server (nginx brotli_static serves `<file>.br`) and the local server.
// The meshopt glb files still compress by 40-45 percent under brotli (gzip 38), the scripts by 85 percent.
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import crypto from 'node:crypto';

const CACHE = 'D:/temp/take37/brcache';
export const brotliable = (f) => /\.(js|glb|json|wasm|html|ferret|map|svg)$/.test(f) && fs.statSync(f).size > 1024;
/** path of the brotli copy of `file` (made if not cached); quality 11 for scripts (they are few), 9 for the big glb files */
export function brotliOf(file) {
  const buf = fs.readFileSync(file), q = /\.glb$/.test(file) ? 9 : 11;
  const out = path.join(CACHE, `${crypto.createHash('sha1').update(buf).digest('hex')}-${q}.br`);
  if (!fs.existsSync(out)) {
    fs.mkdirSync(CACHE, { recursive: true });
    const z = zlib.brotliCompressSync(buf, { params: { [zlib.constants.BROTLI_PARAM_QUALITY]: q, [zlib.constants.BROTLI_PARAM_SIZE_HINT]: buf.length, [zlib.constants.BROTLI_PARAM_LGWIN]: 24 } });
    fs.writeFileSync(out + '.tmp', z); fs.renameSync(out + '.tmp', out);
  }
  return out;
}
