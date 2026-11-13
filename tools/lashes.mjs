// Strand eyelashes (game code, outside the engine): hairs grown along the preset's lash cards (head.dna eyelashes_lod0_mesh): each card is a quad whose
// two vertices nearest the eye are the root and the two farthest the tip. Every card gives `density` hairs, curled up and out, longer toward the outer corner.
// Returns a strand set in head coordinates minus gdy (the groom node adds gdy back), for ribbons().
export function lashStrands(head, { gdy = 0, density = 9, inner = 1.0, outer = 1.7, curl = 0.0045, seed = 5, upperOnly = true, maxLen = 0.0105 } = {}) {
  let r = seed >>> 0; const rnd = () => ((r = (Math.imul(r, 1664525) + 1013904223) >>> 0) / 4294967296)
  const m = head.meshes.find((x) => x.name === 'eyelashes_lod0_mesh'), P = m.positions, L = m.layouts.positions
  const eyeC = (n) => { const e = head.meshes.find((x) => x.name === n), k = e.positions.xs.length; let c = [0, 0, 0]; for (let i = 0; i < k; i++) { c[0] += e.positions.xs[i] / k; c[1] += e.positions.ys[i] / k; c[2] += e.positions.zs[i] / k } return c.map((v) => v * 0.01) }
  const eyes = [eyeC('eyeLeft_lod0_mesh'), eyeC('eyeRight_lod0_mesh')]
  const pt = (li) => { const i = L[li]; return [P.xs[i] * 0.01, P.ys[i] * 0.01, P.zs[i] * 0.01] }
  const strands = []
  for (const f of m.faces) {
    const v = [...f].map(pt), mid = v.reduce((a, p) => a.map((x, i) => x + p[i] / v.length), [0, 0, 0])
    const c = eyes.reduce((b, e) => (Math.hypot(e[0] - mid[0], e[1] - mid[1], e[2] - mid[2]) < Math.hypot(b[0] - mid[0], b[1] - mid[1], b[2] - mid[2]) ? e : b))
    if (upperOnly && mid[1] < c[1] - 0.002) continue
    const d = v.map((p) => Math.hypot(p[0] - c[0], p[1] - c[1], p[2] - c[2])), o = d.map((x, i) => i).sort((a, b) => d[a] - d[b])
    const r0 = v[o[0]], r1 = v[o[1]], t0 = v[o[2]], t1 = v[o[3]]
    // pair each root with the tip nearer to it
    const dd = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]); let ta = t0, tb = t1; if (dd(r0, t1) + dd(r1, t0) < dd(r0, t0) + dd(r1, t1)) { ta = t1; tb = t0 }
    if (dd(r0, ta) > 0.02 || dd(r1, tb) > 0.02) continue
    const out = Math.abs(mid[0]) > Math.abs(c[0]) ? 1 : -1, t = Math.max(0, Math.min(1, ((Math.abs(mid[0]) - Math.abs(c[0])) / 0.012) * 0.5 + 0.5)), len = inner + (outer - inner) * t
    for (let k = 0; k < density; k++) {
      const u = rnd(), jl = 0.85 + 0.3 * rnd(), root = r0.map((x, i) => x + (r1[i] - x) * u), tip = ta.map((x, i) => x + (tb[i] - x) * (u + (rnd() - 0.5) * 0.2))
      const dir = tip.map((x, i) => x - root[i]), pts = []
      const dl = Math.hypot(...dir); if (dl > 0.02) continue
      const cap = Math.min(1, maxLen / (dl * len * jl))
      for (let s = 0; s <= 5; s++) { const q = s / 5, e = len * jl * q
        pts.push([root[0] + dir[0] * e + out * curl * q * q * 0.6, root[1] + dir[1] * e + curl * q * q * jl * len, root[2] + dir[2] * e + curl * q * q * 0.5 * jl * len]) }
      strands.push(pts)
    }
  }
  const nS = strands.length, M = 6, pos = new Float32Array(nS * M * 3), counts = new Int32Array(nS).fill(M), uv = new Float32Array(nS * 2), width = new Float32Array(nS * M).fill(0.0001)
  strands.forEach((p, s) => p.forEach((q, k) => { pos[(s * M + k) * 3] = q[0]; pos[(s * M + k) * 3 + 1] = q[1] - gdy; pos[(s * M + k) * 3 + 2] = q[2] }))
  return { nS, nV: nS * M, counts, pos, uv, width }
}
