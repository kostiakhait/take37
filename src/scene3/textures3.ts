// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import { rnd } from './geo3';

/**
 * The textures the asset library does not have, drawn in code (each is listed in ASSETS.md as made for the game): tarmac (the library has no asphalt), the wear of slab joints, stains and cracks laid over
 * the library's concrete, the corrugation of sheet metal (a normal map; the library's steel supplies the colour), sandbags, chain-link, a patchy tarmac lane, the runway numerals, chalky paint.
 * Every one is periodic where it tiles, so no seam shows.
 */
const hash = (x: number, y: number, s: number) => { let h = (Math.imul(x, 374761393) + Math.imul(y, 668265263) + Math.imul(s, 2147483647)) | 0; h = Math.imul(h ^ (h >>> 13), 1274126177); return ((h ^ (h >>> 16)) >>> 0) / 4294967296; };
/** periodic value noise with n cells across the tile */
const pnoise = (u: number, v: number, n: number, s: number) => {
  const x = u * n, y = v * n, i = Math.floor(x), j = Math.floor(y), fx = x - i, fy = y - j, sx = fx * fx * (3 - 2 * fx), sy = fy * fy * (3 - 2 * fy);
  const a = hash(i % n, j % n, s), b = hash((i + 1) % n, j % n, s), c = hash(i % n, (j + 1) % n, s), d = hash((i + 1) % n, (j + 1) % n, s);
  return (a * (1 - sx) + b * sx) * (1 - sy) + (c * (1 - sx) + d * sx) * sy;
};
const make = (scene: BABYLON.Scene, name: string, w: number, h: number, fill: (img: Uint8ClampedArray, w: number, h: number) => void, o: { mips?: boolean; wrap?: boolean; aniso?: number } = {}) => {
  const t = new BABYLON.DynamicTexture(name, { width: w, height: h }, scene, o.mips !== false), ctx = t.getContext() as unknown as CanvasRenderingContext2D, img = ctx.createImageData(w, h);
  fill(img.data, w, h); ctx.putImageData(img, 0, 0); t.update(true);
  t.wrapU = t.wrapV = o.wrap === false ? BABYLON.Texture.CLAMP_ADDRESSMODE : BABYLON.Texture.WRAP_ADDRESSMODE; t.anisotropicFilteringLevel = o.aniso ?? 8; return t;
};
const ctxOf = (t: BABYLON.DynamicTexture) => t.getContext() as unknown as CanvasRenderingContext2D;

/** tarmac: dark grey aggregate with pale chips, tar patches and slow variation; the tile is 3 m */
export function asphaltTexture(scene: BABYLON.Scene, tone = 0.27): BABYLON.DynamicTexture {
  return make(scene, 'asphalt', 512, 512, (d, w, h) => {
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const u = x / w, v = y / h, chip = hash(x, y, 1), grit = hash(x >> 1, y >> 1, 2), big = pnoise(u, v, 4, 3), mid = pnoise(u, v, 16, 4), fine = pnoise(u, v, 64, 5);
      let l = tone + 0.1 * (chip - 0.5) + 0.07 * (grit - 0.5) + 0.07 * (mid - 0.5) + 0.12 * (big - 0.5) + 0.05 * (fine - 0.5);
      if (chip > 0.975) l += 0.22; if (big < 0.3) l -= 0.05;
      const k = (y * w + x) * 4, c = Math.max(0, Math.min(1, l)) * 255; d[k] = c * 0.98; d[k + 1] = c * 0.99; d[k + 2] = c * 1.03; d[k + 3] = 255;
    }
  });
}

/**
 * Concrete slab wear laid over the library's concrete: expansion joints every 7.5 m, tar repairs along some, dark stains and cracks; RGBA (alpha = how much the dark shows). The tile is 30 m (4 slabs).
 */
export function slabOverlay(scene: BABYLON.Scene, seed = 7): BABYLON.DynamicTexture {
  const S = 1024, t = new BABYLON.DynamicTexture('slabs', { width: S, height: S }, scene, true), c = ctxOf(t), r = rnd(seed);
  c.clearRect(0, 0, S, S);
  const slab = S / 4;
  // the stains and tyre-dirty patches first (inside the tile so they do not need to wrap)
  for (let i = 0; i < 60; i++) { const x = 60 + r() * (S - 120), y = 60 + r() * (S - 120), rad = 20 + r() * 90, g = c.createRadialGradient(x, y, 0, x, y, rad); g.addColorStop(0, `rgba(30,28,24,${0.05 + 0.14 * r()})`); g.addColorStop(1, 'rgba(30,28,24,0)'); c.fillStyle = g; c.fillRect(x - rad, y - rad, rad * 2, rad * 2); }
  for (let i = 0; i < 14; i++) { const x = 40 + r() * (S - 80), y = 40 + r() * (S - 80), rad = 6 + r() * 16, g = c.createRadialGradient(x, y, 0, x, y, rad); g.addColorStop(0, 'rgba(15,12,10,0.5)'); g.addColorStop(1, 'rgba(15,12,10,0)'); c.fillStyle = g; c.fillRect(x - rad, y - rad, rad * 2, rad * 2); }
  // cracks: wandering polylines
  c.lineWidth = 1.2;
  for (let i = 0; i < 26; i++) {
    let x = r() * S, y = r() * S, a = r() * 6.283; c.strokeStyle = `rgba(20,18,16,${0.35 + 0.4 * r()})`; c.beginPath(); c.moveTo(x, y);
    const n = 6 + Math.floor(r() * 14); for (let k = 0; k < n; k++) { a += (r() - 0.5) * 1.1; x += Math.cos(a) * (6 + r() * 14); y += Math.sin(a) * (6 + r() * 14); c.lineTo(x, y); if (x < 0 || y < 0 || x > S || y > S) break; } c.stroke();
  }
  // the joints (wrapping): dark 1 cm lines on the slab edges, a tar seal on some
  for (let k = 0; k < 4; k++) {
    const p = k * slab; const seal = r() < 0.5;
    c.fillStyle = 'rgba(14,12,10,0.8)'; c.fillRect(p - 1, 0, 2.4, S); c.fillRect(0, p - 1, S, 2.4); c.fillRect(S - 1.2, 0, 1.2, S); c.fillRect(0, S - 1.2, S, 1.2);
    if (seal) { c.fillStyle = 'rgba(10,9,8,0.55)'; c.fillRect(p - 3, 0, 6, S); }
    else { c.fillStyle = 'rgba(10,9,8,0.4)'; c.fillRect(0, p - 3, S, 6); }
  }
  t.update(true); t.hasAlpha = true; t.wrapU = t.wrapV = BABYLON.Texture.WRAP_ADDRESSMODE; t.anisotropicFilteringLevel = 8; return t;
}

/** the wear of tarmac: patches of lighter new surface, cracks, oil, two wheel tracks fade, as an RGBA overlay (a tile of 24 m) */
export function tarmacOverlay(scene: BABYLON.Scene, seed = 11): BABYLON.DynamicTexture {
  const S = 1024, t = new BABYLON.DynamicTexture('tarmacwear', { width: S, height: S }, scene, true), c = ctxOf(t), r = rnd(seed);
  c.clearRect(0, 0, S, S);
  for (let i = 0; i < 40; i++) { const x = 40 + r() * (S - 140), y = 40 + r() * (S - 140), w = 40 + r() * 220, h = 30 + r() * 160, tone = r() < 0.5 ? 'rgba(18,18,18,' : 'rgba(150,150,145,'; c.fillStyle = tone + (0.08 + 0.12 * r()) + ')'; c.fillRect(x, y, w, h); }
  for (let i = 0; i < 70; i++) { const x = 30 + r() * (S - 60), y = 30 + r() * (S - 60), rad = 12 + r() * 60, g = c.createRadialGradient(x, y, 0, x, y, rad); g.addColorStop(0, `rgba(8,8,10,${0.2 + 0.3 * r()})`); g.addColorStop(1, 'rgba(8,8,10,0)'); c.fillStyle = g; c.fillRect(x - rad, y - rad, rad * 2, rad * 2); }
  c.lineWidth = 1.4;
  for (let i = 0; i < 40; i++) { let x = r() * S, y = r() * S, a = r() * 6.283; c.strokeStyle = `rgba(6,6,6,${0.4 + 0.4 * r()})`; c.beginPath(); c.moveTo(x, y); for (let k = 0; k < 18; k++) { a += (r() - 0.5) * 1.3; x += Math.cos(a) * (5 + r() * 12); y += Math.sin(a) * (5 + r() * 12); c.lineTo(x, y); } c.stroke(); }
  t.update(true); t.hasAlpha = true; t.wrapU = t.wrapV = BABYLON.Texture.WRAP_ADDRESSMODE; t.anisotropicFilteringLevel = 8; return t;
}

/** the normal map of corrugated sheet: four corrugations across the tile (0.304 m), the profile a rounded sine; the tile is 0.304 m on both sides */
export function corrugationNormal(scene: BABYLON.Scene, strength = 1.6): BABYLON.DynamicTexture {
  return make(scene, 'corrugation', 128, 128, (d, w, h) => {
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const u = x / w, slope = Math.cos(u * Math.PI * 2 * 4) * strength, nx = -slope, nz = 1, l = Math.hypot(nx, nz), k = (y * w + x) * 4;
      d[k] = (nx / l * 0.5 + 0.5) * 255; d[k + 1] = 128; d[k + 2] = (nz / l * 0.5 + 0.5) * 255; d[k + 3] = 255;
    }
  });
}

/** sandbags: bonded courses of rounded bags in sandy hessian with seams, a tile 1.2 x 0.8 m (four bags across, four courses) */
export function sandbagTexture(scene: BABYLON.Scene): BABYLON.DynamicTexture {
  const S = 512, t = new BABYLON.DynamicTexture('sandbags', { width: S, height: S }, scene, true), c = ctxOf(t), r = rnd(31);
  c.fillStyle = '#5a5039'; c.fillRect(0, 0, S, S);
  const rows = 4, bh = S / rows, bw = S / 2;
  for (let row = 0; row < rows; row++) for (let k = -1; k < 3; k++) {
    const x = k * bw + (row % 2 ? bw / 2 : 0), y = row * bh, tone = 150 + r() * 60, grad = c.createLinearGradient(0, y, 0, y + bh);
    grad.addColorStop(0, `rgb(${tone * 0.78},${tone * 0.7},${tone * 0.5})`); grad.addColorStop(0.5, `rgb(${tone},${tone * 0.9},${tone * 0.65})`); grad.addColorStop(1, `rgb(${tone * 0.62},${tone * 0.56},${tone * 0.4})`);
    c.fillStyle = grad; c.beginPath(); (c as unknown as { roundRect: (...a: number[]) => void }).roundRect(x + 3, y + 3, bw - 6, bh - 6, 26); c.fill();
    c.strokeStyle = 'rgba(40,34,22,0.5)'; c.lineWidth = 2; c.stroke();
    for (let i = 0; i < 160; i++) { c.fillStyle = `rgba(${r() < 0.5 ? '30,24,14' : '230,215,170'},0.16)`; c.fillRect(x + 6 + r() * (bw - 12), y + 6 + r() * (bh - 12), 2, 2); }
    c.strokeStyle = 'rgba(40,34,22,0.35)'; c.lineWidth = 1.5; c.beginPath(); c.moveTo(x + bw / 2, y + 8); c.lineTo(x + bw / 2 + (r() - 0.5) * 20, y + bh - 8); c.stroke();
  }
  t.update(true); t.wrapU = t.wrapV = BABYLON.Texture.WRAP_ADDRESSMODE; t.anisotropicFilteringLevel = 8; return t;
}

/** chain-link: a diamond lattice with an alpha (dark galvanised wire), a tile of 1 m; double-sided */
export function chainLinkTexture(scene: BABYLON.Scene): BABYLON.DynamicTexture {
  const S = 128, t = new BABYLON.DynamicTexture('chainlink', { width: S, height: S }, scene, true), c = ctxOf(t);
  c.clearRect(0, 0, S, S); c.strokeStyle = 'rgba(150,152,150,1)'; c.lineWidth = 3;
  for (let k = -2; k <= 4; k++) { c.beginPath(); c.moveTo(k * S / 4, 0); c.lineTo(k * S / 4 + S, S); c.stroke(); c.beginPath(); c.moveTo(k * S / 4 + S, 0); c.lineTo(k * S / 4, S); c.stroke(); }
  t.update(true); t.hasAlpha = true; t.wrapU = t.wrapV = BABYLON.Texture.WRAP_ADDRESSMODE; t.anisotropicFilteringLevel = 8; return t;
}

/** a worn white (paint): chalky paint scratched by tyres, an RGBA tile of 4 m; colour off-white */
export function paintTexture(scene: BABYLON.Scene, wear = 0.35): BABYLON.DynamicTexture {
  const t = make(scene, 'paint', 256, 256, (d, w, h) => {
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const u = x / w, v = y / h, n = pnoise(u, v, 8, 21) * 0.5 + pnoise(u, v, 32, 22) * 0.3 + hash(x, y, 23) * 0.2, k = (y * w + x) * 4;
      const a = Math.max(0, Math.min(1, 1 - wear * Math.max(0, n - 0.35) * 2.2 - (hash(x >> 2, y >> 2, 24) > 0.94 ? 0.5 : 0)));
      d[k] = 235; d[k + 1] = 235; d[k + 2] = 228; d[k + 3] = a * 255;
    }
  });
  t.hasAlpha = true; return t;
}

/** a runway numeral pair ("36") in blocky paint, as an RGBA texture 512 x 512 that reads upright seen from the approach end */
export function numeralTexture(scene: BABYLON.Scene, text: string): BABYLON.DynamicTexture {
  const S = 512, t = new BABYLON.DynamicTexture('numeral' + text, { width: S, height: S }, scene, true), c = ctxOf(t);
  c.clearRect(0, 0, S, S); c.fillStyle = 'rgba(235,235,228,0.95)'; c.font = '900 420px Impact, "Arial Black", sans-serif'; c.textAlign = 'center'; c.textBaseline = 'middle';
  c.scale(1, 1); c.fillText(text, S / 2, S / 2 + 10, S - 30);
  // wear: scratch the paint with noise
  const img = c.getImageData(0, 0, S, S), d = img.data;
  for (let y = 0; y < S; y++) for (let x = 0; x < S; x++) { const k = (y * S + x) * 4; if (d[k + 3]! > 0) { const n = pnoise(x / S, y / S, 12, 33) * 0.6 + hash(x, y, 34) * 0.4; d[k + 3] = d[k + 3]! * Math.max(0.35, 1 - 0.7 * Math.max(0, n - 0.5)); } }
  c.putImageData(img, 0, 0); t.update(true); t.hasAlpha = true; t.anisotropicFilteringLevel = 8; return t;
}

/** a country lane: tarmac with crumbling edges fading into the verge's mud (an RGBA across the lane, 1 tile = 6 m along): the middle of the texture is the road */
export function laneTexture(scene: BABYLON.Scene): BABYLON.DynamicTexture {
  return make(scene, 'lane', 256, 256, (d, w, h) => {
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const u = x / w, v = y / h, cx = Math.abs(u - 0.5) * 2, ed = cx + 0.12 * (pnoise(0, v, 16, 41) - 0.5) + 0.05 * (hash(x, y, 42) - 0.5);
      const road = ed < 0.74 ? 1 : 0, shoulder = Math.max(0, 1 - Math.abs(ed - 0.82) / 0.28);
      const grit = hash(x, y, 43), big = pnoise(u, v, 8, 44), tone = 0.27 + 0.1 * (grit - 0.5) + 0.1 * (big - 0.5) + (grit > 0.98 ? 0.2 : 0);
      const rut = 0.04 * (Math.exp(-(((u - 0.32) * 12) ** 2)) + Math.exp(-(((u - 0.68) * 12) ** 2)));
      const mud = 0.2 + 0.1 * (pnoise(u, v, 12, 45) - 0.5), k = (y * w + x) * 4;
      const l = road ? tone - rut : mud, a = road ? 1 : Math.max(0, Math.min(1, shoulder * 1.0 * (1 - Math.max(0, ed - 1.05) * 3)));
      d[k] = (l * (road ? 0.98 : 1.45)) * 255; d[k + 1] = (l * (road ? 0.99 : 1.15)) * 255; d[k + 2] = (l * (road ? 1.03 : 0.8)) * 255; d[k + 3] = (road ? 1 : a) * 255;
    }
  }, { aniso: 8 });
}

/** a soft round shadow blob (a dark disc fading out), for the contact shadow under things the sun's shadow cannot reach */
export function blobTexture(scene: BABYLON.Scene): BABYLON.DynamicTexture {
  const S = 128, t = new BABYLON.DynamicTexture('blob', { width: S, height: S }, scene, true), c = ctxOf(t);
  const g = c.createRadialGradient(S / 2, S / 2, 0, S / 2, S / 2, S / 2); g.addColorStop(0, 'rgba(0,0,0,0.55)'); g.addColorStop(0.6, 'rgba(0,0,0,0.25)'); g.addColorStop(1, 'rgba(0,0,0,0)');
  c.clearRect(0, 0, S, S); c.fillStyle = g; c.fillRect(0, 0, S, S); t.update(true); t.hasAlpha = true; return t;
}
