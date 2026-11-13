// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// Body colours of the civilian cars: every car of a model in a take gets its own colour, chosen from the seed of the take. Only the body paint (the M_paint material of the
// art/cars glbs: body, doors, lids, painted bumpers) is coloured; glass, chrome, rubber, the cabin keep theirs.
// The near models get a paint material per colour (shared by every car of that colour and model, not a copy per car); the far reduced copies are instances of one merged
// mesh per model: their paint part has a white paint and takes the colour per instance (an instanced colour attribute, multiplied with the dirt vertex colours as the
// near model's albedo is), so a car looks the same on both and when the perspective module switches between them.
import { Rng } from './rng';
import type { KindId } from './config';

/** the palette: the union of the six models' own paint sets (art/cars/<model>/<model>_geom.py COLORS, sRGB 0..255) */
export const PAINT: readonly { name: string; srgb: readonly [number, number, number] }[] = [
  { name: 'black', srgb: [22, 22, 24] }, { name: 'white', srgb: [232, 232, 226] }, { name: 'silver', srgb: [176, 178, 180] },
  { name: 'red', srgb: [158, 30, 28] }, { name: 'maroon', srgb: [104, 26, 36] }, { name: 'burgundy', srgb: [100, 28, 38] },
  { name: 'midnight_blue', srgb: [26, 40, 84] }, { name: 'dark_blue', srgb: [30, 44, 90] }, { name: 'two_tone_blue', srgb: [34, 52, 98] },
  { name: 'light_blue', srgb: [110, 150, 184] }, { name: 'forest_green', srgb: [36, 70, 52] }, { name: 'dark_green', srgb: [34, 64, 50] },
  { name: 'beige', srgb: [214, 196, 156] }, { name: 'desert_tan', srgb: [190, 168, 126] }, { name: 'gold', srgb: [170, 138, 84] },
  { name: 'yellow', srgb: [214, 178, 52] }, { name: 'brown', srgb: [110, 76, 52] }, { name: 'brown_metallic', srgb: [92, 62, 44] },
];
/** the models painted per car (the police car, the Corvette and the tanker keep their own) */
export const PAINTED: readonly KindId[] = ['sedan', 'pickup', 'minivan', 'hatchback', 'coupe', 'wagon'];

const lin = (c: number) => { const x = c / 255; return x <= 0.04045 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4; };
/** the colour of a palette entry, linear (what the PBR albedo and the instanced colour take) */
export function paintLinear(i: number): [number, number, number] { const c = PAINT[i]!.srgb; return [lin(c[0]), lin(c[1]), lin(c[2])]; }

/** the palette index of each painted car of the take: per model, the palette shuffled by the take's seed and dealt in the order of the cars, so no two cars of a model share a
 *  colour while there are no more of them than colours (18); past that the deal starts over */
export function assignPaint(cars: readonly { id: string; kind: KindId }[], seed: number): Map<string, number> {
  const out = new Map<string, number>(), dealt = new Map<KindId, number[]>();
  for (const c of cars) {
    if (!PAINTED.includes(c.kind)) continue;
    let deck = dealt.get(c.kind);
    if (!deck || deck.length === 0) {
      const rng = new Rng((seed * 2654435761 + PAINTED.indexOf(c.kind) * 40503 + 7) >>> 0);
      deck = PAINT.map((_, i) => i);
      for (let i = deck.length - 1; i > 0; i--) { const j = rng.int(i + 1); [deck[i], deck[j]] = [deck[j]!, deck[i]!]; }
      dealt.set(c.kind, deck);
    }
    out.set(c.id, deck.shift()!);
  }
  return out;
}

const isPaint = (m: BABYLON.Nullable<BABYLON.Material>) => !!m && /^(M_paint|paint_)/.test(m.name);
const cache = new Map<string, BABYLON.Material>();
/** the paint material of a model in palette colour i (made once per model and colour) */
function paintMaterial(src: BABYLON.Material, i: number): BABYLON.Material {
  const key = src.uniqueId + ':' + i;
  let m = cache.get(key);
  if (!m || m.getScene().isDisposed) {
    m = src.clone(`${src.name}:${PAINT[i]!.name}`) ?? src;
    const [r, g, b] = paintLinear(i);
    if (m instanceof BABYLON.PBRMaterial) m.albedoColor = new BABYLON.Color3(r, g, b);
    cache.set(key, m);
  }
  return m;
}
/** colour the paint of a near model (full, lod or wrecked) */
export function paintLook(root: BABYLON.Node, i: number | undefined) {
  if (i === undefined) return;
  for (const mesh of root.getChildMeshes(false)) if (isPaint(mesh.material)) mesh.material = paintMaterial(mesh.material!, i);
}
/** the white paint of a model's reduced mesh: the colour comes per instance */
export function whitePaint(src: BABYLON.Material): BABYLON.Material {
  const m = src.clone(src.name + ':per-car') ?? src;
  if (m instanceof BABYLON.PBRMaterial) m.albedoColor = new BABYLON.Color3(1, 1, 1);
  return m;
}
export const paintOf = isPaint;
/** the reduced paint mesh takes a colour per instance */
export function preparePaintInstances(mesh: BABYLON.Mesh) { mesh.registerInstancedBuffer('color', 4); mesh.instancedBuffers.color = new BABYLON.Color4(1, 1, 1, 1); }
export function paintInstance(inst: BABYLON.InstancedMesh, i: number | undefined) {
  if (!inst.sourceMesh.instancedBuffers || !('color' in inst.sourceMesh.instancedBuffers)) return;
  const [r, g, b] = i === undefined ? [1, 1, 1] : paintLinear(i);
  inst.instancedBuffers.color = new BABYLON.Color4(r, g, b, 1);
}
