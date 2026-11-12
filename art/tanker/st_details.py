# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Stage details: livery decals laid on the curved tank by ray casts (company name, hazard placards in their holders, ID panels, capacity, no-smoking, data plate with rivets, the rear plate),
the painted two-tone stripes, and road grime / mud overlays (alpha decals from the borrowed soil and dust textures) on the tank's lower flank, the cab doors, the fenders and the wheel arches.

Nodes: Trailer > Livery (decals), Placards, Grime_Trailer;  Tractor > Grime_Tractor, Placard_Front.
"""
import math

import bmesh
import bpy
from mathutils.bvhtree import BVHTree

import parts as P
import st_tank as K
import tkit as T
from tkit import ATLAS, V3, Mesh


def bvh_of(name):
    ob = T.find(name)
    bm = bmesh.new()
    me = ob.data.copy()
    me.transform(ob.matrix_world)
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    return BVHTree.FromBMesh(bm)


def hit(bvh, x, z, s, off=0.0):
    r = bvh.ray_cast(V3((x, s * 3.0, z)), V3((0, -s, 0)))
    if r[0] is None:
        return None, None
    return r[0] + r[1] * off, r[1]


def laid(m, bvh, name, xc, zc, w, h, s, kind='decal', off=0.0025, nx=14, nz=6, to_x=None):
    """The livery rectangle `name` laid on the tank's side s (+1 left / -1 right): the decal is w along the length (reading toward the rear for the left side, toward the front for
    the right side, as seen by an onlooker), h high, centred at (xc, zc); a grid of ray hits, so it follows the curvature."""
    x, y, rw, rh = ATLAS[name]
    S = 2048.0
    u0, u1 = x / S, (x + rw) / S
    v0, v1 = 1 - (y + rh) / S, 1 - y / S
    dirx = -s                                          # onlooker's left-to-right along x: the left side (+y) is seen with the nose to the left
    rows = []
    for j in range(nz + 1):
        v = j / nz
        row = []
        for i in range(nx + 1):
            u = i / nx
            p, n = hit(bvh, xc + dirx * (u - 0.5) * w, zc + (v - 0.5) * h, s, off)
            if p is None:
                return
            row.append((p, u, v))
        rows.append(row)
    for j in range(nz):
        for i in range(nx):
            q = [rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]]
            vs = [m.bm.verts.new(p) for p, _, _ in q]
            uvs = [(u0 + (u1 - u0) * u, v0 + (v1 - v0) * v) for _, u, v in q]
            if s < 0:
                m.face(vs, kind, uvs)
            else:
                m.face(list(reversed(vs)), kind, list(reversed(uvs)))


def laid_grime(m, bvh, x0, x1, z0, z1, s, kind, nx=18, nz=4, off=0.003, flip_v=False):
    """A grime strip over x0..x1 and z0..z1 (z0 the bottom, where the dirt is thickest); v = 0 at the bottom."""
    rows = []
    for j in range(nz + 1):
        v = j / nz
        row = []
        for i in range(nx + 1):
            u = i / nx
            p, n = hit(bvh, x0 + (x1 - x0) * u, z0 + (z1 - z0) * v, s, off)
            if p is None:
                return
            row.append((p, u * (x1 - x0) / 1.4, 1 - v))
        rows.append(row)
    for j in range(nz):
        for i in range(nx):
            q = [rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]]
            vs = [m.bm.verts.new(p) for p, _, _ in q]
            uvs = [(u, v) for _, u, v in q]
            if s < 0:
                m.face(vs, kind, uvs)
            else:
                m.face(list(reversed(vs)), kind, list(reversed(uvs)))


def holder(m, c, nrm, ex, size=0.285):
    """A placard holder: a frame of four angle-strips round a diamond, riveted to the shell."""
    nrm, ex = V3(nrm).normalized(), V3(ex).normalized()
    ey = V3((0, 0, 1))
    h = size / 2
    corners = [c + ey * (-h * 1.0), c + ex * h, c + ey * h, c - ex * h]
    for k in range(4):
        a, b = corners[k], corners[(k + 1) % 4]
        m.tube([a + nrm * 0.004, b + nrm * 0.004], 0.0085, 'steel', seg=8, cap=True)
    for k in range(4):
        P.rivet(m, corners[k] + nrm * 0.004, nrm, 0.004, 'steel', seg=6)


def build_livery(bv):
    mL = Mesh()
    mH = Mesh()
    zc = K.ZC_TANK
    for s in (1, -1):
        xmid = 0.5 * (K.X_BARREL0 + K.X_BARREL1)
        # the company name across the middle of the tank, big
        laid(mL, bv, 'name_red', xmid + 0.2, zc + 0.20, 3.7, 0.925, s, nx=30, nz=8)
        laid(mL, bv, 'capacity', xmid + 0.2, zc - 0.28, 2.6, 0.41, s, nx=20, nz=4)
        laid(mL, bv, 'flammable_word', K.X_BARREL1 + 1.05, zc - 0.40, 1.35, 0.25, s, nx=14, nz=3)
        laid(mL, bv, 'gasoline', K.X_BARREL0 - 1.05, zc - 0.40, 1.35, 0.25, s, nx=14, nz=3)
        laid(mL, bv, 'nosmoking', K.X_BARREL1 + 1.0, zc + 0.30, 0.62, 0.155, s, nx=8, nz=3)
        laid(mL, bv, 'unit', K.X_BARREL0 - 0.80, zc + 0.35, 0.40, 0.20, s, nx=6, nz=3)
        laid(mL, bv, 'panel_1203', K.X_BARREL1 + 0.85, zc + 0.05, 0.30, 0.15, s, nx=6, nz=3)
        laid(mL, bv, 'panel_1203', K.X_BARREL0 - 0.85, zc + 0.05, 0.30, 0.15, s, nx=6, nz=3)
        # stripes round the tank, under and over the name
        laid(mL, bv, 'stripe_blue', xmid + 0.2, zc - 0.55, 8.2, 0.075, s, nx=64, nz=1)
        laid(mL, bv, 'stripe_red', xmid + 0.2, zc - 0.64, 8.2, 0.075, s, nx=64, nz=1)
        # hazard placards in holders at the ends of each side
        for x in (K.X_BARREL0 - 0.70, K.X_BARREL1 + 0.70):
            p, n = hit(bv, x, zc - 0.05 + 0.0, s, 0.0)
            if p is None:
                continue
            ex = V3((-s, 0, 0))
            holder(mH, p + n * 0.0, n, ex)
            laid(mH, bv, 'placard_flammable', x, zc - 0.05, 0.265, 0.265, s, nx=4, nz=4, off=0.0065)
        # the data plate with rivets, near the front of the right side (curb)
    p, n = hit(bv, K.X_BARREL0 - 1.9, zc - 0.20, -1, 0.0)
    if p is not None:
        mH.rbox(p + n * 0.003, (0.46, 0.011, 0.14), 0.003, 'steel', (V3((1, 0, 0)), V3((0, -1, 0)), V3((0, 0, 1))))
        laid(mH, bv, 'datapl', K.X_BARREL0 - 1.9, zc - 0.20, 0.44, 0.138, -1, nx=6, nz=2, off=0.0095)
        for dx in (-0.22, 0.22):
            for dz in (-0.06, 0.06):
                q, nn = hit(bv, K.X_BARREL0 - 1.9 + dx, zc - 0.20 + dz, -1, 0.0)
                if q is not None:
                    P.rivet(mH, q + nn * 0.0085, nn, 0.0045, 'steel', seg=6)
    # the rear: the plate, a placard holder on the head, the name (smaller)
    mr = Mesh()
    xr = K.X_REAR - 0.06
    mr.rbox(V3((xr + 0.036, 0, 1.18)), (0.014, 0.36, 0.20), 0.004, 'steel_dark')
    mr.decal('plate2', V3((xr + 0.0225, 0, 1.18)), V3((0, -1, 0)), V3((0, 0, 1)), 0.305, 0.152, 'plate_m', nrm=V3((-1, 0, 0)))
    return mL, mH, mr


def run(root):
    bv = bvh_of('TankShell')
    mL, mH, mr = build_livery(bv)
    mL.finish('Livery', T.find('Trailer'), sharp=60, box_uv=False)
    mH.finish('Placards', T.find('Trailer'), sharp=60, box_uv=False)
    mr.finish('Plate_R', T.find('Trailer'), sharp=60, box_uv=False)
    # grime: the lower flank of the tank (with mud thrown up behind the tandem), cab doors, fenders
    gm = Mesh()
    gmud = Mesh()
    for s in (1, -1):
        laid_grime(gm, bv, K.X_BARREL0 - 0.35, K.X_BARREL1 + 0.35, 1.34, 1.95, s, 'grime', nx=44, nz=5)
        laid_grime(gmud, bv, -8.2, K.X_BARREL1 + 0.35, 1.34, 1.80, s, 'grime_mud', nx=14, nz=4, off=0.004)
    gm.finish('Grime_Trailer', T.find('Trailer'), sharp=60, box_uv=False)
    gmud.finish('Mud_Trailer', T.find('Trailer'), sharp=60, box_uv=False)
    # the tractor: the doors' lower part and the flank of the hood are overlays cast on the cab body
    cb = T.find('Cab_Body')
    bm = bmesh.new()
    for nm in ('Cab_Body', 'Door_L_Body', 'Door_R_Body'):
        ob = T.find(nm)
        me = ob.data.copy()
        me.transform(ob.matrix_world)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    bvc = BVHTree.FromBMesh(bm)
    gt = Mesh()
    for s in (1, -1):
        laid_grime(gt, bvc, -0.55, 0.92, 1.10, 1.50, s, 'grime', nx=12, nz=4, off=0.003)
    gt.finish('Grime_Tractor', T.find('Tractor'), sharp=60, box_uv=False)

