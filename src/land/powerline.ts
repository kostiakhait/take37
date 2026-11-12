// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026

/**
 * Power lines over the hills, made in code: lattice pylons of a high-voltage line far from the set, and wooden pole lines that follow the dirt roads. The wires hang as catenaries between
 * the arms and carry the u coordinate along their length, which the wind sway reads (a wire moves most in the middle of the span and not at the insulator).
 */
export interface LineSpec {
  kind: 'pylon' | 'wood';
  /** the route (x, z), metres; supports stand every `span` metres along it */
  route: Array<[number, number]>;
  span: number;
}
export interface PowerLines { poles: BABYLON.Mesh; wires: BABYLON.Mesh[]; towers: Array<{ x: number; z: number; yaw: number; kind: LineSpec['kind'] }> }

class Soup {
  pos: number[] = []; idx: number[] = [];
  /** a thin square-section beam from p to q */
  beam(p: number[], q: number[], t: number) {
    const dx = q[0] - p[0], dy = q[1] - p[1], dz = q[2] - p[2], l = Math.hypot(dx, dy, dz) || 1, ux = dx / l, uy = dy / l, uz = dz / l;
    let ax = 0, ay = 1, az = 0; if (Math.abs(uy) > 0.9) { ax = 1; ay = 0; }
    let bx = uy * az - uz * ay, by = uz * ax - ux * az, bz = ux * ay - uy * ax; const bl = Math.hypot(bx, by, bz) || 1; bx /= bl; by /= bl; bz /= bl;
    const cx = by * uz - bz * uy, cy = bz * ux - bx * uz, cz = bx * uy - by * ux, base = this.pos.length / 3;
    for (const [s, k] of [[-1, -1], [1, -1], [1, 1], [-1, 1]] as const) {
      const ox = (bx * s + cx * k) * t, oy = (by * s + cy * k) * t, oz = (bz * s + cz * k) * t;
      this.pos.push(p[0] + ox, p[1] + oy, p[2] + oz, q[0] + ox, q[1] + oy, q[2] + oz);
    }
    for (let i = 0; i < 4; i++) { const a = base + i * 2, b = base + ((i + 1) % 4) * 2; this.idx.push(a, a + 1, b, b, a + 1, b + 1); }
  }
}

/** a lattice pylon of height h (m), in its own frame: x across the line, z along it; three arms with two conductors each; returns the soup and the attach points of the conductors */
function pylon(h: number): { soup: Soup; arms: number[][] } {
  const s = new Soup(), w0 = h * 0.17, w1 = h * 0.045, sections = [0, 0.3, 0.55, 0.75, 0.9, 1.0];
  const half = (y: number) => w0 + (w1 - w0) * Math.min(1, y / (h * 0.9));
  const leg = (sx: number, sz: number, y: number) => [sx * half(y), y, sz * half(y)];
  for (const [sx, sz] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) for (let i = 0; i < sections.length - 1; i++) s.beam(leg(sx, sz, sections[i] * h), leg(sx, sz, sections[i + 1] * h), 0.16);
  for (let i = 0; i < sections.length - 1; i++) {
    const y0 = sections[i] * h, y1 = sections[i + 1] * h;
    for (const [a, b] of [[[-1, -1], [1, -1]], [[1, -1], [1, 1]], [[1, 1], [-1, 1]], [[-1, 1], [-1, -1]]]) {
      s.beam(leg(a[0], a[1], y0), leg(b[0], b[1], y1), 0.07); s.beam(leg(b[0], b[1], y0), leg(a[0], a[1], y1), 0.07);
      s.beam(leg(a[0], a[1], y1), leg(b[0], b[1], y1), 0.08);
    }
  }
  const arms: number[][] = [];
  for (const [yy, reach] of [[0.62, 0.34], [0.78, 0.3], [0.93, 0.26]]) {
    const y = yy * h, r = reach * h, hf = half(y);
    s.beam([-r, y, 0], [r, y, 0], 0.11); s.beam([-r, y, 0], [-hf, y - h * 0.05, hf], 0.06); s.beam([r, y, 0], [hf, y - h * 0.05, hf], 0.06); s.beam([-r, y, 0], [-hf, y - h * 0.05, -hf], 0.06); s.beam([r, y, 0], [hf, y - h * 0.05, -hf], 0.06);
    for (const side of [-1, 1]) { s.beam([side * r, y, 0], [side * r, y - 2.4, 0], 0.1); arms.push([side * r, y - 2.6, 0]); }       // the insulator string
  }
  s.beam([0, h * 0.96, 0], [0, h * 1.07, 0], 0.07);                                                                                    // the shield wire's peak
  return { soup: s, arms };
}

/** a wooden pole of height h with a crossarm and three insulators */
function wood(h: number): { soup: Soup; arms: number[][] } {
  const s = new Soup();
  s.beam([0, 0, 0], [0, h, 0], 0.15); s.beam([-1.15, h - 0.4, 0], [1.15, h - 0.4, 0], 0.07); s.beam([-0.6, h - 1.2, 0], [-0.05, h - 0.4, 0], 0.04); s.beam([0.6, h - 1.2, 0], [0.05, h - 0.4, 0], 0.04);
  const arms = [[-1.0, h - 0.2, 0], [0, h + 0.15, 0], [1.0, h - 0.2, 0]];
  for (const a of arms) s.beam([a[0], a[1] - 0.2, 0], [a[0], a[1] + 0.05, 0], 0.05);
  return { soup: s, arms };
}

/**
 * Builds the lines: one steel mesh of every pole (the soups merged, placed on the ground and turned to the line), and one wire mesh per line. `ground` is the landscape's height query.
 */
export function buildPowerLines(scene: BABYLON.Scene, specs: LineSpec[], ground: (x: number, z: number) => number, mats: { steel: BABYLON.Material; wood: BABYLON.Material; wire: BABYLON.Material }): PowerLines {
  const towers: PowerLines['towers'] = [], wires: BABYLON.Mesh[] = [];
  const steel = new Soup(), wooden = new Soup();
  for (const spec of specs) {
    // supports at equal spans along the route
    const pts: Array<[number, number, number]> = [];
    let carry = 0;
    for (let i = 0; i + 1 < spec.route.length; i++) {
      const [ax, az] = spec.route[i], [bx, bz] = spec.route[i + 1], len = Math.hypot(bx - ax, bz - az);
      for (let d = carry; d < len; d += spec.span) pts.push([ax + (bx - ax) * d / len, az + (bz - az) * d / len, Math.atan2(bz - az, bx - ax)]);
      carry = ((len - carry) % spec.span) === 0 ? 0 : spec.span - ((len - carry) % spec.span);
    }
    const last = spec.route[spec.route.length - 1]; pts.push([last[0], last[1], pts.length ? pts[pts.length - 1][2] : 0]);
    const h = spec.kind === 'pylon' ? 36 : 10.5, make = spec.kind === 'pylon' ? pylon(h) : wood(h), armsAll: number[][][] = [];
    pts.forEach(([x, z, yaw], i) => {
      // the support's frame: z along the line; yaw turns it to the route's heading (the line's direction at that support is the mean of the two spans)
      const prev = pts[Math.max(0, i - 1)], next = pts[Math.min(pts.length - 1, i + 1)], heading = Math.atan2(next[1] - prev[1], next[0] - prev[0]), y0 = ground(x, z);
      void yaw;
      // local (lx, ly, lz) -> world: x across, z along; rotate by heading about the vertical (z along the heading)
      const c = Math.cos(heading), sn = Math.sin(heading), put = (lx: number, ly: number, lz: number): [number, number, number] => [x + lz * c - lx * sn, y0 + ly, z + lz * sn + lx * c];
      const dst = spec.kind === 'pylon' ? steel : wooden, base = dst.pos.length / 3;
      for (let k = 0; k < make.soup.pos.length; k += 3) { const w = put(make.soup.pos[k], make.soup.pos[k + 1], make.soup.pos[k + 2]); dst.pos.push(w[0], w[1], w[2]); }
      for (const t of make.soup.idx) dst.idx.push(base + t);
      armsAll.push(make.arms.map(a => put(a[0], a[1], a[2])));
      towers.push({ x, z, yaw: heading, kind: spec.kind });
    });
    // the wires: a catenary from each arm of one support to the same arm of the next; the sag is a few per cent of the span
    const groups: Array<{ pos: number[]; uv: number[]; idx: number[] }> = [];
    for (let a = 0; a < armsAll[0].length; a++) {
      for (let i = 0; i + 1 < armsAll.length; i++) {
        const p = armsAll[i][a], q = armsAll[i + 1][a], L = Math.hypot(q[0] - p[0], q[2] - p[2]), sag = Math.max(0.3, L * (spec.kind === 'pylon' ? 0.03 : 0.022)), n = 14, r = spec.kind === 'pylon' ? 0.035 : 0.012;
        if (!groups.length) groups.push({ pos: [], uv: [], idx: [] });
        const g = groups[0], base = g.pos.length / 3;
        for (let k = 0; k <= n; k++) {
          const u = k / n, x = p[0] + (q[0] - p[0]) * u, z = p[2] + (q[2] - p[2]) * u, y = p[1] + (q[1] - p[1]) * u - 4 * sag * u * (1 - u);
          for (let s = 0; s < 4; s++) { const an = s * Math.PI / 2; g.pos.push(x + Math.cos(an) * r * 0, y + Math.cos(an) * r, z + Math.sin(an) * r); g.uv.push(u, 0); }
        }
        for (let k = 0; k < n; k++) for (let s = 0; s < 4; s++) { const a0 = base + k * 4 + s, b0 = base + k * 4 + (s + 1) % 4, a1 = a0 + 4, b1 = b0 + 4; g.idx.push(a0, a1, b0, b0, a1, b1); }
      }
    }
    for (const g of groups) {
      const m = new BABYLON.Mesh(`wires-${spec.kind}`, scene), vd = new BABYLON.VertexData(); vd.positions = g.pos; vd.indices = g.idx; vd.uvs = g.uv;
      const nrm: number[] = []; BABYLON.VertexData.ComputeNormals(g.pos, g.idx, nrm); vd.normals = nrm; vd.applyToMesh(m);
      m.material = mats.wire; m.isPickable = false; m.alwaysSelectAsActiveMesh = true; wires.push(m);
    }
  }
  const poles = new BABYLON.Mesh('poles', scene);
  const build = (soup: Soup, mat: BABYLON.Material, name: string) => {
    if (!soup.pos.length) return null;
    const m = new BABYLON.Mesh(name, scene), vd = new BABYLON.VertexData(), nrm: number[] = [];
    vd.positions = soup.pos; vd.indices = soup.idx; BABYLON.VertexData.ComputeNormals(soup.pos, soup.idx, nrm); vd.normals = nrm; vd.applyToMesh(m); m.material = mat; m.isPickable = false; m.alwaysSelectAsActiveMesh = true; return m;
  };
  const a = build(steel, mats.steel, 'pylons'), b = build(wooden, mats.wood, 'wood-poles');
  poles.dispose();
  return { poles: (a ?? b)!, wires, towers };
}
