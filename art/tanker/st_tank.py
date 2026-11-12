# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Stage tank: the trailer. A 9,000 US gallon aluminium cargo tank (DOT 406 / MC 306 style: an oval shell with dished heads, five compartments whose bulkhead rings show outside as
stiffener bands with weld beads), the running gear (tandem slider subframe, landing legs, kingpin plate) and the rear bumper.

Nodes under Trailer (pivot at the kingpin): TankShell (shell, heads, bands, welds, rivets), Frame_Trailer (subframe, slider, legs, kingpin, bumper, cradle), Fenders_Trailer, MudFlaps_Trailer,
Wheel_T* (from the wheels stage). The fittings (domes, hatches, ladder, rail, valves, lamps) are built in the next stages as their own nodes.
"""
import math

import bpy
from mathutils import Vector

import dims as D
import parts as P
import tkit as T
from tkit import V3, Mesh

A_HALF, B_HALF, PWR = 1.185, 0.985, 2.35          # the oval section: |y/a|^p + |z/b|^p = 1 (half width 1.185: 2.37 m, within the 2.6 m legal width with the fittings)
ZC_TANK = 2.305                                   # axis height: the shell spans 1.32 .. 3.29 m
X_FRONT = -2.05                                   # tip of the front head
HEAD = 0.30                                       # dish depth of each head
NCOMP = 5


def section_area():
    n = 720
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        c, s = math.cos(a), math.sin(a)
        pts.append((A_HALF * math.copysign(abs(c) ** (2 / PWR), c), B_HALF * math.copysign(abs(s) ** (2 / PWR), s)))
    return 0.5 * abs(sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n)))


AREA = section_area()
GAL = 3.785411784e-3                              # m3 per US gallon
L_BARREL = (9000 * GAL - 2 * (2.0 / 3.0) * AREA * HEAD) / AREA     # so that shell + two half-ellipsoid heads hold exactly 9,000 US gallons
X_BARREL0 = X_FRONT - HEAD
X_BARREL1 = X_BARREL0 - L_BARREL
X_REAR = X_BARREL1 - HEAD
BAFFLES = [X_BARREL0 - L_BARREL * k / NCOMP for k in range(1, NCOMP)]
DOME_X = [X_BARREL0 - L_BARREL * (k + 0.5) / NCOMP for k in range(NCOMP)]


def capacity_gal():
    return (AREA * L_BARREL + 2 * (2.0 / 3.0) * AREA * HEAD) / GAL


def sect(x, sc=1.0, n=128):
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        c, s = math.cos(a), math.sin(a)
        pts.append(V3((x, A_HALF * sc * math.copysign(abs(c) ** (2 / PWR), c), ZC_TANK + B_HALF * sc * math.copysign(abs(s) ** (2 / PWR), s))))
    return pts


def surface_point(x, ang, lift=0.0):
    """Point on the barrel at x for the section angle ang (rad; 0 = +y side, pi/2 = top)."""
    c, s = math.cos(ang), math.sin(ang)
    y = A_HALF * math.copysign(abs(c) ** (2 / PWR), c)
    z = B_HALF * math.copysign(abs(s) ** (2 / PWR), s)
    n = V3((0, math.copysign(abs(c) ** (2 - 2 / PWR), c) / A_HALF, math.copysign(abs(s) ** (2 - 2 / PWR), s) / B_HALF))
    n.normalize()
    return V3((x, y, ZC_TANK + z)) + n * lift, n


def head_scales():
    out = []
    capn = 14
    for k in range(capn + 1):
        th = (math.pi / 2) * (1 - k / capn)
        out.append((math.cos(th) if k else 0.012, math.sin(th)))
    return out


def shell_mesh():
    m = Mesh()
    rings = []
    hs = head_scales()
    for sc, t in hs:                                          # front head, tip first
        rings.append(sect(X_BARREL0 + HEAD * t, max(sc, 0.012)))
    n = 44
    for k in range(1, n):                                     # barrel
        rings.append(sect(X_BARREL0 - L_BARREL * k / n))
    for sc, t in reversed(hs):                                # rear head, ending at the tip
        rings.append(sect(X_BARREL1 - HEAD * t, max(sc, 0.012)))
    # alu with wrapped UVs
    vs = m.loft(rings, 'alu')
    # UVs: u along the length (metres), v round the perimeter (metres), seam handled per face
    perim = 7.4
    for f in m.bm.faces:
        us, vsn = [], []
        for lp in f.loops:
            co = lp.vert.co
            ang = math.atan2((co.z - ZC_TANK) / B_HALF, co.y / A_HALF)
            us.append(-co.x / 1.2)
            vsn.append(ang / (2 * math.pi) * perim / 1.2)
        span = perim / 1.2
        if max(vsn) - min(vsn) > span / 2:
            vsn = [v + span if v < 0 else v for v in vsn]
        for lp, u, v in zip(f.loops, us, vsn):
            lp[m.uvl].uv = (u, v)
    return m


def ring_path(x, sc, lift, n=160):
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        p, nn = surface_point(x, a, lift)
        pts.append(p)
    return pts


def stiffeners(m):
    """The compartment bulkhead bands, the head-to-barrel weld rings and the longitudinal seams, with rivets along the bands' edges."""
    # raised bands at the baffles: a flat strap 70 mm wide, 6 mm proud, with a weld bead each side and a row of rivets along the middle
    for x in BAFFLES:
        rings = []
        for dx, lift in ((-0.040, 0.0), (-0.036, 0.008), (0.036, 0.008), (0.040, 0.0)):
            rings.append(ring_path(x + dx, 1.0, lift, 160))
        m.loft(rings, 'alu', loop=False, closed=True)
        for dx in (-0.045, 0.045):
            m.tube(ring_path(x + dx, 1.0, 0.002, 160) + [ring_path(x + dx, 1.0, 0.002, 160)[0]], 0.0034, 'alu', seg=6, cap=False)
        n = 70
        for k in range(n):
            a = 2 * math.pi * (k + 0.5) / n
            p, nn = surface_point(x, a, 0.008)
            P.rivet(m, p, nn, 0.0055, 'steel', seg=8)
    # circumferential weld beads at the head joints (a thicker, rippled bead) and the reinforcement band over each
    for x in (X_BARREL0, X_BARREL1):
        path = ring_path(x, 1.0, 0.0015, 200)
        path.append(path[0])
        P.weld_bead(m, path, 0.0045, 'alu')
    # the longitudinal seams along the barrel: top, upper corners, lower corners, bottom (an aluminium shell is rolled from sheets, welded along the length)
    for ang in (math.radians(90), math.radians(50), math.radians(130), math.radians(-50), math.radians(-130), math.radians(-90), math.radians(8), math.radians(172)):
        pts = [surface_point(x, ang, 0.0015)[0] for x in (X_BARREL0 - L_BARREL * k / 60 for k in range(61))]
        P.weld_bead(m, pts, 0.0032, 'alu')
    # the bottom: a drain sump and a reinforcing keel strap on the underside of each compartment
    for x in DOME_X:
        p, nn = surface_point(x, -math.pi / 2, 0.0)
        m.cyl(p + V3((0, 0, 0.012)), p - V3((0, 0, 0.10)), 0.12, 'alu', seg=28, r1=0.07)
        m.cyl(p - V3((0, 0, 0.10)), p - V3((0, 0, 0.115)), 0.075, 'steel', seg=18)


def frame_mesh():
    m = Mesh()
    kx = D.KINGPIN_X
    # the upper coupler: a heavy plate under the nose with the kingpin, the front bolster and the cross-braces (z 1.294 = the fifth wheel's top)
    m.rbox(V3((kx - 0.30, 0, 1.31)), (1.40, 1.30, 0.032), 0.006, 'frame')
    m.cyl(V3((kx, 0, 1.294)), V3((kx, 0, 1.17)), 0.025, 'steel', seg=18)
    m.cyl(V3((kx, 0, 1.25)), V3((kx, 0, 1.294)), 0.045, 'steel', seg=18)
    for s in (1, -1):
        for dx in (-0.2, 0.1, -0.5, -0.8):
            for dy in (0.50, 0.58):
                P.hex_bolt(m, V3((kx + dx, s * dy, 1.326)), V3((0, 0, 1)), 0.0115, 0.008, 'steel')
    for s in (1, -1):                                                              # the cradle: two upswept rails from the plate into the shell
        P.ibeam(m, V3((kx - 0.9, s * 0.55, 1.33)), V3((-4.2, s * 0.55, 1.20)), 0.20, 0.08, 0.016, 0.012, 'frame', up=V3((0, 1, 0)))
    # the landing gear: two legs with sand shoes, a cross-shaft, a gearbox and a hand crank on the right (folded up)
    lx = -3.55
    for s in (1, -1):
        y = s * 0.92
        m.rbox(V3((lx, y, 1.45)), (0.20, 0.18, 0.26), 0.012, 'frame')
        m.rbox(V3((lx, y, 1.13)), (0.14, 0.14, 0.62), 0.008, 'steel_dark')
        m.rbox(V3((lx, y, 0.86)), (0.12, 0.12, 0.40), 0.006, 'steel')
        m.rbox(V3((lx, y, 0.605)), (0.34, 0.30, 0.016), 0.004, 'steel_dark')
        for k in range(6):
            m.rbox(V3((lx - 0.15 + 0.06 * k, y, 0.625)), (0.014, 0.28, 0.01), 0.002, 'steel')
        for dz in (-0.06, 0.06):
            P.hex_bolt(m, V3((lx + 0.0, y + s * 0.105, 1.45 + dz)), V3((0, s, 0)), 0.011, 0.007, 'steel')
    m.cyl(V3((lx, -0.92, 1.38)), V3((lx, 0.92, 1.38)), 0.017, 'steel_dark', seg=10)
    m.rbox(V3((lx - 0.10, -1.06, 1.38)), (0.12, 0.10, 0.12), 0.012, 'steel_dark')
    m.cyl(V3((lx - 0.10, -1.11, 1.38)), V3((lx - 0.10, -1.30, 1.38)), 0.012, 'steel', seg=10)
    m.cyl(V3((lx - 0.10, -1.30, 1.38)), V3((lx - 0.10, -1.30, 1.18)), 0.010, 'steel', seg=8)
    m.cyl(V3((lx - 0.10, -1.30, 1.18)), V3((lx - 0.10, -1.35, 1.18)), 0.018, 'black', seg=12)
    # rear subframe: two rails, crossmembers, the slider rails and the tandem axles with air-ride beams
    rx0, rx1 = -6.0, -10.95
    for s in (1, -1):
        y = s * 0.46
        P.perforated_plate(m, rx1, rx0, 1.05, 1.28, y, 0.008, 0.20, 0.052, 'frame', sides=12, side=-s)
        for z in (1.04, 1.28):
            m.rbox(V3((0.5 * (rx0 + rx1), s * (0.46 - 0.038), z + 0.005)), (rx0 - rx1, 0.076, 0.012), 0.002, 'frame')
        for xx in (-6.7, -7.4, -8.1):                                                # saddle plates up into the shell
            m.rbox(V3((xx, s * 0.46, 1.41)), (0.40, 0.012, 0.28), 0.004, 'frame')
        # the slider box under the rails
        m.rbox(V3((-9.99, s * 0.64, 0.98)), (2.2, 0.14, 0.14), 0.01, 'frame')
        for xx in (-9.0, -9.45, -9.9, -10.35, -10.8):
            m.cyl(V3((xx, s * 0.71, 0.98)), V3((xx, s * 0.74, 0.98)), 0.013, 'steel', seg=10)
    for x in (-6.2, -7.2, -8.2, -9.2, -10.2, -10.85):
        m.rbox(V3((x, 0, 1.16)), (0.09, 0.92, 0.20), 0.008, 'frame')
    for ax_x in (D.T1_X, D.T2_X):
        z = D.ZC
        m.cyl(V3((ax_x, -0.80, z)), V3((ax_x, 0.80, z)), 0.068, 'steel_dark', seg=28)
        for s in (1, -1):
            m.cyl(V3((ax_x, s * 0.50, z)), V3((ax_x, s * 0.80, z)), 0.082, 'steel_dark', seg=24)
            m.rbox(V3((ax_x - 0.10, s * 0.62, z + 0.02)), (0.36, 0.10, 0.12), 0.01, 'frame')                    # air-ride trailing arm
            m.cyl(V3((ax_x - 0.31, s * 0.72, z + 0.06)), V3((ax_x - 0.47, s * 0.72, z + 0.06)), 0.075, 'steel_dark', seg=24)    # brake chamber
            m.cyl(V3((ax_x - 0.47, s * 0.72, z + 0.06)), V3((ax_x - 0.64, s * 0.72, z + 0.06)), 0.060, 'steel', seg=24)
            m.cyl(V3((ax_x - 0.12, s * 0.62, z + 0.20)), V3((ax_x - 0.12, s * 0.62, 1.04)), 0.12, 'black', seg=24)       # the air spring
            m.cyl(V3((ax_x - 0.12, s * 0.62, z + 0.20)), V3((ax_x - 0.12, s * 0.62, z + 0.23)), 0.14, 'steel', seg=24)
            CK_dm = (V3((ax_x + 0.12, s * 0.56, z + 0.04)), V3((ax_x + 0.16, s * 0.50, 1.05)))
            m.cyl(CK_dm[0], CK_dm[1], 0.026, 'black', seg=14)
    # the rear bumper (ICC, 4" tube) with its brackets and a reflective chevron panel above the tail lamps
    bx = X_REAR - 0.25
    m.cyl(V3((bx, -1.12, 0.78)), V3((bx, 1.12, 0.78)), 0.050, 'steel', seg=20)
    for s in (1, -1):
        m.rbox(V3((bx + 0.12, s * 0.80, 0.90)), (0.26, 0.05, 0.28), 0.008, 'frame')
        m.cyl(V3((bx, s * 1.12, 0.78)), V3((bx, s * 1.12, 0.60)), 0.05, 'steel', seg=20)
    m.rbox(V3((X_REAR + 0.05, 0, 1.21)), (0.12, 2.12, 0.14), 0.01, 'frame')
    return m


def fender_z(x):
    """Height of the tandem fender's top along x: an arch of 0.64 m radius over each wheel, a flat hump of 1.15 m between and beyond."""
    d = min(abs(x - D.T1_X), abs(x - D.T2_X))
    if d < 0.64:
        return max(1.15, D.ZC + math.sqrt(0.64 ** 2 - d * d))
    return 1.15


def trailer_fenders():
    f = Mesh()
    fl = Mesh()
    nk = 60
    for s in (1, -1):
        x0, x1 = D.T2_X - 0.62, D.T1_X + 0.62
        yc, w = s * D.DRIVE_Y, 0.78
        for lift, flip in ((0.0, False), (0.012, True)):
            rows = []
            for j in range(5):
                u = -1 + 2 * j / 4
                rows.append([V3((x0 + (x1 - x0) * k / nk, yc + u * w / 2, fender_z(x0 + (x1 - x0) * k / nk) + 0.045 * (1 - u * u) + lift)) for k in range(nk + 1)])
            f.grid(list(reversed(rows)) if flip else rows, 'steel')
        for u in (-1, 1):
            path = [V3((x0 + (x1 - x0) * k / nk, yc + u * w / 2, fender_z(x0 + (x1 - x0) * k / nk) + 0.006)) for k in range(nk + 1)]
            f.tube(path, 0.009, 'steel', seg=8)
    # mud flaps behind the rear axle: hangers, rubber, a bright strip, bolts
    for s in (1, -1):
        x = D.T2_X - 0.70
        y = s * D.DRIVE_Y
        fl.cyl(V3((x + 0.02, y - 0.40, 0.84)), V3((x + 0.02, y + 0.40, 0.84)), 0.012, 'steel', seg=10)
        for yy in (-0.38, 0.38):
            fl.cyl(V3((x + 0.02, y + yy, 0.84)), V3((x + 0.02, y + yy, 1.08)), 0.011, 'steel', seg=8)
        fl.rbox(V3((x, y, 0.53)), (0.012, 0.66, 0.62), 0.004, 'blackmat')
        fl.rbox(V3((x - 0.0075, y, 0.82)), (0.003, 0.60, 0.03), 0.001, 'steel')
        for dy in (-0.26, 0.26):
            for dz in (0.34, 0.74):
                P.hex_bolt(fl, V3((x - 0.006, y + dy, dz)), V3((-1, 0, 0)), 0.009, 0.005, 'steel')
    return f, fl


def run(root):
    tl = T.find('Trailer')
    sm = shell_mesh()
    stiffeners(sm)
    shell = sm.finish('TankShell', tl, sharp=60, box_uv=False)
    T.log('shell polys', len(shell.data.polygons), 'capacity gal', round(capacity_gal(), 1), 'barrel', round(L_BARREL, 3), 'rear x', round(X_REAR, 3))
    frame_mesh().finish('Frame_Trailer', tl, sharp=45)
    f, fl = trailer_fenders()
    f.finish('Fenders_Trailer', tl, sharp=50)
    fl.finish('MudFlaps_Trailer', tl, sharp=50)
    # a tank-volume proxy for the game's fill/leak logic: the nodes carry the numbers as custom properties
    shell['capacity_us_gal'] = round(capacity_gal(), 1)
    shell['capacity_litres'] = round(capacity_gal() * 3.785411784, 0)
    shell['compartments'] = NCOMP
