# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Street trees for TAKE 37 (Blender 4.2, headless): maple, elm, oak, each as a real branching skeleton with bark (library bark texture) and a crown of painted leaf cards.

Every tree is one mesh with split-up parts: trunk, limbs, branches, twigs and leaf clusters keep their own branch ids, so a wind shader can bend each branch and flutter each cluster.
Per-vertex data for the wind (exported to the glb as custom attributes, see TREES.md): _SWAY, _FLUTTER, _PHASE, _BRANCH, _LEVEL, _PIVOT.
Leaf cards use the cluster atlases leaf_<species>_c.png (made in textures_prep.py) and custom (outward, sphere-like) vertex normals so that the crown shades as a volume, not as flat cards.
Kit names: StreetTree1 maple, 2 elm, 3 oak (summer green); StreetTree4 maple, 5 elm, 6 oak (autumn-mixed colours, other skeleton). Each in LOD0 and LOD1.
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector as V

import kitlib as K

# species: trunk, crown ellipsoid (centre height, radii), limb count and angles, leaf card size, leaf mix
SPECIES = {
    'maple': dict(leaf='leaf_maple', bark='bark', trunk_h=2.8, r0=0.26, c=(0, 0, 6.0), R=(3.2, 3.2, 3.5), limbs=7, limb_ang=(24, 44), up=0.30, droop=0.0,
                  leader=True, dens=0.85, card=0.72, limb_len=(3.0, 4.2), top=8.8),
    'elm': dict(leaf='leaf_elm', bark='bark2', trunk_h=3.6, r0=0.24, c=(0, 0, 7.0), R=(3.4, 3.4, 3.6), limbs=5, limb_ang=(14, 28), up=0.40, droop=0.26,
                leader=False, card=0.68, limb_len=(5.0, 6.0), top=10.6),
    'oak': dict(leaf='leaf_oak', bark='bark2', trunk_h=2.3, r0=0.33, c=(0, 0, 5.4), R=(4.2, 4.2, 2.9), limbs=6, limb_ang=(50, 70), up=0.12, droop=0.10,
                leader=False, card=0.74, limb_len=(4.0, 5.0), top=8.3),
}
ORDER = [('maple', False), ('elm', False), ('oak', False), ('maple', True), ('elm', True), ('oak', True)]    # StreetTree1..6


def hash01(*a):
    return random.Random(hash(a) & 0xffffff).random()


class TreeMesh:
    """Unwelded vertex soup with per-vertex wind data and custom normals."""

    def __init__(self, name):
        self.name = name
        self.P, self.UV, self.C, self.N = [], [], [], []
        self.raw, self.flut, self.phase, self.branch, self.level, self.pivot = [], [], [], [], [], []
        self.F = []            # (vertex ids, material name)

    def vert(self, p, uv, col, nrm, raw, flut, phase, branch, level, pivot):
        self.P.append(V(p))
        self.UV.append(uv)
        self.C.append(col)
        self.N.append(V(nrm).normalized())
        self.raw.append(raw)
        self.flut.append(flut)
        self.phase.append(phase)
        self.branch.append(branch)
        self.level.append(level)
        self.pivot.append(V(pivot))
        return len(self.P) - 1

    def face(self, ids, mat):
        self.F.append((ids, mat))

    def box(self, x0, y0, z0, x1, y1, z1, mat, tone=1.0):
        """Flat-shaded static box (grate, pit frame): wind data zero."""
        c = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        for idx, n in (((0, 3, 2, 1), (0, 0, -1)), ((4, 5, 6, 7), (0, 0, 1)), ((0, 1, 5, 4), (0, -1, 0)), ((1, 2, 6, 5), (1, 0, 0)), ((2, 3, 7, 6), (0, 1, 0)), ((3, 0, 4, 7), (-1, 0, 0))):
            pts = [c[i] for i in idx]
            uvs = [(pts[0][0] if abs(n[2]) > 0 else pts[0][1], pts[0][1] if abs(n[2]) > 0 else pts[0][2])] * 4
            ids = []
            for p in pts:
                u, v = (p[0], p[1]) if abs(n[2]) else ((p[0], p[2]) if abs(n[1]) else (p[1], p[2]))
                ids.append(self.vert(p, (u, v), (tone, tone, tone), n, 0.0, 0.0, 0.0, 0, 0, (0, 0, 0)))
            self.face(ids, mat)

    def build(self, collection=None, props=None):
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.new('UVMap')
        cl = bm.loops.layers.color.new('Color')
        lay = {k: bm.verts.layers.float.new(k) for k in ('_SWAY', '_FLUTTER', '_PHASE', '_BRANCH', '_LEVEL')}
        lpv = bm.verts.layers.float_vector.new('_PIVOT')
        dmax = max(self.raw) or 1.0
        vs = []
        for i, p in enumerate(self.P):
            v = bm.verts.new(p)
            v[lay['_SWAY']] = min(1.0, self.raw[i] / dmax)
            v[lay['_FLUTTER']] = self.flut[i]
            v[lay['_PHASE']] = self.phase[i]
            v[lay['_BRANCH']] = float(self.branch[i])
            v[lay['_LEVEL']] = float(self.level[i])
            q = self.pivot[i]
            v[lpv] = (q.x, q.z, -q.y)                        # glTF space (Y up): the exporter converts positions, not custom attributes
            vs.append(v)
        bm.verts.index_update()
        slots = []
        for ids, mat in self.F:
            if mat not in slots:
                slots.append(mat)
            try:
                f = bm.faces.new([vs[i] for i in ids])
            except ValueError:
                continue
            f.material_index = slots.index(mat)
            f.smooth = True
            for lp in f.loops:
                i = vs.index(lp.vert) if False else lp.vert.index
                lp[uvl].uv = self.UV[i]
                c = self.C[i]
                lp[cl] = (c[0], c[1], c[2], 1.0)
        me = bpy.data.meshes.new(self.name)
        bm.to_mesh(me)
        bm.free()
        for s in slots:
            me.materials.append(K.mat(s))
        me.normals_split_custom_set_from_vertices([tuple(n) for n in self.N])
        o = bpy.data.objects.new(self.name, me)
        (collection or bpy.context.scene.collection).objects.link(o)
        for k, v in (props or {}).items():
            o[k] = v
        return o


class Tree:
    def __init__(self, species, autumn, seed, lod):
        self.sp = SPECIES[species]
        self.species, self.autumn, self.lod = species, autumn, lod
        self.rnd = random.Random(seed * 7919 + 13)
        self.hi = lod == 0
        self.tm = TreeMesh(f'StreetTree_{species}')
        self.branches = []       # skeleton records, for clusters
        self.clusters = []
        self.nb = 0
        sp = self.sp
        self.C = V(sp['c'])
        self.R = V(sp['R'])

    # ------------------------------------------------------------------ envelope
    def env(self, p):
        q = (p - self.C)
        return math.sqrt((q.x / self.R.x) ** 2 + (q.y / self.R.y) ** 2 + (q.z / self.R.z) ** 2)

    def outward(self, p):
        q = p - self.C
        d = V((q.x / self.R.x ** 2, q.y / self.R.y ** 2, q.z / self.R.z ** 2))
        return d.normalized() if d.length > 1e-6 else V((0, 0, 1))

    # ------------------------------------------------------------------ skeleton
    def grow(self, p0, d0, length, r0, level, raw0, seg_len, parent_bid=0, steer=0.0, wob=0.25, up=None, droop=None):
        sp, rnd = self.sp, self.rnd
        up = sp['up'] if up is None else up
        droop = sp['droop'] if droop is None else droop
        p, d = V(p0), V(d0).normalized()
        pts = [p.copy()]
        steps = max(2, int(length / seg_len))
        for i in range(steps):
            t = i / steps
            d = d + V((rnd.gauss(0, wob), rnd.gauss(0, wob), rnd.gauss(0, wob * 0.7))) * 0.5
            d = d + V((0, 0, up * (1.0 - t * 0.5) - droop * t * (1.4 if level > 1 else 1.0))) * 0.35
            if steer > 0 and level >= 1:
                d = d + self.outward(p) * steer * 0.3
            d.normalize()
            p = p + d * (length / steps)
            pts.append(p.copy())
            if level >= 1 and self.env(p) > 1.0 and i >= 1:
                break
        bid = self.nb
        self.nb += 1
        n = len(pts)
        rad = []
        for i in range(n):
            t = i / (n - 1)
            rad.append(max(0.006, r0 * (1.0 - t) ** 0.8 + 0.004))
        b = dict(pts=pts, rad=rad, level=level, raw0=raw0, id=bid, parent=parent_bid, phase=self.rnd.random())
        self.branches.append(b)
        # cumulative skeleton distance at every point
        cum = [raw0]
        for i in range(1, n):
            cum.append(cum[-1] + (pts[i] - pts[i - 1]).length)
        b['cum'] = cum
        return b

    def make_tree(self):
        sp, rnd = self.sp, self.rnd
        # trunk
        top = sp['trunk_h'] + (4.4 if sp['leader'] else 0.0)
        tr = self.grow(V((0, 0, 0)), V((rnd.gauss(0, 0.03), rnd.gauss(0, 0.03), 1)), top, sp['r0'], 0, 0.0, 0.45, wob=0.12, up=0.0, droop=0.0)
        tr['rad'] = [max(0.05, sp['r0'] * (1 - 0.43 * min(1.0, i / max(1, len(tr['pts']) - 1) * (top / sp['trunk_h']) * 0.62))) for i in range(len(tr['pts']))] if True else tr['rad']
        if sp['leader']:
            for i in range(len(tr['rad'])):
                t = i / (len(tr['rad']) - 1)
                tr['rad'][i] = max(0.05, sp['r0'] * (1 - 0.45 * t * 0.7) * (1 - 0.7 * max(0, t - 0.55) / 0.45))
        tr_pts = tr['pts']
        # limbs: spread round the trunk at golden-angle steps over the upper trunk
        n = sp['limbs']
        a0 = rnd.uniform(0, 6.28)
        for i in range(n):
            a = a0 + i * 2.39996
            zt = sp['trunk_h'] * (0.82 + 0.40 * i / max(1, n - 1)) if not sp['leader'] else sp['trunk_h'] * 0.85 + 2.6 * i / max(1, n - 1)
            zt = min(zt, tr_pts[-1].z - 0.2)
            k = min(range(len(tr_pts)), key=lambda j: abs(tr_pts[j].z - zt))
            base = tr_pts[k]
            el = math.radians(rnd.uniform(*sp['limb_ang']))                       # elevation from the vertical
            dirv = V((math.sin(el) * math.cos(a), math.sin(el) * math.sin(a), math.cos(el)))
            ln = rnd.uniform(*sp['limb_len']) * (1.0 - 0.08 * (n - 1 - i) * 0.0)
            if sp['leader'] and i > n - 3:
                ln *= 0.75
            lb = self.grow(base, dirv, ln, tr['rad'][k] * 0.62 * (0.9 if sp['leader'] else 1.0), 1, tr['cum'][k], 0.5, parent_bid=tr['id'], steer=0.55, wob=0.22)
            self.sub(lb)
        if sp['leader']:
            self.sub(tr, leader=True)
        else:
            # a short central stub of foliage at the top of the trunk
            lb = self.grow(tr_pts[-1], V((rnd.gauss(0, 0.2), rnd.gauss(0, 0.2), 1)), 2.6, tr['rad'][-1] * 0.9, 1, tr['cum'][-1], 0.5, parent_bid=tr['id'], steer=0.5)
            self.sub(lb)
        self.fill_crown()
        return tr

    def fill_crown(self):
        """Short twigs from the nearest skeleton point out to sample points of the crown shell, so that the foliage fills the envelope and every cluster hangs on wood."""
        rnd = self.rnd
        cand = []
        for b in self.branches:
            if b['level'] >= 1:
                for j, p in enumerate(b['pts']):
                    cand.append((p, b, j))
        n_fill = {True: 150, False: 70}[self.hi] * (1.5 if self.sp['leader'] else 1.0)
        n_fill = int(n_fill)
        done = 0
        tries = 0
        while done < n_fill and tries < n_fill * 12:
            tries += 1
            d = V((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))).normalized()
            rad = rnd.uniform(0.55, 1.0) ** 0.5
            q = self.C + V((d.x * self.R.x, d.y * self.R.y, d.z * self.R.z)) * rad
            if q.z < 3.0 or (self.sp['leader'] and q.z > 8.6):
                continue
            p, b, j = min(cand, key=lambda c: (c[0] - q).length_squared)
            dist = (p - q).length
            if dist < 0.35 or dist > 2.4:
                continue
            mid = (p + q) / 2 + V((rnd.gauss(0, 0.12), rnd.gauss(0, 0.12), 0.05))
            pts = [p.copy(), mid, q]
            r0 = max(0.012, b['rad'][j] * 0.55)
            bid = self.nb
            self.nb += 1
            cum = [b['cum'][j], b['cum'][j] + dist * 0.5, b['cum'][j] + dist]
            self.branches.append(dict(pts=pts, rad=[r0, r0 * 0.6, 0.008], level=3, raw0=cum[0], id=bid, parent=b['id'], phase=rnd.random(), cum=cum))
            self.clusters.append(dict(p=q, b=self.branches[-1], j=2, sz=0.85))
            done += 1

    def sub(self, b, leader=False):
        """Side branches along branch b (recursively), clusters at the ends."""
        rnd, sp = self.rnd, self.sp
        lvl = b['level']
        pts = b['pts']
        n = len(pts)
        maxlvl = 2
        if lvl < maxlvl:
            count = {0: 7, 1: 6, 2: 4}[lvl] if self.hi else {0: 6, 1: 5, 2: 3}[lvl]
            count = max(1, round(count * sp.get('dens', 1.0)))
            for k in range(count):
                t = 0.32 + 0.66 * (k + rnd.random() * 0.8) / count if lvl else 0.35 + 0.65 * (k + rnd.random() * 0.8) / count
                j = min(n - 2, max(1, int(t * (n - 1))))
                base = pts[j]
                par = (pts[j + 1] - pts[j - 1]).normalized()
                a = rnd.uniform(0, 6.28)
                ortho = par.cross(V((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.2, 0.6)))).normalized()
                ang = math.radians(rnd.uniform(35, 75))
                dirv = (par * math.cos(ang) + ortho * math.sin(ang) + self.outward(base) * 0.4).normalized()
                span = (n - 1 - j) / max(1, n - 1)
                ln = {0: 2.8, 1: 2.2, 2: 1.3}[lvl] * rnd.uniform(0.7, 1.15) * (0.55 + 0.6 * span)
                if leader:
                    ln *= 0.9
                cb = self.grow(base, dirv, ln, b['rad'][j] * 0.6, lvl + 1, b['cum'][j], 0.42 if lvl < 2 else 0.3, parent_bid=b['id'], steer=0.5, wob=0.28)
                self.sub(cb)
        # clusters: the tip, and along the outer part of twigs
        if lvl >= 2:
            for j in range(max(1, int(n * 0.45)), n):
                self.clusters.append(dict(p=pts[j], b=b, j=j, sz=1.0 if j == n - 1 else 0.7))
        elif lvl == 1 and n > 3:
            self.clusters.append(dict(p=pts[-1], b=b, j=n - 1, sz=1.0))

    # ------------------------------------------------------------------ meshes
    def tone_wood(self, p, level):
        g = (0.42 + 0.26 * min(1.0, p.z / 3.0) if level == 0 else 0.6)
        n = 0.84 + 0.3 * K.fbm(V((p.x * 2.1, p.y * 2.1, p.z * 0.7)), 5, 1.0)
        v = g * n
        return (v, v * 0.98, v * 0.94)

    def emit_wood(self, minlvl_cut):
        tm, sp = self.tm, self.sp
        seg_by = {0: 14 if self.hi else 8, 1: 8 if self.hi else 5, 2: 6 if self.hi else 4, 3: 4 if self.hi else 3}
        for b in self.branches:
            lvl = b['level']
            if lvl > minlvl_cut:
                continue
            pts, rad, cum = b['pts'], b['rad'], b['cum']
            n = len(pts)
            seg = seg_by[lvl]
            rings, u_prev = [], None
            Rn = self.rnd
            ph = [Rn.uniform(0, 6.28) for _ in range(3)]
            tile = 1.0
            for i in range(n):
                p = pts[i]
                t = (pts[min(n - 1, i + 1)] - pts[max(0, i - 1)]).normalized()
                if u_prev is None:
                    u = t.cross(V((0, 0, 1)))
                    if u.length < 1e-3:
                        u = t.cross(V((0, 1, 0)))
                else:
                    u = u_prev - t * u_prev.dot(t)
                u.normalize()
                w = t.cross(u)
                u_prev = u
                r = rad[i]
                z = p.z
                flare = 1.0
                if lvl == 0:                                       # root flare and slight lumps along the trunk
                    f = max(0.0, 1.0 - z / 0.9)
                    flare = 1.0 + 0.55 * f ** 1.6
                ring = []
                for k in range(seg + 1):
                    th = 2 * math.pi * (k % seg) / seg
                    rr = r * flare
                    if lvl == 0:
                        rr *= 1.0 + 0.07 * math.sin(th * 3 + ph[0] + z * 1.3) + 0.04 * math.sin(th * 5 + ph[1] + z * 2.7)
                        if flare > 1.001:
                            rr *= 1.0 + (flare - 1.0) * 0.5 * abs(math.sin(th * 2.5 + ph[2]))
                    dv = u * math.cos(th) + w * math.sin(th)
                    pos = p + dv * rr
                    circ = 2 * math.pi * max(r * flare, 0.02)
                    uv = (k / seg * circ / tile, cum[i] / tile * (1.0 if lvl == 0 else 1.3))
                    ring.append(tm.vert(pos, uv, self.tone_wood(pos, lvl), dv, cum[i], 0.0, b['phase'], b['id'], lvl, pts[0]))
                rings.append(ring)
            for i in range(n - 1):
                for k in range(seg):
                    tm.face([rings[i][k], rings[i][k + 1], rings[i + 1][k + 1], rings[i + 1][k]], sp['bark'])
            # close the tip with a point
            tip = tm.vert(pts[-1] + (pts[-1] - pts[-2]).normalized() * 0.01, (0.5, cum[-1]), self.tone_wood(pts[-1], lvl), (pts[-1] - pts[-2]), cum[-1], 0.0, b['phase'], b['id'], lvl, pts[0])
            for k in range(seg):
                tm.face([rings[-1][k], rings[-1][k + 1], tip], sp['bark'])

    def emit_leaves(self, per_cluster, size_mul, rect_pool):
        tm, sp, rnd = self.tm, self.sp, self.rnd
        dmax_branch = max(b['cum'][-1] for b in self.branches)
        for ci, cl in enumerate(self.clusters):
            b, j = cl['b'], cl['j']
            P = cl['p']
            raw = b['cum'][j]
            ph = rnd.random()
            for _ in range(per_cluster):
                out = self.outward(P)
                rc = 0.75 * cl['sz']
                ctr = P + out * 0.15 + V((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.7, 0.7))) * rc
                # keep cards inside a shell of the envelope so that the crown keeps its shape
                e = self.env(ctr)
                if e > 1.08:
                    ctr = self.C + (ctr - self.C) / e * 1.08
                radial = (ctr - self.C).normalized() if (ctr - self.C).length > 1e-6 else V((0, 0, 1))
                nrm = (radial * 1.0 + V((rnd.gauss(0, 0.38), rnd.gauss(0, 0.38), rnd.gauss(0, 0.3)))).normalized()
                if sp['droop'] > 0.2 and rnd.random() < 0.5:
                    nrm = (nrm + V((0, 0, -0.5))).normalized()
                ref = V((0, 0, 1)) if abs(nrm.z) < 0.9 else V((1, 0, 0))
                uax = nrm.cross(ref).normalized()
                vax = nrm.cross(uax)
                ang = rnd.uniform(0, 6.28)
                uax, vax = uax * math.cos(ang) + vax * math.sin(ang), vax * math.cos(ang) - uax * math.sin(ang)
                s = sp['card'] * size_mul * rnd.uniform(0.8, 1.2) * cl['sz'] ** 0.4 * 0.5
                rect = rect_pool[rnd.randrange(len(rect_pool))]
                # shade: darker deep inside the crown, lighter on top and outside
                depth = min(1.0, (ctr - self.C).length / max(self.R.x, 1e-3))
                topl = max(-0.3, min(0.3, (ctr.z - self.C.z) / self.R.z * 0.3))
                tone = (0.62 + 0.55 * depth ** 0.8 + topl) * rnd.uniform(0.9, 1.08)
                hue = rnd.uniform(0.94, 1.06)
                col = (tone * hue, tone, tone * 2 - tone * hue if False else tone * (2 - hue) * 0.98)
                shade_n = (radial * 0.85 + nrm * 0.15)
                corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
                uvs = [(rect[0], rect[1]), (rect[2], rect[1]), (rect[2], rect[3]), (rect[0], rect[3])]
                if uax.cross(vax).dot(shade_n) < 0:                      # winding: the geometric normal agrees with the outward shading normal
                    corners = [(-1, -1), (-1, 1), (1, 1), (1, -1)]
                    uvs = [(rect[0], rect[1]), (rect[0], rect[3]), (rect[2], rect[3]), (rect[2], rect[1])]
                ids = []
                for (cx, cy), uv in zip(corners, uvs):
                    pos = ctr + uax * (cx * s) + vax * (cy * s)
                    # flutter is 0.3 at the middle, 1 at the rim of the card; sway follows the twig the cluster hangs on
                    fl = 0.3 + 0.7 * min(1.0, ((pos - ctr).length / (s * 1.414)))
                    ids.append(tm.vert(pos, uv, col, shade_n, raw + (pos - P).length * 0.5, fl, ph, b['id'], 4, P))
                tm.face(ids, sp['leaf'])

    def emit_core(self, n, size_mul, pool):
        """Dark inner cards near the middle of the crown: gaps between the outer clusters show shaded foliage, not the sky."""
        tm, sp, rnd = self.tm, self.sp, self.rnd
        for _ in range(n):
            a = rnd.uniform(0, 6.28)
            rr = rnd.uniform(0.15, 0.62)
            ctr = self.C + V((math.cos(a) * self.R.x * rr, math.sin(a) * self.R.y * rr, rnd.uniform(-0.6, 0.7) * self.R.z))
            radial = (ctr - self.C).normalized() if (ctr - self.C).length > 1e-6 else V((0, 0, 1))
            nrm = (radial + V((rnd.gauss(0, 0.6), rnd.gauss(0, 0.6), rnd.gauss(0, 0.6)))).normalized()
            ref = V((0, 0, 1)) if abs(nrm.z) < 0.9 else V((1, 0, 0))
            u = nrm.cross(ref).normalized()
            v = nrm.cross(u)
            s = sp['card'] * size_mul * rnd.uniform(1.1, 1.5) * 0.5
            rect = pool[rnd.randrange(len(pool))]
            tone = rnd.uniform(0.36, 0.5)
            col = (tone, tone, tone * 0.9)
            ids = []
            for (cx, cy), uv in zip([(-1, -1), (1, -1), (1, 1), (-1, 1)], [(rect[0], rect[1]), (rect[2], rect[1]), (rect[2], rect[3]), (rect[0], rect[3])]):
                pos = ctr + u * (cx * s) + v * (cy * s)
                ids.append(tm.vert(pos, uv, col, radial, 0.0 + 0.5 * (pos.z / 10.0) * 10.0, 0.4, rnd.random(), 0, 4, ctr))
            tm.face(ids, sp['leaf'])

    def pit(self):
        tm = self.tm
        tm.box(-0.6, -0.6, 0.0, 0.6, 0.6, 0.02, 'soil', 0.55)
        for (a, b, c, d) in ((-0.64, -0.64, 0.64, -0.56), (-0.64, 0.56, 0.64, 0.64), (-0.64, -0.56, -0.56, 0.56), (0.56, -0.56, 0.64, 0.56)):
            tm.box(a, b, 0.0, c, d, 0.045, 'paint_dark')
        if self.hi:
            for k in range(-3, 4):                                   # cast-iron grate bars either side of the trunk, leaving the opening for it
                x = k * 0.15
                if abs(x) > 0.12:
                    tm.box(x - 0.02, -0.56, 0.0, x + 0.02, 0.56, 0.04, 'black_metal')


def build_tree(lod, tree_no):
    species, autumn = ORDER[tree_no - 1]
    seed = tree_no * 31 + 5
    T = Tree(species, autumn, seed, lod)
    T.make_tree()
    T.pit()
    sp = T.sp
    rects = [(0.0 + 0.004, 0.5 + 0.004, 0.5 - 0.004, 1.0 - 0.004), (0.5 + 0.004, 0.5 + 0.004, 1.0 - 0.004, 1.0 - 0.004),
             (0.004, 0.004, 0.5 - 0.004, 0.5 - 0.004), (0.5 + 0.004, 0.004, 1.0 - 0.004, 0.5 - 0.004)]       # atlas cells: green, yellow-green, gold, red  (v up: row 0 is the top)
    if autumn:
        pool = [rects[2], rects[2], rects[3], rects[3], rects[1], rects[0], rects[2], rects[3]]
    else:
        pool = [rects[0], rects[0], rects[1], rects[0], rects[1], rects[1], rects[0], rects[2]]
    T.emit_wood(3 if lod == 0 else 2)
    per, mul = (7, 1.0) if lod == 0 else (3, 1.9)
    T.emit_leaves(per, mul, pool)
    T.emit_core(60 if lod == 0 else 22, mul, pool)
    name = f'StreetTree{tree_no}_LOD{lod}'
    T.tm.name = name
    nw = sum(len(i) - 2 for i, mm in T.tm.F if mm in ('bark', 'bark2'))
    print('TREE', name, 'wood tris', nw, 'leaf tris', sum(len(i) - 2 for i, mm in T.tm.F if mm.startswith('leaf')), 'clusters', len(T.clusters), 'branches', len(T.branches))
    o = T.tm.build(props={'front': '+X', 'seed': tree_no, 'species': species, 'autumn': int(autumn), 'sway_format': 'TREES.md'})
    o.name = name
    o.data.name = name
    return o
