# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Stage fittings: everything on the tank. Five manhole domes (Dome_1..5: collar, flange with bolts, rollover ring, vapour probe) each with its own hinged hatch node (Hatch_1..5: cover,
gasket, hinge, swing bolts, vent; pivot at the hinge, opens about Y), the rollover rails (Rail_L / Rail_R) with posts, the rear ladder (Ladder_Rear), the delivery piping: four side outlets
(Valve_1..4: internal emergency valve, drop pipe, bottom valve with its pull handle, API adapter with a chained dust cap), the rear outlet (Valve_5), the hose tube (HoseTube) and the hoses,
the vapour-recovery manifold and the fusible shut-off link.

All nodes are children of Trailer, so the game can break the trailer away as one piece.
"""
import math

import bpy
from mathutils import Matrix

import dims as D
import parts as P
import st_tank as K
import tkit as T
from tkit import V3, Mesh

Z_TOP = K.ZC_TANK + K.B_HALF                      # the shell's top on the centre line


def dome(i, x):
    m = Mesh()
    zb = Z_TOP - 0.03
    # reinforcing pad welded to the shell, the collar, the rolled flange, the coaming's drain notch, the rollover ring
    m.cyl(V3((x, 0, zb)), V3((x, 0, zb + 0.020)), 0.40, 'alu', seg=48, r1=0.37)
    m.cyl(V3((x, 0, zb)), V3((x, 0, zb + 0.20)), 0.318, 'alu', seg=48)
    m.cyl(V3((x, 0, zb + 0.20)), V3((x, 0, zb + 0.215)), 0.352, 'alu', seg=48)
    P.ring_torus(m, V3((x, 0, zb + 0.062)), V3((0, 0, 1)), 0.318, 0.012, 'alu', seg=64, tseg=8)
    P.weld_bead(m, [V3((x + 0.322 * math.cos(2 * math.pi * k / 64), 0.322 * math.sin(2 * math.pi * k / 64), zb + 0.021)) for k in range(65)], 0.0045, 'alu')
    for k in range(16):                                                           # the flange bolts
        a = 2 * math.pi * (k + 0.5) / 16
        P.hex_bolt(m, V3((x + 0.335 * math.cos(a), 0.335 * math.sin(a), zb + 0.215)), V3((0, 0, 1)), 0.0095, 0.0075, 'steel')
    for k in range(40):                                                           # rivets round the pad
        a = 2 * math.pi * (k + 0.5) / 40
        P.rivet(m, V3((x + 0.385 * math.cos(a), 0.385 * math.sin(a), zb + 0.0105 + 0.0)), V3((0, 0, 1)), 0.005, 'steel', seg=6)
    # rollover protection: a raised ring on four legs round the dome
    P.ring_torus(m, V3((x, 0, zb + 0.34)), V3((0, 0, 1)), 0.395, 0.019, 'alu', seg=64, tseg=8)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        p0 = V3((x + 0.40 * math.cos(a), 0.40 * math.sin(a), zb + 0.02))
        p1 = V3((x + 0.395 * math.cos(a), 0.395 * math.sin(a), zb + 0.34))
        m.cyl(p0, p1, 0.016, 'alu', seg=10)
    # the vapour probe: a 4 inch adapter on the dome shoulder with a dust cap on a chain
    pa = V3((x + 0.0, 0.46, zb - 0.0))
    m.cyl(pa, pa + V3((0, 0, 0.12)), 0.050, 'alu', seg=24)
    m.cyl(pa + V3((0, 0, 0.12)), pa + V3((0, 0, 0.14)), 0.066, 'alu', seg=24)
    m.cyl(pa + V3((0, 0, 0.14)), pa + V3((0, 0, 0.18)), 0.060, 'steel', seg=24)
    return m


def hatch(i, x):
    """Local frame: world; the hinge axis at x - 0.30 along Y at z top of the dome."""
    zb = Z_TOP - 0.03 + 0.215
    hx = x - 0.34
    m = Mesh()
    # lid: a domed disc 0.32 radius with a rolled edge, gasket below, the vent in the middle, the handle, four swing bolts with wing nuts, the hinge lugs
    rows = []
    for k in range(8):
        r = 0.355 * (1 - k / 8) ** 0.8 if k else 0.355
        z = zb + 0.012 + 0.045 * (1 - (r / 0.355) ** 2)
        rows.append([V3((x + r * math.cos(2 * math.pi * j / 64), r * math.sin(2 * math.pi * j / 64), z)) for j in range(64)])
    rows.append([V3((x + 0.0001 * math.cos(2 * math.pi * j / 64), 0.0001 * math.sin(2 * math.pi * j / 64), zb + 0.057)) for j in range(64)])
    m.loft(rows, 'alu')
    P.ring_torus(m, V3((x, 0, zb + 0.012)), V3((0, 0, 1)), 0.352, 0.0085, 'alu', seg=64, tseg=8)
    P.ring_torus(m, V3((x, 0, zb + 0.004)), V3((0, 0, 1)), 0.332, 0.006, 'blackmat', seg=64, tseg=6)               # the gasket
    # the vent: an emergency pressure/vacuum cap on a stub
    m.cyl(V3((x, 0, zb + 0.056)), V3((x, 0, zb + 0.09)), 0.05, 'steel', seg=24)
    P.capsule(m, V3((x, 0, zb + 0.09)), V3((x, 0, zb + 0.115)), 0.062, 'steel', seg=24, dome=0.03)
    for k in range(6):
        a = 2 * math.pi * k / 6
        m.cyl(V3((x + 0.04 * math.cos(a), 0.04 * math.sin(a), zb + 0.115)), V3((x + 0.04 * math.cos(a), 0.04 * math.sin(a), zb + 0.14)), 0.0035, 'steel', seg=6)
    m.cyl(V3((x - 0.17, 0.0, zb + 0.052)), V3((x + 0.17, 0.0, zb + 0.052)), 0.012, 'steel', seg=10)       # the carrying handle
    for dx in (-0.17, 0.17):
        m.cyl(V3((x + dx, 0, zb + 0.040)), V3((x + dx, 0, zb + 0.052)), 0.012, 'steel', seg=10)
    # swing bolts with wing nuts on the front half of the ring, hinge ears at the back
    for k in range(4):
        a = math.radians((-45, -15, 15, 45)[k])
        p = V3((x + 0.37 * math.cos(a), 0.37 * math.sin(a), zb + 0.015))
        m.rbox(p, (0.05, 0.03, 0.022), 0.006, 'steel', (V3((math.cos(a), math.sin(a), 0)), V3((-math.sin(a), math.cos(a), 0)), V3((0, 0, 1))))
        m.cyl(p, p + V3((0, 0, 0.032)), 0.0065, 'steel', seg=8)
        m.rbox(p + V3((0, 0, 0.036)), (0.012, 0.05, 0.018), 0.004, 'steel_dark', (V3((1, 0, 0)), V3((0, 1, 0)), V3((0, 0, 1))))
    for s in (1, -1):
        m.rbox(V3((hx + 0.02, s * 0.12, zb + 0.008)), (0.06, 0.04, 0.03), 0.008, 'steel')
        m.cyl(V3((hx, s * 0.14, zb + 0.02)), V3((hx, s * 0.10, zb + 0.02)), 0.011, 'steel', seg=10)
    # a bright reflective placard patch on the lid: the compartment number
    return m


def valve_assembly(i, x, side):
    """Compartment i's bottom outlet. side = +1 left, 0 the rear (compartment 5)."""
    m = Mesh()
    sx = x
    # the internal emergency valve is under the sump (z 1.205); the drop pipe goes down to z 0.96, runs out sideways under the rail, rises to the valve at the edge
    zs, zp = 1.205, 0.96
    if side > 0:
        y1 = 1.08
        m.cyl(V3((sx, 0, zs)), V3((sx, 0, zp)), 0.050, 'alu', seg=20)
        P.band(m, V3((sx, 0, zs - 0.03)), V3((0, 0, 1)), 0.052, 0.035, 0.006, 'steel', seg=20)
        m.cyl(V3((sx, 0, zp)), V3((sx, y1 - 0.06, zp)), 0.050, 'alu', seg=20)
        m.cyl(V3((sx, y1 - 0.06, zp)), V3((sx, y1, zp)), 0.058, 'steel', seg=24)                       # the bottom valve body
        m.rbox(V3((sx, y1 - 0.03, zp)), (0.12, 0.09, 0.12), 0.02, 'steel')
        for a in range(6):
            P.hex_bolt(m, V3((sx + 0.052 * math.cos(math.pi / 3 * a), y1 - 0.075, zp + 0.052 * math.sin(math.pi / 3 * a))), V3((0, -1, 0)), 0.007, 0.006, 'steel')
        # the pull handle (red) with an eye, the shaft through the body
        m.cyl(V3((sx - 0.07, y1 - 0.03, zp)), V3((sx + 0.07, y1 - 0.03, zp)), 0.009, 'steel', seg=8)
        m.tube([V3((sx + 0.07, y1 - 0.03, zp)), V3((sx + 0.13, y1 - 0.03, zp + 0.09)), V3((sx + 0.12, y1 - 0.03, zp + 0.20))], 0.012, 'valve_red', seg=8)
        P.ring_torus(m, V3((sx + 0.12, y1 - 0.03, zp + 0.22)), V3((0, 1, 0)), 0.022, 0.006, 'valve_red', seg=16, tseg=6)
        # the outlet: elbow out, a 4 inch API adapter (cam-and-groove coupling) with a cap on a chain
        m.cyl(V3((sx, y1, zp)), V3((sx, y1 + 0.10, zp)), 0.054, 'alu', seg=24)
        m.cyl(V3((sx, y1 + 0.10, zp)), V3((sx, y1 + 0.135, zp)), 0.066, 'steel', seg=24)
        m.cyl(V3((sx, y1 + 0.135, zp)), V3((sx, y1 + 0.20, zp)), 0.057, 'steel', seg=24)
        m.rbox(V3((sx - 0.07, y1 + 0.17, zp)), (0.02, 0.06, 0.03), 0.005, 'steel_dark')
        m.rbox(V3((sx + 0.07, y1 + 0.17, zp)), (0.02, 0.06, 0.03), 0.005, 'steel_dark')
        m.cyl(V3((sx, y1 + 0.20, zp)), V3((sx, y1 + 0.235, zp)), 0.070, 'black', seg=24)                     # the dust cap
        m.cyl(V3((sx, y1 + 0.235, zp)), V3((sx, y1 + 0.245, zp)), 0.050, 'black', seg=18)
        m.tube([V3((sx, y1 + 0.12, zp + 0.06)), V3((sx + 0.05, y1 + 0.17, zp + 0.14)), V3((sx + 0.02, y1 + 0.215, zp + 0.065))], 0.0035, 'steel', seg=5)
        # a clamp strap to the shell side and a drip catch under it
        m.rbox(V3((sx, y1 + 0.075, zp - 0.075)), (0.16, 0.20, 0.012), 0.004, 'steel_dark')
        # the compartment's number plate
    else:
        m.cyl(V3((sx, 0, zs)), V3((sx, 0, zp)), 0.050, 'alu', seg=20)
        m.cyl(V3((sx, 0, zp)), V3((K.X_REAR - 0.10, 0, zp)), 0.050, 'alu', seg=20)
        xo = K.X_REAR - 0.10
        m.rbox(V3((xo - 0.03, 0, zp)), (0.09, 0.12, 0.12), 0.02, 'steel')
        m.cyl(V3((xo - 0.06, 0, zp)), V3((xo - 0.18, 0, zp)), 0.058, 'alu', seg=24)
        m.cyl(V3((xo - 0.18, 0, zp)), V3((xo - 0.215, 0, zp)), 0.068, 'steel', seg=24)
        m.cyl(V3((xo - 0.215, 0, zp)), V3((xo - 0.26, 0, zp)), 0.060, 'steel', seg=24)
        m.cyl(V3((xo - 0.26, 0, zp)), V3((xo - 0.295, 0, zp)), 0.072, 'black', seg=24)
        m.tube([V3((xo - 0.03, 0.0, zp + 0.06)), V3((xo - 0.02, 0.06, zp + 0.17)), V3((xo - 0.03, 0.14, zp + 0.24))], 0.012, 'valve_red', seg=8)
        P.ring_torus(m, V3((xo - 0.03, 0.15, zp + 0.255)), V3((1, 0, 0)), 0.022, 0.006, 'valve_red', seg=16, tseg=6)
    return m


def hose_tube_and_hoses():
    m = Mesh()
    # a hose tube (a 6 inch aluminium tube with a capped end) hung under the right side of the tank, and the hoses on a rack at the rear
    x0, x1, y, z = -4.30, -8.35, -1.02, 1.18
    m.cyl(V3((x0, y, z)), V3((x1, y, z)), 0.115, 'alu', seg=40)
    m.cyl(V3((x1 + 0.05, y, z)), V3((x1 + 0.06, y, z)), 0.105, 'blackmat', seg=32)
    for xx in (-4.9, -6.5, -8.0):
        P.band(m, V3((xx, y, z)), V3((1, 0, 0)), 0.115, 0.07, 0.006, 'steel', seg=32)
        m.rbox(V3((xx, y + 0.0, z + 0.17)), (0.07, 0.04, 0.12), 0.006, 'steel_dark')
    m.cyl(V3((x0 + 0.03, y, z)), V3((x0 + 0.05, y, z)), 0.125, 'black', seg=32)
    # the delivery hoses: the tube's rear end is open and a 4 inch hose is half drawn out of it, looped and laid on a hose saddle, brass cam-lock couplings on both ends
    e = V3((x1 - 0.02, y, z))
    P.ring_torus(m, e + V3((-0.0, 0, 0)), V3((1, 0, 0)), 0.095, 0.014, 'steel', seg=32, tseg=6)
    path = [e + V3((0.30, 0.0, 0.0)), e + V3((-0.10, 0.0, 0.0)), e + V3((-0.35, -0.01, -0.01)), e + V3((-0.55, -0.08, -0.06)), e + V3((-0.72, -0.18, -0.20)), e + V3((-0.60, -0.28, -0.38)),
            e + V3((-0.38, -0.25, -0.46)), e + V3((-0.30, -0.12, -0.35))]
    m.tube(path, 0.047, 'hose', seg=14, cap=True)
    for p, d in ((path[0], V3((1, 0, 0))), (path[-1], V3((0.3, 0.5, 0.8)))):
        m.cyl(p, p + d.normalized() * 0.07, 0.056, 'brass', seg=18)
        m.cyl(p + d.normalized() * 0.07, p + d.normalized() * 0.085, 0.062, 'brass', seg=18)
    m.rbox(e + V3((-0.30, -0.12, -0.50)), (0.30, 0.16, 0.02), 0.006, 'steel_dark')
    return m


def rails():
    out = []
    for s in (1, -1):
        m = Mesh()
        y = s * 0.52
        x0, x1 = K.X_BARREL0 - 0.30, K.X_BARREL1 + 0.35

        def top_z(yy):
            r = min(abs(yy) / K.A_HALF, 0.999)
            return K.ZC_TANK + K.B_HALF * (1 - r ** K.PWR) ** (1 / K.PWR)
        zt = top_z(y)
        h = 0.62
        path = [V3((x0 + 0.20, y, zt + 0.0)), V3((x0, y, zt + h)), V3((x1, y, zt + h)), V3((x1 - 0.20, y, zt + 0.0))]
        m.tube(path, 0.0175, 'alu', seg=14, cap=True)
        m.tube([V3((x0 + 0.05, y, zt + 0.30)), V3((x1 - 0.05, y, zt + 0.30))], 0.014, 'alu', seg=12, cap=True)                  # the mid rail
        n = 7
        for k in range(n):
            xx = x0 + (x1 - x0) * k / (n - 1)
            m.cyl(V3((xx, y, zt - 0.005)), V3((xx, y, zt + h)), 0.016, 'alu', seg=12)
            m.cyl(V3((xx, y, zt - 0.003)), V3((xx, y, zt + 0.012)), 0.034, 'alu', seg=16)                                  # the foot
            for a in range(3):
                aa = 2 * math.pi * a / 3
                P.hex_bolt(m, V3((xx + 0.024 * math.cos(aa), y + 0.024 * math.sin(aa), zt + 0.012)), V3((0, 0, 1)), 0.0065, 0.005, 'steel', washer=False)
        out.append((s, m))
    return out


def ladder():
    m = Mesh()
    xl = K.X_REAR - 0.12
    z0, z1 = 0.98, 3.58
    # two stiles, rungs every 0.30 m (with a knurled tread), a top grab hoop; stand-off brackets to the head
    for y in (-0.22, 0.22):
        m.cyl(V3((xl, y, z0)), V3((xl, y, z1)), 0.020, 'alu', seg=14)
        for z in (1.45, 2.20, 2.95):
            m.rbox(V3((xl + 0.075, y, z)), (0.16, 0.026, 0.05), 0.006, 'alu')
            P.hex_bolt(m, V3((xl + 0.14, y, z + 0.0)), V3((1, 0, 0)), 0.008, 0.005, 'steel')
    z = z0 + 0.30
    while z < z1 - 0.05:
        m.cyl(V3((xl, -0.22, z)), V3((xl, 0.22, z)), 0.0145, 'alu', seg=12)
        for j in range(6):
            m.rbox(V3((xl, -0.18 + 0.072 * j, z + 0.014)), (0.014, 0.012, 0.004), 0.001, 'steel')
        z += 0.30
    m.tube([V3((xl, -0.22, z1)), V3((xl + 0.0, -0.22, z1 + 0.18)), V3((xl + 0.16, -0.22, z1 + 0.30)), V3((xl + 0.32, -0.22, z1 + 0.30))], 0.018, 'alu', seg=12, cap=True)
    m.tube([V3((xl, 0.22, z1)), V3((xl + 0.0, 0.22, z1 + 0.18)), V3((xl + 0.16, 0.22, z1 + 0.30)), V3((xl + 0.32, 0.22, z1 + 0.30))], 0.018, 'alu', seg=12, cap=True)
    # the ladder's foot guard: a bent bar so a bumper cannot hook the rungs
    m.tube([V3((xl - 0.02, -0.22, z0)), V3((xl - 0.02, 0.22, z0))], 0.016, 'steel', seg=10)
    return m


def vapor_manifold():
    m = Mesh()
    # vapour recovery: a 4 inch pipe along the top left of the shell, from the dome fittings to a coupler at the rear, held by saddles
    y = 0.80
    def z_at(yy):
        r = min(abs(yy) / K.A_HALF, 0.999)
        return K.ZC_TANK + K.B_HALF * (1 - r ** K.PWR) ** (1 / K.PWR)
    zt = z_at(y) + 0.075
    xs = [K.X_BARREL0 - 0.4, K.X_BARREL1 + 0.55]
    m.cyl(V3((xs[0], y, zt)), V3((xs[1], y, zt)), 0.05, 'alu', seg=24)
    for x in K.DOME_X:
        m.cyl(V3((x, 0.46, Z_TOP + 0.15)), V3((x, y, zt)), 0.03, 'alu', seg=14)
        m.rbox(V3((x, y, zt)), (0.14, 0.14, 0.14), 0.02, 'steel')
    for k in range(10):
        xx = xs[0] + (xs[1] - xs[0]) * (k + 0.5) / 10
        P.band(m, V3((xx, y, zt)), V3((1, 0, 0)), 0.05, 0.03, 0.005, 'steel', seg=20)
        m.cyl(V3((xx, y, zt - 0.05)), V3((xx, y, z_at(y) - 0.005)), 0.01, 'steel', seg=8)
    m.cyl(V3((xs[1], y, zt)), V3((xs[1] - 0.05, y, zt)), 0.062, 'steel', seg=24)
    m.cyl(V3((xs[1] - 0.05, y, zt)), V3((xs[1] - 0.085, y, zt)), 0.066, 'black', seg=24)
    # fusible link on a cable from the rear valve to the cab: a short bracket and cable loop at the rear
    m.cyl(V3((K.X_REAR - 0.01, 0.55, 1.12)), V3((K.X_REAR - 0.13, 0.55, 1.12)), 0.007, 'steel', seg=6)
    P.ring_torus(m, V3((K.X_REAR - 0.14, 0.55, 1.12)), V3((1, 0, 0)), 0.02, 0.004, 'steel', seg=16, tseg=6)
    return m


def run(root):
    tl = T.find('Trailer')
    for i, x in enumerate(K.DOME_X, 1):
        dome(i, x).finish(f'Dome_{i}', tl, sharp=55)
        hm = hatch(i, x)
        hx, hz = x - 0.34, Z_TOP - 0.03 + 0.215
        piv = T.empty(f'Hatch_{i}', V3((hx, 0, hz)), tl)
        hm.finish(f'Hatch_{i}_Mesh', piv, sharp=55, origin=V3((hx, 0, hz)))
        # origin of the pivot's mesh is at the hinge: the mesh's vertices are in the hinge's frame
    for i, x in enumerate(K.DOME_X[:4], 1):
        valve_assembly(i, x, 1).finish(f'Valve_{i}', tl, sharp=50)
    valve_assembly(5, K.DOME_X[4], 0).finish('Valve_5', tl, sharp=50)
    hose_tube_and_hoses().finish('HoseTube', tl, sharp=50)
    for s, m in rails():
        m.finish('Rail_' + ('L' if s > 0 else 'R'), tl, sharp=50)
    ladder().finish('Ladder_Rear', tl, sharp=50)
    vapor_manifold().finish('VaporLine', tl, sharp=50)
