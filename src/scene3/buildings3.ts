// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import { FIELD_LEVEL } from './ground3';
import { HANGARS, TOWER, FUEL, NISSEN, R22_SPOT, PAVED, type Hangar } from './layout3';
import { Geo, Frame, box as boxRaw, cylinder as cylRaw, pipe as pipeRaw, rnd, type V3, type RGB } from './geo3';
import { Mats } from './mats3';
import { corrugationNormal, sandbagTexture } from './textures3';
import { WEATHERS } from './config';

/**
 * The airfield's buildings, made of boxes, arches and slices in `Geo` with the library's materials (brick, tiles, steel, rust, concrete, plaster, timber); only the corrugation of the sheet roofs
 * (a normal map) and the sandbags are drawn in code (textures3.ts). Hangars: two arched sheet-steel hangars on brick walls, one gabled brick workshop hangar, each with its big door half open and
 * an unlit dark inside; the watch tower; Nissen huts; the fuel store (bunded tanks, pump house, drums, a bowser); a windsock that turns with the wind; the R22's marked pad.
 */
const L = FIELD_LEVEL, Y0 = L + 0.04;
const deg = (d: number) => (d * Math.PI) / 180;
/** the geometry helpers take heights above the field's level */
const box = (g: Geo, f: Frame, x0: number, x1: number, y0: number, y1: number, z0: number, z1: number, c?: RGB, tile?: [number, number], top?: [number, number], o?: { bottom?: boolean; top?: boolean }) => boxRaw(g, f, x0, x1, y0 + L, y1 + L, z0, z1, c, tile, top, o);
const cylinder = (g: Geo, f: Frame, cx: number, cz: number, y0: number, y1: number, r0: number, r1: number, sides: number, c?: RGB, tile?: number, caps?: boolean) => cylRaw(g, f, cx, cz, y0 + L, y1 + L, r0, r1, sides, c, tile, caps);
const pipe = (g: Geo, f: Frame, x0: number, x1: number, yc: number, cz: number, r: number, sides: number, c?: RGB, tile?: number) => pipeRaw(g, f, x0, x1, yc + L, cz, r, sides, c, tile);
const dark = (c: RGB, k: number): RGB => [c[0] * k, c[1] * k, c[2] * k];
export interface Buildings { meshes: BABYLON.Mesh[]; casters: BABYLON.Mesh[]; windsock: { update(windFromDeg: number, speed: number, t: number): void }; counts: { hangars: number; huts: number; drums: number; vertices: number } }

export async function buildBuildings(scene: BABYLON.Scene, mats: Mats): Promise<Buildings> {
  const meshes: BABYLON.Mesh[] = [], casters: BABYLON.Mesh[] = [];
  let vertices = 0;
  const keep = (m: BABYLON.Mesh | null, cast = true) => { if (m) { meshes.push(m); if (cast) casters.push(m); vertices += m.getTotalVertices(); } return m; };
  const brick = await mats.get('brick-clay-old', { tint: [2.3, 1.95, 1.75], rough: 0.92 }), brick2 = await mats.get('bricks01-wa', { tint: [1.9, 1.65, 1.5], rough: 0.92 });
  const tiles = await mats.get('roof-tiles', { tint: [0.85, 0.8, 0.78], rough: 0.9 }), conc = await mats.get('concrete', { tint: [0.85, 0.83, 0.8], rough: 0.9 }), plaster = await mats.get('stucko-wa1', { tint: [0.92, 0.9, 0.82], rough: 0.95 });
  const wood = await mats.get('wood-brown', { tint: [0.75, 0.7, 0.62], rough: 0.9 }), woodDk = await mats.get('wood-dark-brown', { tint: [0.6, 0.55, 0.5], rough: 0.9 }), block = await mats.get('concrete-block', { tint: [1.7, 1.65, 1.55], rough: 0.92 });
  const corr = corrugationNormal(scene, 1.7); corr.uScale = corr.vScale = 3 / 0.304;
  const sheet = async (id: string, tint: RGB, key: string, rough = 0.62, metal = 0.3) => { const m = await mats.get(id, { tint, rough, key }); m.bumpTexture = corr; m.bumpTexture.level = 1.0; m.metallic = metal; return m; };
  const steel = await sheet('metal-steel', [0.78, 0.8, 0.82], 'hangar-sheet-1'), rust = await sheet('metal-rust', [0.8, 0.72, 0.66], 'hangar-sheet-2', 0.8, 0.2), nissen = await sheet('metal-rust', [1.0, 0.95, 0.88], 'nissen-sheet', 0.85, 0.15), doorM = await sheet('metal-rust', [1.0, 0.86, 0.74], 'hangar-door', 0.85, 0.2);
  const glass = new BABYLON.PBRMaterial('glass', scene); glass.albedoColor = new BABYLON.Color3(0.05, 0.08, 0.1); glass.metallic = 0.1; glass.roughness = 0.1; glass.environmentIntensity = 1.2; glass.emissiveColor = new BABYLON.Color3(0.05, 0.07, 0.09); glass.backFaceCulling = false;
  const frameM = new BABYLON.PBRMaterial('frame', scene); frameM.albedoColor = new BABYLON.Color3(0.85, 0.85, 0.8); frameM.metallic = 0; frameM.roughness = 0.7; frameM.backFaceCulling = false;
  const bm = (name: string, c: RGB, r = 0.8, mt = 0) => { const m = new BABYLON.PBRMaterial(name, scene); m.albedoColor = new BABYLON.Color3(...c); m.metallic = mt; m.roughness = r; m.backFaceCulling = false; m.twoSidedLighting = true; m.environmentIntensity = 0.4; return m; };
  const inside = new BABYLON.PBRMaterial('hangar-inside', scene); inside.albedoColor = new BABYLON.Color3(0.3, 0.28, 0.26); inside.unlit = true; inside.backFaceCulling = false;

  /** an end wall under a roof profile, in slices: the opening (door) cut from the bottom */
  const endWall = (g: Geo, f: Frame, z: number, flip: number, xs: number[], prof: (x: number) => number, door: { w: number; h: number } | null, c: RGB, tile: [number, number]) => {
    const n = f.d(0, 0, flip), pts = [...xs]; if (door) pts.push(-door.w / 2, door.w / 2); pts.sort((a, b) => a - b);
    for (let i = 0; i + 1 < pts.length; i++) {
      const a = pts[i]!, b = pts[i + 1]!; if (b - a < 1e-4) continue;
      const mid = (a + b) / 2, lo = door && Math.abs(mid) < door.w / 2 ? door.h : 0;
      const ya = Math.max(lo, prof(a)), yb = Math.max(lo, prof(b)), P = (x: number, y: number) => f.p(x, L + y, z);
      g.quad([P(a, lo), P(b, lo), P(b, yb), P(a, ya)], n, [[a / tile[0], lo / tile[1]], [b / tile[0], lo / tile[1]], [b / tile[0], yb / tile[1]], [a / tile[0], ya / tile[1]]], c);
    }
  };
  /** a window: a pane with a frame of four bars, on a wall at local (x, z) facing `flip` */
  const windowAt = (gg: Geo, gf: Geo, f: Frame, x: number, y: number, z: number, w: number, h: number, flip: number, side = false) => {
    const t = 0.05 * flip, P = (u: number, v: number): V3 => side ? f.p(x, L + v, z + u) : f.p(x + u, L + v, z);
    gg.quad([P(-w / 2, y), P(w / 2, y), P(w / 2, y + h), P(-w / 2, y + h)], side ? f.d(flip, 0, 0) : f.d(0, 0, flip), [[0, 0], [1, 0], [1, 1], [0, 1]]);
    const bar = (a: V3, b: V3, c: V3, d: V3) => gf.quad([a, b, c, d], side ? f.d(flip, 0, 0) : f.d(0, 0, flip), [[0, 0], [1, 0], [1, 1], [0, 1]]);
    const T = 0.06, off = (p: V3): V3 => side ? [p[0] + f.d(t, 0, 0)[0], p[1], p[2] + f.d(t, 0, 0)[2]] : [p[0] + f.d(0, 0, t)[0], p[1], p[2] + f.d(0, 0, t)[2]];
    const q = (u0: number, u1: number, v0: number, v1: number) => bar(off(P(u0, v0)), off(P(u1, v0)), off(P(u1, v1)), off(P(u0, v1)));
    q(-w / 2 - T, w / 2 + T, y - T, y + T); q(-w / 2 - T, w / 2 + T, y + h - T, y + h + T); q(-w / 2 - T, -w / 2 + T, y, y + h); q(w / 2 - T, w / 2 + T, y, y + h); q(-T / 2, T / 2, y, y + h); q(-w / 2, w / 2, y + h / 2 - T / 2, y + h / 2 + T / 2);
  };

  // ---------------------------------------------------------------- hangars
  const hangar = (h: Hangar) => {
    const f = new Frame(h.cx, 0, h.cz, Math.PI / 2), S = h.span, D = h.depth, a = S / 2, b = h.ridge - h.eave, arch = h.kind === 'arch';
    const gBrick = new Geo(), gRoof = new Geo(), gIn = new Geo(), gDoor = new Geo(), gConc = new Geo(), gGlass = new Geo(), gFrame = new Geo(), gTile = new Geo();
    const prof = arch ? (x: number) => h.eave + b * Math.sqrt(Math.max(0, 1 - (x / a) * (x / a))) : (x: number) => h.eave + b * (1 - Math.abs(x) / a);
    const xsArch = Array.from({ length: 17 }, (_, i) => Math.cos((i / 16) * Math.PI) * a).reverse(), xs = arch ? xsArch : [-a, 0, a];
    const doorW = arch ? S - 6.5 : S - 5, doorH = Math.min(arch ? h.eave + b * 0.5 : h.eave - 0.3, prof(doorW / 2) - 0.5);
    const baseC: RGB = arch ? [0.9, 0.86, 0.82] : [1, 1, 1];
    // side walls: brick up to the eave, a concrete plinth, windows in a band
    const wallTile: [number, number] = [3, 3];
    for (const s of [-1, 1]) {
      const x = s * a; gBrick.quad([f.p(x, L, -D / 2), f.p(x, L, D / 2), f.p(x, L + h.eave, D / 2), f.p(x, L + h.eave, -D / 2)], f.d(s, 0, 0), [[-D / 2 / 3, 0], [D / 2 / 3, 0], [D / 2 / 3, h.eave / 3], [-D / 2 / 3, h.eave / 3]], baseC);
      box(gConc, f, s * a - 0.12, s * a + 0.12, 0, 0.45, -D / 2 - 0.1, D / 2 + 0.1, [0.85, 0.85, 0.85], [2, 2]);
      for (let z = -D / 2 + 3; z <= D / 2 - 2.5; z += 4.4) windowAt(gGlass, gFrame, f, x, 2.2, z, 1.6, h.eave > 4 ? 1.5 : 1.3, s, true);   // (side windows)
    }
    // the window panes above sit at height 2.3: lift them
    // end walls with the big door; the back wall solid
    endWall(gBrick, f, -D / 2, -1, xs, prof, { w: doorW, h: doorH }, baseC, wallTile); endWall(gBrick, f, D / 2, 1, xs, prof, null, baseC, wallTile);
    // reveal of the opening: 0.5 m deep
    for (const s of [-1, 1]) gBrick.quad([f.p(s * doorW / 2, L, -D / 2), f.p(s * doorW / 2, L, -D / 2 + 0.5), f.p(s * doorW / 2, L + doorH, -D / 2 + 0.5), f.p(s * doorW / 2, L + doorH, -D / 2)], f.d(-s, 0, 0), [[0, 0], [0.2, 0], [0.2, 1], [0, 1]], [0.7, 0.7, 0.7]);
    gBrick.quad([f.p(-doorW / 2, L + doorH, -D / 2), f.p(doorW / 2, L + doorH, -D / 2), f.p(doorW / 2, L + doorH, -D / 2 + 0.5), f.p(-doorW / 2, L + doorH, -D / 2 + 0.5)], f.d(0, -1, 0), [[0, 0], [1, 0], [1, 0.2], [0, 0.2]], [0.7, 0.7, 0.7]);
    // a concrete lintel beam and a canopy over the doors
    box(gConc, f, -doorW / 2 - 0.3, doorW / 2 + 0.3, doorH, doorH + 0.6, -D / 2 - 0.15, -D / 2 + 0.3, [0.9, 0.9, 0.9], [2, 2]);
    // roof
    const prow: V3[][] = [];
    if (arch) {
      let arc = 0;
      for (let i = 0; i + 1 < xs.length; i++) {
        const x0 = xs[i]!, x1 = xs[i + 1]!, y0 = prof(x0), y1 = prof(x1), seg = Math.hypot(x1 - x0, y1 - y0), mx = (x0 + x1) / 2, nx = (y1 - y0) / seg, ny = -(x1 - x0) / seg;
        const n = f.d(-(y1 - y0) / seg, (x1 - x0) / seg, 0), nn = 1; void mx; void nx; void ny;
        gRoof.quad([f.p(x0, L + y0, -D / 2 - 0.3), f.p(x1, L + y1, -D / 2 - 0.3), f.p(x1, L + y1, D / 2 + 0.3), f.p(x0, L + y0, D / 2 + 0.3)], [n[0] / nn, n[1] / nn, n[2] / nn], [[(-D / 2) / 3, arc / 3], [(-D / 2) / 3, (arc + seg) / 3], [(D / 2) / 3, (arc + seg) / 3], [(D / 2) / 3, arc / 3]]);
        // the underside: inside liner, unlit and darker toward the back wall
        const c0: RGB = [1, 1, 1], c1: RGB = [0.22, 0.22, 0.22];
        gIn.quad([f.p(x0, L + y0 - 0.08, -D / 2 + 0.3), f.p(x1, L + y1 - 0.08, -D / 2 + 0.3), f.p(x1, L + y1 - 0.08, D / 2 - 0.1), f.p(x0, L + y0 - 0.08, D / 2 - 0.1)], [0, -1, 0], [[0, 0], [0, 0], [0, 0], [0, 0]], c0);
        void c1; arc += seg;
      }
      void prow;
    } else {
      for (const s of [-1, 1]) {
        const x0 = 0, x1 = s * a, y0 = h.ridge, y1 = h.eave, seg = Math.hypot(a, b), n = f.d(s * b / seg, a / seg, 0);
        gTile.quad([f.p(x0, L + y0 + 0.1, -D / 2 - 0.45), f.p(x1 + s * 0.45, L + y1 - 0.16, -D / 2 - 0.45), f.p(x1 + s * 0.45, L + y1 - 0.16, D / 2 + 0.45), f.p(x0, L + y0 + 0.1, D / 2 + 0.45)], n, [[-(D / 2) / 3, 0], [-(D / 2) / 3, seg / 3], [(D / 2) / 3, seg / 3], [(D / 2) / 3, 0]]);
        gIn.quad([f.p(x0, L + y0 - 0.1, -D / 2 + 0.3), f.p(x1, L + y1 - 0.1, -D / 2 + 0.3), f.p(x1, L + y1 - 0.1, D / 2 - 0.1), f.p(x0, L + y0 - 0.1, D / 2 - 0.1)], [0, -1, 0], [[0, 0], [0, 0], [0, 0], [0, 0]]);
      }
      box(gConc, f, -0.15, 0.15, h.ridge - 0.02, h.ridge + 0.22, -D / 2 - 0.45, D / 2 + 0.45, [0.5, 0.2, 0.15], [1, 1]);   // a ridge course (reads as a terracotta ridge)
    }
    // the inside: floor, back wall, side liners (unlit, gradient into dark)
    const IN = (x: number, y: number, z: number): V3 => f.p(x, L + y, z), shade = (z: number): RGB => { const k = Math.max(0.16, 1 - ((z + D / 2) / D) * 0.9); return [k, k * 0.98, k * 0.95]; };
    for (const s of [-1, 1]) { const x = s * (a - 0.14), z0 = -D / 2 + 0.4, z1 = D / 2 - 0.15; gIn.quad([IN(x, 0.05, z0), IN(x, 0.05, z1), IN(x, h.eave, z1), IN(x, h.eave, z0)], [0, 1, 0], [[0, 0], [0, 0], [0, 0], [0, 0]], shade(z0)); }
    gIn.quad([IN(-a, 0.06, -D / 2 + 0.4), IN(a, 0.06, -D / 2 + 0.4), IN(a, 0.06, D / 2 - 0.15), IN(-a, 0.06, D / 2 - 0.15)], [0, 1, 0], [[0, 0], [0, 0], [0, 0], [0, 0]], [0.5, 0.5, 0.5]);
    gIn.quad([IN(-a, 0.05, D / 2 - 0.15), IN(a, 0.05, D / 2 - 0.15), IN(a, h.eave, D / 2 - 0.15), IN(-a, h.eave, D / 2 - 0.15)], [0, 0, -1], [[0, 0], [0, 0], [0, 0], [0, 0]], [0.16, 0.16, 0.15]);
    // gradient into dark along the roof liner: darken the far vertices of the last quads by z (vertex order: z0, z0, z1, z1)
    // door leaves: two on two rails, half open; ribs and a top rail
    const leafW = (S - 7) / 2 * 0.9, open = 0.55;
    for (const s of [-1, 1]) {
      const x0 = s > 0 ? a - 0.4 - leafW : -a + 0.4, x1 = x0 + leafW, zz = s > 0 ? -D / 2 - 0.35 : -D / 2 - 0.9, shift = s * 0;
      void open; void shift;
      box(gDoor, f, x0, x1, 0.15, doorH + 0.2, zz - 0.05, zz + 0.05, [1, 1, 1], [3, 3]);
      for (let x = x0 + 0.9; x < x1 - 0.3; x += 1.6) box(gDoor, f, x - 0.08, x + 0.08, 0.15, doorH + 0.2, zz + (s > 0 ? -0.14 : -0.14), zz - 0.05, [0.75, 0.7, 0.66], [3, 3]);
      box(gConc, f, x0 - 0.05, x1 + 0.05, doorH + 0.2, doorH + 0.5, zz - 0.15, zz + 0.12, [0.35, 0.34, 0.33], [1, 1]);
      for (const wx of [x0 + 0.5, x1 - 0.5]) box(gConc, f, wx - 0.2, wx + 0.2, 0.02, 0.2, zz - 0.1, zz + 0.1, [0.22, 0.22, 0.22], [1, 1]);
    }
    // rails above the door for the leaves
    box(gConc, f, -a + 0.2, a - 0.2, doorH + 0.5, doorH + 0.62, -D / 2 - 1.0, -D / 2 - 0.2, [0.3, 0.3, 0.32], [1, 1]);
    // a lean-to workshop on the north side (local +x), small windows
    if (h.id !== 'H3') {
      const w = 5.5, d2 = D * 0.55, hh = 3.3;
      box(gBrick, f, a, a + w, 0, hh, -D / 2 + 3, -D / 2 + 3 + d2, [0.95, 0.88, 0.84], [3, 3], [3, 3], { top: false });
      gTile.quad([f.p(a - 0.1, L + hh + 0.9, -D / 2 + 2.7), f.p(a + w + 0.4, L + hh - 0.15, -D / 2 + 2.7), f.p(a + w + 0.4, L + hh - 0.15, -D / 2 + 3.3 + d2), f.p(a - 0.1, L + hh + 0.9, -D / 2 + 3.3 + d2)], f.d(0.2, 1, 0), [[0, 0], [0, 2], [d2 / 3, 2], [d2 / 3, 0]]);
      windowAt(gGlass, gFrame, f, a + w, 0, -D / 2 + 3 + d2 / 2, 1.5, 1.2, 1, true);
      box(gDoor, f, a + 1.5, a + 2.7, 0.0, 2.2, -D / 2 + 3 - 0.06, -D / 2 + 3 + 0.02, [0.3, 0.45, 0.32], [1, 1]);
    }
    // downpipes and a gutter at the eaves (arch) / a chimney (gable)
    if (!arch) box(gBrick, f, -a + 1.6, -a + 2.7, h.eave - 1, h.ridge + 1.4, D / 2 - 3.2, D / 2 - 2.1, [0.9, 0.8, 0.75], [1, 1]);
    for (const z of [-D / 2 + 0.3, D / 2 - 0.3]) for (const s of [-1, 1]) box(gConc, f, s * (a + 0.06) - 0.06, s * (a + 0.06) + 0.06, 0, h.eave, z - 0.06, z + 0.06, [0.18, 0.2, 0.2], [1, 1]);
    // the house number painted on the front, high on the wall
    keep(gBrick.mesh(scene, h.id + '-brick', arch ? brick : brick2)); keep(gRoof.mesh(scene, h.id + '-roof', h.id === 'H1' ? steel : rust)); keep(gTile.mesh(scene, h.id + '-tiles', tiles));
    keep(gDoor.mesh(scene, h.id + '-door', doorM)); keep(gConc.mesh(scene, h.id + '-conc', conc)); keep(gIn.mesh(scene, h.id + '-in', inside), false);
    keep(gGlass.mesh(scene, h.id + '-glass', glass, { colors: false }), false); keep(gFrame.mesh(scene, h.id + '-frame', frameM, { colors: false }));
  };
  for (const h of HANGARS) hangar(h);

  // ---------------------------------------------------------------- the control tower
  {
    const f = new Frame(TOWER.cx, 0, TOWER.cz, deg(TOWER.yaw)), gB = new Geo(), gP = new Geo(), gC = new Geo(), gW = new Geo(), gG = new Geo(), gF = new Geo(), gM = new Geo(), gT = new Geo();
    const W0 = 10.6, D0 = 7.4, H0 = 3.4, W1 = 8.8, D1 = 6.4, H1 = 3.0, Hc = 2.5;
    box(gB, f, -W0 / 2, W0 / 2, 0, H0, -D0 / 2, D0 / 2, [0.95, 0.88, 0.84], [3, 3], [3, 3], { top: false });
    box(gC, f, -W0 / 2 - 0.15, W0 / 2 + 0.15, 0, 0.5, -D0 / 2 - 0.15, D0 / 2 + 0.15, [0.85, 0.85, 0.85], [2, 2]);
    // ground floor windows (front and back), a door on the side
    for (const x of [-3.6, -1.2, 1.2, 3.6]) { windowAt(gG, gF, f, x, 1.1, -D0 / 2 - 0.0, 1.3, 1.5, -1); windowAt(gG, gF, f, x, 1.1, D0 / 2, 1.3, 1.5, 1); }
    box(gM, f, -W0 / 2 - 0.05, -W0 / 2 + 0.05, 0.0, 2.2, -0.6, 0.6, [0.22, 0.34, 0.26], [1, 1]);
    // the first floor (watch office) of plaster, set in, with a balcony all round on the first floor's slab
    box(gP, f, -W0 / 2 - 1.1, W0 / 2 + 1.1, H0, H0 + 0.3, -D0 / 2 - 1.4, D0 / 2 + 1.1, [0.8, 0.8, 0.78], [2, 2], [2, 2]);
    box(gP, f, -W1 / 2, W1 / 2, H0 + 0.3, H0 + 0.3 + H1, -D1 / 2 - 0.3, D1 / 2 - 0.3, [1, 0.97, 0.9], [3, 3], [3, 3], { top: false });
    // the glazed visual control room on top: a band of windows on the three seaward sides
    const yR = H0 + 0.3 + H1, w2 = W1 - 0.8, d2 = D1 - 0.8, zc = -0.3;
    box(gP, f, -w2 / 2 - 0.2, w2 / 2 + 0.2, yR, yR + 0.3, -d2 / 2 - 0.5 + zc, d2 / 2 + 0.2 + zc, [0.78, 0.78, 0.75], [2, 2], [2, 2]);
    // glass walls of the control room: front (to -z local = toward the runway side), left, right: panes between mullions
    const gl = (x0: number, z0: number, x1: number, z1: number, n: V3) => { gG.quad([f.p(x0, L + yR + 0.3, z0), f.p(x1, L + yR + 0.3, z1), f.p(x1, L + yR + 0.3 + Hc, z1), f.p(x0, L + yR + 0.3 + Hc, z0)], f.d(n[0], n[1], n[2]), [[0, 0], [1, 0], [1, 1], [0, 1]]); };
    gl(-w2 / 2, -d2 / 2 + zc, w2 / 2, -d2 / 2 + zc, [0, 0, -1]); gl(-w2 / 2, d2 / 2 + zc, w2 / 2, d2 / 2 + zc, [0, 0, 1]); gl(-w2 / 2, -d2 / 2 + zc, -w2 / 2, d2 / 2 + zc, [-1, 0, 0]); gl(w2 / 2, -d2 / 2 + zc, w2 / 2, d2 / 2 + zc, [1, 0, 0]);
    for (let i = 0; i <= 6; i++) { const x = -w2 / 2 + (i / 6) * w2; box(gF, f, x - 0.04, x + 0.04, yR + 0.3, yR + 0.3 + Hc, -d2 / 2 + zc - 0.05, -d2 / 2 + zc + 0.02, [0.85, 0.85, 0.8], [1, 1]); box(gF, f, x - 0.04, x + 0.04, yR + 0.3, yR + 0.3 + Hc, d2 / 2 + zc - 0.02, d2 / 2 + zc + 0.05, [0.85, 0.85, 0.8], [1, 1]); }
    for (let i = 0; i <= 3; i++) { const z = -d2 / 2 + zc + (i / 3) * d2; for (const s of [-1, 1]) box(gF, f, s * w2 / 2 - 0.05 - (s > 0 ? 0 : -0.1), s * w2 / 2 + 0.05 + (s > 0 ? 0.1 : 0), yR + 0.3, yR + 0.3 + Hc, z - 0.04, z + 0.04, [0.85, 0.85, 0.8], [1, 1]); }
    box(gF, f, -w2 / 2, w2 / 2, yR + 0.3 + Hc / 2 - 0.03, yR + 0.3 + Hc / 2 + 0.03, -d2 / 2 + zc - 0.06, -d2 / 2 + zc, [0.85, 0.85, 0.8], [1, 1]);
    // the roof of the control room: a flat slab with a deep overhang and a parapet, a mast, a rotating beacon, a flagpole, a wind vane, a rail
    const yT = yR + 0.3 + Hc;
    box(gC, f, -w2 / 2 - 0.9, w2 / 2 + 0.9, yT, yT + 0.3, -d2 / 2 - 1.1 + zc, d2 / 2 + 0.7 + zc, [0.8, 0.8, 0.78], [2, 2], [2, 2]);
    box(gP, f, -w2 / 2 - 0.9, w2 / 2 + 0.9, yT + 0.3, yT + 0.75, -d2 / 2 - 1.1 + zc, -d2 / 2 - 1.0 + zc, [0.82, 0.82, 0.8], [2, 2]);
    cylinder(gM, f, w2 / 2 - 0.4, 0.5 + zc, yT + 0.3, yT + 7.2, 0.07, 0.04, 8, [0.45, 0.45, 0.45], 2);
    box(gM, f, w2 / 2 - 1.5, w2 / 2 + 0.7, yT + 5.2, yT + 5.26, 0.45 + zc, 0.55 + zc, [0.45, 0.45, 0.45], [1, 1]); box(gM, f, w2 / 2 - 1.1, w2 / 2 + 0.3, yT + 6.2, yT + 6.25, 0.46 + zc, 0.54 + zc, [0.45, 0.45, 0.45], [1, 1]);
    cylinder(gM, f, -w2 / 2 + 0.6, 0.0 + zc, yT + 0.3, yT + 5.6, 0.04, 0.03, 6, [0.85, 0.85, 0.85], 2);
    // balcony rails: posts and two rails round the slab's free edges
    const rail = (x0: number, z0: number, x1: number, z1: number) => { const n = Math.max(1, Math.round(Math.hypot(x1 - x0, z1 - z0) / 1.2)); for (let i = 0; i <= n; i++) { const x = x0 + ((x1 - x0) * i) / n, z = z0 + ((z1 - z0) * i) / n; box(gF, f, x - 0.025, x + 0.025, H0 + 0.3, H0 + 1.35, z - 0.025, z + 0.025, [0.2, 0.22, 0.22], [1, 1]); } for (const yy of [H0 + 0.75, H0 + 1.3]) box(gF, f, Math.min(x0, x1) - 0.03, Math.max(x0, x1) + 0.03, H0 + 0.3 + (yy - H0 - 0.3), H0 + 0.3 + (yy - H0 - 0.3) + 0.05, Math.min(z0, z1) - 0.03, Math.max(z0, z1) + 0.03, [0.2, 0.22, 0.22], [1, 1]); };
    rail(-W0 / 2 - 1.05, -D0 / 2 - 1.35, W0 / 2 + 1.05, -D0 / 2 - 1.35); rail(-W0 / 2 - 1.05, -D0 / 2 - 1.35, -W0 / 2 - 1.05, D0 / 2 + 1.05); rail(W0 / 2 + 1.05, -D0 / 2 - 1.35, W0 / 2 + 1.05, D0 / 2 + 1.05); rail(-W0 / 2 - 1.05, D0 / 2 + 1.05, W0 / 2 + 1.05, D0 / 2 + 1.05);
    // an outside stair on the back: concrete steps up to the balcony
    for (let i = 0; i < 16; i++) box(gC, f, W0 / 2 + 0.2, W0 / 2 + 1.1, 0, 0.2 + i * 0.2, D0 / 2 - 0.6 - i * 0.25 + 0.0, D0 / 2 + 0.0 - i * 0.25 + 0.0 + 0.3, [0.8, 0.8, 0.78], [1.5, 1.5]);
    // a guard hut and sandbags at the foot, a flag halyard
    keep(gB.mesh(scene, 'tower-brick', brick)); keep(gP.mesh(scene, 'tower-plaster', plaster)); keep(gC.mesh(scene, 'tower-conc', conc)); keep(gG.mesh(scene, 'tower-glass', glass, { colors: false }), false); keep(gF.mesh(scene, 'tower-frames', frameM, { colors: false })); keep(gM.mesh(scene, 'tower-mast', bm('mast', [0.5, 0.5, 0.5], 0.5, 0.5), { colors: true })); void gW; void gT;
  }

  // ---------------------------------------------------------------- Nissen huts
  {
    const gS = new Geo(), gE = new Geo(), gD = new Geo(), gF = new Geo(), gG = new Geo(), gC = new Geo();
    for (const n of NISSEN) {
      const f = new Frame(n.cx, 0, n.cz, deg(n.yaw)), R = 3.6, len = n.len, N = 14, prof = (i: number): [number, number] => { const th = (i / N) * Math.PI; return [Math.cos(th) * R, Math.sin(th) * R * 0.95]; };
      let arc = 0;
      for (let i = 0; i < N; i++) {
        const [x0, y0] = prof(i), [x1, y1] = prof(i + 1), seg = Math.hypot(x1 - x0, y1 - y0), am = ((i + 0.5) / N) * Math.PI;
        gS.quad([f.p(x1, L + y1, -len / 2), f.p(x0, L + y0, -len / 2), f.p(x0, L + y0, len / 2), f.p(x1, L + y1, len / 2)], f.d(Math.cos(am), Math.sin(am), 0), [[-len / 2 / 3, (arc + seg) / 3], [-len / 2 / 3, arc / 3], [len / 2 / 3, arc / 3], [len / 2 / 3, (arc + seg) / 3]]); arc += seg;
      }
      for (const [z, s] of [[-len / 2, -1], [len / 2, 1]] as Array<[number, number]>) {
        const xs = Array.from({ length: N + 1 }, (_, i) => prof(i)[0]).sort((p, q) => p - q), P = (x: number, y: number) => f.p(x, L + y, z), pf = (x: number) => Math.sqrt(Math.max(0, 1 - (x / R) * (x / R))) * R * 0.95;
        const dw = 1.0, dh = 2.1, dx = 0.4, door = z < 0;
        const pts = [...xs, ...(door ? [dx - dw / 2, dx + dw / 2] : [-2.1 - 0.5, -2.1 + 0.5, 2.1 - 0.5, 2.1 + 0.5])].sort((p, q) => p - q);
        for (let i = 0; i + 1 < pts.length; i++) {
          const a = pts[i]!, b = pts[i + 1]!; if (b - a < 1e-4) continue; const m = (a + b) / 2;
          const inDoor = door && m > dx - dw / 2 && m < dx + dw / 2, inWin = !door && (Math.abs(m + 2.1) < 0.5 || Math.abs(m - 2.1) < 0.5);
          if (inWin) { gE.quad([P(a, 0), P(b, 0), P(b, 0.9), P(a, 0.9)], f.d(0, 0, s), [[a / 3, 0], [b / 3, 0], [b / 3, 0.3], [a / 3, 0.3]], [0.9, 0.85, 0.8]); gE.quad([P(a, 1.9), P(b, 1.9), P(b, pf(b)), P(a, pf(a))], f.d(0, 0, s), [[a / 3, 0.6], [b / 3, 0.6], [b / 3, pf(b) / 3], [a / 3, pf(a) / 3]], [0.9, 0.85, 0.8]); }
          else gE.quad([P(a, inDoor ? dh : 0), P(b, inDoor ? dh : 0), P(b, Math.max(inDoor ? dh : 0, pf(b))), P(a, Math.max(inDoor ? dh : 0, pf(a)))], f.d(0, 0, s), [[a / 3, 0], [b / 3, 0], [b / 3, pf(b) / 3], [a / 3, pf(a) / 3]], [0.9, 0.85, 0.8]);
        }
        if (door) box(gD, f, dx - dw / 2 + 0.03, dx + dw / 2 - 0.03, 0, dh - 0.03, z - 0.08, z + 0.02, [0.3, 0.42, 0.3], [1, 1]);
        else for (const wx of [-2.1, 2.1]) { gG.quad([P(wx - 0.5, 0.9), P(wx + 0.5, 0.9), P(wx + 0.5, 1.9), P(wx - 0.5, 1.9)], f.d(0, 0, s), [[0, 0], [1, 0], [1, 1], [0, 1]]); box(gF, f, wx - 0.55, wx + 0.55, 0.85, 0.92, z + (s > 0 ? 0 : -0.08), z + (s > 0 ? 0.08 : 0), [0.9, 0.9, 0.85], [1, 1]); box(gF, f, wx - 0.55, wx + 0.55, 1.88, 1.95, z + (s > 0 ? 0 : -0.08), z + (s > 0 ? 0.08 : 0), [0.9, 0.9, 0.85], [1, 1]); }
      }
      box(gC, f, -R - 0.12, R + 0.12, 0, 0.3, -len / 2 - 0.1, len / 2 + 0.1, [0.75, 0.75, 0.73], [2, 2]);
      cylinder(gD, f, -2.4, 1.2, L - L + 3.8, 5.9, 0.15, 0.12, 6, [0.3, 0.28, 0.27], 1);     // a stove chimney
    }
    keep(gS.mesh(scene, 'nissen-shell', nissen)); keep(gE.mesh(scene, 'nissen-ends', brick2)); keep(gD.mesh(scene, 'nissen-doors', bm('nd', [0.8, 0.8, 0.78], 0.85), { colors: true })); keep(gF.mesh(scene, 'nissen-frames', frameM, { colors: true })); keep(gG.mesh(scene, 'nissen-glass', glass, { colors: false }), false); keep(gC.mesh(scene, 'nissen-base', conc));
  }

  // ---------------------------------------------------------------- the fuel store
  let drums = 0;
  {
    const f = new Frame(FUEL.cx, 0, FUEL.cz, 0), gB = new Geo(), gT = new Geo(), gD = new Geo(), gS = new Geo(), gW = new Geo(), gP = new Geo(), r = rnd(77);
    const w = FUEL.w, d = FUEL.d;
    // the bund wall (concrete block, 0.9 m) round the tanks' half, a gap for the access
    const bw = 0.35, bh = 0.95, bx0 = -w / 2, bx1 = w / 2 - 12, bz0 = -d / 2, bz1 = d / 2;
    box(gB, f, bx0, bx1, 0, bh, bz0, bz0 + bw, [1, 1, 1], [2, 2]); box(gB, f, bx0, bx1, 0, bh, bz1 - bw, bz1, [1, 1, 1], [2, 2]); box(gB, f, bx0, bx0 + bw, 0, bh, bz0, bz1, [1, 1, 1], [2, 2]); box(gB, f, bx1 - bw, bx1, 0, bh, bz0, bz1 - 9, [1, 1, 1], [2, 2]);
    // the floor of the bund: poured concrete a little above the field
    gB.quad([f.p(bx0, L + 0.06, bz0), f.p(bx1, L + 0.06, bz0), f.p(bx1, L + 0.06, bz1), f.p(bx0, L + 0.06, bz1)], f.d(0, 1, 0), [[0, 0], [5, 0], [5, 5], [0, 5]], [0.8, 0.8, 0.78]);
    // three horizontal tanks on saddles
    const tankC: RGB[] = [[0.55, 0.57, 0.52], [0.5, 0.52, 0.48], [0.58, 0.45, 0.38]];
    for (let i = 0; i < 3; i++) {
      const z = bz0 + 5.4 + i * 7.6, x0 = bx0 + 3.5, x1 = bx1 - 4;
      pipe(gT, f, x0, x1, 2.05, z, 1.55, 18, tankC[i]!, 2.5);
      for (const x of [x0 + 1.6, x1 - 1.6]) { box(gB, f, x - 0.35, x + 0.35, 0, 0.7, z - 1.4, z + 1.4, [0.85, 0.85, 0.85], [2, 2]); }
      for (const x of [x0 + 0.01, x1 - 0.01]) for (let k = 0; k < 18; k++) { const a0 = (k / 18) * 6.2832, a1 = ((k + 1) / 18) * 6.2832; gT.tri([f.p(x, L + 2.05, z), f.p(x, L + 2.05 + Math.sin(a0) * 1.55, z + Math.cos(a0) * 1.55), f.p(x, L + 2.05 + Math.sin(a1) * 1.55, z + Math.cos(a1) * 1.55)], f.d(x === x0 + 0.01 ? -1 : 1, 0, 0), [[0.5, 0.5], [0.5, 0.5], [0.5, 0.5]], tankC[i]!); }
      cylinder(gT, f, (x0 + x1) / 2, z, L - L + 3.5, 4.2, 0.55, 0.5, 10, [0.42, 0.44, 0.4], 1);      // a manhole dome
      box(gT, f, (x0 + x1) / 2 - 0.9, (x0 + x1) / 2 + 0.9, 3.4, 3.46, z - 0.25, z + 0.25, [0.25, 0.25, 0.25], [1, 1]);
      for (let k = 0; k < 4; k++) { const x = x0 + 3 + k * ((x1 - x0 - 6) / 3); pipe(gT, f, x - 0.08, x + 0.08, 2.05, z, 1.62, 18, [0.3, 0.3, 0.3], 1); }      // hoops
    }
    // pipework along the front of the tanks with valves
    for (let i = 0; i < 3; i++) { const z = bz0 + 5.4 + i * 7.6; cylinder(gP, f, bx1 - 2.2, z, 0.06, 1.7, 0.1, 0.1, 8, [0.2, 0.2, 0.22], 1, false); pipe(gP, f, bx1 - 2.2, bx1 + 6, 1.7, z, 0.1, 8, [0.2, 0.2, 0.22], 1); }
    pipe(gP, f, bx1 + 5.9, bx1 + 6.1, 1.7, bz0 + 5.4, 0.1, 8, [0.2, 0.2, 0.22], 1); box(gP, f, bx1 + 5.9, bx1 + 6.1, 0, 1.7, bz0 + 5.3, bz0 + 5.5, [0.2, 0.2, 0.22], [1, 1]); box(gP, f, bx1 + 5.9, bx1 + 6.1, 0, 1.7, bz0 + 5.4 + 15.1, bz0 + 5.6 + 15.1, [0.2, 0.2, 0.22], [1, 1]);
    // the pump house (brick, flat roof) at the bund's open side
    const px = w / 2 - 9, pz = bz0 + 3;
    box(gB, f, px, px + 6, 0, 3.0, pz, pz + 5, [0.95, 0.88, 0.84], [3, 3], [3, 3]); box(gB, f, px - 0.2, px + 6.2, 3.0, 3.25, pz - 0.2, pz + 5.2, [0.8, 0.8, 0.78], [2, 2]);
    // oil drums: a stack of lying pallets in rows (the colours of 1940s fuel: dark green, red, blue, grey, rust)
    const dc: RGB[] = [[0.22, 0.32, 0.2], [0.55, 0.16, 0.12], [0.2, 0.3, 0.5], [0.5, 0.5, 0.48], [0.5, 0.3, 0.18], [0.3, 0.38, 0.22]];
    const drum = (x: number, z: number, y0: number) => { const c = dc[Math.floor(r() * dc.length)]!; cylinder(gD, f, x, z, y0, y0 + 0.86, 0.29, 0.29, 10, c, 1.2); for (const hy of [0.14, 0.43, 0.72]) cylinder(gD, f, x, z, y0 + hy, y0 + hy + 0.05, 0.3, 0.3, 10, dark(c, 0.8), 1, false); drums++; };
    for (let row = 0; row < 3; row++) for (let col = 0; col < 12; col++) { const x = w / 2 - 14 + col * 0.64 + (row % 2) * 0.1, z = d / 2 - 3.4 + row * 0.66; drum(x, z, 0.14); if (col % 3 !== 2) drum(x, z, 1.0); box(gW, f, x - 0.3, x + 0.3, 0, 0.14, z - 0.3, z + 0.3, [0.6, 0.5, 0.4], [1, 1]); }
    for (let k = 0; k < 14; k++) drum(w / 2 - 17 + r() * 3.4, d / 2 - 12.5 + r() * 3, 0.04);
    // a stack of pallets and crates near the pump house; a fire point: red sand buckets on a rack
    box(gW, f, w / 2 - 17, w / 2 - 14, 0, 1.0, bz1 - 24, bz1 - 22.4, [0.7, 0.62, 0.5], [1, 1]);
    for (let i = 0; i < 4; i++) cylinder(gD, f, px + 0.6 + i * 0.5, pz + 5.5, 1.6, 1.95, 0.17, 0.2, 8, [0.7, 0.12, 0.08], 1);
    box(gW, f, px + 0.2, px + 2.8, 0, 1.6, pz + 5.3, pz + 5.45, [0.7, 0.62, 0.5], [1, 1]);
    // the bowser: a tanker trailer on four wheels with a hand pump
    const bf = new Frame(FUEL.cx - 8, 0, FUEL.cz + 16, deg(20)), gBw = new Geo();
    box(gBw, bf, -1.1, 1.1, 0.5, 0.75, -3.2, 3.2, [0.18, 0.2, 0.18], [1, 1]); pipe(gBw, bf, -3.2, 3.2, 1.4, 0, 0.95, 14, [0.28, 0.4, 0.26], 2);
    for (const x of [-2.2, 2.2]) for (const z of [-0.85, 0.85]) pipe(gBw, bf, x - 0.12, x + 0.12, 0.42, z, 0.42, 10, [0.08, 0.08, 0.08], 1);
    box(gBw, bf, 3.2, 4.4, 0.55, 0.65, -0.1, 0.1, [0.15, 0.15, 0.16], [1, 1]); box(gBw, bf, 3.2, 3.5, 0.55, 1.4, -0.45, 0.45, [0.5, 0.2, 0.15], [1, 1]);
    keep(gB.mesh(scene, 'fuel-bund', block)); keep(gT.mesh(scene, 'fuel-tanks', bm('tank', [1, 1, 1], 0.55, 0.5))); keep(gD.mesh(scene, 'fuel-drums', bm('drum', [1, 1, 1], 0.5, 0.45))); keep(gW.mesh(scene, 'fuel-pallets', wood));
    keep(gP.mesh(scene, 'fuel-pipes', bm('pipe', [1, 1, 1], 0.5, 0.6))); keep(gBw.mesh(scene, 'fuel-bowser', bm('bowser', [1, 1, 1], 0.6, 0.3))); void gS;
  }

  // ---------------------------------------------------------------- sheds, a bicycle shelter, a flag and the R22's pad
  {
    const gB = new Geo(), gR = new Geo(), gW = new Geo(), gC = new Geo();
    const shed = (cx: number, cz: number, yaw: number, w: number, d: number, h: number) => {
      const f = new Frame(cx, 0, cz, deg(yaw)); box(gW, f, -w / 2, w / 2, 0, h, -d / 2, d / 2, [1, 1, 1], [2, 2], [2, 2], { top: false });
      gR.quad([f.p(-w / 2 - 0.2, L + h + 0.5, -d / 2 - 0.2), f.p(w / 2 + 0.2, L + h - 0.1, -d / 2 - 0.2), f.p(w / 2 + 0.2, L + h - 0.1, d / 2 + 0.2), f.p(-w / 2 - 0.2, L + h + 0.5, d / 2 + 0.2)], f.d(0.15, 1, 0), [[0, 0], [1, 0], [1, 1], [0, 1]]);
      box(gC, f, -w / 2 - 0.1, w / 2 + 0.1, 0, 0.2, -d / 2 - 0.1, d / 2 + 0.1, [0.7, 0.7, 0.68], [2, 2]);
    };
    shed(214, 250, 0, 6, 4, 2.6); shed(204, 190, 90, 5, 3.4, 2.4); shed(300, 405, 0, 7, 4, 2.7); shed(150, 546, 90, 4.2, 3.2, 2.5);
    keep(gW.mesh(scene, 'sheds', wood)); keep(gR.mesh(scene, 'shed-roofs', rust)); keep(gC.mesh(scene, 'shed-bases', conc)); void gB;
  }
  // the R22's pad: a white square ring with a corner marks and an H, drawn in code, painted on the concrete
  {
    const S = 512, t = new BABYLON.DynamicTexture('padH', { width: S, height: S }, scene, true), c = t.getContext() as unknown as CanvasRenderingContext2D;
    c.clearRect(0, 0, S, S); c.strokeStyle = 'rgba(236,236,226,0.95)'; c.lineWidth = 16; c.beginPath(); c.arc(S / 2, S / 2, S / 2 - 18, 0, 7); c.stroke();
    c.lineWidth = 34; c.lineCap = 'butt'; c.beginPath(); c.moveTo(S * 0.33, S * 0.26); c.lineTo(S * 0.33, S * 0.74); c.moveTo(S * 0.67, S * 0.26); c.lineTo(S * 0.67, S * 0.74); c.moveTo(S * 0.33, S * 0.5); c.lineTo(S * 0.67, S * 0.5); c.stroke();
    for (let i = 0; i < 900; i++) { c.globalCompositeOperation = 'destination-out'; c.fillStyle = `rgba(0,0,0,${0.1 + 0.4 * Math.random()})`; c.fillRect(Math.random() * S, Math.random() * S, 2 + Math.random() * 4, 2 + Math.random() * 4); }
    t.update(true); t.hasAlpha = true;
    const m = new BABYLON.StandardMaterial('padH', scene); m.diffuseTexture = t; m.useAlphaFromDiffuseTexture = true; m.transparencyMode = BABYLON.Material.MATERIAL_ALPHABLEND; m.specularColor = BABYLON.Color3.Black(); m.zOffset = -6; m.zOffsetUnits = -6; m.backFaceCulling = false; m.disableDepthWrite = true;
    const g = new Geo(), p = R22_SPOT.pad, y = Y0 + 0.04; g.quad([[R22_SPOT.x - p, y, R22_SPOT.z - p], [R22_SPOT.x + p, y, R22_SPOT.z - p], [R22_SPOT.x + p, y, R22_SPOT.z + p], [R22_SPOT.x - p, y, R22_SPOT.z + p]], [0, 1, 0], [[0, 0], [1, 0], [1, 1], [0, 1]]);
    keep(g.mesh(scene, 'r22-pad', m, { colors: false }), false);
  }

  // ---------------------------------------------------------------- the windsock: a mast by the dispersal's end, a cone that hangs and swings with the wind
  const mastAt = { x: PAVED.runway.x1 + 34, z: -90 };
  const gm = new Geo(), mf = new Frame(mastAt.x, 0, mastAt.z, 0);
  cylinder(gm, mf, 0, 0, L, L + 7.4, 0.12, 0.07, 8, [0.85, 0.85, 0.85], 2); box(gm, mf, -0.6, 0.6, L + 0.0, L + 0.5, -0.6, 0.6, [0.7, 0.7, 0.68], [2, 2]);
  keep(gm.mesh(scene, 'windsock-mast', bm('mastw', [1, 1, 1], 0.6)));
  const sockNode = new BABYLON.TransformNode('windsock', scene); sockNode.position.set(mastAt.x, L + 7.2, mastAt.z);
  const arm = new BABYLON.TransformNode('windsock-arm', scene); arm.parent = sockNode;
  const gs = new Geo(), SEG = 5, SIDES = 12, len = 3.6;
  for (let k = 0; k < SEG; k++) {
    const r0 = 0.45 - (k * 0.3) / SEG, r1 = 0.45 - ((k + 1) * 0.3) / SEG, c: RGB = k % 2 ? [0.95, 0.94, 0.9] : [0.95, 0.32, 0.08], x0 = 0.12 + (k * len) / SEG, x1 = 0.12 + ((k + 1) * len) / SEG;
    for (let i = 0; i < SIDES; i++) { const a0 = (i / SIDES) * 6.2832, a1 = ((i + 1) / SIDES) * 6.2832, am = (a0 + a1) / 2; gs.quad([[x0, Math.sin(a0) * r0, Math.cos(a0) * r0], [x1, Math.sin(a0) * r1, Math.cos(a0) * r1], [x1, Math.sin(a1) * r1, Math.cos(a1) * r1], [x0, Math.sin(a1) * r0, Math.cos(a1) * r0]], [0.2, Math.sin(am), Math.cos(am)], [[0, 0], [0, 0], [0, 0], [0, 0]], c); }
  }
  for (let i = 0; i < 16; i++) { const a0 = (i / 16) * 6.2832, a1 = ((i + 1) / 16) * 6.2832; gs.quad([[0.1, Math.sin(a0) * 0.5, Math.cos(a0) * 0.5], [0.14, Math.sin(a0) * 0.46, Math.cos(a0) * 0.46], [0.14, Math.sin(a1) * 0.46, Math.cos(a1) * 0.46], [0.1, Math.sin(a1) * 0.5, Math.cos(a1) * 0.5]], [-1, 0, 0], [[0, 0], [0, 0], [0, 0], [0, 0]], [0.3, 0.3, 0.3]); }
  const sockM = bm('sock', [1, 1, 1], 0.85); sockM.emissiveColor = new BABYLON.Color3(0.04, 0.03, 0.02);
  const sock = gs.mesh(scene, 'windsock-cone', sockM, { freeze: false }); if (sock) { sock.parent = arm; meshes.push(sock); casters.push(sock); }
  const windsock = {
    update(windFromDeg: number, speed: number, t: number) {
      const to = deg(windFromDeg + 180), heading = Math.atan2(Math.sin(to), -Math.cos(to));        // the cone points along +x of the arm; compass 0 = -z, 90 = +x
      const stiff = Math.min(1, speed / 6.5), droop = (1 - stiff) * 1.25, flutter = Math.sin(t * 3.1) * 0.05 * stiff;
      sockNode.rotation.y = Math.PI / 2 - to; void heading; arm.rotation.z = -droop + flutter;
    },
  };
  void WEATHERS;
  void sandbagTexture; void woodDk;
  return { meshes, casters, windsock, counts: { hangars: HANGARS.length, huts: NISSEN.length, drums, vertices } };
}
