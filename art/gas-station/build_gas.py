# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""1987 roadside gas station for TAKE 37 (generic, no brands): canopy on columns, six pumps in three islands, a shop with a glass front and a car-wash bay, price pole,
tank fill hatches, air and water stand, bins, forecourt slab with oil stains and drains, apron to the street.

  blender -b -P art/gas-station/build_gas.py -- [--out art/gas-station/gas_station.glb] [--blend D:/temp/take37/gas/gas.blend]

Frame: origin on the ground at the middle of the street frontage, +X = from the street into the lot (so the lot's front faces -X toward the street... the game rotates the
GasStation_Anchor so that +X points at the street), +Y left, +Z up. Lot 68 m wide (Y -34..34), 36 m deep (X 0..36). Nodes:
  GasStation (root)
    Static/       Forecourt, Apron, Shop, Signs backing, Hatches, AirStand, Fence, Lamp posts   (non-destructible)
    Canopy        canopy roof + fascia + lamps (own node; blow up and burn separately), CanopyColumn_* are own nodes (destructible: collapse)
    Pump_00..05   each an empty at the pump foot with LOD0/LOD1 meshes and sub-nodes Hose_*, Nozzle_* ; extras: destructible, fuel, burnable
    PriceSign     the price pole (destructible)
    Bin_*, AirStand (destructible)
    Fire_Anchor_* empties where the game starts flames: pump tops, canopy edge, hatches
"""
import json
import math
import pathlib
import random
import sys

import bpy
from mathutils import Vector as V

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / 'street'))
import kitlib as K  # noqa: E402
import props_kit as PK  # noqa: E402
from kitlib import MB  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
arg = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d  # noqa: E731
HERE = pathlib.Path(__file__).resolve().parent
OUT = arg('--out', str(HERE / 'gas_station.glb'))
BLEND = arg('--blend', 'D:/temp/take37/gas/gas.blend')
STATS = {}


def log(*a):
    print('[gas]', *a, flush=True)


def tone(seed, h=0.5, amt=0.35):
    def f(p):
        g = 1.0 - amt * max(0.0, 1.0 - p.z / h) ** 1.4
        n = 0.82 + 0.3 * K.fbm(V((p.x * 0.4, p.y * 0.4, p.z * 0.4)), seed, 1.0)
        return (g * n, g * n * 0.99, g * n * 0.97)
    return f


# ---------------------------------------------------------------- pump
def pump(lod, name='Pump', seed=1):
    """1987 electro-mechanical dispenser: 0.9 x 0.5 x 1.55 m cabinet, two faces (+X and -X sides of the island are the customer sides... here customer faces are +Y / -Y), rotating-digit display,
    hose on a hook, nozzle in the boot, pump top globe light; grade selector buttons; base plate bolted to the island."""
    m = MB(f'{name}_LOD{lod}', seed)
    m.tone = tone(seed, 0.8, 0.3)
    hi = lod == 0
    bv = 0.012 if hi else 0.0
    W, Dp = 0.48, 0.62                         # half widths: along X (island axis) and Y (customer faces)
    m.box(-W - 0.04, -Dp - 0.04, 0.0, W + 0.04, Dp + 0.04, 0.05, 'steel', bv=bv)          # base plate
    m.box(-W, -Dp, 0.05, W, Dp, 0.55, 'paint_white', bv=bv)                              # lower cabinet
    m.box(-W + 0.02, -Dp - 0.02, 0.55, W - 0.02, Dp + 0.02, 0.62, 'paint_dark', bv=bv)    # shelf / drip ledge
    m.box(-W + 0.03, -Dp + 0.03, 0.62, W - 0.03, Dp - 0.03, 1.38, 'paint_white', bv=bv)  # upper cabinet
    m.box(-W + 0.03, -Dp + 0.1, 1.38, W - 0.03, Dp - 0.1, 1.5, 'paint_red', bv=bv)        # head band in the (neutral) house colour
    m.box(-W + 0.06, -Dp + 0.13, 1.5, W - 0.06, Dp - 0.13, 1.56, 'paint_dark', bv=bv)    # cap
    # base skirt panel and louvre
    for s in (-1, 1):
        y = s * Dp
        m.box(-W + 0.08, y - (0.0 if s < 0 else -0.0), 0.12, W - 0.08, y + s * 0.012, 0.45, 'paint_dark', bv=0.004 if hi else 0)       # service door
        if hi:
            for k in range(8):
                m.box(-W + 0.14, y, 0.17 + k * 0.035, W - 0.14, y + s * 0.02, 0.185 + k * 0.035, 'steel')
        # display window with rotating digits
        m.box(-W + 0.08, y + s * 0.0, 0.98, W - 0.08, y + s * 0.015, 1.3, 'black_metal', bv=0.004 if hi else 0)
        m.box(-W + 0.1, y + s * 0.015, 1.02, W - 0.1, y + s * 0.02, 1.26, 'glass_dirty')
        if hi:
            for row, lab in enumerate((0, 1, 2)):
                for dgt in range(5 if row else 4):
                    zc = 1.2 - row * 0.075
                    xc = -0.3 + dgt * 0.11
                    m.box(xc, y + s * 0.0075, zc, xc + 0.075, y + s * 0.011, zc + 0.06, 'paint_white')
        # grade selector row
        if hi:
            for k in range(3):
                m.box(-0.15 + k * 0.15, y + s * 0.0, 0.76, -0.06 + k * 0.15, y + s * 0.03, 0.82, ['paint_blue', 'paint_green', 'paint_red'][k], bv=0.004)
            m.box(-W + 0.07, y, 0.65, W - 0.07, y + s * 0.012, 0.72, 'paint_grey')
        # hose hook, side pocket: nozzle boot
        bx = -W + 0.1 if s < 0 else W - 0.1
    # nozzle boots and hoses on both customer sides: boot at x = +-0.3 on the (+Y) side etc.
    objs = {}
    for s in (-1, 1):
        x = 0.33 * (1 if s > 0 else -1)
        y = s * Dp
        m.box(x - 0.05, y, 0.7, x + 0.05, y + s * 0.1, 0.92, 'black_metal', bv=0.01 if hi else 0)
    base = m.build(f'{name}_LOD{lod}')
    # hoses and nozzles are separate children (they swing / get pulled off)
    hn = []
    for s in (-1, 1):
        x = 0.33 * (1 if s > 0 else -1)
        y = s * Dp
        h = MB(f'Hose_{name}_{"A" if s > 0 else "B"}_LOD{lod}', seed + s)
        h.tone = lambda p: (0.8, 0.8, 0.8)
        pts = [(x, y + s * 0.04, 1.38), (x, y + s * 0.2, 1.5), (x - 0.12 * s * (1 if s > 0 else -1) * -1, y + s * 0.38, 1.1), (x, y + s * 0.34, 0.68), (x, y + s * 0.06, 0.82)]
        pts = [V(p) for p in pts]
        # catenary-ish loop through the points, sampled with a Catmull-Rom spline for a smooth hose
        smooth = []
        n = 12 if hi else 4
        for i in range(len(pts) - 1):
            p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, len(pts) - 1)]
            for k in range(n):
                t = k / n
                smooth.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
        smooth.append(pts[-1])
        h.tube(smooth, 0.022 if hi else 0.02, 'rubber', seg=8 if hi else 4)
        ho = h.build(f'Hose_{name}_{"A" if s > 0 else "B"}_LOD{lod}')
        nz = MB(f'Nozzle_{name}_{"A" if s > 0 else "B"}_LOD{lod}', seed + 3 * s)
        nz.at(x, y + s * 0.06, 0.84)
        nz.box(-0.03, -0.03, -0.1, 0.03, 0.03, 0.04, 'chrome', bv=0.006 if hi else 0)      # body in the boot
        nz.cyl(0.0, 0.0, 0.04, 0.2, 0.012, 'chrome', seg=8 if hi else 4)                       # spout pointing up in the boot
        if hi:
            nz.box(-0.02, s * -0.0, -0.02, 0.02, s * 0.06, 0.0, 'black_metal', bv=0.004)        # trigger guard
        nz.pop()
        no = nz.build(f'Nozzle_{name}_{"A" if s > 0 else "B"}_LOD{lod}')
        hn += [ho, no]
    return base, hn


def forecourt_tone(seed=3):
    def f(p):
        n = 0.78 + 0.34 * K.fbm(V((p.x * 0.3, p.y * 0.3, 0.0)), seed, 1.0)
        slab = 0.9 + 0.12 * random.Random(int(math.floor(p.x / 4.5) * 31 + math.floor(p.y / 4.5) * 17)).random()
        stain = 1.0 - 0.45 * max(0.0, K.fbm(V((p.x * 1.1, p.y * 1.1, 4.0)), seed + 4, 1.0) - 0.55) * 2.6
        return (n * slab * stain,) * 3
    return f


def build():
    K.reset()
    rnd = random.Random(37)
    root = K.empty('GasStation', size=3.0)
    cs = K.coll('Gas_Static')
    cd = K.coll('Gas_Destructible')
    cm = K.coll('Gas_Markers')
    g_static = K.empty('Static', parent=root, collection=cs)
    # ---------------------------------------------------------------- forecourt, apron, kerbs
    fm = MB('Forecourt', seed=2, uvshift=False)
    fm.tone = forecourt_tone()
    LOTY, LOTX = 34.0, 36.0
    # concrete slab 4.5 m panels with tooled joints: surface at z=0.0; the apron meets the street sidewalk level with a ramp
    nx, ny = int(LOTX / 1.5), int(LOTY * 2 / 1.5)
    fm.grid((0.0, -LOTY, 0.0), (1.5, 0, 0), (0, LOTY * 2 / ny, 0), nx, ny, 'concrete', out=(0, 0, 1))
    # joints: dark strips
    for i in range(1, int(LOTX / 4.5) + 1):
        fm.box(i * 4.5 - 0.012, -LOTY, 0.0, i * 4.5 + 0.012, LOTY, 0.004, 'tar')
    for j in range(-int(LOTY / 4.5), int(LOTY / 4.5) + 1):
        fm.box(0.0, j * 4.5 - 0.012, 0.0, LOTX, j * 4.5 + 0.012, 0.004, 'tar')
    forecourt = fm.build('Forecourt', collection=cs, parent=g_static)
    # perimeter kerb round the lot's back and sides, planting strip behind
    km = MB('Perimeter', seed=4, uvshift=False)
    km.box(LOTX, -LOTY, 0.0, LOTX + 0.25, LOTY, 0.2, 'kerb', bv=0.02)
    km.box(0.0, -LOTY - 0.25, 0.0, LOTX, -LOTY, 0.2, 'kerb', bv=0.02)
    km.box(0.0, LOTY, 0.0, LOTX, LOTY + 0.25, 0.2, 'kerb', bv=0.02)
    km.box(LOTX + 0.25, -LOTY - 0.25, -0.03, LOTX + 6, LOTY + 0.25, 0.02, 'verge')
    peri = km.build('Perimeter', collection=cs, parent=g_static)
    # island kerbs: three pump islands (each 7.5 x 1.3 m, 0.18 high) in a row along Y at x = 16
    isl = MB('Islands', seed=5, uvshift=False)
    isl.tone = tone(5, 0.2, 0.3)
    isl_y = [-14.0, 0.0, 14.0]
    for y in isl_y:
        isl.box(16 - 3.75, y - 0.65, 0.0, 16 + 3.75, y + 0.65, 0.18, 'kerb', bv=0.03)
        isl.box(16 - 3.75, y - 0.55, 0.18, 16 + 3.75, y + 0.55, 0.19, 'concrete')
        for xx in (16 - 3.55, 16 + 3.55):                                                                   # bollards at the island ends
            isl.cyl(xx, y, 0.18, 1.0, 0.09, 'paint_yellow', seg=12)
            isl.cyl(xx, y, 1.0, 1.04, 0.1, 'paint_yellow', seg=12)
    isl_o = isl.build('Islands', collection=cs, parent=g_static)
    # drains and oil stains on the forecourt (decals from the street atlas)
    dm = MB('ForecourtDecals', seed=6, uvshift=False)

    def cell(i, inset=0.003):
        c, r = i % 4, i // 4
        return (c * 0.25 + inset, 1 - (r + 1) * 0.25 + inset, c * 0.25 + 0.25 - inset, 1 - r * 0.25 - inset)

    def decal(x, y, w, h, ang, ci, z=0.005):
        r = cell(ci)
        ca, sa = math.cos(ang), math.sin(ang)
        pts = [(x + dx * ca - dy * sa, y + dx * sa + dy * ca, z) for (dx, dy) in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
        dm.face(pts, 'decals', out=(0, 0, 1), uv=[(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])])
    for y in isl_y:
        for side in (-1, 1):
            for k in range(4):                                                                              # fuel and oil drips where cars stand beside the islands
                decal(16 + rnd.uniform(-3, 3), y + side * rnd.uniform(1.8, 3.2), rnd.uniform(1.0, 2.4), rnd.uniform(1.0, 2.4), rnd.uniform(0, 6.28), rnd.choice([0, 1, 9]), 0.005 + 0.0005 * k)
            decal(16 + rnd.uniform(-2, 2), y + side * 1.0, 3.0, 1.6, 0.0, 9, 0.0068)                       # fuel spill at the pumps
    for (x, y) in ((6, -22), (28, -6), (8, 20), (30, 26), (22, 8), (12, -6)):
        decal(x, y, rnd.uniform(2.5, 4.0), rnd.uniform(2.5, 4.0), rnd.uniform(0, 6.28), rnd.choice([2, 3, 8]), 0.007)
    for (x, y) in ((24, -14), (24, 0), (24, 14), (8, -4)):
        decal(x, y, 1.0, 0.5, 0.0, 6, 0.01)
    decal(12.0, 8.0, 0.78, 0.78, 0.3, 5, 0.012)
    decal(30.0, -12.0, 0.78, 0.78, 1.1, 5, 0.012)
    for (x, y) in ((5.0, -8.0), (9.0, 20.0)):
        decal(x, y, 1.0, 5.0, math.pi / 2, 7, 0.008)
    fd = dm.build('ForecourtDecals', collection=cs, parent=g_static)
    # ---------------------------------------------------------------- shop building
    SX0, SX1, SY0, SY1 = 26.0, 33.0, -25.0, -9.0                # shop block at the back left (-Y side)
    bm = MB('Shop', seed=7)
    bm.tone = lambda p: tuple([(0.8 + 0.3 * K.fbm(V((p.x * 0.4, p.y * 0.4, p.z * 0.4)), 7, 1.0)) * (1.0 - 0.3 * max(0.0, 1.0 - p.z / 1.0) ** 1.4)] * 3)
    H = 3.6
    # shop faces the island row (-X side): glass front with a door, brick side/back walls
    bm.box(SX0, SY0, 0.0, SX1, SY1, 0.3, 'concrete', bv=0.01)                                         # plinth
    wall = 'brick_buff'
    # front wall (at x = SX0): piers + a continuous storefront glass 0.3..2.7, a door at y = -13.5
    gl0, gl1 = 0.35, 2.75
    for (a, b) in ((SY0, SY0 + 0.6), (-14.4, -12.6), (SY1 - 0.6, SY1)):
        bm.box(SX0 - 0.08, a, 0.3, SX0 + 0.3, b, H, wall, bv=0.01)
    bm.box(SX0 - 0.08, SY0, gl1, SX0 + 0.3, SY1, H, wall, bv=0.01)                                  # lintel band over the glass
    bm.box(SX0 - 0.08, SY0 + 0.6, 0.3, SX0 + 0.3, -14.4, gl0, wall, bv=0.01)                         # sill walls
    bm.box(SX0 - 0.08, -12.6, 0.3, SX0 + 0.3, SY1 - 0.6, gl0, wall, bv=0.01)
    for (a, b) in ((SY0 + 0.6, -14.4), (-12.6, SY1 - 0.6)):
        bm.quad((SX0 + 0.1, b, gl0), (SX0 + 0.1, a, gl0), (SX0 + 0.1, a, gl1), (SX0 + 0.1, b, gl1), 'glass', out=(-1, 0, 0))
        bm.box(SX0 - 0.06, a, gl1 - 0.06, SX0 + 0.16, b, gl1, 'paint_dark')
        bm.box(SX0 - 0.06, a, gl0, SX0 + 0.16, b, gl0 + 0.06, 'paint_dark')
        n = int((b - a) / 1.8)
        for k in range(n + 1):
            yy = a + (b - a) * k / n
            bm.box(SX0 - 0.06, yy - 0.04, gl0, SX0 + 0.16, yy + 0.04, gl1, 'paint_dark', bv=0.006)
    # door in the opening -14.4..-12.6
    bm.box(SX0 - 0.0, -14.35, 0.3, SX0 + 0.08, -12.65, 2.3, 'paint_dark', bv=0.01)
    bm.quad((SX0 - 0.002, -12.8, 0.45), (SX0 - 0.002, -14.2, 0.45), (SX0 - 0.002, -14.2, 2.2), (SX0 - 0.002, -12.8, 2.2), 'glass', out=(-1, 0, 0))
    bm.box(SX0 - 0.1, -13.0, 1.0, SX0 - 0.02, -12.95, 1.25, 'chrome', bv=0.003)
    # interior seen through the glass: a back wall with shelves and a counter, lit
    ix = SX0 + 2.2
    r = (0.0, 0.5, 0.5, 1.0)
    bm.uvrect([(ix, SY1 - 0.6, 0.3), (ix, SY0 + 0.6, 0.3), (ix, SY0 + 0.6, gl1), (ix, SY1 - 0.6, gl1)], 'interiors', (0.004, 0.504, 0.496, 0.996), out=(-1, 0, 0))
    bm.quad((SX0 + 0.1, SY0 + 0.6, 0.31), (ix, SY0 + 0.6, 0.31), (ix, SY1 - 0.6, 0.31), (SX0 + 0.1, SY1 - 0.6, 0.31), 'wood_oak', out=(0, 0, 1))
    bm.quad((SX0 + 0.1, SY0 + 0.6, gl1), (SX0 + 0.1, SY1 - 0.6, gl1), (ix, SY1 - 0.6, gl1), (ix, SY0 + 0.6, gl1), 'plaster_cream', out=(0, 0, -1))
    bm.box(SX0 + 0.9, -23.0, 0.31, SX0 + 1.5, -15.5, 1.05, 'wood_dark', bv=0.01)                         # counter
    # other walls and roof
    bm.box(SX0, SY0 - 0.0, 0.3, SX1, SY0 + 0.3, H, 'brick_old', bv=0.0)
    bm.box(SX0, SY1 - 0.3, 0.3, SX1, SY1, H, 'brick_old', bv=0.0)
    bm.box(SX1 - 0.3, SY0, 0.3, SX1, SY1, H, 'brick_old')
    bm.box(SX0 - 0.35, SY0 - 0.35, H, SX1 + 0.35, SY1 + 0.35, H + 0.35, 'paint_white', bv=0.015)     # roof slab with parapet edge
    bm.box(SX0 - 0.3, SY0 - 0.3, H + 0.35, SX1 + 0.3, SY1 + 0.3, H + 0.45, 'tar')
    # a canopy fascia band across the front (sign band), blank panel in the house colour
    bm.box(SX0 - 0.38, SY0 - 0.35, H - 0.1, SX0 - 0.3, SY1 + 0.35, H + 0.35, 'paint_red', bv=0.006)
    # roof units
    bm.box(29.0, -20, H + 0.45, 30.5, -18.4, H + 1.3, 'paint_grey', bv=0.02)
    bm.cyl(31.5, -12, H + 0.45, H + 1.0, 0.18, 'steel', seg=10)
    # windows on the side walls, wall plaque, a door on the back
    for yy in (-21.0, -16.5):
        bm.box(SX0 + 1.5, SY0 - 0.04, 1.2, SX0 + 3.0, SY0, 2.4, 'paint_dark')
        bm.quad((SX0 + 1.55, SY0 - 0.045, 1.25), (SX0 + 2.95, SY0 - 0.045, 1.25), (SX0 + 2.95, SY0 - 0.045, 2.35), (SX0 + 1.55, SY0 - 0.045, 2.35), 'glass_dirty', out=(0, -1, 0))
        break
    bm.box(SX1, -20.0, 0.3, SX1 + 0.05, -18.8, 2.4, 'paint_dark')          # back door
    # car-wash bay: a second block with a roller door, at the shop's far end
    bm.box(SX0, SY1 + 0.0, 0.0, SX1, SY1 + 6.0, 0.3, 'concrete')
    bm.box(SX0, SY1 + 6.0 - 0.3, 0.3, SX1, SY1 + 6.0, H, 'brick_old')
    bm.box(SX0, SY1, 0.3, SX0 + 0.3, SY1 + 1.2, H, wall)
    bm.box(SX0, SY1 + 4.8, 0.3, SX0 + 0.3, SY1 + 6.0, H, wall)
    bm.box(SX0, SY1 + 1.2, 2.8, SX0 + 0.3, SY1 + 4.8, H, wall)
    bm.box(SX1 - 0.3, SY1, 0.3, SX1, SY1 + 6.0, H, 'brick_old')
    bm.box(SX0, SY1, H, SX1, SY1 + 6.0, H + 0.1, 'tar')
    for k in range(14):                                                    # roller door slats
        bm.box(SX0 + 0.04, SY1 + 1.2, 0.3 + k * 0.18, SX0 + 0.11, SY1 + 4.8, 0.3 + k * 0.18 + 0.16, 'steel', bv=0.004)
    shop = bm.build('Shop', collection=cs, parent=g_static)
    # ---------------------------------------------------------------- canopy (own node) and its columns (own nodes)
    cx0, cx1, cy0, cy1 = 9.0, 23.0, -22.0, 22.0                      # canopy plan, over the three islands
    cz = 4.9
    cp = MB('Canopy', seed=8)
    cp.tone = tone(8, 5.0, 0.12)
    # roof: shallow steel deck, fascia 0.9 m deep with a red stripe band and white panels, soffit with recessed lamps
    cp.box(cx0, cy0, cz, cx1, cy1, cz + 0.12, 'paint_white', bv=0.01)                                   # deck
    cp.box(cx0 - 0.1, cy0 - 0.1, cz - 0.15, cx0, cy1 + 0.1, cz + 0.55, 'paint_white', bv=0.02)         # fascia (street side, -X)
    cp.box(cx1, cy0 - 0.1, cz - 0.15, cx1 + 0.1, cy1 + 0.1, cz + 0.55, 'paint_white', bv=0.02)
    cp.box(cx0 - 0.1, cy0 - 0.1, cz - 0.15, cx1 + 0.1, cy0, cz + 0.55, 'paint_white', bv=0.02)
    cp.box(cx0 - 0.1, cy1, cz - 0.15, cx1 + 0.1, cy1 + 0.1, cz + 0.55, 'paint_white', bv=0.02)
    for (x0_, x1_, y0_, y1_) in ((cx0 - 0.105, cx0 - 0.1, cy0, cy1), (cx1 + 0.1, cx1 + 0.105, cy0, cy1)):
        cp.box(x0_ - 0.005, y0_, cz + 0.15, x1_ + 0.005, y1_, cz + 0.32, 'paint_red')                         # stripes
    cp.box(cx0, cy0 - 0.105, cz + 0.15, cx1, cy0 - 0.1, cz + 0.32, 'paint_red')
    cp.box(cx0, cy1 + 0.1, cz + 0.15, cx1, cy1 + 0.105, cz + 0.32, 'paint_red')
    cp.box(cx0, cy0, cz - 0.05, cx1, cy1, cz, 'plaster_white')                                         # soffit panel
    for yy in range(-18, 19, 4):                                                                      # soffit lamps, recessed diffuser troughs
        for xx in (12.0, 16.0, 20.0):
            cp.box(xx - 0.6, yy - 0.15, cz - 0.07, xx + 0.6, yy + 0.15, cz - 0.04, 'lamp_glass')
    for yy in range(-20, 21, 4):                                                                      # soffit beams
        cp.box(cx0, yy - 0.06, cz - 0.2, cx1, yy + 0.06, cz - 0.05, 'paint_grey', bv=0.01)
    cp.box(cx0 + 2, cy0 + 1, cz + 0.12, cx0 + 3.5, cy0 + 2.4, cz + 0.6, 'paint_grey', bv=0.02)         # a roof vent
    canopy = cp.build('Canopy', collection=cd, parent=root, props={'destructible': 1, 'burnable': 1, 'mass_kg': 2600, 'role': 'canopy roof'})
    # columns: four rows... six, each its own node with a base plinth
    columns = []
    for i, (x, y) in enumerate(((12.0, -7.0), (20.0, -7.0), (12.0, 7.0), (20.0, 7.0), (12.0, -21.0), (20.0, -21.0), (12.0, 21.0), (20.0, 21.0))[:0] or ((11.0, -7.0), (21.0, -7.0), (11.0, 7.0), (21.0, 7.0))):
        cm_ = MB(f'CanopyColumn_{i}', seed=20 + i)
        cm_.tone = tone(20 + i, 1.2, 0.4)
        cm_.box(x - 0.25, y - 0.25, 0.0, x + 0.25, y + 0.25, 0.3, 'concrete', bv=0.03)
        cm_.cyl(x, y, 0.3, cz - 0.15, 0.17, 'paint_white', seg=18)
        cm_.cyl(x, y, 0.3, 0.9, 0.2, 'paint_yellow', seg=18, caps=(False, False))
        cm_.cyl(x, y, cz - 0.15, cz, 0.24, 'paint_grey', seg=18, caps=(False, True))
        columns.append(cm_.build(f'CanopyColumn_{i}', collection=cd, parent=root, props={'destructible': 1, 'mass_kg': 380, 'role': 'canopy column', 'supports': 'Canopy'}))
    # ---------------------------------------------------------------- pumps (LOD pair each), six pumps: two per island
    PL = {}
    for lod in (0, 1):
        PL[lod] = pump(lod)
    srcs = []
    pumps = []
    pidx = 0
    for ii, y in enumerate(isl_y):
        for jx in (-1.75, 1.75):
            nm = f'Pump_{pidx:02d}'
            e = K.empty(nm, loc=(16 + jx, y, 0.19), parent=root, collection=cd, size=0.4,
                        props={'destructible': 1, 'burnable': 1, 'fuel_l': 160, 'mass_kg': 420, 'role': 'fuel dispenser', 'grade': ['regular', 'unleaded', 'premium'][pidx % 3]})
            for lod in (0, 1):
                base, hn = PL[lod]
                o = K.dup(base, f'{nm}_LOD{lod}', parent=e, collection=cd)
                o['lod'] = lod
                for part in hn:
                    pn = part.name.split('_')
                    kind = pn[0]
                    side = pn[2]
                    c = K.dup(part, f'{kind}_{nm}_{side}_LOD{lod}', parent=e, collection=cd)
                    c['lod'] = lod
            fa = K.empty(f'Fire_{nm}_top', loc=(0, 0, 1.58), parent=e, collection=cm, size=0.3)
            fa2 = K.empty(f'Fire_{nm}_hose', loc=(0, 0.4, 0.7), parent=e, collection=cm, size=0.3)
            pumps.append(e)
            pidx += 1
    for lod in (0, 1):                                                       # source meshes are not exported: move them to a hidden collection
        for o in [PL[lod][0]] + PL[lod][1]:
            for c in o.users_collection:
                c.objects.unlink(o)
            K.coll('Gas_Source').objects.link(o)
    # ---------------------------------------------------------------- price pole (street side, own node)
    pp = MB('PriceSign', seed=9)
    pp.tone = tone(9, 2.0, 0.3)
    pp.box(-0.35, -0.35, 0.0, 0.35, 0.35, 0.4, 'concrete', bv=0.04)
    pp.cyl(0, 0, 0.4, 6.4, 0.14, 'paint_grey', seg=16)
    pp.box(-0.2, -1.1, 6.0, 0.2, 1.1, 8.0, 'paint_white', bv=0.03)                     # double-sided board
    pp.box(-0.22, -1.1, 7.2, 0.22, 1.1, 8.0, 'paint_red', bv=0.02)                     # house-colour head (blank: no brand)
    # price panels: three rows of rotating digits (generic) -- boxes of light grey with dark digits from DejaVu drawn into the texture atlas
    pp.box(-0.205, -0.95, 6.15, -0.2, 0.95, 7.1, 'paint_dark')
    pp.box(0.2, -0.95, 6.15, 0.205, 0.95, 7.1, 'paint_dark')
    for sgn in (-1, 1):
        x = 0.2 * sgn + 0.0015 * sgn
        for k, (lab, pr) in enumerate((('REGULAR', '0.89'), ('UNLEADED', '0.97'), ('PREMIUM', '1.09'))):
            zc = 6.97 - k * 0.3
            pp.box(x - 0.001, -0.9, zc - 0.12, x + 0.001, -0.1, zc + 0.12, 'sun_paper' if False else 'paint_white')
            pp.box(x - 0.001, 0.05, zc - 0.12, x + 0.001, 0.9, zc + 0.12, 'lamp_glass')
    pp.cyl(0, 0, 8.0, 8.04, 0.14, 'steel', seg=8)
    price = pp.build('PriceSign', collection=cd, parent=root, props={'destructible': 1, 'mass_kg': 650, 'role': 'price pole'})
    price.location = (-0.0, 30.0, 0.0)
    # ---------------------------------------------------------------- tank hatches, vent pipes, air/water stand, bins, lamp posts
    th = MB('TankHatches', seed=10, uvshift=False)
    th.tone = tone(10, 0.1, 0.4)
    for (x, y) in ((8.0, -4.0), (8.0, 0.0), (8.0, 4.0), (8.0, 8.0)):
        th.cyl(x, y, -0.003, 0.012, 0.32, 'steel', seg=20)
        th.cyl(x, y, 0.012, 0.016, 0.26, 'paint_red' if y in (-4.0, 4.0) else 'paint_blue', seg=20)            # colour-coded fill caps
        th.cyl(x, y, -0.003, 0.002, 0.36, 'black_metal', seg=20, caps=(False, False))
        th.cyl(x, y, 0.016, 0.02, 0.06, 'steel', seg=8)
    th.box(6.8, -5.5, -0.003, 9.2, 9.5, 0.002, 'tar') if False else None
    hatches = th.build('TankHatches', collection=cs, parent=g_static)
    vents = MB('VentPipes', seed=11)
    vents.tone = tone(11, 0.6, 0.3)
    for y in (-4.5, 5.0):
        vents.cyl(34.8, y, 0.0, 3.6, 0.03, 'steel', seg=8)
        vents.cyl(34.8, y, 3.6, 3.7, 0.045, 'steel', seg=8)
    vent_o = vents.build('VentPipes', collection=cd, parent=root, props={'destructible': 1, 'mass_kg': 30, 'role': 'tank vent pipe'})
    air = MB('AirStand', seed=12)
    air.tone = tone(12, 0.6, 0.35)
    air.box(-0.4, -0.2, 0.0, 0.4, 0.2, 0.08, 'concrete', bv=0.01)
    air.box(-0.28, -0.14, 0.08, 0.28, 0.14, 1.25, 'paint_blue', bv=0.015)
    air.box(-0.3, -0.16, 1.25, 0.3, 0.16, 1.32, 'paint_dark', bv=0.01)
    air.box(-0.2, -0.14 - 0.01, 0.85, 0.2, -0.14, 1.15, 'paint_white')                                 # gauge face
    air.cyl(0.0, -0.15, 0.93, 1.07, 0.09, 'chrome', seg=14)
    air.box(-0.2, 0.14, 0.4, 0.2, 0.15, 0.7, 'paint_white')
    air.tube([(0.2, 0.0, 1.1), (0.4, 0.0, 1.0), (0.5, 0.1, 0.5), (0.3, 0.2, 0.15)], 0.02, 'rubber', seg=6)
    air.cyl(0.3, 0.2, 0.0, 0.15, 0.03, 'chrome', seg=8)
    air.box(0.6, -0.12, 0.0, 0.85, 0.12, 0.75, 'paint_grey', bv=0.01)                                    # water tap box
    air.cyl(0.725, -0.12, 0.45, 0.5, 0.025, 'chrome', seg=8)
    airs = air.build('AirStand', collection=cd, parent=root, props={'destructible': 1, 'mass_kg': 90, 'role': 'air and water stand'})
    airs.location = (24.5, 24.0, 0.0)
    airs.rotation_euler = (0, 0, math.pi)
    for i, (x, y) in enumerate(((8.0, -11.0), (24.0, -11.0), (24.0, 11.0))):
        e = K.empty(f'Bin_{i}', loc=(x, y, 0.19 if False else 0.0), rot=(0, 0, math.pi), parent=root, collection=cd, props={'destructible': 1, 'mass_kg': 25, 'role': 'bin'})
        for lod in (0, 1):
            o = K.dup(PK.bin_(lod), f'Bin_{i}_LOD{lod}', parent=e, collection=cd)
    # a squeegee bucket stand and a tyre stack by the shop
    ts = MB('TyreStack', seed=13)
    for k in range(5):
        ts.lathe([(0.17, 0.0), (0.31, 0.02), (0.33, 0.07), (0.33, 0.15), (0.31, 0.19), (0.17, 0.2), (0.15, 0.1)], 'rubber', x=0, y=0, seg=18) if k == 0 else None
    tyres = MB('Tyres', seed=14)
    for k in range(4):
        tyres.at(0, 0, k * 0.2)
        tyres.lathe([(0.17, 0.0), (0.31, 0.01), (0.33, 0.06), (0.33, 0.14), (0.31, 0.19), (0.17, 0.2), (0.15, 0.1), (0.17, 0.0)], 'rubber', seg=20)
        tyres.pop()
    ty = tyres.build('TyreStack', collection=cd, parent=root, props={'destructible': 1, 'burnable': 1, 'mass_kg': 60, 'role': 'tyres'})
    ty.location = (25.0, -8.0, 0.0)
    # lamp posts at the lot corners (street furniture dup)
    for i, (x, y) in enumerate(((3.0, -30.0), (3.0, 30.0))):
        e = K.empty(f'Lamp_{i}', loc=(x, y, 0), rot=(0, 0, math.pi if False else 0), parent=root, collection=cd, props={'destructible': 1, 'mass_kg': 900, 'role': 'lamp'})
        for lod in (0, 1):
            o = K.dup(PK.lamp_cobra(lod), f'Lamp_{i}_LOD{lod}', parent=e, collection=cd)
    # a chain-link fence at the lot sides
    fm_ = MB('Fence', seed=15)
    fm_.tone = tone(15, 0.5, 0.3)
    for sgn in (-1, 1):
        y = sgn * (LOTY + 0.4)
        n = int(LOTX / 2.5)
        for i in range(n + 1):
            fm_.cyl(i * 2.5, y, 0.0, 1.8, 0.03, 'steel', seg=6)
        fm_.tube([(0, y, 1.78), (LOTX, y, 1.78)], 0.02, 'steel', seg=5)
        fm_.tube([(0, y, 0.1), (LOTX, y, 0.1)], 0.01, 'steel', seg=4)
        for i in range(int(LOTX / 0.15)):                                    # wire diamonds as thin diagonal tubes would be heavy: a mesh panel card with alpha
            pass
    fence = fm_.build('Fence', collection=cs, parent=g_static)
    # fire anchors
    for i, (x, y, z) in enumerate(((9.0, -22.0, 5.2), (23.0, 22.0, 5.2), (8.0, 0.0, 0.1), (28.0, -16.0, 3.7))):
        K.empty(f'Fire_Anchor_{i}', loc=(x, y, z), parent=root, collection=cm, size=0.5)
    # colliders
    colls = []
    for nm, (x0, y0, z0, x1, y1, z1) in (('COL_Shop', (SX0, SY0, 0, SX1, SY1 + 6.0, H + 0.45)), ('COL_Forecourt', (0, -LOTY, -0.2, LOTX, LOTY, 0.0)), ('COL_Island_0', (12.25, isl_y[0] - 0.65, 0, 19.75, isl_y[0] + 0.65, 0.19)),
                                         ('COL_Island_1', (12.25, isl_y[1] - 0.65, 0, 19.75, isl_y[1] + 0.65, 0.19)), ('COL_Island_2', (12.25, isl_y[2] - 0.65, 0, 19.75, isl_y[2] + 0.65, 0.19))):
        c = MB(nm, uvshift=False)
        c.box(x0, y0, z0, x1, y1, z1, 'tar')
        o = c.build(nm, collection=cm, parent=root)
        colls.append(o)
    # ---- fix up collections for export, stats
    objs = K.descendants(root)
    K.save_blend(BLEND)
    K.export_glb(objs, OUT)
    meshes = [o for o in objs if o.type == 'MESH']
    STATS['tris_lod0'] = sum(K.tris(o) for o in meshes if o.get('lod', 0) != 1)
    STATS['tris_by_node'] = {o.name: K.tris(o) for o in meshes if o.get('lod', 0) != 1 and K.tris(o) > 0 and not o.name.startswith(('Hose_', 'Nozzle_'))}
    json.dump(STATS, open('D:/temp/take37/gas/gas_stats.json', 'w'), indent=1)
    log('exported', OUT, STATS['tris_lod0'])


build()
