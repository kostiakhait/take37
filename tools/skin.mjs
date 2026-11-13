// Skin texture touch-ups for the TAKE 37 characters (game code, outside the engine).
import { createRequire } from 'node:module'
const sharp = createRequire(import.meta.url)('D:/REPO/ferret/node_modules/.pnpm/sharp@0.34.5/node_modules/sharp')

const ell = (x, y, cx, cy, rx, ry, soft) => { const d = Math.hypot((x - cx) / rx, (y - cy) / ry); return Math.max(0, Math.min(1, (1 - d) / soft)) }
/** the shaved zone in 1024-px texture coordinates: 0..1 */
function shaveMask(X, Y) {
  let m = ell(X, Y, 520, 650, 400, 235, 0.65)                       // lower face, jaw, sideburns
  m *= 1 - ell(X, Y, 512, 600, 118, 52, 0.4)                        // lips
  m *= 1 - ell(X, Y, 512, 515, 95, 38, 0.4)                         // nostrils
  return Math.max(0, m)
}

/** Clean-shaven: the preset's face texture has a stubble shadow on chin, jaw, upper lip and sideburns. The low-frequency tone there is pulled to the cheek colour,
 *  the speckle is mostly removed, the lips and the nostrils are untouched. png: the face base colour map (square), returns a png. */
export async function shave(png, { strength = 0.95, keepDetail = 0.3 } = {}) {
  const f = await sharp(png).ensureAlpha().raw().toBuffer({ resolveWithObject: true }), W = f.info.width, s = W / 1024, N = W * W
  const blur = async (r) => (await sharp(f.data, { raw: f.info }).blur(r).raw().toBuffer())
  const low = await blur(6 * s), mid = await blur(2.2 * s)
  // reference skin: cheeks under the eyes and the forehead, from the blurred map
  let ref = [0, 0, 0], n = 0
  for (const [cx, cy] of [[330, 455], [700, 455], [350, 440], [680, 440]]) { const i = (Math.round(cy * s) * W + Math.round(cx * s)) * 4; for (let k = 0; k < 3; k++) ref[k] += low[i + k]; n++ }
  ref = ref.map((v) => v / n)
  const out = Buffer.from(f.data)
  for (let y = 0; y < W; y++) for (let x = 0; x < W; x++) {
    let m = shaveMask(x / s, y / s)
    m *= strength
    if (m <= 0) continue
    const i = (y * W + x) * 4
    for (let k = 0; k < 3; k++) {
      const hf = f.data[i + k] - mid[i + k], tone = ref[k] + (low[i + k] - ref[k]) * 0.4
      out[i + k] = Math.max(0, Math.min(255, f.data[i + k] * (1 - m) + (tone + hf * keepDetail) * m))
    }
  }
  return sharp(out, { raw: f.info }).png().toBuffer()
}

/** the same zone of the face normal map: the stubble grain is smoothed away, the forms of the face stay (png: the tangent-space normal map, square) */
export async function shaveNormal(png, { strength = 0.95 } = {}) {
  const f = await sharp(png).ensureAlpha().raw().toBuffer({ resolveWithObject: true }), W = f.info.width, s = W / 1024
  const low = await sharp(f.data, { raw: f.info }).blur(2 * s).raw().toBuffer(), out = Buffer.from(f.data)
  for (let y = 0; y < W; y++) for (let x = 0; x < W; x++) { const m = shaveMask(x / s, y / s) * strength; if (m <= 0) continue; const i = (y * W + x) * 4
    for (let k = 0; k < 3; k++) out[i + k] = f.data[i + k] * (1 - m) + low[i + k] * m }
  return sharp(out, { raw: f.info }).png().toBuffer()
}

/** Bright make-up on the face base colour map (square png, the MetaHuman UV layout): lipstick on the lips, eyeshadow on the lids, blush on the cheeks, a darker lash line. */
export async function makeup(png, { lip = [175, 18, 38], shadow = [205, 120, 95], blush = [215, 105, 100], lipAlpha = 0.6, shadowAlpha = 0.45, blushAlpha = 0.22 } = {}) {
  const f = await sharp(png).ensureAlpha().raw().toBuffer({ resolveWithObject: true }), W = f.info.width, s = W / 1024, out = Buffer.from(f.data)
  const mix = (i, c, a, keepLum = 0.5) => { const lum = (f.data[i] + f.data[i + 1] + f.data[i + 2]) / 3, k = 1 - keepLum + keepLum * (lum / 150); for (let q = 0; q < 3; q++) out[i + q] = Math.max(0, Math.min(255, out[i + q] * (1 - a) + c[q] * k * a)) }
  for (let y = 0; y < W; y++) for (let x = 0; x < W; x++) {
    const X = x / s, Y = y / s, i = (y * W + x) * 4
    const redness = Math.max(0, Math.min(1, (f.data[i] - (f.data[i + 1] + f.data[i + 2]) / 2 - 25) / 45))
    const lipA = ell(X, Y, 512, 603, 100, 40, 0.2) * redness**2
    if (lipA > 0) mix(i, lip, lipA * lipAlpha, 0.55)
    const lid = Math.max(ell(X, Y, 385, 380, 62, 24, 0.7), ell(X, Y, 640, 380, 62, 24, 0.7))
    if (lid > 0) mix(i, shadow, lid * shadowAlpha, 0.6)
    const lash = Math.max(ell(X, Y, 385, 392, 58, 7, 0.8), ell(X, Y, 640, 392, 58, 7, 0.8))
    if (lash > 0) mix(i, [40, 22, 20], lash * 0.55, 0.3)
    const bl = Math.max(ell(X, Y, 320, 500, 95, 62, 0.9), ell(X, Y, 705, 500, 95, 62, 0.9))
    if (bl > 0) mix(i, blush, bl * blushAlpha, 0.5)
  }
  return sharp(out, { raw: f.info }).png().toBuffer()
}

/** the preset's lash card texture recoloured (rgb of the opaque part), the alpha untouched */
export async function darkLashes(png, rgb, alpha = 1) {
  const f = await sharp(png).ensureAlpha().raw().toBuffer({ resolveWithObject: true }), out = Buffer.from(f.data)
  for (let i = 0; i < out.length; i += 4) { const lum = Math.max(0.5, Math.min(1.2, (f.data[i] + f.data[i + 1] + f.data[i + 2]) / 3 / 60)); for (let k = 0; k < 3; k++) out[i + k] = Math.min(255, rgb[k] * lum); out[i + 3] = out[i + 3] * alpha }
  return sharp(out, { raw: f.info }).png().toBuffer()
}
