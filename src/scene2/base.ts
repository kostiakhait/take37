// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
/**
 * The villain's post on the shore of scene 2 (made for the game, procedural, in khaki and grey, no signs or emblems): a barrack, a watch tower with a searchlight and a
 * fence with a gate that opens on the road to the mole. It stands on the levelled pad of `shore.ts` (BASE). Also the dirt road from the gate to the mole's landward end.
 */
import { BASE, MOLE, bed } from './shore';

const KHAKI: [number, number, number] = [0.5, 0.45, 0.31], GREY: [number, number, number] = [0.42, 0.44, 0.45], DARK: [number, number, number] = [0.14, 0.14, 0.15], ROOF: [number, number, number] = [0.3, 0.34, 0.32], WOOD: [number, number, number] = [0.33, 0.26, 0.18];
/** the post: the fence's half extents about the pad's centre (x along the beach, z in and out), the gate's width and which side it is on (+x: the side of the mole) */
export const POST = { halfX: 22, halfZ: 17, gate: 5.5, barrack: { x: BASE.x - 8, z: BASE.z + 6, w: 16, d: 6.4, h: 3.2 }, tower: { x: BASE.x + 14, z: BASE.z + 10 } };

export interface Post { root: BABYLON.TransformNode; gate: { x: number; z: number }; searchlight: BABYLON.TransformNode }

export function buildPost(scene: BABYLON.Scene): Post {
  const root = new BABYLON.TransformNode('post', scene);
  const mat = (name: string, c: [number, number, number], metal = 0, rough = 0.8) => { const m = new BABYLON.PBRMaterial(name, scene); m.albedoColor = new BABYLON.Color3(...c); m.metallic = metal; m.roughness = rough; return m; };
  const M = { khaki: mat('post-khaki', KHAKI), grey: mat('post-grey', GREY, 0.2, 0.7), dark: mat('post-dark', DARK, 0.3, 0.7), roof: mat('post-roof', ROOF, 0.5, 0.55), wood: mat('post-wood', WOOD), lens: mat('post-lens', [1, 0.95, 0.8], 0, 0.2) };
  (M.lens as BABYLON.PBRMaterial).emissiveColor = new BABYLON.Color3(0.9, 0.85, 0.6);
  const parts: Record<keyof typeof M, BABYLON.Mesh[]> = { khaki: [], grey: [], dark: [], roof: [], wood: [], lens: [] };
  const box = (k: keyof typeof M, x: number, y: number, z: number, sx: number, sy: number, sz: number, ry = 0, rz = 0) => { const b = BABYLON.MeshBuilder.CreateBox('b', { width: sx, height: sy, depth: sz }, scene); b.position.set(x, y, z); b.rotation.y = ry; b.rotation.z = rz; parts[k].push(b); return b; };
  const cyl = (k: keyof typeof M, x: number, y: number, z: number, d: number, h: number, rx = 0, rz = 0) => { const c = BABYLON.MeshBuilder.CreateCylinder('c', { diameter: d, height: h, tessellation: 12 }, scene); c.position.set(x, y, z); c.rotation.x = rx; c.rotation.z = rz; parts[k].push(c); return c; };
  const g = BASE.h;                      // the pad's height

  // ---- the barrack: a long hut on a low plinth, gabled corrugated roof, a door, windows, a stove pipe ----
  const B = POST.barrack, x0 = B.x, z0 = B.z;
  box('grey', x0, g + 0.15, z0, B.w + 0.4, 0.3, B.d + 0.4);
  box('khaki', x0, g + 0.3 + B.h / 2, z0, B.w, B.h, B.d);
  const pitch = 0.42, rl = (B.d / 2 + 0.5) / Math.cos(pitch), ry = g + 0.3 + B.h + (B.d / 4) * Math.tan(pitch) + 0.1;
  box('roof', x0, ry, z0 - B.d / 4 - 0.12, B.w + 0.9, 0.08, rl, 0, 0).rotation.x = -pitch;
  box('roof', x0, ry, z0 + B.d / 4 + 0.12, B.w + 0.9, 0.08, rl, 0, 0).rotation.x = pitch;
  box('roof', x0, ry + (B.d / 4) * Math.tan(pitch) + 0.06, z0, B.w + 0.9, 0.12, 0.3);
  for (const gx of [-B.w / 2, B.w / 2]) for (const dz of [-1, 1]) box('khaki', x0 + gx, g + 0.3 + B.h + 0.5, z0 + dz * 0.01, 0.12, 0.9, B.d * 0.8);        // the gable ends' fill under the roof
  // the door on the long side facing the gate (+z side is seaward; the door is on -z, towards the pad's middle) and the windows
  const dz = z0 - B.d / 2 - 0.03;
  box('wood', x0 + 4, g + 0.3 + 1.05, dz, 1.1, 2.1, 0.08); box('grey', x0 + 4, g + 0.3 + 0.08, dz - 0.4, 1.9, 0.16, 0.9); box('grey', x0 + 4, g + 0.3 + 0.2, dz - 0.8, 1.9, 0.2, 0.7);
  for (const wx of [-6, -2, 1.2, 6.5]) { box('dark', x0 + wx, g + 0.3 + 1.8, dz, 1.1, 0.9, 0.06); box('wood', x0 + wx, g + 0.3 + 1.8, dz - 0.03, 1.22, 0.08, 0.04); box('wood', x0 + wx, g + 0.3 + 1.36, dz - 0.03, 1.22, 0.06, 0.06); }
  for (const wx of [-6, -2, 2, 6]) box('dark', x0 + wx, g + 0.3 + 1.8, z0 + B.d / 2 + 0.03, 1.1, 0.9, 0.06);
  cyl('dark', x0 - 5.5, g + 0.3 + B.h + 1.5, z0 + 0.8, 0.28, 2.0);

  // ---- the watch tower: four legs braced, a platform, a hut with a roof and the searchlight ----
  const T = POST.tower, th = 7.0, tw = 1.7;
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) {
    const lean = 0.05; box('wood', T.x + sx * tw / 2 * 1.0, g + th / 2, T.z + sz * tw / 2, 0.22, th, 0.22).rotation.set(-sz * lean * 0, 0, 0);
  }
  for (const h of [1.4, 3.2, 5.0]) { for (const sz of [-1, 1]) box('wood', T.x, g + h, T.z + sz * tw / 2, tw, 0.1, 0.1); for (const sx of [-1, 1]) box('wood', T.x + sx * tw / 2, g + h, T.z, 0.1, 0.1, tw); }
  for (const [a, b] of [[0, 1.4], [1.4, 3.2], [3.2, 5.0], [5.0, 7.0]]) { const hh = b - a, len = Math.hypot(tw, hh), ang = Math.atan2(tw, hh); for (const sz of [-1, 1]) box('wood', T.x, g + (a + b) / 2, T.z + sz * tw / 2, 0.07, len, 0.07).rotation.z = ang; }
  box('wood', T.x, g + th + 0.06, T.z, tw + 1.4, 0.14, tw + 1.4);
  box('khaki', T.x, g + th + 0.14 + 1.0, T.z, tw + 0.9, 0.9, tw + 0.9);
  for (const sx of [-1, 1]) box('wood', T.x + sx * (tw / 2 + 0.52), g + th + 0.14 + 0.45, T.z, 0.06, 0.9, tw + 1.2);
  box('roof', T.x, g + th + 0.14 + 2.0, T.z, tw + 1.9, 0.1, tw + 1.9);
  // the cabin's window openings all round, dark
  for (const [wx, wz, sx, sz] of [[0, 1, 1.4, 0.05], [0, -1, 1.4, 0.05], [1, 0, 0.05, 1.4], [-1, 0, 0.05, 1.4]]) box('dark', T.x + wx * (tw / 2 + 0.47), g + th + 0.14 + 1.2, T.z + wz * (tw / 2 + 0.47), sx, 0.55, sz);
  // the searchlight on a post on the platform's seaward edge: a drum with a glass front looking out to sea (+z)
  const sl = new BABYLON.TransformNode('searchlight', scene); sl.parent = root; sl.position.set(T.x, g + th + 0.14 + 0.5, T.z + tw / 2 + 0.95);
  const drum = BABYLON.MeshBuilder.CreateCylinder('drum', { diameter: 0.7, height: 0.6, tessellation: 16 }, scene); drum.rotation.x = Math.PI / 2; drum.parent = sl; drum.material = M.dark;
  const lens = BABYLON.MeshBuilder.CreateCylinder('lens', { diameter: 0.6, height: 0.03, tessellation: 16 }, scene); lens.rotation.x = Math.PI / 2; lens.position.z = 0.31; lens.parent = sl; lens.material = M.lens;
  const fork = BABYLON.MeshBuilder.CreateBox('fork', { width: 0.06, height: 0.5, depth: 0.06 }, scene); fork.position.y = -0.45; fork.parent = sl; fork.material = M.dark;
  sl.rotation.x = 0.12;

  // ---- the fence: posts every 3 m, three wires and a chain-link panel between, a gate on the +x side ----
  const fh = 2.3, chain = new BABYLON.DynamicTexture('chain', { width: 128, height: 128 }, scene, true);
  { const c = chain.getContext() as CanvasRenderingContext2D; c.clearRect(0, 0, 128, 128); c.strokeStyle = 'rgba(120,125,128,0.95)'; c.lineWidth = 3; for (let i = -128; i < 256; i += 32) { c.beginPath(); c.moveTo(i, 0); c.lineTo(i + 128, 128); c.stroke(); c.beginPath(); c.moveTo(i + 128, 0); c.lineTo(i, 128); c.stroke(); } chain.update(); chain.hasAlpha = true; chain.wrapU = chain.wrapV = BABYLON.Texture.WRAP_ADDRESSMODE; }
  const wire = new BABYLON.PBRMaterial('post-chain', scene); wire.albedoTexture = chain; wire.useAlphaFromAlbedoTexture = true; wire.transparencyMode = BABYLON.Material.MATERIAL_ALPHATEST; wire.alphaCutOff = 0.4; wire.backFaceCulling = false; wire.metallic = 0.5; wire.roughness = 0.6;
  const panels: BABYLON.Mesh[] = [];
  const panel = (ax: number, az: number, bx: number, bz: number) => {
    const len = Math.hypot(bx - ax, bz - az), p = BABYLON.MeshBuilder.CreatePlane('panel', { width: len, height: fh - 0.2, sideOrientation: BABYLON.Mesh.DOUBLESIDE }, scene);
    p.position.set((ax + bx) / 2, g + fh / 2 + 0.05, (az + bz) / 2); p.rotation.y = -Math.atan2(bz - az, bx - ax);
    // the texture runs by the panel's own size: tiles of about 0.35 m
    const uv = p.getVerticesData(BABYLON.VertexBuffer.UVKind)!.slice(); for (let i = 0; i < uv.length; i += 2) { uv[i] *= len / 0.35; uv[i + 1] *= (fh - 0.2) / 0.35; } p.setVerticesData(BABYLON.VertexBuffer.UVKind, uv);
    panels.push(p);
    for (const hh of [0.2, fh * 0.5, fh - 0.02]) { const b = box('grey', (ax + bx) / 2, g + hh, (az + bz) / 2, len, 0.04, 0.04); b.rotation.y = -Math.atan2(bz - az, bx - ax); }
  };
  const cx = BASE.x, cz = BASE.z, hx = POST.halfX, hz = POST.halfZ, gw = POST.gate / 2;
  const edges: Array<[number, number, number, number]> = [[cx - hx, cz - hz, cx + hx, cz - hz], [cx - hx, cz + hz, cx + hx, cz + hz], [cx - hx, cz - hz, cx - hx, cz + hz], [cx + hx, cz - hz, cx + hx, cz - gw], [cx + hx, cz + gw, cx + hx, cz + hz]];
  for (const [ax, az, bx, bz] of edges) {
    const len = Math.hypot(bx - ax, bz - az), n = Math.max(1, Math.round(len / 3));
    for (let i = 0; i < n; i++) { const t0 = i / n, t1 = (i + 1) / n; panel(ax + (bx - ax) * t0, az + (bz - az) * t0, ax + (bx - ax) * t1, az + (bz - az) * t1); }
    for (let i = 0; i <= n; i++) box('wood', ax + (bx - ax) * i / n, g + fh / 2, az + (bz - az) * i / n, 0.14, fh + 0.2, 0.14);
  }
  // the gate: two tall posts, a leaf standing open on the inside and a swung-open second leaf (a frame of bars with the same wire)
  for (const sz of [-1, 1]) box('wood', cx + hx, g + 1.4, cz + sz * gw, 0.22, 2.8, 0.22);
  box('wood', cx + hx, g + 2.8, cz, 0.18, 0.14, POST.gate + 0.2);
  for (const [sz, ang] of [[-1, 1.4], [1, 1.4]]) {
    const leaf = new BABYLON.TransformNode('leaf', scene); leaf.parent = root; leaf.position.set(cx + hx, g, cz + sz * gw); leaf.rotation.y = Math.PI / 2 + sz * ang;
    const lw = gw - 0.1;
    // the leaf's own axis is local x, pointing from the post across the opening
    const bar = (lx: number, y: number, sx: number, sy: number) => { const b = BABYLON.MeshBuilder.CreateBox('lf', { width: sx, height: sy, depth: 0.06 }, scene); b.position.set(lx, y, 0); b.parent = leaf; b.material = M.grey; };
    for (const y of [0.25, fh - 0.15, fh / 2]) bar(sz * lw / 2, y, lw, 0.06); for (const lx of [0, 0.5, 1].map(f => sz * lw * f)) bar(lx, fh / 2 + 0.05, 0.05, fh - 0.2);
    const pl = BABYLON.MeshBuilder.CreatePlane('leafwire', { width: lw, height: fh - 0.4, sideOrientation: BABYLON.Mesh.DOUBLESIDE }, scene); pl.parent = leaf; pl.position.set(sz * lw / 2, fh / 2 + 0.05, 0); pl.material = wire;
    const uv = pl.getVerticesData(BABYLON.VertexBuffer.UVKind)!.slice(); for (let i = 0; i < uv.length; i += 2) { uv[i] *= lw / 0.35; uv[i + 1] *= (fh - 0.4) / 0.35; } pl.setVerticesData(BABYLON.VertexBuffer.UVKind, uv);
  }
  // merge each material's parts into one mesh
  for (const k of Object.keys(parts) as Array<keyof typeof M>) { if (!parts[k].length) continue; const m = BABYLON.Mesh.MergeMeshes(parts[k], true, true)!; m.name = 'post_' + k; m.material = M[k]; m.parent = root; m.isPickable = false; }
  if (panels.length) { const m = BABYLON.Mesh.MergeMeshes(panels, true, true)!; m.name = 'post_wire'; m.material = wire; m.parent = root; m.isPickable = false; }
  return { root, gate: { x: cx + hx, z: cz }, searchlight: sl };
}

/** the dirt road from the gate to the mole's landward end: a ribbon on the ground, ruts darker, the edges fade into the sand */
export function buildRoad(scene: BABYLON.Scene, from: { x: number; z: number }): BABYLON.Mesh {
  const to = { x: MOLE.x - 1.6, z: MOLE.rampFrom - 4 };
  const pts: Array<[number, number]> = [];
  const mid = (t: number) => { const bend = Math.sin(t * Math.PI) * 7; return [from.x + (to.x - from.x) * t - bend * 0.6, from.z + (to.z - from.z) * t + bend] as [number, number]; };
  const N = 60; for (let i = 0; i <= N; i++) pts.push(mid(i / N));
  const pos: number[] = [], col: number[] = [], idx: number[] = [], nor: number[] = [];
  const W = 4.2, SEG = 7;           // the width and the cross-section's samples
  for (let i = 0; i < pts.length; i++) {
    const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)], dx = b[0] - a[0], dz = b[1] - a[1], l = Math.hypot(dx, dz) || 1, nx = -dz / l, nz = dx / l;
    for (let j = 0; j < SEG; j++) {
      const f = j / (SEG - 1) * 2 - 1, x = pts[i][0] + nx * f * W / 2, z = pts[i][1] + nz * f * W / 2;
      pos.push(x, bed(x, z) + 0.06, z); nor.push(0, 1, 0);
      const rut = Math.abs(Math.abs(f) - 0.45) < 0.14 ? 0.78 : 1, edge = 1 - Math.pow(Math.abs(f), 3.2), n = 0.92 + 0.08 * Math.sin(i * 1.7 + j * 3.1);
      col.push(0.42 * rut * n, 0.33 * rut * n, 0.22 * rut * n, Math.min(1, edge * 1.6) * 0.95);
    }
  }
  for (let i = 0; i < pts.length - 1; i++) for (let j = 0; j < SEG - 1; j++) { const a = i * SEG + j, b = a + 1, c = a + SEG, d = c + 1; idx.push(a, b, c, b, d, c); }
  const m = new BABYLON.Mesh('road', scene), vd = new BABYLON.VertexData(); vd.positions = pos; vd.normals = nor; vd.colors = col; vd.indices = idx; vd.applyToMesh(m, false);
  const mat = new BABYLON.StandardMaterial('road', scene); mat.specularColor = new BABYLON.Color3(0, 0, 0); mat.diffuseColor = new BABYLON.Color3(1, 1, 1); mat.transparencyMode = BABYLON.Material.MATERIAL_ALPHABLEND; mat.zOffset = -2; mat.backFaceCulling = false;
  m.hasVertexAlpha = true; m.material = mat; m.isPickable = false; m.alphaIndex = 5;
  return m;
}
