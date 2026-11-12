# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Stage wheels: the three wheel meshes of the rig and the 18 wheel nodes.

11R22.5 radial truck tyres (no maker named) on polished aluminium disc wheels, 10-stud hub-piloted, with hand holes, nut covers, hub caps and brake drums.
  steer  : single tyre, ribbed tread, hub with oil cap
  drive  : dual tyres, lug tread, deep-dish outer disc, drum behind
  trailer: dual tyres, rib tread
Every Wheel_* node is an empty at the wheel centre (spin about its Y); its child mesh shares one mesh datablock per type, the right side being the left rotated 180 degrees about Z.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

import carkit as CK
import dims as D
import tkit as T
from tkit import V3, Mesh

N_TYRE = 180


def tread_rib(u, v):
    av = abs(v)
    for g in (0.20, 0.56):
        if abs(av - g) < 0.055:
            return 0.0125
    if av > 0.86:
        return 0.002
    if (u * 120 + av * 3) % 1.0 < 0.05 and av < 0.8:
        return 0.002
    return 0.0


def tread_lug(u, v, n_pitch=30):
    av = abs(v)
    if av < 0.07:
        return 0.012 if int(u * n_pitch * 2) % 2 == 0 else 0.0
    k = u * n_pitch + 0.33 * (1 - av) * (1 if v > 0 else -1) * 0.0 + 0.30 * av
    fr = k - math.floor(k)
    if fr < 0.34 and av > 0.09:
        return 0.0145 if av < 0.80 else 0.010
    if abs(av - 0.40) < 0.02:
        return 0.004
    return 0.0


def rings_xz(rs_y, n, s=1.0):
    return [[V3((r * math.cos(2 * math.pi * k / n), s * y, r * math.sin(2 * math.pi * k / n))) for k in range(n)] for r, y in rs_y]


def disc_with_holes(face_prof, hole_r, hole_ang0, n_holes, hole_w, hole_h, y_lo, y_hi):
    """The wheel disc face lofted from `face_prof` [(r, y)] and cut by oval hand holes (exact boolean); returns a bmesh."""
    m = Mesh()
    m.loft(rings_xz(face_prof, 96), 'alu_wheel')
    ob = m.finish('wdisc', box_uv=False)
    cutters = []
    for k in range(n_holes):
        a = hole_ang0 + 2 * math.pi * k / n_holes
        cm = Mesh()
        c = V3((hole_r * math.cos(a), 0, hole_r * math.sin(a)))
        ax = (V3((-math.sin(a), 0, math.cos(a))), V3((0, 1, 0)), V3((math.cos(a), 0, math.sin(a))))
        cm.rbox(c + V3((0, (y_lo + y_hi) / 2, 0)), (hole_w, y_hi - y_lo, hole_h), min(hole_w, hole_h) * 0.45, 'black', ax, seg=3)
        cutters.append(cm.finish(f'hc{k}', box_uv=False))
    T.boolean(ob, cutters, 'DIFFERENCE')
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bpy.data.objects.remove(ob)
    return bm


def add_bm(m, bm, kind, flip_y=False):
    tmp = bm
    if flip_y:
        bmesh.ops.scale(tmp, vec=(1, -1, 1), verts=tmp.verts)
        bmesh.ops.reverse_faces(tmp, faces=tmp.faces)
    m.merge(tmp, kind)


def smoothstep(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def wheel_disc(m, side, dish):
    """One disc wheel about the centre plane y=0 (outer flange toward +y when side=+1). dish: 0 for a steer wheel (face near the flange), >0 deep-dish outer duals."""
    Rr = D.R_RIM
    s = side
    sec = [(-0.105, Rr + 0.016), (-0.100, Rr + 0.019), (-0.095, Rr + 0.004), (-0.090, Rr - 0.008), (0.090, Rr - 0.008), (0.095, Rr + 0.004), (0.100, Rr + 0.019), (0.105, Rr + 0.016),
           (0.103, Rr + 0.002), (0.096, Rr - 0.004)]
    m.loft([[V3((r * math.cos(2 * math.pi * k / 120), s * y, r * math.sin(2 * math.pi * k / 120))) for y, r in sec] for k in range(120)], 'alu_wheel', closed=False, loop=True)

    def fy(r):
        return 0.090 - 0.012 * smoothstep((0.27 - r) / 0.05) - dish * smoothstep((0.235 - r) / 0.085)

    prof = [(r, fy(r)) for r in (Rr - 0.008, 0.262, 0.245, 0.228, 0.210, 0.192, 0.175, 0.158, 0.135, 0.100, 0.0)]
    bm = disc_with_holes(prof, 0.205, math.pi / 10, 10, 0.074, 0.058, -0.5, 0.5)
    if s < 0:
        bmesh.ops.scale(bm, vec=(1, -1, 1), verts=bm.verts)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    m.merge(bm, 'alu_wheel')
    yn = fy(0.1429)
    for k in range(10):                                   # hub-piloted flanged nuts on the 285.75 mm circle
        a = 2 * math.pi * k / 10
        c = V3((0.1429 * math.cos(a), s * yn, 0.1429 * math.sin(a)))
        m.cyl(c, c + V3((0, s * 0.022, 0)), 0.0185, 'steel', seg=6)
        m.cyl(c + V3((0, s * 0.022, 0)), c + V3((0, s * 0.028, 0)), 0.0125, 'steel', seg=8)
    y0 = fy(0.098)
    m.loft(rings_xz([(0.098, y0), (0.094, y0 + 0.014), (0.080, y0 + 0.020), (0.0, y0 + 0.022)], 72, s), 'chrome')      # the hub cover
    CK.valve_stem(m, s, 0.215, fy(0.215), -50.0)


def tyre_mesh(m, tread, dy, tag, letter=True, n=144, nv=24):
    """The tyre appended to m, its centre plane at y=dy (its lettered side toward +y)."""
    t = Mesh()
    CK.tyre(t, 1, D.R_TYRE, D.R_RIM, D.W_TYRE, tread, [('11R22.5', 90, 0.50, 0.020), ('RADIAL', 270, 0.50, 0.020), ('TUBELESS', 180, 0.30, 0.012)] if letter else [], n=n, nv=nv)
    for v in t.bm.verts:
        v.co.y += dy
    # carry over the material kinds
    mi = {}
    for i, k in enumerate(t.kinds):
        mi[i] = m.mi(k)
    vmap = {v: m.bm.verts.new(v.co) for v in t.bm.verts}
    for f in t.bm.faces:
        try:
            nf = m.bm.faces.new([vmap[v] for v in f.verts])
            nf.material_index = mi[f.material_index]
        except ValueError:
            pass
    t.bm.free()


def drum_and_hub(m, side, y_in, steer):
    s = side
    # brake drum behind the wheel (finned), hub barrel with the bearing cap
    m.cyl(V3((0, s * y_in, 0)), V3((0, s * (y_in - 0.19), 0)), 0.205 if not steer else 0.200, 'steel_dark', seg=48)
    for k in range(32):
        a = 2 * math.pi * k / 32
        m.box(V3((0.206 * math.cos(a), s * (y_in - 0.07), 0.206 * math.sin(a))), (0.005, 0.12, 0.010), 'steel_dark', (V3((-math.sin(a), 0, math.cos(a))), V3((0, 1, 0)), V3((math.cos(a), 0, math.sin(a)))))
    m.cyl(V3((0, s * (y_in - 0.19), 0)), V3((0, s * (y_in - 0.20), 0)), 0.225, 'frame', seg=48)         # backing plate


def build_wheel(kind):
    m = Mesh()
    if kind == 'steer':
        tyre_mesh(m, tread_rib, 0.0, 's')
        wheel_disc(m, 1, 0.0)
        drum_and_hub(m, 1, 0.095, True)
        # the steer hub's oil cap (clear window) on the nut ring
        m.cyl(V3((0, 0.100, 0)), V3((0, 0.138, 0)), 0.070, 'chrome', seg=32, r1=0.060)
        m.cyl(V3((0, 0.138, 0)), V3((0, 0.142, 0)), 0.050, 'lens_amber', seg=24)
    else:
        tr = tread_lug if kind == 'drive' else tread_rib
        sp = D.DUAL / 2
        tyre_mesh(m, tr, sp, 'o')
        tyre_mesh(m, tr, -sp, 'i', letter=False, n=64, nv=8)     # the inner tyre of a dual is hidden behind the outer one: a light mesh
        o = Mesh()
        # outer disc: deep dish, centre plane +sp; inner disc mirrored about 0
        wheel_disc(o, 1, 0.115)
        for v in o.bm.verts:
            v.co.y += sp
        i = Mesh()
        wheel_disc(i, 1, 0.115)
        bmesh.ops.scale(i.bm, vec=(1, -1, 1), verts=i.bm.verts)
        bmesh.ops.reverse_faces(i.bm, faces=i.bm.faces)
        for v in i.bm.verts:
            v.co.y -= sp
        for src in (o, i):
            mi = {j: m.mi(k) for j, k in enumerate(src.kinds)}
            vmap = {v: m.bm.verts.new(v.co) for v in src.bm.verts}
            for f in src.bm.faces:
                try:
                    nf = m.bm.faces.new([vmap[v] for v in f.verts])
                    nf.material_index = mi[f.material_index]
                except ValueError:
                    pass
            src.bm.free()
        # the axle end and its hub cap standing in the deep dish of the outer wheel, the drum behind
        m.cyl(V3((0, 0.02, 0)), V3((0, sp - 0.02, 0)), 0.16, 'steel_dark', seg=40)
        drum_and_hub(m, 1, -sp - 0.095, False)
        m.cyl(V3((0, -sp - 0.285, 0)), V3((0, -sp - 0.30, 0)), 0.095, 'steel_dark', seg=24)
    ob = m.finish('W_' + kind, sharp=40)
    return ob


def make_nodes(parent, specs, ob_by_kind):
    """specs: (node name, kind, world centre, side)"""
    for name, kind, c, side in specs:
        e = T.empty(name, c, parent)
        src = ob_by_kind[kind]
        ob = bpy.data.objects.new(name + '_mesh', src.data)
        bpy.context.scene.collection.objects.link(ob)
        ob.parent = e
        if side < 0:
            ob.rotation_euler = (0, 0, math.pi)


def run(root):
    obs = {k: build_wheel(k) for k in ('steer', 'drive', 'trailer')}
    specs = []
    tr = T.find('Tractor')
    for sd, sn in ((1, 'L'), (-1, 'R')):
        specs.append((f'Wheel_F{sn}', 'steer', V3((D.STEER_X, sd * D.STEER_Y, D.ZC)), sd))
        specs.append((f'Wheel_D1{sn}', 'drive', V3((D.D1_X, sd * D.DRIVE_Y, D.ZC)), sd))
        specs.append((f'Wheel_D2{sn}', 'drive', V3((D.D2_X, sd * D.DRIVE_Y, D.ZC)), sd))
    make_nodes(tr, specs, obs)
    trl = T.find('Trailer')
    specs = []
    for sd, sn in ((1, 'L'), (-1, 'R')):
        specs.append((f'Wheel_T1{sn}', 'trailer', V3((D.T1_X, sd * D.DRIVE_Y, D.ZC)), sd))
        specs.append((f'Wheel_T2{sn}', 'trailer', V3((D.T2_X, sd * D.DRIVE_Y, D.ZC)), sd))
    make_nodes(trl, specs, obs)
    for ob in obs.values():                                  # the templates are unlinked (their meshes live on in the nodes)
        bpy.data.objects.remove(ob, do_unlink=True)
