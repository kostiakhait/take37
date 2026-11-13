// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import { FIELD, RUNWAY, TAXI } from './config';
import { FIELD_LEVEL } from './ground3';
import { PAVED, PERIMETER, ROAD, EDGE_STEP, FILLET, type Rect } from './layout3';
import { Geo, Frame, box, rnd, type V3, type RGB } from './geo3';
import { Mats, TILE, decalMaterial } from './mats3';
import { asphaltTexture, slabOverlay, tarmacOverlay, paintTexture, numeralTexture, laneTexture, chainLinkTexture } from './textures3';

/**
 * The airfield's pavements and what lies on them: the concrete runway (the library's concrete, with slab joints, stains and cracks laid over it and its markings as geometry), the tarmac of the
 * taxiway, links and dispersal (tarmac drawn in code: the library has none), the concrete hangar apron (the library's other concrete), edge lights, the access road, the perimeter fence and gate, the
 * drainage ditches' water. All of it lies on the field's flat level `FIELD_LEVEL` (the road follows the ground beyond it).
 */
const L = FIELD_LEVEL, Y = L + 0.045;
const ID = new Frame(0, 0, 0, 0);

export interface Surfaces { meshes: BABYLON.Mesh[]; edgeLights: number; roadLength: number; fence: { posts: number; length: number }; shadowCasters: BABYLON.Mesh[] }

export async function buildSurfaces(scene: BABYLON.Scene, mats: Mats, ground: (x: number, z: number) => number): Promise<Surfaces> {
  const meshes: BABYLON.Mesh[] = [], casters: BABYLON.Mesh[] = [];
  const keep = (m: BABYLON.Mesh | null) => { if (m) meshes.push(m); return m; };
  const conc = await mats.get('concrete', { tint: [0.92, 0.9, 0.86], rough: 0.88, zOffset: -1 }), conc2 = await mats.get('concrete-312', { tint: [0.88, 0.86, 0.82], rough: 0.9, zOffset: -1 });
  const tar = new BABYLON.PBRMaterial('tarmac', scene); tar.albedoTexture = asphaltTexture(scene); tar.roughness = 0.93; tar.metallic = 0; tar.backFaceCulling = false; tar.zOffset = -1; tar.zOffsetUnits = -1; tar.environmentIntensity = 0.3;

  // ---- slabs of pavement: a flat quad a hair above the field's level and a thin edge so they stand on the ground ----
  const slab = (g: Geo, r: Rect, tile: number, c: RGB = [1, 1, 1], edge = true) => {
    g.quad([[r.x0, Y, r.z0], [r.x1, Y, r.z0], [r.x1, Y, r.z1], [r.x0, Y, r.z1]], [0, 1, 0], [[r.x0 / tile, r.z0 / tile], [r.x1 / tile, r.z0 / tile], [r.x1 / tile, r.z1 / tile], [r.x0 / tile, r.z1 / tile]], c);
    if (edge) { const d = 0.16, e = Y - d; for (const [a, b, n] of [[[r.x0, r.z0], [r.x1, r.z0], [0, 0, -1]], [[r.x1, r.z0], [r.x1, r.z1], [1, 0, 0]], [[r.x1, r.z1], [r.x0, r.z1], [0, 0, 1]], [[r.x0, r.z1], [r.x0, r.z0], [-1, 0, 0]]] as Array<[[number, number], [number, number], V3]>) g.quad([[a[0], e, a[1]], [b[0], e, b[1]], [b[0], Y, b[1]], [a[0], Y, a[1]]], n, [[0, 0], [1, 0], [1, 0.05], [0, 0.05]], [c[0] * 0.8, c[1] * 0.8, c[2] * 0.8]); }
  };
  // ---- rounded junctions: a convex polygon fan for a rectangle whose free corners are rounded (radius per corner x0z0, x1z0, x1z1, x0z1), and concave fillets in the corners where one pavement meets another ----
  const ARC = 24, skirt = (g: Geo, pts: Array<[number, number]>, d = 0.16) => { for (let i = 0; i + 1 < pts.length; i++) { const a = pts[i]!, b = pts[i + 1]!, nx = b[1] - a[1], nz = a[0] - b[0], l = Math.hypot(nx, nz) || 1; g.quad([[a[0], Y - d, a[1]], [b[0], Y - d, b[1]], [b[0], Y, b[1]], [a[0], Y, a[1]]], [nx / l, 0, nz / l], [[0, 0], [1, 0], [1, 1], [0, 1]]); } };
  const fan = (g: Geo, pts0: Array<[number, number]>, tile: number, yy = Y, c: RGB = [1, 1, 1], apex?: [number, number]) => { let ar = 0; for (let i = 0; i < pts0.length; i++) { const a = pts0[i]!, b = pts0[(i + 1) % pts0.length]!; ar += a[0] * b[1] - b[0] * a[1]; } const pts = ar < 0 ? [...pts0].reverse() : pts0; let cx = 0, cz = 0; if (apex) { cx = apex[0]; cz = apex[1]; } else { for (const p of pts) { cx += p[0]; cz += p[1]; } cx /= pts.length; cz /= pts.length; } for (let i = 0; i < pts.length; i++) { const a = pts[i]!, b = pts[(i + 1) % pts.length]!; if (apex && (a === apex || b === apex)) continue; g.tri([[a[0], yy, a[1]], [b[0], yy, b[1]], [cx, yy, cz]], [0, 1, 0], [[a[0] / tile, a[1] / tile], [b[0] / tile, b[1] / tile], [cx / tile, cz / tile]], c); } };
  const roundedPts = (r: Rect, rad: [number, number, number, number]): Array<[number, number]> => {
    const out: Array<[number, number]> = [], cs: Array<[number, number, number, number, number]> = [[r.x0, r.z0, 1, 1, rad[0]], [r.x1, r.z0, -1, 1, rad[1]], [r.x1, r.z1, -1, -1, rad[2]], [r.x0, r.z1, 1, -1, rad[3]]];
    const startAng = [Math.PI, Math.PI * 1.5, 0, Math.PI * 0.5];
    cs.forEach(([x, z, sx, sz, R], k) => { if (R <= 0) { out.push([x, z]); return; } const cx = x + sx * R, cz = z + sz * R; for (let i = 0; i <= ARC; i++) { const a = startAng[k]! + (i / ARC) * (Math.PI / 2); out.push([cx + Math.cos(a) * R, cz + Math.sin(a) * R]); } });
    return out;
  };
  /** the concave corner P = (px, pz) of two pavements, the free quarter-plane lying at (sx, sz); the arc is centred in the free quarter */
  const filletPts = (px: number, pz: number, sx: number, sz: number, R: number): Array<[number, number]> => {
    const cx = px + sx * R, cz = pz + sz * R, pts: Array<[number, number]> = [[px, pz]];
    for (let i = 0; i <= ARC; i++) { const a = (i / ARC) * (Math.PI / 2), ux = -sx, vz = -sz; pts.push([cx + R * ux * Math.cos(a), cz + R * vz * Math.sin(a)]); }
    return pts;
  };
  const rh0 = RUNWAY.half, tl = TAXI.x - TAXI.half, tr = TAXI.x + TAXI.half;
  /** every concave junction of the layout: [corner x, corner z, free-quarter signs, radius] */
  const FILLETS: Array<[number, number, number, number, number]> = [];
  PAVED.links.forEach((r, li) => { const R = FILLET.link; for (const [z, sz] of [[r.z0, -1], [r.z1, 1]] as Array<[number, number]>) { FILLETS.push([rh0, z, 1, sz, R]); if ((li === 0 && sz < 0) || (li === PAVED.links.length - 1 && sz > 0)) continue; /* the end links' outer edges run straight on into the taxiway's ends */ FILLETS.push([tl, z, -1, sz, R]); } });
  for (const [r, R] of [[PAVED.dispersal, FILLET.apron], [PAVED.apron, FILLET.apron]] as Array<[Rect, number]>) for (const [z, sz] of [[r.z0, -1], [r.z1, 1]] as Array<[number, number]>) FILLETS.push([tr, z, 1, sz, R]);
  const gRun = new Geo(), gTar = new Geo(), gApron = new Geo(), fc = FILLET.corner;
  slab(gRun, PAVED.runway, TILE.concrete!);
  // the taxiway: east corners rounded at both ends (the west ones are the links' edges)
  fan(gTar, roundedPts(PAVED.taxi, [0, fc, fc, 0]), 3);
  { const pts = roundedPts(PAVED.taxi, [0, fc, fc, 0]); skirt(gTar, [...pts, pts[0]!]); }
  for (const r of PAVED.links) slab(gTar, r, 3, [1, 1, 1], false);
  { const r = PAVED.dispersal; fan(gTar, roundedPts(r, [0, fc, fc, 0]), 3); const pts = roundedPts(r, [0, fc, fc, 0]); skirt(gTar, [...pts, pts[0]!]); }
  { const r = PAVED.apron, pts = roundedPts(r, [0, fc, fc, 0]); fan(gApron, pts, TILE['concrete-312']!); skirt(gApron, [...pts, pts[0]!]); }
  for (const [px, pz, sx, sz, R] of FILLETS) { const pts = filletPts(px, pz, sx, sz, R), big = px > tr - 1 && px < tr + 1 && Math.abs(R - FILLET.apron) < 0.1 && pz > 280; fan(px > tr - 1 && pz > 280 ? gApron : gTar, pts, px > tr - 1 && pz > 280 ? TILE['concrete-312']! : 3, Y, [1, 1, 1], pts[0]!); void big; skirt(px > tr - 1 && pz > 280 ? gApron : gTar, pts.slice(1)); }
  keep(gRun.mesh(scene, 'runway', conc)); keep(gTar.mesh(scene, 'tarmac', tar)); keep(gApron.mesh(scene, 'apron', conc2));

  // ---- wear laid over them (RGBA overlays; tile 30 m / 24 m) ----
  const slabs = decalMaterial(scene, 'slab-wear', { tex: slabOverlay(scene), z: -2 }), tarWear = decalMaterial(scene, 'tarmac-wear', { tex: tarmacOverlay(scene), z: -2 });
  const wRun = new Geo(), wTar = new Geo();
  const over = (g: Geo, r: Rect, tile: number) => g.quad([[r.x0, Y + 0.012, r.z0], [r.x1, Y + 0.012, r.z0], [r.x1, Y + 0.012, r.z1], [r.x0, Y + 0.012, r.z1]], [0, 1, 0], [[r.x0 / tile, r.z0 / tile], [r.x1 / tile, r.z0 / tile], [r.x1 / tile, r.z1 / tile], [r.x0 / tile, r.z1 / tile]]);
  over(wRun, PAVED.runway, 30); fan(wRun, roundedPts(PAVED.apron, [0, fc, fc, 0]), 30, Y + 0.012);
  fan(wTar, roundedPts(PAVED.taxi, [0, fc, fc, 0]), 24, Y + 0.012); for (const r of PAVED.links) over(wTar, r, 24); fan(wTar, roundedPts(PAVED.dispersal, [0, fc, fc, 0]), 24, Y + 0.012);
  for (const [px, pz, sx, sz, R] of FILLETS) { const pts = filletPts(px, pz, sx, sz, R), big = px > tr - 1 && pz > 280; fan(big ? wRun : wTar, pts, big ? 30 : 24, Y + 0.012, [1, 1, 1], pts[0]!); }
  keep(wRun.mesh(scene, 'slab-wear', slabs, { colors: false })); keep(wTar.mesh(scene, 'tarmac-wear', tarWear, { colors: false }));

  // ---- the runway's rubber: dark streaks where tyres touch down, at both ends; oil in the centre of the parking line ----
  const rub = new BABYLON.DynamicTexture('rubber', { width: 256, height: 512 }, scene, true), rc = rub.getContext() as unknown as CanvasRenderingContext2D, r1 = rnd(5);
  rc.clearRect(0, 0, 256, 512);
  for (let i = 0; i < 240; i++) { const x = 40 + r1() * 176, y = r1() * 512, a = 0.04 + 0.12 * r1(), w = 3 + r1() * 12, h = 20 + r1() * 90; rc.fillStyle = `rgba(10,9,8,${a})`; rc.fillRect(x, y, w, h); }
  for (let i = 0; i < 18; i++) { const x = 70 + r1() * 116, y = 40 + r1() * 400, g = rc.createLinearGradient(0, y, 0, y + 110); g.addColorStop(0, 'rgba(8,8,8,0)'); g.addColorStop(0.5, 'rgba(8,8,8,0.35)'); g.addColorStop(1, 'rgba(8,8,8,0)'); rc.fillStyle = g; rc.fillRect(x, y, 7, 110); }
  rub.update(true); rub.hasAlpha = true;
  const rubM = decalMaterial(scene, 'rubber', { tex: rub, z: -3 }), gRub = new Geo();
  for (const [za, zb] of [[RUNWAY.z1 - 130, RUNWAY.z1 - 12], [RUNWAY.z0 + 12, RUNWAY.z0 + 130]] as Array<[number, number]>) gRub.quad([[-9, Y + 0.02, za], [9, Y + 0.02, za], [9, Y + 0.02, zb], [-9, Y + 0.02, zb]], [0, 1, 0], [[0, 0], [1, 0], [1, 1], [0, 1]]);
  keep(gRub.mesh(scene, 'rubber', rubM, { colors: false }));

  // ---- markings as geometry: crisp at every distance; the chalky paint alpha wears them ----
  const paint = paintTexture(scene), white = decalMaterial(scene, 'paint-white', { tex: paint, z: -4 }), yellowTex = paint, yellow = decalMaterial(scene, 'paint-yellow', { tex: yellowTex, colour: [0.95, 0.78, 0.2], z: -4 });
  const gW = new Geo(), gY = new Geo(), Yp = Y + 0.03;
  const bar = (g: Geo, x0: number, x1: number, z0: number, z1: number) => g.quad([[x0, Yp, z0], [x1, Yp, z0], [x1, Yp, z1], [x0, Yp, z1]], [0, 1, 0], [[x0 / 4, z0 / 4], [x1 / 4, z0 / 4], [x1 / 4, z1 / 4], [x0 / 4, z1 / 4]]);
  const rh = RUNWAY.half;
  // the runway: edge lines, centre dashes, threshold bars at both ends, touchdown pairs
  bar(gW, -rh + 0.9, -rh + 1.3, RUNWAY.z0 + 4, RUNWAY.z1 - 4); bar(gW, rh - 1.3, rh - 0.9, RUNWAY.z0 + 4, RUNWAY.z1 - 4);
  for (let z = RUNWAY.z0 + 150; z < RUNWAY.z1 - 150; z += 50) bar(gW, -0.45, 0.45, z, z + 30);
  for (const north of [false, true]) {
    const zs = north ? RUNWAY.z0 + 6 : RUNWAY.z1 - 6, s = north ? 1 : -1;
    for (let i = 0; i < 8; i++) { const x = (i - 3.5) * 2.0 - 0.45; bar(gW, x - 0.4, x + 0.4, north ? zs : zs - 30, north ? zs + 30 : zs); void s; }
    for (const dz of [150, 300]) for (const sx of [-1, 1]) { const zc = north ? RUNWAY.z0 + dz : RUNWAY.z1 - dz; for (let k = 0; k < (dz === 150 ? 2 : 1); k++) bar(gW, sx * (5.5 + k * 1.8) - 0.5, sx * (5.5 + k * 1.8) + 0.5, zc - 11, zc + 11); }
  }
  // the taxiway's yellow centre line, along its links and onto the runway's edge; a hold line at each link
  // the centre lines: along the taxiway between the lead-on curves, and from each link a curve of radius `lead` onto the taxiway (both ways at a through link, one way at the two end links); hold lines across the links
  const rib = (g: Geo, line: Array<[number, number]>, hw = 0.1) => { for (let i = 0; i + 1 < line.length; i++) { const a = line[i]!, b = line[i + 1]!, dx = b[0] - a[0], dz = b[1] - a[1], l = Math.hypot(dx, dz) || 1, nx = -dz / l * hw, nz = dx / l * hw; g.quad([[a[0] - nx, Yp, a[1] - nz], [b[0] - nx, Yp, b[1] - nz], [b[0] + nx, Yp, b[1] + nz], [a[0] + nx, Yp, a[1] + nz]], [0, 1, 0], [[a[0] / 4, a[1] / 4], [b[0] / 4, a[1] / 4], [b[0] / 4, b[1] / 4], [a[0] / 4, b[1] / 4]]); } };
  const R2 = FILLET.lead, zEnds = [TAXI.links[0]! + R2, TAXI.links[TAXI.links.length - 1]! - R2];
  bar(gY, TAXI.x - 0.1, TAXI.x + 0.1, zEnds[0]!, zEnds[1]!);
  const nLinks = TAXI.links.length;
  TAXI.links.forEach((zc, li) => {
    bar(gY, rh + 0.5, TAXI.x - R2, zc - 0.1, zc + 0.1);
    for (const dir of [-1, 1]) {
      if ((li === 0 && dir < 0) || (li === nLinks - 1 && dir > 0)) continue;   // the end links turn one way only (toward the middle of the taxiway)
      const cx = TAXI.x - R2, cz = zc + dir * R2, arc: Array<[number, number]> = [];
      for (let i = 0; i <= 14; i++) { const f = (i / 14) * (Math.PI / 2); arc.push([cx + R2 * Math.sin(f), cz - dir * R2 * Math.cos(f)]); }
      rib(gY, arc);
    }
  });
  for (const r of PAVED.links) { bar(gY, rh + 3.0, rh + 3.15, r.z0 + 0.4, r.z1 - 0.4); bar(gY, rh + 3.4, rh + 3.55, r.z0 + 0.4, r.z1 - 0.4); }
  keep(gW.mesh(scene, 'paint-white', white, { colors: false })); keep(gY.mesh(scene, 'paint-yellow', yellow, { colors: false }));
  // the numerals "36" (read from the south, the landing run north) and "18" at the other end
  const gN = new Geo(), mk = (text: string, zc: number, north: boolean) => {
    const a = 5, b = 6.5, y = Y + 0.035, t = numeralTexture(scene, text), m = decalMaterial(scene, 'num' + text, { tex: t, z: -5 });
    const g = new Geo(), p: V3[] = north ? [[-a, y, zc - b], [a, y, zc - b], [a, y, zc + b], [-a, y, zc + b]] : [[a, y, zc + b], [-a, y, zc + b], [-a, y, zc - b], [a, y, zc - b]];
    g.quad(p, [0, 1, 0], [[0, 0], [1, 0], [1, 1], [0, 1]]); keep(g.mesh(scene, 'numeral-' + text, m, { colors: false }));
  };
  mk('36', RUNWAY.z1 - 52, false); mk('18', RUNWAY.z0 + 52, true); void gN;

  // ---- edge lights: white posts on the runway's edge every EDGE_STEP m, green at the thresholds, blue lamps along the taxiway ----
  const post = BABYLON.MeshBuilder.CreateCylinder('edgepost', { height: 0.38, diameterTop: 0.1, diameterBottom: 0.16, tessellation: 6 }, scene), lamp = BABYLON.MeshBuilder.CreateSphere('edgelamp', { diameter: 0.16, segments: 6 }, scene);
  const pm = new BABYLON.PBRMaterial('edgepost', scene); pm.albedoColor = new BABYLON.Color3(0.82, 0.82, 0.8); pm.metallic = 0; pm.roughness = 0.8; post.material = pm;
  const mkLamp = (name: string, col: [number, number, number]) => { const m = new BABYLON.StandardMaterial(name, scene); m.emissiveColor = new BABYLON.Color3(...col); m.diffuseColor = BABYLON.Color3.Black(); m.specularColor = BABYLON.Color3.Black(); return m; };
  const lampW = lamp.clone('lampW'), lampB = lamp.clone('lampB'), lampG = lamp.clone('lampG'); lamp.dispose();
  lampW.material = mkLamp('lampW', [0.9, 0.88, 0.7]); lampB.material = mkLamp('lampB', [0.1, 0.2, 1.2]); lampG.material = mkLamp('lampG', [0.1, 1.0, 0.25]);
  const posts: number[] = [], wl: number[] = [], bl: number[] = [], gl: number[] = [];
  const put = (arr: number[], x: number, y: number, z: number, s = 1) => { arr.push(s, 0, 0, 0, 0, s, 0, 0, 0, 0, s, 0, x, y, z, 1); };
  let nLights = 0;
  for (let z = RUNWAY.z0; z <= RUNWAY.z1 + 0.1; z += EDGE_STEP) for (const sx of [-1, 1]) { const x = sx * (rh + 1.4); put(posts, x, L + 0.19, z); put(wl, x, L + 0.42, z); nLights++; }
  for (const zz of [RUNWAY.z0 + 1, RUNWAY.z1 - 1]) for (let i = -4; i <= 4; i++) { put(gl, i * 4.0, L + 0.1, zz, 1.0); nLights++; }
  // blue lamps along both edges of the taxiway except where a link, the dispersal or the apron opens; round each fillet, a lamp on its arc, and one on each rounded corner
  const open = (sx: number, z: number) => (sx < 0 && PAVED.links.some(r => z > r.z0 - FILLET.link - 2 && z < r.z1 + FILLET.link + 2)) || (sx > 0 && [PAVED.dispersal, PAVED.apron].some(r => z > r.z0 - FILLET.apron - 2 && z < r.z1 + FILLET.apron + 2));
  for (let z = TAXI.z0; z <= TAXI.z1; z += 30) for (const sx of [-1, 1]) { if (open(sx, z)) continue; put(bl, TAXI.x + sx * (TAXI.half + 1.0), L + 0.12, z); nLights++; }
  for (const [px, pz, sx, sz, R] of FILLETS) for (const f of [0.25, 0.75]) { const a = f * Math.PI / 2, cx = px + sx * R, cz = pz + sz * R, rr = R - 1.0; put(bl, cx - sx * rr * Math.cos(a), L + 0.12, cz - sz * rr * Math.sin(a)); nLights++; }
  for (const zz of [TAXI.z0, TAXI.z1]) for (const f of [0.5]) { const R = FILLET.corner, a = f * Math.PI / 2, sz = zz < 0 ? 1 : -1, cx = tr - R, cz = zz + sz * R; put(bl, cx + (R + 1) * Math.cos(a), L + 0.12, cz - sz * (R + 1) * Math.sin(a)); nLights++; }
  const inst = (m: BABYLON.Mesh, buf: number[]) => { if (!buf.length) { m.dispose(); return; } m.thinInstanceSetBuffer('matrix', new Float32Array(buf), 16, true); m.alwaysSelectAsActiveMesh = true; m.isPickable = false; meshes.push(m); };
  inst(post, posts); inst(lampW, wl); inst(lampB, bl); inst(lampG, gl);

  // ---- the access road ----
  const lane = decalMaterial(scene, 'lane', { tex: laneTexture(scene), z: -3, spec: 0.03 }), gRoad = new Geo();
  const pts: Array<[number, number]> = [];
  for (let i = 0; i + 1 < ROAD.length; i++) {
    const p0 = ROAD[Math.max(0, i - 1)]!, p1 = ROAD[i]!, p2 = ROAD[i + 1]!, p3 = ROAD[Math.min(ROAD.length - 1, i + 2)]!, n = Math.max(2, Math.round(Math.hypot(p2[0] - p1[0], p2[1] - p1[1]) / 4));
    for (let k = 0; k < n; k++) { const t = k / n, t2 = t * t, t3 = t2 * t, f = (a: number, b: number, c: number, d: number) => 0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3); pts.push([f(p0[0], p1[0], p2[0], p3[0]), f(p0[1], p1[1], p2[1], p3[1])]); }
  }
  pts.push(ROAD[ROAD.length - 1]!);
  const left: V3[] = [], right: V3[] = []; let run = 0, roadLen = 0;
  const hw = 3.4;
  pts.forEach((p, i) => {
    const a = pts[Math.max(0, i - 1)]!, b = pts[Math.min(pts.length - 1, i + 1)]!, dx = b[0] - a[0], dz = b[1] - a[1], l = Math.hypot(dx, dz) || 1, nx = -dz / l, nz = dx / l;
    const lx = p[0] + nx * hw, lz = p[1] + nz * hw, rx = p[0] - nx * hw, rz = p[1] - nz * hw;
    left.push([lx, ground(lx, lz) + 0.06, lz]); right.push([rx, ground(rx, rz) + 0.06, rz]);
    if (i) { run += Math.hypot(p[0] - pts[i - 1]![0], p[1] - pts[i - 1]![1]); roadLen = run; }
  });
  { let acc = 0; gRoad.strip(left, right, (i) => { if (i) acc += Math.hypot(pts[i]![0] - pts[i - 1]![0], pts[i]![1] - pts[i - 1]![1]); return acc / 6; }, [1, 1, 1], 1); }
  keep(gRoad.mesh(scene, 'road', lane));

  // ---- perimeter fence: a stadium of chain-link on posts, with a double gate on the east side ----
  const fenceTex = chainLinkTexture(scene), fenceM = new BABYLON.PBRMaterial('chainlink', scene); fenceM.albedoTexture = fenceTex; fenceM.albedoTexture.hasAlpha = true; fenceM.useAlphaFromAlbedoTexture = true; fenceM.transparencyMode = BABYLON.Material.MATERIAL_ALPHATEST; fenceM.alphaCutOff = 0.4;
  fenceM.backFaceCulling = false; fenceM.twoSidedLighting = true; fenceM.metallic = 0.6; fenceM.roughness = 0.5; fenceM.environmentIntensity = 0.4;
  const ring: Array<[number, number]> = [], [ax, az] = FIELD.from, [bx, bz] = FIELD.to, R = PERIMETER.radius;
  for (let z = az; z <= bz; z += 20) ring.push([bx + R, z]);
  for (let i = 0; i <= 24; i++) { const a = (i / 24) * Math.PI; ring.push([bx + Math.cos(a) * R, bz + Math.sin(a) * R]); }
  for (let z = bz; z >= az; z -= 20) ring.push([bx - R, z]);
  for (let i = 0; i <= 24; i++) { const a = Math.PI + (i / 24) * Math.PI; ring.push([ax + Math.cos(a) * R, az + Math.sin(a) * R]); }
  const gate = PERIMETER.gate, gF = new Geo(), fposts: number[] = []; let fl = 0;
  const FH = 2.0;
  for (let i = 0; i < ring.length; i++) {
    const a = ring[i]!, b = ring[(i + 1) % ring.length]!, d = Math.hypot(b[0] - a[0], b[1] - a[1]); if (d < 0.1) continue;
    const nseg = Math.max(1, Math.round(d / 3.5));
    for (let k = 0; k < nseg; k++) {
      const x0 = a[0] + ((b[0] - a[0]) * k) / nseg, z0 = a[1] + ((b[1] - a[1]) * k) / nseg, x1 = a[0] + ((b[0] - a[0]) * (k + 1)) / nseg, z1 = a[1] + ((b[1] - a[1]) * (k + 1)) / nseg;
      const mx = (x0 + x1) / 2, mz = (z0 + z1) / 2; if (Math.abs(mx - gate.x) < 6 && Math.abs(mz - gate.z) < 5.2) continue;     // the gate's opening
      const ya = ground(x0, z0), yb = ground(x1, z1), sl = Math.hypot(x1 - x0, z1 - z0);
      gF.quad([[x0, ya, z0], [x1, yb, z1], [x1, yb + FH, z1], [x0, ya + FH, z0]], [0, 0, 1], [[0, 0], [sl, 0], [sl, FH], [0, FH]]); fl += sl;
      put(fposts, x0, ya + FH / 2, z0);
    }
  }
  keep(gF.mesh(scene, 'fence', fenceM, { colors: false }));
  const fpost = BABYLON.MeshBuilder.CreateBox('fencepost', { width: 0.1, height: FH + 0.25, depth: 0.1 }, scene), fpm = new BABYLON.PBRMaterial('fencepost', scene); fpm.albedoColor = new BABYLON.Color3(0.42, 0.36, 0.3); fpm.metallic = 0; fpm.roughness = 0.9; fpost.material = fpm;
  inst(fpost, fposts);
  // the gate: two posts and two leaves (open), a gatehouse lamp
  const gG = new Geo(), woodM = await mats.get('wood-pine', { tint: [0.7, 0.66, 0.6], rough: 0.9 });
  const gf = new Frame(gate.x, ground(gate.x, gate.z), gate.z, Math.PI / 2);
  for (const s of [-1, 1]) { box(gG, gf, s * 5.6 - 0.25, s * 5.6 + 0.25, 0, 2.6, -0.25, 0.25, [1, 1, 1], [2, 2]); }
  for (const s of [-1, 1]) { const f2 = new Frame(gate.x + 3.6 * Math.sin(0.0), ground(gate.x, gate.z), gate.z + s * 5.3, Math.PI / 2 - s * 1.35); box(gG, f2, 0, 4.8 * 0.5, 0.15, 1.9, -0.05, 0.05, [0.85, 0.85, 0.85], [2, 2]); box(gG, f2, 0, 2.4, 0.15, 0.3, -0.06, 0.06, [0.9, 0.9, 0.9], [2, 2]); }
  casters.push(keep(gG.mesh(scene, 'gate', woodM))!);
  void ID;
  return { meshes, edgeLights: nLights, roadLength: roadLen, fence: { posts: fposts.length / 16, length: fl }, shadowCasters: casters };
}
