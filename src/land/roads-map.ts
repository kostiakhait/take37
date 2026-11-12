// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import { DIRT_ROADS } from './relief';

/**
 * The dirt roads as a picture of the land from above (a texture the terrain shader reads by world position): the chunks of the far land are too coarse to carry a road in their vertex
 * colours, a picture 1.1 m to the texel carries it to the horizon. Red is the road (soft at the edge), green the worn middle where the wheels run.
 */
export const ROADS_BOX = { x0: -2100, z0: -1300, w: 4600, h: 2900 };

export function roadsTexture(scene: BABYLON.Scene): BABYLON.DynamicTexture {
  const W = 4096, H = Math.round(W * ROADS_BOX.h / ROADS_BOX.w), tex = new BABYLON.DynamicTexture('roads-map', { width: W, height: H }, scene, true);
  const g = tex.getContext() as unknown as CanvasRenderingContext2D, px = W / ROADS_BOX.w;
  g.fillStyle = '#000'; g.fillRect(0, 0, W, H);
  g.lineCap = 'round'; g.lineJoin = 'round';
  const path = (pts: Array<[number, number]>) => { g.beginPath(); pts.forEach(([x, z], i) => { const u = (x - ROADS_BOX.x0) * px, v = H - (z - ROADS_BOX.z0) * px; if (i) g.lineTo(u, v); else g.moveTo(u, v); }); g.stroke(); };
  for (const r of DIRT_ROADS) {
    // the edge: wide and soft, then the bed, then the worn middle
    g.strokeStyle = 'rgb(110,0,0)'; g.lineWidth = (r.width * 1.5) * px; path(r.points);
    g.strokeStyle = 'rgb(255,0,0)'; g.lineWidth = r.width * px; path(r.points);
    g.strokeStyle = 'rgb(255,255,0)'; g.lineWidth = r.width * 0.45 * px; path(r.points);
  }
  tex.wrapU = tex.wrapV = BABYLON.Texture.CLAMP_ADDRESSMODE;
  tex.update(true);
  return tex;
}
