// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import type { WindField } from './wind-sway';

/**
 * Flags on poles. A flag is a cloth of a grid of vertices: it turns about its pole to lie downwind (with the inertia of cloth), hangs limp in a calm, and in a wind streams out with a
 * travelling wave whose amplitude grows from the hoist to the fly and with the speed of the wind, the wavelength shortening as it freshens; gusts snap it. The wind is the field's.
 */
export interface FlagSpec { x: number; z: number; ground: number; pole: number; w: number; h: number; texture?: BABYLON.Texture }

const COLS = 22, ROWS = 12;

export function stripesTexture(scene: BABYLON.Scene): BABYLON.DynamicTexture {
  // a flag of thirteen stripes and a blue field of fifty stars, drawn as a texture
  const tex = new BABYLON.DynamicTexture('flag', { width: 512, height: 270 }, scene, true), c = tex.getContext() as unknown as CanvasRenderingContext2D;
  const H = 270, W = 512, sh = H / 13;
  for (let i = 0; i < 13; i++) { c.fillStyle = i % 2 === 0 ? '#b22234' : '#f4f1ec'; c.fillRect(0, i * sh, W, sh + 1); }
  c.fillStyle = '#3c3b6e'; c.fillRect(0, 0, W * 0.4, sh * 7);
  c.fillStyle = '#f4f1ec';
  for (let r = 0; r < 9; r++) for (let k = 0; k < (r % 2 === 0 ? 6 : 5); k++) { const x = W * 0.4 * ((k + (r % 2 === 0 ? 0.5 : 1)) / 6.0), y = sh * 7 * ((r + 0.7) / 9.4); c.beginPath(); c.arc(x, y, 3.2, 0, 6.283); c.fill(); }
  tex.update(); return tex;
}

export class Flag {
  readonly mesh: BABYLON.Mesh;
  readonly pole: BABYLON.Mesh;
  private pos: Float32Array;
  private heading = 0;
  private phase: number;
  constructor(private scene: BABYLON.Scene, private field: WindField, readonly spec: FlagSpec, mat: BABYLON.Material, poleMat: BABYLON.Material) {
    this.phase = (spec.x * 0.13 + spec.z * 0.29) % 6.283;
    const n = (COLS + 1) * (ROWS + 1);
    this.pos = new Float32Array(n * 3);
    const uv: number[] = [], idx: number[] = [];
    for (let j = 0; j <= ROWS; j++) for (let i = 0; i <= COLS; i++) uv.push(i / COLS, 1 - j / ROWS);
    for (let j = 0; j < ROWS; j++) for (let i = 0; i < COLS; i++) { const a = j * (COLS + 1) + i; idx.push(a, a + 1, a + COLS + 1, a + 1, a + COLS + 2, a + COLS + 1); }
    const m = new BABYLON.Mesh('flag', scene), vd = new BABYLON.VertexData(); vd.positions = Array.from(this.pos); vd.indices = idx; vd.uvs = uv; vd.normals = new Array(n * 3).fill(0); vd.applyToMesh(m, true);
    m.material = mat; m.isPickable = false; m.alwaysSelectAsActiveMesh = true; this.mesh = m;
    const p = BABYLON.MeshBuilder.CreateCylinder('flagpole', { height: spec.pole, diameterTop: 0.07, diameterBottom: 0.13, tessellation: 10 }, scene);
    p.position.set(spec.x, spec.ground + spec.pole / 2, spec.z); p.material = poleMat; p.isPickable = false; this.pole = p;
    const ball = BABYLON.MeshBuilder.CreateSphere('flagball', { diameter: 0.18, segments: 8 }, scene); ball.position.set(spec.x, spec.ground + spec.pole + 0.08, spec.z); ball.material = poleMat; ball.isPickable = false; ball.parent = null;
    this.update(0);
  }
  update(dt: number) {
    const f = this.field.u, s = this.spec, sp = this.field.speedAt(s.x, s.z) * 1.1, t = f.time;
    // turn to lie downwind; slow in a calm
    const target = Math.atan2(f.dirZ, f.dirX);
    let d = target - this.heading; d = Math.atan2(Math.sin(d), Math.cos(d));
    const k = Math.min(1, dt * (0.6 + 0.35 * sp)); this.heading += d * (sp < 0.8 ? k * 0.2 : k);
    const stream = Math.min(1, sp / 7), len = s.w, hh = s.h, top = s.ground + s.pole - 0.2, ch = Math.cos(this.heading), sh = Math.sin(this.heading);
    const wl = Math.max(0.6, 3.2 / (1 + sp * 0.28)), omega = 2.5 + sp * 0.9, amp = 0.05 + 0.2 * Math.min(1, sp / 9) * (1 + 0.3 * Math.sin(t * 1.7 + this.phase));
    for (let j = 0; j <= ROWS; j++) for (let i = 0; i <= COLS; i++) {
      const u = i / COLS, v = j / ROWS, o = (j * (COLS + 1) + i) * 3;
      // the cloth along the wind: when limp it hangs down from the hoist, when the wind blows it streams out horizontally
      const out = len * u * stream * 0.98 + len * u * (1 - stream) * 0.12;
      const hang = (1 - stream) * len * u * u * 0.55;
      const wave = Math.sin((u * len) / wl * 6.283 - t * omega + v * 1.2 + this.phase) * amp * Math.min(1, u * 1.8) * len * 0.3 * (0.3 + 0.7 * stream);
      const flutterV = Math.sin(t * 7.3 + u * 9 + v * 3 + this.phase) * 0.015 * u * Math.min(1, sp / 6);
      const lx = out, ly = -v * hh - hang + flutterV, lz = wave;
      // local x along the wind heading, z across it
      this.pos[o] = s.x + lx * ch - lz * sh; this.pos[o + 1] = top + ly; this.pos[o + 2] = s.z + lx * sh + lz * ch;
    }
    this.mesh.updateVerticesData(BABYLON.VertexBuffer.PositionKind, this.pos, false, false);
    const nrm: number[] = []; BABYLON.VertexData.ComputeNormals(this.pos, this.mesh.getIndices()!, nrm); this.mesh.updateVerticesData(BABYLON.VertexBuffer.NormalKind, nrm, false, false);
    this.mesh.refreshBoundingInfo();
  }
}
