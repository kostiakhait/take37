# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Stage chassis: the tractor's frame and everything under and beside it, and the fifth wheel.

Nodes (under Tractor): Chassis (frame rails with lightening holes, crossmembers, axles, springs, walking-beam tandem, driveline, engine, transmission, steering, brakes, steps, battery box,
air tanks, air dryer), FuelTank_L / FuelTank_R, Exhaust_L / Exhaust_R (muffler and stack), FifthWheel, Fenders_Rear, MudFlaps_Tractor, AirLines.
"""
import math

import bpy
from mathutils import Vector

import carkit as CK
import dims as D
import parts as P
import tkit as T
from tkit import V3, Mesh

FZ0, FZ1 = 0.80, 1.10                      # frame rail bottom / top
RAIL_Y = 0.43                              # outer face of the rails
FX0, FX1 = -4.30, 3.05


def frame_rails(m):
    for s in (1, -1):
        y = s * RAIL_Y
        # web with lightening holes
        P.perforated_plate(m, FX0, FX1, FZ0 + 0.011, FZ1 - 0.011, y, 0.0095, 0.115, 0.043, 'frame', sides=14, side=-s)
        for z in (FZ0, FZ1 - 0.011):                                         # flanges, inward
            m.rbox(V3((0.5 * (FX0 + FX1), s * (RAIL_Y - 0.0375), z + 0.0055)), (FX1 - FX0, 0.075, 0.011), 0.0025, 'frame')
        # the small rivets / bolts along the flanges where crossmembers and brackets are joined
    for x in (2.80, 1.62, 0.48, -0.72, -1.00, -3.42, -4.22):
        m.rbox(V3((x, 0, 0.5 * (FZ0 + FZ1) + 0.02)), (0.10, 2 * RAIL_Y - 0.02, 0.19 if x < 2 else 0.24), 0.008, 'frame')
        for s in (1, -1):                                                       # gusset plates with bolts
            m.rbox(V3((x, s * (RAIL_Y - 0.032), 0.5 * (FZ0 + FZ1) + 0.02)), (0.15, 0.010, 0.24), 0.004, 'frame')
            for dx, dz in ((-0.05, -0.08), (0.05, -0.08), (-0.05, 0.08), (0.05, 0.08)):
                P.hex_bolt(m, V3((x + dx, s * (RAIL_Y - 0.038), 0.5 * (FZ0 + FZ1) + 0.02 + dz)), V3((0, -s, 0)), 0.0085, 0.0065, 'steel')


def front_axle(m):
    x, z = D.STEER_X, D.ZC
    for s in (1, -1):
        P.ibeam(m, V3((x, s * 0.05, z + 0.01)), V3((x, s * 0.76, z + 0.03)), 0.11, 0.085, 0.017, 0.016, 'steel_dark', up=V3((1, 0, 0)))
        P.ibeam(m, V3((x, s * 0.76, z + 0.03)), V3((x, s * 0.845, z + 0.075)), 0.10, 0.08, 0.018, 0.016, 'steel_dark', up=V3((1, 0, 0)))
        # king pin boss, knuckle, spindle, wheel-end seal
        m.cyl(V3((x - 0.01, s * 0.86, z - 0.10)), V3((x - 0.01, s * 0.86, z + 0.19)), 0.05, 'steel_dark', seg=20)
        m.rbox(V3((x, s * 0.87, z + 0.01)), (0.14, 0.09, 0.24), 0.02, 'steel_dark')
        m.cyl(V3((x, s * 0.88, z)), V3((x, s * 0.96, z)), 0.045, 'steel', seg=20)
        # steering arm and tie rod behind the axle
        m.cyl(V3((x - 0.16, s * 0.88, z + 0.03)), V3((x - 0.20, s * 0.78, z + 0.03)), 0.017, 'steel_dark', seg=10)
        m.cyl(V3((x - 0.18, s * 0.80, z + 0.03)), V3((x - 0.19, s * 0.06, z + 0.03)), 0.019, 'steel', seg=12)
        # brake chamber and slack adjuster
        m.cyl(V3((x - 0.12, s * 0.70, z + 0.05)), V3((x - 0.27, s * 0.70, z + 0.05)), 0.075, 'steel_dark', seg=24)
        m.cyl(V3((x - 0.27, s * 0.70, z + 0.05)), V3((x - 0.285, s * 0.70, z + 0.05)), 0.060, 'steel', seg=24)
        m.cyl(V3((x - 0.10, s * 0.70, z + 0.05)), V3((x - 0.02, s * 0.76, z - 0.02)), 0.012, 'steel', seg=8)
        # leaf spring over the axle, U-bolts, hangers, shackle, shock
        sy = s * 0.62
        P.leaf_pack(m, V3((x, sy, z + 0.085)), 1.28, 0.09, 9, 0.011, 0.055)
        for dx in (-0.12, 0.12):
            m.box(V3((x + dx, sy, z + 0.20)), (0.025, 0.14, 0.035), 'steel')
            for yy in (-0.06, 0.06):
                m.cyl(V3((x + dx, sy + yy, z - 0.04)), V3((x + dx, sy + yy, z + 0.20)), 0.009, 'steel', seg=8)
        m.rbox(V3((x, sy, z + 0.135)), (0.23, 0.12, 0.035), 0.006, 'steel_dark')
        m.rbox(V3((x + 0.80, s * 0.50, FZ0 - 0.04)), (0.16, 0.12, 0.17), 0.012, 'frame')                       # front hanger on the rail
        m.rbox(V3((x - 0.80, s * 0.50, FZ0 - 0.04)), (0.18, 0.12, 0.17), 0.012, 'frame')                       # rear shackle bracket
        m.cyl(V3((x - 0.80, s * 0.55, FZ0 - 0.09)), V3((x - 0.67, s * 0.55, z + 0.13)), 0.0075, 'steel', seg=8)
        m.cyl(V3((x - 0.80, s * 0.67, FZ0 - 0.09)), V3((x - 0.67, s * 0.67, z + 0.13)), 0.0075, 'steel', seg=8)
        CK.damper(m, V3((x + 0.10, s * 0.55, z + 0.05)), V3((x + 0.12, s * 0.51, FZ0 - 0.02)), 0.032, 0.012, 'black')
    # steering box on the left rail, pitman arm and drag link, steering column shaft
    m.cyl(V3((x - 0.62, 0.40, FZ0 + 0.10)), V3((x - 0.62, 0.40, FZ0 - 0.12)), 0.065, 'steel_dark', seg=24)
    m.cyl(V3((x - 0.62, 0.40, FZ0 - 0.12)), V3((x - 0.62, 0.40, FZ0 - 0.19)), 0.025, 'steel', seg=12)
    m.cyl(V3((x - 0.62, 0.40, FZ0 - 0.17)), V3((x - 0.19, 0.84, z + 0.04)), 0.017, 'steel', seg=10)


def tandem(m):
    for ax_x in (D.D1_X, D.D2_X):
        z = D.ZC
        # axle housing (tapered tube) and the carrier ("pumpkin") with its cover bolted on
        m.cyl(V3((ax_x, -0.80, z)), V3((ax_x, 0.80, z)), 0.062, 'steel_dark', seg=24)
        for s in (1, -1):
            m.cyl(V3((ax_x, s * 0.13, z)), V3((ax_x, s * 0.58, z)), 0.082, 'steel_dark', seg=24, r1=0.064)
        P.capsule(m, V3((ax_x + 0.13, 0, z)), V3((ax_x - 0.17, 0, z)), 0.175, 'steel_dark', seg=40, dome=0.06)
        m.cyl(V3((ax_x + 0.13, 0, z)), V3((ax_x + 0.19, 0, z)), 0.135, 'steel_dark', seg=32, r1=0.10)
        m.cyl(V3((ax_x - 0.176, 0, z)), V3((ax_x - 0.185, 0, z)), 0.14, 'steel', seg=32)
        for k in range(10):
            a = 2 * math.pi * k / 10
            P.hex_bolt(m, V3((ax_x - 0.185, 0.115 * math.cos(a), z + 0.115 * math.sin(a))), V3((-1, 0, 0)), 0.0085, 0.006, 'steel')
        m.cyl(V3((ax_x - 0.18, 0.0, z + 0.145)), V3((ax_x - 0.20, 0.0, z + 0.145)), 0.011, 'steel', seg=8)       # breather
        # brake chambers (spring brakes) on the rear of the axle, slack adjusters
        for s in (1, -1):
            m.cyl(V3((ax_x - 0.19, s * 0.66, z + 0.05)), V3((ax_x - 0.34, s * 0.66, z + 0.05)), 0.080, 'steel_dark', seg=24)
            m.cyl(V3((ax_x - 0.34, s * 0.66, z + 0.05)), V3((ax_x - 0.52, s * 0.66, z + 0.05)), 0.062, 'steel', seg=24)
            m.cyl(V3((ax_x - 0.12, s * 0.66, z + 0.05)), V3((ax_x - 0.19, s * 0.66, z + 0.05)), 0.012, 'steel', seg=8)
            m.cyl(V3((ax_x - 0.12, s * 0.70, z + 0.05)), V3((ax_x - 0.10, s * 0.60, z - 0.03)), 0.012, 'steel', seg=8)
            m.box(V3((ax_x - 0.11, s * 0.66, z - 0.01)), (0.05, 0.11, 0.05), 'steel_dark')
    # walking-beam suspension: a saddle on each rail, the beam under it joining both axles
    for s in (1, -1):
        sy = s * 0.545
        m.rbox(V3((-2.2, s * 0.50, FZ0 - 0.07)), (0.34, 0.14, 0.20), 0.012, 'frame')
        for dx in (-0.1, 0.1):
            P.hex_bolt(m, V3((-2.2 + dx, s * 0.575, FZ0 - 0.05)), V3((0, s, 0)), 0.011, 0.008, 'steel')
        z = D.ZC + 0.13
        P.ibeam(m, V3((D.D1_X, sy, z)), V3((-2.2, sy, z + 0.07)), 0.15, 0.09, 0.022, 0.020, 'steel_dark', up=V3((0, 1, 0)))
        P.ibeam(m, V3((-2.2, sy, z + 0.07)), V3((D.D2_X, sy, z)), 0.15, 0.09, 0.022, 0.020, 'steel_dark', up=V3((0, 1, 0)))
        m.cyl(V3((-2.2, sy - 0.06, z + 0.07)), V3((-2.2, sy + 0.06, z + 0.07)), 0.085, 'steel', seg=24)
        for ax_x in (D.D1_X, D.D2_X):
            m.cyl(V3((ax_x, sy - 0.08, D.ZC + 0.0)), V3((ax_x, sy + 0.08, D.ZC)), 0.11, 'steel_dark', seg=24)         # beam end on the axle seat
            for yy in (-0.05, 0.05):
                m.cyl(V3((ax_x + 0.12, sy + yy, D.ZC - 0.10)), V3((ax_x + 0.12, sy + yy, D.ZC + 0.17)), 0.010, 'steel', seg=8)       # U-bolts
        # torque rods: upper and lower to each axle from the frame
        for ax_x, fx in ((D.D1_X, -0.95), (D.D2_X, -3.35)):
            m.cyl(V3((ax_x, s * 0.40, D.ZC + 0.14)), V3((fx, s * 0.40, FZ0 + 0.08)), 0.020, 'steel_dark', seg=10)
            m.cyl(V3((ax_x, s * 0.50, D.ZC - 0.02)), V3((fx, s * 0.50, FZ0 - 0.02)), 0.020, 'steel_dark', seg=10)
            m.rbox(V3((fx, s * 0.46, FZ0 + 0.02)), (0.10, 0.06, 0.20), 0.008, 'frame')
    # inter-axle and main driveshafts with universal joints
    m.cyl(V3((D.D1_X - 0.18, 0, D.ZC)), V3((D.D2_X + 0.19, 0, D.ZC)), 0.045, 'steel', seg=16)
    m.cyl(V3((-0.15, 0, 0.92)), V3((D.D1_X + 0.19, 0, D.ZC + 0.04)), 0.052, 'steel', seg=18)
    for p, a in ((V3((-0.15, 0, 0.92)), V3((D.D1_X + 0.19, 0, D.ZC + 0.04))), (V3((D.D1_X - 0.18, 0, D.ZC)), V3((D.D2_X + 0.19, 0, D.ZC)))):
        for q in (p, a):
            m.rbox(q, (0.09, 0.09, 0.09), 0.015, 'steel_dark')
            m.cyl(q - V3((0, 0.06, 0)), q + V3((0, 0.06, 0)), 0.012, 'steel', seg=8)
    m.cyl(V3((-0.15, 0, 0.92)), V3((-0.45, 0, 0.935)), 0.07, 'steel_dark', seg=18)
    # the rear frame end: a pintle-free crossmember cap and the tail bracket for the flaps
    m.rbox(V3((FX0 + 0.01, 0, 0.97)), (0.04, 0.9, 0.2), 0.01, 'frame')


def engine_trans(m):
    x0 = 1.90
    # block, oil pan, head with valve cover, turbo, manifolds, fan, shroud, radiator, hoses, air intake
    m.rbox(V3((x0 - 0.20, 0, 1.00)), (1.10, 0.62, 0.62), 0.03, 'steel_dark')
    m.rbox(V3((x0 - 0.20, 0, 0.72)), (0.9, 0.52, 0.16), 0.03, 'steel')
    m.rbox(V3((x0 - 0.20, 0, 1.40)), (1.0, 0.46, 0.14), 0.02, 'steel_dark')
    for k in range(6):
        P.hex_bolt(m, V3((x0 - 0.62 + k * 0.17, 0.0, 1.475)), V3((0, 0, 1)), 0.012, 0.008, 'steel')
    for s in (1, -1):
        m.cyl(V3((x0 - 0.65, s * 0.33, 1.12)), V3((x0 + 0.20, s * 0.33, 1.12)), 0.045, 'rust', seg=12)             # exhaust manifold
        m.rbox(V3((x0 + 0.30, s * 0.30, 1.14)), (0.18, 0.12, 0.14), 0.02, 'steel')                                  # turbo / injector pump
    m.rbox(V3((x0 + 0.5, 0, 1.00)), (0.30, 0.55, 0.50), 0.03, 'steel_dark')
    # fan and shroud, radiator core and tanks
    fx = 2.66
    for k in range(7):
        a = 2 * math.pi * k / 7
        c = V3((fx, 0.19 * math.cos(a), 1.03 + 0.19 * math.sin(a)))
        m.rbox(c, (0.015, 0.20, 0.07), 0.004, 'black', (V3((1, 0, 0)), V3((0, math.cos(a), math.sin(a))), V3((0, -math.sin(a), math.cos(a)))))
    m.cyl(V3((fx - 0.01, 0, 1.03)), V3((fx + 0.03, 0, 1.03)), 0.05, 'steel', seg=18)
    P.ring_torus(m, V3((fx - 0.05, 0, 1.03)), V3((1, 0, 0)), 0.41, 0.025, 'black', seg=56)
    m.rbox(V3((2.91, 0, 1.05)), (0.12, 1.00, 1.04), 0.012, 'alu')
    for k in range(34):
        m.rbox(V3((2.975, -0.47 + 0.0285 * k, 1.05)), (0.02, 0.012, 1.0), 0.002, 'steel')
    m.rbox(V3((2.91, 0, 1.60)), (0.14, 1.06, 0.07), 0.01, 'black')
    m.rbox(V3((2.91, 0, 0.51 + 0.04)), (0.14, 1.06, 0.07), 0.01, 'black')
    m.cyl(V3((2.84, 0.15, 1.58)), V3((2.2, 0.20, 1.28)), 0.035, 'hose', seg=12)
    m.cyl(V3((2.84, -0.15, 0.58)), V3((2.2, -0.22, 0.86)), 0.035, 'hose', seg=12)
    # alternator, belt drive pulleys
    m.cyl(V3((2.35, 0.34, 1.30)), V3((2.35, 0.50, 1.30)), 0.065, 'steel_dark', seg=20)
    m.cyl(V3((2.72, 0.0, 1.03)), V3((2.75, 0.0, 1.03)), 0.12, 'black', seg=24)
    # transmission and clutch bell
    P.capsule(m, V3((0.30, 0, 0.98)), V3((-0.15, 0, 0.92)), 0.20, 'steel_dark', seg=32, dome=0.08)
    m.rbox(V3((0.55, 0, 0.98)), (0.42, 0.44, 0.44), 0.03, 'steel_dark')
    m.rbox(V3((0.78, 0, 0.99)), (0.14, 0.58, 0.58), 0.04, 'steel_dark')
    m.rbox(V3((0.1, 0.0, 1.18)), (0.28, 0.25, 0.08), 0.015, 'steel')


def steps_misc(m):
    for s in (1, -1):
        # tank straps' mounting and the cab step brackets: a lower step and the plate over the tank
        for xx, zz, w in ((0.76, 0.50, 0.40),):
            m.rbox(V3((xx, s * 1.00, zz)), (0.42, 0.28, 0.018), 0.004, 'steel')
            for k in range(8):                                                                       # tread bars of the diamond plate
                m.rbox(V3((xx - 0.17 + k * 0.048, s * 1.00, zz + 0.011)), (0.016, 0.24, 0.006), 0.002, 'steel')
            m.rbox(V3((xx + 0.13, s * 0.90, zz + 0.12)), (0.03, 0.06, 0.24), 0.006, 'frame')
            m.rbox(V3((xx - 0.13, s * 0.90, zz + 0.12)), (0.03, 0.06, 0.24), 0.006, 'frame')
            m.rbox(V3((xx, s * 1.12, zz + 0.12)), (0.03, 0.03, 0.22), 0.006, 'frame')
        # upper step over the tank
        m.rbox(V3((0.12, s * 0.98, 0.985)), (0.56, 0.34, 0.016), 0.004, 'steel')
        for k in range(11):
            m.rbox(V3((0.12 - 0.25 + k * 0.05, s * 0.98, 0.9955)), (0.016, 0.30, 0.006), 0.002, 'steel')
    # battery box on the left, ahead of the cab, a drop-down cover and strap, cables to the frame
    m.rbox(V3((1.38, 0.60, 0.95)), (0.55, 0.34, 0.36), 0.015, 'steel_dark')
    m.rbox(V3((1.38, 0.60, 1.14)), (0.57, 0.36, 0.035), 0.012, 'steel')
    for dx in (-0.2, 0.2):
        P.hex_bolt(m, V3((1.38 + dx, 0.775, 0.95)), V3((0, 1, 0)), 0.011, 0.007, 'steel')
    m.cyl(V3((1.60, 0.52, 1.14)), V3((1.9, 0.30, 1.22)), 0.012, 'black', seg=8)
    # air tanks across the rear of the frame and the air dryer
    for x in (-3.68, -4.02):
        P.capsule(m, V3((x, -0.43, 0.63)), V3((x, 0.43, 0.63)), 0.15, 'steel_dark', seg=32, dome=0.05)
        P.band(m, V3((x, -0.30, 0.63)), V3((0, 1, 0)), 0.15, 0.04, 0.004, 'steel', seg=32)
        P.band(m, V3((x, 0.30, 0.63)), V3((0, 1, 0)), 0.15, 0.04, 0.004, 'steel', seg=32)
        m.rbox(V3((x, 0, 0.77)), (0.07, 0.8, 0.02), 0.005, 'steel')
        m.cyl(V3((x, 0.0, 0.48)), V3((x, 0.0, 0.50)), 0.02, 'brass', seg=10)                # drain cock
    m.cyl(V3((-0.82, 0.62, 0.92)), V3((-0.82, 0.62, 1.20)), 0.075, 'steel', seg=20)
    m.cyl(V3((-0.82, 0.62, 1.20)), V3((-0.82, 0.62, 1.23)), 0.04, 'black', seg=14)
    # frame-mounted cable and air lines running along the left rail (a bundle of tubes with clips)
    for k, (c, r) in enumerate((('hose', 0.010), ('black', 0.008), ('valve_red', 0.008))):
        m.tube([V3((1.2, 0.395, 0.86 + 0.02 * k)), V3((-3.6, 0.395, 0.86 + 0.02 * k))], r, c, seg=8)
    for x in (1.0, 0.0, -1.0, -2.0, -3.0):
        m.rbox(V3((x, 0.40, 0.90)), (0.025, 0.02, 0.10), 0.004, 'steel')


def build_chassis():
    m = Mesh()
    frame_rails(m)
    front_axle(m)
    tandem(m)
    engine_trans(m)
    steps_misc(m)
    return m


def fuel_tank(s):
    m = Mesh()
    xc, yc, zc = 0.0, s * 0.95, 0.66
    P.capsule(m, V3((xc - 0.50, yc, zc)), V3((xc + 0.50, yc, zc)), 0.31, 'alu', seg=48, dome=0.07, rings=5)
    for dx in (-0.30, 0.30):                                                  # stainless straps, each with a buckle and bolts
        P.band(m, V3((xc + dx, yc, zc)), V3((1, 0, 0)), 0.31, 0.06, 0.005, 'steel', seg=48)
        m.rbox(V3((xc + dx, yc, zc - 0.318)), (0.07, 0.04, 0.03), 0.006, 'steel')
        P.hex_bolt(m, V3((xc + dx, yc + s * 0.0, zc - 0.34)), V3((0, 0, -1)), 0.009, 0.006, 'steel')
    for k in range(2):                                                         # weld seam circles at the head joints
        P.weld_bead(m, [V3((xc + (-0.43 + 0.86 * k), yc + 0.30 * math.cos(2 * math.pi * i / 36), zc + 0.30 * math.sin(2 * math.pi * i / 36))) for i in range(37)], 0.0035, 'steel')
    # filler neck with a vented chrome cap, fuel gauge sender plate
    m.cyl(V3((xc - 0.22, yc + s * 0.10, zc + 0.30)), V3((xc - 0.22, yc + s * 0.10, zc + 0.36)), 0.045, 'steel', seg=20)
    m.cyl(V3((xc - 0.22, yc + s * 0.10, zc + 0.36)), V3((xc - 0.22, yc + s * 0.10, zc + 0.385)), 0.058, 'chrome', seg=24)
    m.cyl(V3((xc - 0.22, yc + s * 0.10, zc + 0.385)), V3((xc - 0.22, yc + s * 0.10, zc + 0.40)), 0.032, 'chrome', seg=18)
    for k in range(6):
        a = 2 * math.pi * k / 6
        m.cyl(V3((xc - 0.22 + 0.048 * math.cos(a), yc + s * 0.10 + 0.048 * math.sin(a), zc + 0.365)), V3((xc - 0.22 + 0.048 * math.cos(a), yc + s * 0.10 + 0.048 * math.sin(a), zc + 0.386)), 0.004, 'steel', seg=6)
    m.cyl(V3((xc + 0.25, yc, zc - 0.30)), V3((xc + 0.25, yc, zc - 0.34)), 0.025, 'brass', seg=12)           # drain plug
    return m


def exhaust(s):
    m = Mesh()
    x, y = -0.80, s * 0.98
    # bracket from the rail, muffler (rust heat shield), polished stack with clamps and a bevelled top
    m.rbox(V3((x, s * 0.70, 1.16)), (0.20, 0.60, 0.03), 0.006, 'frame')
    m.rbox(V3((x, s * 0.60, 1.05)), (0.05, 0.03, 0.16), 0.004, 'frame')
    P.capsule(m, V3((x, y, 1.20)), V3((x, y, 1.80)), 0.135, 'steel', seg=36, dome=0.07)
    m.cyl(V3((x, y, 1.26)), V3((x, y, 1.74)), 0.145, 'stain', seg=36)
    for z in (1.30, 1.70):
        P.band(m, V3((x, y, z)), V3((0, 0, 1)), 0.145, 0.04, 0.005, 'steel', seg=36)
    m.cyl(V3((x, y, 1.78)), V3((x, y, 1.90)), 0.075, 'chrome', seg=24)
    m.cyl(V3((x, y, 1.90)), V3((x, y, 3.60)), 0.0635, 'chrome', seg=32)
    m.cyl(V3((x, y, 3.60)), V3((x, y, 3.64)), 0.0695, 'chrome', seg=32)
    for z in (2.15, 2.85):                                                     # stack brackets to the cab corner
        P.band(m, V3((x, y, z)), V3((0, 0, 1)), 0.0635, 0.05, 0.006, 'steel', seg=24)
        m.rbox(V3((x + 0.09, y - s * 0.02, z)), (0.14, 0.03, 0.05), 0.005, 'steel')
        P.hex_bolt(m, V3((x + 0.04, y + s * 0.0, z + 0.03)), V3((1, 0, 0)), 0.008, 0.005, 'steel')
    # the down-pipe elbow into the muffler's foot
    m.cyl(V3((x, y, 1.14)), V3((x, y, 1.22)), 0.058, 'steel', seg=20)
    return m


def fifth_wheel():
    m = Mesh()
    x0, z0 = D.KINGPIN_X, 1.10
    # mounting plates across the rails, two pedestals, the top plate ("horseshoe"), jaws, handle
    m.rbox(V3((x0, 0, z0 + 0.015)), (0.80, 1.00, 0.03), 0.006, 'frame')
    for s in (1, -1):
        for dx in (-0.30, 0.30):
            for dy in (0.42, 0.50):
                P.hex_bolt(m, V3((x0 + dx, s * dy, z0 + 0.03)), V3((0, 0, 1)), 0.012, 0.008, 'steel')
        m.rbox(V3((x0, s * 0.37, z0 + 0.085)), (0.34, 0.16, 0.12), 0.014, 'steel_dark')
        m.cyl(V3((x0, s * 0.37 - 0.09, z0 + 0.12)), V3((x0, s * 0.37 + 0.09, z0 + 0.12)), 0.04, 'steel', seg=16)
    # plate outline: an ellipse (a = 0.52 long, b = 0.46 wide) with a throat notch opening rearward (funnel mouth, 0.13 m throat)
    n = 64
    poly = []
    for i in range(n + 1):
        a = -math.pi + 0.34 + (2 * math.pi - 0.68) * i / n                # from the rear-left round the front to the rear-right
        poly.append((0.52 * math.cos(a), 0.46 * math.sin(a)))
    poly += [(-0.50, 0.12), (-0.26, 0.075), (-0.02, 0.065), (-0.02, -0.065), (-0.26, -0.075), (-0.50, -0.12)]
    zt0, zt1 = z0 + 0.15, z0 + 0.19
    cx = x0
    top = [V3((cx + x * 0.965, y * 0.965, zt1 + 0.004)) for x, y in poly]
    mid = [V3((cx + x, y, zt1 - 0.004)) for x, y in poly]
    bot = [V3((cx + x, y, zt0)) for x, y in poly]
    m.loft([bot, mid, top], 'steel', closed=True, caps=True)
    # grease-worn bright wear ring on the plate and the lock jaws
    ring2 = [V3((cx + 0.36 * math.cos(a), 0.34 * math.sin(a), zt1 + 0.0055)) for a in [-math.pi + 0.45 + (2 * math.pi - 0.9) * i / 60 for i in range(61)]]
    m.tube(ring2, 0.0035, 'chrome', seg=6)
    for s in (1, -1):
        m.rbox(V3((cx - 0.06, s * 0.10, zt1 + 0.03)), (0.12, 0.06, 0.07), 0.012, 'steel_dark')
        m.rbox(V3((cx - 0.20, s * 0.18, zt0 - 0.03)), (0.10, 0.05, 0.05), 0.008, 'steel')
    m.cyl(V3((cx - 0.30, 0.33, zt0 - 0.05)), V3((cx + 0.02, 0.50, zt0 - 0.05)), 0.011, 'steel', seg=8)           # release handle
    m.cyl(V3((cx + 0.02, 0.50, zt0 - 0.05)), V3((cx + 0.02, 0.52, zt0 + 0.02)), 0.011, 'steel', seg=8)
    m.cyl(V3((cx + 0.02, 0.52, zt0 + 0.02)), V3((cx + 0.02, 0.52, zt0 + 0.08)), 0.017, 'black', seg=12)
    # grease nipples
    for s in (1, -1):
        m.cyl(V3((cx + 0.2, s * 0.37, zt0 - 0.0)), V3((cx + 0.2, s * 0.37, zt0 - 0.03)), 0.006, 'brass', seg=6)
    return m


def fenders_and_flaps():
    f = Mesh()
    fl = Mesh()
    for s in (1, -1):
        for ax_x in (D.D1_X, D.D2_X):
            R, w, t = 0.64, 0.80, 0.014
            yc = s * D.DRIVE_Y
            a0, a1 = math.radians(16), math.radians(164)
            seg = 32
            for rr, flip in ((R, False), (R + t, True)):                      # a stamped sheet with thickness: two skins, arched across (a shallow crown)
                rows = []
                for j in range(5):
                    u = -1 + 2 * j / 4
                    y = yc + u * w / 2
                    row = []
                    for k in range(seg + 1):
                        a = a0 + (a1 - a0) * k / seg
                        crown = 0.045 * (1 - u * u)
                        row.append(V3((ax_x + (rr + crown) * math.cos(a), y, D.ZC + (rr + crown) * math.sin(a))))
                    rows.append(row)
                f.grid(list(reversed(rows)) if flip else rows, 'paint')
            for j in (0, 4):                                                   # rolled edges
                u = -1 + 2 * j / 4
                path = [V3((ax_x + (R + 0.007) * math.cos(a0 + (a1 - a0) * k / seg), yc + u * w / 2, D.ZC + (R + 0.007) * math.sin(a0 + (a1 - a0) * k / seg))) for k in range(seg + 1)]
                f.tube(path, 0.010, 'steel', seg=8)
            for k in range(3, seg - 2, 5):                                     # stamped ribs: raised bead rivets along the crown
                a = a0 + (a1 - a0) * k / seg
                P.rivet(f, V3((ax_x + (R + 0.059) * math.cos(a), yc + 0.30, D.ZC + (R + 0.059) * math.sin(a))), V3((math.cos(a), 0, math.sin(a))), 0.0055, 'steel')
                P.rivet(f, V3((ax_x + (R + 0.059) * math.cos(a), yc - 0.30, D.ZC + (R + 0.059) * math.sin(a))), V3((math.cos(a), 0, math.sin(a))), 0.0055, 'steel')
    # mud flaps behind the rear drive wheels: hanger bar and posts, the rubber flap, a bright bottom weight strip, bolts
    for s in (1, -1):
        x = D.D2_X - 0.62
        y = s * D.DRIVE_Y
        fl.cyl(V3((x + 0.02, y - 0.40, 0.80)), V3((x + 0.02, y + 0.40, 0.80)), 0.012, 'steel', seg=10)
        for yy in (-0.38, 0.38):
            fl.cyl(V3((x + 0.02, y + yy, 0.80)), V3((x + 0.02, y + yy, 1.05)), 0.011, 'steel', seg=8)
        fl.rbox(V3((x, y, 0.50)), (0.012, 0.66, 0.62), 0.004, 'blackmat')
        fl.rbox(V3((x - 0.0075, y, 0.78)), (0.003, 0.60, 0.03), 0.001, 'steel')
        for dy in (-0.26, 0.26):
            for dz in (0.30, 0.70):
                P.hex_bolt(fl, V3((x - 0.006, y + dy, dz)), V3((-1, 0, 0)), 0.009, 0.005, 'steel')
    return f, fl


def air_lines():
    m = Mesh()
    x0, x1 = -0.70, -1.52
    for yy, c in ((0.20, 'lens_red'), (-0.20, 'paint_navy'), (0.0, 'black')):
        P.coil_hose(m, V3((x0, yy, 1.55)), V3((x1, yy * 1.0, 1.60)), 0.022, 0.0065, 12, c if c != 'lens_red' else 'valve_red', sag=0.08)
        m.cyl(V3((x0 + 0.02, yy, 1.55)), V3((x0, yy, 1.55)), 0.016, 'steel', seg=10)
    return m


def run(root):
    tr = T.find('Tractor')
    ch = build_chassis().finish('Chassis', tr, sharp=45)
    T.log('chassis', len(ch.data.polygons))
    for s, n in ((1, 'L'), (-1, 'R')):
        fuel_tank(s).finish(f'FuelTank_{n}', tr, sharp=45)
        exhaust(s).finish(f'Exhaust_{n}', tr, sharp=45)
    fifth_wheel().finish('FifthWheel', tr, sharp=45)
    f, fl = fenders_and_flaps()
    f.finish('Fenders_Rear', tr, sharp=50)
    fl.finish('MudFlaps_Tractor', tr, sharp=50)
    air_lines().finish('AirLines', tr, sharp=60)
