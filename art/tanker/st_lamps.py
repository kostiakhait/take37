# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Stage lamps: every lamp and reflector, as separate nodes the game can light or smash.

Under Tractor: Lamps_Head (4 round sealed beams in chrome buckets), Lamps_Turn (amber front turn/parking lamps in the bumper ends), Lamps_MarkerT (fender and cab markers).
Under Trailer: Lamps_Tail (stop/tail/turn, 3 round red per side, white reversing lamps), Lamps_Marker (side markers, ID and clearance clusters), Reflectors, Tape (conspicuity tape DOT-C2).
"""
import math

import bpy

import carkit as CK
import dims as D
import parts as P
import st_tank as K
import tkit as T
from tkit import V3, Mesh


def head_lamps():
    m = Mesh()
    gx = 3.00
    for s in (1, -1):
        y = s * 0.80
        m.rbox(V3((gx + 0.02, y, 1.20)), (0.14, 0.30, 0.42), 0.03, 'chrome')                       # the bucket
        for z in (1.31, 1.09):
            CK.round_lamp(m, V3((gx + 0.092, y, z)), V3((1, 0, 0)), 0.078, 0.07, 'lens_clear', 'chrome')
        m.rbox(V3((gx - 0.05, y, 1.41)), (0.26, 0.20, 0.02), 0.004, 'steel_dark')
        for dy in (-0.10, 0.10):
            P.hex_bolt(m, V3((gx + 0.092, y + dy, 1.20)), V3((1, 0, 0)), 0.008, 0.005, 'steel')
    return m


def turn_lamps():
    m = Mesh()
    for s in (1, -1):
        CK.fluted_lens(m, V3((3.215, s * 0.99, 0.745)), V3((1, 0, 0)), V3((0, 0, 1)), 0.17, 0.085, 0.03, 5, 1, 'lens_amber', pattern='flutes', bulge=0.005)
        m.rbox(V3((3.20, s * 0.99, 0.745)), (0.04, 0.20, 0.115), 0.012, 'chrome')
        CK.fluted_lens(m, V3((3.222, s * 0.99, 0.745)), V3((1, 0, 0)), V3((0, 0, 1)), 0.15, 0.065, 0.025, 5, 1, 'lens_amber', pattern='flutes', bulge=0.004)
    return m


def marker_t():
    m = Mesh()
    for s in (1, -1):
        # fender top marker (amber, front) and cab side marker (amber) with tiny chrome guards
        for c, ax in ((V3((2.95, s * 0.98, 1.34)), V3((1, 0, 0))), (V3((0.30, s * 1.13, 2.97)), V3((0, s, 0))), (V3((D.D2_X - 0.78, s * 1.13, 1.22)), V3((0, s, 0)))):
            CK.fluted_lens(m, c, ax, V3((0, 0, 1)), 0.075, 0.04, 0.018, 2, 1, 'lens_amber' if c.x > -2 else 'lens_red', pattern='flutes', bulge=0.003)
    return m


def tail_lamps():
    m = Mesh()
    xb = K.X_REAR - 0.045
    # the lamp board: a plate across the rear at z 1.0..1.36 with the lamp pods
    m.rbox(V3((xb + 0.02, 0, 1.18)), (0.04, 2.20, 0.34), 0.008, 'steel_dark')
    for s in (1, -1):
        for k, y in enumerate((0.55, 0.73, 0.91)):
            CK.round_lamp(m, V3((xb - 0.0, s * y, 1.18)), V3((-1, 0, 0)), 0.0535, 0.05, 'lens_red', 'chrome', rings=6, n=32)
        # reversing lamp (white) and a license-plate lamp
        CK.round_lamp(m, V3((xb - 0.0, s * 0.30, 1.18)), V3((-1, 0, 0)), 0.045, 0.045, 'lens_clear', 'chrome', rings=5, n=28)
        # corner reflectors
        m.rbox(V3((xb - 0.006, s * 1.045, 1.11)), (0.012, 0.075, 0.075), 0.006, 'reflector_red')
        m.rbox(V3((xb - 0.006, s * 1.045, 1.25)), (0.012, 0.075, 0.075), 0.006, 'reflector_red')
    m.rbox(V3((xb - 0.012, 0, 1.30)), (0.02, 0.07, 0.04), 0.006, 'steel')                        # plate lamp
    return m


def marker_trailer():
    m = Mesh()
    # amber front / red rear side markers, two per side; clearance-lamp clusters (3 amber at the front top, 3 red at the rear top)
    zc = 1.62
    r = abs((zc - K.ZC_TANK) / K.B_HALF)
    y = K.A_HALF * (1 - r ** K.PWR) ** (1 / K.PWR)
    for s in (1, -1):
        for x, kind in ((K.X_BARREL0 - 0.55, 'lens_amber'), (K.X_BARREL0 - 4.1, 'lens_amber'), (K.X_BARREL1 + 0.55, 'lens_red'), (K.X_BARREL1 + 4.1, 'lens_red')):
            nrm = V3((0, s, 0.08)).normalized()
            m.rbox(V3((x, s * (y + 0.004), zc)), (0.13, 0.014, 0.075), 0.01, 'steel')
            CK.fluted_lens(m, V3((x, s * (y + 0.012), zc)), V3((0, s, 0)), V3((0, 0, 1)), 0.11, 0.055, 0.02, 3, 1, kind, pattern='flutes', bulge=0.004)
    zt = K.ZC_TANK + K.B_HALF
    for (x0, kind, sgn) in ((K.X_BARREL0 - 0.10, 'lens_amber', 1), (K.X_BARREL1 + 0.12, 'lens_red', -1)):
        m.rbox(V3((x0, 0, zt + 0.045)), (0.07, 0.80, 0.03), 0.008, 'steel_dark')
        for yy in (-0.30, 0.0, 0.30):
            CK.fluted_lens(m, V3((x0 - sgn * 0.0 + (0.045 if sgn > 0 else -0.045), yy, zt + 0.075)), V3((sgn, 0, 0)), V3((0, 0, 1)), 0.075, 0.04, 0.02, 2, 1, kind, pattern='flutes', bulge=0.003)
    return m


def reflectors():
    m = Mesh()
    zc = 1.40
    r = abs((zc - K.ZC_TANK) / K.B_HALF)
    y = K.A_HALF * (1 - r ** K.PWR) ** (1 / K.PWR)
    for s in (1, -1):
        for x, kind in ((K.X_BARREL0 - 0.55, 'reflector_red'), (K.X_BARREL1 + 0.55, 'reflector_red'), (K.X_BARREL0 - 4.1, 'reflector_red')):
            m.rbox(V3((x, s * (y + 0.004), zc)), (0.09, 0.012, 0.09), 0.008, 'reflector_red')
            P.rivet(m, V3((x - 0.035, s * (y + 0.011), zc + 0.035)), V3((0, s, 0)), 0.003, 'steel', seg=6)
            P.rivet(m, V3((x + 0.035, s * (y + 0.011), zc - 0.035)), V3((0, s, 0)), 0.003, 'steel', seg=6)
    return m


def tape_mesh():
    """DOT-C2 conspicuity tape: red/white, 50 mm, in a line along each side low on the tank, a line along the lower rear, a strip on the upper rear corners."""
    m = Mesh()
    for s in (1, -1):
        for zc in (1.56,):
            r = abs((zc - K.ZC_TANK) / K.B_HALF)
            y = K.A_HALF * (1 - r ** K.PWR) ** (1 / K.PWR)
            # follow the shell with short straight pieces (the surface is nearly flat along x at fixed z)
            nrm = V3((0, s, 0.0))
            p0 = V3((K.X_BARREL0 - 0.18, s * (y + 0.0), zc))
            p1 = V3((K.X_BARREL1 + 0.18, s * (y + 0.0), zc))
            m.tape(p0, p1, 0.050, V3((0, s, 0.05)))
    xb = K.X_REAR - 0.052
    m.tape(V3((xb, 1.12, 1.045)), V3((xb, -1.12, 1.045)), 0.05, V3((-1, 0, 0)))
    return m


def run(root):
    tr, tl = T.find('Tractor'), T.find('Trailer')
    head_lamps().finish('Lamps_Head', tr, sharp=60)
    turn_lamps().finish('Lamps_Turn', tr, sharp=60)
    marker_t().finish('Lamps_MarkerT', tr, sharp=60)
    tail_lamps().finish('Lamps_Tail', tl, sharp=60)
    marker_trailer().finish('Lamps_Marker', tl, sharp=60)
    reflectors().finish('Reflectors', tl, sharp=60)
    tape_mesh().finish('Tape', tl, sharp=60, box_uv=False)
