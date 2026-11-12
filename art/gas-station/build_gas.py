# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""1987 American roadside gas station for TAKE 37 (fictional brand VALDOR, no real mark): deep fascia canopy on guarded columns, six electronic dispensers with readable
digit displays, price stele with 1987 prices, mini-mart with stocked shelves and coolers, car-wash bay, tank hatches, drains, markings.

  python -I art/gas-station/gas_tex.py                       (textures, once)
  blender -b -P art/gas-station/build_gas.py -- [--out gas_station.glb] [--lite gas_station_lite.glb] [--blend D:/temp/take37/gas/gas.blend]

Frame: origin on the ground at the middle of the street frontage, +X from the street into the lot, +Y left, +Z up. Lot x 0..36, y -34..34.
Every part with mass is an own node: an empty <Name> with <Name>_LOD0 / <Name>_LOD1 mesh children (extras: destructible, burnable, mass_kg, fuel_l, role).
  Pump_00..05 (+ Hose_*, Nozzle_* children), Canopy, CanopyColumn_0..2, PriceSign, AirStand, IceChest, PropaneCage, OilRack, TyreStack, Bin_*, NewsBox_*, Lamp_*, VentPipes, SignPost_*
  Static: Forecourt, Islands, Shop, Details
gas_station_lite.glb holds the LOD1 meshes only.
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
from kitlib import MB  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
arg = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d  # noqa: E731
HERE = pathlib.Path(__file__).resolve().parent
OUT = arg('--out', str(HERE / 'gas_station.glb'))
LITE = arg('--lite', str(HERE / 'gas_station_lite.glb'))
BLEND = arg('--blend', 'D:/temp/take37/gas/gas.blend')
STATS = {}
LOTX, LOTY = 36.0, 34.0
ISL_X, ISL_Y = 16.0, [-14.0, 0.0, 14.0]
CZ = 5.0
SX0, SX1, SY0, SY1 = 26.0, 33.0, -25.0, -9.0
H_SHOP = 3.9
R = CS = CD = CM = None


def log(*a):
    print('[gas]', *a, flush=True)


def tone(seed, h=0.5, amt=0.35):
    def f(p):
        g = 1.0 - amt * max(0.0, 1.0 - p.z / h) ** 1.4
        n = 0.84 + 0.28 * K.fbm(V((p.x * 0.4, p.y * 0.4, p.z * 0.4)), seed, 1.0)
        return (g * n, g * n * 0.99, g * n * 0.97)
    return f


def lodnode(name, fn, loc=(0, 0, 0), rz=0.0, dest=True, props=None, parent=None, seed=1):
    par = parent or R
    c = CD if dest else CS
    e = K.empty(name, loc=loc, rot=(0, 0, rz), parent=par, collection=c, size=0.3)
    if dest:
        e['destructible'] = 1
    for k, v in (props or {}).items():
        e[k] = v
    objs = []
    for lod in (0, 1):
        m = MB(f'{name}_LOD{lod}', seed)
        m.tone = tone(seed)
        fn(m, lod == 0)
        o = m.build(f'{name}_LOD{lod}', collection=c, parent=e)
        o['lod'] = lod
        objs.append(o)
    return e, objs


def cell(i, inset=0.004):
    c, r = i % 4, i // 4
    return (c * 0.25 + inset, 1 - (r + 1) * 0.25 + inset, c * 0.25 + 0.25 - inset, 1 - r * 0.25 - inset)


def sticker(m, i, x, y, z, w, h, nrm):
    """Decor-atlas cell i on a wall, centre (x, y, z), w wide, h high, facing nrm in '+x','-x','+y','-y'."""
    r = cell(i)
    if nrm in ('+x', '-x'):
        sg = 1 if nrm == '+x' else -1
        a, b = (-w / 2, w / 2) if sg > 0 else (w / 2, -w / 2)         # facing +x: left to right is +y
        p = [(x, y + a, z - h / 2), (x, y + b, z - h / 2), (x, y + b, z + h / 2), (x, y + a, z + h / 2)]
        o = (sg, 0, 0)
    else:
        sg = 1 if nrm == '+y' else -1
        a, b = (w / 2, -w / 2) if sg > 0 else (-w / 2, w / 2)         # facing +y: left to right is -x
        p = [(x + a, y, z - h / 2), (x + b, y, z - h / 2), (x + b, y, z + h / 2), (x + a, y, z + h / 2)]
        o = (0, sg, 0)
    m.face(p, 'decor', out=o, uv=[(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])])


def box_col(m, x0, y0, z0, x1, y1, z1, col):
    c = (col[0] / 255.0, col[1] / 255.0, col[2] / 255.0)
    cen = V(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    for pts in ([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)], [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
                [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], [(x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)], [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)]):
        m.face(pts, 'goods', inside=cen, color=lambda p, c=c: c)


# ---------------------------------------------------------------- pump
def pump_body(m, hi):
    hx, hy = 0.45, 0.25
    bv = 0.02 if hi else 0.0
    m.box(-hx - 0.04, -hy - 0.04, 0.0, hx + 0.04, hy + 0.04, 0.06, 'steel', bv=0.01 if hi else 0)
    m.box(-hx, -hy, 0.06, hx, hy, 0.3, 'paint_dark', bv=bv)
    m.box(-hx + 0.005, -hy + 0.005, 0.3, hx - 0.005, hy - 0.005, 0.8, 'paint_white', bv=bv)
    m.box(-hx, -hy, 0.8, hx, hy, 1.43, 'paint_white', bv=bv)
    m.box(-hx - 0.012, -hy - 0.012, 0.78, hx + 0.012, hy + 0.012, 0.8, 'paint_red')
    m.box(-hx - 0.02, -hy - 0.02, 0.28, hx + 0.02, hy + 0.02, 0.3, 'paint_red')
    m.box(-hx - 0.01, -hy - 0.01, 1.43, hx + 0.01, hy + 0.01, 1.47, 'paint_dark', bv=0.005 if hi else 0)
    m.box(-hx - 0.02, -hy - 0.03, 1.47, hx + 0.02, hy + 0.03, 1.84, 'paint_white', bv=0.03 if hi else 0)
    m.box(-hx - 0.025, -hy - 0.035, 1.84, hx + 0.025, hy + 0.035, 1.87, 'paint_dark', bv=0.008 if hi else 0)
    for s in (-1, 1):
        a, b = (hx, -hx) if s > 0 else (-hx, hx)
        yy = s * (hy + 0.0325)
        m.face([(a * 0.96, yy, 1.49), (b * 0.96, yy, 1.49), (b * 0.96, yy, 1.82), (a * 0.96, yy, 1.82)], 'pumphead', out=(0, s, 0), uv=[(0, 0), (1, 0), (1, 1), (0, 1)])
        yf = s * (hy + 0.004)
        m.face([(a * 0.9, yf, 0.82), (b * 0.9, yf, 0.82), (b * 0.9, yf, 1.42), (a * 0.9, yf, 1.42)], 'pumpface', out=(0, s, 0), uv=[(0, 0), (1, 0), (1, 1), (0, 1)])
        yg = s * (hy + 0.016)
        m.face([(a * 0.8, yg, 1.18), (b * 0.8, yg, 1.18), (b * 0.8, yg, 1.4), (a * 0.8, yg, 1.4)], 'glass', out=(0, s, 0))
        if hi:
            for k in range(7):
                m.box(-0.28, s * hy, 0.4 + k * 0.045, 0.28, s * (hy + 0.014), 0.4 + k * 0.045 + 0.022, 'steel')
            m.box(-0.33, s * hy, 0.33, 0.33, s * (hy + 0.006), 0.77, 'paint_grey', bv=0.004)
            m.box(0.22, s * (hy + 0.006), 0.52, 0.27, s * (hy + 0.025), 0.6, 'chrome', bv=0.004)
    for s in (-1, 1):
        x = s * (hx + 0.02)
        m.box(min(x, x + s * 0.12), -0.07, 0.82, max(x, x + s * 0.12), 0.07, 0.99, 'black_metal', bv=0.01 if hi else 0)
        m.box(min(x, x + s * 0.07), -0.05, 1.12, max(x, x + s * 0.07), 0.05, 1.25, 'steel', bv=0.005 if hi else 0)
        if hi:
            sticker(m, 11, x, 0.0, 1.38, 0.2, 0.2, '+x' if s > 0 else '-x')


def pump_hoses(lod, name, seed):
    hi = lod == 0
    res = []
    for s in (-1, 1):
        nm = 'A' if s > 0 else 'B'
        pts = [V((s * 0.30, s * 0.27, 1.26)), V((s * 0.52, s * 0.31, 1.44)), V((s * 0.74, s * 0.28, 1.25)), V((s * 0.78, s * 0.14, 1.08)), V((s * 0.62, 0.0, 1.14)), V((s * 0.57, 0.0, 1.12))]
        sm = []
        n = 10 if hi else 3
        for i in range(len(pts) - 1):
            p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, len(pts) - 1)]
            for k in range(n):
                t = k / n
                sm.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
        sm.append(pts[-1])
        h = MB(f'Hose_{name}_{nm}_LOD{lod}', seed + s)
        h.tone = lambda p: (0.85, 0.85, 0.85)
        h.tube(sm, 0.024 if hi else 0.022, 'rubber', seg=8 if hi else 4)
        h.cyl(s * 0.30, s * 0.27, 1.20, 1.30, 0.03, 'chrome', seg=8 if hi else 4)
        ho = h.build(f'Hose_{name}_{nm}_LOD{lod}')
        nz = MB(f'Nozzle_{name}_{nm}_LOD{lod}', seed + 3 * s)
        nz.at(s * 0.57, 0.0, 0.94)
        nz.cyl(0.0, 0.0, -0.13, 0.0, 0.011, 'chrome', seg=8 if hi else 4)
        nz.box(-0.035, -0.045, 0.0, 0.035, 0.045, 0.2, 'black_metal', bv=0.008 if hi else 0)
        nz.box(-0.03, -0.045, 0.2, 0.03, 0.045, 0.24, 'chrome')
        if hi:
            nz.tube([(0.0, 0.045, 0.1), (0.0, 0.1, 0.09), (0.0, 0.1, 0.02), (0.0, 0.045, 0.01)], 0.008, 'chrome', seg=5, caps=False)
            nz.box(-0.012, -0.075, 0.07, 0.012, -0.045, 0.1, 'paint_red', bv=0.003)
        nz.pop()
        no = nz.build(f'Nozzle_{name}_{nm}_LOD{lod}')
        res += [ho, no]
    return res


# ---------------------------------------------------------------- canopy
def canopy_body(m, hi):
    cx0, cx1, cy0, cy1 = 9.0, 23.0, -22.0, 22.0
    m.box(cx0, cy0, CZ + 0.4, cx1, cy1, CZ + 0.55, 'paint_white', bv=0.01 if hi else 0)
    fz0, fz1 = CZ - 0.1, CZ + 0.95
    ox0, ox1, oy0, oy1 = cx0 - 0.3, cx1 + 0.3, cy0 - 0.3, cy1 + 0.3
    for (x0, x1, y0, y1) in ((ox0, cx0, oy0, oy1), (cx1, ox1, oy0, oy1), (ox0, ox1, oy0, cy0), (ox0, ox1, cy1, oy1)):
        m.box(x0, y0, fz0, x1, y1, fz1, 'paint_white', bv=0.03 if hi else 0)
    for xf, o in ((ox0, -1), (ox1, 1)):
        d = 0.012 * o
        for (za, zb, mt) in ((CZ + 0.38, CZ + 0.62, 'paint_red'), (CZ + 0.32, CZ + 0.36, 'paint_yellow'), (CZ + 0.64, CZ + 0.67, 'paint_yellow')):
            m.box(min(xf, xf + d), oy0, za, max(xf, xf + d), oy1, zb, mt)
    for yf, o in ((oy0, -1), (oy1, 1)):
        d = 0.012 * o
        for (za, zb, mt) in ((CZ + 0.38, CZ + 0.62, 'paint_red'), (CZ + 0.32, CZ + 0.36, 'paint_yellow'), (CZ + 0.64, CZ + 0.67, 'paint_yellow')):
            m.box(ox0, min(yf, yf + d), za, ox1, max(yf, yf + d), zb, mt)
    if hi:
        for k in range(int((oy1 - oy0) / 0.4)):
            yy = oy0 + k * 0.4
            for xf, o in ((ox0, -1), (ox1, 1)):
                m.box(min(xf, xf + 0.008 * o), yy, fz0 + 0.05, max(xf, xf + 0.008 * o), yy + 0.012, CZ + 0.3, 'paint_grey')
                m.box(min(xf, xf + 0.008 * o), yy, CZ + 0.7, max(xf, xf + 0.008 * o), yy + 0.012, fz1 - 0.04, 'paint_grey')
        m.box(ox0 - 0.04, oy0 - 0.04, fz0 - 0.03, ox1 + 0.04, oy1 + 0.04, fz0 + 0.02, 'steel', bv=0.008)
        m.box(ox0 - 0.04, oy0 - 0.04, fz1 - 0.02, ox1 + 0.04, oy1 + 0.04, fz1 + 0.04, 'steel', bv=0.008)
    # lit brand plaques on both long faces (left/right of centre)
    for xf, o in ((ox0, -1), (ox1, 1)):
        for yc in (-11.0, 11.0):
            hw, z0, z1 = 1.8, CZ + 0.69, CZ + 0.94
            m.box(min(xf, xf + 0.04 * o), yc - hw, z0 - 0.02, max(xf, xf + 0.04 * o), yc + hw, z1 + 0.02, 'paint_dark', bv=0.006 if hi else 0)
            a, b = (yc + hw, yc - hw) if o < 0 else (yc - hw, yc + hw)
            xx = xf + 0.041 * o
            m.face([(xx, a, z0), (xx, b, z0), (xx, b, z1), (xx, a, z1)], 'shopfascia', out=(o, 0, 0), uv=[(0, 0.18), (0.55, 0.18), (0.55, 0.82), (0, 0.82)])
    # soffit with rib grid and recessed fluorescent troughs
    m.box(cx0, cy0, CZ - 0.04, cx1, cy1, CZ, 'plaster_white')
    for k in range(int((cy1 - cy0) / 2.0) + 1):
        yy = cy0 + k * 2.0
        m.box(cx0, yy - 0.05, CZ - 0.22, cx1, yy + 0.05, CZ - 0.04, 'paint_grey', bv=0.008 if hi else 0)
    for xx in (cx0 + 0.4, 12.0, 16.0, 20.0, cx1 - 0.4):
        m.box(xx - 0.05, cy0, CZ - 0.16, xx + 0.05, cy1, CZ - 0.04, 'paint_grey')
    for yy in ([-18.0, -14.0, -10.0, -4.0, 0.0, 4.0, 10.0, 14.0, 18.0] if hi else [-14.0, 0.0, 14.0]):
        for xx in ((12.5, 16.0, 19.5) if hi else (16.0,)):
            m.box(xx - 0.55, yy - 0.14, CZ - 0.25, xx + 0.55, yy + 0.14, CZ - 0.2, 'paint_grey', bv=0.01 if hi else 0)
            m.box(xx - 0.5, yy - 0.1, CZ - 0.255, xx + 0.5, yy + 0.1, CZ - 0.25, 'fluor')
    if hi:
        m.tube([(cx0 + 0.3, cy0 + 0.5, CZ - 0.07), (cx0 + 0.3, cy1 - 0.5, CZ - 0.07)], 0.02, 'steel', seg=6)
        for yy in (-14.0, 0.0, 14.0):
            m.box(15.2, yy - 0.15, CZ - 0.14, 16.8, yy + 0.15, CZ - 0.04, 'paint_grey', bv=0.01)
        for yy in (-14.0, 14.0):
            m.box(15.0, yy - 0.3, CZ + 0.55, 17.0, yy + 0.3, CZ + 0.6, 'steel', bv=0.004)
            for k in range(6):
                m.box(15.1, yy - 0.25 + k * 0.1, CZ + 0.6, 16.9, yy - 0.22 + k * 0.1, CZ + 0.63, 'black_metal')
        m.box(11.0, -3.0, CZ + 0.55, 12.4, -1.4, CZ + 1.1, 'paint_grey', bv=0.03)
        m.cyl(19.5, 5.0, CZ + 0.55, CZ + 0.95, 0.16, 'steel', seg=12)
        m.cyl(19.5, 5.0, CZ + 0.95, CZ + 1.05, 0.24, 'steel', seg=12, r1=0.06)


def column_body(m, hi):
    bv = 0.02 if hi else 0.0
    m.box(-0.5, -0.5, 0.0, 0.5, 0.5, 0.28, 'concrete', bv=0.03 if hi else 0)
    m.box(-0.23, -0.23, 0.28, 0.23, 0.23, CZ - 0.2, 'paint_white', bv=bv)
    m.box(-0.245, -0.245, 1.25, 0.245, 0.245, 1.6, 'paint_red', bv=bv)
    m.box(-0.245, -0.245, 1.6, 0.245, 0.245, 1.64, 'paint_yellow')
    m.box(-0.3, -0.3, CZ - 0.2, 0.3, 0.3, CZ + 0.05, 'paint_grey', bv=bv)
    ro = 0.42
    for z in (0.35, 0.9):
        m.tube([(ro, ro, z), (-ro, ro, z), (-ro, -ro, z), (ro, -ro, z), (ro, ro, z)], 0.04, 'paint_yellow', seg=8 if hi else 4, caps=False)
    for (x, y) in ((ro, ro), (-ro, ro), (-ro, -ro), (ro, -ro)):
        m.cyl(x, y, 0.28, 0.94, 0.04, 'paint_yellow', seg=10 if hi else 4)
    if hi:
        for (x, y) in ((ro, ro), (-ro, ro), (-ro, -ro), (ro, -ro)):
            m.cyl(x, y, 0.28, 0.32, 0.07, 'steel', seg=10)
        m.tube([(0.26, 0.2, CZ - 0.25), (0.26, 0.2, 0.45)], 0.04, 'paint_grey', seg=8)
        m.tube([(0.26, 0.2, 0.45), (0.3, 0.2, 0.3), (0.55, 0.2, 0.18)], 0.04, 'paint_grey', seg=8)
        m.box(0.5, 0.0, 0.0, 1.1, 0.6, 0.012, 'black_metal')
        for k in range(6):
            m.box(0.55, 0.05 + k * 0.09, 0.012, 1.05, 0.08 + k * 0.09, 0.02, 'steel')
        for z in (1.6, 3.0, 4.4):
            m.box(0.24, 0.17, z, 0.3, 0.23, z + 0.06, 'steel')
        sticker(m, 12, 0.0, -0.2455, 2.1, 0.3, 0.3, '-y')
        sticker(m, 5, 0.0, 0.2455, 2.1, 0.3, 0.3, '+y')
    else:
        m.tube([(0.26, 0.2, CZ - 0.25), (0.26, 0.2, 0.2)], 0.04, 'paint_grey', seg=4)


# ---------------------------------------------------------------- price stele
def stele_body(m, hi):
    m.box(-0.8, -0.8, 0.0, 0.8, 0.8, 0.2, 'kerb', bv=0.03 if hi else 0)
    m.box(-0.5, -0.5, 0.2, 0.5, 0.5, 0.75, 'concrete', bv=0.04 if hi else 0)
    m.box(-0.2, -0.2, 0.75, 0.2, 0.2, 5.3, 'paint_grey', bv=0.02 if hi else 0)
    m.box(-0.34, -0.34, 0.75, 0.34, 0.34, 0.85, 'paint_dark', bv=0.01 if hi else 0)
    if hi:
        for z in (2.0, 3.5):
            m.box(-0.23, -0.23, z, 0.23, 0.23, z + 0.05, 'paint_dark')
        for (x, y) in ((0.42, 0.42), (-0.42, 0.42), (-0.42, -0.42), (0.42, -0.42)):
            m.cyl(x, y, 0.75, 0.82, 0.03, 'steel', seg=6)
    zc0, zc1, w = 5.0, 8.5, 1.0
    m.box(-0.35, -w - 0.1, zc0 - 0.1, 0.35, w + 0.1, zc1 + 0.15, 'paint_dark', bv=0.03 if hi else 0, skip=('+y', '-y'))
    for s in (-1, 1):
        y = s * (w + 0.12)
        a, b = (w, -w) if s > 0 else (-w, w)
        m.face([(a, y, zc0), (b, y, zc0), (b, y, zc1), (a, y, zc1)], 'pricesign', out=(0, s, 0), uv=[(0, 0), (1, 0), (1, 1), (0, 1)])
        ya, yb = (y - 0.11, y + 0.01) if s > 0 else (y - 0.01, y + 0.11)
        m.box(-0.36, ya, zc0 - 0.12, 0.36, yb, zc0, 'paint_red')
        m.box(-0.36, ya, zc1, 0.36, yb, zc1 + 0.17, 'paint_red')
    m.box(-0.3, -w, zc1 + 0.15, 0.3, w, zc1 + 0.22, 'steel', bv=0.01 if hi else 0)


# ---------------------------------------------------------------- small destructibles
def air_body(m, hi):
    m.box(-0.45, -0.25, 0.0, 0.45, 0.25, 0.1, 'concrete', bv=0.012 if hi else 0)
    m.box(-0.3, -0.15, 0.1, 0.3, 0.15, 1.3, 'paint_blue', bv=0.02 if hi else 0)
    m.box(-0.33, -0.18, 1.3, 0.33, 0.18, 1.38, 'paint_dark', bv=0.012 if hi else 0)
    r = cell(8)
    m.face([(0.22, 0.152, 0.7), (-0.22, 0.152, 0.7), (-0.22, 0.152, 1.2), (0.22, 0.152, 1.2)], 'decor', out=(0, 1, 0), uv=[(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])])
    m.cyl(0.0, 0.16, 0.34, 0.56, 0.09, 'chrome', seg=14 if hi else 6)
    m.tube([(0.2, 0.16, 0.9), (0.4, 0.3, 0.75), (0.5, 0.4, 0.3), (0.35, 0.4, 0.08)], 0.022, 'rubber', seg=6 if hi else 3)
    m.box(0.62, -0.12, 0.0, 0.9, 0.12, 0.85, 'paint_grey', bv=0.012 if hi else 0)
    m.cyl(0.76, -0.12, 0.5, 0.58, 0.03, 'chrome', seg=8)
    r = cell(9)
    m.face([(0.62, -0.121, 0.62), (0.9, -0.121, 0.62), (0.9, -0.121, 0.8), (0.62, -0.121, 0.8)], 'decor', out=(0, -1, 0), uv=[(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])])


def icechest_body(m, hi):
    m.box(-0.4, -0.85, 0.0, 0.4, 0.85, 0.12, 'paint_dark', bv=0.01 if hi else 0)
    m.box(-0.38, -0.83, 0.12, 0.38, 0.83, 1.5, 'paint_white', bv=0.03 if hi else 0)
    m.box(-0.4, -0.85, 1.5, 0.4, 0.85, 1.58, 'paint_red', bv=0.02 if hi else 0)
    sticker(m, 3, 0.382, 0.0, 0.95, 1.4, 1.4, '+x')
    for k in (-1, 1):
        m.box(0.38, k * 0.42 - 0.2, 0.28, 0.39, k * 0.42 + 0.2, 0.34, 'steel')
    if hi:
        m.box(-0.1, 0.84, 0.3, 0.1, 0.9, 0.5, 'black_metal', bv=0.005)
        for k in range(6):
            m.box(-0.28, 0.84, 0.2 + k * 0.04, 0.28, 0.855, 0.22 + k * 0.04, 'steel')


def propane_body(m, hi):
    m.box(-0.45, -0.75, 0.0, 0.45, 0.75, 0.06, 'concrete', bv=0.01 if hi else 0)
    for (x, y) in ((-0.38, -0.7), (0.38, -0.7), (-0.38, 0.7), (0.38, 0.7)):
        m.cyl(x, y, 0.06, 1.55, 0.025, 'paint_grey', seg=6 if hi else 4)
    for z in (0.3, 0.8, 1.5):
        m.tube([(0.38, -0.7, z), (0.38, 0.7, z), (-0.38, 0.7, z), (-0.38, -0.7, z), (0.38, -0.7, z)], 0.012, 'steel', seg=4 if hi else 3, caps=False)
    for k in range(3):
        for j in range(2):
            x, y = -0.2 + j * 0.4, -0.45 + k * 0.45
            m.lathe([(0.0, 0.07), (0.15, 0.07), (0.16, 0.1), (0.16, 0.6), (0.14, 0.66), (0.08, 0.7), (0.07, 0.72), (0.07, 0.8), (0.0, 0.8)], 'paint_white', x=x, y=y, seg=14 if hi else 6)
            if hi:
                m.cyl(x, y, 0.8, 0.86, 0.05, 'chrome', seg=8)


def oilrack_body(m, hi):
    rnd = random.Random(4)
    m.box(-0.3, -0.5, 0.0, 0.3, 0.5, 0.05, 'paint_dark', bv=0.008 if hi else 0)
    for z in (0.05, 0.5, 0.95):
        m.box(-0.28, -0.48, z, 0.28, 0.48, z + 0.02, 'steel')
    for sy in (-0.47, 0.47):
        m.box(-0.28, sy - 0.015, 0.0, 0.28, sy + 0.015, 1.4, 'paint_dark')
    cols = ((200, 30, 36), (24, 90, 160), (240, 190, 30), (240, 240, 235), (40, 130, 70))
    for z in (0.07, 0.52, 0.97):
        n = 8 if hi else 3
        for k in range(n):
            y = -0.4 + k * 0.8 / max(1, n - 1)
            for dx in ((-0.1, 0.1) if hi else (0.0,)):
                box_col(m, dx - 0.05, y - 0.045, z, dx + 0.05, y + 0.045, z + 0.24, rnd.choice(cols))
        m.face([(0.054 - 0.1 - 0.05 + 0.1, -0.45, z + 0.05), (0.054 - 0.1 - 0.05 + 0.1, 0.45, z + 0.05), (0.054 - 0.1 - 0.05 + 0.1, 0.45, z + 0.2), (0.054 - 0.1 - 0.05 + 0.1, -0.45, z + 0.2)], 'oilcan', out=(1, 0, 0),
               uv=[(0.02, 0.35), (0.98, 0.35), (0.98, 0.9), (0.02, 0.9)]) if False else None


def tyres_body(m, hi):
    for k in range(5):
        m.at(0, 0, k * 0.2)
        m.lathe([(0.2, 0.0), (0.3, 0.005), (0.34, 0.04), (0.35, 0.07), (0.35, 0.13), (0.34, 0.16), (0.3, 0.195), (0.2, 0.2), (0.18, 0.16), (0.185, 0.1), (0.18, 0.04), (0.2, 0.0)], 'rubber', seg=28 if hi else 12)
        if hi:
            m.lathe([(0.348, 0.03), (0.358, 0.05), (0.358, 0.15), (0.348, 0.17)], 'rubber', seg=36)
        m.pop()


def bin_body(m, hi):
    m.lathe([(0.0, 0.0), (0.26, 0.0), (0.3, 0.04), (0.32, 0.9), (0.0, 0.9)], 'paint_green', seg=20 if hi else 8)
    m.lathe([(0.32, 0.9), (0.34, 0.93), (0.34, 0.98), (0.3, 1.02), (0.0, 1.02)], 'paint_dark', seg=20 if hi else 8)
    if hi:
        for z in (0.3, 0.55, 0.78):
            m.cyl(0, 0, z, z + 0.02, 0.325, 'paint_dark', seg=20, caps=(False, False))
        m.box(0.2, -0.12, 0.8, 0.36, 0.12, 0.98, 'black_metal', bv=0.01)


def newsbox_body(m, hi):
    m.box(-0.2, -0.22, 0.0, 0.2, 0.22, 0.12, 'paint_dark', bv=0.01 if hi else 0)
    m.box(-0.18, -0.2, 0.12, 0.18, 0.2, 1.0, 'paint_blue', bv=0.015 if hi else 0)
    m.box(0.18, -0.15, 0.55, 0.2, 0.15, 0.9, 'glass_dirty')
    m.box(0.18, -0.12, 0.2, 0.21, 0.12, 0.4, 'steel')
    if hi:
        m.box(0.2, -0.04, 0.3, 0.23, 0.04, 0.34, 'chrome')


def lamp_body(m, hi):
    seg = 16 if hi else 8
    m.cyl(0, 0, 0, 0.5, 0.25, 'concrete', seg=seg, caps=(False, True))
    m.lathe([(0.17, 0.5), (0.16, 0.7), (0.075, 1.0), (0.065, 8.6), (0.055, 8.7)], 'paint_grey', seg=seg)
    m.tube([(0, 0, 8.55), (0.05, 0, 8.95), (0.5, 0, 9.2), (1.3, 0, 9.3), (2.1, 0, 9.18)], 0.04, 'paint_grey', seg=8 if hi else 4)
    m.box(1.7, -0.2, 8.95, 2.75, 0.2, 9.18, 'paint_grey', bv=0.03 if hi else 0)
    m.box(1.8, -0.17, 8.93, 2.65, 0.17, 8.95, 'lamp_glass')


def vent_body(m, hi):
    for y in (-4.5, 5.0):
        m.cyl(0.0, y, 0.0, 3.6, 0.04, 'paint_grey', seg=10 if hi else 5)
        m.cyl(0.0, y, 3.6, 3.7, 0.06, 'paint_grey', seg=10 if hi else 5)
        m.lathe([(0.0, 3.7), (0.08, 3.7), (0.0, 3.86)], 'steel', x=0, y=y, seg=8)
        if hi:
            m.box(-0.12, y - 0.12, 0.0, 0.12, y + 0.12, 0.3, 'paint_yellow', bv=0.01)


def signpost_body(m, hi, which=15):
    m.cyl(0, 0, 0, 2.4, 0.03, 'steel', seg=8 if hi else 4)
    m.box(0.04, -0.3, 1.5, 0.052, 0.3, 2.3, 'steel', bv=0.004 if hi else 0)
    r = cell(which)
    m.face([(0.0521, -0.28, 1.52), (0.0521, 0.28, 1.52), (0.0521, 0.28, 2.28), (0.0521, -0.28, 2.28)], 'decor', out=(1, 0, 0), uv=[(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])])


# ---------------------------------------------------------------- shop
def shop_body(m, hi):
    rnd = random.Random(21)
    W0, W1 = SY0, SY1
    wallm = 'brick_buff'
    bv = 0.01 if hi else 0
    m.box(SX0, W0, 0.0, SX1, W1, 0.3, 'concrete', bv=bv)
    gl0, gl1 = 0.35, 2.75
    DY0, DY1 = -14.4, -12.6
    for (a, b) in ((W0, W0 + 0.6), (DY0, DY1), (W1 - 0.6, W1)):
        m.box(SX0 - 0.08, a, 0.3, SX0 + 0.3, b, H_SHOP, wallm, bv=bv)
    m.box(SX0 - 0.08, W0, gl1, SX0 + 0.3, W1, H_SHOP, wallm, bv=bv)
    m.box(SX0 - 0.08, W0 + 0.6, 0.3, SX0 + 0.3, DY0, gl0, wallm, bv=bv)
    m.box(SX0 - 0.08, DY1, 0.3, SX0 + 0.3, W1 - 0.6, gl0, wallm, bv=bv)
    for (a, b) in ((W0 + 0.6, DY0), (DY1, W1 - 0.6)):
        m.quad((SX0 + 0.1, b, gl0), (SX0 + 0.1, a, gl0), (SX0 + 0.1, a, gl1), (SX0 + 0.1, b, gl1), 'glass_shop', out=(-1, 0, 0))
        m.box(SX0 - 0.06, a, gl1 - 0.06, SX0 + 0.16, b, gl1, 'paint_dark')
        m.box(SX0 - 0.06, a, gl0, SX0 + 0.16, b, gl0 + 0.06, 'paint_dark')
        n = max(1, int((b - a) / 1.8))
        for k in range(n + 1):
            yy = a + (b - a) * k / n
            m.box(SX0 - 0.06, yy - 0.04, gl0, SX0 + 0.16, yy + 0.04, gl1, 'paint_dark', bv=0.006 if hi else 0)
    m.box(SX0 - 0.02, DY0 + 0.02, 0.3, SX0 + 0.08, DY1 - 0.02, 2.3, 'paint_dark', bv=0.01 if hi else 0)
    for (a, b) in ((DY0 + 0.07, -13.52), (-13.48, DY1 - 0.07)):
        m.quad((SX0 - 0.004, b, 0.55), (SX0 - 0.004, a, 0.55), (SX0 - 0.004, a, 2.2), (SX0 - 0.004, b, 2.2), 'glass_shop', out=(-1, 0, 0))
        m.box(SX0 - 0.012, a, 0.3, SX0 - 0.004, b, 0.5, 'steel')
    if hi:
        for yy in (-13.62, -13.38):
            m.tube([(SX0 - 0.06, yy, 1.0), (SX0 - 0.06, yy, 1.25)], 0.012, 'chrome', seg=6)
    m.box(SX0 - 0.1, -14.4, 2.3, SX0 + 0.1, -12.6, 2.34, 'paint_dark')
    sticker(m, 4, SX0 - 0.012, -13.1, 1.5, 0.28, 0.28, '-x')
    sticker(m, 5, SX0 - 0.012, -13.9, 1.5, 0.28, 0.28, '-x')
    m.box(SX0 - 0.45, W0 - 0.3, H_SHOP, SX0, W1 + 0.3, H_SHOP + 0.12, 'paint_white', bv=bv)
    m.box(SX0 - 0.45, W0 - 0.3, H_SHOP + 0.12, SX0 - 0.3, W1 + 0.3, H_SHOP + 1.0, 'paint_dark', bv=bv, skip=('-x',))
    m.face([(SX0 - 0.451, W1 + 0.3, H_SHOP + 0.15), (SX0 - 0.451, W0 - 0.3, H_SHOP + 0.15), (SX0 - 0.451, W0 - 0.3, H_SHOP + 0.98), (SX0 - 0.451, W1 + 0.3, H_SHOP + 0.98)], 'shopfascia', out=(-1, 0, 0),
           uv=[(0, 0.0), (1, 0.0), (1, 1), (0, 1)])
    m.box(SX0 - 1.2, -15.2, 2.9, SX0, -11.8, 3.0, 'paint_white', bv=0.01 if hi else 0)
    m.box(SX0 - 1.2, -15.2, 2.95, SX0 - 1.17, -11.8, 3.12, 'paint_red')
    m.box(SX0 - 1.2, -15.2, 2.88, SX0 - 0.1, -15.17, 3.12, 'paint_red')
    m.box(SX0 - 1.2, -11.83, 2.88, SX0 - 0.1, -11.8, 3.12, 'paint_red')
    m.box(SX0 - 0.1, W0 - 0.1, H_SHOP, SX1 + 0.1, W1 + 0.1, H_SHOP + 0.2, 'paint_white', bv=bv)
    m.box(SX0 - 0.45, W0 - 0.3, H_SHOP + 1.0, SX1 + 0.3, W1 + 0.3, H_SHOP + 1.08, 'steel', bv=0.005 if hi else 0)
    m.box(SX0, W0 - 0.3, H_SHOP + 0.2, SX1 + 0.3, W0 - 0.1, H_SHOP + 1.0, 'paint_dark')
    m.box(SX0, W1 + 0.1, H_SHOP + 0.2, SX1 + 0.3, W1 + 0.3, H_SHOP + 1.0, 'paint_dark')
    m.box(SX1 + 0.1, W0 - 0.3, H_SHOP + 0.2, SX1 + 0.3, W1 + 0.3, H_SHOP + 1.0, 'paint_dark')
    m.box(SX0 + 1.0, W0 + 2.0, H_SHOP + 0.2, SX0 + 2.6, W0 + 3.6, H_SHOP + 1.0, 'paint_grey', bv=0.03 if hi else 0)
    m.cyl(SX0 + 4, W1 - 3, H_SHOP + 0.2, H_SHOP + 0.9, 0.18, 'steel', seg=12 if hi else 6)
    m.box(SX0 + 2.5, W1 - 3.5, H_SHOP + 0.2, SX0 + 4.2, W1 - 1.8, H_SHOP + 1.5, 'paint_grey', bv=0.03 if hi else 0)
    m.box(SX0, W0, 0.3, SX1, W0 + 0.3, H_SHOP, 'brick_old')
    m.box(SX0, W1 - 0.3, 0.3, SX1, W1, H_SHOP, 'brick_old')
    m.box(SX1 - 0.3, W0, 0.3, SX1, W1, H_SHOP, 'brick_old')
    m.box(SX1, -20.0, 0.3, SX1 + 0.06, -18.8, 2.4, 'paint_grey', bv=0.008 if hi else 0)
    for xs in (SX0 + 2.0, SX0 + 4.5):
        m.box(xs, W0 - 0.05, 1.3, xs + 1.5, W0, 2.5, 'paint_dark')
        m.quad((xs + 0.05, W0 - 0.052, 1.35), (xs + 1.45, W0 - 0.052, 1.35), (xs + 1.45, W0 - 0.052, 2.45), (xs + 0.05, W0 - 0.052, 2.45), 'glass_dirty', out=(0, -1, 0))
    for yy in (-23.0, -17.5, -11.5):
        m.box(SX0 - 0.1, yy - 0.2, 3.2, SX0 + 0.12, yy + 0.2, 3.38, 'paint_grey', bv=0.01 if hi else 0)
        m.box(SX0 - 0.1, yy - 0.15, 3.18, SX0 + 0.1, yy + 0.15, 3.2, 'lamp_glass')
    # car-wash bay
    m.box(SX0, SY1, 0.0, SX1, SY1 + 6.0, 0.3, 'concrete')
    m.box(SX0, SY1 + 6.0 - 0.3, 0.3, SX1, SY1 + 6.0, H_SHOP, 'brick_old')
    m.box(SX0 - 0.08, SY1, 0.3, SX0 + 0.3, SY1 + 1.2, H_SHOP, wallm, bv=bv)
    m.box(SX0 - 0.08, SY1 + 4.8, 0.3, SX0 + 0.3, SY1 + 6.0, H_SHOP, wallm, bv=bv)
    m.box(SX0 - 0.08, SY1 + 1.2, 2.8, SX0 + 0.3, SY1 + 4.8, H_SHOP, wallm, bv=bv)
    m.box(SX1 - 0.3, SY1, 0.3, SX1, SY1 + 6.0, H_SHOP, 'brick_old')
    m.box(SX0, SY1, H_SHOP, SX1, SY1 + 6.0, H_SHOP + 0.15, 'paint_white')
    nsl = 14 if hi else 4
    for k in range(nsl):
        zz = 0.3 + k * (2.5 / nsl)
        m.box(SX0 + 0.04, SY1 + 1.2, zz, SX0 + 0.11, SY1 + 4.8, zz + (2.5 / nsl) - 0.02, 'steel', bv=0.004 if hi else 0)
    # interior
    ix0, ix1 = SX0 + 0.15, SX1 - 0.3
    iy0, iy1 = W0 + 0.3, W1 - 0.3
    m.quad((ix0, iy0, 0.31), (ix1, iy0, 0.31), (ix1, iy1, 0.31), (ix0, iy1, 0.31), 'shopfloor', out=(0, 0, 1))
    m.quad((ix0, iy0, gl1 + 0.4), (ix0, iy1, gl1 + 0.4), (ix1, iy1, gl1 + 0.4), (ix1, iy0, gl1 + 0.4), 'shopwall', out=(0, 0, -1))
    m.quad((ix1, iy1, 0.31), (ix1, iy0, 0.31), (ix1, iy0, gl1 + 0.4), (ix1, iy1, gl1 + 0.4), 'shopwall', out=(-1, 0, 0))
    m.quad((ix0, iy0, 0.31), (ix0, iy0, gl1 + 0.4), (ix1, iy0, gl1 + 0.4), (ix1, iy0, 0.31), 'shopwall', out=(0, 1, 0))
    m.quad((ix0, iy1, 0.31), (ix1, iy1, 0.31), (ix1, iy1, gl1 + 0.4), (ix0, iy1, gl1 + 0.4), 'shopwall', out=(0, -1, 0))
    for yy in (-22.0, -18.0, -14.0, -11.0):
        for xx in (SX0 + 1.3, SX0 + 3.8):
            m.box(xx - 0.6, yy - 0.15, gl1 + 0.37, xx + 0.6, yy + 0.15, gl1 + 0.4, 'fluor')
    cx = ix1 - 0.05
    m.box(cx - 0.8, iy0 + 0.2, 0.31, cx, iy1 - 0.2, 2.3, 'paint_white', bv=0.01 if hi else 0)
    n = 6
    ys = [iy0 + 0.4 + k * (iy1 - iy0 - 0.8) / n for k in range(n + 1)]
    drinks = ((200, 30, 36), (24, 90, 160), (30, 140, 70), (240, 190, 30), (230, 230, 230), (100, 50, 120))
    for k in range(n):
        m.box(cx - 0.805, ys[k] + 0.03, 0.45, cx - 0.79, ys[k + 1] - 0.03, 2.2, 'glass_dirty')
        for lv in range(5):
            z = 0.55 + lv * 0.36
            for j in range(4 if hi else 1):
                col = rnd.choice(drinks)
                w_ = (ys[k + 1] - ys[k] - 0.2) / (4 if hi else 1) - 0.03
                y0_ = ys[k] + 0.1 + j * (ys[k + 1] - ys[k] - 0.2) / (4 if hi else 1)
                box_col(m, cx - 0.78, y0_, z, cx - 0.62, y0_ + w_, z + 0.28, col)
    for gx in (SX0 + 3.0, SX0 + 5.0):
        ya, yb = iy0 + 1.2, (iy0 + 7.0 if gx < SX0 + 4 else iy0 + 6.0)
        m.box(gx - 0.3, ya, 0.31, gx + 0.3, yb, 0.4, 'paint_dark')
        m.box(gx - 0.3, ya, 0.31, gx - 0.28, yb, 1.7, 'paint_grey')
        m.box(gx + 0.28, ya, 0.31, gx + 0.3, yb, 1.7, 'paint_grey')
        for lv in range(5):
            z = 0.4 + lv * 0.28
            m.box(gx - 0.3, ya, z, gx + 0.3, yb, z + 0.02, 'steel')
            nn = int((yb - ya) / (0.16 if hi else 0.5))
            for j in range(nn):
                col = rnd.choice(((200, 30, 36), (24, 90, 160), (230, 200, 40), (240, 240, 235), (30, 120, 70), (230, 130, 30), (120, 70, 40)))
                y0_ = ya + j * (yb - ya) / nn
                hh = rnd.uniform(0.14, 0.24)
                for sgn in (-1, 1):
                    box_col(m, gx + sgn * 0.14 - 0.08, y0_ + 0.01, z + 0.02, gx + sgn * 0.14 + 0.08, y0_ + (yb - ya) / nn - 0.01, z + 0.02 + hh, col)
    m.box(SX0 + 1.0, -12.3, 0.31, SX0 + 1.9, -9.5, 1.05, 'wood_dark', bv=0.01 if hi else 0)
    m.box(SX0 + 0.95, -12.35, 1.05, SX0 + 1.95, -9.45, 1.09, 'paint_grey')
    m.box(SX0 + 1.1, -11.4, 1.09, SX0 + 1.6, -10.7, 1.3, 'paint_dark', bv=0.01)
    m.box(SX0 + 1.15, -11.3, 1.3, SX0 + 1.5, -10.8, 1.42, 'paint_grey')
    m.box(SX0 + 1.5, -9.6, 1.4, SX0 + 1.8, -9.5, 2.3, 'paint_dark')


# ---------------------------------------------------------------- forecourt and details
def forecourt_tone(seed=3):
    def f(p):
        n = 0.8 + 0.3 * K.fbm(V((p.x * 0.3, p.y * 0.3, 0.0)), seed, 1.0)
        slab = 0.9 + 0.12 * random.Random(int(math.floor(p.x / 4.5) * 31 + math.floor(p.y / 4.5) * 17)).random()
        stain = 1.0 - 0.4 * max(0.0, K.fbm(V((p.x * 1.1, p.y * 1.1, 4.0)), seed + 4, 1.0) - 0.55) * 2.6
        under = 0.88 if (9.0 < p.x < 23.0 and -22 < p.y < 22) else 1.0
        return (n * slab * stain * under,) * 3
    return f


def forecourt_body(m, hi):
    m.tone = forecourt_tone()
    cs = 1.5 if hi else 6.0
    nx, ny = int(LOTX / cs), int(LOTY * 2 / cs)
    m.grid((0.0, -LOTY, 0.0), (cs, 0, 0), (0, LOTY * 2 / ny, 0), nx, ny, 'concrete', out=(0, 0, 1))
    if hi:
        for i in range(1, int(LOTX / 4.5) + 1):
            m.box(i * 4.5 - 0.012, -LOTY, 0.0, i * 4.5 + 0.012, LOTY, 0.004, 'tar')
        for j in range(-int(LOTY / 4.5), int(LOTY / 4.5) + 1):
            m.box(0.0, j * 4.5 - 0.012, 0.0, LOTX, j * 4.5 + 0.012, 0.004, 'tar')
    m.box(LOTX, -LOTY, 0.0, LOTX + 0.25, LOTY, 0.2, 'kerb', bv=0.02 if hi else 0)
    m.box(0.0, -LOTY - 0.25, 0.0, LOTX, -LOTY, 0.2, 'kerb', bv=0.02 if hi else 0)
    m.box(0.0, LOTY, 0.0, LOTX, LOTY + 0.25, 0.2, 'kerb', bv=0.02 if hi else 0)
    m.box(LOTX + 0.25, -LOTY - 0.25, -0.03, LOTX + 8, LOTY + 0.25, 0.02, 'verge')


def islands_body(m, hi):
    m.tone = tone(5, 0.2, 0.3)
    for y in ISL_Y:
        x0, x1 = ISL_X - 3.75, ISL_X + 3.75
        m.box(x0, y - 0.7, 0.0, x1, y + 0.7, 0.2, 'kerb', bv=0.04 if hi else 0)
        m.box(x0 + 0.05, y - 0.62, 0.2, x1 - 0.05, y + 0.62, 0.205, 'concrete')
        for s in (-1, 1):
            m.box(x0, min(y + s * 0.7, y + s * 0.62), 0.2, x1, max(y + s * 0.7, y + s * 0.62), 0.21, 'paint_yellow')
        for xx in (x0 + 0.2, x1 - 0.2):
            m.cyl(xx, y, 0.2, 1.0, 0.1, 'paint_yellow', seg=14 if hi else 6)
            m.cyl(xx, y, 1.0, 1.04, 0.105, 'paint_yellow', seg=14 if hi else 6)
            if hi:
                m.cyl(xx, y, 0.2, 0.26, 0.15, 'steel', seg=14)
        m.box(x0 + 0.5, y - 0.15, 0.2, x0 + 0.62, y + 0.15, 1.3, 'paint_red', bv=0.01 if hi else 0)
        m.box(x0 + 0.4, y - 0.18, 1.0, x0 + 0.72, y + 0.18, 1.25, 'paint_white', bv=0.01 if hi else 0)
        if hi:
            m.at(x1 - 0.8, y, 0.205)
            m.lathe([(0.0, 0.0), (0.17, 0.0), (0.19, 0.3), (0.0, 0.3)], 'paint_blue', seg=14)
            m.tube([(0.1, 0.0, 0.3), (0.08, 0.0, 0.75)], 0.012, 'steel', seg=5)
            m.box(0.0, -0.14, 0.72, 0.18, 0.14, 0.76, 'rubber', bv=0.005)
            m.pop()


def details_body(m, hi):
    rnd = random.Random(11)

    def decal(x, y, w, h, ang, ci, z=0.006):
        r = cell(ci, 0.003)
        ca, sa = math.cos(ang), math.sin(ang)
        pts = [(x + dx * ca - dy * sa, y + dx * sa + dy * ca, z) for (dx, dy) in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
        m.face(pts, 'decals', out=(0, 0, 1), uv=[(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])])

    def line(x0, y0, x1, y1, mat, w=0.12):
        L = math.hypot(x1 - x0, y1 - y0)
        nx, ny = -(y1 - y0) / L * w / 2, (x1 - x0) / L * w / 2
        m.face([(x0 - nx, y0 - ny, 0.008), (x1 - nx, y1 - ny, 0.008), (x1 + nx, y1 + ny, 0.008), (x0 + nx, y0 + ny, 0.008)], mat, out=(0, 0, 1), uv=[(0, 0), (L / 2, 0), (L / 2, w / 2), (0, w / 2)])

    for y in ISL_Y:
        for side in (-1, 1):
            for k in range(7 if hi else 3):
                decal(ISL_X + rnd.uniform(-3.4, 3.4), y + side * rnd.uniform(1.7, 3.0), rnd.uniform(1.0, 2.6), rnd.uniform(1.0, 2.6), rnd.uniform(0, 6.28), rnd.choice([0, 1, 9]), 0.006 + 0.0004 * k)
            decal(ISL_X + rnd.uniform(-2.5, 2.5), y + side * 1.15, 3.2, 1.5, 0.0, 9, 0.0075)
    for (x, y) in ((6, -26), (30, -2), (8, 22), (31, 27), (22, 9), (5, -7), (28, 14)):
        decal(x, y, rnd.uniform(2.5, 4.5), rnd.uniform(2.5, 4.5), rnd.uniform(0, 6.28), rnd.choice([2, 3, 8, 4]), 0.007)
    for (x, y, a) in ((12.5, -8.0, 0.3), (30.0, -4.0, 1.1), (24.0, 18.0, 0.0)):
        decal(x, y, 0.78, 0.78, a, 5, 0.012)
    for (x, y, d) in ((3.0, -6.0, 1), (3.0, 6.0, 1)):
        line(x, y, x + 4.0 * d, y, 'line_white', 0.2)
    for k in range(6):
        yy = SY0 + 1.0 + k * 3.0
        if yy < SY1:
            line(SX0 - 5.5, yy, SX0 - 2.0, yy, 'line_white', 0.1)
    line(SX0 - 5.5, SY0 + 1.0, SX0 - 5.5, SY1 - 0.6, 'line_white', 0.1)
    for y in ISL_Y:
        for k in range(4):
            line(ISL_X - 4.4, y - 0.55 + k * 0.28, ISL_X - 4.9, y - 0.95 + k * 0.28, 'line_yellow', 0.1)
    line(SX0 - 2.2, SY0, SX0 - 2.2, SY1, 'line_yellow', 0.2)

    def grate(x0, y0, x1, y1):
        m.box(x0 - 0.04, y0 - 0.04, 0.0, x1 + 0.04, y1 + 0.04, 0.01, 'black_metal')
        horiz = (x1 - x0) > (y1 - y0)
        ln = (x1 - x0) if horiz else (y1 - y0)
        n = int(ln / 0.06) if hi else int(ln / 0.3)
        for k in range(n):
            t = (k + 0.5) / n
            if horiz:
                m.box(x0 + ln * t - 0.012, y0, 0.0, x0 + ln * t + 0.012, y1, 0.014, 'steel')
            else:
                m.box(x0, y0 + ln * t - 0.012, 0.0, x1, y0 + ln * t + 0.012, 0.014, 'steel')
    for y in ISL_Y:
        for s in (-1, 1):
            grate(ISL_X - 3.2, y + s * 2.2 - 0.07, ISL_X + 3.2, y + s * 2.2 + 0.07)
    grate(SX0 - 2.0, -19.4, SX0 - 1.4, -18.6)
    grate(34.0, 0.0, 34.4, 4.0)
    for (x, y, col) in ((7.0, -4.5, 'paint_red'), (7.0, 0.0, 'paint_blue'), (7.0, 4.5, 'paint_white'), (7.0, 9.0, 'paint_green')):
        m.cyl(x, y, -0.005, 0.014, 0.4, 'steel', seg=28 if hi else 12)
        m.cyl(x, y, 0.014, 0.02, 0.3, col, seg=28 if hi else 12)
        m.cyl(x, y, 0.02, 0.1, 0.11, 'steel', seg=14 if hi else 6)
        m.cyl(x, y, 0.1, 0.13, 0.13, col, seg=14 if hi else 6)
        if hi:
            for j in range(8):
                a = j * math.pi / 4
                m.cyl(x + 0.35 * math.cos(a), y + 0.35 * math.sin(a), 0.014, 0.034, 0.02, 'steel', seg=6)
            m.cyl(x + 0.26, y, 0.02, 0.06, 0.04, 'paint_yellow', seg=8)
    decal(24.8, 24.0, 2.0, 2.0, 0.0, 9, 0.0078)


# ---------------------------------------------------------------- build
def build():
    global R, CS, CD, CM
    K.reset()
    R = K.empty('GasStation', size=3.0)
    CS = K.coll('Gas_Static')
    CD = K.coll('Gas_Destructible')
    CM = K.coll('Gas_Markers')
    g_static = K.empty('Static', parent=R, collection=CS)
    for nm, fn, seed in (('Forecourt', forecourt_body, 2), ('Islands', islands_body, 5), ('Shop', shop_body, 7), ('Details', details_body, 6)):
        lodnode(nm, fn, dest=False, parent=g_static, seed=seed)
    lodnode('Canopy', canopy_body, props={'burnable': 1, 'mass_kg': 2600, 'role': 'canopy roof; falls when CanopyColumn_* are gone'}, seed=8)
    for i, y in enumerate(ISL_Y):
        lodnode(f'CanopyColumn_{i}', column_body, loc=(ISL_X, y, 0.19), props={'mass_kg': 520, 'role': 'canopy column', 'supports': 'Canopy'}, seed=20 + i)
    pidx = 0
    for ii, y in enumerate(ISL_Y):
        for jx in (-1.75, 1.75):
            nm = f'Pump_{pidx:02d}'
            e, objs = lodnode(nm, pump_body, loc=(ISL_X + jx, y, 0.2), props={'burnable': 1, 'fuel_l': 160, 'mass_kg': 420, 'role': 'fuel dispenser, 2 customers on the +-Y faces',
                                                                         'grade': ['regular', 'unleaded', 'super'][pidx % 3]}, seed=30 + pidx)
            for lod in (0, 1):
                for part in pump_hoses(lod, nm, 40 + pidx):
                    CD.objects.link(part)
                    part.parent = e
                    part['lod'] = lod
            K.empty(f'Fire_{nm}_top', loc=(ISL_X + jx, y, 2.0), parent=R, collection=CM, size=0.3)
            K.empty(f'Fire_{nm}_hose', loc=(ISL_X + jx + 0.7, y, 1.1), parent=R, collection=CM, size=0.3)
            pidx += 1
    lodnode('PriceSign', stele_body, loc=(3.2, 30.5, 0.0), props={'mass_kg': 900, 'role': 'price stele, 8.7 m, lit', 'lit': 1}, seed=9)
    lodnode('AirStand', air_body, loc=(24.5, 24.0, 0.0), rz=math.pi, props={'mass_kg': 90, 'role': 'air and water stand'}, seed=12)
    lodnode('IceChest', icechest_body, loc=(SX0 - 0.7, -10.9, 0.0), props={'mass_kg': 260, 'role': 'packaged ice freezer'}, seed=13)
    lodnode('PropaneCage', propane_body, loc=(SX0 - 0.7, -22.0, 0.0), props={'burnable': 1, 'mass_kg': 140, 'role': 'propane exchange cage', 'explosive': 1}, seed=14)
    lodnode('OilRack', oilrack_body, loc=(SX0 - 0.6, -16.8, 0.0), props={'burnable': 1, 'mass_kg': 40, 'role': 'oil rack'}, seed=15)
    lodnode('TyreStack', tyres_body, loc=(SX0 - 0.8, SY1 + 1.0, 0.0), props={'burnable': 1, 'mass_kg': 60, 'role': 'tyres'}, seed=16)
    for i, (x, y) in enumerate(((SX0 - 0.7, -8.0), (23.8, -11.0), (10.0, 11.0), (26.8, -3.0))):
        lodnode(f'Bin_{i}', bin_body, loc=(x, y, 0.0), props={'mass_kg': 25, 'role': 'bin'}, seed=17 + i)
    for i, y in enumerate((-19.4, -20.1)):
        lodnode(f'NewsBox_{i}', newsbox_body, loc=(SX0 - 0.4, y, 0.0), props={'mass_kg': 40, 'role': 'news box'}, seed=22 + i)
    for i, (x, y) in enumerate(((3.0, -30.0), (3.0, 20.0), (33.0, 30.0))):
        lodnode(f'Lamp_{i}', lamp_body, loc=(x, y, 0.0), rz=(0.0 if i < 2 else math.pi), props={'mass_kg': 900, 'role': 'lamp'}, seed=26 + i)
    lodnode('VentPipes', vent_body, loc=(34.8, 0.0, 0.0), props={'mass_kg': 30, 'role': 'tank vent pipes'}, seed=11)
    for i, (x, y, w, rz) in enumerate(((2.0, -20.0, 15, 0.0), (2.0, 20.0, 6, 0.0), (LOTX - 2, 8.0, 12, math.pi))):
        lodnode(f'SignPost_{i}', lambda m, hi, w=w: signpost_body(m, hi, w), loc=(x, y, 0.0), rz=rz, props={'mass_kg': 12, 'role': 'sign'}, seed=60 + i)
    for i, (x, y, z) in enumerate(((9.0, -22.0, 5.2), (23.0, 22.0, 5.2), (7.0, 0.0, 0.1), (SX0, -17.0, 2.0), (SX0 - 0.7, -22.0, 1.0))):
        K.empty(f'Fire_Anchor_{i}', loc=(x, y, z), parent=R, collection=CM, size=0.5)
    cols = (('COL_Shop', (SX0, SY0, 0, SX1, SY1 + 6.0, H_SHOP + 0.2)), ('COL_Forecourt', (0, -LOTY, -0.3, LOTX, LOTY, 0.0))) + tuple((f'COL_Island_{i}', (ISL_X - 3.75, y - 0.7, 0, ISL_X + 3.75, y + 0.7, 0.2)) for i, y in enumerate(ISL_Y))
    for nm, (x0, y0, z0, x1, y1, z1) in cols:
        c = MB(nm, uvshift=False)
        c.box(x0, y0, z0, x1, y1, z1, 'tar')
        c.build(nm, collection=CM, parent=R)
    objs = K.descendants(R)
    K.save_blend(BLEND)
    K.export_glb(objs, OUT)
    lite = [o for o in objs if not (o.type == 'MESH' and o.get('lod') == 0)]
    K.export_glb(lite, LITE)
    meshes = [o for o in objs if o.type == 'MESH']
    STATS['tris_lod0'] = sum(K.tris(o) for o in meshes if o.get('lod', 0) != 1)
    STATS['tris_lod1'] = sum(K.tris(o) for o in meshes if o.get('lod') == 1)
    STATS['by_node'] = {o.name: K.tris(o) for o in meshes if o.get('lod') == 0}
    json.dump(STATS, open('D:/temp/take37/gas/gas_stats.json', 'w'), indent=1)
    log('exported', OUT, STATS['tris_lod0'], STATS['tris_lod1'])


build()
