# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Landing gear, engine bay, drive, main rotor, tail group, tail rotor, lights, antennas, registration decals. Build frame: nose -X, +Y aircraft right (see interior.py)."""
import math
import numpy as np
import bpy
import bmesh
from mathutils import Vector, Matrix
from . import kit, params as P
from .kit import seg, crom, sgnpow
from .fuselage import boom_centre, boom_radius, cabin_point
from .interior import rbox

HUB_C = Vector((0.0, 0.0, P.HUB_Z - 0.06))          # centre of the teeter hinge
TR_HUB = Vector((4.40, -0.215, 0.0))                # z filled from the boom centre line


# ============================================================ skids
def skid_profile(sgn):
    """skid tube centre line: toe turned up, straight along the ground, heel turned up (x from the toe -1.65 to the heel 0.75)"""
    y = sgn * 0.925
    return [(-1.65, y, 0.20), (-1.55, y, 0.10), (-1.40, y, 0.042), (0.55, y, 0.042), (0.68, y, 0.08), (0.75, y, 0.17)]


def cross_profile(x, sgn=1):
    """one half of a cross tube: from the skid (z 0.042) up the splayed leg to the belly and on to the centre line"""
    return [(x, sgn * 0.925, 0.05), (x, sgn * 0.88, 0.12), (x, sgn * 0.74, 0.27), (x, sgn * 0.56, 0.40), (x, sgn * 0.40, 0.46), (x, sgn * 0.22, 0.482), (x, 0.0, 0.485)]


def build_skids(ctx):
    root, M = ctx['root'], ctx['M']
    out = {}
    for side, sgn in (('R', 1), ('L', -1)):
        bm = bmesh.new()
        pts = kit.smooth_poly(skid_profile(sgn), 5)
        kit.bm_tube(bm, pts, 0.036, n=14, mat_idx=0)
        # skid shoe: flat wear strip under the tube, heel and toe caps
        kit.bm_box(bm, (-0.45, sgn * 0.925, 0.006), (1.90, 0.06, 0.012), mat_idx=1)
        # step plate on the skid at the door: a bracket tube and a flat tread with a grip pattern in the mesh
        ob = kit.from_bm('Skid_' + side, bm, [M['skid'], M['alu']], root)
        kit.tag(ob, 'Zone_Skids', 'intact', detach='part')
        out['skid_' + side] = ob
    for nm, x in (('Cross_Front', -0.77), ('Cross_Rear', 0.50)):
        bm = bmesh.new()
        pts = kit.smooth_poly(list(reversed(cross_profile(x, -1))) + cross_profile(x, 1)[1:], 4)
        kit.bm_tube(bm, pts, 0.0285, n=12, mat_idx=0)
        # saddle clamps where the tube meets each skid
        for sgn in (1, -1):
            kit.bm_cyl(bm, (x - 0.045, sgn * 0.925, 0.042), (x + 0.045, sgn * 0.925, 0.042), 0.048, 0.048, n=14, mat_idx=1)
        # fuselage attachment fittings (straps round the tube under the belly)
        for yy in (-0.30, 0.30):
            kit.bm_box(bm, (x, yy, 0.50), (0.07, 0.06, 0.05), mat_idx=1)
        ob = kit.from_bm(nm, bm, [M['skid'], M['alu']], root)
        kit.tag(ob, 'Zone_Skids', 'intact', detach='part')
        out[nm.lower()] = ob
    # steps: a bracket from the skid up and a small tread, both sides
    for side, sgn in (('R', 1), ('L', -1)):
        bm = bmesh.new()
        kit.bm_tube(bm, [(-0.30, sgn * 0.925, 0.07), (-0.30, sgn * 0.80, 0.19), (-0.30, sgn * 0.70, 0.30)], 0.014, n=8, mat_idx=0)
        rbox(bm, (-0.30, sgn * 0.72, 0.305), (0.22, 0.14, 0.012), 0.004, 1)
        ob = kit.from_bm('Step_' + side, bm, [M['alu'], M['steel']], root)
        kit.tag(ob, 'Zone_Skids', 'intact', detach='part')
        out['step_' + side] = ob
    # ground handling wheels: stub axles on the rear cross tube, wheels folded up beside the belly
    for side, sgn in (('R', 1), ('L', -1)):
        bm = bmesh.new()
        kit.bm_cyl(bm, (0.50, sgn * 0.30, 0.50), (0.50, sgn * 0.37, 0.50), 0.014, 0.014, n=8, mat_idx=0)
        kit.bm_cyl(bm, (0.50, sgn * 0.38, 0.50), (0.50, sgn * 0.45, 0.50), 0.075, 0.075, n=int(18), mat_idx=1)
        kit.bm_cyl(bm, (0.50, sgn * 0.45, 0.50), (0.50, sgn * 0.452, 0.50), 0.04, 0.04, n=12, mat_idx=2)
        ob = kit.from_bm('GroundWheel_' + side, bm, [M['steel'], M['rubber'], M['alu']], root)
        kit.tag(ob, 'Zone_Skids', 'intact', detach='part')
        out['wheel_' + side] = ob
    return out


# ============================================================ engine bay
def fins(bm, p0, p1, r, n_fin=7, mat_idx=0, r_fin=1.28):
    p0, p1 = Vector(p0), Vector(p1)
    d = (p1 - p0)
    k = seg(n_fin, 3)
    for i in range(k):
        a = p0 + d * (i / k)
        b = p0 + d * ((i + 0.55) / k)
        kit.bm_cyl(bm, a, b, r * r_fin, r * r_fin, n=14, mat_idx=mat_idx)
        kit.bm_cyl(bm, b, p0 + d * ((i + 1) / k), r, r, n=14, caps=False, mat_idx=mat_idx)


def build_engine(ctx):
    """Lycoming O-360 (Beta II; the standard R22 has the O-320): horizontally opposed four, crank axis fore-aft (the fan drum on the rear end, as seen in the photographs), vee-belt
    sheave on the front, with its mount tubes, exhaust, carburettor, magnetos, oil sump, hoses."""
    root, M = ctx['root'], ctx['M']
    out = {}
    x0 = 1.18      # crankcase centre
    zc = 0.84
    bm = bmesh.new()
    rbox(bm, (x0, 0, zc), (0.38, 0.30, 0.26), 0.04, 0)                           # crankcase
    rbox(bm, (x0 + 0.02, 0, zc - 0.17), (0.30, 0.26, 0.09), 0.02, 0)             # oil sump
    rbox(bm, (x0 + 0.24, 0, zc + 0.02), (0.14, 0.26, 0.20), 0.03, 0)             # accessory case
    for sgn in (1, -1):
        for dx in (-0.10, 0.12):
            xx = x0 + dx
            fins(bm, (xx, sgn * 0.14, zc), (xx, sgn * 0.33, zc), 0.058, 7, 0)       # barrel with cooling fins
            kit.bm_cyl(bm, (xx, sgn * 0.33, zc), (xx, sgn * 0.40, zc), 0.07, 0.065, n=16, mat_idx=0)   # head
            rbox(bm, (xx, sgn * 0.37, zc + 0.07), (0.09, 0.05, 0.045), 0.01, 1)      # rocker cover
            kit.bm_cyl(bm, (xx + 0.06, sgn * 0.31, zc + 0.03), (xx + 0.06, sgn * 0.19, zc + 0.04), 0.008, 0.008, n=6, mat_idx=2)   # push-rod tube
            kit.bm_cyl(bm, (xx, sgn * 0.38, zc - 0.07), (xx, sgn * 0.38, zc - 0.20), 0.022, 0.022, n=8, mat_idx=3)               # exhaust port stub
    ob = kit.from_bm('Engine_Block', bm, [M['engine'], M['engine_dark'], M['steel'], M['exhaust']], root)
    kit.tag(ob, 'Zone_Engine', 'intact', detach='part')
    out['block'] = ob
    # cooling fan drum on the rear end, vee-belt sheave on the front
    bm = bmesh.new()
    kit.bm_cyl(bm, (x0 + 0.31, 0, zc), (x0 + 0.50, 0, zc), 0.26, 0.26, n=32, mat_idx=0)
    kit.bm_cyl(bm, (x0 + 0.50, 0, zc), (x0 + 0.51, 0, zc), 0.20, 0.20, n=28, mat_idx=1)
    for i in range(seg(12, 6)):
        a = 2 * math.pi * i / seg(12, 6)
        kit.bm_cyl(bm, (x0 + 0.505, math.cos(a) * 0.04, zc + math.sin(a) * 0.04), (x0 + 0.51, math.cos(a) * 0.19, zc + math.sin(a) * 0.19), 0.004, 0.004, n=4, mat_idx=2)
    ob = kit.from_bm('Engine_FanDrum', bm, [M['engine_dark'], M['steel_dark'], M['steel']], root)
    kit.tag(ob, 'Zone_Engine', 'intact', detach='part')
    out['fan'] = ob
    # lower sheave (front) and the 4 vee-belts running up to the upper sheave in the cowl; main-rotor drive shaft forward to the transmission
    bm = bmesh.new()
    xs = x0 - 0.30
    kit.bm_cyl(bm, (xs, 0, zc), (xs + 0.11, 0, zc), 0.15, 0.15, n=28, mat_idx=0)
    zu = 1.45
    kit.bm_cyl(bm, (xs + 0.0, 0, zu), (xs + 0.11, 0, zu), 0.095, 0.095, n=24, mat_idx=0)
    for i in range(4):
        xx = xs + 0.02 + i * 0.022
        for sgn in (1, -1):
            kit.bm_box(bm, (xx, sgn * 0.12, (zc + zu) / 2), (0.016, 0.014, zu - zc), mat_idx=1)
        kit.bm_cyl(bm, (xx - 0.008, 0, zc - 0.15), (xx + 0.008, 0, zc - 0.15), 0.0, 0.0, n=3, mat_idx=1) if False else None
    kit.bm_cyl(bm, (xs - 0.55, 0, zu), (xs, 0, zu), 0.025, 0.025, n=10, mat_idx=2)       # drive shaft to the main transmission
    ob = kit.from_bm('Engine_Belts', bm, [M['steel_dark'], M['belt_drive'], M['steel']], root)
    kit.tag(ob, 'Zone_Engine', 'intact', detach='part')
    out['belts'] = ob
    # exhaust: two stubs down into a muffler under the engine, tail pipe out to the rear on the right
    bm = bmesh.new()
    for sgn in (1, -1):
        for dx in (-0.10, 0.12):
            kit.bm_tube(bm, kit.smooth_poly([(x0 + dx, sgn * 0.38, zc - 0.20), (x0 + dx, sgn * 0.40, zc - 0.28), (x0 + 0.02, sgn * 0.22, 0.58)], 4), 0.020, n=10, mat_idx=0)
    rbox(bm, (x0 + 0.05, 0, 0.52), (0.40, 0.26, 0.10), 0.03, 0)
    kit.bm_tube(bm, kit.smooth_poly([(x0 + 0.20, 0.08, 0.50), (x0 + 0.38, 0.16, 0.46), (x0 + 0.58, 0.22, 0.52)], 4), 0.028, n=12, mat_idx=0)
    ob = kit.from_bm('Engine_Exhaust', bm, [M['exhaust']], root)
    kit.tag(ob, 'Zone_Engine', 'intact', detach='part')
    out['exhaust'] = ob
    # carburettor with its intake box below the sump, magnetos, hoses and wiring
    bm = bmesh.new()
    rbox(bm, (x0 - 0.04, 0, zc - 0.28), (0.14, 0.12, 0.10), 0.02, 0)
    rbox(bm, (x0 + 0.30, 0.10, zc + 0.12), (0.07, 0.07, 0.07), 0.015, 1)
    rbox(bm, (x0 + 0.30, -0.10, zc + 0.12), (0.07, 0.07, 0.07), 0.015, 1)
    for sgn in (1, -1):
        kit.bm_tube(bm, kit.smooth_poly([(x0 - 0.02, sgn * 0.04, zc - 0.28), (x0 - 0.02, sgn * 0.18, zc - 0.22), (x0 + 0.1, sgn * 0.36, zc - 0.12)], 4), 0.014, n=8, mat_idx=2)
        kit.bm_tube(bm, kit.smooth_poly([(x0 + 0.30, sgn * 0.10, zc + 0.15), (x0 + 0.2, sgn * 0.25, zc + 0.20), (x0 + 0.02, sgn * 0.37, zc + 0.09)], 4), 0.006, n=6, mat_idx=2)
    ob = kit.from_bm('Engine_Accessories', bm, [M['engine_dark'], M['steel_dark'], M['hose']], root)
    kit.tag(ob, 'Zone_Engine', 'intact', detach='part')
    out['acc'] = ob
    # mount: steel tube cage from the cabin's back wall to the engine and the boom root
    bm = bmesh.new()
    tubes = [
        [(0.84, 0.36, 0.62), (1.06, 0.40, 0.74)], [(0.84, -0.36, 0.62), (1.06, -0.40, 0.74)], [(0.84, 0.36, 1.12), (1.20, 0.36, 1.02)], [(0.84, -0.36, 1.12), (1.20, -0.36, 1.02)],
        [(1.06, 0.40, 0.74), (1.48, 0.30, 0.62)], [(1.06, -0.40, 0.74), (1.48, -0.30, 0.62)], [(1.06, 0.40, 0.74), (1.20, 0.36, 1.02)], [(1.06, -0.40, 0.74), (1.20, -0.36, 1.02)],
        [(1.20, 0.36, 1.02), (1.40, 0.20, 1.20)], [(1.20, -0.36, 1.02), (1.40, -0.20, 1.20)], [(1.48, 0.30, 0.62), (1.55, 0.0, 0.70)], [(1.48, -0.30, 0.62), (1.55, 0.0, 0.70)],
        [(1.48, 0.30, 0.62), (1.40, 0.20, 1.20)], [(1.48, -0.30, 0.62), (1.40, -0.20, 1.20)], [(0.84, 0.36, 0.62), (0.84, 0.36, 1.12)], [(0.84, -0.36, 0.62), (0.84, -0.36, 1.12)],
        [(0.84, 0.36, 0.62), (1.06, -0.40, 0.74)], [(0.84, -0.36, 0.62), (1.06, 0.40, 0.74)], [(1.06, 0.40, 0.74), (1.0, 0.1, 0.55)], [(1.06, -0.40, 0.74), (1.0, -0.1, 0.55)],
    ]
    for t in tubes:
        kit.bm_tube(bm, t, 0.014, n=8, mat_idx=0)
    ob = kit.from_bm('Engine_Mount', bm, [M['steel_dark']], root)
    kit.tag(ob, 'Zone_Engine', 'intact', detach='part')
    out['mount'] = ob
    return out


# ============================================================ blades
def blade_mesh(M, r0, r1, chord, twist_deg, cone_deg, mat, name_uv_span=None, ragged=0.0, seed=1, tip_round=True, thick=0.15, torn_te=0.0, root_chord=None):
    """airfoil blade along +Y from r0 to r1 about the pivot at the origin. LE toward -X (blade moving CCW seen from above), pitch axis at quarter chord; twist linear root->tip (deg, negative = nose down),
    cone angle up; ragged = amplitude of a broken-off end; returns (bm, ring list)"""
    full = name_uv_span or (r0, r1)
    rs = np.random.RandomState(seed)
    n_s = seg(34, 14)
    stations = list(np.linspace(r0, r1, n_s))
    sect = kit.naca4(thick, seg(14, 6))
    n_pts = len(sect)
    rings = []
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    verts = []
    for ri, r in enumerate(stations):
        ft = (r - full[0]) / (full[1] - full[0])
        tw = math.radians(twist_deg * ft)
        c = chord * (1.0 if not tip_round else (1.0 if r < r1 - 0.05 else max(0.55, 1 - (r - (r1 - 0.05)) / 0.05 * 0.45))) if root_chord is None else (root_chord + (chord - root_chord) * ft)
        row = []
        for (xc, zc) in sect:
            lx, lz = (xc - 0.25) * c, zc * c
            x, z = lx * math.cos(tw) + lz * math.sin(tw), -lx * math.sin(tw) + lz * math.cos(tw)
            y = r
            z += r * math.sin(math.radians(cone_deg))
            if ragged and ri >= n_s - 4:
                k = (ri - (n_s - 4)) / 3.0
                jag = (rs.rand() - 0.3) * ragged * (0.3 + 0.7 * k)
                y += jag + (0.5 * ragged if x > 0 else -0.2 * ragged) * k
                z += (rs.rand() - 0.5) * 0.03 * k
            row.append(bm.verts.new((x, y, z)))
        verts.append(row)
    for k in range(len(stations) - 1):
        for j in range(n_pts):
            jj = (j + 1) % n_pts
            f = bm.faces.new((verts[k][j], verts[k][jj], verts[k + 1][jj], verts[k + 1][j]))
            f.smooth = True
            f.material_index = 0
            for lp in f.loops:
                idx = (verts[k].index(lp.vert) if lp.vert in verts[k] else verts[k + 1].index(lp.vert))
                ft = (lp.vert.co.y - full[0]) / (full[1] - full[0])
                lp[uvl].uv = (ft, sect[idx][0])
    for ring in (verts[0], verts[-1]):
        f = bm.faces.new(ring if ring is verts[-1] else ring[::-1])
        f.smooth = False
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    return bm


def build_main_rotor(ctx):
    root, M = ctx['root'], ctx['M']
    out = {}
    hub = HUB_C
    # mast: from the pylon top to the hub, boot at the base (static)
    bm = bmesh.new()
    kit.bm_cyl(bm, (0, 0, 2.38), (0, 0, 2.46), 0.085, 0.07, n=24, mat_idx=1)
    kit.bm_cyl(bm, (0, 0, 2.44), (0, 0, 2.58), 0.048, 0.044, n=20, mat_idx=0)
    kit.bm_cyl(bm, (0, 0, 2.46), (0, 0, 2.52), 0.062, 0.062, n=20, mat_idx=2)
    ob = kit.from_bm('Mast', bm, [M['steel'], M['rubber'], M['alu']], root)
    kit.tag(ob, 'Zone_MainRotor', 'intact', detach='part')
    out['mast'] = ob
    # spin node at the hub: everything that turns with the rotor lives under it; the blades under the teeter node
    spin = kit.empty('Rotor_Spin', tuple(hub), root, kind='CIRCLE', size=0.5, spin_axis='+Y (glb); counter-clockwise seen from above', rpm_nominal=530)
    teeter = kit.empty('Rotor_Teeter', tuple(hub), root, kind='ARROWS', size=0.25, teeter_axis='glb X (fore-aft)', note='rotate +-8 deg about the fore-aft axis; blades A and B are its children')
    kit.reparent(teeter, spin)
    # head: teeter housing, hinge bolt along fore-aft, blade grips (feathering sleeves) along the span, pitch horns and links
    bm = bmesh.new()
    rbox(bm, (0, 0, 0.0), (0.16, 0.36, 0.10), 0.02, 0)
    kit.bm_cyl(bm, (-0.09, 0, 0.0), (0.09, 0, 0.0), 0.022, 0.022, n=12, mat_idx=1)
    rbox(bm, (0, 0, -0.07), (0.12, 0.16, 0.05), 0.015, 0)
    for sgn in (1, -1):
        kit.bm_cyl(bm, (0.0, sgn * 0.18, 0.0), (0.0, sgn * 0.52, 0.0), 0.045, 0.040, n=16, mat_idx=0)       # grip
        kit.bm_box(bm, (-0.07 * sgn, sgn * 0.30, 0.07), (0.03, 0.03, 0.10), mat_idx=1)                        # pitch horn
        kit.bm_cyl(bm, (-0.07 * sgn, sgn * 0.30, 0.12), (-0.07 * sgn, sgn * 0.30, -0.22), 0.007, 0.007, n=6, mat_idx=1)  # pitch link
    ob = kit.from_bm('Rotor_Hub', bm, [M['steel_dark'], M['steel']], root)
    kit.place(ob, tuple(hub))
    kit.reparent(ob, spin)
    kit.tag(ob, 'Zone_MainRotor', 'intact', detach='part')
    out['hub'] = ob
    # blades: A to the right (+Y), B to the left (-Y, the same blade turned 180 deg about the vertical)
    for nm, sgn in (('A', 1), ('B', -1)):
        bm = blade_mesh(M, 0.55, P.ROTOR_R, P.ROTOR_CHORD, -8.0, 1.5, M['blade'])
        if sgn < 0:
            bmesh.ops.rotate(bm, verts=list(bm.verts), cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi, 3, 'Z'))
        ob = kit.from_bm('Blade_' + nm, bm, [M['blade']], root)
        kit.place(ob, tuple(hub))
        kit.reparent(ob, teeter)
        kit.tag(ob, 'Zone_MainRotor', 'intact', detach='blade', pivot='hub', feather_axis='along the blade')
        out['blade_' + nm] = ob
    # blur disc: a flat disc at the blade height with a radial alpha ramp; the game fades it in with rotor speed (nodes Rotor_Disc)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    n = seg(64, 24)
    c = bm.verts.new((0, 0, 0))
    ring = [bm.verts.new((math.cos(2 * math.pi * i / n) * P.ROTOR_R, math.sin(2 * math.pi * i / n) * P.ROTOR_R, P.ROTOR_R * math.sin(math.radians(1.5)))) for i in range(n)]
    for i in range(n):
        j = (i + 1) % n
        f = bm.faces.new((c, ring[i], ring[j]))
        for lp in f.loops:
            lp[uvl].uv = (0.5 + lp.vert.co.x / P.ROTOR_R / 2, 0.5 + lp.vert.co.y / P.ROTOR_R / 2)
    ob = kit.from_bm('Rotor_Disc', bm, [M['disc']], root, smooth=False)
    kit.place(ob, tuple(hub))
    kit.reparent(ob, spin)
    kit.tag(ob, 'Zone_MainRotor', 'intact', fx='blur', note='show when the rotor turns fast; hide the blades then')
    out['disc'] = ob
    out['spin'] = spin
    out['teeter'] = teeter
    return out


# ============================================================ tail group
def build_tail(ctx):
    root, M = ctx['root'], ctx['M']
    out = {}
    bz = boom_centre(4.40).z
    TR = Vector((4.40, -0.215, bz))
    ctx['tr_hub'] = TR
    # --- vertical fin with the lower tail guard fin (all one plate), paint main / accent
    bm = bmesh.new()
    fin_poly = [(4.40, 2.37), (4.58, 2.37), (4.63, 1.96), (4.63, 1.80), (4.60, 1.40), (4.52, 1.27), (4.38, 1.27), (4.31, 1.62), (4.27, 1.92)]
    kit.bm_plate(bm, fin_poly, -0.016, 0.016, 0.006, 0)
    # mark the lower part in the accent colour
    for f in bm.faces:
        if f.calc_center_median().z < 1.80:
            f.material_index = 1
    ob = kit.from_bm('Fin', bm, [M['paint'], M['accent']], root)
    kit.planar_uv(ob, (0, 2), 1.0)
    kit.tag(ob, 'Zone_TailBoom', 'intact', detach='part')
    out['fin'] = ob
    # tail skid (guard): bent tube from the fin foot rearward and down; rubber tip
    bm = bmesh.new()
    kit.bm_tube(bm, kit.smooth_poly([(4.50, 0.0, 1.30), (4.62, 0.0, 1.16), (4.78, 0.0, 1.10), (4.90, 0.0, 1.14)], 5), 0.017, n=10, mat_idx=0)
    kit.bm_cyl(bm, (4.90, 0, 1.14), (4.95, 0, 1.17), 0.021, 0.021, n=10, mat_idx=1)
    ob = kit.from_bm('Tail_Guard', bm, [M['alu'], M['rubber']], root)
    kit.tag(ob, 'Zone_TailBoom', 'intact', detach='part')
    out['guard'] = ob
    # --- horizontal stabiliser (symmetric, with the two vertical end plates striped red/white as photographed) and its brackets
    bm = bmesh.new()
    sx0, sx1, sz = 3.58, 3.78, 1.665
    n = 14
    airf = kit.naca4(0.10, n)
    # a thin symmetric plate, span 0.87
    vs = []
    for yy in (-P.STAB_SPAN / 2, P.STAB_SPAN / 2):
        ring = []
        for (xc, zc) in airf:
            ring.append(bm.verts.new((sx0 + xc * (sx1 - sx0), yy, sz + zc * (sx1 - sx0))))
        vs.append(ring)
    for j in range(len(airf)):
        jj = (j + 1) % len(airf)
        f = bm.faces.new((vs[0][j], vs[1][j], vs[1][jj], vs[0][jj]))
        f.smooth = True
    for ring, rev in ((vs[0], True), (vs[1], False)):
        bm.faces.new(ring[::-1] if rev else ring)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    ob = kit.from_bm('Stabilizer', bm, [M['paint']], root)
    kit.tag(ob, 'Zone_TailBoom', 'intact', detach='part')
    out['stab'] = ob
    for sgn in (1, -1):
        bm = bmesh.new()
        nb = 6
        for i in range(nb):
            z0 = 1.52 + i * (1.82 - 1.52) / nb
            poly = [(3.56, z0), (3.80, z0), (3.80, z0 + (1.82 - 1.52) / nb), (3.56, z0 + (1.82 - 1.52) / nb)]
            fs = kit.bm_plate(bm, poly, sgn * (P.STAB_SPAN / 2) - 0.005, sgn * (P.STAB_SPAN / 2) + 0.005, 0.0015, i % 2)
        ob = kit.from_bm('StabPlate_' + ('R' if sgn > 0 else 'L'), bm, [M['trim'], M['paint']], root)
        kit.tag(ob, 'Zone_TailBoom', 'intact', detach='part')
        out['plate_' + ('R' if sgn > 0 else 'L')] = ob
    bm = bmesh.new()
    for sgn in (1, -1):
        kit.bm_tube(bm, [(3.60, 0.0, 1.70), (3.66, sgn * 0.20, 1.67)], 0.008, n=6, mat_idx=0)
    kit.bm_box(bm, (3.68, 0, 1.72), (0.14, 0.05, 0.05), mat_idx=0)
    ob = kit.from_bm('Stab_Bracket', bm, [M['steel']], root)
    kit.tag(ob, 'Zone_TailBoom', 'intact')
    out['stab_bracket'] = ob
    # --- tail rotor gearbox + drive-shaft cover (the cover is the exposed tube between the fan housing and the boom root, and the clamped joint covers along the boom)
    bm = bmesh.new()
    kit.bm_cyl(bm, (4.40, -0.02, bz), (4.40, -0.15, bz), 0.052, 0.058, n=20, mat_idx=0)
    kit.bm_cyl(bm, (4.40, -0.15, bz), (4.40, -0.19, bz), 0.040, 0.034, n=16, mat_idx=0)
    kit.bm_cyl(bm, (4.40, -0.19, bz), (4.40, -0.205, bz), 0.060, 0.060, n=20, mat_idx=1)
    rbox(bm, (4.47, -0.06, bz), (0.12, 0.10, 0.09), 0.02, 0)
    kit.bm_tube(bm, [(4.44, -0.02, bz + 0.05), (4.52, -0.05, bz + 0.07), (4.55, -0.08, bz + 0.05)], 0.007, n=6, mat_idx=1)    # pitch-change link
    ob = kit.from_bm('TR_Gearbox', bm, [M['alu'], M['steel_dark']], root)
    kit.tag(ob, 'Zone_TailRotor', 'intact', detach='part')
    out['tr_gb'] = ob
    bm = bmesh.new()
    kit.bm_cyl(bm, (1.40, 0, 1.50), (3.30, 0, boom_centre(3.30).z - 0.0), 0.0, 0.0, n=3) if False else None
    # exposed shaft cover with clamps and bellows rings at the boom root (visible where the shaft enters the boom)
    kit.bm_cyl(bm, (1.32, 0.0, 1.46), (1.52, 0.0, 1.50), 0.036, 0.034, n=14, mat_idx=0)
    for i in range(seg(6, 3)):
        xx = 1.33 + i * 0.03
        kit.bm_cyl(bm, (xx, 0, 1.46 + (xx - 1.32) * 0.2), (xx + 0.012, 0, 1.46 + (xx + 0.012 - 1.32) * 0.2), 0.043, 0.043, n=14, mat_idx=1)
    ob = kit.from_bm('Driveshaft_Cover', bm, [M['steel_dark'], M['rubber']], root)
    kit.tag(ob, 'Zone_TailBoom', 'intact', detach='part')
    out['dscover'] = ob
    # driveshaft inside the boom (visible when the boom is torn open), in two sections
    bm = bmesh.new()
    kit.bm_cyl(bm, (1.50, 0, 1.50), (4.40, 0, bz), 0.016, 0.016, n=8, mat_idx=0)
    ob = kit.from_bm('Driveshaft', bm, [M['steel']], root)
    kit.tag(ob, 'Zone_TailBoom', 'intact')
    out['driveshaft'] = ob
    # beacon (red dome) and tail strobe, on the boom top near the break and on the fin tip; antenna whip aft of the pylon; tie-down eye under the boom
    bm = bmesh.new()
    zb = boom_centre(3.38).z + boom_radius(3.38) * 1.06
    kit.bm_cyl(bm, (3.38, 0, zb - 0.01), (3.38, 0, zb + 0.015), 0.032, 0.03, n=14, mat_idx=0)
    ob = kit.from_bm('Beacon_Base', bm, [M['alu']], root)
    kit.tag(ob, 'Zone_TailBoom', 'intact')
    out['beacon_base'] = ob
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg(16, 8), v_segments=seg(8, 4), radius=0.032)
    for v in bm.verts:
        v.co.z = max(v.co.z, 0) * 0.9
        v.co += Vector((3.38, 0, zb + 0.015))
    for f in bm.faces:
        f.smooth = True
    ob = kit.from_bm('Light_Beacon', bm, [M['lamp_beacon']], root)
    kit.tag(ob, 'Zone_TailBoom', 'intact', light='beacon red anti-collision')
    out['light_beacon'] = ob
    return out


def build_tail_rotor(ctx):
    root, M = ctx['root'], ctx['M']
    out = {}
    TR = ctx['tr_hub']
    spin = kit.empty('TailRotor_Spin', tuple(TR), root, kind='CIRCLE', size=0.3, spin_axis='glb Z (to the left of the aircraft)', note='top blade moves toward the nose (UNVERIFIED direction)')
    bm = bmesh.new()
    kit.bm_cyl(bm, (0, -0.0, 0), (0, -0.05, 0), 0.040, 0.040, n=16, mat_idx=0)
    kit.bm_cyl(bm, (0, -0.03, -0.095), (0, -0.03, 0.095), 0.016, 0.016, n=10, mat_idx=0)
    for sgn in (1, -1):
        kit.bm_cyl(bm, (0, -0.03, sgn * 0.04), (0, -0.03, sgn * 0.14), 0.020, 0.017, n=10, mat_idx=1)
    ob = kit.from_bm('TR_Hub', bm, [M['steel_dark'], M['steel']], root)
    kit.place(ob, tuple(TR))
    kit.reparent(ob, spin)
    kit.tag(ob, 'Zone_TailRotor', 'intact', detach='part')
    out['hub'] = ob
    # blades: chord 0.115 (R22 tail rotor blades are wide), root cut-out 0.09, NACA 0012; top blade LE toward the nose (-X)
    for nm, sgn in (('A', 1), ('B', -1)):
        bm = blade_mesh(M, 0.10, P.TAIL_ROTOR_D / 2, 0.115, 0.0, 0.0, M['tblade'], thick=0.12, tip_round=True)
        # the blade was made along +Y: stand it up (+Y -> +Z) and give it pitch 12 deg about its span axis
        bmesh.ops.rotate(bm, verts=list(bm.verts), cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'X'))
        bmesh.ops.rotate(bm, verts=list(bm.verts), cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(12), 3, 'Z'))
        if sgn < 0:
            bmesh.ops.rotate(bm, verts=list(bm.verts), cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi, 3, 'Y'))
        ob = kit.from_bm('TR_Blade_' + nm, bm, [M['tblade']], root)
        kit.place(ob, (TR.x, TR.y - 0.03, TR.z))
        kit.reparent(ob, spin)
        kit.tag(ob, 'Zone_TailRotor', 'intact', detach='blade', pivot='hub')
        out['blade_' + nm] = ob
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    n = seg(36, 16)
    c = bm.verts.new((0, 0, 0))
    ring = [bm.verts.new((math.cos(2 * math.pi * i / n) * P.TAIL_ROTOR_D / 2, 0, math.sin(2 * math.pi * i / n) * P.TAIL_ROTOR_D / 2)) for i in range(n)]
    for i in range(n):
        j = (i + 1) % n
        f = bm.faces.new((c, ring[j], ring[i]))
        for lp in f.loops:
            lp[uvl].uv = (0.5 + lp.vert.co.x / P.TAIL_ROTOR_D, 0.5 + lp.vert.co.z / P.TAIL_ROTOR_D)
    ob = kit.from_bm('TailRotor_Disc', bm, [M['disc']], root, smooth=False)
    kit.place(ob, (TR.x, TR.y - 0.03, TR.z))
    kit.reparent(ob, spin)
    kit.tag(ob, 'Zone_TailRotor', 'intact', fx='blur')
    out['disc'] = ob
    out['spin'] = spin
    return out


# ============================================================ lights, antenna, decals
def build_lights(ctx):
    root, M = ctx['root'], ctx['M']
    out = {}

    def lens(name, p, r, mat, zone, light, nrm=(0, 0, 1)):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=seg(14, 8), v_segments=seg(8, 4), radius=r)
        for v in bm.verts:
            d = Vector(nrm).normalized()
            h = v.co.dot(d)
            if h < 0:
                v.co -= d * h * 0.9
            v.co += Vector(p)
        for f in bm.faces:
            f.smooth = True
        ob = kit.from_bm(name, bm, [mat], root)
        kit.tag(ob, zone, 'intact', light=light)
        return ob
    out['nav_r'] = lens('Light_Nav_Green_R', (0.28, 0.44, 1.60), 0.03, M['lamp_green'], 'Zone_Cabin', 'navigation green right', (0, 0.7, 0.7))
    out['nav_l'] = lens('Light_Nav_Red_L', (0.28, -0.44, 1.60), 0.03, M['lamp_red'], 'Zone_Cabin', 'navigation red left', (0, -0.7, 0.7))
    out['nav_t'] = lens('Light_Nav_White_Tail', (4.64, 0.0, 2.30), 0.025, M['lamp_white'], 'Zone_TailBoom', 'navigation white tail', (1, 0, 0))
    for nm, sgn in (('L', -1), ('R', 1)):
        p = cabin_point(0.17, math.radians(165) * sgn if sgn > 0 else 2 * math.pi - math.radians(165))
        bm = bmesh.new()
        kit.bm_cyl(bm, (p.x - 0.01, p.y, p.z), (p.x + 0.02, p.y, p.z), 0.04, 0.04, n=18, mat_idx=0)
        ob = kit.from_bm('Light_Landing_' + nm, bm, [M['lamp_white']], root)
        kit.tag(ob, 'Zone_Cabin', 'intact', light='landing')
        out['landing_' + nm] = ob
    # whip antenna: base on the aft deck, leaning aft
    bm = bmesh.new()
    kit.bm_cyl(bm, (0.80, 0.0, 1.55), (0.82, 0.0, 1.60), 0.02, 0.016, n=10, mat_idx=0)
    kit.bm_tube(bm, [(0.82, 0, 1.60), (0.98, 0, 1.88), (1.12, 0, 2.15)], 0.0035, n=6, mat_idx=1)
    ob = kit.from_bm('Antenna', bm, [M['plastic'], M['steel']], root)
    kit.tag(ob, 'Zone_Engine', 'intact', detach='part')
    out['antenna'] = ob
    # emitters and sockets: smoke / fire / fuel leak points (empties, never rendered)
    return out


def build_decals(ctx):
    root, M = ctx['root'], ctx['M']
    out = {}
    for nm, sgn in (('R', 1), ('L', -1)):
        x0, x1 = 1.80, 2.70
        nxs, nys = seg(12, 6), 2
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.new('UVMap')
        g = []
        hh = 0.072
        for iy in range(nys + 1):
            row = []
            for ix in range(nxs + 1):
                x = x0 + (x1 - x0) * ix / nxs
                r = boom_radius(x) * 1.0
                c = boom_centre(x)
                dz = -hh + 2 * hh * iy / nys
                ang = math.asin(max(-1, min(1, dz / (r * 1.06))))
                y = sgn * (r * 0.92 * math.cos(ang) + 0.0015)
                row.append(bm.verts.new((x, y, c.z + dz)))
            g.append(row)
        for iy in range(nys):
            for ix in range(nxs):
                vs = [g[iy][ix], g[iy][ix + 1], g[iy + 1][ix + 1], g[iy + 1][ix]]
                if sgn < 0:
                    vs = vs[::-1]
                f = bm.faces.new(vs)
                for lp in f.loops:
                    t = (lp.vert.co.x - x0) / (x1 - x0)
                    # text reads left to right as the viewer sees it: on the right side the nose (-X) is at the viewer's right
                    u = 1 - t if sgn > 0 else t
                    # (a mirrored text on the left side would otherwise be read from behind)
                    lp[uvl].uv = (u, (lp.vert.co.z - (boom_centre(lp.vert.co.x).z - hh)) / (2 * hh))
        ob = kit.from_bm('Decal_Reg_' + nm, bm, [M['reg']], root, smooth=False)
        kit.tag(ob, 'Zone_TailBoom', 'intact', registration=P.REG)
        out['reg_' + nm] = ob
    return out


def build(ctx):
    kit_mech = {}
    kit_mech['skids'] = build_skids(ctx)
    kit_mech['engine'] = build_engine(ctx)
    kit_mech['rotor'] = build_main_rotor(ctx)
    kit_mech['tail'] = build_tail(ctx)
    kit_mech['tr'] = build_tail_rotor(ctx)
    kit_mech['lights'] = build_lights(ctx)
    kit_mech['decals'] = build_decals(ctx)
    ctx['mech'] = kit_mech
