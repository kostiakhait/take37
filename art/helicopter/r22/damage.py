# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Damaged-state nodes of every zone (build frame: nose -X, +Y right; zones.finish() turns it). Every node carries state='damaged'; the viewer/game hides them until a zone's
`Dmg_<Zone>_*` group is shown, and the group's `replaces` property names the intact nodes to hide at the same time. Detachable pieces (the broken-off remainders) sit under `Dmg_Pieces`
with their pivot at their centre so the destruction system can drop them."""
import math
import numpy as np
import bpy
import bmesh
from mathutils import Vector, Matrix
from . import kit, params as P
from .kit import seg
from .fuselage import cabin_point, boom_centre, boom_radius
from .mech import blade_mesh, HUB_C, skid_profile, cross_profile, CROSS_REAR_X, ENG_X0, ENG_ZC
from .fuselage import cowl_half_width
from .interior import rbox

RS = np.random.RandomState(37)


def hole_decal(root, M, name, p, n, size, mat='hole', rot=0.0):
    """a quad of `size` metres on the surface at p with normal n (offset 1.5 mm), UV 0..1; reads the decal texture's alpha"""
    n = Vector(n).normalized()
    t = n.cross(Vector((0, 0, 1)))
    if t.length < 1e-3:
        t = n.cross(Vector((1, 0, 0)))
    t.normalize()
    b = n.cross(t).normalized()
    c, s = math.cos(rot), math.sin(rot)
    t, b = t * c + b * s, -t * s + b * c
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    h = size / 2
    vs = [bm.verts.new(Vector(p) + n * 0.0015 + t * x * h + b * y * h) for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    f = bm.faces.new(vs)
    for lp, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        lp[uvl].uv = uv
    return kit.from_bm(name, bm, [M[mat]], root, smooth=False)


def petals(bm, p, n, r, k=7, out=1.7, lift=0.8, seed=1, mat_idx=0, mat_in=1):
    """a ragged hole: a fan of k torn metal petals bent outward around centre p (normal n), radius r"""
    rs = np.random.RandomState(seed)
    n = Vector(n).normalized()
    t = n.cross(Vector((0, 0, 1)))
    if t.length < 1e-3:
        t = n.cross(Vector((1, 0, 0)))
    t.normalize()
    b = n.cross(t).normalized()
    ang = [2 * math.pi * (i + rs.rand() * 0.4) / k for i in range(k)]
    ang.append(ang[0] + 2 * math.pi)
    for i in range(k):
        a0, a1 = ang[i], ang[i + 1]
        am = (a0 + a1) / 2 + (rs.rand() - 0.5) * 0.3
        ro = r * (0.85 + 0.3 * rs.rand())
        v0 = Vector(p) + (t * math.cos(a0) + b * math.sin(a0)) * ro
        v1 = Vector(p) + (t * math.cos(a1) + b * math.sin(a1)) * ro
        tip = Vector(p) + (t * math.cos(am) + b * math.sin(am)) * ro * out + n * r * lift * (0.6 + 0.7 * rs.rand())
        a, bb, c = bm.verts.new(v0), bm.verts.new(v1), bm.verts.new(tip)
        f = bm.faces.new((a, bb, c))
        f.material_index = mat_idx
        f.smooth = False
        g = bm.faces.new((bm.verts.new(v1 + n * 0.002), bm.verts.new(v0 + n * 0.002), bm.verts.new(tip + n * 0.002)))
        g.material_index = mat_in
        g.smooth = False


def shard_pane(root, M, name, grid_pts, hit_uv, seed, drop=0.22):
    """a shattered pane: the cells of the pane's grid, each a little smaller and jittered, those near the hit and a few random ones missing"""
    rs = np.random.RandomState(seed)
    K, N = grid_pts.shape[:2]
    bm = bmesh.new()
    for k in range(K - 1):
        for j in range(N - 1):
            u, v = (k + 0.5) / (K - 1), (j + 0.5) / (N - 1)
            d = math.hypot(u - hit_uv[0], v - hit_uv[1])
            if d < 0.07 or rs.rand() < drop * max(0.2, 1 - d * 2):
                continue
            q = [Vector(grid_pts[k, j]), Vector(grid_pts[k + 1, j]), Vector(grid_pts[k + 1, j + 1]), Vector(grid_pts[k, j + 1])]
            c = sum(q, Vector()) / 4
            sc = 0.68 + 0.28 * rs.rand()
            nrm = (q[1] - q[0]).cross(q[3] - q[0]).normalized()
            shift = nrm * (rs.rand() - 0.5) * 0.008
            R = Matrix.Rotation((rs.rand() - 0.5) * 0.35, 3, nrm)
            vs = [bm.verts.new(c + R @ ((p - c) * sc) + shift) for p in q]
            try:
                bm.faces.new(vs)
            except ValueError:
                pass
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    return kit.from_bm(name, bm, [M['glass']], root, smooth=False)


def build(ctx):
    root, M = ctx['root'], ctx['M']
    D = kit.empty('Damage_States', (0, 0, 0), root, kind='PLAIN_AXES', size=0.1, note='nodes with state=damaged; hidden until the zone is hit; each Dmg_ group lists replaces=[intact nodes to hide]')
    ctx['dmg_root'] = D
    groups = {}
    rotor = ctx['mech']['rotor'] if 'mech' in ctx else None

    def group(name, zone, replaces='', note=''):
        g = kit.empty(name, (0, 0, 0), D, kind='PLAIN_AXES', size=0.08, zone=zone, state='damaged', replaces=replaces, note=note)
        groups[name] = g
        return g

    def put(ob, g, zone, parent=None, **kw):
        ob.parent = parent or g
        kit.tag(ob, zone, 'damaged', group=g.name, **kw)
        kit.ensure_attr(ob)
        return ob

    # ------------------------------------------------ Zone_Cabin
    g = group('Dmg_Cabin_Holes', 'Zone_Cabin', note='bullet holes (decals) in the cabin side skin and nose')
    hits = [(0.9, 70, 0.07), (1.4, 95, 0.08), (1.7, 110, 0.06), (0.55, 55, 0.07), (2.0, 85, 0.09), (0.35, 120, 0.06)]
    for i, (s, deg, sz) in enumerate(hits):
        for side in (1, -1):
            if i % 2 != (0 if side > 0 else 1):
                continue
            a = math.radians(deg)
            p = cabin_point(s, a if side > 0 else 2 * math.pi - a)
            nrm = Vector((0, math.sin(a) * side, math.cos(a) * 0.6)).normalized()
            put(hole_decal(root, M, 'Dmg_Hole_Cabin_%s_%d' % ('R' if side > 0 else 'L', i), p, nrm, sz * 2.2, 'hole', RS.rand() * 6), g, 'Zone_Cabin')
    g = group('Dmg_Cabin_Torn', 'Zone_Cabin', note='ripped skin flaps on the right shoulder and the lower nose, edges bent outward')
    bm = bmesh.new()
    petals(bm, cabin_point(1.45, math.radians(112)), Vector((0, 0.92, 0.35)), 0.11, 8, 1.6, 0.7, 3, 0, 1)
    petals(bm, cabin_point(0.45, math.radians(140)), Vector((-0.3, 0.6, -0.5)), 0.08, 7, 1.7, 0.6, 5, 0, 1)
    put(kit.from_bm('Dmg_Torn_Cabin', bm, [M['torn'], M['charred']], root, smooth=False), g, 'Zone_Cabin')
    g = group('Dmg_Cabin_Scorch', 'Zone_Cabin', note='scorch on the right side of the cabin')
    put(hole_decal(root, M, 'Dmg_Soot_Cabin', cabin_point(2.2, math.radians(70)), (0, 0.9, 0.4), 0.5, 'soot', 0.3), g, 'Zone_Cabin')
    g = group('Dmg_Cabin_Windshield', 'Zone_Cabin', replaces='Glass_Windshield', note='shattered canopy: loose shards with gaps, the hit on the pilot side')
    ks = np.linspace(0.07, 0.98, seg(11, 7))
    phis = np.radians(np.linspace(-76, 76, seg(15, 9)))
    pts = np.zeros((len(ks), len(phis), 3))
    for a, s in enumerate(ks):
        for b, ph in enumerate(phis):
            c = cabin_point(s, ph)
            pts[a, b] = (c.x, c.y, c.z + 0.003)
    put(shard_pane(root, M, 'Dmg_Glass_Windshield', pts, (0.55, 0.30), 11), g, 'Zone_Cabin', glass=True)
    g = group('Dmg_Cabin_DoorGlass', 'Zone_Cabin', replaces='Door_R_Glass', note='right door window shattered')
    pts = np.zeros((seg(7, 5), seg(7, 5), 3))
    for a, s in enumerate(np.linspace(1.12, 1.82, pts.shape[0])):
        for b, ph in enumerate(np.radians(np.linspace(40, 82, pts.shape[1]))):
            c = cabin_point(s, ph)
            pts[a, b] = (c.x, c.y + 0.002, c.z)
    put(shard_pane(root, M, 'Dmg_Glass_DoorR', pts, (0.5, 0.5), 5, 0.15), g, 'Zone_Cabin', glass=True)

    # ------------------------------------------------ Zone_Engine
    g = group('Dmg_Engine_Holes', 'Zone_Engine', note='bullet holes through the aft deck and a torn panel')
    for i in range(5):
        put(hole_decal(root, M, 'Dmg_Hole_Cowl_%d' % i, (0.92 + 0.07 * i, 0.05 + 0.02 * i, 1.58 + 0.04 * i), (0, 0.1, 1), 0.1, 'hole', RS.rand() * 6), g, 'Zone_Engine')
    bm = bmesh.new()
    petals(bm, Vector((1.05, 0.0, 1.62)), Vector((0.1, 0.0, 1)), 0.1, 8, 1.7, 0.9, 9)
    put(kit.from_bm('Dmg_Torn_Cowl', bm, [M['torn'], M['charred']], root, smooth=False), g, 'Zone_Engine')
    g = group('Dmg_Engine_Burnt', 'Zone_Engine', note='soot on the engine bay and charred sleeve over the crankcase; Emit_Fire_Engine / Emit_Smoke_Engine sit here')
    for i, (c, s_) in enumerate([((ENG_X0, 0.0, ENG_ZC), 0.9), ((ENG_X0 + 0.22, 0.3, 0.80), 0.6), ((ENG_X0 + 0.02, -0.2, 1.1), 0.6)]):
        cy = cowl_half_width(c[0]) + 0.004       # on the belly cowl's side wall
        put(hole_decal(root, M, 'Dmg_Soot_Engine_%d' % i, (c[0], cy, c[2]), (0, 1, 0), s_, 'soot', i), g, 'Zone_Engine')
        put(hole_decal(root, M, 'Dmg_Soot_EngineL_%d' % i, (c[0], -cy, c[2]), (0, -1, 0), s_, 'soot', i + 1), g, 'Zone_Engine')
    bm = bmesh.new()
    rbox(bm, (ENG_X0, 0.0, ENG_ZC), (0.36, 0.32, 0.30), 0.04, 0)
    put(kit.from_bm('Dmg_Charred_Block', bm, [M['charred']], root), g, 'Zone_Engine')

    # ------------------------------------------------ Zone_TailBoom (the bent pose is TailGroup's bent_pose_euler_deg; here the torn edge at the break and the holes)
    g = group('Dmg_Boom_TornEdge', 'Zone_TailBoom', note='jagged torn end of the forward boom at the break plane x=3.2, shown when TailGroup is bent or detached')
    bm = bmesh.new()
    n = 20
    z3 = boom_centre(3.20).z
    r0 = boom_radius(3.20)
    ring = []
    for i in range(n):
        a = 2 * math.pi * i / n
        jag = 1.0 + 0.30 * (RS.rand() - 0.2) * (1 if i % 2 else 0.4)
        ring.append(bm.verts.new((3.20 - 0.06 * RS.rand() * (1 if i % 3 == 0 else 0.3), r0 * 0.92 * math.sin(a) * jag, z3 + r0 * 1.06 * math.cos(a) * jag)))
    c = bm.verts.new((3.12, 0.0, z3))
    for i in range(n):
        f = bm.faces.new((ring[i], ring[(i + 1) % n], c))
        f.material_index = 0
        f.smooth = False
    put(kit.from_bm('Dmg_Boom_TornEdge_Mesh', bm, [M['torn']], root, smooth=False), g, 'Zone_TailBoom')
    g = group('Dmg_Boom_Holes', 'Zone_TailBoom', note='a burst of holes along the boom, in the fin, soot at the break')
    for i in range(7):
        x = 2.2 + 0.22 * i
        a = 0.9 + 0.1 * i
        put(hole_decal(root, M, 'Dmg_Hole_Boom_%d' % i, (x, boom_radius(x) * 0.92 * math.sin(a), boom_centre(x).z + boom_radius(x) * 1.06 * math.cos(a)), (0, math.sin(a), math.cos(a)), 0.09, 'hole', i), g, 'Zone_TailBoom')
    put(hole_decal(root, M, 'Dmg_Hole_Fin', (4.46, 0.018, 1.95), (0, 1, 0), 0.12, 'hole', 0.5), g, 'Zone_TailBoom')
    put(hole_decal(root, M, 'Dmg_Soot_Boom', (3.3, 0.1, boom_centre(3.3).z), (0, 1, 0), 0.4, 'soot', 0.2), g, 'Zone_TailBoom')

    # ------------------------------------------------ Zone_MainRotor
    g = group('Dmg_MainRotor_BladeA', 'Zone_MainRotor', replaces='Blade_A', note='blade A snapped at 1.45 m: stub (child of Rotor_Teeter) and the loose outer part Dmg_Piece_Blade_A_Outer')
    bm = blade_mesh(M, 0.55, 1.45, P.ROTOR_CHORD, -8.0 * (1.45 - 0.55) / (P.ROTOR_R - 0.55), 1.5, M['blade'], name_uv_span=(0.55, P.ROTOR_R), ragged=0.06, seed=4, tip_round=False)
    stub = kit.from_bm('Dmg_Blade_A_Stub', bm, [M['blade']], root)
    kit.place(stub, tuple(HUB_C))
    put(stub, g, 'Zone_MainRotor', parent=rotor['teeter'] if rotor else g, detach='blade')
    stub.matrix_parent_inverse = Matrix.Identity(4)
    if rotor:
        stub.location = (0, 0, 0)
    pieces = kit.empty('Dmg_Pieces', (0, 0, 0), D, kind='PLAIN_AXES', size=0.1, note='loose remainders of broken parts, pivot at their centre; drop them with the physics')
    bm = blade_mesh(M, 1.45, P.ROTOR_R, P.ROTOR_CHORD, -8.0, 1.5, M['blade'], name_uv_span=(0.55, P.ROTOR_R), ragged=0.06, seed=5)
    outer = kit.from_bm('Dmg_Piece_Blade_A_Outer', bm, [M['blade']], root)
    mc = Vector((0, (1.45 + P.ROTOR_R) / 2, P.ROTOR_R * math.sin(math.radians(1.5)) * 0.7))
    outer.data.transform(Matrix.Translation(-mc))
    outer.location = Vector(HUB_C) + mc
    outer.parent = pieces
    kit.tag(outer, 'Zone_MainRotor', 'damaged', group=g.name, detach='piece', note='break at r=1.45 m, mass about 2 kg')
    kit.ensure_attr(outer)

    # ------------------------------------------------ Zone_TailRotor
    g = group('Dmg_TailRotor_Bent', 'Zone_TailRotor', replaces='TR_Blade_A', note='tail rotor blade A bent back and cut short (child of TailRotor_Spin)')
    TR = ctx['tr_hub']
    bm = blade_mesh(M, 0.10, 0.36, 0.115, 0.0, 0.0, M['tblade'], thick=0.12, tip_round=False, ragged=0.03, seed=8)
    bmesh.ops.rotate(bm, verts=list(bm.verts), cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'X'))
    bmesh.ops.rotate(bm, verts=list(bm.verts), cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(12), 3, 'Z'))
    for v in bm.verts:
        h = max(0.0, v.co.z - 0.17)
        v.co.y += -h * 1.2
        v.co.z -= h * 0.25
    ob = kit.from_bm('Dmg_TR_Blade_A_Bent', bm, [M['tblade']], root)
    put(ob, g, 'Zone_TailRotor', parent=ctx['mech']['tr']['spin'], detach='blade')
    ob.location = (0, -0.03, 0)

    # ------------------------------------------------ Zone_Fuel
    g = group('Dmg_Fuel_Rupture', 'Zone_Fuel', replaces='Tank_Main', note='right tank torn open at the side, fuel stain on the sill')
    bm = bmesh.new()
    rbox(bm, (0.52, 0.34, 0.70), (0.34, 0.34, 0.20), 0.05, 0)
    petals(bm, Vector((0.52, 0.52, 0.72)), Vector((0, 1, 0.1)), 0.07, 7, 1.7, 0.6, 15, 0, 1)
    put(kit.from_bm('Dmg_Tank_Main_Torn', bm, [M['fuel'], M['charred']], root), g, 'Zone_Fuel')
    put(hole_decal(root, M, 'Dmg_Stain_Fuel', (0.52, 0.56, 0.62), (0, 1, 0), 0.5, 'soot', 0.4), g, 'Zone_Fuel')

    # ------------------------------------------------ Zone_Skids
    g = group('Dmg_Skids_Bent', 'Zone_Skids', replaces='Skid_R,Cross_Rear', note='right skid crumpled and the rear cross tube bent on that side')
    bm = bmesh.new()
    bent = [(x, y + 0.10 * math.sin((x + 1.6) * 1.9) * (0 if x < -0.9 else 1), z + (0.08 * (x + 0.9) if x > -0.9 else 0.0)) for (x, y, z) in skid_profile(1)]
    kit.bm_tube(bm, kit.smooth_poly(bent, 5), 0.036, n=14, mat_idx=0)
    put(kit.from_bm('Dmg_Skid_R_Bent', bm, [M['skid']], root), g, 'Zone_Skids', detach='part')
    bm = bmesh.new()
    cp = [(x, y, z + (0.16 if i == 1 else 0.10 if i < 3 else 0.0)) for i, (x, y, z) in enumerate(cross_profile(CROSS_REAR_X, 1))]
    kit.bm_tube(bm, kit.smooth_poly(cp, 4), 0.0285, n=12, mat_idx=0)
    put(kit.from_bm('Dmg_Cross_Rear_Bent', bm, [M['skid']], root), g, 'Zone_Skids')
    ctx['dmg_groups'] = groups
