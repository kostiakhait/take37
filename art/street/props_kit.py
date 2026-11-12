# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Street furniture kit for TAKE 37: every prop is built twice (LOD0 for close first-person view, LOD1 reduced for repetition at distance).

Local frame of a prop: origin on the ground at its foot, +X = front (towards the roadway when placed at the kerb), +Z up. Dimensions follow US 1980s practice
(hydrant 0.75 m, parking meter 1.2 m, cobra-head pole 9 m, wood utility pole 11 m, MUTCD sign blades 0.76 m, 75 mm bollard cones 0.7 m).
Each builder returns a dict {lod: Blender object}; DEST lists the props the game may blow up / knock over (placed under Destructible nodes by the layout).
"""
import math
import random

import bpy
from mathutils import Vector as V

import kitlib as K
from kitlib import MB

DEST = {'LampCobra': 900, 'LampAcorn': 350, 'TrafficLight': 700, 'Hydrant': 250, 'Mailbox': 180, 'Bench': 60, 'Bin': 25, 'Meter': 40, 'UtilityPole': 1800, 'RoadSign': 20,
        'NewsBox': 40, 'PhoneBooth': 220, 'CrowdBarrier': 30, 'Sawhorse': 25, 'Cone': 2, 'Planter': 180, 'TrashBags': 15, 'StreetTree': 0}     # mass in kg


def dirt(h=0.35, amt=0.45, seed=0, hue=(1.0, 0.97, 0.92)):
    """Vertex tone: grime at the foot (road splash), blotches by noise, slightly lighter top."""
    def f(p):
        g = 1.0 - amt * max(0.0, 1.0 - p.z / h) ** 1.5
        n = 0.82 + 0.3 * K.fbm(p, seed, 2.2)
        return (g * n * hue[0], g * n * hue[1], g * n * hue[2])
    return f


def pair(fn, *a, **k):
    return {0: fn(0, *a, **k), 1: fn(1, *a, **k)}


def _name(base, lod):
    return f'{base}_LOD{lod}'


# ---- poles and lamps --------------------------------------------------------------------------------------------------------------------------------------------------
def lamp_cobra(lod):
    m = MB(_name('LampCobra', lod), 1)
    m.tone = dirt(1.2, 0.4, 1)
    hi = lod == 0
    seg = 16 if hi else 8
    m.cyl(0, 0, 0, 0.35, 0.22, 'concrete', seg=seg, caps=(False, True))                   # concrete foot
    m.box(-0.2, -0.2, 0.33, 0.2, 0.2, 0.37, 'steel', bv=0.008 if hi else 0)                # base plate
    m.lathe([(0.17, 0.37), (0.16, 0.6), (0.075, 0.9), (0.065, 8.6), (0.055, 8.7)], 'paint_grey', seg=seg)   # tapered pole
    if hi:
        m.box(0.06, -0.07, 0.8, 0.17, 0.07, 1.25, 'steel', bv=0.008)                       # hand-hole door
        for z in (1.6, 4.0, 6.5):
            m.cyl(0, 0, z, z + 0.04, 0.085 - z * 0.0012, 'steel', seg=16)                  # weld bands
    m.tube([(0, 0, 8.55), (0.05, 0, 8.95), (0.5, 0, 9.2), (1.3, 0, 9.3), (2.1, 0, 9.18)], 0.04, 'paint_grey', seg=8 if hi else 4)
    m.box(1.7, -0.2, 8.95, 2.75, 0.2, 9.18, 'paint_grey', bv=0.03 if hi else 0)           # luminaire housing
    m.box(1.8, -0.17, 8.93, 2.65, 0.17, 8.95, 'lamp_glass')                                # lens
    if hi:
        m.box(2.0, -0.12, 9.18, 2.5, 0.12, 9.24, 'steel', bv=0.01)
        m.cyl(2.75, 0, 8.95, 9.18, 0.02, 'steel', seg=6)
    o = m.build(props={'front': '+X'})
    return o


def lamp_acorn(lod):
    m = MB(_name('LampAcorn', lod), 2)
    m.tone = dirt(1.0, 0.4, 2)
    seg = 16 if lod == 0 else 8
    base = [(0.0, 0.0), (0.26, 0.0), (0.26, 0.08), (0.22, 0.12), (0.2, 0.3), (0.14, 0.6), (0.1, 0.9), (0.085, 1.0)]
    m.lathe(base, 'paint_green', seg=seg)
    m.lathe([(0.085, 1.0), (0.07, 1.1), (0.06, 3.5), (0.09, 3.58), (0.09, 3.66)], 'paint_green', seg=seg)
    m.lathe([(0.0, 3.66), (0.13, 3.66), (0.2, 3.72), (0.22, 3.78)], 'paint_green', seg=seg)
    m.lathe([(0.22, 3.78), (0.25, 3.95), (0.26, 4.15), (0.22, 4.35), (0.14, 4.5), (0.12, 4.52)], 'lamp_glass', seg=seg)   # acorn globe
    m.lathe([(0.12, 4.52), (0.14, 4.54), (0.1, 4.62), (0.0, 4.66)], 'paint_green', seg=seg)
    if lod == 0:
        for k in range(8):                                                   # fluting on the base
            a = k * math.pi / 4
            m.cyl(0.19 * math.cos(a), 0.19 * math.sin(a), 0.14, 0.7, 0.014, 'paint_green', seg=6, r1=0.01, caps=(False, False))
        m.tube([(0, 0.07, 3.0), (0, 0.55, 3.0), (0, 0.55, 3.35)], 0.025, 'paint_green', seg=6)   # a banner arm
    return m.build(props={'front': '+X'})


def traffic_light(lod):
    m = MB(_name('TrafficLight', lod), 3)
    m.tone = dirt(1.3, 0.4, 3)
    hi = lod == 0
    seg = 16 if hi else 8
    m.cyl(0, 0, 0, 0.3, 0.2, 'concrete', seg=seg, caps=(False, True))
    m.lathe([(0.14, 0.3), (0.12, 0.8), (0.09, 6.2), (0.075, 6.4)], 'paint_dark', seg=seg)
    m.tube([(0, 0, 6.0), (0.3, 0, 6.35), (2.0, 0, 6.5), (4.8, 0, 6.4), (6.2, 0, 6.3)], 0.055, 'paint_dark', seg=8 if hi else 4)

    def head(x, y, z, lamp_on='red'):
        # 12 inch three-section vertical signal head, visors, backplate
        m.box(x - 0.17, y - 0.17, z - 0.52, x + 0.17, y + 0.17, z + 0.52, 'paint_dark', bv=0.03 if hi else 0)
        m.box(x - 0.2, y - 0.3, z - 0.62, x - 0.17, y + 0.3, z + 0.62, 'paint_dark')       # backplate
        for i, (lens, zz) in enumerate((('red_lens', 0.34), ('amber_lens', 0.0), ('green_lens', -0.34))):
            m.cyl(x + 0.17, y, z + zz - 0.1, z + zz + 0.1, 0.1, lens, seg=14 if hi else 8, caps=(False, False)) if False else None
            m.lathe([(0.0, 0.0), (0.1, 0.0), (0.1, 0.02)], lens, x=x + 0.17, y=y, seg=14 if hi else 8) if False else None
            m.at(x + 0.17, y, z + zz, ry=math.pi / 2)
            m.lathe([(0.0, 0.0), (0.1, 0.0), (0.105, 0.03), (0.0, 0.05)], lens, seg=14 if hi else 8)
            m.pop()
            if hi:
                m.box(x + 0.17, y - 0.12, z + zz + 0.09, x + 0.45, y + 0.12, z + zz + 0.115, 'paint_dark')     # visor roof
                m.box(x + 0.17, y - 0.12, z + zz + 0.09, x + 0.45, y - 0.115, z + zz + 0.0, 'paint_dark')
                m.box(x + 0.17, y + 0.115, z + zz + 0.09, x + 0.45, y + 0.12, z + zz + 0.0, 'paint_dark')
    head(0.4, 0.0, 5.7)
    head(3.4, 0.0, 5.65)
    if hi:
        m.cyl(0.4, 0, 5.99, 6.35, 0.03, 'paint_dark', seg=6)
        m.cyl(3.4, 0, 6.17, 6.4, 0.03, 'paint_dark', seg=6)
    # pedestrian head on the pole (hand / walker), box with two lenses
    m.box(0.09, -0.2, 2.5, 0.35, 0.2, 3.0, 'paint_dark', bv=0.02 if hi else 0)
    m.box(0.35, -0.16, 2.78, 0.37, 0.16, 2.96, 'red_lens')
    m.box(0.35, -0.16, 2.54, 0.37, 0.16, 2.72, 'steel')
    if hi:
        m.box(0.09, 0.09, 1.1, 0.2, 0.2, 1.4, 'paint_yellow', bv=0.01)       # push-button box
    return m.build(props={'front': '+X'})


def utility_pole(lod):
    m = MB(_name('UtilityPole', lod), 4)
    m.tone = dirt(2.0, 0.35, 4, (0.9, 0.85, 0.8))
    hi = lod == 0
    seg = 14 if hi else 7
    m.lathe([(0.0, -0.1), (0.19, -0.1), (0.19, 0.0), (0.16, 1.0), (0.14, 6.0), (0.115, 10.5), (0.0, 10.6)], 'wood_dark', seg=seg)
    m.box(-0.06, -1.3, 9.55, 0.06, 1.3, 9.72, 'wood_dark', bv=0.012 if hi else 0)       # cross-arm
    m.box(-0.06, -0.5, 9.0, 0.06, 0.5, 9.1, 'wood_dark')
    for s in (-1, 1):
        m.tube([(0.07, 0.15 * s, 9.55), (0.07, 0.8 * s, 9.1)], 0.02, 'steel', seg=4, caps=False)
    for y in (-1.15, -0.55, 0.0, 0.55, 1.15):                                           # pin insulators
        m.lathe([(0.0, 9.72), (0.045, 9.72), (0.05, 9.8), (0.035, 9.9), (0.04, 9.98), (0.02, 10.05), (0.0, 10.05)], 'paint_sage', x=0, y=y, seg=8 if hi else 5)
    m.cyl(0.32, 0.0, 8.0, 8.75, 0.22, 'paint_grey', seg=seg, caps=(True, True))        # transformer can
    if hi:
        m.cyl(0.32, 0.0, 8.75, 8.82, 0.1, 'paint_grey', seg=seg)
        for dy in (-0.07, 0.07):
            m.lathe([(0.0, 8.82), (0.03, 8.82), (0.03, 8.9), (0.0, 8.95)], 'paint_sage', x=0.32, y=dy, seg=6)
        for z in range(2, 9):                                                            # step bolts and the pole tag
            m.cyl(-0.12, 0.05 * (z % 2), z * 1.0, z * 1.0 + 0.012, 0.012, 'steel', seg=5, caps=(False, True))
        m.box(0.14, -0.04, 2.8, 0.15, 0.04, 2.95, 'paint_yellow')
        m.tube([(0.16, 0.0, 9.1), (0.17, 0.0, 6.0), (0.16, 0.0, 2.5), (0.15, 0.0, 0.3)], 0.014, 'cable', seg=4, caps=False)   # ground wire
    return m.build(props={'front': '+X'})


# ---- hydrant, meter, mailbox, boxes ------------------------------------------------------------------------------------------------------------------------------------
def hydrant(lod):
    m = MB(_name('Hydrant', lod), 5)
    m.tone = dirt(0.45, 0.5, 5)
    hi = lod == 0
    seg = 16 if hi else 8
    m.lathe([(0.0, -0.02), (0.14, -0.02), (0.14, 0.03), (0.11, 0.06), (0.1, 0.1), (0.088, 0.14), (0.088, 0.52), (0.1, 0.54), (0.1, 0.58)], 'paint_red', seg=seg)
    m.lathe([(0.1, 0.58), (0.108, 0.6), (0.1, 0.63), (0.085, 0.66), (0.06, 0.71), (0.0, 0.73)], 'paint_red', seg=seg)       # bonnet dome
    m.cyl(0, 0, 0.7, 0.755, 0.03, 'steel', seg=6, r1=0.025)                                                                 # operating nut
    for s in (-1, 1):                                                                                                       # hose nozzles, side
        m.at(0, 0.0, 0.4, rx=-s * math.pi / 2)
        m.lathe([(0.0, 0.05), (0.052, 0.05), (0.052, 0.13), (0.06, 0.14), (0.06, 0.18), (0.052, 0.19), (0.0, 0.19)], 'paint_red', seg=seg if hi else 6)
        m.pop()
    m.at(0.0, 0.0, 0.34, ry=math.pi / 2)                                                                                    # pumper nozzle, front
    m.lathe([(0.0, 0.07), (0.07, 0.07), (0.07, 0.15), (0.08, 0.16), (0.08, 0.22), (0.07, 0.23), (0.0, 0.23)], 'paint_red', seg=seg)
    m.pop()
    if hi:
        for k in range(6):                                                                                                  # bonnet and flange bolts
            a = k * math.pi / 3
            m.cyl(0.115 * math.cos(a), 0.115 * math.sin(a), 0.0, 0.03, 0.012, 'steel', seg=6)
        for s in (-1, 1):
            m.tube([(0.0, s * 0.12, 0.5), (0.04, s * 0.14, 0.45), (0.0, s * 0.19, 0.34), (0.0, s * 0.23, 0.4)], 0.004, 'chrome', seg=3, caps=False)   # cap chains
    return m.build(props={'front': '+X'})


def meter(lod):
    m = MB(_name('Meter', lod), 6)
    m.tone = dirt(0.5, 0.4, 6)
    hi = lod == 0
    m.cyl(0, 0, 0, 1.0, 0.032, 'paint_grey', seg=12 if hi else 6)
    m.cyl(0, 0, 0, 0.02, 0.055, 'steel', seg=12 if hi else 6, caps=(False, True))
    m.lathe([(0.0, 1.0), (0.085, 1.0), (0.095, 1.06), (0.085, 1.2), (0.06, 1.26), (0.0, 1.27)], 'paint_dark', seg=14 if hi else 8)   # dome head
    m.at(0.0, 0.0, 1.12, ry=-math.pi / 2)
    if hi:
        m.lathe([(0.0, 0.07), (0.07, 0.07), (0.07, 0.1), (0.0, 0.1)], 'glass', seg=14)
        m.lathe([(0.0, 0.065), (0.07, 0.065), (0.0, 0.065)], 'sun_paper', seg=14)
    m.pop()
    if hi:
        m.box(0.08, -0.012, 1.02, 0.115, 0.012, 1.075, 'chrome')                  # coin slot cap
    return m.build(props={'front': '+X'})


def mailbox(lod):
    m = MB(_name('Mailbox', lod), 7)
    m.tone = dirt(0.7, 0.35, 7)
    hi = lod == 0
    bv = 0.012 if hi else 0
    m.box(-0.3, -0.25, 0.0, 0.3, 0.25, 0.1, 'paint_dark', bv=bv)
    m.box(-0.28, -0.23, 0.1, 0.28, 0.23, 1.0, 'paint_blue', bv=bv)
    # arched top: half cylinder along X
    seg = 12 if hi else 6
    for k in range(seg):
        a0, a1 = math.pi * k / seg, math.pi * (k + 1) / seg
        pts = [(-0.28, 0.23 * math.cos(a0), 1.0 + 0.23 * math.sin(a0)), (0.28, 0.23 * math.cos(a0), 1.0 + 0.23 * math.sin(a0)), (0.28, 0.23 * math.cos(a1), 1.0 + 0.23 * math.sin(a1)), (-0.28, 0.23 * math.cos(a1), 1.0 + 0.23 * math.sin(a1))]
        m.face(pts, 'paint_blue', out=(0, math.cos((a0 + a1) / 2), math.sin((a0 + a1) / 2)), smooth=True)
    m.face([(-0.28, 0.23, 1.0), (-0.28, 0.0, 1.23), (-0.28, -0.23, 1.0)], 'paint_blue', out=(-1, 0, 0))
    m.face([(0.28, 0.23, 1.0), (0.28, -0.23, 1.0), (0.28, 0.0, 1.23)], 'paint_blue', out=(1, 0, 0))
    m.box(0.28, -0.2, 0.62, 0.31, 0.2, 0.9, 'paint_blue', bv=0.006 if hi else 0)      # the drop-down pull door
    m.box(0.31, -0.17, 0.78, 0.33, 0.17, 0.82, 'black_metal')                            # mail slot
    if hi:
        m.box(0.31, -0.06, 0.66, 0.34, 0.06, 0.7, 'steel', bv=0.004)                   # pull handle
        m.box(0.28, -0.1, 0.35, 0.285, 0.1, 0.55, 'paint_white')                         # pick-up times plate
    return m.build(props={'front': '+X'})


def newsbox(lod):
    m = MB(_name('NewsBox', lod), 8)
    m.tone = dirt(0.5, 0.45, 8)
    hi = lod == 0
    m.box(-0.2, -0.22, 0.0, 0.2, 0.22, 0.12, 'paint_dark', bv=0.01 if hi else 0)
    m.box(-0.18, -0.2, 0.12, 0.18, 0.2, 1.0, 'paint_red', bv=0.015 if hi else 0)
    m.box(0.18, -0.15, 0.55, 0.2, 0.15, 0.9, 'glass_dirty')
    m.box(0.18, -0.12, 0.2, 0.21, 0.12, 0.4, 'steel')
    if hi:
        m.box(0.2, -0.04, 0.3, 0.23, 0.04, 0.34, 'chrome')
        m.box(-0.2, -0.22, 0.98, 0.2, 0.22, 1.02, 'paint_red', bv=0.006)
    return m.build(props={'front': '+X'})


def bin_(lod):
    m = MB(_name('Bin', lod), 9)
    m.tone = dirt(0.6, 0.45, 9)
    hi = lod == 0
    seg = 18 if hi else 8
    m.lathe([(0.0, 0.0), (0.27, 0.02), (0.3, 0.05), (0.31, 0.9), (0.0, 0.9)], 'paint_green', seg=seg)                  # drum
    m.lathe([(0.31, 0.9), (0.32, 0.92), (0.32, 0.96), (0.28, 0.98), (0.0, 0.98)], 'paint_dark', seg=seg)                 # lid
    m.lathe([(0.2, 0.98), (0.2, 1.0), (0.0, 1.0)], 'paint_dark', seg=seg) if False else None
    if hi:
        for z in (0.25, 0.5, 0.75):
            m.cyl(0, 0, z, z + 0.02, 0.315, 'paint_dark', seg=seg, caps=(False, False))
        m.at(0.28, 0, 0.82, ry=0)
        m.box(0.0, -0.12, 0.0, 0.05, 0.12, 0.1, 'black_metal')                                                          # flap opening
        m.pop()
    return m.build(props={'front': '+X'})


def bench(lod):
    m = MB(_name('Bench', lod), 10)
    m.tone = dirt(0.5, 0.35, 10)
    hi = lod == 0
    for y in (-0.8, 0.8):                                                                                               # cast iron ends
        m.extrude([(-0.28, 0.0), (-0.22, 0.0), (-0.2, 0.43), (-0.3, 0.46), (-0.36, 0.86), (-0.3, 0.86), (-0.24, 0.5), (0.24, 0.5), (0.26, 0.0), (0.33, 0.0), (0.3, 0.45), (0.3, 0.52), (-0.16, 0.52)][:0] or
                  [(-0.26, 0.0), (-0.18, 0.0), (-0.17, 0.4), (0.25, 0.43), (0.29, 0.0), (0.37, 0.0), (0.33, 0.47), (-0.17, 0.47), (-0.3, 0.88), (-0.37, 0.88)], 'y', y - 0.03, y + 0.03, 'paint_dark')
    for i in range(3):                                                                                                  # seat slats
        m.box(-0.12 + i * 0.13, -0.9, 0.45, -0.02 + i * 0.13, 0.9, 0.48, 'wood_pine' if hi else 'wood_brown', bv=0.006 if hi else 0)
    for i in range(3):                                                                                                  # back slats
        zz = 0.58 + i * 0.1
        a = -0.22 - (zz - 0.5) * 0.3
        m.box(a - 0.025, -0.9, zz, a + 0.005, 0.9, zz + 0.075, 'wood_pine' if hi else 'wood_brown', bv=0.006 if hi else 0)
    return m.build(props={'front': '+X'})


def planter(lod):
    m = MB(_name('Planter', lod), 11)
    m.tone = dirt(0.5, 0.4, 11)
    hi = lod == 0
    m.box(-0.5, -0.5, 0.0, 0.5, 0.5, 0.7, 'concrete', bv=0.025 if hi else 0)
    m.box(-0.42, -0.42, 0.62, 0.42, 0.42, 0.7, 'soil')
    if hi:
        rnd = random.Random(3)
        for _ in range(14):                                       # shrubs: small leaf cards
            x, y = rnd.uniform(-0.35, 0.35), rnd.uniform(-0.35, 0.35)
            s = rnd.uniform(0.25, 0.4)
            m.face([(x - s, y, 0.65), (x + s, y, 0.65), (x + s, y, 0.65 + s * 1.5), (x - s, y, 0.65 + s * 1.5)], 'leaves', out=(0, 1, 0), uv=[(0, 0), (1, 0), (1, 1), (0, 1)])
            m.face([(x, y - s, 0.65), (x, y + s, 0.65), (x, y + s, 0.65 + s * 1.5), (x, y - s, 0.65 + s * 1.5)], 'leaves', out=(1, 0, 0), uv=[(0, 0), (1, 0), (1, 1), (0, 1)])
    else:
        m.box(-0.35, -0.35, 0.7, 0.35, 0.35, 1.0, 'grass')
    return m.build(props={'front': '+X'})


def phone_booth(lod):
    m = MB(_name('PhoneBooth', lod), 12)
    m.tone = dirt(0.8, 0.35, 12)
    hi = lod == 0
    w = 0.45
    m.box(-w, -w, 0.0, w, w, 0.1, 'concrete', bv=0.01 if hi else 0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.box(sx * w - 0.03, sy * w - 0.03, 0.1, sx * w + 0.03, sy * w + 0.03, 2.2, 'paint_grey', bv=0.005 if hi else 0)
    m.box(-w - 0.03, -w - 0.03, 2.2, w + 0.03, w + 0.03, 2.32, 'paint_grey', bv=0.012 if hi else 0)
    m.box(-w - 0.01, -w - 0.01, 2.32, w + 0.01, w + 0.01, 2.4, 'paint_grey')
    m.box(-0.28, -0.04, 2.16, 0.28, 0.04, 2.3, 'lamp_glass') if False else None
    m.box(0.46, -0.3, 2.0, 0.47, 0.3, 2.14, 'white_plastic')                       # sign panel
    for (a, b, c, d) in ((-w, -w, w, -w), (-w, w, w, w), (-w, -w, -w, w)):
        m.box(min(a, c) - 0.004, min(b, d) - 0.004, 0.2, max(a, c) + 0.004, max(b, d) + 0.004, 2.15, 'glass')
    if hi:
        for zz in (0.65, 1.15, 1.65):
            for (a, b, c, d) in ((-w, -w, w, -w), (-w, w, w, w), (-w, -w, -w, w)):
                m.box(min(a, c) - 0.01, min(b, d) - 0.01, zz, max(a, c) + 0.01, max(b, d) + 0.01, zz + 0.025, 'paint_grey')
    m.box(-0.38, -0.2, 1.0, -0.2, 0.2, 1.4, 'paint_dark', bv=0.012 if hi else 0)       # the telephone
    m.box(-0.2, -0.12, 1.2, -0.17, 0.12, 1.35, 'chrome')
    if hi:
        m.tube([(-0.2, 0.14, 1.28), (-0.12, 0.14, 1.36), (-0.12, 0.14, 1.3), (-0.2, 0.14, 1.22)], 0.012, 'paint_dark', seg=5)
    return m.build(props={'front': '+X'})


# ---- signs ---------------------------------------------------------------------------------------------------------------------------------------------------------------
def road_sign(lod, kind='stop'):
    """Galvanised post with a sign face from the atlas (textures_prep.py)."""
    import json
    atlas = json.load(open(K.TEX / 'signs_atlas.json'))
    m = MB(_name('RoadSign_' + kind, lod), 13)
    m.tone = dirt(1.0, 0.25, 13)
    hi = lod == 0
    H = 3.2 if kind.startswith('blade') else 2.3
    m.cyl(0, 0, 0, H, 0.025, 'steel', seg=8 if hi else 4)
    key, w, h, zc = {'stop': ('stop', 0.76, 0.76, 2.15), 'speed25': ('speed25', 0.6, 0.76, 2.2), 'nopark': ('nopark', 0.46, 0.6, 1.9), 'oneway': ('oneway', 0.76, 0.5, 2.2),
                     'xwalk': ('xwalk', 0.76, 0.76, 2.15), 'dne': ('dne', 0.76, 0.76, 2.15)}.get(kind, (None,) * 4)
    if kind == 'blade_main' or kind.startswith('blade'):
        names = [kind[6:] or 'main_st']
        zs = [3.05]
        for nm, zc2 in zip(names, zs):
            r = atlas['blade_' + nm]
            m.box(0.04, -0.46, zc2 - 0.1, 0.055, 0.46, zc2 + 0.1, 'steel', bv=0.004 if hi else 0)
            m.uvrect([(0.06, -0.46, zc2 - 0.1), (0.06, 0.46, zc2 - 0.1), (0.06, 0.46, zc2 + 0.1), (0.06, -0.46, zc2 + 0.1)], 'signs', (r[0], r[1] + 0.0 + (r[3] - r[1]) * 0.25, r[2], r[3] - (r[3] - r[1]) * 0.25), out=(1, 0, 0))
            m.uvrect([(0.04, 0.46, zc2 - 0.1), (0.04, -0.46, zc2 - 0.1), (0.04, -0.46, zc2 + 0.1), (0.04, 0.46, zc2 + 0.1)], 'signs', (r[0], r[1] + (r[3] - r[1]) * 0.25, r[2], r[3] - (r[3] - r[1]) * 0.25), out=(-1, 0, 0))
    else:
        r = atlas[key]
        if kind == 'stop':
            # octagonal face: the plate is an octagon with the atlas mapped over its bounding square
            c = (0.052, 0.0, zc)
            R = 0.38 / math.cos(math.pi / 8)
            pts, uvs = [], []
            for k in range(8):
                a = math.pi / 8 + k * math.pi / 4
                pts.append((0.052, -R * math.cos(a), zc + R * math.sin(a)))
                uvs.append((r[0] + (r[2] - r[0]) * (0.5 - 0.484 * math.cos(a)), r[1] + (r[3] - r[1]) * (0.5 + 0.484 * math.sin(a))))
            m.face(pts, 'signs', out=(1, 0, 0), uv=uvs)
            m.face([(0.04, y, z) for (_, y, z) in pts], 'steel', out=(-1, 0, 0))
            for k in range(8):
                a, b = pts[k], pts[(k + 1) % 8]
                m.face([(0.04, a[1], a[2]), (0.04, b[1], b[2]), (0.052, b[1], b[2]), (0.052, a[1], a[2])], 'steel', inside=(0.046, 0, zc))
        else:
            m.box(0.04, -w / 2, zc - h / 2, 0.052, w / 2, zc + h / 2, 'steel', bv=0.004 if hi else 0, skip=('+x',))
            m.uvrect([(0.0521, -w / 2, zc - h / 2), (0.0521, w / 2, zc - h / 2), (0.0521, w / 2, zc + h / 2), (0.0521, -w / 2, zc + h / 2)], 'signs', r, out=(1, 0, 0))
    if hi:
        m.cyl(0, 0, H, H + 0.03, 0.03, 'steel', seg=8, caps=(False, True))
    return m.build(props={'front': '+X'})


def cone(lod):
    m = MB(_name('Cone', lod), 14)
    m.tone = dirt(0.3, 0.3, 14)
    seg = 14 if lod == 0 else 8
    m.box(-0.2, -0.2, 0.0, 0.2, 0.2, 0.025, 'rubber', bv=0.008 if lod == 0 else 0)
    m.lathe([(0.1, 0.025), (0.1, 0.03), (0.075, 0.4), (0.05, 0.7), (0.032, 0.7)], 'paint_orange', seg=seg)
    m.lathe([(0.075, 0.4), (0.0791, 0.45), (0.0764, 0.5), (0.07, 0.5)], 'paint_white', seg=seg) if False else None
    m.cyl(0, 0, 0.3, 0.46, 0.0905, 'paint_white', seg=seg, r1=0.0735, caps=(False, False))
    return m.build(props={'front': '+X'})


def crowd_barrier(lod):
    """Steel crowd-control barrier, 2.3 m long, 1.1 m high, feet; the film-crew street closure."""
    m = MB(_name('CrowdBarrier', lod), 15)
    m.tone = dirt(0.6, 0.35, 15)
    hi = lod == 0
    sg = 8 if hi else 4
    for y in (-1.05, 1.05):
        m.tube([(0, y, 0.02), (0, y, 1.1)], 0.02, 'steel', seg=sg)
        m.box(-0.35, y - 0.03, 0.0, 0.35, y + 0.03, 0.04, 'steel', bv=0.008 if hi else 0)       # feet
    for z in (0.2, 1.1):
        m.tube([(0, -1.05, z), (0, 1.05, z)], 0.02, 'steel', seg=sg)
    n = 9 if hi else 5
    for i in range(n):
        y = -0.92 + i * 1.84 / (n - 1)
        m.tube([(0, y, 0.2), (0, y, 1.1)], 0.01, 'steel', seg=4 if hi else 3, caps=False)
    m.box(0.0, -1.0, 0.45, 0.012, 1.0, 0.95, 'white_plastic') if False else None
    return m.build(props={'front': '+X'})


def sawhorse(lod):
    """Type III barricade: two striped rails on A-frame legs, with a ROAD CLOSED panel."""
    import json
    atlas = json.load(open(K.TEX / 'signs_atlas.json'))
    m = MB(_name('Sawhorse', lod), 16)
    m.tone = dirt(0.5, 0.3, 16)
    hi = lod == 0
    for y in (-0.9, 0.9):
        for s in (-1, 1):
            m.tube([(0.0, y, 1.05), (s * 0.4, y, 0.0)], 0.03, 'wood_pine' if hi else 'wood_brown', seg=4, caps=False)
    for z in (0.95, 0.65):
        m.box(-0.02, -1.15, z, 0.02, 1.15, z + 0.2, 'paint_white', bv=0.004 if hi else 0)
        for i in range(8):                                                                    # orange diagonal stripes
            y0 = -1.15 + i * 0.3
            m.face([(0.021, y0, z), (0.021, y0 + 0.15, z), (0.021, y0 + 0.3, z + 0.2), (0.021, y0 + 0.15, z + 0.2)], 'paint_orange', out=(1, 0, 0)) if y0 + 0.3 <= 1.15 else None
            m.face([(-0.021, y0 + 0.15, z), (-0.021, y0, z), (-0.021, y0 + 0.15, z + 0.2), (-0.021, y0 + 0.3, z + 0.2)], 'paint_orange', out=(-1, 0, 0)) if y0 + 0.3 <= 1.15 else None
    r = atlas['closed']
    m.uvrect([(0.04, 0.4, 0.28), (0.04, -0.4, 0.28), (0.04, -0.4, 0.58), (0.04, 0.4, 0.58)], 'signs', (r[0], r[1] + (r[3] - r[1]) * 0.15, r[2], r[3] - (r[3] - r[1]) * 0.15), out=(1, 0, 0))
    m.box(0.02, -0.4, 0.28, 0.04, 0.4, 0.58, 'steel', skip=('+x',))
    return m.build(props={'front': '+X'})


def trash_bags(lod):
    m = MB(_name('TrashBags', lod), 17)
    m.tone = dirt(0.6, 0.2, 17)
    rnd = random.Random(8)
    seg = 10 if lod == 0 else 6
    for i in range(4 if lod == 0 else 3):
        x, y, s = rnd.uniform(-0.3, 0.3), rnd.uniform(-0.4, 0.4), rnd.uniform(0.9, 1.2)
        m.lathe([(0.0, 0.0), (0.22 * s, 0.02), (0.3 * s, 0.2), (0.27 * s, 0.4), (0.12 * s, 0.52), (0.04 * s, 0.56), (0.0, 0.5)], 'rubber', x=x, y=y, seg=seg)
    return m.build(props={'front': '+X'})


# ---- trees -------------------------------------------------------------------------------------------------------------------------------------------------------------
def street_tree(lod, seed=1):
    rnd = random.Random(seed)
    m = MB(_name('StreetTree', lod), 20 + seed)
    m.tone = dirt(0.8, 0.3, 20)
    hi = lod == 0
    seg = 12 if hi else 6
    # tree pit: cast iron grate frame in the pavement
    m.box(-0.6, -0.6, 0.0, 0.6, 0.6, 0.02, 'soil')
    m.box(-0.62, -0.62, 0.0, 0.62, -0.56, 0.04, 'paint_dark')
    m.box(-0.62, 0.56, 0.0, 0.62, 0.62, 0.04, 'paint_dark')
    m.box(-0.62, -0.56, 0.0, -0.56, 0.56, 0.04, 'paint_dark')
    m.box(0.56, -0.56, 0.0, 0.62, 0.56, 0.04, 'paint_dark')
    # trunk and branches
    trunk = [(0.26, 0.0), (0.2, 0.3), (0.16, 1.6), (0.13, 3.0), (0.1, 3.6)]
    m.lathe([(0.0, 0.0)] + trunk, 'bark', seg=seg)
    cards = []
    leaf = (0.0, 0.0, 1.0, 1.0)

    def branch(p0, d, length, r, depth):
        p1 = p0 + d * length
        mid = (p0 + p1) / 2 + V((0, 0, 0.1 * length))
        m.tube([p0, mid, p1], r, 'bark', seg=6 if hi else 4, caps=False)
        if depth > 0:
            n = 3 if hi else 2
            for _ in range(n):
                a = rnd.uniform(0, 2 * math.pi)
                nd = (d * 0.6 + V((math.cos(a), math.sin(a), 0.55)) * 0.8).normalized()
                branch(p1, nd, length * rnd.uniform(0.6, 0.8), r * 0.62, depth - 1)
        else:
            cards.append(p1)
    for i in range(5 if hi else 3):
        a = i * 2 * math.pi / (5 if hi else 3) + rnd.uniform(-0.4, 0.4)
        d = (V((math.cos(a), math.sin(a), 0.0)) * 0.7 + V((0, 0, 0.8))).normalized()
        branch(V((0, 0, 3.3 + rnd.uniform(-0.2, 0.3))), d, rnd.uniform(1.6, 2.2), 0.08, 1 if hi else 0)
    cards.append(V((0, 0, 4.6)))
    n_cards = 7 if hi else 3
    for c in cards:
        for _ in range(n_cards):
            sz = rnd.uniform(1.5, 2.1)
            yaw, tilt = rnd.uniform(0, math.pi), rnd.uniform(-0.5, 0.5)
            ex = V((math.cos(yaw), math.sin(yaw), 0)) * sz / 2
            ey = V((-math.sin(yaw) * math.sin(tilt), math.cos(yaw) * math.sin(tilt), math.cos(tilt))) * sz / 2
            ctr = c + V((rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.5), rnd.uniform(0.0, 0.6)))
            hue = rnd.uniform(0.75, 1.15)
            n = ex.cross(ey)
            m.face([ctr - ex - ey, ctr + ex - ey, ctr + ex + ey, ctr - ex + ey], 'leaves', out=n, uv=[(0, 0), (1, 0), (1, 1), (0, 1)], color=lambda p, h=hue: (h, h * 1.02, h * 0.9))
    return m.build(props={'front': '+X', 'seed': seed})


# ---- registry -------------------------------------------------------------------------------------------------------------------------------------------------------------
def all_props():
    """{kit name: {0: obj, 1: obj}}; the road-sign variants are separate kit items."""
    P = {}
    for nm, fn in (('LampCobra', lamp_cobra), ('LampAcorn', lamp_acorn), ('TrafficLight', traffic_light), ('UtilityPole', utility_pole), ('Hydrant', hydrant), ('Meter', meter), ('Mailbox', mailbox),
                   ('NewsBox', newsbox), ('Bin', bin_), ('Bench', bench), ('Planter', planter), ('PhoneBooth', phone_booth), ('Cone', cone), ('CrowdBarrier', crowd_barrier),
                   ('Sawhorse', sawhorse), ('TrashBags', trash_bags)):
        P[nm] = pair(fn)
    for kind in ('stop', 'speed25', 'nopark', 'oneway', 'xwalk', 'dne', 'blade_main_st', 'blade_elm_st', 'blade_oak_st', 'blade_mill_st', 'blade_church_st', 'blade_walnut_st'):
        P['RoadSign_' + kind] = pair(road_sign, kind)
    for s in (1, 2, 3):
        P[f'StreetTree{s}'] = pair(street_tree, s)
        for lod in (0, 1):
            P[f'StreetTree{s}'][lod].name = f'StreetTree{s}_LOD{lod}'
            P[f'StreetTree{s}'][lod].data.name = f'StreetTree{s}_LOD{lod}'
    return P
