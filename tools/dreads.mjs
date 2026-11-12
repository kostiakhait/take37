// Dreadlocks made from a long straight groom: neighbouring strands are gathered into bundles at the root and every bundle is twisted into one thick rope.
export function dreadlocks(st, { cell = 0.024, radius = 0.0045, turns = 7, M = 28, keep = 0.5 } = {}) {
  let r = 12345; const rnd = () => ((r = (Math.imul(r, 1664525) + 1013904223) >>> 0) / 4294967296)
  const paths = [], off = []; let o = 0
  for (let s = 0; s < st.nS; s++) { off.push(o); o += st.counts[s] }
  const groups = new Map()
  for (let s = 0; s < st.nS; s++) {
    const n = st.counts[s]; if (n < 2) continue
    const p = []; for (let k = 0; k < M; k++) { const t = (k / (M - 1)) * (n - 1), i0 = Math.floor(t), i1 = Math.min(n - 1, i0 + 1), f = t - i0, a = (off[s] + i0) * 3, b = (off[s] + i1) * 3
      p.push([st.pos[a] + (st.pos[b] - st.pos[a]) * f, st.pos[a + 1] + (st.pos[b + 1] - st.pos[a + 1]) * f, st.pos[a + 2] + (st.pos[b + 2] - st.pos[a + 2]) * f]) }
    const key = [Math.floor(p[0][0] / cell), Math.floor(p[0][1] / cell), Math.floor(p[0][2] / cell)].join(',')
    if (!groups.has(key)) groups.set(key, []); groups.get(key).push(p)
  }
  const out = []
  for (const g of groups.values()) {
    if (g.length < 3) continue
    const mean = Array.from({ length: M }, (_, k) => { const m = [0, 0, 0]; for (const p of g) for (let q = 0; q < 3; q++) m[q] += p[k][q] / g.length; return m })
    // the lock hangs and curls a little along its own length: keep the mean, add a slight common sway
    const sway = rnd() * 6.28
    for (let i = 0; i < g.length; i++) {
      if (rnd() > keep + 0.5) continue
      const ph = rnd() * 6.28, rr = radius * (0.35 + 0.65 * rnd()), pts = []
      for (let k = 0; k < M; k++) {
        const a = mean[Math.max(0, k - 1)], b = mean[Math.min(M - 1, k + 1)]; let tx = b[0] - a[0], ty = b[1] - a[1], tz = b[2] - a[2]; const tl = Math.hypot(tx, ty, tz) || 1; tx /= tl; ty /= tl; tz /= tl
        // any perpendicular basis
        let ux = 0, uy = 0, uz = 1; if (Math.abs(tz) > 0.9) { ux = 1; uz = 0 }
        let vx = ty * uz - tz * uy, vy = tz * ux - tx * uz, vz = tx * uy - ty * ux; const vl = Math.hypot(vx, vy, vz) || 1; vx /= vl; vy /= vl; vz /= vl
        ux = vy * tz - vz * ty; uy = vz * tx - vx * tz; uz = vx * ty - vy * tx
        const t = k / (M - 1), th = ph + turns * 6.2832 * t, taper = k > M - 4 ? (M - 1 - k) / 3 : 1, rad = rr * taper + 0.0007
        pts.push([mean[k][0] + rad * (Math.cos(th) * ux + Math.sin(th) * vx) + 0.0025 * Math.sin(sway + 5 * t) * t, mean[k][1] + rad * (Math.cos(th) * uy + Math.sin(th) * vy), mean[k][2] + rad * (Math.cos(th) * uz + Math.sin(th) * vz)])
      }
      out.push(pts)
    }
  }
  const nS = out.length, pos = new Float32Array(nS * M * 3), counts = new Int32Array(nS).fill(M), uv = new Float32Array(nS * 2), width = new Float32Array(nS * M).fill(0.0004)
  out.forEach((p, s) => { p.forEach((v, k) => { pos[(s * M + k) * 3] = v[0]; pos[(s * M + k) * 3 + 1] = v[1]; pos[(s * M + k) * 3 + 2] = v[2] }) })
  return { nS, nV: nS * M, counts, pos, uv, width }
}

/** Round locks: the same bundles as dreadlocks(), but every bundle is ONE smooth tube (round section, rounded tip, slightly irregular), not twisted ribbons.
 *  Returns a mesh for extraMeshes ({pos,nrm,uv,idx}) in head coordinates; dy is the groom's vertical offset (the mesh has no node offset). */
export function dreadTubes(st, { cell = 0.026, radius = 0.0068, M = 30, sides = 9, dy = 0, tipCut = 0.12, sizeJitter = 0.18 } = {}) {
  let r = 777; const rnd = () => ((r = (Math.imul(r, 1664525) + 1013904223) >>> 0) / 4294967296)
  const off = []; let o = 0
  for (let s = 0; s < st.nS; s++) { off.push(o); o += st.counts[s] }
  const groups = new Map()
  for (let s = 0; s < st.nS; s++) {
    const n = st.counts[s]; if (n < 2) continue
    const p = []; for (let k = 0; k < M; k++) { const t = (k / (M - 1)) * (n - 1), i0 = Math.floor(t), i1 = Math.min(n - 1, i0 + 1), f = t - i0, a = (off[s] + i0) * 3, b = (off[s] + i1) * 3
      p.push([st.pos[a] + (st.pos[b] - st.pos[a]) * f, st.pos[a + 1] + (st.pos[b + 1] - st.pos[a + 1]) * f, st.pos[a + 2] + (st.pos[b + 2] - st.pos[a + 2]) * f]) }
    const key = [Math.floor(p[0][0] / cell), Math.floor(p[0][1] / cell), Math.floor(p[0][2] / cell)].join(',')
    if (!groups.has(key)) groups.set(key, []); groups.get(key).push(p)
  }
  const pos = [], nrm = [], uv = [], idx = []
  for (const g of groups.values()) {
    if (g.length < 3) continue
    const mean = Array.from({ length: M }, (_, k) => { const m = [0, 0, 0]; for (const p of g) for (let q = 0; q < 3; q++) m[q] += p[k][q] / g.length; return m })
    const ph = rnd() * 6.28, amp = 0.0022 * (0.5 + rnd()), freq = 2 + rnd() * 2, rr = radius * (1 - sizeJitter + 2 * sizeJitter * rnd()), cut = 1 - tipCut * rnd()
    const last = Math.max(8, Math.round((M - 1) * cut)), base = pos.length / 3
    for (let k = 0; k <= last; k++) {
      const a = mean[Math.max(0, k - 1)], b = mean[Math.min(M - 1, k + 1)]; let tx = b[0] - a[0], ty = b[1] - a[1], tz = b[2] - a[2]; const tl = Math.hypot(tx, ty, tz) || 1; tx /= tl; ty /= tl; tz /= tl
      let ux = 0, uy = 0, uz = 1; if (Math.abs(tz) > 0.9) { ux = 1; uz = 0 }
      let vx = ty * uz - tz * uy, vy = tz * ux - tx * uz, vz = tx * uy - ty * ux; const vl = Math.hypot(vx, vy, vz) || 1; vx /= vl; vy /= vl; vz /= vl
      ux = vy * tz - vz * ty; uy = vz * tx - vx * tz; uz = vx * ty - vy * tx
      const t = k / (M - 1), f = k > last - 4 ? (last - k) / 4 : 1, rad = rr * Math.sqrt(1 - (1 - f) ** 2) * (1 - 0.18 * t) + 0.0002
      const sw = amp * Math.sin(ph + freq * 6.2832 * t) * Math.min(1, t * 3)
      for (let a2 = 0; a2 <= sides; a2++) {
        const th = (a2 / sides) * 6.2832, c = Math.cos(th), s = Math.sin(th), nx = c * ux + s * vx, ny = c * uy + s * vy, nz = c * uz + s * vz
        pos.push(mean[k][0] + rad * nx + sw * ux, mean[k][1] + rad * ny + dy, mean[k][2] + rad * nz + sw * uz); nrm.push(nx, ny, nz); uv.push(a2 / sides, t * 5)
      }
    }
    for (let k = 0; k < last; k++) for (let a2 = 0; a2 < sides; a2++) { const i0 = base + k * (sides + 1) + a2, i1 = i0 + sides + 1; idx.push(i0, i1, i0 + 1, i0 + 1, i1, i1 + 1) }
  }
  return { pos, nrm, uv, idx, locks: groups.size }
}
