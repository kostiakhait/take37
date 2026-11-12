// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// The set read off the art files, by node name: colliders, destructible props, parking slots, spawns, the gas station parts with their extras. Pure data (no Babylon).
// Game frame: x along the street, y up, z across; the glTF's z is mirrored (the player lane is z = -1.7, the oncoming lane z = +1.7).
import { glbJson, nodeBounds, type GLtf } from './glbinfo';

export type V3 = [number, number, number];
export interface Box { min: V3; max: V3 }
export type PropClass = 'knock' | 'anchored';
export interface PropDef { id: string; kind: string; mass: number; box: Box; cls: PropClass }
export interface StationPart {
  id: string; box: Box; mass: number; role: string;
  destructible: boolean; burnable: boolean; explosive: boolean; fuelL: number; supports?: string; lit: boolean;
}
export interface ParkSlot { id: string; x: number; z: number; dir: 1 | -1 }
export interface Layout {
  statics: Box[];
  props: PropDef[];
  slots: ParkSlot[];
  spawns: { pursuit: V3; player: V3 };
  station: { parts: StationPart[]; fireAnchors: V3[]; fireNodes: { id: string; at: V3 }[]; lot: Box; origin: V3 };
  /** road surface: |z| under this is the road, up to `walkTo` the sidewalk (m) */
  road: { half: number; walkTo: number; walkH: number };
}

const ANCHORED = new Set(['Hydrant', 'UtilityPole', 'LampAcorn', 'TrafficLight', 'PhoneBooth', 'Meter', 'Mailbox']);
const tp = (m: number[], p: V3): V3 => [m[0]! * p[0] + m[4]! * p[1] + m[8]! * p[2] + m[12]!, m[1]! * p[0] + m[5]! * p[1] + m[9]! * p[2] + m[13]!, m[2]! * p[0] + m[6]! * p[1] + m[10]! * p[2] + m[14]!];
/** a glTF-frame box through a matrix, into the game frame (z mirrored) */
function toGame(min: V3, max: V3, m?: number[]): Box {
  const mn: V3 = [1e9, 1e9, 1e9], mx: V3 = [-1e9, -1e9, -1e9];
  for (let c = 0; c < 8; c++) {
    let p: V3 = [c & 1 ? max[0] : min[0], c & 2 ? max[1] : min[1], c & 4 ? max[2] : min[2]];
    if (m) p = tp(m, p);
    for (let d = 0; d < 3; d++) { mn[d] = Math.min(mn[d]!, d === 2 ? -p[2] : p[d]!); mx[d] = Math.max(mx[d]!, d === 2 ? -p[2] : p[d]!); }
  }
  return { min: mn, max: mx };
}
const has = (b: { min: V3; max: V3 }) => b.max[0] > b.min[0] || b.max[1] > b.min[1] || b.max[2] > b.min[2];

/** a pole with an arm over the road is a pole: the solid part is the base at the kerb end of the box (the arm is overhead) */
function baseBox(b: Box, kind: string): Box {
  if (!/^(TrafficLight|LampAcorn|UtilityPole)$/.test(kind)) return b;
  const out: Box = { min: [...b.min] as V3, max: [...b.max] as V3 };
  for (const d of [0, 2] as const) if (b.max[d] - b.min[d] > 1.4) { const far = Math.abs(b.max[d]) > Math.abs(b.min[d]); if (far) out.min[d] = b.max[d] - 0.7; else out.max[d] = b.min[d] + 0.7; }
  out.max[1] = Math.min(out.max[1], 4);
  return out;
}

/** the station is moved along the street so that its 68.5 m lot sits in the 67 m gap between the two buildings (centre of the gap): the overlap with each is 0.75 m of empty apron instead of 2.5 m on one side */
export const STATION_SHIFT_X = 2.5;

export function readLayout(street: GLtf, colliders: GLtf, gas: GLtf): Layout {
  // colliders: the buildings (walls the cars hit); the sidewalks are ground
  const cb = nodeBounds(colliders);
  const statics: Box[] = [];
  colliders.nodes.forEach((n, i) => { if (n.name && /^COL_Bld/.test(n.name) && has(cb[i]!)) statics.push(toGame(cb[i]!.min, cb[i]!.max)); });

  const sb = nodeBounds(street);
  const props: PropDef[] = [], slots: ParkSlot[] = [];
  let anchorM: number[] | undefined, pursuit: V3 = [12, 0, -1.7], player: V3 = [30, 0, -1.7];
  street.nodes.forEach((n, i) => {
    const nm = n.name ?? '';
    const ex = n.extras as { kind?: string; mass_kg?: number; heading?: string } | undefined;
    if (/^DEST_[A-Za-z]+_\d+$/.test(nm) && ex?.kind && has(sb[i]!)) props.push({ id: nm, kind: ex.kind, mass: ex.mass_kg ?? 30, box: baseBox(toGame(sb[i]!.min, sb[i]!.max), ex.kind), cls: ANCHORED.has(ex.kind) ? 'anchored' : 'knock' });
    else if (/^PARK_[LR]_\d+$/.test(nm)) { const w = sb[i]!.world; slots.push({ id: nm, x: w[12]!, z: -w[14]!, dir: ex?.heading === '-X' ? -1 : 1 }); }
    else if (nm === 'GasStation_Anchor') anchorM = sb[i]!.world;
    else if (nm === 'SPAWN_Pursuit') { const w = sb[i]!.world; pursuit = [w[12]!, 0, -w[14]!]; }
    else if (nm === 'SPAWN_Player') { const w = sb[i]!.world; player = [w[12]!, 0, -w[14]!]; }
  });

  // the station: every node of the file in the street frame through the anchor
  const gb = nodeBounds(gas), parts: StationPart[] = [], fireAnchors: V3[] = [], fireNodes: { id: string; at: V3 }[] = [];
  // the station lies BEHIND the sidewalk on the player's side: the file's +x (street edge to the shop) runs away from the road, which the anchor's own rotation does not do, so the game turns it (render in MOCKUPS.md)
  const a0 = anchorM ?? [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 562, 0, 9.3, 1];
  const am = [0, 0, 1, 0, 0, 1, 0, 0, -1, 0, 0, 0, a0[12]! + STATION_SHIFT_X, a0[13]!, a0[14]!, 1];
  let lot: Box = { min: [528, 0, -50], max: [596, 10, 0] };
  gas.nodes.forEach((n, i) => {
    const nm = n.name ?? '', ex = (n.extras ?? {}) as Record<string, unknown>;
    if (/^Fire_Anchor_\d+$/.test(nm)) { const w = gb[i]!.world; const p = tp(am, [w[12]!, w[13]!, w[14]!]); fireAnchors.push([p[0], p[1], -p[2]]); }
    else if (/^Fire_Pump_\d+_(top|hose)$/.test(nm)) { const w = gb[i]!.world; const p = tp(am, [w[12]!, w[13]!, w[14]!]); fireNodes.push({ id: nm, at: [p[0], p[1], -p[2]] }); }
    else if (nm === 'GasStation' && has(gb[i]!)) lot = toGame(gb[i]!.min, gb[i]!.max, am);
    else if (ex.destructible && has(gb[i]!)) parts.push({ id: nm, box: toGame(gb[i]!.min, gb[i]!.max, am), mass: +(ex.mass_kg ?? 50), role: String(ex.role ?? ''), destructible: true, burnable: !!ex.burnable, explosive: !!ex.explosive, fuelL: +(ex.fuel_l ?? 0), supports: ex.supports as string | undefined, lit: !!ex.lit });
  });
  const org = tp(am, [0, 0, 0]);
  return { statics, props, slots, spawns: { pursuit, player }, station: { parts, fireAnchors, fireNodes, lot, origin: [org[0], org[1], -org[2]] }, road: { half: 6.0, walkTo: 9.3, walkH: 0.15 } };
}

export function parseLayout(streetBuf: ArrayBuffer, colliderBuf: ArrayBuffer, gasBuf: ArrayBuffer): Layout {
  return readLayout(glbJson(streetBuf), glbJson(colliderBuf), glbJson(gasBuf));
}
