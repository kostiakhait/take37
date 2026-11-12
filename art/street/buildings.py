# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""1980s small-town main-street buildings for TAKE 37: brick, clapboard and plaster fronts, 2-3 storeys, storefronts with awnings, signs, cornices, fire escapes.

Local frame: origin on the ground at the middle of the street front, +X = out of the front (towards the street), building runs back along -X, +Z up, width along Y.
make_building(spec, lod) returns one object (LOD0 full detail, LOD1 reduced: flush windows, coarse cells, no small trim).
spec keys: seed, W, D, floors, wall (material), trim (material), roof ('flat'|'gable'|'saw'), shop (shop sign index), awning (material or None), style ('brick'|'clap'|'plaster'), fire_escape, corner.
"""
import json
import math
import random

from mathutils import Vector as V

import kitlib as K
from kitlib import MB

FH0, FH = 4.3, 3.4            # ground-floor and upper floor heights
SIGN_ATLAS = {'cols': 2, 'rows': 16}


def sign_rect(i):
    c, r = i % 2, i // 2
    return (c * 0.5, 1 - (r + 1) / 16, c * 0.5 + 0.5, 1 - r / 16)


def interior_rect(i):
    c, r = i % 2, i // 2
    return (c * 0.5 + 0.004, 1 - (r + 1) * 0.5 + 0.004, c * 0.5 + 0.496, 1 - r * 0.5 - 0.004)


def tone_fn(seed, kind='wall'):
    def f(p):
        splash = 1.0 - 0.38 * max(0.0, 1.0 - p.z / 1.1) ** 1.4
        n = 0.80 + 0.32 * K.fbm(V((p.x * 0.35, p.y * 0.35, p.z * 0.35)), seed, 1.0)
        streak = 1.0 - 0.20 * max(0.0, K.fbm(V((p.y * 2.7, p.x * 2.7, p.z * 0.09)), seed + 3, 1.0) - 0.45) * 2.2
        soot = 1.0 - 0.12 * max(0.0, (p.z - 8.0) / 3.0) if p.z > 8 else 1.0
        v = splash * n * streak * soot
        return (v, v * 0.985, v * 0.96)
    return f


def cells(lo, hi, step):
    n = max(1, int(math.ceil((hi - lo) / step)))
    return [lo + (hi - lo) * i / n for i in range(n + 1)]


class Facade:
    """A wall plane at x = x0 facing +X, built from quad cells with holes for openings (so vertex tone varies across the wall)."""

    def __init__(self, m, x0, y0, y1, z0, z1, wall, openings, step, hi):
        self.m, self.x0, self.wall, self.open = m, x0, wall, openings
        ys = {y0, y1}
        zs = {z0, z1}
        for (a, b, c, d) in openings:
            ys.update((a, b))
            zs.update((c, d))
        ys, zs = sorted(ys), sorted(zs)

        def refine(vals):
            out = []
            for a, b in zip(vals[:-1], vals[1:]):
                out += cells(a, b, step)[:-1]
            out.append(vals[-1])
            return out
        ys, zs = refine(ys), refine(zs)
        for ya, yb in zip(ys[:-1], ys[1:]):
            for za, zb in zip(zs[:-1], zs[1:]):
                cy, cz = (ya + yb) / 2, (za + zb) / 2
                if any(a < cy < b and c < cz < d for (a, b, c, d) in openings):
                    continue
                m.face([(x0, yb, za), (x0, ya, za), (x0, ya, zb), (x0, yb, zb)], wall, out=(1, 0, 0))


def window_upper(m, y, zc, w, h, x0, hi, spec, rnd, lit):
    """Double-hung window in a wall at x0: reveal, casing, sill, lintel, two sashes with muntins, glass, blind behind."""
    trim = spec['trim']
    y0, y1, z0, z1 = y - w / 2, y + w / 2, zc - h / 2, zc + h / 2
    d = 0.22 if hi else 0.0
    if hi:
        for pts, nrm in (([(x0, y1, z0), (x0 - d, y1, z0), (x0 - d, y1, z1), (x0, y1, z1)], (0, -1, 0)), ([(x0, y0, z0), (x0, y0, z1), (x0 - d, y0, z1), (x0 - d, y0, z0)], (0, 1, 0)),
                         ([(x0, y0, z1), (x0, y1, z1), (x0 - d, y1, z1), (x0 - d, y0, z1)], (0, 0, -1))):
            m.face(pts, spec['wall'], out=nrm)
        m.face([(x0, y0, z0), (x0 - d, y0, z0), (x0 - d, y1, z0), (x0, y1, z0)], trim, out=(0, 0, 1))
        # casing
        c = 0.09
        m.box(x0, y0 - c, z1, x0 + 0.03, y1 + c, z1 + c, trim, bv=0.008)
        m.box(x0, y0 - c, z0 - c, x0 + 0.03, y0, z1, trim, bv=0.006)
        m.box(x0, y1, z0 - c, x0 + 0.03, y1 + c, z1, trim, bv=0.006)
        m.box(x0 - 0.02, y0 - 0.06, z0 - 0.1, x0 + 0.14, y1 + 0.06, z0 - 0.0, trim, bv=0.012)      # sill, projecting
        m.box(x0 - 0.02, y0 - 0.14, z1 + c, x0 + 0.06, y1 + 0.14, z1 + c + 0.14, 'concrete' if spec['style'] != 'clap' else trim, bv=0.01)   # lintel / head
        xg = x0 - d + 0.04
        # sashes
        mid = (z0 + z1) / 2
        f = 0.045
        for (sz0, sz1, xo) in ((z0, mid + 0.02, 0.0), (mid - 0.02, z1, 0.035)):
            xs = xg + xo
            m.box(xs, y0, sz0, xs + 0.04, y0 + f, sz1, trim, bv=0.004)
            m.box(xs, y1 - f, sz0, xs + 0.04, y1, sz1, trim, bv=0.004)
            m.box(xs, y0 + f, sz0, xs + 0.04, y1 - f, sz0 + f, trim, bv=0.004)
            m.box(xs, y0 + f, sz1 - f, xs + 0.04, y1 - f, sz1, trim, bv=0.004)
            for k in (1, 2):                                       # muntins 3 across
                yy = y0 + (y1 - y0) * k / 3
                m.box(xs + 0.01, yy - 0.008, sz0 + f, xs + 0.03, yy + 0.008, sz1 - f, trim)
            zz = (sz0 + sz1) / 2
            m.box(xs + 0.01, y0 + f, zz - 0.008, xs + 0.03, y1 - f, zz + 0.008, trim)
        m.quad((xg + 0.02, y1, z0), (xg + 0.02, y0, z0), (xg + 0.02, y0, z1), (xg + 0.02, y1, z1), 'glass_dirty', out=(1, 0, 0))
    else:
        m.quad((x0 - 0.02, y1, z0), (x0 - 0.02, y0, z0), (x0 - 0.02, y0, z1), (x0 - 0.02, y1, z1), 'glass_dirty', out=(1, 0, 0))
        m.box(x0, y0 - 0.05, z0 - 0.08, x0 + 0.1, y1 + 0.05, z0, trim)
    # what is behind the glass: blind, curtain or dark room
    bx = x0 - (0.5 if hi else 0.3)
    r = interior_rect(rnd.randrange(4))
    m.uvrect([(bx, y1, z0), (bx, y0, z0), (bx, y0, z1), (bx, y1, z1)], 'interiors', r, out=(1, 0, 0))


def shopfront(m, spec, hi, x0, y0, y1, rnd):
    """Ground floor: bulkhead, display windows, recessed door, transom, sign band, awning."""
    W = y1 - y0
    trim = spec['trim']
    zb, zt = 0.55, 3.15                          # display glass from 0.55 to 3.15
    door_w = 1.0
    dpos = rnd.choice([-1, 0, 1]) * (W / 2 - door_w / 2 - 1.2) if W > 8 else (W / 2 - door_w / 2 - 0.5) * rnd.choice([-1, 1])
    margin = 0.35
    # piers at both ends
    glass_y0, glass_y1 = y0 + margin, y1 - margin
    rec = 1.1                                   # door recess depth
    dy0, dy1 = dpos - door_w / 2 - 0.12, dpos + door_w / 2 + 0.12
    seg = [(glass_y0, dy0), (dy1, glass_y1)]
    shopmat = spec.get('bulk', 'brick_brown')
    wood = 'wood_dark'
    # frames around each display window
    for (a, b) in seg:
        if b - a < 0.8:
            continue
        # bulkhead panel
        m.box(x0 - 0.1, a, 0.0, x0 + 0.06, b, zb, shopmat, bv=0.012 if hi else 0)
        m.box(x0 - 0.02, a - 0.05, zb - 0.04, x0 + 0.1, b + 0.05, zb + 0.04, trim, bv=0.01 if hi else 0)      # stall board cap
        # glass, set back 0.25
        xg = x0 - 0.22
        m.quad((xg, b, zb), (xg, a, zb), (xg, a, zt), (xg, b, zt), 'glass', out=(1, 0, 0))
        # frame: aluminium-wood mullions
        fr = 0.06
        m.box(xg - 0.02, a, zb, xg + 0.1, a + fr, zt, wood, bv=0.006 if hi else 0)
        m.box(xg - 0.02, b - fr, zb, xg + 0.1, b, zt, wood, bv=0.006 if hi else 0)
        m.box(xg - 0.02, a, zt - fr, xg + 0.1, b, zt, wood, bv=0.006 if hi else 0)
        m.box(xg - 0.02, a, zb, xg + 0.1, b, zb + fr, wood, bv=0.006 if hi else 0)
        n = int((b - a) / 1.6)
        if hi:
            for k in range(1, n + 1):
                yy = a + (b - a) * k / (n + 1)
                m.box(xg - 0.01, yy - 0.025, zb, xg + 0.08, yy + 0.025, zt, wood, bv=0.004)
            m.box(xg - 0.01, a, zt - 0.5, xg + 0.08, b, zt - 0.45, wood)                                 # transom bar
        # shop interior backdrop, lit
        bx = x0 - 0.9
        r = interior_rect(rnd.randrange(4))
        m.uvrect([(bx, b, zb), (bx, a, zb), (bx, a, zt), (bx, b, zt)], 'interiors', r, out=(1, 0, 0))
        m.quad((x0 - 0.22, a, zt), (x0 - 0.22, b, zt), (bx, b, zt), (bx, a, zt), 'interiors', out=(0, 0, -1), uv=[(0.02, 0.9), (0.02, 0.9), (0.02, 0.9), (0.02, 0.9)]) if False else None
        m.quad((x0 - 0.22, a, zb), (bx, a, zb), (bx, b, zb), (x0 - 0.22, b, zb), 'wood_oak', out=(0, 0, 1))      # floor boards
        m.quad((x0 - 0.22, a, zt), (bx, a, zt), (bx, b, zt), (x0 - 0.22, b, zt), 'plaster_cream', out=(0, 0, -1))
        m.quad((x0 - 0.22, a, zb), (x0 - 0.22, a, zt), (bx, a, zt), (bx, a, zb), 'plaster_cream', out=(0, 1, 0))
        m.quad((x0 - 0.22, b, zb), (bx, b, zb), (bx, b, zt), (x0 - 0.22, b, zt), 'plaster_cream', out=(0, -1, 0))
    # recessed entrance
    xr = x0 - rec
    m.quad((x0 - 0.12, dpos + door_w / 2 + 0.12, 0.0), (xr, dpos + door_w / 2 + 0.12, 0.0), (xr, dpos + door_w / 2 + 0.12, zt), (x0 - 0.12, dpos + door_w / 2 + 0.12, zt), spec['wall'], out=(0, -1, 0))
    m.quad((xr, dpos - door_w / 2 - 0.12, 0.0), (x0 - 0.12, dpos - door_w / 2 - 0.12, 0.0), (x0 - 0.12, dpos - door_w / 2 - 0.12, zt), (xr, dpos - door_w / 2 - 0.12, zt), spec['wall'], out=(0, 1, 0))
    m.quad((x0 - 0.12, dy0, zt), (xr, dy0, zt), (xr, dy1, zt), (x0 - 0.12, dy1, zt), 'plaster_cream', out=(0, 0, -1))
    m.quad((x0 - 0.12, dy0, 0.01), (xr, dy0, 0.01), (xr, dy1, 0.01), (x0 - 0.12, dy1, 0.01), 'concrete', out=(0, 0, 1))
    # glass door with a wooden frame, a push bar and kick plate
    m.box(xr - 0.04, dpos - door_w / 2, 0.0, xr + 0.04, dpos + door_w / 2, 2.15, wood, bv=0.01 if hi else 0, skip=())
    m.quad((xr + 0.045, dpos + door_w / 2 - 0.1, 0.5), (xr + 0.045, dpos - door_w / 2 + 0.1, 0.5), (xr + 0.045, dpos - door_w / 2 + 0.1, 2.05), (xr + 0.045, dpos + door_w / 2 - 0.1, 2.05), 'glass', out=(1, 0, 0))
    if hi:
        m.box(xr + 0.04, dpos - 0.04, 0.95, xr + 0.12, dpos - 0.01, 1.1, 'chrome', bv=0.003)               # handle
        m.box(xr + 0.045, dpos - door_w / 2 + 0.1, 0.05, xr + 0.055, dpos + door_w / 2 - 0.1, 0.45, 'steel')
        m.quad((xr - 0.04, dpos + door_w / 2 - 0.1, 0.5), (xr - 0.04, dpos - door_w / 2 + 0.1, 0.5), (xr - 0.04, dpos - door_w / 2 + 0.1, 2.05), (xr - 0.04, dpos + door_w / 2 - 0.1, 2.05), 'glass', out=(-1, 0, 0))
        m.box(x0 - 0.05, dpos - 0.5, 0.0, x0 + 0.2, dpos + 0.5, 0.04, 'concrete', bv=0.01)           # threshold step
    # transom above door
    m.quad((xr + 0.01, dpos + door_w / 2, 2.2), (xr + 0.01, dpos - door_w / 2, 2.2), (xr + 0.01, dpos - door_w / 2, zt - 0.05), (xr + 0.01, dpos + door_w / 2, zt - 0.05), 'glass', out=(1, 0, 0))
    # sign band with the atlas board; a cornice over it
    sy0, sy1 = y0 + 0.2, y1 - 0.2
    sz0, sz1 = zt + 0.12, zt + 0.12 + min(0.95, (sy1 - sy0) / 7.0)
    sz1 = max(sz1, sz0 + 0.55)
    m.box(x0, sy0, sz0 - 0.05, x0 + 0.12, sy1, sz1 + 0.05, trim, bv=0.01 if hi else 0, skip=('+x',))
    m.uvrect([(x0 + 0.121, sy0 + 0.05, sz0), (x0 + 0.121, sy1 - 0.05, sz0), (x0 + 0.121, sy1 - 0.05, sz1), (x0 + 0.121, sy0 + 0.05, sz1)], 'shopsigns',
             tuple(sign_rect(spec['shop'])), out=(1, 0, 0)) if False else None
    r = sign_rect(spec['shop'])
    # the board keeps the atlas aspect (8:1): centred, as wide as it can be
    bw = min(sy1 - sy0 - 0.1, (sz1 - sz0) * 8.0)
    bh = bw / 8.0
    yc, zc = (sy0 + sy1) / 2, (sz0 + sz1) / 2
    m.uvrect([(x0 + 0.121, yc - bw / 2, zc - bh / 2), (x0 + 0.121, yc + bw / 2, zc - bh / 2), (x0 + 0.121, yc + bw / 2, zc + bh / 2), (x0 + 0.121, yc - bw / 2, zc + bh / 2)], 'shopsigns', r, out=(1, 0, 0))
    # awning: sloped canvas, striped, with valence and frame arms
    if spec.get('awning'):
        az0, az1, ad = zt + 0.05, zt - 0.62, 1.25
        a0, a1 = spec['awning']
        ay0, ay1 = y0 + 0.4, y1 - 0.4
        nst = max(2, int((ay1 - ay0) / 0.3)) if hi else max(2, int((ay1 - ay0) / 1.2))
        for i in range(nst):
            ya, yb = ay0 + (ay1 - ay0) * i / nst, ay0 + (ay1 - ay0) * (i + 1) / nst
            mt = a0 if i % 2 == 0 else a1
            m.face([(x0 + 0.1, yb, az0), (x0 + 0.1, ya, az0), (x0 + ad, ya, az1), (x0 + ad, yb, az1)], mt, out=(0.3, 0, 1))                      # top
            m.face([(x0 + 0.1, ya, az0 - 0.02), (x0 + 0.1, yb, az0 - 0.02), (x0 + ad, yb, az1 - 0.02), (x0 + ad, ya, az1 - 0.02)], mt, out=(-0.3, 0, -1))  # underside
            m.face([(x0 + ad, yb, az1), (x0 + ad, ya, az1), (x0 + ad + 0.03, ya, az1 - 0.3), (x0 + ad + 0.03, yb, az1 - 0.3)], mt, out=(1, 0, 0))      # valence
        if hi:
            for yy in (ay0, ay1):
                m.tube([(x0 + 0.1, yy, az0 - 0.05), (x0 + ad, yy, az1 - 0.05)], 0.015, 'black_metal', seg=5)
            m.tube([(x0 + ad, ay0, az1 - 0.03), (x0 + ad, ay1, az1 - 0.03)], 0.012, 'black_metal', seg=5)
    return dict(door=dpos, zt=zt, sz1=sz1)


def cornice(m, spec, hi, x0, y0, y1, ztop):
    trim, wall = spec['trim'], spec['wall']
    if hi:
        m.box(x0 - 0.02, y0 - 0.12, ztop - 0.9, x0 + 0.12, y1 + 0.12, ztop - 0.45, trim, bv=0.01)          # frieze
        m.box(x0 - 0.02, y0 - 0.2, ztop - 0.45, x0 + 0.3, y1 + 0.2, ztop - 0.3, trim, bv=0.012)
        n = int((y1 - y0) / 0.55)
        for i in range(n + 1):                                                                            # brackets
            yy = y0 + (y1 - y0) * i / n
            m.box(x0 + 0.05, yy - 0.06, ztop - 0.45, x0 + 0.4, yy + 0.06, ztop - 0.2, trim, bv=0.008)
        m.box(x0 - 0.02, y0 - 0.25, ztop - 0.2, x0 + 0.5, y1 + 0.25, ztop, trim, bv=0.012)                  # cap
        m.box(x0 - 0.0, y0 - 0.25, ztop, x0 + 0.1, y1 + 0.25, ztop + 0.55, wall if spec['style'] != 'clap' else trim, bv=0.008)   # parapet
        m.box(x0 - 0.04, y0 - 0.3, ztop + 0.55, x0 + 0.16, y1 + 0.3, ztop + 0.62, 'steel', bv=0.008)       # coping
    else:
        m.box(x0 - 0.02, y0 - 0.25, ztop - 0.9, x0 + 0.5, y1 + 0.25, ztop, trim)
        m.box(x0 - 0.0, y0 - 0.25, ztop, x0 + 0.1, y1 + 0.25, ztop + 0.6, wall)


def fire_escape(m, hi, x0, yc, z_levels):
    """Black iron platforms at each upper floor, a stair between them, a drop ladder."""
    mat = 'black_metal'
    pw, pd = 2.0, 1.0
    for z in z_levels:
        m.box(x0, yc - pw / 2, z - 0.06, x0 + pd, yc + pw / 2, z, mat, bv=0.004 if hi else 0)
        if hi:
            for k in range(1, 14):                                                      # grating slots
                m.box(x0 + 0.05, yc - pw / 2 + k * pw / 14, z + 0.001, x0 + pd - 0.05, yc - pw / 2 + k * pw / 14 + 0.012, z + 0.012, 'steel')
        for (ax, ay, bx, by) in ((x0 + pd, yc - pw / 2, x0 + pd, yc + pw / 2), (x0, yc - pw / 2, x0 + pd, yc - pw / 2), (x0, yc + pw / 2, x0 + pd, yc + pw / 2)):
            m.tube([(ax, ay, z + 1.0), (bx, by, z + 1.0)], 0.02, mat, seg=5 if hi else 3)
            if hi:
                n = int(max(abs(bx - ax), abs(by - ay)) / 0.14)
                for k in range(n + 1):
                    t = k / n
                    m.tube([(ax + (bx - ax) * t, ay + (by - ay) * t, z), (ax + (bx - ax) * t, ay + (by - ay) * t, z + 1.0)], 0.008, mat, seg=4, caps=False)
        for (yy) in (yc - pw / 2, yc + pw / 2):
            m.tube([(x0 + pd, yy, z - 0.06), (x0, yy, z - 0.5)], 0.015, mat, seg=4 if hi else 3)                  # brackets back to the wall
    for i, (z0, z1) in enumerate(zip(z_levels[:-1], z_levels[1:])):                          # steep stairs outside the platforms, alternating direction
        sg = 1 if i % 2 == 0 else -1
        ya, yb = yc - sg * pw / 2, yc + sg * pw / 2
        for xx in (x0 + pd + 0.1, x0 + pd + 0.75):
            m.tube([(xx, ya, z1 - 0.06), (xx, yb, z0 - 0.06)], 0.02, mat, seg=5 if hi else 3)
            m.tube([(xx, ya, z1 + 0.95), (xx, yb, z0 + 0.95)], 0.016, mat, seg=4 if hi else 3)
        if hi:
            for k in range(11):
                t = (k + 0.5) / 11
                yy = ya + (yb - ya) * t
                zz = z1 - 0.06 + (z0 - z1) * t
                m.box(x0 + pd + 0.1, yy - 0.12, zz, x0 + pd + 0.75, yy + 0.12, zz + 0.025, mat)
    z0 = z_levels[0]
    for yy in (yc - 0.2, yc + 0.2):                                                         # drop ladder from the lowest platform
        m.tube([(x0 + pd - 0.05, yy, z0 - 0.06), (x0 + pd + 0.3, yy, 2.4)], 0.015, mat, seg=4)
    if hi:
        for k in range(8):
            z = 2.5 + k * 0.4
            if z < z0 - 0.1:
                t = (z - 2.4) / (z0 - 0.06 - 2.4)
                xx = x0 + pd + 0.3 - 0.35 * t
                m.tube([(xx, yc - 0.2, z), (xx, yc + 0.2, z)], 0.01, mat, seg=4)


def make_building(spec, lod):
    seed = spec['seed']
    rnd = random.Random(seed)
    hi = lod == 0
    W, D, n = spec['W'], spec['D'], spec['floors']
    zf = [0.0, FH0] + [FH0 + FH * i for i in range(1, n)]
    H = FH0 + FH * (n - 1)
    ztop = H + 0.0
    m = MB(f"Bld_{spec['name']}_LOD{lod}", seed)
    m.tone = tone_fn(seed)
    wall, trim = spec['wall'], spec['trim']
    y0, y1 = -W / 2, W / 2
    step = 1.0 if hi else 2.4
    # --- openings of the front wall
    openings = []
    bays = max(2, int(round(W / 2.9)))
    bw = W / bays
    wins = []
    for fl in range(1, n):
        zc = zf[fl] + 1.45
        for b in range(bays):
            yc = y0 + bw * (b + 0.5)
            wins.append((yc, zc))
            openings.append((yc - 0.5, yc + 0.5, zc - 0.85, zc + 0.85))
    # ground floor openings: the shopfront is built as a whole, the wall around it from piers and the band above
    shop_y0, shop_y1 = y0 + 0.0, y1 - 0.0
    zsh = 3.15
    # --- front wall
    Facade(m, 0.0, y0, y1, 0.0, ztop, wall, openings + [(y0 + 0.35, y1 - 0.35, 0.0, zsh)], step, hi)
    # plinth
    m.box(-0.0, y0 - 0.02, 0.0, 0.08, y1 + 0.02, 0.5, 'concrete', bv=0.015 if hi else 0, skip=('-x',))
    # --- shopfront and its sign
    rnd2 = random.Random(seed + 11)
    info = shopfront(m, spec, hi, 0.0, y0, y1, rnd2)
    # string course above the shop sign and between floors
    for fl in range(1, n + 1):
        zc = zf[fl] if fl < n else None
        if zc is not None and hi:
            m.box(-0.0, y0 - 0.05, zc - 0.12, 0.1, y1 + 0.05, zc + 0.04, trim if spec['style'] != 'brick' else 'concrete', bv=0.01)
    for (yc, zc) in wins:
        window_upper(m, yc, zc, 1.0, 1.7, 0.0, hi, spec, rnd2, False)
    cornice(m, spec, hi, 0.0, y0, y1, ztop + 0.0)
    # corner pilasters (brick buildings) / corner boards (clapboard)
    pw = 0.32 if spec['style'] == 'brick' else 0.14
    for ys in (y0, y1 - pw):
        m.box(0.0, ys, 0.5, 0.06, ys + pw, ztop, spec['wall'] if spec['style'] == 'brick' else trim, bv=0.01 if hi else 0)
    # --- side walls, back wall, roof
    sstep = 2.2 if hi else 4.0
    for (ys, nrm, flip) in ((y0, (0, -1, 0), 1), (y1, (0, 1, 0), -1)):
        side_open = []
        for fl in range(1, n):
            for k in range(max(1, int(D / 7))):
                xc = -2.5 - k * 6.5
                if xc - 0.5 > -D:
                    side_open.append((xc - 0.5, xc + 0.5, zf[fl] + 0.6, zf[fl] + 2.2))
        xs = sorted({0.0, -D} | {v for (a, b, c, d) in side_open for v in (a, b)})
        zs = sorted({0.0, ztop + 0.6} | {v for (a, b, c, d) in side_open for v in (c, d)})
        xs = [v for i in range(len(xs) - 1) for v in cells(xs[i], xs[i + 1], sstep)[:-1]] + [xs[-1]]
        zs = [v for i in range(len(zs) - 1) for v in cells(zs[i], zs[i + 1], sstep)[:-1]] + [zs[-1]]
        sm = 'brick_old' if spec['style'] == 'brick' else wall
        for xa, xb in zip(xs[:-1], xs[1:]):
            for za, zb in zip(zs[:-1], zs[1:]):
                if any(a < (xa + xb) / 2 < b and c < (za + zb) / 2 < d for (a, b, c, d) in side_open):
                    continue
                pts = [(xa, ys, za), (xb, ys, za), (xb, ys, zb), (xa, ys, zb)]
                m.face(pts, sm, out=nrm)
        for (a, b, c, d) in side_open:
            m.quad((a, ys, c), (b, ys, c), (b, ys, d), (a, ys, d), 'glass_dirty', out=nrm)
            m.box(a - 0.05, ys - 0.03 if ys < 0 else ys, c - 0.07, b + 0.05, ys if ys < 0 else ys + 0.03, c, trim) if hi else None
    m.face([(-D, y1, 0), (-D, y0, 0), (-D, y0, ztop + 0.6), (-D, y1, ztop + 0.6)], 'brick_old' if spec['style'] == 'brick' else wall, out=(-1, 0, 0))
    # roof
    if spec['roof'] == 'flat':
        m.face([(0.0, y0, ztop + 0.55), (0.0, y1, ztop + 0.55), (-D, y1, ztop + 0.55), (-D, y0, ztop + 0.55)], 'tar', out=(0, 0, 1))
        if hi:
            r2 = random.Random(seed + 5)
            for _ in range(r2.randint(2, 4)):
                x, y = r2.uniform(-D + 2, -2), r2.uniform(y0 + 1, y1 - 1)
                kind = r2.choice(['vent', 'box', 'chimney'])
                zr = ztop + 0.55
                if kind == 'vent':
                    m.cyl(x, y, zr, zr + 0.5, 0.15, 'steel', seg=10)
                    m.cyl(x, y, zr + 0.5, zr + 0.62, 0.22, 'steel', seg=10, r1=0.05)
                elif kind == 'box':
                    m.box(x - 0.6, y - 0.5, zr, x + 0.6, y + 0.5, zr + 0.8, 'paint_grey', bv=0.02)
                else:
                    m.box(x - 0.4, y - 0.4, zr, x + 0.4, y + 0.4, zr + 2.0, 'brick_old', bv=0.02)
                    m.box(x - 0.48, y - 0.48, zr + 2.0, x + 0.48, y + 0.48, zr + 2.12, 'concrete')
            if r2.random() < 0.6:                                                         # a 1980s TV aerial
                x, y = -D / 2, r2.uniform(y0 + 2, y1 - 2)
                zr = ztop + 0.55
                m.tube([(x, y, zr), (x, y, zr + 4.5)], 0.02, 'steel', seg=5)
                for i in range(5):
                    zz = zr + 2.2 + i * 0.5
                    m.tube([(x, y - (1.0 - i * 0.12), zz), (x, y + (1.0 - i * 0.12), zz)], 0.008, 'steel', seg=3)
    else:
        # pitched roof, ridge along Y at -D/2? ridge parallel to the street (along Y): two slopes front/back
        rz = 2.2
        zr0 = ztop + 0.55
        m.face([(0.12, y0 - 0.2, zr0), (0.12, y1 + 0.2, zr0), (-D / 2, y1 + 0.2, zr0 + rz), (-D / 2, y0 - 0.2, zr0 + rz)], 'slate', out=(0.5, 0, 1))
        m.face([(-D, y1 + 0.2, zr0), (-D, y0 - 0.2, zr0), (-D / 2, y0 - 0.2, zr0 + rz), (-D / 2, y1 + 0.2, zr0 + rz)], 'slate', out=(-0.5, 0, 1))
        m.face([(0.12, y0 - 0.2, zr0), (-D / 2, y0 - 0.2, zr0 + rz), (-D, y0 - 0.2, zr0)], wall, out=(0, -1, 0))
        m.face([(0.12, y1 + 0.2, zr0), (-D, y1 + 0.2, zr0), (-D / 2, y1 + 0.2, zr0 + rz)], wall, out=(0, 1, 0))
    # fire escape
    if spec.get('fire_escape') and n >= 2:
        fe_y = rnd.choice([-1, 1]) * (W / 2 - 2.6) if W > 9 else 0.0
        fe_y = (wins[0][0] if wins else 0.0)
        m.at(0.0, 0, 0)
        fire_escape(m, hi, 0.04, fe_y, [zf[fl] + 0.55 for fl in range(1, n)])
        m.pop()
    # gutters and downspouts
    if hi:
        for ys in (y0 + 0.12, y1 - 0.12):
            m.tube([(0.2, ys, ztop - 0.5), (0.2, ys, 0.3), (0.35, ys, 0.0)], 0.04, 'steel', seg=6)
    o = m.build(props={'front': '+X', 'width': W, 'depth': D, 'floors': n, 'height': ztop + 0.6, 'style': spec['style']})
    return o


def make_designs(count=36):
    """The building designs of the street: widths from a menu, wall/trim/awning/sign picked by seeded choice."""
    rnd = random.Random(1987)
    widths = [6.5, 7.5, 8.5, 9.5, 10.5, 12.0, 13.5, 15.0]
    styles = [('brick', ['brick_red', 'brick_brown', 'brick_buff', 'brick_old'], 'trim_white'), ('clap', ['clap_white', 'clap_cream', 'clap_blue', 'clap_sage', 'clap_yellow', 'clap_grey'], 'trim_white'),
              ('plaster', ['plaster_cream', 'plaster_sage', 'plaster_grey', 'plaster_rose', 'plaster_white'], 'trim_white')]
    awns = [('awn_red', 'awn_white'), ('awn_green', 'awn_cream'), ('awn_navy', 'awn_white'), ('awn_burg', 'awn_cream'), ('awn_gold', 'awn_white'), None, ('awn_green', 'awn_white'), ('awn_red', 'awn_cream')]
    out = []
    for i in range(count):
        st, walls, trim = styles[[0, 0, 1, 0, 2, 1, 0, 2, 0, 1][i % 10]]
        floors = rnd.choice([2, 2, 3, 3, 2]) if st != 'clap' else rnd.choice([2, 2, 3])
        out.append(dict(name=f'{i:02d}', seed=100 + i * 7, W=rnd.choice(widths), D=rnd.choice([16.0, 18.0, 20.0, 22.0]), floors=floors, wall=rnd.choice(walls), trim=trim, style=st,
                        roof='flat' if (st != 'clap' or rnd.random() < 0.5) else 'gable', shop=i % 32, awning=awns[(i * 3 + 1) % len(awns)], fire_escape=(st == 'brick' and floors == 3 and rnd.random() < 0.8),
                        bulk=rnd.choice(['brick_brown', 'wood_dark', 'brick_old'])))
    return out
