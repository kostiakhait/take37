// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// Scene 1 populated: the player's police car, the villain's Corvette, parked cars along the kerbs, moving traffic in both lanes, the tanker, the gas station's fuel. One call per take; `seed` makes the take's variations.
import type { NodeInfo } from '@ferret/destruction/autoparts';
import { buildRoadCar, buildTanker } from './carspec';
import { Sim, type Car } from './sim';
import { FireWorld } from './fire';
import { trafficDriver, vincentDriver, planVincent, holdLane, type VincentPlan } from './ai';
import { TRAFFIC_KINDS, type KindId } from './config';
import { Rng } from './rng';
import type { Layout } from './layout';

export type KindInfos = Partial<Record<KindId, NodeInfo[]>>;
export interface Scene1 { sim: Sim; fire: FireWorld; player: Car; vincent: Car; tanker: Car; plan: VincentPlan; seed: number }

export function buildScene1(layout: Layout, infos: KindInfos, seed: number, opts: { parkedShare?: number; traffic?: boolean } = {}): Scene1 {
  const rng = new Rng(seed * 7919 + 13), sim = new Sim(layout, seed);
  const fire = new FireWorld(sim);
  const car = (id: string, role: Car['role'], kind: KindId, x: number, z: number, yaw: number) => {
    const b = kind === 'tanker' ? buildTanker(infos.tanker!) : buildRoadCar(kind, infos[kind]!);
    const c = sim.addCar(id, role, b, [x, 0, z], yaw); fire.registerCar(c); return c;
  };
  const player = car('police', 'player', 'police', layout.spawns.pursuit[0], layout.spawns.pursuit[2], 0);
  const vincent = car('vincent', 'vincent', 'corvette', layout.spawns.player[0], layout.spawns.player[2], 0);
  player.occupied = true; vincent.occupied = true;
  const lot = layout.station.lot, pumps = sim.props.filter((p) => /^Pump_/.test(p.id)).map((p) => (p.def.box.min[0] + p.def.box.max[0]) / 2);
  const islandsX = [...new Set(pumps.map((x) => Math.round(x)))].sort((a, b) => a - b);
  const plan = planVincent(rng, { origin: layout.station.origin, lot: { min: lot.min, max: lot.max } });
  vincent.drive = vincentDriver(plan, { islandsX, frontZ: lot.max[2] - 1, backZ: lot.min[2] + 14, exitX: (islandsX[islandsX.length - 1] ?? 576) + 16 });

  // parked: a share of the kerb slots, a car of any kind in each, nose along the slot's direction
  const share = opts.parkedShare ?? 0.5;
  for (const s of layout.slots) {
    if (s.x > lot.min[0] - 8 && s.x < lot.max[0] + 8) continue;
    if (s.x < 8 && Math.abs(s.z) < 6 && s.z < 0) continue;
    if (!rng.chance(share)) continue;
    const kind = rng.pick(TRAFFIC_KINDS);
    car('park:' + s.id, 'parked', kind, s.x + rng.range(-0.3, 0.3), s.z + rng.range(-0.15, 0.15), s.dir === 1 ? 0 : Math.PI);
  }
  // the tanker: rolling slowly to the station and standing in front of its forecourt, in the player's lane (it delivers fuel there), a few metres from the pumps' street edge
  const stopX = layout.station.origin[0] - 8;
  const tanker = car('tanker', 'tanker', 'tanker', stopX - 50, -1.7, 0);
  tanker.drive = (c, sm) => { const x = c.veh.pos[0], v = c.veh.vel[0]; if (c.wrecked) { c.ctl.throttle = 0; c.ctl.brake = 0.3; return; } if (x >= stopX - 0.3 && Math.abs(v) < 1.5) { c.ctl.throttle = 0; c.ctl.brake = 1; return; }   // standing: the brake held (a coasting truck crept 40 m past its place)
    const want = Math.min(6, Math.max(0, (stopX - x) * 0.35)); holdLane(c, -1.7, want); void sm; void v; };
  tanker.occupied = true;
  if (opts.traffic !== false) {
    let x = 75 + rng.range(0, 30), i = 0;
    while (x < 590) { if (Math.abs(x - stopX) > 40) { const k = rng.pick(TRAFFIC_KINDS), c = car('t+' + i++, 'traffic', k, x, -1.7 + rng.range(-0.15, 0.15), 0); c.drive = trafficDriver(1, -1.7, rng.range(9, 13)); c.occupied = true; } x += rng.range(90, 170); }
    x = 40 + rng.range(0, 60); i = 0;
    while (x < 600) { const k = rng.pick(TRAFFIC_KINDS), c = car('t-' + i++, 'traffic', k, x, 1.7 + rng.range(-0.15, 0.15), Math.PI); c.drive = trafficDriver(-1, 1.7, rng.range(8, 13)); c.occupied = true; x += rng.range(230, 420); }
  }
  fire.registerStation();
  return { sim, fire, player, vincent, tanker, plan, seed };
}
