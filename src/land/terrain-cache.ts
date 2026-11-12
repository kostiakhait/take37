// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import type { TerrainView } from '@ferret/terrain';

/**
 * The land seen from the playable places, kept. The engine's `TerrainView` plans the chunks round one camera, builds three a frame and throws away what the plan has left: from a camera that
 * jumps (a verdict camera, a crane, the cab at the far end of the street) the ground is a heap of holes until the new plan is built. Here every chunk the view builds is kept (hidden, not disposed)
 * and shown again the moment a plan asks for it, and the chunks of the places the game looks from (the cab along the 600 m street, the set cameras, the station, a high crane) are built ahead,
 * in slices while the page loads. Far chunks stay as coarse as the plan makes them; the chunks of the platform itself are few, because the plan is by distance.
 */
export interface Pins { /** builds the next slice of the anchors' chunks within `ms`; true when all are built */ warm(ms: number): boolean; readonly total: number; readonly built: number; /** milliseconds spent in `warm` so far */ readonly ms: number }

/** where the game's camera goes, ordered by when it is needed: the cab start, the set cameras, then along the street, then the station and the ends */
export function anchors(): Array<[number, number]> {
  const a: Array<[number, number]> = [[30, -1.7], [52, 3.4], [200, 7.5], [340, -7.5], [440, 7.8], [506, -5], [606, 6], [560, -30]];
  for (let x = 0; x <= 640; x += 40) for (const z of [-2, 8]) a.push([x, z]);
  a.push([-40, 0], [680, 0], [250, 60], [250, -60]);
  return a;
}

type Live = { mesh: BABYLON.Mesh; chunk: { id: string }; ver: number };
export function pinTerrain(terrain: TerrainView, list: Array<[number, number]> = anchors()): Pins {
  const t = terrain as unknown as { live: Map<string, Live>; planner: { plan(x: number, z: number): Array<{ id: string }> }; update(c: [number, number, number]): unknown; o: { buildsPerUpdate?: number; buildMs?: number } };
  const pins = new Map<string, Live>(), original = t.update.bind(terrain) as (c: [number, number, number]) => ReturnType<TerrainView['update']>;
  /** hidden, not disposed: the engine disposes what its plan has left; a pinned mesh only goes dark */
  const adopt = () => { for (const [id, l] of t.live) if (!pins.has(id)) { pins.set(id, l); const m = l.mesh, real = m.dispose.bind(m); (m as unknown as { realDispose: typeof real }).realDispose = real; m.dispose = () => { m.setEnabled(false); }; } };
  terrain.update = (c) => {
    for (const p of t.planner.plan(c[0], c[2])) { const l = pins.get(p.id); if (l && !t.live.has(p.id)) { l.mesh.setEnabled(true); t.live.set(p.id, l); } }
    const s = original(c); adopt(); return s;
  };
  let next = 0, built = 0, spent = 0;
  const known = new Set<string>(); let total = 0;
  for (const [x, z] of list) for (const p of t.planner.plan(x, z)) if (!known.has(p.id)) { known.add(p.id); total++; }
  return {
    get total() { return total; }, get built() { return pins.size; }, get ms() { return Math.round(spent); },
    warm(ms) {
      const t0 = performance.now();
      while (next < list.length && performance.now() - t0 < ms) {
        const [x, z] = list[next], s = terrain.update([x, 2, z]);
        if (s.pending === 0) next++;
      }
      built = pins.size; void built; spent += performance.now() - t0;
      return next >= list.length;
    },
  };
}
