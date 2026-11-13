# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Cabin, doors, glass, mast fairing, aft cowl, tail boom, tail-boom fin/stabiliser carrier. All lofted from section tables read off the Robinson drawing and photographs (params.py)."""
import math
import numpy as np
import bpy
import bmesh
from mathutils import Vector
from . import kit, params as P
from .kit import crom, sgnpow, seg

# ---- cabin section tables (s = metres aft of the nose tip) -----------------------------------------------------------
ZC = [(0, 0.78), (0.35, 0.92), (0.8, 1.12), (1.3, 1.14), (2.45, 1.10)]
HU = [(0, 0.22), (0.35, 0.50), (0.8, 0.63), (1.1, 0.66), (1.5, 0.60), (2.0, 0.54), (2.45, 0.46)]
HD = [(0, 0.20), (0.35, 0.34), (0.8, 0.58), (1.3, 0.62), (2.45, 0.50)]
WW = [(0, 0.50), (0.5, 0.50), (1.0, 0.56), (1.6, 0.56), (2.1, 0.53), (2.45, 0.46)]
STATIONS = [0.012, 0.04, 0.08, 0.14, 0.22, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.98, 1.08, 1.20, 1.32, 1.44, 1.56, 1.68, 1.80, 1.95, 2.10, 2.25, 2.45]
S_DOOR0, S_DOOR1, S_WIN0, S_WIN1, S_WS1 = 0.98, 1.95, 1.10, 1.84, 0.98


def cabin_point(s, phi, nose=True):
    """point of the cabin section at s (m from the nose) and angle phi (0 = top centre, + toward the left side, pi = belly)"""
    f = math.sqrt(max(0.0, 1 - (1 - min(s / 0.35, 1.0)) ** 2)) if nose else 1.0
    zc, hu, hd, w = crom(ZC, s), crom(HU, s) * f, crom(HD, s) * f, crom(WW, s) * f
    n = 2.3 + 0.5 * min(s / 0.8, 1)
    c, sn = math.cos(phi), math.sin(phi)
    z = zc + (hu if c >= 0 else hd) * sgnpow(c, 2 / n)
    y = w * sgnpow(sn, 2 / n) * (1 - 0.20 * max(0.0, -c) ** 1.5)
    return Vector((P.XN + s, y, z))


def cabin_grid(N):
    S = STATIONS
    pts = np.zeros((len(S), N, 3))
    for k, s in enumerate(S):
        for j in range(N):
            pts[k, j] = cabin_point(s, 2 * math.pi * j / N)
    return pts


def build_cabin(root, M, N=None):
    N = N or seg(64, 32)
    N = N - N % 8
    Pt = cabin_grid(N)
    UV = kit.arc_uv(Pt, 0.5, 1.0)
    K = Pt.shape[0]

    def cls(k, j):
        s = (STATIONS[k] + STATIONS[k + 1]) / 2
        ph = 360.0 * (j + 0.5) / N
        left = ph < 180
        a = ph if left else 360 - ph       # fold: 0 top, 180 belly
        # windshield: from the nose to the door front, |phi| < 78 deg, centre cell (j = N-1 / 0) is the centre post
        if s < S_WS1 and a < 78 and s > 0.06:
            if j == N - 1 or j == 0 and False:
                return ('skin', 0)
            return ('wind', 0)
        if S_DOOR0 <= s < S_DOOR1 and 33 <= a < 113:
            side = 'R' if left else 'L'   # +Y is the aircraft's right in the build frame
            if S_WIN0 <= s < S_WIN1 and a < 85:
                return ('doorglass_' + side, 0)
            return ('door_' + side, 1 if a > 100 else 0)
        # livery: the lower body in the accent colour, a thin stripe above the waist
        if a > 118 or (100 <= a < 106):
            return ('skin', 1)
        return ('skin', 0)

    bms, vm = kit.loft_grid(Pt, UV, cls)
    objs = {}
    # nose cap and rear bulkhead in the skin
    bm = bms['skin']
    v0 = vm['skin']
    ring0 = [v0.get((0, j)) for j in range(N)]
    if all(ring0):
        f = bm.faces.new(ring0[::-1] if False else ring0)
        f.material_index = 1
    # rear bulkhead gets its own object (carpet-covered luggage wall)
    bk = bmesh.new()
    ring = [bk.verts.new(Pt[K - 1, j]) for j in range(N)]
    f = bk.faces.new(ring[::-1])
    f.material_index = 0
    for name, b in bms.items():
        if name.startswith('doorglass') or name == 'wind':
            kit.bm_solidify(b, 0.0035)
            ob = kit.from_bm({'wind': 'Glass_Windshield', 'doorglass_L': 'Glass_Door_L', 'doorglass_R': 'Glass_Door_R'}[name], b, [M['glass']], root)
        elif name.startswith('door'):
            kit.bm_solidify(b, 0.0028, inner_mat=2)
            ob = kit.from_bm('Door_' + name[-1] + '_skin', b, [M['paint'], M['accent'], M['int_grey']], root)
        else:
            kit.bm_solidify(b, 0.0028, inner_mat=2)
            ob = kit.from_bm('Cabin_Skin', b, [M['paint'], M['accent'], M['int_grey']], root)
        objs[name] = ob
    objs['bulkhead'] = kit.from_bm('Bulkhead_Rear', bk, [M['int_dark']], root, smooth=False)
    return objs, Pt


def door_split(root, objs, Pt, M):
    """pair each side's door skin and glass under a Door_X empty-pivot object: hinge at the front edge (pivot), a 4 mm panel gap, handle and window seal"""
    out = {}
    for side, sgn in (('R', 1), ('L', -1)):
        skin = objs['door_' + side]
        glass = objs['doorglass_' + side]
        # hinge line: the door's front edge at mid height
        x0 = P.XN + S_DOOR0
        pivot = Vector((x0, sgn * crom(WW, S_DOOR0) * 0.98, 1.05))
        # shrink the door's outline 4 mm towards its centre for the panel gap
        for ob in (skin, glass):
            c = Vector((P.XN + (S_DOOR0 + S_DOOR1) / 2, sgn * 0.5, 1.0))
            bm = bmesh.new()
            bm.from_mesh(ob.data)
            bb = [v for v in bm.verts if len([e for e in v.link_edges if len(e.link_faces) == 1]) > 0]
            for v in bb:
                d = c - v.co
                d.y = 0
                if d.length > 1e-6:
                    v.co += d.normalized() * 0.004
            bm.to_mesh(ob.data)
            bm.free()
        door = kit.empty('Door_' + side, tuple(pivot), root, kind='ARROWS', size=0.1)
        kit.tag(door, 'Zone_Cabin', 'intact', detach='hinged', hinge_axis='z', hinge_side='front')
        kit.reparent(skin, door)
        kit.reparent(glass, door)
        skin.name = 'Door_' + side + '_Skin'
        glass.name = 'Door_' + side + '_Glass'
        out[side] = door
        # handle: outer lever near the rear edge, and a rubber seal around the window
        bm = bmesh.new()
        hx, hy, hz = P.XN + S_DOOR1 - 0.18, sgn * (crom(WW, S_DOOR1 - 0.18) * (1 - 0.02) + 0.006), 0.98
        # the handle sits on the surface: recompute the point at the door's lower region
        p = cabin_point(S_DOOR1 - 0.18, sgn * math.radians(70))
        kit.bm_box(bm, (p.x, p.y + sgn * 0.012, p.z), (0.12, 0.016, 0.022), mat_idx=0)
        kit.bm_box(bm, (p.x + 0.04, p.y + sgn * 0.005, p.z), (0.03, 0.02, 0.03), mat_idx=0)
        h = kit.from_bm('Door_' + side + '_Handle', bm, [M['steel']], None)
        kit.reparent(h, door)
        # window rubber seal: a thin rectangular ring around the glass
        out['handle_' + side] = h
    return out


def build_pylon(root, M):
    """mast fairing ('pylon'): front edge nearly vertical, the rear edge raked; rounded rectangle sections lofted up the mast"""
    zs = [1.46, 1.70, 1.95, 2.20, 2.40, 2.44, 2.455]
    xf = -0.19
    N = seg(32, 16)
    rings = []
    for z in zs:
        t = (z - 1.46) / (2.44 - 1.46)
        xr = 0.80 + (0.42 - 0.80) * min(t, 1.0)
        a = (xr - xf) / 2
        cx = (xr + xf) / 2
        b = 0.35 + (0.17 - 0.35) * min(t, 1.0)
        k = 1.0 if z < 2.44 else 0.55 if z < 2.45 else 0.35
        pts = []
        for j in range(N):
            th = 2 * math.pi * j / N
            pts.append(Vector((cx + k * a * sgnpow(math.cos(th), 2 / 3.2), -k * b * sgnpow(math.sin(th), 2 / 3.2), z)))
        rings.append(pts)
    bm = bmesh.new()
    grid, vr = kit.bm_loft(bm, rings, cap_end=True)
    for row in grid:
        for f in row:
            f.smooth = True
    kit.bm_solidify(bm, 0.003, inner_mat=1)
    ob = kit.from_bm('Pylon_Fairing', bm, [M['paint'], M['int_grey']], root)
    # UV
    kit.planar_uv(ob, (0, 2), 0.5)
    return ob


def build_cowl(root, M):
    """aft deck above the engine: from the cabin's back wall (x 0.80) to the boom root (x 1.35); the side panels (lower) are separate removable cowls"""
    xs = [0.80, 0.88, 0.96, 1.04, 1.12, 1.20, 1.28, 1.36]
    N = seg(32, 16)
    N -= N % 8
    Pt = np.zeros((len(xs), N, 3))
    HW = [(0.8, 0.36), (1.0, 0.26), (1.36, 0.17)]
    TP = [(0.8, 1.54), (1.0, 1.62), (1.36, 1.77)]
    BT = [(0.8, 1.22), (1.0, 1.30), (1.36, 1.43)]
    for k, x in enumerate(xs):
        w, t, b = crom(HW, x), crom(TP, x), crom(BT, x)
        zc, h = (t + b) / 2, (t - b) / 2
        for j in range(N):
            ph = 2 * math.pi * j / N
            c, s = math.cos(ph), math.sin(ph)
            Pt[k, j] = (x, w * sgnpow(s, 0.7), zc + h * sgnpow(c, 0.7))
    UV = kit.arc_uv(Pt, 0.5, 1.0)

    def cls(k, j):
        ph = 360.0 * (j + 0.5) / N
        a = ph if ph < 180 else 360 - ph
        xm = (xs[k] + xs[k + 1]) / 2
        if 74 <= a < 130 and xm < 1.20:
            return ('panel_' + ('R' if ph < 180 else 'L'), 0)
        return ('cowl', 0)
    bms, vm = kit.loft_grid(Pt, UV, cls)
    out = {}
    for name, b in bms.items():
        kit.bm_solidify(b, 0.003, inner_mat=1)
        if name == 'cowl':
            out[name] = kit.from_bm('Cowl_Aft', b, [M['paint'], M['int_grey']], root)
        else:
            ob = kit.from_bm('Cowl_Panel_' + name[-1], b, [M['paint'], M['int_grey']], root)
            out[name] = ob
    return out


COWL_W = [(0.80, 0.46), (1.05, 0.45), (1.20, 0.37), (1.42, 0.24)]       # half width of the belly cowl round the engine
COWL_BOT = [(0.80, 0.60), (0.92, 0.51), (1.20, 0.52), (1.42, 0.56)]
COWL_TOP = [(0.80, 1.40), (1.00, 1.46), (1.42, 1.55)]                    # tops out inside the aft deck (its lower edge is the BT table in build_cowl), so no gap shows between them
COWL_END = 1.42


def cowl_half_width(x):
    return crom(COWL_W, x)


def build_cowl_belly(root, M, eng_x0, eng_zc):
    """belly cowl: closes the engine bay from the cabin's back wall (x 0.80) to a domed rear end (x 1.42..1.47) on both sides and underneath, and merges into the aft deck above. The belly has an oblong opening
    from x 0.94 to the rear, through which the muffler, the tail pipe, the sump and the lower part of the cooling-fan scroll show from below and behind (the engine sits low on the centre line, inside the cowl, the skids
    and the aft cabin); the sides are closed"""
    N = seg(32, 16)
    N -= N % 8
    xs = [0.80, 0.86, 0.92, 1.00, 1.08, 1.16, 1.24, 1.32, 1.38, COWL_END]
    rings = []

    def ring(x, k=1.0):
        w, t, b = crom(COWL_W, x if x <= COWL_END else COWL_END), crom(COWL_TOP, min(x, COWL_END)), crom(COWL_BOT, min(x, COWL_END))
        zc, h = (t + b) / 2, (t - b) / 2
        return [(x, k * w * sgnpow(math.sin(2 * math.pi * j / N), 0.9), zc + k * h * sgnpow(math.cos(2 * math.pi * j / N), 0.6 if math.cos(2 * math.pi * j / N) > 0 else 0.9)) for j in range(N)]
    for x in xs:
        rings.append(ring(x))
    for k in (0.8, 0.5, 0.2):                   # the domed rear end
        rings.append(ring(COWL_END + 0.05 * (1 - k * k), k))
    Pt = np.array(rings)
    UV = kit.arc_uv(Pt, 0.5, 1.0)

    def cls(k, j):
        ph = 360.0 * (j + 0.5) / N
        a = ph if ph < 180 else 360 - ph
        xm = Pt[k:k + 2, :, 0].mean()
        if a > 150 and xm >= 0.94:              # belly opening
            return None
        return ('cowl', 1 if a > 118 else 0)
    bms, vm = kit.loft_grid(Pt, UV, cls)
    b = bms['cowl']
    kit.bm_solidify(b, 0.003, inner_mat=2)
    return kit.from_bm('Cowl_Belly', b, [M['paint'], M['accent'], M['int_grey']], root)


def boom_centre(x):
    return Vector((x, 0.0, 1.60 + max(0.0, x - 1.35) * 0.085))


def boom_radius(x):
    return crom([(1.36, 0.175), (2.2, 0.145), (3.2, 0.105), (4.1, 0.080), (4.60, 0.074)], x)


def boom_grid(x0, x1, bend=0.0, kink_x=None, N=None):
    N = N or seg(24, 12)
    n = max(4, int(round((x1 - x0) / 0.12 * (kit.DET if kit.DET < 1 else 1))))
    xs = np.linspace(x0, x1, n + 1)
    Pt = np.zeros((len(xs), N, 3))
    for k, x in enumerate(xs):
        c, r = boom_centre(x), boom_radius(x)
        dz, dy = 0.0, 0.0
        if kink_x is not None and x > kink_x:       # bent boom: the part behind kink_x swings up and sideways
            d = x - kink_x
            dz = math.sin(bend) * d + 0.3 * d * d * 0.4
            dy = math.sin(bend * 0.6) * d * 1.2
        for j in range(N):
            ph = 2 * math.pi * j / N
            # slightly oval: taller than wide near the root
            Pt[k, j] = (x, c.y + dy + r * 0.92 * math.sin(ph), c.z + dz + r * 1.06 * math.cos(ph))
    return xs, Pt


def build_boom(root, M, x0, x1, name, end_cap=True, bend=0.0, kink_x=None):
    xs, Pt = boom_grid(x0, x1, bend, kink_x)
    UV = kit.arc_uv(Pt, 0.5, 1.0)

    def cls(k, j):
        ph = 360.0 * (j + 0.5) / Pt.shape[1]
        a = ph if ph < 180 else 360 - ph
        return ('b', 1 if a > 128 else 0)
    bms, vm = kit.loft_grid(Pt, UV, cls)
    b = bms['b']
    if end_cap:
        N = Pt.shape[1]
        ring = [vm['b'][(len(xs) - 1, j)] for j in range(N)]
        f = b.faces.new(ring[::-1])
        f.material_index = 1
    kit.bm_solidify(b, 0.0022, inner_mat=2)
    return kit.from_bm(name, b, [M['paint'], M['accent'], M['int_grey']], root)
