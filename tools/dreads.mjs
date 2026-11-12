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
