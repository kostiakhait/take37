// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// Bounds of the named nodes of a glb, read from its JSON chunk (accessor min/max and node transforms), without loading any mesh.
// The result is in the game's frame: x forward, y up, z across with the glTF's z mirrored (the loader's mirror of a right-handed file into the left-handed scene).
import type { NodeInfo } from '@ferret/destruction/autoparts';

type V3 = [number, number, number];
interface GNode { name?: string; children?: number[]; mesh?: number; matrix?: number[]; translation?: V3; rotation?: [number, number, number, number]; scale?: V3; extras?: Record<string, unknown> }
interface GLtf { nodes: GNode[]; meshes?: { primitives: { attributes: { POSITION: number } }[] }[]; accessors?: { min?: number[]; max?: number[] }[]; scenes?: { nodes: number[] }[] }

/** the JSON chunk of a .glb */
export function glbJson(buf: ArrayBuffer): GLtf {
  const dv = new DataView(buf);
  if (dv.getUint32(0, true) !== 0x46546c67) throw new Error('not a glb');
  const len = dv.getUint32(12, true);
  return JSON.parse(new TextDecoder().decode(new Uint8Array(buf, 20, len))) as GLtf;
}

const local = (n: GNode): number[] => {
  if (n.matrix) return n.matrix;
  const t = n.translation ?? [0, 0, 0], q = n.rotation ?? [0, 0, 0, 1], s = n.scale ?? [1, 1, 1], [x, y, z, w] = q;
  return [(1 - 2 * (y * y + z * z)) * s[0], 2 * (x * y + z * w) * s[0], 2 * (x * z - y * w) * s[0], 0, 2 * (x * y - z * w) * s[1], (1 - 2 * (x * x + z * z)) * s[1], 2 * (y * z + x * w) * s[1], 0,
    2 * (x * z + y * w) * s[2], 2 * (y * z - x * w) * s[2], (1 - 2 * (x * x + y * y)) * s[2], 0, t[0], t[1], t[2], 1];
};
const mul = (a: number[], b: number[]): number[] => { const o = new Array<number>(16).fill(0); for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) for (let k = 0; k < 4; k++) o[c * 4 + r]! += a[k * 4 + r]! * b[c * 4 + k]!; return o; };
const tp = (m: number[], p: V3): V3 => [m[0]! * p[0] + m[4]! * p[1] + m[8]! * p[2] + m[12]!, m[1]! * p[0] + m[5]! * p[1] + m[9]! * p[2] + m[13]!, m[2]! * p[0] + m[6]! * p[1] + m[10]! * p[2] + m[14]!];

/** world bounds (glTF frame) of every node with geometry below it, by node index, and the node's world matrix */
export function nodeBounds(j: GLtf): { min: V3; max: V3; world: number[] }[] {
  const parent = new Map<number, number>(); j.nodes.forEach((n, i) => (n.children ?? []).forEach((c) => parent.set(c, i)));
  const worlds = new Map<number, number[]>();
  const W = (i: number): number[] => { let w = worlds.get(i); if (w) return w; const p = parent.get(i), m = local(j.nodes[i]!); w = p === undefined ? m : mul(W(p), m); worlds.set(i, w); return w; };
  const out: { min: V3; max: V3; world: number[] }[] = [];
  j.nodes.forEach((_, i) => {
    const mn: V3 = [1e9, 1e9, 1e9], mx: V3 = [-1e9, -1e9, -1e9]; let has = false;
    const rec = (k: number): void => {
      const n = j.nodes[k]!;
      if (n.mesh !== undefined) for (const pr of j.meshes![n.mesh]!.primitives) {
        const a = j.accessors![pr.attributes.POSITION]!; if (!a.min || !a.max) continue;
        for (let c = 0; c < 8; c++) { const w = tp(W(k), [c & 1 ? a.max[0]! : a.min[0]!, c & 2 ? a.max[1]! : a.min[1]!, c & 4 ? a.max[2]! : a.min[2]!]); has = true; for (let d = 0; d < 3; d++) { mn[d] = Math.min(mn[d]!, w[d]!); mx[d] = Math.max(mx[d]!, w[d]!); } }
      }
      for (const c of n.children ?? []) rec(c);
    };
    rec(i);
    out[i] = has ? { min: mn, max: mx, world: W(i) } : { min: [0, 0, 0], max: [0, 0, 0], world: W(i) };
  });
  return out;
}

/** the bounds of the named nodes in the game's frame (z mirrored); wheels get their hub (the centre of the bounds); a door mesh `Door_FL` also stands as `Door_FL_shell` where the model has no shell node */
export function nodeInfos(j: GLtf): NodeInfo[] {
  const b = nodeBounds(j), infos: NodeInfo[] = [];
  const flip = (mn: V3, mx: V3): { min: V3; max: V3 } => ({ min: [mn[0], mn[1], -mx[2]], max: [mx[0], mx[1], -mn[2]] });
  const names = new Set(j.nodes.map((n) => n.name));
  j.nodes.forEach((n, i) => {
    const nm = n.name; if (!nm || (b[i]!.min[0] === 0 && b[i]!.max[0] === 0 && b[i]!.min[1] === 0 && b[i]!.max[1] === 0)) return;
    const f = flip(b[i]!.min, b[i]!.max), info: NodeInfo = { name: nm, min: f.min, max: f.max };
    if (/^Wheel_[FR][LR]$/.test(nm)) info.origin = [(f.min[0] + f.max[0]) / 2, (f.min[1] + f.max[1]) / 2, (f.min[2] + f.max[2]) / 2];
    infos.push(info);
    if (/^Door_[FR][LR]$/.test(nm) && !names.has(nm + '_shell')) infos.push({ ...info, name: nm + '_shell' });
  });
  return infos;
}

/** overall bounds of the model (all nodes) in the game's frame */
export function modelBounds(j: GLtf): { min: V3; max: V3 } {
  const b = nodeBounds(j); const mn: V3 = [1e9, 1e9, 1e9], mx: V3 = [-1e9, -1e9, -1e9];
  for (const r of j.scenes?.[0]?.nodes ?? []) { const x = b[r]!; if (x.max[0] === x.min[0] && x.max[1] === x.min[1]) continue; for (let d = 0; d < 3; d++) { mn[d] = Math.min(mn[d]!, x.min[d]!); mx[d] = Math.max(mx[d]!, x.max[d]!); } }
  return { min: [mn[0], mn[1], -mx[2]], max: [mx[0], mx[1], -mn[2]] };
}
export type { GLtf, GNode };
