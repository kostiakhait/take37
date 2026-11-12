# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Street wear and small things for TAKE 37: litter, leaves on road and walk, puddles, sidewalk cracks and utility lids, service drops and a second wire span.
Uses its own random stream (seed 1987 + 5), so the layout of the rest of the street is unchanged. Everything is a flat decal quad (alpha-blended, 5-12 mm above the surface) in 100 m chunks.
Atlases: litter_c.png (4 x 4), puddle_c.png (2 x 2), decals_c.png (road decals, cracks, lids); all drawn in textures_detail.py / textures_prep.py.
"""
import math
import random

import street_geo as G
import kitlib as K
from kitlib import MB

LIT = 'litter'


def cell4(i, e=0.003):
    c, r = i % 4, i // 4
    return (c / 4 + e, 1 - (r + 1) / 4 + e, (c + 1) / 4 - e, 1 - r / 4 - e)


def cell2(i, e=0.004):
    c, r = i % 2, i // 2
    return (c / 2 + e, 1 - (r + 1) / 2 + e, (c + 1) / 2 - e, 1 - r / 2 - e)


class Decor:
    def __init__(self, coll, parent):
        self.coll, self.parent = coll, parent
        self.mbs = {}

    def mb(self, x, kind):
        c = int((x - G.L0) // G.CHUNK)
        k = (kind, c)
        if k not in self.mbs:
            m = MB(f'Decor_{kind}_{c:02d}', seed=c + 400, uvshift=False)
            m.tone = lambda p: (1, 1, 1)
            self.mbs[k] = m
        return self.mbs[k]

    def quad(self, x, y, z, w, h, ang, mat, rect, kind, tone=1.0):
        m = self.mb(x, kind)
        ca, sa = math.cos(ang), math.sin(ang)
        pts = []
        for (dx, dy) in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
            pts.append((x + dx * ca - dy * sa, y + dx * sa + dy * ca, z))
        m.face(pts, mat, out=(0, 0, 1), uv=[(rect[0], rect[1]), (rect[2], rect[1]), (rect[2], rect[3]), (rect[0], rect[3])], color=lambda p: (tone, tone, tone))

    def build(self):
        out = []
        for (kind, c), m in sorted(self.mbs.items()):
            if m.bm.faces:
                o = m.build(f'Decor_{kind}_{c:02d}', collection=self.coll, parent=self.parent)
                o['static'] = 1
                out.append(o)
        return out


def add_decor(coll, parent, gas, tree_x, bin_x):
    """tree_x: {side: [x]} of tree pits; bin_x: [(x, side)] of bins and trash. Returns the objects."""
    rnd = random.Random(1987 + 5)
    D = Decor(coll, parent)
    zs = G.ZK + 0.006
    walk0, walk1 = G.YK + G.KW + 0.25, G.BL - 0.25

    def in_gas(x, side):
        return gas and side == -1 and gas[0] - 1 < x < gas[1] + 1

    def at_cross(x):
        for xc in sorted(set(G.CROSS_L + G.CROSS_R)):
            if abs(x - xc) < G.SW / 2 + G.R + 0.5:
                return True
        return False
    n = {'lit': 0, 'leaf': 0, 'pud': 0, 'crack': 0, 'lid': 0}
    for side in (1, -1):
        # litter on the sidewalk: singles all along, clumps by bins and in the lee of the building line
        x = G.L0 + 3
        while x < G.L1 - 3:
            x += rnd.uniform(2.5, 8.0)
            if at_cross(x) or in_gas(x, side):
                continue
            y = side * rnd.choice([rnd.uniform(walk0, walk1), rnd.uniform(walk1 - 1.0, walk1), rnd.uniform(walk0, walk0 + 0.8)])
            ci = rnd.choice([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 4, 9])
            D.quad(x, y, zs, rnd.uniform(0.28, 0.5), rnd.uniform(0.28, 0.5), rnd.uniform(0, 6.28), LIT, cell4(ci), 'litter', rnd.uniform(0.85, 1.0))
            n['lit'] += 1
        # litter in the gutter and the kerbside parking lane
        x = G.L0 + 5
        while x < G.L1 - 5:
            x += rnd.uniform(6, 16)
            if in_gas(x, side):
                continue
            D.quad(x, side * rnd.uniform(5.35, 5.78), 0.012, rnd.uniform(0.3, 0.5), rnd.uniform(0.3, 0.5), rnd.uniform(0, 6.28), LIT, cell4(rnd.choice([0, 1, 3, 4, 6, 9, 10, 11])), 'litter')
            n['lit'] += 1
        # autumn leaves: gutter drifts and sidewalk piles, denser near the trees
        for tx in tree_x[side]:
            for _ in range(rnd.randint(4, 8)):
                x = tx + rnd.gauss(0, 2.4)
                y = side * rnd.choice([rnd.uniform(5.3, 5.8), rnd.uniform(6.1, 8.8), rnd.uniform(4.0, 5.3)])
                zz = 0.012 if abs(y) < 5.9 else zs + 0.001
                D.quad(x, y, zz, rnd.uniform(0.6, 1.1), rnd.uniform(0.6, 1.1), rnd.uniform(0, 6.28), LIT, cell4(rnd.choice([12, 13, 14, 15])), 'leaf')
                n['leaf'] += 1
        for (bx, bs) in bin_x:
            if bs != side:
                continue
            for _ in range(2):
                D.quad(bx + rnd.gauss(0, 0.5), side * rnd.uniform(6.2, 7.4), zs + 0.002, rnd.uniform(0.3, 0.5), rnd.uniform(0.3, 0.5), rnd.uniform(0, 6.28), LIT, cell4(rnd.choice([0, 1, 2, 3, 4, 5, 6, 10, 11])), 'litter')
                n['lit'] += 1
        # puddles: gutter (the low line along the kerb) and the parking lane edge, after rain
        x = G.L0 + 12
        while x < G.L1 - 8:
            x += rnd.uniform(14, 40)
            if at_cross(x) or in_gas(x, side):
                continue
            w = rnd.uniform(1.6, 3.6)
            D.quad(x, side * rnd.uniform(5.2, 5.6), 0.0105, w, w * rnd.uniform(0.35, 0.6), rnd.uniform(-0.15, 0.15), 'puddle', cell2(rnd.randrange(4)), 'puddle')
            n['pud'] += 1
        # sidewalk cracks, heaved slab edges and utility lids (coal hole, water valve, cable pull box)
        x = G.L0 + 4
        while x < G.L1 - 4:
            x += rnd.uniform(5, 15)
            if at_cross(x) or in_gas(x, side):
                continue
            D.quad(x, side * rnd.uniform(walk0 + 0.3, walk1 - 0.3), zs + 0.001, rnd.uniform(1.4, 2.4), rnd.uniform(1.4, 2.4), rnd.uniform(0, 6.28), 'decals', _dc(rnd.choice([2, 3, 8])), 'crack')
            n['crack'] += 1
        x = G.L0 + 20
        while x < G.L1 - 10:
            x += rnd.uniform(35, 80)
            if at_cross(x) or in_gas(x, side):
                continue
            D.quad(x, side * rnd.uniform(6.4, 8.0), zs + 0.002, 0.42, 0.42, rnd.uniform(0, 6.28), 'decals', _dc(5), 'lid')
            n['lid'] += 1
    # puddles in the roadway low points near the crowns, and a few on the road itself
    x = G.L0 + 30
    while x < G.L1 - 10:
        x += rnd.uniform(60, 120)
        if at_cross(x):
            continue
        w = rnd.uniform(2.0, 4.0)
        D.quad(x, rnd.choice([-3.8, 3.9, -2.2]), 0.0112, w, w * 0.5, rnd.uniform(-0.2, 0.2), 'puddle', cell2(rnd.randrange(4)), 'puddle')
        n['pud'] += 1
    objs = D.build()
    return objs, n


def _dc(i, inset=0.003):
    c, r = i % 4, i // 4
    return (c * 0.25 + inset, 1 - (r + 1) * 0.25 + inset, c * 0.25 + 0.25 - inset, 1 - r * 0.25 - inset)


def add_wires(wm, pole_x, x0=6.75):
    """Extra wires: a lower telephone/cable pair along the poles, and service drops from each pole to the building line on the near side."""
    rnd = random.Random(1987 + 6)
    for xa, xb in zip(pole_x[:-1], pole_x[1:]):
        if xb - xa > 60:
            continue
        for (yo, zo) in ((-0.9, 8.05), (0.9, 8.05)):                  # telephone and cable TV pair, tighter sag
            pts = []
            for i in range(9):
                t = i / 8
                pts.append((xa + (xb - xa) * t, x0 + yo, zo - 0.3 * 4 * t * (1 - t)))
            wm.tube(pts, 0.007, 'cable', seg=4, caps=False)
    for xp in pole_x:                                                  # service drops across the sidewalk to the front of the nearest building
        for k in range(2):
            xt = xp + rnd.uniform(-9, 9)
            pts = []
            for i in range(7):
                t = i / 6
                pts.append((xp + (xt - xp) * t, x0 + (G.BL - 0.5 - x0) * t, 9.2 - (9.2 - 6.2) * t - 0.35 * 4 * t * (1 - t)))
            wm.tube(pts, 0.006, 'cable', seg=4, caps=False)
