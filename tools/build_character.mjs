// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// Test characters on the MetaHuman base: node character.mjs <girl|wizard|witch> [out.glb]
// preset export (head/body DNA + textures) + strand grooms bound to the head + garments (robe/dress, belt, hat) -> one glb for look.mjs
import fs from 'node:fs'
import { createRequire } from 'node:module'
const sharp = createRequire(import.meta.url)('D:/REPO/ferret/node_modules/.pnpm/sharp@0.34.5/node_modules/sharp')
import { buildGlb } from 'file:///D:/REPO/ferret/tools/humans/mh/toglb.mjs'
import { readDna } from 'file:///D:/REPO/ferret/tools/humans/mh/dna.mjs'
import { readStrands, ribbons, bindToHead } from 'file:///D:/REPO/ferret/tools/humans/mh/strands.mjs'
import { scalpTint, scalpMatte } from 'file:///D:/REPO/ferret/tools/humans/mh/groom.mjs'
import { robe, belt, hat, fabric, bodyRegions, mantle } from 'file:///D:/REPO/ferret/tools/humans/mh/garment.mjs'
import { bullHead, growFur } from 'file:///D:/REPO/ferret/tools/humans/mh/bull.mjs'

const RED = { root: [0.16, 0.035, 0.012], tip: [0.36, 0.1, 0.03] }
const BR = (c, t, w = 0.0001) => ({ root: c, tip: t, w, seg: 4 })
const SPECS = {
  matthew: { export: 'Orlando', scalp: [0.12, 0.03, 0.01], clothing: 'matthew', grooms: [
    { g: 'Hair__Hair_M_Layered', ...RED },
    { g: 'Eyebrows__Eyebrows_M_Natural', ...BR([0.14, 0.03, 0.01], [0.26, 0.07, 0.02]) }] },
  edward: { export: 'T37_Edward', scalp: [0.02, 0.015, 0.01], clothing: 'edward', grooms: [
    { g: 'Hair__Hair_M_TwistedBraids', root: [0.016, 0.012, 0.008], tip: [0.03, 0.022, 0.015], jitter: 0.15 },
    { g: 'Eyebrows__Eyebrows_M_Full', ...BR([0.02, 0.014, 0.01], [0.04, 0.03, 0.02]) }] },
  emily: { export: 'Girl', scalp: [0.35, 0.26, 0.1], clothing: process.env.DRESS ?? 'emilyA', grooms: [
    { g: 'Hair__Hair_L_Straight', root: [0.3, 0.2, 0.07], tip: [0.62, 0.48, 0.2] },
    { g: 'Eyebrows__Eyebrows_M_SlightArch', ...BR([0.2, 0.13, 0.05], [0.3, 0.21, 0.09]) }] },
  vincent: { export: 'Walter', scalp: [0.3, 0.29, 0.27], clothing: 'vincent', grooms: [
    { g: 'Hair__Hair_L_MessyClumps', root: [0.3, 0.29, 0.27], tip: [0.62, 0.6, 0.57] },
    { g: 'Beards__Beard_L_Messy', root: [0.33, 0.32, 0.3], tip: [0.62, 0.6, 0.57], w: 0.00017, extend: 0.1 },
    { g: 'Eyebrows__Eyebrows_L_Scraggly', root: [0.42, 0.4, 0.37], tip: [0.65, 0.63, 0.6], w: 0.0001, seg: 4 }] },
}
SPECS.arnold = { export: 'Victor', scalp: [0.05, 0.04, 0.03], clothing: 'arnold', grooms: [
  { g: 'Hair__Hair_S_SlickBack', root: [0.04, 0.03, 0.02], tip: [0.1, 0.075, 0.05] },
  { g: 'Eyebrows__Eyebrows_M_SlightArch', ...BR([0.04, 0.03, 0.02], [0.08, 0.06, 0.04]) }] }
SPECS.director = { export: 'Bruce', scalp: [0.1, 0.08, 0.06], clothing: 'director', grooms: [
  { g: 'Hair__Hair_L_MessyClumps', root: [0.07, 0.05, 0.035], tip: [0.2, 0.15, 0.1] },
  { g: 'Beards__Beard_L_Messy', root: [0.08, 0.06, 0.04], tip: [0.22, 0.17, 0.12], w: 0.00017, extend: 0.07 },
  { g: 'Mustaches__Mustache_L_Messy', root: [0.08, 0.06, 0.04], tip: [0.2, 0.15, 0.1], w: 0.00016, seg: 6 },
  { g: 'Eyebrows__Eyebrows_L_Scraggly', root: [0.08, 0.06, 0.04], tip: [0.2, 0.15, 0.1], w: 0.0001, seg: 4 }] }
const [who = 'girl', out = `D:/temp/take37/chars/${who}.glb`] = process.argv.slice(2)
// TIER=full (the look renders), desktop (library: LOD1, every 2nd strand, wider) or low (LOD3, every 8th strand, half the segments)
const TIER = { full: { lod: 0, step: 1, wk: 1, segk: 1, tex: 0 }, desktop: { lod: 1, step: 2, wk: 1.4, segk: 1, tex: 2048 }, low: { lod: 3, step: 8, wk: 2.6, segk: 0.5, tex: 512 } }[process.env.TIER ?? 'full']
const S = SPECS[who] ?? (who.startsWith('bare_') ? { export: who.slice(5), grooms: [] } : who.startsWith('hair_') ? { export: who.split('_')[1], scalp: [0.02, 0.015, 0.01], grooms: [{ g: 'Hair__' + who.split('_').slice(2).join('_'), root: [0.016, 0.012, 0.008], tip: [0.03, 0.022, 0.015], jitter: 0.15 }] } : undefined), DIR = `D:/temp/mh/export/${S.export}_DCC/${S.export}`, TEX = `D:/temp/mh/export/${S.export}_TEX`
const dna = readDna(fs.readFileSync(`${DIR}/head.dna`)), body = readDna(fs.readFileSync(`${DIR}/body.dna`))
const hm = dna.meshes.find((x) => x.name === 'head_lod0_mesh'), eye = dna.meshes.find((x) => x.name === 'eyeLeft_lod0_mesh')
const gdy = eye.positions.ys.reduce((a, b) => a + b, 0) / eye.positions.ys.length / 100 - 1.6822 + 0.18
const strandGrooms = []
let hairPts = null
for (const G of S.grooms) {
  const st = readStrands(`D:/temp/mh/strands/${G.g}.hair`); const b = bindToHead(st, hm, gdy, { facial: !G.g.startsWith('Hair__') }); G.st = st
  if (G.extend) { // longer beard: strands below the mouth hang further down (and a little forward, clear of the chest)
    const eyeY = gdy + 1.6822 - 0.18; let off = 0
    for (let s = 0; s < st.nS; s++) { const c = st.counts[s], ry = st.pos[off * 3 + 1] + gdy, k0 = Math.max(0, Math.min(1, (eyeY - 0.07 - ry) / 0.05))
      if (k0 > 0) for (let k = 1; k < c; k++) { const t = k / (c - 1), i = (off + k) * 3; st.pos[i + 1] -= G.extend * k0 * t ** 1.3; st.pos[i + 2] += 0.035 * k0 * t ** 2 }
      off += c }
  }
  console.log(G.g, st.nS, 'strands, bound', b.meanMoveMm.toFixed(1), 'mm, miss', b.miss)
  if (G.g.startsWith('Hair__')) hairPts = st.pos
}
// scalp tint under the main hair
const hairName = S.grooms[0]?.g.split('__')[1]
const headBasecolor = hairName && await scalpTint(`${TEX}/face_BASECOLOR.png`, 'D:/temp/mh/grooms', hairName, { color: S.scalp, strength: 0.9 })
const headSrmf = hairName && await scalpMatte(`${DIR}/Maps/Head_SRMF.png`, 'D:/temp/mh/grooms', hairName)
// garments
const extraMeshes = []
if (S.robe) {
  const fab = await fabric({ color: S.robe.color, weave: S.robe.leather ? 6 : 48, noise: S.robe.leather ? 0.6 : 0.3 })
  const mat = S.robe.leather ? { base: fab.base, normal: fab.normal, normalScale: 0.25, rough: 0.62, double: true }
    : { base: fab.base, normal: fab.normal, normalScale: 0.6, rough: 0.92, sheen: S.robe.color.map((c) => Math.min(1, c * 1.6 + 0.04)), sheenRough: 0.45, double: true }
  const R = robe(body, { ...S.robe, headMesh: hm, material: mat }); extraMeshes.push(...R.meshes)
  if (S.belt) extraMeshes.push(belt(R, R.meshes.at(-1), { thick: S.beltThick ?? 0.016, material: { color: S.belt, rough: 0.8 } }))
  console.log('robe waist', R.waist.toFixed(3), 'floor', R.floor.toFixed(3))
}
let hide = null, raise = 0
if (S.clothing) {
  const { dressOutfit } = await import('file:///D:/REPO/ferret/tools/clothing/outfit.mjs'), { OUTFITS } = await import('./outfits.mjs')
  const r = await dressOutfit(S.export, OUTFITS[S.clothing], { lod: TIER.lod, maxTex: TIER.tex || 4096 })
  extraMeshes.push(...r.extraMeshes); hide = r.hide; raise = r.raise
  // the head mesh carries the jaw and the neck: never hide any of it (a collar must not take the chin away)
  if (hide.has('head')) hide.set('head', new Uint8Array(hide.get('head').length))
  // the cap presses the hair: strands above the cap's band are pulled under the crown
  const capD = r.dressed.find((d) => d.name === 'cap')
  if (capD && hairPts) { let y0 = Infinity; for (let i = 1; i < capD.positions.length; i += 3) y0 = Math.min(y0, capD.positions[i])
    for (let i = 0; i < hairPts.length; i += 3) { const y = hairPts[i + 1] + gdy; if (y < y0 - 0.005) continue; hairPts[i + 1] = Math.min(hairPts[i + 1], y0 - gdy - 0.002 + (y - y0) * 0.05) } }
}
if (S.hat && hairPts) {
  // hat sits on the hair: the brim height where the hair is widest just above the brows; radius = hair extent there + 1 cm
  let top = -1e9; for (let i = 1; i < hairPts.length; i += 3) top = Math.max(top, hairPts[i] + gdy)
  const y = top - 0.075; let cx = 0, cz = 0, n = 0, rx = 0, rz = 0
  for (let i = 0; i < hairPts.length; i += 3) { const yy = hairPts[i + 1] + gdy; if (Math.abs(yy - y) < 0.012) { cx += hairPts[i]; cz += hairPts[i + 2]; n++ } }
  cx /= n; cz /= n
  for (let i = 0; i < hairPts.length; i += 3) { const yy = hairPts[i + 1] + gdy; if (Math.abs(yy - y) < 0.012) { rx = Math.max(rx, Math.abs(hairPts[i] - cx)); rz = Math.max(rz, Math.abs(hairPts[i + 2] - cz)) } }
  const fab = await fabric({ color: S.hat.color, weave: 40, noise: 0.35, seed: 9 })
  // the hat presses the hair: everything above the brim is pulled inside the cone
  const hrx = rx * 0.97 + 0.006, hrz = rz * 0.97 + 0.006
  for (let i = 0; i < hairPts.length; i += 3) { const yy = hairPts[i + 1] + gdy - y; if (yy <= -0.01) continue
    const s = Math.max(0.05, 1 - Math.max(0, yy) / S.hat.height) * 0.9, dx = (hairPts[i] - cx) / hrx, dz = (hairPts[i + 2] - cz) / hrz, r = Math.hypot(dx, dz)
    const f = Math.min(1, (yy + 0.01) / 0.02); if (r > s) { const k = 1 - f + f * (s / r); hairPts[i] = cx + dx * k * hrx; hairPts[i + 2] = cz + dz * k * hrz }
    if (yy > 0.05) hairPts[i + 1] = y - gdy + 0.05 + (yy - 0.05) * 0.3 }
  extraMeshes.push(hat({ ...S.hat, rigid: 'head', centre: [cx, cz], y, rx: hrx, rz: hrz, material: { base: fab.base, normal: fab.normal, normalScale: 0.5, rough: 0.9, sheen: S.hat.color.map((c) => Math.min(1, c * 1.2 + 0.015)), sheenRough: 0.6, double: true } }))
  console.log('hat at', y.toFixed(3), 'r', rx.toFixed(3), rz.toFixed(3))
}
let kinds = null
if (S.bull) {
  // the human head goes; the bull head sits on the top of the body's neck
  const bm = body.meshes.find((m) => m.name === 'body_lod0_mesh'), reg = bodyRegions(body, bm)
  let top = -1e9; for (let i = 0; i < bm.positions.xs.length; i++) top = Math.max(top, bm.positions.ys[i] * 0.01)
  let cx = 0, cz = 0, n = 0; for (let i = 0; i < bm.positions.xs.length; i++) if (bm.positions.ys[i] * 0.01 > top - 0.02) { cx += bm.positions.xs[i] * 0.01; cz += bm.positions.zs[i] * 0.01; n++ }
  const at = [cx / n, top + 0.045, cz / n - 0.02]
  const B = bullHead({ at, scale: S.bull.scale })
  // fur mantle over the shoulders hides where the bull neck enters the body
  const M = mantle(body, { headMesh: hm, material: { color: S.bull.fur.map((c) => c * 0.8), rough: 0.9 } })
  extraMeshes.push(M)
  const mf = growFur(M, { count: 140000, seed: 11, length: (p) => 0.05 + 0.05 * Math.max(0, Math.min(1, (M.top - 0.06 - p[1]) / 0.12)), flow: (p) => [p[0] * 0.6, -1, (p[2] - at[2]) * 0.5], curl: () => 0.9, lift: 0.5, seg: 6 })
  strandGrooms.push({ name: 'mantle_fur', dy: 0, ribbons: ribbons(mf, { step: 1, seg: 6, w: 0.00018, root: S.bull.fur, tip: S.bull.furTip.map((c) => c * 1.15), jitter: 0.4, shadowK: 0.5 }) })
  extraMeshes.push(...B.meshes); kinds = ['body']
  strandGrooms.push({ name: 'bull_fur', dy: 0, ribbons: ribbons(B.fur, { step: 1, seg: 5, w: 0.00016, root: S.bull.fur, tip: S.bull.furTip, jitter: 0.35, shadowK: 0.5 }) })
  console.log('bull at', at.map((x) => x.toFixed(3)), 'fur', B.fur.nS, 'head verts', B.raw.pos.length / 3)
}
for (const G of S.grooms) strandGrooms.push({ name: G.g.split('__')[1], ribbons: ribbons(G.st, { step: G.step ?? TIER.step, seg: Math.max(3, Math.round((G.seg ?? 8) * TIER.segk)), w: (G.w ?? 0.0002) * (G.step ? 1 : TIER.wk), root: G.root, tip: G.tip, jitter: G.jitter ?? 0.3, shadowK: 0.5 }) })
fs.writeFileSync(out, await buildGlb(DIR, { hide, raise, skin: process.env.SKIN === '1', headLod: TIER.lod, bodyLod: TIER.lod, texMax: TIER.tex, headSrmf, texDir: TEX, strandGrooms, extraMeshes, headBasecolor, kinds }))
console.log(out)
