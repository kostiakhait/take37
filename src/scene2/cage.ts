// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
/**
 * The prisoners' cage of scene 2: a steel-bar cage on a timber platform that stands on four casters, so that a stuntman's shoulder can push it along the mole's deck (and a hard
 * push can send it rolling away). Made for the game, procedural (no library model); the parameters below are what the physics binds to (a box body of `mass` with the casters'
 * rolling resistance), kept here as data so that the picture and the body agree.
 */
export const CAGE = {
  /** the cage on its platform: width (across the push), depth (along it), height of the bars above the platform, m */
  width: 2.0, depth: 2.0, barHeight: 2.0,
  /** the platform's top above the deck: the casters' diameter plus the platform's thickness, m */
  platformTop: 0.42,
  /** the casters: radius, m; rolling resistance coefficient of steel casters on planks (force = coefficient * weight) */
  casterRadius: 0.1, rollingResistance: 0.04,
  /** the empty cage with its platform and casters, kg (a shoulder shove of about 700 N then gives about 1.8 m/s^2; the prisoner is added by the mechanics) */
  mass: 350,
  /** bars: diameter and spacing, m */
  barDiameter: 0.024, barSpacing: 0.16,
};

interface Mats { steel: BABYLON.Material; wood: BABYLON.Material; rubber: BABYLON.Material; rust: BABYLON.Material }
export function cageMaterials(scene: BABYLON.Scene): Mats {
  const m = (name: string, c: [number, number, number], metal: number, rough: number) => { const x = new BABYLON.PBRMaterial(name, scene); x.albedoColor = new BABYLON.Color3(...c); x.metallic = metal; x.roughness = rough; return x; };
  return { steel: m('cage-steel', [0.2, 0.21, 0.22], 0.85, 0.5), wood: m('cage-wood', [0.36, 0.27, 0.17], 0, 0.85), rubber: m('cage-rubber', [0.05, 0.05, 0.05], 0, 0.9), rust: m('cage-rust', [0.34, 0.2, 0.12], 0.6, 0.75) };
}

/** builds a cage standing with its platform's underside (the casters' ground) at y = 0 of the returned node, centred on x and z; the door is on the +x side (the side the steamer is on) */
export function buildCage(scene: BABYLON.Scene, name: string, mats: Mats): BABYLON.TransformNode {
  const root = new BABYLON.TransformNode(name, scene), C = CAGE;
  const parts: Record<keyof Mats, BABYLON.Mesh[]> = { steel: [], wood: [], rubber: [], rust: [] };
  const box = (k: keyof Mats, x: number, y: number, z: number, sx: number, sy: number, sz: number) => { const b = BABYLON.MeshBuilder.CreateBox('b', { width: sx, height: sy, depth: sz }, scene); b.position.set(x, y, z); parts[k].push(b); };
  const cyl = (k: keyof Mats, x: number, y: number, z: number, d: number, h: number, axis: 'y' | 'x' | 'z' = 'y') => { const c = BABYLON.MeshBuilder.CreateCylinder('c', { diameter: d, height: h, tessellation: 10 }, scene); c.position.set(x, y, z); if (axis === 'x') c.rotation.z = Math.PI / 2; else if (axis === 'z') c.rotation.x = Math.PI / 2; parts[k].push(c); };
  const hw = C.width / 2, hd = C.depth / 2, y0 = C.platformTop, H = C.barHeight, bd = C.barDiameter, t = 0.06;
  // the platform: plank deck on two steel runners, a toe rail
  box('wood', 0, y0 - 0.06, 0, C.width + 0.1, 0.1, C.depth + 0.1);
  for (const x of [-hw * 0.6, hw * 0.6]) box('steel', x, y0 - 0.16, 0, 0.08, 0.1, C.depth + 0.06);
  for (const z of [-hd - 0.03, hd + 0.03]) box('steel', 0, y0 + 0.01, z, C.width + 0.12, 0.06, 0.04);
  // four casters under the corners: fork, wheel (rubber tyre on an axle), swivel plate
  for (const [x, z] of [[-hw + 0.12, -hd + 0.12], [hw - 0.12, -hd + 0.12], [-hw + 0.12, hd - 0.12], [hw - 0.12, hd - 0.12]]) {
    box('steel', x, y0 - 0.14, z, 0.12, 0.03, 0.12);
    box('steel', x - 0.045, y0 - 0.22, z, 0.015, 0.14, 0.07); box('steel', x + 0.045, y0 - 0.22, z, 0.015, 0.14, 0.07);
    cyl('rubber', x, C.casterRadius, z, C.casterRadius * 2, 0.06, 'x');
  }
  // the cage: corner posts, the top and bottom frames, vertical bars on all four sides (the +x side has the door), a roof of bars
  const top = y0 + H;
  for (const [x, z] of [[-hw, -hd], [hw, -hd], [-hw, hd], [hw, hd]]) box('steel', x, y0 + H / 2, z, t, H, t);
  for (const y of [y0 + 0.08, y0 + H * 0.5, top]) { box('steel', 0, y, -hd, C.width, 0.04, 0.04); box('steel', 0, y, hd, C.width, 0.04, 0.04); box('steel', -hw, y, 0, 0.04, 0.04, C.depth); box('steel', hw, y, 0, 0.04, 0.04, C.depth); }
  const nx = Math.round(C.width / C.barSpacing), nz = Math.round(C.depth / C.barSpacing);
  for (let i = 1; i < nx; i++) { const x = -hw + i * C.width / nx; cyl('steel', x, y0 + H / 2, -hd, bd, H); cyl('steel', x, y0 + H / 2, hd, bd, H); }
  for (let i = 1; i < nz; i++) { const z = -hd + i * C.depth / nz; cyl('steel', -hw, y0 + H / 2, z, bd, H); cyl('steel', hw, y0 + H / 2, z, bd, H); }
  for (let i = 1; i < nx; i += 2) cyl('steel', -hw + i * C.width / nx, top + 0.02, 0, bd, C.depth, 'z');
  box('steel', 0, top + 0.05, 0, C.width * 0.9, 0.02, 0.04);
  // the door on the +x side: a heavier frame over the bars, a hasp and a padlock
  box('rust', hw + 0.02, y0 + H * 0.45, 0, 0.04, H * 0.82, 0.78); box('rust', hw + 0.04, y0 + H * 0.45, 0.36, 0.05, 0.14, 0.12); box('steel', hw + 0.07, y0 + H * 0.45 - 0.1, 0.36, 0.06, 0.1, 0.08);
  for (const y of [y0 + 0.4, y0 + H * 0.82]) box('steel', hw + 0.04, y, -0.4, 0.06, 0.08, 0.06);
  // a push bar on the -x side at shoulder height (the side the stuntman pushes from)
  box('rust', -hw - 0.1, y0 + 1.25, 0, 0.06, 0.06, 1.2); for (const z of [-0.5, 0.5]) box('rust', -hw - 0.05, y0 + 1.25, z, 0.14, 0.04, 0.04);
  for (const k of Object.keys(parts) as Array<keyof Mats>) { if (!parts[k].length) continue; const m = BABYLON.Mesh.MergeMeshes(parts[k], true, true)!; m.name = `${name}_${k}`; m.material = mats[k]; m.parent = root; m.isPickable = false; }
  return root;
}
