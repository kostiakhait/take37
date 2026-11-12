# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Stage interior: the cab inside. Floor with mat and the transmission tunnel, the dash with its gauge cluster (dials with ticks and needles), switches, the two push-pull park valves,
vents, the CB radio, the steering column and wheel (SteeringWheel pivot, spins about its local Z), pedals, the two gear levers, the air-ride driver's seat and the passenger bench,
the headliner, the visors, the back wall.

Nodes under Cab: Interior (empty) > Interior_Trim, Interior_Dash, Interior_Seats, Interior_Pedals, SteeringWheel (pivot) > SteeringWheel_Mesh, Gauges, Lever_Main, Lever_Range.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Quaternion

import carkit as CK
import parts as P
import tkit as T
from tkit import V3, Mesh

DRV_Y = 0.50                                 # driver's seat centre (left)


def gauge(m, c, r, kind_bezel='chrome'):
    """A dial on the dash facing -X (toward the driver): bezel ring, black face, 11 white ticks, a red needle, a glass lens."""
    ax = V3((-1, 0, 0))
    c = V3(c)
    P.ring_torus(m, c, ax, r, 0.0035, kind_bezel, seg=36, tseg=6)
    m.cyl(c + V3((0.001, 0, 0)), c + V3((-0.002, 0, 0)), r, 'gauge', seg=36)
    for k in range(11):
        a = math.radians(-120 + 240 * k / 10)
        d = V3((0, math.sin(a), math.cos(a)))
        m.box(c + V3((-0.0035, 0, 0)) + d * (r * 0.82), (0.0012, 0.0022, r * 0.16), 'paint_white', (V3((1, 0, 0)), V3((0, d.z, -d.y)), d))
    a = math.radians(-35)
    d = V3((0, math.sin(a), math.cos(a)))
    m.box(c + V3((-0.0045, 0, 0)) + d * (r * 0.38), (0.0012, 0.0035, r * 0.78), 'valve_red', (V3((1, 0, 0)), V3((0, d.z, -d.y)), d))
    m.cyl(c + V3((-0.0035, 0, 0)), c + V3((-0.0065, 0, 0)), r * 0.09, 'black', seg=12)
    m.cyl(c + V3((-0.0075, 0, 0)), c + V3((-0.0085, 0, 0)), r * 0.98, 'lens_clear', seg=36)


def steering_wheel_mesh():
    """Local frame: hub at the origin, wheel plane = XY, column toward -Z (the driver is at +Z). Radius 0.2286 (18 in), a 4-spoke wheel with a padded black rim."""
    m = Mesh()
    P.ring_torus(m, V3((0, 0, 0)), V3((0, 0, 1)), 0.2286, 0.0165, 'black', seg=72, tseg=12)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        d = V3((math.cos(a), math.sin(a), 0))
        m.tube([d * 0.04 + V3((0, 0, -0.012)), d * 0.12 + V3((0, 0, -0.006)), d * 0.2286 + V3((0, 0, 0))], [0.012, 0.010, 0.009], 'black', seg=10)
    P.capsule(m, V3((0, 0, -0.04)), V3((0, 0, 0.02)), 0.06, 'black', seg=36, dome=0.012)
    m.cyl(V3((0, 0, 0.03)), V3((0, 0, 0.033)), 0.036, 'chrome', seg=24)
    m.cyl(V3((0, 0, -0.04)), V3((0, 0, -0.12)), 0.04, 'black', seg=18)
    return m


def build_dash():
    m = Mesh()
    # a moulded dash panel across the cowl with the instrument pod in front of the driver
    xb = 0.84
    rows = []
    for k in range(13):
        u = -1 + 2 * k / 12
        y = u * 1.045
        top = 1.82 + 0.015 * (1 - u * u)
        rows.append([V3((xb + 0.06, y, top - 0.02)), V3((xb - 0.05, y, top + 0.005)), V3((xb - 0.19, y, top - 0.04)), V3((xb - 0.24, y, top - 0.12)), V3((xb - 0.23, y, 1.45)),
                     V3((xb - 0.05, y, 1.40)), V3((xb + 0.06, y, 1.40))])
    m.loft(rows, 'dash', closed=False, caps=False)
    # the pod over the driver's dials
    m.rbox(V3((xb - 0.19, DRV_Y, 1.80)), (0.18, 0.62, 0.20), 0.05, 'dash')
    # six dials on the pod: speedometer and tachometer large, four small ones between them
    xg = xb - 0.285
    gauge(m, V3((xg, DRV_Y + 0.17, 1.80)), 0.062)
    gauge(m, V3((xg, DRV_Y - 0.17, 1.80)), 0.062)
    for k, (dy, dz) in enumerate(((0.045, 1.835), (-0.045, 1.835), (0.045, 1.765), (-0.045, 1.765))):
        gauge(m, V3((xg, DRV_Y + dy * 1.0, dz)), 0.030)
    # the radio and CB on a bracket, the heater control panel, switches, vents
    m.rbox(V3((xb - 0.15, -0.30, 1.62)), (0.12, 0.34, 0.12), 0.012, 'black')
    m.rbox(V3((xb - 0.2105, -0.30, 1.62)), (0.002, 0.30, 0.09), 0.004, 'steel_dark')
    for k in range(4):
        m.cyl(V3((xb - 0.212, -0.42 + 0.08 * k, 1.62)), V3((xb - 0.226, -0.42 + 0.08 * k, 1.62)), 0.016, 'black', seg=14)
    m.cyl(V3((xb - 0.212, -0.30, 1.585)), V3((xb - 0.232, -0.30, 1.585)), 0.01, 'steel', seg=10)
    m.rbox(V3((xb - 0.21, 0.0, 1.62)), (0.04, 0.56, 0.10), 0.01, 'dash')
    for k in range(6):
        m.rbox(V3((xb - 0.233, -0.22 + 0.088 * k, 1.62)), (0.012, 0.04, 0.03), 0.004, 'black')
        m.cyl(V3((xb - 0.233, -0.22 + 0.088 * k, 1.645)), V3((xb - 0.237, -0.22 + 0.088 * k, 1.645)), 0.003, 'lens_amber', seg=6)
    for y in (-0.62, -0.78, 0.9):
        m.rbox(V3((xb - 0.23, y, 1.70)), (0.015, 0.12, 0.05), 0.01, 'black')
        for k in range(5):
            m.rbox(V3((xb - 0.239, y, 1.685 + 0.01 * k)), (0.004, 0.10, 0.003), 0.0005, 'dash')
    # the two push-pull air valves: yellow diamond (trailer supply) and red octagon (parking), on stems
    m.cyl(V3((xb - 0.22, 0.18, 1.55)), V3((xb - 0.30, 0.18, 1.55)), 0.006, 'steel', seg=8)
    m.rbox(V3((xb - 0.315, 0.18, 1.55)), (0.02, 0.045, 0.045), 0.006, 'safety_yellow', (V3((1, 0, 0)), V3((0, 0.7071, 0.7071)), V3((0, -0.7071, 0.7071))))
    m.cyl(V3((xb - 0.22, 0.28, 1.55)), V3((xb - 0.30, 0.28, 1.55)), 0.006, 'steel', seg=8)
    m.cyl(V3((xb - 0.30, 0.28, 1.55)), V3((xb - 0.32, 0.28, 1.55)), 0.026, 'valve_red', seg=8)
    return m


def build_trim():
    m = Mesh()
    # floor mat over the floor plate, the transmission tunnel (the "doghouse"), rubber heel mats, footrest, the kick panels
    m.rbox(V3((0.15, 0, 1.012)), (1.40, 2.08, 0.024), 0.006, 'cloth')
    m.rbox(V3((0.62, 0.0, 1.22)), (0.55, 0.62, 0.42), 0.05, 'dash')
    m.rbox(V3((0.62, 0.0, 1.435)), (0.57, 0.64, 0.02), 0.01, 'fabric')
    for s in (1, -1):
        m.rbox(V3((0.60, s * 0.50, 1.027)), (0.55, 0.5, 0.012), 0.004, 'rubber')
        for k in range(8):
            m.rbox(V3((0.45 + 0.04 * k, s * 0.50, 1.036)), (0.012, 0.45, 0.004), 0.001, 'blackmat')
        m.rbox(V3((0.80, s * 0.92, 1.26)), (0.16, 0.20, 0.50), 0.02, 'dash')
    # headliner: a quilted panel under the roof with a centre console (map lamp, CB mic hook) and the dome light
    zr = 2.915
    rows = []
    for k in range(11):
        u = -1 + 2 * k / 10
        rows.append([V3((x, u * 1.02, zr + 0.0 - 0.02 * u * u + 0.0 * x - (0.0 if x < 0.7 else 0.86 * (x - 0.70) / 0.28))) for x in (-0.56, -0.2, 0.2, 0.6, 0.70)])
    m.loft(rows, 'headliner', closed=False)
    m.rbox(V3((0.0, 0.0, 2.905)), (0.45, 0.20, 0.03), 0.01, 'bulb')
    m.rbox(V3((0.0, 0.0, 2.918)), (0.5, 0.24, 0.012), 0.004, 'steel_dark')
    # back wall: a padded panel with the rear window's trim, a storage shelf behind the seats and a dome-light
    m.rbox(V3((-0.572, 0, 1.75)), (0.02, 2.04, 0.90), 0.01, 'fabric')
    m.rbox(V3((-0.50, 0, 2.18)), (0.12, 2.0, 0.025), 0.006, 'dash')
    # sun visors: two padded boards on arms
    for s in (1, -1):
        m.rbox(V3((0.64, s * 0.55, 2.80)), (0.02, 0.50, 0.24), 0.012, 'headliner', (V3((0.9, 0, -0.43)).normalized(), V3((0, 1, 0)), V3((0.43, 0, 0.9)).normalized()))
        m.cyl(V3((0.60, s * 0.30, 2.90)), V3((0.64, s * 0.30, 2.85)), 0.006, 'steel', seg=8)
    # a shift boot and the gear levers' base, parking brake and a cup holder with an ashtray tray
    m.rbox(V3((0.40, 0.17, 1.46)), (0.10, 0.10, 0.04), 0.01, 'blackmat')
    m.rbox(V3((0.55, -0.25, 1.46)), (0.14, 0.14, 0.03), 0.008, 'dash')
    P.ring_torus(m, V3((0.55, -0.25, 1.462)), V3((0, 0, 1)), 0.045, 0.008, 'steel_dark', seg=24, tseg=6)
    # the grab handle on the A-pillars inside and the coat hook
    for s in (1, -1):
        m.tube([V3((0.78, s * 1.04, 1.85)), V3((0.82, s * 1.05, 2.30)), V3((0.85, s * 1.04, 2.50))], 0.012, 'chrome', seg=8)
    return m


def build_seats():
    m = Mesh()
    for y, wid, tag in ((DRV_Y, 0.52, 'driver'), (-0.50, 0.52, 'pass')):
        sx = -0.12
        zb = 1.32 if tag == 'driver' else 1.28
        # base: an air-ride pedestal with a scissor mechanism, rails and a black bellows
        m.rbox(V3((sx, y, 1.04)), (0.55, 0.5, 0.05), 0.01, 'steel_dark')
        m.rbox(V3((sx, y, zb - 0.09)), (0.50, 0.46, 0.05), 0.01, 'steel_dark')
        for s2 in (1, -1):
            m.cyl(V3((sx - 0.12, y + s2 * 0.19, 1.07)), V3((sx + 0.12, y + s2 * 0.19, zb - 0.11)), 0.012, 'steel', seg=8)
            m.cyl(V3((sx + 0.12, y + s2 * 0.19, 1.07)), V3((sx - 0.12, y + s2 * 0.19, zb - 0.11)), 0.012, 'steel', seg=8)
        m.cyl(V3((sx, y, 1.06)), V3((sx, y, zb - 0.11)), 0.10, 'blackmat', seg=24)
        # cushion with pleats and piping, the bolstered back, a headrest, armrests (driver)
        CK.cushion(m, V3((sx + 0.02, y, zb)), V3((1, 0, 0)), V3((0, 1, 0)), V3((0, 0, 1)), 0.52, wid, 0.12, pleats=6, kind='seat', piping='seat', crown=0.018)
        ez = V3((0.966, 0, 0.26)).normalized()
        ex = V3((0, 1, 0))
        ey = ez.cross(ex)
        CK.cushion(m, V3((sx - 0.30, y, zb + 0.34)), V3((0, 1, 0)), V3((-0.26, 0, 0.966)), ez, wid, 0.62, 0.11, pleats=7, kind='seat', piping='seat', crown=0.02)
        CK.cushion(m, V3((sx - 0.37, y, zb + 0.78)), V3((0, 1, 0)), V3((-0.26, 0, 0.966)), ez, 0.26, 0.20, 0.09, pleats=3, kind='seat', piping='seat', crown=0.015)
        m.cyl(V3((sx - 0.35, y - 0.06, zb + 0.62)), V3((sx - 0.37, y - 0.06, zb + 0.68)), 0.008, 'chrome', seg=8)
        m.cyl(V3((sx - 0.35, y + 0.06, zb + 0.62)), V3((sx - 0.37, y + 0.06, zb + 0.68)), 0.008, 'chrome', seg=8)
        if tag == 'driver':
            for s2 in (1, -1):
                m.rbox(V3((sx - 0.12, y + s2 * 0.30, zb + 0.20)), (0.40, 0.07, 0.05), 0.02, 'seat')
                m.rbox(V3((sx - 0.12, y + s2 * 0.27, zb + 0.10)), (0.03, 0.03, 0.18), 0.006, 'steel_dark')
        # a seat belt: a black strap from the shoulder bolt with a buckle (lap + sash)
        m.tube([V3((sx - 0.40, y - 0.22, zb + 0.78)), V3((sx - 0.32, y - 0.12, zb + 0.50)), V3((sx - 0.08, y + 0.14, zb + 0.14))], 0.016, 'blackmat', seg=4)
        m.rbox(V3((sx - 0.08, y + 0.15, zb + 0.14)), (0.04, 0.05, 0.02), 0.004, 'steel')
    return m


def build_pedals():
    m = Mesh()
    y = DRV_Y
    # three pedals on pivot arms through the firewall: clutch, brake, accelerator
    for dy, wid in ((-0.16, 0.11), (0.0, 0.14), (0.15, 0.07)):
        pc = V3((0.58, y + dy, 1.12))
        m.cyl(V3((0.85, y + dy, 1.40)), pc, 0.012, 'steel_dark', seg=8)
        m.rbox(pc + V3((-0.0, 0, 0.0)), (0.02, wid, 0.16), 0.01, 'steel_dark', (V3((0.866, 0, 0.5)), V3((0, 1, 0)), V3((-0.5, 0, 0.866))))
        for k in range(4):
            m.rbox(pc + V3((-0.0012, 0, -0.06 + 0.04 * k)), (0.004, wid - 0.02, 0.006), 0.001, 'rubber')
    m.rbox(V3((0.58, y - 0.28, 1.12)), (0.04, 0.13, 0.12), 0.012, 'rubber')                 # the dead pedal / footrest
    return m


def build_levers():
    a = Mesh()
    b = Mesh()
    # main gear lever with a knob (13-speed pattern on the knob), and the range selector toggle beside it
    a.cyl(V3((0.40, 0.17, 1.46)), V3((0.32, 0.17, 1.82)), 0.011, 'steel', seg=10)
    a.cyl(V3((0.32, 0.17, 1.82)), V3((0.318, 0.17, 1.83)), 0.011, 'steel', seg=10)
    P.capsule(a, V3((0.317, 0.17, 1.83)), V3((0.311, 0.17, 1.87)), 0.027, 'black', seg=20, dome=0.012)
    b.cyl(V3((0.395, 0.24, 1.47)), V3((0.38, 0.24, 1.60)), 0.007, 'steel', seg=8)
    P.capsule(b, V3((0.38, 0.24, 1.60)), V3((0.378, 0.24, 1.62)), 0.012, 'black', seg=12, dome=0.006)
    return a, b


def run(root):
    cab = T.find('Cab')
    ia = T.empty('Interior', V3((0, 0, 0)), cab)
    build_dash().finish('Interior_Dash', ia, sharp=50)
    build_trim().finish('Interior_Trim', ia, sharp=50)
    build_seats().finish('Interior_Seats', ia, sharp=60)
    build_pedals().finish('Interior_Pedals', ia, sharp=50)
    la, lb = build_levers()
    la.finish('Lever_Main', ia, sharp=50)
    lb.finish('Lever_Range', ia, sharp=50)
    # steering column and wheel: the column's axis from the dash to the hub, the wheel pivots about its own Z
    hub = V3((0.50, DRV_Y, 1.72))
    base = V3((0.80, DRV_Y, 1.40))
    d = (hub - base).normalized()
    colm = Mesh()
    colm.cyl(base, hub - d * 0.02, 0.038, 'black', seg=24)
    colm.cyl(base + d * 0.08, base + d * 0.14, 0.050, 'black', seg=24)
    colm.rbox(hub - d * 0.10 + V3((0, 0, 0.06)), (0.06, 0.06, 0.12), 0.01, 'black')                 # stalk switch housing
    colm.tube([hub - d * 0.10 + V3((0, 0.02, 0.06)), hub - d * 0.10 + V3((0, 0.13, 0.06))], 0.007, 'black', seg=8)
    colm.tube([hub - d * 0.10 + V3((0, -0.02, 0.06)), hub - d * 0.10 + V3((0, -0.13, 0.05))], 0.007, 'black', seg=8)
    colm.finish('SteeringColumn', ia, sharp=50)
    sw = T.empty('SteeringWheel', hub, ia)
    sw.rotation_mode = 'QUATERNION'
    sw.rotation_quaternion = V3((0, 0, 1)).rotation_difference(d)
    wm = steering_wheel_mesh()
    bmesh.ops.translate(wm.bm, vec=hub, verts=wm.bm.verts)
    wm.finish('SteeringWheel_Mesh', sw, sharp=55)
