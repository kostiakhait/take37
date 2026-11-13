# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Fast shatter of glass panes by an arrangement of straight cracks (crashkit.break_glass for M_glass): a handful of straight crack lines (about half of them radiating from the impact
point, the rest across the pane) are CUT through the pane (bmesh bisect, perpendicular to the pane), so the shards have straight clean outlines and cost a few dozen cuts, not hundreds.
Shards near the impact fall out first; the rest stay as slightly tilted, shrunken pieces with visible gaps. frac 1 = gone (only shards on the frame stay as jagged teeth).
install() puts it in place of crashkit.break_glass; lamp lenses (other materials) keep the original function."""
import math
import random

import bmesh
import numpy as np
from mathutils import Quaternion, Vector as V3

import crashkit as ck

_orig = ck.break_glass


def _panes(bm, fs):
    """connected groups of faces (through shared edges) among fs"""
    fset = set(fs)
    seen, out = set(), []
    for f in fs:
        if f in seen:
            continue
        st, grp = [f], []
        seen.add(f)
        while st:
            g = st.pop()
            grp.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h in fset and h not in seen:
                        seen.add(h)
                        st.append(h)
        out.append(grp)
    return out


def break_glass(ob, region, frac, seed, cells=170, tilt=7.0, mats=('M_glass',)):
    if tuple(mats) != ('M_glass',):
        return _orig(ob, region, frac, seed, cells, tilt, mats)
    me = ob.data
    mw = ob.matrix_world
    M3 = mw.to_3x3()
    bm = bmesh.new()
    bm.from_mesh(me)
    pane_l = bm.faces.layers.int.new('pane')
    cell_l = bm.faces.layers.int.new('cell')
    bm.faces.ensure_lookup_table()
    names = [m.name if m else '' for m in me.materials]
    fs = [f for f in bm.faces if names[f.material_index] == 'M_glass' and region(mw @ f.calc_center_median())]
    if not fs:
        bm.free()
        return 0
    rnd = random.Random(seed)
    panes = [g for g in _panes(bm, fs) if len(g) >= 6]
    for pid, g in enumerate(panes, 1):
        for f in g:
            f[pane_l] = pid
    info = {}
    for pid, g in enumerate(panes, 1):
        C = np.array([(mw @ f.calc_center_median())[:] for f in g])
        nrm = np.array(sum((M3 @ f.normal * f.calc_area() for f in g), V3())[:])
        nrm /= max(np.linalg.norm(nrm), 1e-9)
        up = np.array([0, 0, 1.0]) if abs(nrm[2]) < 0.9 else np.array([1.0, 0, 0])
        u = np.cross(nrm, up)
        u /= np.linalg.norm(u)
        v = np.cross(nrm, u)
        cen = C.mean(axis=0)
        a, b = (C - cen) @ u, (C - cen) @ v
        info[pid] = dict(cen=cen, n=nrm, u=u, v=v, ext=(a.min(), a.max(), b.min(), b.max()))
    cuts = {}
    for pid, inf in info.items():
        a0, a1, b0, b1 = inf['ext']
        size = max(a1 - a0, b1 - b0)
        nl = int(np.clip(6 + 9 * min(frac, 1.0) + size * 3, 7, 18))
        fx = (rnd.uniform(0.3, 0.7), rnd.uniform(0.3, 0.7))
        foc = inf['cen'] + inf['u'] * (a0 + (a1 - a0) * fx[0]) + inf['v'] * (b0 + (b1 - b0) * fx[1])
        inf['foc'] = foc
        lines = []
        for k in range(nl):
            ang = math.pi * (k / max(1, nl // 2) if k < nl // 2 + 1 else rnd.random()) + rnd.uniform(-0.2, 0.2)
            if k <= nl // 2:
                p0 = foc + inf['u'] * rnd.uniform(-0.04, 0.04) + inf['v'] * rnd.uniform(-0.04, 0.04)
            else:
                p0 = inf['cen'] + inf['u'] * rnd.uniform(a0, a1) + inf['v'] * rnd.uniform(b0, b1)
            d = inf['u'] * math.cos(ang) + inf['v'] * math.sin(ang)
            m = np.cross(inf['n'], d)
            m /= np.linalg.norm(m)
            lines.append((p0, m))
        cuts[pid] = lines
        for p0, m in lines:
            sub = [f for f in bm.faces if f.is_valid and f[pane_l] == pid]
            geom = list(sub) + list({e for f in sub for e in f.edges}) + list({vv for f in sub for vv in f.verts})
            co = mw.inverted() @ V3(p0.tolist())
            no = (M3.transposed() @ V3(m.tolist())).normalized()
            bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=co, plane_no=no)
    bm.faces.ensure_lookup_table()
    bm.faces.index_update()
    pf = [f for f in bm.faces if f.is_valid and f[pane_l] > 0]
    sset = {f.index for f in pf}
    ids, base = {}, 0
    cent = np.array([(mw @ f.calc_center_median())[:] for f in pf])
    keys = []
    for f, c in zip(pf, cent):
        pid = f[pane_l]
        bits = 0
        for k, (p0, m) in enumerate(cuts[pid]):
            if (c - p0) @ m > 0:
                bits |= 1 << k
        keys.append((pid, bits))
    for kk in keys:
        if kk not in ids:
            ids[kk] = len(ids)
    for f, kk in zip(pf, keys):
        f[cell_l] = ids[kk]
    onframe = [any(len(e.link_faces) == 1 or any(lf.index not in sset for lf in e.link_faces) for e in f.edges) for f in pf]
    frame_cells = {ids[kk] for kk, o in zip(keys, onframe) if o}
    # which cells fall out: near the impact first
    cell_c = {}
    for f, c in zip(pf, cent):
        cell_c.setdefault(f[cell_l], []).append(c)
    gone = set()
    for (pid, bits), cid in ids.items():
        inf = info[pid]
        ctr = np.mean(cell_c[cid], axis=0)
        size = max(inf['ext'][1] - inf['ext'][0], inf['ext'][3] - inf['ext'][2])
        dist = np.linalg.norm(ctr - inf['foc']) / max(size, 0.1)
        if frac >= 0.999:
            if not (cid in frame_cells and rnd.random() < 0.5):
                gone.add(cid)
        elif rnd.random() < min(1.0, max(0.0, frac * 1.1 + 0.2 - 0.6 * dist)):
            gone.add(cid)
    kill = [f for f in pf if f[cell_l] in gone]
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    keep = [f for f in pf if f.is_valid]
    cut_e = list({e for f in keep for e in f.edges if len(e.link_faces) == 2 and e.link_faces[0][pane_l] > 0 and e.link_faces[1][pane_l] > 0
                  and e.link_faces[0][cell_l] != e.link_faces[1][cell_l]})
    bmesh.ops.split_edges(bm, edges=cut_e)
    frame_v = set()
    for f in bm.faces:
        if f.is_valid and f[pane_l] == 0:
            frame_v.update(vv.index for vv in f.verts)
    bm.verts.ensure_lookup_table()
    byc = {}
    for f in keep:
        if f.is_valid:
            byc.setdefault(f[cell_l], []).append(f)
    inv = mw.inverted()
    for c, faces in byc.items():
        vs = {vv for f in faces for vv in f.verts if vv.index not in frame_v}
        if not vs:
            continue
        ctr = sum((mw @ vv.co for vv in vs), V3()) / len(vs)
        nrm = sum((M3 @ f.normal for f in faces), V3()).normalized()
        axis = V3((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized()
        q = Quaternion(axis, math.radians(rnd.uniform(0.5, 1.0) * tilt * (2.0 if frac >= 0.999 else 1.0 + 1.2 * frac)))
        off = nrm * rnd.uniform(-0.01, 0.01)
        for vv in vs:
            w = mw @ vv.co
            vv.co = inv @ (ctr + q @ ((w - ctr) * 0.965) + off)
    bm.faces.layers.int.remove(pane_l)
    bm.faces.layers.int.remove(cell_l)
    bm.to_mesh(me)
    bm.free()
    me.update()
    return len(kill)


def install():
    ck.break_glass = break_glass
