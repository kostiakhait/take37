// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import { buildWater, type WaterSurfaceView } from '@ferret/levels';
import { seaState } from '@ferret/waves';
import { Sea } from '@airwar/world/sea';
import { lakesLocal } from './height3';

/**
 * The water of the zone: each lake of the Zeppelin landscape is a disc-sized patch of the engine's water (`buildWater`: Gerstner waves in the vertex shader, sky reflection, depth colour, foam) lying at the lake's own level.
 * The patch is wider than the lake; the ground, which lies above the level outside the shore, hides the rest of it. The big lake, the one the airfield looks toward, has waves from the wind; the small ones are calm.
 */
type V3 = [number, number, number];
export class Lakes {
  readonly views: Array<{ view: WaterSurfaceView; x: number; z: number; r: number; level: number }> = [];
  private big: WaterSurfaceView | null = null;
  /** the sea off the eastern coast: the air war sample's own Sea (a Gerstner patch that follows the camera, a flat far plane) */
  readonly sea: Sea;
  constructor(scene: BABYLON.Scene, o: { skyTop: V3; skyHorizon: V3; sunDir: V3; sunColor: V3; clock: () => number; minRadius?: number }) {
    this.sea = new Sea(scene, o);
    for (const l of lakesLocal()) {
      if (l.r < (o.minRadius ?? 800) || l.level < 0) continue;   // the coast's big discs (level < 0) are the sea's, drawn by the airwar Sea
      const w = l.r * 3.0, big = l.r > 3000;
      const view = buildWater(scene, { level: l.level, size: [w, w], absorption: [90, 130, 160], scattering: [0.05, 0.09, 0.1], roughness: 0.05, opacity: 0.97, foam: big ? 0.6 : 0.2, meso: 0.4 } as never,
        { name: 'lake' + this.views.length, skyTop: o.skyTop, skyHorizon: o.skyHorizon, sunDir: [-o.sunDir[0], -o.sunDir[1], -o.sunDir[2]], sunColor: o.sunColor, clock: o.clock });
      { // the patch is a disc, not a square: the triangles of its grid beyond 1.3 r of the lake's centre are dropped (the shore is irregular by +-24 %; beyond it the ground is above the level and hides the rest)
        const m = view.mesh, pos = m.getVerticesData(BABYLON.VertexBuffer.PositionKind), idx = m.getIndices();
        if (pos && idx) { const keep: number[] = [], lim = l.r * 1.3; for (let i = 0; i < idx.length; i += 3) { const a = idx[i]! * 3, b = idx[i + 1]! * 3, c = idx[i + 2]! * 3; if (Math.hypot((pos[a]! + pos[b]! + pos[c]!) / 3, (pos[a + 2]! + pos[b + 2]! + pos[c + 2]!) / 3) <= lim) keep.push(idx[i]!, idx[i + 1]!, idx[i + 2]!); } m.setIndices(keep); }
      }
      view.mesh.position.x = l.x; view.mesh.position.z = l.z; view.mesh.isPickable = false;
      this.views.push({ view, x: l.x, z: l.z, r: l.r, level: l.level }); if (big) this.big = view;
    }
  }
  setWind(speed: number, fromDeg: number) {
    const t = ((fromDeg + 180) * Math.PI) / 180, dir = (Math.atan2(-Math.cos(t), Math.sin(t)) * 180) / Math.PI;
    this.sea.setWind(speed, fromDeg);
    if (this.big) this.big.setWaves(seaState(Math.max(2, speed), dir, { count: 12, seed: 7, spread: 50 }));
    const m = Math.min(1, 0.15 + speed / 14), dx = Math.cos((dir * Math.PI) / 180), dz = Math.sin((dir * Math.PI) / 180);
    for (const v of this.views) { v.view.material.setFloat('meso', m); v.view.material.setVector2('mesoDir', new BABYLON.Vector2(dx, dz)); }
  }
  update(cam: V3) { this.sea.update(cam); }
  setLight(toSun: V3, color: V3) { this.sea.setLight(toSun, color); for (const v of this.views) { v.view.material.setVector3('sunDir', new BABYLON.Vector3(-toSun[0], -toSun[1], -toSun[2])); v.view.material.setColor3('sunColor', new BABYLON.Color3(...color)); } }
  setFog(color: BABYLON.Color3, density: number) { this.sea.setFog(color, density); for (const v of this.views) { v.view.material.setColor3('fogColor', color); v.view.material.setFloat('fogDensity', density); } }
}
