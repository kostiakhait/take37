# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Stage cab: the day cab (a hollow lofted shell, exact boolean cuts for the windows and door gaps), the two doors with their glass, cards, handles and west-coast mirrors,
the windshield and rear window, the trim; the long hood with front fenders and the grille; the front bumper and the headlamps.

Nodes under Tractor:  Cab (empty) > Cab_Body, Cab_Glass, Cab_Trim, Door_L / Door_R (pivots at the hinge, spin about Z) > Door_x_Body, Door_x_Glass, Door_x_Trim, Mirror_x,
Hood (pivot at the front hinge, tilts about Y) > Hood_Body, Fenders_Front, Grille, Lamps_Head;   Bumper_F;  Lamps are made in the lamps stage.
"""
import math

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

import carkit as CK
import dims as D
import parts as P
import tkit as T
from tkit import V3, Mesh

XB, XF = -0.62, 0.98                 # back of cab, cowl
Y_WALL = 1.115
Z_FLOOR = 1.0
BAND_NAVY = (1.46, 1.51)
HINGE_X = 0.93


def zroof(x):
    return 2.98 if x <= 0.70 else 2.98 - 0.86 * (x - 0.70) / 0.28


def half(x, ins=0.0):
    """The cab's half section at x: (y, z) from the roof's centre line down the side to the floor's centre line; `ins` pulls it inwards (the inner cavity)."""
    zt = zroof(x)
    e = 0.0
    if x < XB + 0.10:                                              # the rounded back edge
        t = (x - XB) / 0.10
        e = 0.10 * (1 - math.sqrt(max(0.0, 1 - (1 - t) ** 2)))
    pts = [(0.0, zt + 0.02), (0.45, zt + 0.012), (0.80, zt - 0.014), (0.97, zt - 0.06), (1.045, zt - 0.13), (1.093, zt - 0.26), (1.113, zt - 0.42), (Y_WALL, 1.95), (Y_WALL, 1.60),
           (Y_WALL, BAND_NAVY[1]), (Y_WALL, BAND_NAVY[0]), (Y_WALL, 1.30), (1.108, 1.16), (1.09, 1.05), (1.02, Z_FLOOR + 0.002), (0.6, Z_FLOOR), (0.0, Z_FLOOR)]
    out = []
    for i, (y, z) in enumerate(pts):
        y2 = max(0.0, y - ins - (e * min(1.0, y / 0.9) if i < len(pts) - 2 else 0.0))
        if i == 0:
            y2 = 0.0
        z2 = z - ins - (e * 0.8 if i <= 7 else 0.0)
        if z < 1.1:
            z2 = z + ins
        out.append((y2, z2))
    return T.chaikin(out, 2)


def ring3(x, hf):
    return [V3((x, y, z)) for y, z in hf] + [V3((x, -y, z)) for y, z in reversed(hf[1:-1])]


def stations(x0, x1):
    xs = [XB + d for d in (0, 0.005, 0.015, 0.03, 0.05, 0.075, 0.10)]
    x = XB + 0.25
    while x < 0.70:
        xs.append(x)
        x += 0.17
    xs += [0.70, 0.76, 0.82, 0.88, 0.94, XF]
    return [min(max(v, x0), x1) for v in xs if x0 - 1e-9 <= v <= x1 + 1e-9]


def solid(name, ins, kind):
    m = Mesh()
    xs = stations(XB + ins, XF - ins)
    rings = [ring3(x, half(x, ins)) for x in xs]
    m.loft(rings, kind, caps=True)
    return m.finish(name, box_uv=False, sharp=60)


def prism_obj(name, poly, ya, yb, a=0, b=2, ax=1, kind='black'):
    m = Mesh()
    m.prism(poly, a, b, ax, ya, yb, kind)
    return m.finish(name, box_uv=False)


def offset_poly(poly, d):
    """The polygon grown by d (vertex normals of a convex-ish outline, adequate for the door's shape)."""
    n = len(poly)
    out = []
    for i in range(n):
        p0, p1, p2 = Vector(poly[i - 1]), Vector(poly[i]), Vector(poly[(i + 1) % n])
        e0 = (p1 - p0).normalized()
        e1 = (p2 - p1).normalized()
        n0 = Vector((e0.y, -e0.x))
        n1 = Vector((e1.y, -e1.x))
        bis = (n0 + n1).normalized()
        k = d / max(0.3, bis.dot(n0))
        q = p1 + bis * k
        out.append((q.x, q.y))
    return out


DOOR_POLY = [(-0.20, 1.10), (0.93, 1.10), (0.93, 2.14), (0.76, 2.70), (0.62, 2.90), (-0.20, 2.90)]          # (x, z) counter-clockwise seen from +y... orientation fixed by the prism
WIN_POLY = [(-0.09, 1.99), (0.83, 1.99), (0.83, 2.27), (0.67, 2.79), (-0.09, 2.79)]


def ccw(poly):
    a = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))
    return poly if a > 0 else list(reversed(poly))


def convert(poly):
    return ccw(poly)


def build_shell():
    outer = solid('cab_outer', 0.0, 'paint')
    inner = solid('cab_inner', 0.045, 'interior')
    T.boolean(outer, [inner], 'DIFFERENCE')
    # windows: the doors' side windows, the rear window, the windshield (two panes' openings with a centre post left)
    cut = []
    for s in (1, -1):
        cut.append(prism_obj(f'w{s}', convert(WIN_POLY), 0.55 if s > 0 else -1.4, 1.4 if s > 0 else -0.55, a=0, b=2, ax=1, kind='seal'))
    cut.append(prism_obj('rw', convert([(-0.80, 2.25), (-0.30, 2.25), (-0.30, 2.78), (-0.80, 2.78)]), -0.50 + 0.0, 0.50, a=0, b=2, ax=1, kind='seal'))
    # the rear window is cut through the back wall: extruded along y between -0.5..0.5, in x z
    # windshield openings: boxes aligned to the slope
    d = V3((0.28, 0, -0.86)).normalized()
    n = V3((0.86, 0, 0.28)).normalized()
    p0 = V3((0.70, 0, 2.98))
    for lo, hi in ((0.03, 0.90), (-0.90, -0.03)):
        c = p0 + d * 0.40 + n * 0.02
        m = Mesh()
        m.rbox(V3((c.x, 0.5 * (lo + hi), c.z)), (0.55, hi - lo, 0.30), 0.0, 'seal', (d, V3((0, 1, 0)), n))
        cut.append(m.finish('wsc', box_uv=False))
    T.boolean(outer, cut, 'DIFFERENCE')
    return outer


def split_doors(shell):
    doors = {}
    for s in (1, -1):
        cm = Mesh()
        cm.prism(convert(DOOR_POLY), 0, 2, 1, 0.80 * s if s > 0 else -1.4, 1.4 if s > 0 else -0.80, 'seal')
        c1 = cm.finish(f'dc{s}', box_uv=False)
        bm = bmesh.new()
        bm.from_mesh(shell.data)
        me = bpy.data.meshes.new(f'door{s}')
        bm.to_mesh(me)
        bm.free()
        for mt in shell.data.materials:
            me.materials.append(mt)
        dob = bpy.data.objects.new(f'door{s}', me)
        bpy.context.scene.collection.objects.link(dob)
        T.boolean(dob, [c1], 'INTERSECT')
        doors[s] = dob
        gap = Mesh()
        gap.prism(convert(offset_poly(DOOR_POLY, 0.004)), 0, 2, 1, 0.80 * s if s > 0 else -1.4, 1.4 if s > 0 else -0.80, 'seal')
        T.boolean(shell, [gap.finish(f'gap{s}', box_uv=False)], 'DIFFERENCE')
    return doors


def paint_zones(ob):
    """Two-tone livery: white below the belt stripe, a navy band, red above. Faces of the outer paint only."""
    me = ob.data
    names = [m.name for m in me.materials]
    idx = {k: names.index('M_' + k) if 'M_' + k in names else None for k in ('paint', 'paint_white', 'paint_navy')}
    for k in ('paint_white', 'paint_navy'):
        if idx[k] is None:
            me.materials.append(T.mat(k))
            idx[k] = len(me.materials) - 1
    for f in me.polygons:
        if f.material_index == idx['paint']:
            z = f.center.z
            if z < BAND_NAVY[0] - 0.005:
                f.material_index = idx['paint_white']
            elif z < BAND_NAVY[1] + 0.005:
                f.material_index = idx['paint_navy']


def wall_y(bvh, x, z, s):
    hit = bvh.ray_cast(V3((x, s * 3.0, z)), V3((0, -s, 0)))
    return (hit[0].y if hit[0] is not None else s * Y_WALL)


def build_glass_and_trim(bvh, doors):
    glass = Mesh()
    trim = Mesh()
    # windshield: two flat panes on the slope plane, 0.045 below the surface; a centre post and a rubber gasket
    d = V3((0.28, 0, -0.86)).normalized()
    n = V3((0.86, 0, 0.28)).normalized()
    p0 = V3((0.70, 0, 2.98)) - n * 0.052
    for lo, hi in ((0.045, 0.885), (-0.885, -0.045)):
        for kind, th, off in (('glass', 0.006, 0.0),):
            c = p0 + d * 0.40 + n * off
            glass.rbox(V3((c.x, 0.5 * (lo + hi), c.z)), (0.50, hi - lo, th), 0.002, kind, (d, V3((0, 1, 0)), n))
        # gasket frame round each pane
        corners = [p0 + d * 0.15 + V3((0, lo, 0)), p0 + d * 0.65 + V3((0, lo, 0)), p0 + d * 0.65 + V3((0, hi, 0)), p0 + d * 0.15 + V3((0, hi, 0))]
        corners = [V3((p.x, p.y, p.z)) + n * 0.050 for p in corners]
        trim.tube(corners + [corners[0]], 0.011, 'seal', seg=8, cap=False, loop=False)
    trim.rbox(p0 + d * 0.40 + n * 0.052, (0.52, 0.07, 0.020), 0.006, 'paint', (d, V3((0, 1, 0)), n))      # centre post
    # rear window pane and gasket
    glass.rbox(V3((XB + 0.06, 0, 2.515)), (0.010, 0.96, 0.50), 0.002, 'glass')
    # sun visor over the windshield (a painted sheet bent over the header) with brackets
    vis = []
    for j in range(7):
        u = -1 + 2 * j / 6
        y = u * 1.04
        zc = 2.985 - 0.045 * u * u
        vis.append([V3((0.62 + 0.0, y, zc + 0.02)), V3((0.80, y, zc - 0.03)), V3((0.98 - 0.04 * u * u, y, zc - 0.13)), V3((0.985 - 0.04 * u * u, y, zc - 0.145)), V3((0.80, y, zc - 0.045)), V3((0.62, y, zc + 0.008))])
    trim.loft(vis, 'paint', closed=True, caps=False)
    for j in range(2):
        pass
    # roof: five amber marker lamps on the header, a stainless drip rail either side
    for k in range(5):
        y = -0.36 + 0.18 * k
        trim.rbox(V3((0.585, y, 3.0)), (0.07, 0.11, 0.058), 0.012, 'steel')
        trim.rbox(V3((0.62, y, 3.0)), (0.012, 0.09, 0.040), 0.008, 'lens_amber')
    for s in (1, -1):
        path = [V3((x, s * wall_y(bvh, x, 2.93, s) * 0.0 + s * 1.045, 2.93 + 0.012)) for x in (-0.52, -0.25, 0.0, 0.25, 0.5, 0.66)]
        trim.tube(path, 0.007, 'chrome', seg=8)
        # the side window gaskets: a rubber loop round the opening at the wall
        pts = []
        for x, z in ccw(WIN_POLY):
            pts.append(V3((x, wall_y(bvh, x, z, s) * 1.0 + s * 0.001, z)))
        trim.tube(pts, 0.010, 'seal', seg=8, loop=True)
        # A-pillar grab handle and cab corner stainless trim
        trim.cyl(V3((0.90, s * 1.15, 1.35)), V3((0.90, s * 1.15, 1.95)), 0.011, 'chrome', seg=12)
        for z in (1.35, 1.95):
            trim.cyl(V3((0.90, s * 1.11, z)), V3((0.90, s * 1.15, z)), 0.009, 'chrome', seg=10)
        # back-of-cab: stainless trim, a step for the fifth-wheel deck and air connections' bracket
    trim.rbox(V3((XB - 0.012, 0, 1.52)), (0.020, 2.18, 0.06), 0.008, 'chrome')
    trim.rbox(V3((XB - 0.012, 0, 1.46)), (0.012, 2.18, 0.04), 0.004, 'paint_navy')
    trim.rbox(V3((XB - 0.04, 0, 1.55 + 0.05)), (0.08, 0.60, 0.24), 0.01, 'steel_dark')           # air line box with the gladhand couplings
    for yy in (-0.2, 0.0, 0.2):
        trim.cyl(V3((XB - 0.08, yy, 1.60)), V3((XB - 0.11, yy, 1.60)), 0.022, 'brass', seg=12)
    return glass, trim


def build_door(s, dob, bvh):
    """Door_L / Door_R: a pivot empty at the hinge; the body shell, glass, trim (handle, lock, hinge covers), the inner card, the mirror."""
    hinge = V3((HINGE_X, s * Y_WALL, 1.10))
    piv = T.empty('Door_' + ('L' if s > 0 else 'R'), hinge, T.find('Cab'))
    T.log('door', s, len(dob.data.polygons))
    # body: move the shell piece under the pivot, mesh recentred
    me = dob.data
    me.transform(__import__('mathutils').Matrix.Translation(-hinge))
    dob.location = (0, 0, 0)
    dob.name = piv.name + '_Body'
    dob.parent = piv
    T.smooth(dob, 45)
    nm = 'L' if s > 0 else 'R'
    glass = Mesh()
    trim = Mesh()
    card = Mesh()
    xs = [p[0] for p in WIN_POLY]
    # the window pane, a little inside the wall; chrome-free frame by the gasket; wind-down regulator strip hidden
    pts = []
    for x, z in ccw(WIN_POLY):
        k = 0.012
        cx, cz = 0.37, 2.39
        pts.append((x + (cx - x) * 0.03, z + (cz - z) * 0.03))
    yg = s * (Y_WALL - 0.048)
    glass.prism(pts, 0, 2, 1, yg - 0.003 * s, yg + 0.003 * s, 'glass')
    # handle, lock and door-edge trim
    hx, hz = -0.05, 1.82
    trim.rbox(V3((hx, s * (Y_WALL + 0.012), hz)), (0.19, 0.022, 0.045), 0.012, 'chrome')
    trim.rbox(V3((hx + 0.12, s * (Y_WALL + 0.004), hz + 0.02)), (0.04, 0.010, 0.04), 0.005, 'steel_dark')       # key lock
    trim.cyl(V3((hx + 0.12, s * (Y_WALL + 0.008), hz + 0.02)), V3((hx + 0.12, s * (Y_WALL + 0.012), hz + 0.02)), 0.011, 'chrome', seg=16)
    for z in (1.30, 2.40):
        trim.cyl(V3((HINGE_X - 0.02, s * (Y_WALL + 0.0), z - 0.08)), V3((HINGE_X - 0.02, s * (Y_WALL + 0.0), z + 0.08)), 0.014, 'steel', seg=12)
    # the inner door card: fabric panel with an armrest, the pull, speaker grille, window crank, a map pocket
    yc = s * (Y_WALL - 0.060)
    card.rbox(V3((0.36, yc, 1.58)), (1.05, 0.020, 0.78), 0.008, 'fabric')
    card.rbox(V3((0.30, yc - s * 0.03, 1.55)), (0.55, 0.05, 0.07), 0.02, 'seat')                               # armrest
    card.rbox(V3((0.40, yc - s * 0.015, 1.30)), (0.70, 0.040, 0.22), 0.012, 'dash')                           # map pocket
    card.rbox(V3((0.55, yc - s * 0.012, 1.74)), (0.14, 0.03, 0.05), 0.012, 'dash')
    card.cyl(V3((0.62, yc - s * 0.012, 1.95)), V3((0.62, yc - s * 0.04, 1.95)), 0.02, 'steel', seg=16)
    for k in range(5):
        card.rbox(V3((0.20 + 0.04 * k, yc - s * 0.012, 1.20)), (0.01, 0.01, 0.15), 0.002, 'blackmat')
    card.rbox(V3((0.36, yc, 1.99)), (1.0, 0.030, 0.045), 0.012, 'dash')                                        # upper rail of the card
    # lettering: the company name on the white lower panel, the unit number on the red
    if True:
        ex = V3((1, 0, 0)) if s > 0 else V3((-1, 0, 0))
        trim.decal('name_red', V3((0.36, s * (Y_WALL + 0.002), 1.275)), V3((-s, 0, 0)), V3((0, 0, 1)), 0.88, 0.22, 'decal', nrm=V3((0, s, 0)))
        trim.decal('unit', V3((0.62, s * (Y_WALL + 0.002), 1.72)), V3((-s, 0, 0)), V3((0, 0, 1)), 0.21, 0.105, 'decal', nrm=V3((0, s, 0)))
    for mm, nme in ((glass, 'Glass'), (trim, 'Trim'), (card, 'Card')):
        mm.finish(f'Door_{nm}_{nme}', piv, sharp=55)
    # west-coast mirror: two stainless arms, a vertical head with the main and a convex spot mirror
    mir = Mesh()
    mx, my = 0.72, s * 1.31
    for z in (2.05, 2.62):
        mir.cyl(V3((HINGE_X - 0.06, s * (Y_WALL + 0.01), z)), V3((mx, my - s * 0.04, z)), 0.012, 'chrome', seg=12)
        mir.rbox(V3((HINGE_X - 0.06, s * (Y_WALL + 0.01), z)), (0.06, 0.02, 0.06), 0.006, 'steel')
    mir.rbox(V3((mx, my, 2.33)), (0.045, 0.19, 0.66), 0.02, 'steel')                                           # the housing
    mir.rbox(V3((mx + 0.0205, my, 2.40)), (0.002, 0.172, 0.46), 0.0, 'mirror')                                 # the main flat glass
    mir.rbox(V3((mx + 0.0205, my, 2.08)), (0.004, 0.14, 0.14), 0.012, 'mirror')                                # the convex spot mirror
    mir.rbox(V3((mx + 0.0165, my, 2.33)), (0.002, 0.185, 0.64), 0.0, 'black')
    mir.finish(f'Mirror_{nm}', piv, sharp=55)
    return piv


def build_hood():
    hood_pivot = T.empty('Hood', V3((3.0, 0, 1.20)), T.find('Tractor'))
    m = Mesh()
    xs = [XF + 0.015 + (3.01 - XF - 0.015) * k / 14 for k in range(15)]
    rings = []
    for x in xs:
        t = (x - XF) / (3.01 - XF)
        zt = 1.93 - 0.17 * t * t - 0.06 * t
        w = 0.72 - 0.10 * t
        hf = [(0.0, zt + 0.025), (0.5 * w, zt + 0.018), (0.88 * w, zt), (w, zt - 0.06), (w + 0.045, zt - 0.20), (w + 0.062, 1.40), (w + 0.05, 1.22)]
        rings.append(ring3(x, T.chaikin(hf, 2) + [(0.0, 1.20)][:0]))
    # a closed solid shell would need a floor: leave the hood open underneath, as the real fibreglass hood is; hollow with an inner skin so it has thickness
    m.loft(rings, 'paint', caps=False)
    inner = []
    for x in xs:
        t = (x - XF) / (3.01 - XF)
        zt = 1.93 - 0.17 * t * t - 0.06 * t - 0.02
        w = 0.72 - 0.10 * t - 0.02
        hf = [(0.0, zt + 0.025), (0.5 * w, zt + 0.018), (0.88 * w, zt), (w, zt - 0.06), (w + 0.045, zt - 0.20), (w + 0.062, 1.40), (w + 0.05, 1.22)]
        inner.append(list(reversed(ring3(x, T.chaikin(hf, 2)))))
    m.loft(inner, 'interior', caps=False)
    # centre chrome spine and hinge-line bead, hood louvres (dark recessed slots), hood latches
    spine = [V3((x, 0, (1.93 - 0.17 * ((x - XF) / (3.01 - XF)) ** 2 - 0.06 * (x - XF) / (3.01 - XF)) + 0.027)) for x in xs]
    m.tube(spine, 0.012, 'chrome', seg=10)
    for s in (1, -1):
        for k in range(7):
            x = 1.40 + 0.105 * k
            t = (x - XF) / (3.01 - XF)
            w = 0.72 - 0.10 * t
            m.rbox(V3((x, s * (w + 0.058), 1.60)), (0.026, 0.012, 0.30), 0.004, 'black')
        for x in (1.30, 2.30):
            m.rbox(V3((x, s * 0.80, 1.31)), (0.07, 0.03, 0.05), 0.01, 'chrome')
    # fibreglass seam: the mould joint line down each shoulder (a thin ridge)
    for s in (1, -1):
        seam = []
        for x in xs:
            t = (x - XF) / (3.01 - XF)
            zt = 1.93 - 0.17 * t * t - 0.06 * t
            w = 0.72 - 0.10 * t
            seam.append(V3((x, s * (w + 0.003), zt - 0.065)))
        m.tube(seam, 0.0025, 'paint', seg=6)
    hood = m.finish('Hood_Body', hood_pivot, sharp=50)
    # front fenders: an arch over each steer wheel, joined to the hood by a flat top flare
    fm = Mesh()
    for s in (1, -1):
        yc = s * D.STEER_Y
        R, w, t = 0.605, 0.60, 0.013
        a0, a1 = math.radians(2), math.radians(178)
        seg = 40
        for rr, flip in ((R, False), (R + t, True)):
            rows = []
            for j in range(7):
                u = -1 + 2 * j / 6
                y = yc + u * w / 2
                row = []
                for k in range(seg + 1):
                    a = a0 + (a1 - a0) * k / seg
                    crown = 0.05 * (1 - u * u)
                    row.append(V3((D.STEER_X + (rr + crown) * math.cos(a) * (1.22 if math.cos(a) > 0 else 1.0), y, D.ZC + (rr + crown) * math.sin(a))))
                rows.append(row)
            fm.grid(list(reversed(rows)) if flip else rows, 'paint')
        for u in (-1, 1):                                                                  # rolled edges
            path = [V3((D.STEER_X + (R + 0.056 * 0 + 0.0) * math.cos(a0 + (a1 - a0) * k / seg) * (1.22 if math.cos(a0 + (a1 - a0) * k / seg) > 0 else 1.0), yc + u * w / 2, D.ZC + R * math.sin(a0 + (a1 - a0) * k / seg))) for k in range(seg + 1)]
            fm.tube(path, 0.009, 'steel', seg=8)
        # the inner flare joining the hood side (a sloped panel) and a splash apron inside
    fm.finish('Fenders_Front', hood_pivot, sharp=50)
    # grille: a chrome shell, the opening with vertical bars, a bright centre badge plate left blank
    gm = Mesh()
    gx = 3.02
    gm.rbox(V3((gx + 0.03, 0, 1.45)), (0.10, 1.28, 0.82), 0.04, 'chrome')
    gm.rbox(V3((gx + 0.085, 0, 1.45)), (0.01, 1.08, 0.64), 0.01, 'black')
    P.grille_bars(gm, gx + 0.087, -0.52, 0.52, 1.14, 1.76, 27, 'chrome', depth=0.034, w=0.014)
    for z in (1.30, 1.45, 1.60):
        gm.rbox(V3((gx + 0.084, 0, z)), (0.018, 1.06, 0.016), 0.004, 'chrome')
    gm.rbox(V3((gx + 0.085, 0, 1.92)), (0.02, 0.50, 0.06), 0.012, 'chrome')                                    # a blank nameplate bar
    for s in (1, -1):                                                                                          # corner brackets with the hood-to-grille bolts
        for dz in (-0.34, 0.0, 0.34):
            P.hex_bolt(gm, V3((gx + 0.08, s * 0.62, 1.45 + dz)), V3((1, 0, 0)), 0.01, 0.007, 'steel')
    # a simple chrome hood ornament: a swept blade on a base
    gm.rbox(V3((XF + 2.0, 0, 1.97 + 0.02)), (0.12, 0.05, 0.03), 0.01, 'chrome')
    om = [V3((XF + 2.0 - 0.06, 0, 1.99)), V3((XF + 2.0 + 0.0, 0, 2.06)), V3((XF + 2.0 + 0.12, 0, 2.03)), V3((XF + 2.0 + 0.06, 0, 1.99))]
    gm.prism([(p.x, p.z) for p in om], 0, 2, 1, -0.012, 0.012, 'chrome')
    gm.finish('Grille', hood_pivot, sharp=50)
    return hood_pivot


def build_bumper():
    m = Mesh()
    bx = 3.20
    # a three-piece chrome bumper: a centre section and two angled ends, with brackets to the frame rails, a license-plate pad and tow hooks
    prof = [(0.0, 0.00), (0.0, 0.26), (0.035, 0.30), (0.075, 0.26), (0.075, 0.03), (0.03, -0.01)]       # (x offset toward front, z offset) of the channel: a rolled C
    sections = [(0.0, 0.0), (0.55, 0.0), (0.95, -0.12), (1.20, -0.34)]
    for s in (1, -1):
        for (y0, d0), (y1, d1) in zip(sections, sections[1:]):
            r0 = [V3((bx - 0.075 + d0 + px, s * y0, 0.58 + pz)) for px, pz in prof]
            r1 = [V3((bx - 0.075 + d1 + px, s * y1, 0.58 + pz)) for px, pz in prof]
            m.loft([r0, r1] if s > 0 else [r1, r0], 'chrome', caps=False)
        e = sections[-1]
        r = [V3((bx - 0.075 + e[1] + px, s * e[0], 0.58 + pz)) for px, pz in prof]
        rv = [m.bm.verts.new(p) for p in r]
        m.face(rv if s > 0 else list(reversed(rv)), 'chrome')
        m.rbox(V3((bx - 0.19, s * 0.40, 0.80)), (0.36, 0.09, 0.07), 0.01, 'frame')                          # bumper brackets
        m.rbox(V3((bx - 0.30, s * 0.40, 0.90)), (0.30, 0.03, 0.20), 0.008, 'frame')
        for dz in (0.0, 0.1):
            P.hex_bolt(m, V3((bx - 0.30, s * 0.415, 0.86 + dz * 1.0)), V3((0, s, 0)), 0.01, 0.007, 'steel')
        for dy in (-0.07, 0.07):
            P.hex_bolt(m, V3((bx + 0.036 + 0.0, s * (0.40 + dy), 0.58 + 0.06)), V3((1, 0, 0)), 0.011, 0.008, 'steel')
        # tow hook: a hook bent from a round bar under the bumper
        hook = [V3((bx - 0.16, s * 0.25, 0.60)), V3((bx - 0.02, s * 0.25, 0.54)), V3((bx + 0.05, s * 0.25, 0.46)), V3((bx + 0.00, s * 0.25, 0.38)), V3((bx - 0.07, s * 0.25, 0.40))]
        m.tube(hook, 0.018, 'steel_dark', seg=8)
    # plate and its pad
    m.rbox(V3((bx + 0.044, 0, 0.74)), (0.012, 0.36, 0.20), 0.004, 'steel_dark')
    pl = Mesh()
    pl.decal('plate', V3((bx + 0.052, 0, 0.74)), V3((0, 1, 0)), V3((0, 0, 1)), 0.305, 0.152, 'plate_m', nrm=V3((1, 0, 0)), flip=False)
    return m, pl


def run(root):
    tr = T.find('Tractor')
    cab = T.empty('Cab', V3((0, 0, 0)), tr)
    shell = build_shell()
    bvh = BVHTree.FromObject(shell, bpy.context.evaluated_depsgraph_get())
    T.log('shell', len(shell.data.polygons))
    doors = split_doors(shell)
    paint_zones(shell)
    for s, d in doors.items():
        paint_zones(d)
    shell.name = 'Cab_Body'
    shell.parent = cab
    T.smooth(shell, 45)
    glass, trim = build_glass_and_trim(bvh, doors)
    glass.finish('Cab_Glass', cab, sharp=60)
    trim.finish('Cab_Trim', cab, sharp=55)
    for s in (1, -1):
        build_door(s, doors[s], bvh)
    T.log('doors built')
    build_hood()
    b, pl = build_bumper()
    b.finish('Bumper_F', tr, sharp=45)
    pl.finish('Plate_F', tr, sharp=60)
