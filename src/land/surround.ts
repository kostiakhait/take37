// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import { hash2, makeRock } from '@ferret/terrain';
import { PLATFORM, platformEdgeDistance } from '../config/stage';
import { sage, strawTuft } from './plants';

/**
 * The near surround of the platform: outcrops of large rocks in groups, and big shrubs and tussocks, set by hand-made rules (a seeded scatter in a belt 15 to 420 m off the platform,
 * off the dirt roads, off the steep ground), because the module's scatter is a density per biome and keeps the same weight at 20 m as at 2 km.
 */
export interface SurroundOptions { seed: number; ground: (x: number, z: number) => number; roadDistance: (x: number, z: number) => number }

function rng(seed: number) { let a = seed >>> 0; return () => { a = (a + 0x6d2b79f5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

function rockMesh(scene: BABYLON.Scene, seed: number, variant: number, mat: BABYLON.Material): BABYLON.Mesh {
  const d = makeRock(seed, variant, 0.75, 2), mesh = new BABYLON.Mesh(`surround-rock-${variant}`, scene), n = d.positions.length / 3, col = new Float32Array(n * 4);
  for (let i = 0; i < n; i++) {
    const y = d.positions[i * 3 + 1], t = Math.min(1, Math.max(0, y)), h = hash2(i, variant, seed);
    const k = 0.78 + 0.28 * h, w = 0.8 + 0.5 * t;
    col[i * 4] = 0.5 * k * w; col[i * 4 + 1] = 0.44 * k * w; col[i * 4 + 2] = 0.36 * k * w; col[i * 4 + 3] = 1;
  }
  const vd = new BABYLON.VertexData(); vd.positions = d.positions; vd.indices = d.indices; vd.normals = d.normals; vd.colors = col; vd.applyToMesh(mesh);
  mesh.material = mat; mesh.isPickable = false; return mesh;
}

function plantMesh(scene: BABYLON.Scene, name: string, data: { positions: Float32Array; normals: Float32Array; indices: Uint32Array | number[]; colors: Float32Array }, mat: BABYLON.Material): BABYLON.Mesh {
  const mesh = new BABYLON.Mesh(name, scene), vd = new BABYLON.VertexData();
  vd.positions = data.positions; vd.indices = Array.from(data.indices); vd.normals = data.normals; vd.colors = data.colors; vd.applyToMesh(mesh); mesh.material = mat; mesh.isPickable = false; return mesh;
}

export function buildSurround(scene: BABYLON.Scene, rockMat: BABYLON.Material, plantMat: BABYLON.Material, o: SurroundOptions) {
  const R = rng(o.seed), [ax, az] = PLATFORM.from, [bx] = PLATFORM.to;
  const rocks = [0, 1, 2, 3, 4].map(v => rockMesh(scene, o.seed + 3, v, rockMat));
  const sages = [0, 1, 2, 3].map(v => plantMesh(scene, `surround-sage-${v}`, sage(o.seed, v), plantMat));
  const tufts = [0, 1, 2].map(v => plantMesh(scene, `surround-tuft-${v}`, strawTuft(o.seed, v), plantMat));
  const rockM: number[][] = rocks.map(() => []), sageM: number[][] = sages.map(() => []), tuftM: number[][] = tufts.map(() => []);
  const slope = (x: number, z: number) => Math.hypot(o.ground(x + 3, z) - o.ground(x - 3, z), o.ground(x, z + 3) - o.ground(x, z - 3)) / 6;
  /** a random spot in the belt round the platform */
  const spot = (): [number, number] => {
    for (let k = 0; k < 40; k++) {
      const x = ax - 300 + R() * (bx - ax + 600), z = (R() * 2 - 1) * (PLATFORM.halfWidth + 420);
      const e = platformEdgeDistance(x, z);
      if (e > 14 && e < 420 && o.roadDistance(x, z) > 3) return [x, z];
    }
    return [ax - 200, 200];
  };
  const push = (list: number[], x: number, y: number, z: number, sx: number, sy: number, yaw: number, tilt = 0) => {
    const m = BABYLON.Matrix.Compose(new BABYLON.Vector3(sx, sy, sx), BABYLON.Quaternion.RotationYawPitchRoll(yaw, tilt, 0), new BABYLON.Vector3(x, y, z));
    list.push(...m.toArray());
  };
  // outcrops: a heart of one or two big rocks with smaller ones round it
  for (let c = 0; c < 46; c++) {
    const [cx, cz] = spot(), n = 4 + Math.floor(R() * 9), big = 1.6 + R() * 2.6;
    for (let i = 0; i < n; i++) {
      const a = R() * 6.283, d = (i === 0 ? 0 : 1 + R() * big * 2.2), x = cx + Math.cos(a) * d, z = cz + Math.sin(a) * d, s = i === 0 ? big : big * (0.15 + 0.5 * R()) , v = Math.floor(R() * rocks.length);
      push(rockM[v], x, o.ground(x, z) - s * 0.12, z, s * (0.9 + 0.5 * R()), s * (0.65 + 0.4 * R()), R() * 6.283, (R() - 0.5) * 0.3);
    }
  }
  // lone rocks
  for (let i = 0; i < 160; i++) { const [x, z] = spot(), s = 0.35 + 1.2 * R() * R(), v = Math.floor(R() * rocks.length); push(rockM[v], x, o.ground(x, z) - s * 0.1, z, s * 1.2, s, R() * 6.283); }
  // big shrubs in clumps of sage, tussocks between them
  for (let c = 0; c < 60; c++) {
    const [cx, cz] = spot(), n = 3 + Math.floor(R() * 6);
    for (let i = 0; i < n; i++) {
      const a = R() * 6.283, d = R() * 9, x = cx + Math.cos(a) * d, z = cz + Math.sin(a) * d;
      if (platformEdgeDistance(x, z) < 12 || o.roadDistance(x, z) < 2.5 || slope(x, z) > 0.7) continue;
      const s = 1.1 + 1.9 * R() * R(); push(sageM[Math.floor(R() * sages.length)], x, o.ground(x, z) - 0.05, z, s * 1.35, s, R() * 6.283);
      for (let k = 0; k < 2; k++) { const x2 = x + (R() - 0.5) * 4, z2 = z + (R() - 0.5) * 4; if (platformEdgeDistance(x2, z2) < 12 || o.roadDistance(x2, z2) < 2) continue; const t = 0.7 + 0.9 * R(); push(tuftM[Math.floor(R() * tufts.length)], x2, o.ground(x2, z2), z2, t, t, R() * 6.283); }
    }
  }
  const apply = (meshes: BABYLON.Mesh[], lists: number[][]) => meshes.forEach((m, i) => {
    const n = lists[i].length / 16; if (!n) { m.setEnabled(false); return; }
    m.thinInstanceSetBuffer('matrix', new Float32Array(lists[i]), 16, true);
    const ic = new Float32Array(n * 4); for (let k = 0; k < n; k++) { const t = 0.88 + 0.24 * R(); ic[k * 4] = t; ic[k * 4 + 1] = t; ic[k * 4 + 2] = t; ic[k * 4 + 3] = 1; }
    m.thinInstanceSetBuffer('instanceColor', ic, 4, true); m.thinInstanceRefreshBoundingInfo(true); m.alwaysSelectAsActiveMesh = true;
  });
  apply(rocks, rockM); apply(sages, sageM); apply(tufts, tuftM);
  return { meshes: [...rocks, ...sages, ...tufts], count: [rockM, sageM, tuftM].flat().reduce((s, l) => s + l.length / 16, 0) };
}
