// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
import type { WindField } from './wind-sway';

/**
 * Litter driven by the wind: sheets of paper, bags, dry leaves and cups lying on the road and the verge, lifted and carried by the gusts of the wind field, tumbling and settling again.
 * A few hundred pieces live in a ring round the camera (thin instances of one bent sheet); what leaves the ring is born again on the upwind side, so there is always litter where the
 * eye is. Each piece falls under gravity, is dragged towards the air's velocity by its own area-to-mass ratio, lifts in a gust that passes its threshold, bounces and drags on the ground.
 */
interface Piece { x: number; y: number; z: number; vx: number; vy: number; vz: number; yaw: number; pitch: number; roll: number; spin: number; size: number; drag: number; lift: number; seed: number; air: boolean; tone: number }

export interface LitterOptions { count?: number; radius?: number; ground: (x: number, z: number) => number; seed?: number }

const hash = (a: number, b: number) => { let x = (a * 374761393 + b * 668265263) | 0; x = (x ^ (x >>> 13)) * 1274126177 | 0; return ((x ^ (x >>> 16)) >>> 0) / 4294967296; };

export class Litter {
  readonly mesh: BABYLON.Mesh;
  private pieces: Piece[] = [];
  private matrices: Float32Array;
  private colors: Float32Array;
  private n: number; private radius: number;
  private ground: (x: number, z: number) => number;
  private tick = 0;
  /** how many pieces are in the air now */
  airborne = 0;

  constructor(private scene: BABYLON.Scene, private field: WindField, o: LitterOptions) {
    this.n = o.count ?? 260; this.radius = o.radius ?? 55; this.ground = o.ground;
    // a sheet bent along its middle, so that it catches the air and lies in a curve
    const pos = [-0.5, 0, -0.5, 0, 0.05, -0.5, 0.5, 0, -0.5, -0.5, 0, 0.5, 0, 0.05, 0.5, 0.5, 0, 0.5], idx = [0, 3, 1, 1, 3, 4, 1, 4, 2, 2, 4, 5], uv = [0, 0, 0.5, 0, 1, 0, 0, 1, 0.5, 1, 1, 1];
    const m = new BABYLON.Mesh('litter', scene), vd = new BABYLON.VertexData(), nrm: number[] = []; vd.positions = pos; vd.indices = idx; vd.uvs = uv; BABYLON.VertexData.ComputeNormals(pos, idx, nrm); vd.normals = nrm; vd.applyToMesh(m);
    const tex = new BABYLON.DynamicTexture('litter-tex', { width: 128, height: 128 }, scene, true), ctx = tex.getContext() as unknown as CanvasRenderingContext2D;
    ctx.fillStyle = '#e8e2d2'; ctx.fillRect(0, 0, 128, 128);
    for (let i = 0; i < 12; i++) { ctx.fillStyle = `rgba(60,55,50,${0.25 + 0.2 * hash(i, 1)})`; ctx.fillRect(10, 10 + i * 9.5, 40 + hash(i, 2) * 70, 3); }    // lines of print
    ctx.strokeStyle = 'rgba(90,80,70,0.35)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(0, 64); ctx.lineTo(128, 70); ctx.stroke();                          // a fold
    tex.update();
    const mat = new BABYLON.StandardMaterial('litter', scene); mat.diffuseTexture = tex; mat.specularColor = new BABYLON.Color3(0.05, 0.05, 0.05); mat.backFaceCulling = false; mat.twoSidedLighting = true;
    m.material = mat; m.isPickable = false; m.alwaysSelectAsActiveMesh = true; m.receiveShadows = false;
    this.mesh = m;
    this.matrices = new Float32Array(this.n * 16); this.colors = new Float32Array(this.n * 4);
    for (let i = 0; i < this.n; i++) this.pieces.push(this.born(i, 0, 0, true));
    this.mesh.thinInstanceSetBuffer('matrix', this.matrices, 16, false); this.mesh.thinInstanceSetBuffer('color', this.colors, 4, false);
  }

  private born(i: number, cx: number, cz: number, anywhere: boolean, upwind?: [number, number]): Piece {
    const s = ++this.tick * 7 + i, R = this.radius, a = hash(s, 1) * 6.283, r = Math.sqrt(hash(s, 2)) * R;
    let x = cx + Math.cos(a) * r, z = cz + Math.sin(a) * r;
    if (!anywhere && upwind) { x = cx + upwind[0] * R * 0.95 + (hash(s, 3) - 0.5) * R * 1.2 * -upwind[1]; z = cz + upwind[1] * R * 0.95 + (hash(s, 3) - 0.5) * R * 1.2 * upwind[0]; }
    const kind = hash(s, 4);
    // 0 paper, 1 bag, 2 leaf, 3 cup: size, drag (m2 per kg over g), gust threshold
    const size = kind < 0.5 ? 0.18 + 0.12 * hash(s, 5) : kind < 0.75 ? 0.3 + 0.2 * hash(s, 5) : kind < 0.93 ? 0.07 + 0.05 * hash(s, 5) : 0.09;
    const drag = kind < 0.5 ? 2.2 : kind < 0.75 ? 3.2 : kind < 0.93 ? 1.8 : 0.5, lift = kind < 0.5 ? 5.5 : kind < 0.75 ? 4.5 : kind < 0.93 ? 6.5 : 9;
    return { x, y: this.ground(x, z) + 0.02, z, vx: 0, vy: 0, vz: 0, yaw: hash(s, 6) * 6.283, pitch: 0, roll: 0, spin: 0, size, drag, lift, seed: s, air: false, tone: kind };
  }

  /** advance by dt seconds about the camera at (cx, cz) */
  update(dt: number, cx: number, cz: number) {
    if (dt <= 0) return;
    const f = this.field.u, dirX = f.dirX, dirZ = f.dirZ, R = this.radius;
    let air = 0;
    for (let i = 0; i < this.n; i++) {
      let p = this.pieces[i];
      if (Math.hypot(p.x - cx, p.z - cz) > R * 1.15) { p = this.pieces[i] = this.born(i, cx, cz, false, [-dirX, -dirZ]); }
      const sp = this.field.speedAt(p.x, p.z), gy = this.ground(p.x, p.z);
      // the air: the wind at the height of the piece, a little turbulent
      const h = Math.max(0.05, p.y - gy), prof = Math.pow(Math.max(h, 0.3) / 10, 0.16) * 1.15, ua = sp * prof;
      const tur = Math.sin(f.time * 3.1 + p.seed) * 0.25 + Math.sin(f.time * 7.7 + p.seed * 1.3) * 0.15;
      const ax = dirX * ua + -dirZ * ua * tur * 0.5, az = dirZ * ua + dirX * ua * tur * 0.5;
      const onGround = h < 0.06;
      if (onGround && !p.air) {
        // on the ground: friction holds it until a gust passes the threshold, then it slides and may lift
        if (sp > p.lift * (0.8 + 0.4 * hash(p.seed, 9)) && hash(Math.floor(f.time * 4), p.seed) < 0.16 + 0.1 * (sp - p.lift)) { p.air = true; p.vy = 0.8 + 0.4 * sp * hash(p.seed, 10); }
        else { const slide = Math.max(0, ua - p.lift * 0.6) * 0.18; p.vx += (dirX * slide - p.vx) * Math.min(1, dt * 4); p.vz += (dirZ * slide - p.vz) * Math.min(1, dt * 4); p.x += p.vx * dt; p.z += p.vz * dt; p.y = this.ground(p.x, p.z) + 0.02; p.spin *= 0.9; p.yaw += p.spin * dt; p.pitch *= 0.9; p.roll *= 0.9; this.put(i, p, false); continue; }
      }
      if (p.air || !onGround) {
        const k = p.drag * Math.min(1, dt * 1.6);
        p.vx += (ax - p.vx) * k; p.vz += (az - p.vz) * k;
        p.vy += -9.81 * dt * 0.35 + (ua > p.lift ? (ua - p.lift) * 0.55 * dt * (0.5 + 0.5 * Math.sin(f.time * 2.3 + p.seed)) : 0);
        p.vy *= 1 - Math.min(1, dt * 0.8);
        p.x += p.vx * dt; p.y += p.vy * dt; p.z += p.vz * dt;
        p.spin = (Math.hypot(p.vx, p.vz) * 1.4 + 2) * (hash(p.seed, 11) < 0.5 ? 1 : -1); p.yaw += p.spin * dt * 0.5; p.pitch = Math.sin(f.time * 4 + p.seed) * 0.8; p.roll = Math.cos(f.time * 5 + p.seed * 2) * 0.9;
        const g2 = this.ground(p.x, p.z);
        if (p.y <= g2 + 0.02) { p.y = g2 + 0.02; if (p.vy < -1.5) p.vy = -p.vy * 0.3; else { p.vy = 0; p.air = false; } p.vx *= 0.6; p.vz *= 0.6; }
        air++;
      }
      this.put(i, p, true);
    }
    this.airborne = air;
    this.mesh.thinInstanceBufferUpdated('matrix');
  }

  private put(i: number, p: Piece, air: boolean) {
    const q = BABYLON.Quaternion.RotationYawPitchRoll(p.yaw, air ? p.pitch : p.pitch * 0.3, air ? p.roll : p.roll * 0.3);
    const m = BABYLON.Matrix.Compose(new BABYLON.Vector3(p.size, p.size, p.size), q, new BABYLON.Vector3(p.x, p.y, p.z));
    m.copyToArray(this.matrices, i * 16);
    const t = p.tone, o = i * 4;
    if (t < 0.5) { const v = 0.82 + 0.18 * hash(p.seed, 20); this.colors[o] = v; this.colors[o + 1] = v * 0.98; this.colors[o + 2] = v * 0.92; }
    else if (t < 0.75) { const v = 0.55 + 0.4 * hash(p.seed, 21); this.colors[o] = v * 0.8; this.colors[o + 1] = v * 0.85; this.colors[o + 2] = v; }
    else if (t < 0.93) { this.colors[o] = 0.58; this.colors[o + 1] = 0.4; this.colors[o + 2] = 0.2; }
    else { this.colors[o] = 0.85; this.colors[o + 1] = 0.85; this.colors[o + 2] = 0.82; }
    this.colors[o + 3] = 1;
  }
}
