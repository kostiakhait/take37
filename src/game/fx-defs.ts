// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// Effects of scene 1 that the engine's catalogue does not have as such, written in the module's own definition language with its builders (puff, streaks, glow): a burst of collision sparks, the scrape of metal on asphalt,
// the glitter of breaking glass, tyre smoke with its black mark, a dirt kick, a fuel spill, a flash with a shock ring for chain blasts. Every size and count follows a parameter that the game fills from the physics event
// (energy in joules, speed in m/s, fuel in kilograms); the numbers that are art (colours, flicker) are marked as such. No Babylon here.
import { puff, streaks, glow, FULL_CATALOG, type VfxDef, type Rgb } from '@ferret/vfx';

const E = '(max(energy, 100) / 1000)';           // energy in kJ, never zero
const defs: VfxDef[] = [];
const add = (d: VfxDef) => { defs.push(d); };
const ORANGE: Rgb = [1, 0.62, 0.18], YELLOW: Rgb = [1, 0.9, 0.5], WHITE: Rgb = [1, 0.97, 0.9];

// ---- collision sparks: a white-yellow shower, a few long orange ones, a short flash of light; the count grows with the cube root of the work done (art: the colours) ----
add({
  version: 1, name: 'take37.sparks', description: 'sparks and a flash of two bodies meeting: the count and the speed follow the energy of the hit', seed: 3701, duration: 2.5, radius: 'pow(energy / 1000, 0.3333) * 3 + 6',
  params: { energy: { unit: 'J', default: 40000, min: 100, max: 5e7, doc: 'energy lost in the hit' } },
  emitters: [
    streaks({ name: 'hot', max: 220, bursts: [{ at: 0, count: `clamp(18 * pow(${E}, 0.5), 12, 200)` }], shape: { shape: 'sphere', radius: 0.15 }, life: [0.35, 1.0], velocity: { speed: [`3 + pow(${E}, 0.5) * 1.2`, `7 + pow(${E}, 0.5) * 3.5`], direction: 'up', spread: 85 }, size: [0.05, 0.1], rgb: YELLOW, glow: true, stretch: 0.05, emissive: 4, temperature: [1900, 2800], modules: [{ module: 'gravity', scale: 0.7 }, { module: 'drag', coefficient: 0.6 }, { module: 'collide', with: 'ground', onHit: 'bounce', bounce: 0.35 }] }),
    streaks({ name: 'long', max: 90, bursts: [{ at: 0.02, count: `clamp(7 * pow(${E}, 0.5), 5, 80)` }], shape: { shape: 'sphere', radius: 0.2 }, life: [0.6, 1.5], velocity: { speed: [`4 + pow(${E}, 0.5) * 1.5`, `9 + pow(${E}, 0.5) * 4.5`], direction: 'up', spread: 70 }, size: [0.06, 0.12], rgb: ORANGE, glow: true, stretch: 0.07, emissive: 3.2, temperature: [1500, 2100], modules: [{ module: 'gravity', scale: 0.9 }, { module: 'drag', coefficient: 0.35 }, { module: 'collide', with: 'ground', onHit: 'bounce', bounce: 0.3 }] }),
    glow({ name: 'flash', max: 4, bursts: [{ at: 0, count: 1 }], life: [0.09, 0.16], size: [`0.7 + pow(${E}, 0.3333) * 0.5`, `1.1 + pow(${E}, 0.3333) * 0.8`], sizeCurve: [[0, 0.5], [0.2, 1], [1, 0.3]], rgb: WHITE, alpha: [[0, 1], [0.4, 0.8], [1, 0]], emissive: 4, flip: 'soft-disc' }),
    puff({ name: 'smoke', max: 40, bursts: [{ at: 0.05, count: `clamp(pow(${E}, 0.5), 3, 24)` }], shape: { shape: 'sphere', radius: 0.2 }, life: [1.2, 2.6], velocity: { speed: [0.5, `1.5 + pow(${E}, 0.3333) * 0.4`], direction: 'up', spread: 60 }, size: [0.15, 0.35], grow: 4, rgb: [0.3, 0.3, 0.32], alpha: 0.4, flip: 'smoke-puff' }),
  ],
  light: { rgb: [1, 0.78, 0.42], intensity: `3000 + ${E} * 90`, range: `8 + pow(${E}, 0.3333) * 3`, over: [[0, 1], [0.1, 0.5], [0.4, 0]], flicker: { amount: 0.5, rate: 30 } },
  dot: { kind: 'light', rgb: [1, 0.8, 0.5], intensity: 0.5, size: 2 }, game: { tags: ['sparks', 'impact'] },
});

// ---- the scrape of metal on the road or on a wall: a fan of sparks that streams back along the motion, about 0.4 s per spawn ----
add({
  version: 1, name: 'take37.scrape', description: 'metal dragged over the road: a fan of orange sparks along the direction of travel (spawned a few times a second while it lasts)', seed: 3702, duration: 0.6, radius: 8,
  params: { speed: { unit: 'm/s', default: 12, min: 0, max: 80, doc: 'sliding speed' } },
  emitters: [
    streaks({ name: 'sparks', max: 120, runFor: 0.35, rate: 'clamp(90 + speed * 12, 60, 500)', shape: { shape: 'box', size: [0.6, 0.02, 0.4] }, life: [0.25, 0.8], velocity: { speed: ['1 + speed * 0.1', '2 + speed * 0.3'], direction: 'up', spread: 55 }, size: [0.015, 0.04], rgb: ORANGE, glow: true, stretch: 0.06, emissive: 4, temperature: [1600, 2500], modules: [{ module: 'gravity', scale: 0.8 }, { module: 'drag', coefficient: 0.4 }, { module: 'collide', with: 'ground', onHit: 'bounce', bounce: 0.3 }] }),
    glow({ name: 'glare', max: 6, runFor: 0.3, rate: 14, life: [0.08, 0.14], size: [0.3, 0.6], rgb: [1, 0.8, 0.45], alpha: [[0, 0.8], [1, 0]], emissive: 3, flip: 'soft-disc' }),
  ],
  light: { rgb: [1, 0.7, 0.35], intensity: 1800, range: 9, over: [[0, 1], [0.6, 0.6], [1, 0]], flicker: { amount: 0.6, rate: 35 } }, game: { tags: ['sparks'] },
});

// ---- breaking glass: a flash of white glints, many small points of cyan, white and gold that fall slowly, a fine white dust; the count follows the pane's area (art: the colours) ----
add({
  version: 1, name: 'take37.glitter', description: 'a burst of glass: glints that catch the light as they fall, and a thin white powder', seed: 3703, duration: 3, radius: 'size * 4 + 6',
  params: { size: { unit: 'm', default: 1.5, min: 0.1, max: 12, doc: 'size of the pane or the glazing that broke' } },
  emitters: [
    glow({ name: 'glints', max: 260, bursts: [{ at: 0, count: 'clamp(70 * size, 30, 260)' }], shape: { shape: 'box', size: ['size', 'size * 0.8', 0.1] }, life: [0.7, 1.8], velocity: { speed: [1.5, 'size * 3 + 3'], direction: 'out', spread: 90 }, size: [0.025, 0.07], sizeCurve: [[0, 1], [0.5, 0.8], [1, 0.1]], gradient: [{ at: 0, rgb: [1, 1, 1], alpha: 1 }, { at: 0.4, rgb: [0.7, 0.9, 1], alpha: 1 }, { at: 1, rgb: [1, 0.85, 0.5], alpha: 1 }], emissive: 3.5, alpha: [[0, 1], [0.7, 0.8], [1, 0]], modules: [{ module: 'gravity', scale: 0.55 }, { module: 'drag', coefficient: 0.5 }, { module: 'collide', with: 'ground', onHit: 'bounce', bounce: 0.25 }] }),
    streaks({ name: 'slivers', max: 120, bursts: [{ at: 0, count: 'clamp(35 * size, 15, 120)' }], shape: { shape: 'box', size: ['size', 'size * 0.8', 0.1] }, life: [0.5, 1.2], velocity: { speed: [2, 'size * 4 + 4'], direction: 'out', spread: 80 }, size: [0.01, 0.03], rgb: [0.85, 0.96, 1], glow: true, stretch: 0.05, emissive: 2.4, modules: [{ module: 'gravity', scale: 0.9 }, { module: 'drag', coefficient: 0.25 }, { module: 'collide', with: 'ground', onHit: 'bounce', bounce: 0.3 }] }),
    puff({ name: 'powder', max: 40, bursts: [{ at: 0, count: 'clamp(8 * size, 4, 40)' }], shape: { shape: 'box', size: ['size', 'size * 0.8', 0.1] }, life: [1.2, 2.4], velocity: { speed: [0.3, 1.4], direction: 'out', spread: 90 }, size: [0.1, 0.25], grow: 3, rgb: [0.88, 0.93, 0.95], alpha: 0.28, flip: 'dust-puff' }),
  ],
  light: { rgb: [0.85, 0.95, 1], intensity: 900, range: 7, over: [[0, 1], [0.15, 0.2], [0.5, 0]] }, game: { tags: ['glass'] },
});

// ---- tyre smoke: a grey-white cloud off the patch, thicker with the slip; and the black mark on the road ----
add({
  version: 1, name: 'take37.tyre-smoke', description: 'one puff of tyre smoke from a sliding wheel (spawned every few frames while it slides) and the black mark it leaves', seed: 3704, duration: 3, radius: 10,
  params: { amount: { default: 0.5, min: 0, max: 1, doc: 'how hard the tyre slides: the share of the burn that shows as smoke' }, speed: { unit: 'm/s', default: 10, min: 0, max: 80, doc: 'speed of the car' } },
  emitters: [puff({ name: 'smoke', max: 60, bursts: [{ at: 0, count: 'clamp(2 + 6 * amount, 2, 8)' }], shape: { shape: 'disc', radius: 0.18 }, life: [1.4, 3], velocity: { speed: [0.3, '0.6 + amount * 1.2'], direction: 'up', spread: 50, inherit: 0.3 }, size: [`0.28 + amount * 0.2`, `0.5 + amount * 0.4`], grow: 4.5, rgb: [0.82, 0.82, 0.84], alpha: 'clamp(0.2 + amount * 0.35, 0.2, 0.6)', flip: 'smoke-puff', modules: [{ module: 'drag', coefficient: 1.2 }, { module: 'buoyancy', accel: 1.2 }, { module: 'wind', influence: 0.9 }] })],
  decals: [{ kind: 'soot', size: 'clamp(0.5 + amount * 0.9, 0.5, 1.4)', at: 'start', life: 90, fade: 30 }], game: { tags: ['smoke'] },
});

// ---- a kick of dirt and road dust at a hit on the ground or a kerb ----
add({
  version: 1, name: 'take37.dirt-kick', description: 'a kick of dust and grit where a heavy thing meets the ground; the size follows the energy', seed: 3705, duration: 4, radius: 'pow(energy / 1000, 0.3333) * 2 + 6',
  params: { energy: { unit: 'J', default: 20000, min: 100, max: 5e7 }, r: { default: 0.52, min: 0, max: 1, doc: 'dust colour (art: asphalt dust)' }, g: { default: 0.47, min: 0, max: 1 }, b: { default: 0.4, min: 0, max: 1 } },
  emitters: [
    puff({ name: 'dust', max: 80, bursts: [{ at: 0, count: `clamp(8 * pow(${E}, 0.5), 8, 70)` }], shape: { shape: 'disc', radius: `0.3 + pow(${E}, 0.3333) * 0.15` }, life: [1.2, 3.2], velocity: { speed: [0.8, `2 + pow(${E}, 0.3333) * 1.4`], direction: 'out', spread: 35 }, size: [0.3, `0.6 + pow(${E}, 0.3333) * 0.35`], grow: 3.5, rgb: [0.52, 0.47, 0.4], alpha: 0.5, flip: 'dust-puff', modules: [{ module: 'drag', coefficient: 1.8 }, { module: 'buoyancy', accel: 0.6 }, { module: 'wind', influence: 1 }] }),
    streaks({ name: 'grit', max: 100, bursts: [{ at: 0, count: `clamp(10 * pow(${E}, 0.5), 8, 90)` }], shape: { shape: 'disc', radius: 0.3 }, life: [0.5, 1.4], velocity: { speed: [2, `5 + pow(${E}, 0.3333) * 2.5`], direction: 'up', spread: 60 }, size: [0.012, 0.04], rgb: [0.55, 0.5, 0.42], stretch: 0.03, modules: [{ module: 'gravity' }, { module: 'drag', coefficient: 0.3 }, { module: 'collide', with: 'ground', onHit: 'bounce', bounce: 0.35 }] }),
  ],
  game: { tags: ['dust'] },
});

// ---- spilt fuel: a dark wet patch that spreads, with a shimmer of vapour; the patch is as wide as the spill makes it (a 1 cm film: D = 2 sqrt(m / (rho pi 0.01))) ----
add({
  version: 1, name: 'take37.spill', description: 'a pool of spilt petrol: a wet dark stain with a thin pale vapour over it', seed: 3706, duration: 40, radius: 'size * 2 + 8',
  params: { size: { unit: 'm', default: 3, min: 0.3, max: 30, doc: 'diameter of the pool' } },
  emitters: [puff({ name: 'vapour', max: 40, rate: 'clamp(size, 1, 10)', runFor: 30, shape: { shape: 'disc', radius: 'size * 0.5' }, life: [1.5, 3], velocity: { speed: [0.1, 0.4], direction: 'up', spread: 30 }, size: ['size * 0.2', 'size * 0.4'], grow: 2, rgb: [0.85, 0.85, 0.7], alpha: 0.12, flip: 'smoke-puff' })],
  decals: [{ kind: 'wet', size: 'size', at: 'start', life: 120, fade: 40 }], game: { tags: ['spill'] },
});

// ---- the flash and the shock ring of a blast, added to the catalogue's fireball: a white flash that blinds, a ring of dust that races out, a heat glow on the ground (art: the colours) ----
add({
  version: 1, name: 'take37.flash', description: 'the first instant of a big blast: a white flash, a ring of dust racing out at the shock speed, and a long warm glow', seed: 3707, duration: 5, radius: 'pow(tnt, 0.3333) * 14',
  params: { tnt: { unit: 'kg', default: 100, min: 0.1, max: 1e5, doc: 'TNT equivalent' } },
  emitters: [
    glow({ name: 'flash', max: 6, bursts: [{ at: 0, count: 1 }], life: [0.12, 0.3], size: ['pow(tnt, 0.3333) * 4', 'pow(tnt, 0.3333) * 6'], sizeCurve: [[0, 0.4], [0.15, 1], [1, 1.3]], rgb: [1, 0.86, 0.6], alpha: [[0, 0.8], [0.3, 0.6], [1, 0]], emissive: 2.2, flip: 'soft-disc' }),
    puff({ name: 'ring', max: 160, bursts: [{ at: 0.03, count: 'clamp(30 + pow(tnt, 0.3333) * 12, 40, 150)' }], shape: { shape: 'disc', radius: 'pow(tnt, 0.3333) * 0.4', ring: true }, life: [1.5, 3.5], velocity: { speed: ['pow(tnt, 0.3333) * 8', 'pow(tnt, 0.3333) * 14'], direction: 'out', spread: 6 }, size: ['pow(tnt, 0.3333) * 0.5', 'pow(tnt, 0.3333) * 1.1'], grow: 3, rgb: [0.62, 0.55, 0.47], alpha: 0.5, flip: 'dust-puff', modules: [{ module: 'drag', coefficient: 1.4 }] }),
    glow({ name: 'glow', max: 30, bursts: [{ at: 0.1, count: 'clamp(pow(tnt, 0.3333) * 1.2, 3, 12)' }], life: [1.2, 3.8], size: ['pow(tnt, 0.3333) * 3', 'pow(tnt, 0.3333) * 6'], sizeCurve: [[0, 0.6], [0.3, 1], [1, 1.4]], shape: { shape: 'sphere', radius: 'pow(tnt, 0.3333) * 1.5' }, velocity: { speed: [0, 1.5], direction: 'up', spread: 80 }, rgb: [1, 0.45, 0.12], alpha: [[0, 0], [0.15, 0.4], [1, 0]], emissive: 1.4, flip: 'soft-disc' }),
    streaks({ name: 'embers', max: 200, bursts: [{ at: 0.05, count: 'clamp(40 * pow(tnt, 0.3333), 40, 200)' }], shape: { shape: 'sphere', radius: 'pow(tnt, 0.3333) * 0.5' }, life: [1.5, 4], velocity: { speed: ['pow(tnt, 0.3333) * 2', 'pow(tnt, 0.3333) * 7'], direction: 'up', spread: 75 }, size: [0.03, 0.08], rgb: ORANGE, glow: true, stretch: 0.06, emissive: 3, temperature: [1300, 2200], modules: [{ module: 'gravity', scale: 0.5 }, { module: 'drag', coefficient: 0.25 }, { module: 'wind', influence: 0.3 }, { module: 'collide', with: 'ground', onHit: 'bounce', bounce: 0.25 }] }),
  ],
  light: { rgb: [1, 0.72, 0.38], intensity: 'pow(tnt, 0.6667) * 6e4', range: 'pow(tnt, 0.3333) * 45', over: [[0, 1], [0.05, 0.9], [0.25, 0.45], [0.7, 0.15], [1, 0]], flicker: { amount: 0.35, rate: 12 }, farGlow: 'pow(tnt, 0.3333) * 90' },
  dot: { kind: 'light', rgb: [1, 0.7, 0.35], intensity: 1, size: 4 }, game: { tags: ['blast'] },
});

// ---- the fireball of the tanker: the catalogue's fuel-air ball with fewer, dimmer sprites. Measured (frames at 0.4, 1.5, 4 and 10 s, effects skipped one by one): the whole sky and the far street went white
//      for four seconds because of this ball alone: 150 additive sprites of 50 to 80 m each, every one at the radiance cap, stacked in front of the camera and pushed through the ACES shoulder to pure white. Not the
//      sky, the light cap, the tone mapping, the bloom or the exposure. A ball of 28 sprites at 0.3 of the radiance keeps the colour (orange to yellow) and the size, which are the catalogue's. ----
{
  const base = FULL_CATALOG.find((d) => d.name === 'blast.fuel-air') as unknown as (VfxDef & { emitters: { name?: string; rate?: unknown; render?: { emissive?: unknown } }[] }) | undefined;
  if (base) {
    const d = JSON.parse(JSON.stringify(base)) as typeof base;
    d.name = 'take37.fireball'; d.seed = 3709;
    for (const e of d.emitters) if (e.name === 'ball') {
      if (typeof e.rate === 'string') e.rate = e.rate.replace(/^120\s*\//, '28 /');
      if (e.render && typeof e.render.emissive === 'string') e.render.emissive = e.render.emissive.replace(/^1\.4\s*\*/, '0.4 *');
    }
    add(d);
  }
}

// ---- the look of the station fires (owner's pass): the catalogue's fires re-coloured and re-shaped by data. Art, all of it, on top of the catalogue's physics (flame height, rise speed, temperature follow `heat` and `D` as ever):
//      orange flames that are dim at the root (the smoke in front of the glowing part hides it) and bright only at the tips, tongues of many heights (a wide range of speed, size and life, and a few tall thin ones), a thick tall
//      smoke column (more and bigger puffs, more opaque, longer lived), a dim orange light, and the engine's soot decals laid in growing layers under the fire. ----
type Loose = Record<string, unknown>;
const ORANGE_RAMP = [{ at: 0, rgb: [0.9, 0.3, 0.05], alpha: 1 }, { at: 0.45, rgb: [0.95, 0.3, 0.04], alpha: 1 }, { at: 1, rgb: [0.45, 0.06, 0.02], alpha: 1 }];
const scaleLead = (v: unknown, k: number): unknown => (typeof v === 'string' ? v.replace(/^[\d.]+\s*\*/, `${k} *`) : v);
const times = (v: unknown, k: number): unknown => (Array.isArray(v) ? v.map((x) => times(x, k)) : typeof v === 'number' ? v * k : `(${String(v)}) * ${k}`);
function station(baseName: string, name: string, seed: number, o: { glow: number; smoke: number; soot: boolean; tongues: boolean; sootSize: string }): void {
  const base = FULL_CATALOG.find((d) => d.name === baseName) as unknown as (VfxDef & { emitters: Loose[] }) | undefined;
  if (!base) return;
  const d = JSON.parse(JSON.stringify(base)) as VfxDef & { emitters: Loose[]; light?: Loose; decals?: Loose[] };
  d.name = name; d.seed = seed;
  const extra: Loose[] = [];
  for (const e of d.emitters) {
    const r = e.render as Loose | undefined;
    if (r?.flipbook === 'flame' && r.blend === 'add') {
      // orange, dim in the lower part: the radiance factor is cut and the ramp starts at deep orange, not at pale yellow
      r.emissive = scaleLead(r.emissive, o.glow); e.colorOverLife = ORANGE_RAMP;
      if (e.name === 'flame' && o.tongues) {
        // tongues of different heights: a wide spread of rise speed, size and life, plus a few tall narrow ones
        const b = base.emitters.find((x) => x.name === 'flame')!, bv = b.velocity as { speed: unknown[] }, bs = b.size as unknown[], bl = b.lifetime as unknown[];
        e.velocity = { ...bv, spread: 16, speed: [times(bv.speed[0], 0.45), times(bv.speed[1], 1.2)] };
        e.size = [times(bs[0], 0.5), times(bs[1], 0.95)]; e.lifetime = [times(bl[0], 0.7), times(bl[1], 1.25)];
        e.rate = `(${String(b.rate)}) * 1.1`; e.max = 400; e.alphaOverLife = [[0, 0], [0.12, 0.45], [0.8, 0.35], [1, 0]];
        const tall = JSON.parse(JSON.stringify(e)) as Loose; tall.name = 'tongues'; tall.max = 90; tall.rate = 'clamp(5 * (D + 1), 2, 40)';
        tall.velocity = { ...bv, spread: 6, speed: [times(bv.speed[1], 1.15), times(bv.speed[1], 1.7)] };
        tall.size = [times(bs[0], 0.4), times(bs[1], 0.5)]; tall.lifetime = [times(bl[0], 1.2), times(bl[1], 1.7)];
        (tall.render as Loose).emissive = scaleLead((tall.render as Loose).emissive, 0.8);
        extra.push(tall);
      }
    } else if (e.name === 'smoke') {
      // thick, high, fat and opaque: bigger puffs that grow to six times, a denser stream, longer life, a steeper rise
      const b = base.emitters.find((x) => x.name === 'smoke')!, bv = b.velocity as { speed: unknown[] };
      e.size = times(b.size, 1.7); e.sizeOverLife = [[0, 0.5], [0.4, 2.4], [1, 6.5]]; e.rate = `(${String(b.rate)}) * ${o.smoke}`; e.max = 1100;
      e.lifetime = times(b.lifetime, 1.5); e.velocity = { ...bv, speed: [times(bv.speed[0], 1.2), times(bv.speed[1], 1.4)] };
      e.alphaOverLife = [[0, 0], [0.08, 0.35], [0.2, 0.92], [0.7, 0.8], [1, 0]]; e.color = [0.035, 0.034, 0.033];
    }
  }
  d.emitters.push(...extra);
  if (d.light) { d.light.rgb = [1, 0.4, 0.1]; d.light.intensity = `(${String(d.light.intensity)}) * 0.3`; }
  if (o.soot) d.decals = [0, 4, 10, 20, 35].map((at, i) => ({ kind: 'soot', size: `(${o.sootSize}) * ${(1 + i * 0.3).toFixed(2)}`, at, life: 900, fade: 120 }));
  add(d as VfxDef);
}
station('fire.pool-petrol', 'take37.pump-fire', 3710, { glow: 0.4, smoke: 2.2, soot: true, tongues: true, sootSize: 'D * 1.1 + 1' });
station('fire.building', 'take37.canopy-fire', 3711, { glow: 0.4, smoke: 1.8, soot: true, tongues: true, sootSize: 'D * 0.7 + 3' });
station('fire.jet', 'take37.jet-fire', 3712, { glow: 0.75, smoke: 1, soot: false, tongues: false, sootSize: '1' });

// ---- a flying burning piece: a trail of sparks and a thin stream of smoke, for a part thrown off a car or a fragment of a tank (follows the piece through the host's attachment) ----
add({
  version: 1, name: 'take37.piece-trail', description: 'sparks and a thin smoke trail behind a flying part or fragment', seed: 3708, duration: 8, radius: 14,
  params: { glowing: { default: 1, min: 0, max: 1, doc: '1 for a hot, burning piece' } },
  emitters: [
    streaks({ name: 'sparks', max: 70, runFor: 3, rate: 'glowing * 45', shape: { shape: 'point' }, life: [0.3, 0.9], velocity: { speed: [0.5, 3], direction: 'up', spread: 90 }, size: [0.015, 0.035], rgb: ORANGE, glow: true, stretch: 0.05, emissive: 3.5, temperature: [1500, 2300], modules: [{ module: 'gravity', scale: 0.8 }, { module: 'drag', coefficient: 0.5 }] }),
    puff({ name: 'smoke', max: 80, rate: 'glowing * 14 + 4', runFor: 7, shape: { shape: 'point' }, life: [1.2, 3], velocity: { speed: [0.2, 0.8], direction: 'up', spread: 40 }, size: [0.1, 0.22], grow: 5, rgb: [0.12, 0.12, 0.13], alpha: 0.5, flip: 'smoke-puff', modules: [{ module: 'drag', coefficient: 0.8 }, { module: 'buoyancy', accel: 2 }, { module: 'wind', influence: 0.9 }] }),
  ],
  game: { tags: ['debris'] },
});

export const TAKE37_FX: readonly VfxDef[] = defs;
