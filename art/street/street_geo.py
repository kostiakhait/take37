# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Road, kerb, gutter, sidewalk, marking and decal geometry of the main street (street runs along +X from L0 to L1, centre line y = 0).

Cross-section (metres): two 3.4 m lanes, two 2.4 m parking lanes, 0.4 m gutter pan, 0.2 m kerb 0.15 high, 3.3 m sidewalk, building line at |y| = 9.3.
Side streets: 10 m wide, kerb returns of 2.5 m radius, 2.5 m walks along them.
All meshes are cut into 100 m chunks (frustum culling) by Chunker; vertex tone carries wear (wheel tracks, patches, stains) so that no texture repeat shows.
"""
import math
import random

from mathutils import Vector as V

import kitlib as K
from kitlib import MB

L0, L1 = -40.0, 640.0
YK = 5.8            # kerb face
KW = 0.2
ZK = 0.15
BL = 9.3            # building line
LANE = 3.4
R = 2.5             # kerb return radius
SW = 10.0           # side street width
CROSS_L = [100.0, 200.0, 305.0, 410.0, 515.0]
CROSS_R = [200.0, 305.0, 410.0, 515.0]
SIDE_LEN = 44.0     # side street length beyond the main kerb (y = 5.8 .. 49.8)
GAS = (528.0, 596.0)   # right side lot between these x: no kerb or sidewalk (the gas station has its own aprons)
CHUNK = 100.0


class Chunker:
    def __init__(self, prefix, seed0=0):
        self.prefix, self.mbs, self.seed0 = prefix, {}, seed0

    def get(self, kind, x, tone=None):
        c = int((x - L0) // CHUNK)
        k = (kind, c)
        if k not in self.mbs:
            m = MB(f'{self.prefix}_{kind}_{c:02d}', seed=self.seed0 + c * 5 + len(self.mbs), uvshift=False)
            m.tone = tone
            self.mbs[k] = m
        return self.mbs[k]

    def build_all(self, coll, parent=None):
        out = []
        for (kind, c), m in sorted(self.mbs.items()):
            if not m.bm.faces:
                continue
            o = m.build(f'{self.prefix}_{kind}_{c:02d}', collection=coll, parent=parent)
            out.append(o)
        return out


def h2(a, b, s=0):
    return random.Random(int(a * 977 + b * 131 + s * 7919) & 0xffffff).random()


def road_tone(seed=0):
    def f(p):
        ay = abs(p.y)
        n = 0.82 + 0.34 * K.fbm(V((p.x * 0.18, p.y * 0.4, 0.0)), seed, 1.0)                 # mottled ageing
        lane_c = LANE / 2 if ay < LANE else (LANE + (YK - LANE) / 2)
        t1 = abs(ay - (lane_c - 0.82))                                                        # wheel tracks: rubbed smooth and darker with an oil line between
        t2 = abs(ay - (lane_c + 0.82))
        track = max(0.0, 1 - min(t1, t2) / 0.42) if ay < LANE else 0.0
        oil = max(0.0, 1 - abs(ay - lane_c) / 0.25) if ay < LANE else 0.0
        v = n * (1.0 - 0.14 * track - 0.12 * oil)
        v *= 1.0 - 0.18 * max(0.0, 1 - abs(ay - YK + 0.2) / 0.5)                           # gutter grime
        return (v * 0.98, v * 0.985, v * 1.02)
    return f


def sidewalk_tone(seed=0):
    def f(p):
        sx, sy = math.floor(p.x / 1.65), math.floor(p.y / 1.65)
        slab = 0.86 + 0.22 * h2(sx, sy, seed)
        n = 0.88 + 0.22 * K.fbm(V((p.x * 0.5, p.y * 0.5, 0)), seed, 1.0)
        edge = 1.0 - 0.15 * max(0.0, 1 - (abs(p.y) - YK - KW) / 0.4)                       # kerb-side grime
        v = slab * n * edge
        return (v, v * 0.99, v * 0.96)
    return f


def sweep(m, path, prof, mat, flip_out=False):
    """Extrude a solid profile [(offset to the left of travel, z), ...] (CCW) along a polyline."""
    for a, b in zip(path[:-1], path[1:]):
        t = V((b[0] - a[0], b[1] - a[1], 0))
        if t.length < 1e-6:
            continue
        t.normalize()
        n = V((-t.y, t.x, 0))
        for i in range(len(prof)):
            (o0, z0), (o1, z1) = prof[i], prof[(i + 1) % len(prof)]
            if abs(o0 - o1) < 1e-6 and abs(z0 - z1) < 1e-6:
                continue
            outv = n * (z1 - z0) + V((0, 0, -(o1 - o0)))
            P = [V((a[0], a[1], 0)) + n * o0 + V((0, 0, z0)), V((b[0], b[1], 0)) + n * o0 + V((0, 0, z0)), V((b[0], b[1], 0)) + n * o1 + V((0, 0, z1)), V((a[0], a[1], 0)) + n * o1 + V((0, 0, z1))]
            m.face(P, mat, out=outv)


KERB = [(0.0, 0.0), (KW, 0.0), (KW, ZK), (0.035, ZK), (0.0, ZK - 0.035)]


def arc(c, r, a0, a1, n):
    return [(c[0] + r * math.cos(a0 + (a1 - a0) * i / n), c[1] + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def mirror(path):
    return [(x, -y) for (x, y) in reversed(path)]


def kerb_pieces(cross, gas=None):
    """Kerb centre-line pieces for the left side (y > 0); the right side is the mirror image. Each piece travels with the sidewalk on its left."""
    pieces = []
    xs = [L0]
    cur = L0
    for xc in cross:
        pieces.append([(cur, YK), (xc - SW / 2 - R, YK)])
        pieces.append(arc((xc - SW / 2 - R, YK + R), R, -math.pi / 2, 0, 8))                    # west corner, then the west leg
        pieces.append([(xc - SW / 2, YK + R), (xc - SW / 2, YK + SIDE_LEN)])
        pieces.append([(xc + SW / 2, YK + SIDE_LEN), (xc + SW / 2, YK + R)])                    # east leg, then the east corner
        pieces.append(arc((xc + SW / 2 + R, YK + R), R, math.pi, 1.5 * math.pi, 8))
        cur = xc + SW / 2 + R
    pieces.append([(cur, YK), (L1, YK)])
    return pieces


def build_road(CH, cross_l, cross_r, gas, props_out):
    """Fills the Chunker with road, gutters, kerbs, sidewalks, markings. gas = (x0, x1) of the lot on the right side."""
    rt = road_tone(1)
    # ---- main asphalt in 1.5 x ~0.73 m cells
    step = 1.5
    nx = int((L1 - L0) / step)
    for ix in range(nx):
        x = L0 + ix * step
        m = CH.get('asphalt', x + 1, rt)
        m.grid((x, -YK, 0), (step, 0, 0), (0, YK * 2 / 16, 0), 1, 16, 'asphalt', out=(0, 0, 1))
    # ---- cross streets and their kerb-return fillets
    for side, cross in ((1, cross_l), (-1, cross_r)):
        for xc in cross:
            ys = YK
            n_y = int(SIDE_LEN / 1.5)
            for iy in range(n_y):
                for ix in range(4):
                    x0 = xc - SW / 2 + ix * SW / 4
                    m = CH.get('asphalt', xc, rt)
                    y0 = side * (ys + iy * 1.5)
                    pts = [(x0, y0), (x0 + SW / 4, y0), (x0 + SW / 4, y0 + side * 1.5), (x0, y0 + side * 1.5)]
                    m.face([(p[0], p[1], 0) for p in pts], 'asphalt', out=(0, 0, 1))
            for sx in (-1, 1):                                                                    # fillets between main road and side street
                cx = xc + sx * (SW / 2 + R)
                cy = side * (YK + R)
                kx, ky = xc + sx * SW / 2, side * YK
                a0 = (math.atan2(side * (YK - cy) * side, cx * 0 + (cx - cx) + 0)) if False else None
                pts = []
                for i in range(9):
                    t = i / 8
                    if sx == -1:      # corner at xc - 5: arc from (kx - R, ky) to (kx, ky + side * R)
                        ang = -math.pi / 2 + t * math.pi / 2
                        pts.append((cx + R * math.cos(ang), cy + side * R * math.sin(ang)))
                    else:
                        ang = math.pi + t * math.pi / 2
                        pts.append((cx + R * math.cos(ang), cy + side * R * math.sin(ang)))
                m = CH.get('asphalt', xc, rt)
                for p, q in zip(pts[:-1], pts[1:]):
                    m.face([(kx, ky, 0), (p[0], p[1], 0), (q[0], q[1], 0)], 'asphalt', out=(0, 0, 1))
    # ---- gutter pans (concrete, 0.4 m) along the main kerb, cut at side streets and the gas lot
    def runs(cross):
        out, cur = [], L0
        for xc in cross:
            out.append((cur, xc - SW / 2 - R))
            cur = xc + SW / 2 + R
        out.append((cur, L1))
        return out
    for side, cross in ((1, cross_l), (-1, cross_r)):
        for (a, b) in runs(cross):
            if side == -1 and gas and a < gas[1] and b > gas[0]:
                segs = [(a, gas[0]), (gas[1], b)]
            else:
                segs = [(a, b)]
            for (sa, sb) in segs:
                if sb - sa < 0.5:
                    continue
                n = max(1, int((sb - sa) / 2.0))
                for i in range(n):
                    xa, xb = sa + (sb - sa) * i / n, sa + (sb - sa) * (i + 1) / n
                    m = CH.get('kerb', xa)
                    m.tone = lambda p: (0.8 + 0.2 * K.fbm(p * 0.7, 3, 1.0) * 1.0,) * 3
                    m.face([(xa, side * (YK - 0.4), 0.002), (xb, side * (YK - 0.4), 0.002), (xb, side * YK, 0.002), (xa, side * YK, 0.002)], 'kerb', out=(0, 0, 1))
    # ---- kerbs
    for side in (1, -1):
        cross = cross_l if side == 1 else cross_r
        pcs = kerb_pieces(cross)
        for pc in pcs:
            pcs_ = pc if side == 1 else mirror(pc)
            if side == -1 and gas:
                # clip straight pieces to leave the gas lot open
                xs = [p[0] for p in pcs_]
                if min(xs) < gas[1] and max(xs) > gas[0] and abs(pcs_[0][1] - pcs_[-1][1]) < 1e-6:
                    a, b = min(xs), max(xs)
                    parts = []
                    if a < gas[0]:
                        parts.append([(a, pcs_[0][1]), (gas[0], pcs_[0][1])] if pcs_[0][0] < pcs_[-1][0] else [(gas[0], pcs_[0][1]), (a, pcs_[0][1])])
                    if b > gas[1]:
                        parts.append([(gas[1], pcs_[0][1]), (b, pcs_[0][1])] if pcs_[0][0] < pcs_[-1][0] else [(b, pcs_[0][1]), (gas[1], pcs_[0][1])])
                    for pp in parts:
                        sweep(CH.get('kerb', pp[0][0]), pp, KERB, 'kerb')
                    continue
            # subdivide long pieces so chunks stay local
            pts = pcs_
            out = [pts[0]]
            for a, b in zip(pts[:-1], pts[1:]):
                L = math.hypot(b[0] - a[0], b[1] - a[1])
                k = max(1, int(L / 8.0))
                for i in range(1, k + 1):
                    out.append((a[0] + (b[0] - a[0]) * i / k, a[1] + (b[1] - a[1]) * i / k))
            for a, b in zip(out[:-1], out[1:]):
                m = CH.get('kerb', (a[0] + b[0]) / 2)
                m.tone = lambda p: (0.78 + 0.28 * K.fbm(p * 0.6, 5, 1.0),) * 3
                sweep(m, [a, b], KERB, 'kerb')
    # ---- sidewalks: slabs of 1.65 m aligned to a global grid; per-slab tone and random 90 degree turns
    st = sidewalk_tone(2)
    sl = 1.65

    def slab_quad(m, x0, x1, y0, y1):
        # UV by global position, rotated by slab hash so neighbouring slabs do not repeat
        sx, sy = math.floor((x0 + x1) / 2 / sl), math.floor((y0 + y1) / 2 / sl)
        rot = int(h2(sx, sy, 9) * 4)
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        uvs = []
        for (px, py) in pts:
            u, v = (px - sx * sl) / sl, (py - sy * sl) / sl
            for _ in range(rot):
                u, v = 1 - v, u
            uvs.append((u + 0.0, v + 0.0))
        return m.face([(p[0], p[1], ZK) for p in pts], 'sidewalk', out=(0, 0, 1), uv=uvs)

    def rect_slabs(x0, x1, y0, y1, nm=None):
        xs = [x0] + [k * sl for k in range(int(math.floor(x0 / sl)) + 1, int(math.ceil(x1 / sl))) if x0 < k * sl < x1] + [x1]
        ys = [y0] + [k * sl for k in range(int(math.floor(y0 / sl)) + 1, int(math.ceil(y1 / sl))) if y0 < k * sl < y1] + [y1]
        for xa, xb in zip(xs[:-1], xs[1:]):
            for ya, yb in zip(ys[:-1], ys[1:]):
                if xb - xa < 1e-4 or yb - ya < 1e-4:
                    continue
                m = CH.get('sidewalk', (xa + xb) / 2, st)
                slab_quad(m, xa, xb, ya, yb)

    def lip(m, a, b, side):
        pass
    for side, cross in ((1, cross_l), (-1, cross_r)):
        yi, yo = sorted((side * (YK + KW), side * BL))
        for (a, b) in runs(cross):
            segs = [(a, b)]
            if side == -1 and gas and a < gas[1] and b > gas[0]:
                segs = [(a, gas[0] - 1.0), (gas[1] + 1.0, b)]
            for (sa, sb) in segs:
                if sb - sa > 0.3:
                    rect_slabs(sa, sb, yi, yo)
        for xc in cross:                                                                          # corner sectors and the walks along the side streets
            for sx in (-1, 1):
                cx = xc + sx * (SW / 2 + R)
                cy = side * (YK + R)
                m = CH.get('sidewalk', xc, st)
                for i in range(8):
                    if sx == -1:
                        a0, a1 = -math.pi / 2 + i * math.pi / 16, -math.pi / 2 + (i + 1) * math.pi / 16
                        p0, p1 = (cx + (R - KW) * math.cos(a0), cy + side * (R - KW) * math.sin(a0)), (cx + (R - KW) * math.cos(a1), cy + side * (R - KW) * math.sin(a1))
                    else:
                        a0, a1 = math.pi + i * math.pi / 16, math.pi + (i + 1) * math.pi / 16
                        p0, p1 = (cx + (R - KW) * math.cos(a0), cy + side * (R - KW) * math.sin(a0)), (cx + (R - KW) * math.cos(a1), cy + side * (R - KW) * math.sin(a1))
                    mm = CH.get('sidewalk', xc, st)
                    mm.face([(cx, cy, ZK), (p0[0], p0[1], ZK), (p1[0], p1[1], ZK)], 'sidewalk', out=(0, 0, 1),
                            uv=[(cx / sl, cy / sl), (p0[0] / sl, p0[1] / sl), (p1[0] / sl, p1[1] / sl)])
                # the walk along the leg: x in [xc - 7.5, xc - 5 - KW]
                if sx == -1:
                    rect_slabs(xc - SW / 2 - R, xc - SW / 2 - KW, *sorted((side * (YK + R), side * (YK + SIDE_LEN))))
                else:
                    rect_slabs(xc + SW / 2 + KW, xc + SW / 2 + R, *sorted((side * (YK + R), side * (YK + SIDE_LEN))))
                # filler between the sector's flat edge, the walk and the main walk
                # the main walk spans y in [YK + KW, BL]; the sector reaches y = YK + R: both are covered by the walk rectangles above (runs end at x = xc -+ (5 + R))
    # ---- kerb back faces are hidden by the walk; the walk's edge toward buildings is the building plinth
    return


def build_markings(CH, cross_l, cross_r, gas):
    rnd = random.Random(5)
    z = 0.004

    def strip(kind, x0, x1, y0, y1, mat, wear=1.0):
        m = CH.get(kind, (x0 + x1) / 2)
        L = max(abs(x1 - x0), abs(y1 - y0))
        w = min(abs(x1 - x0), abs(y1 - y0))
        horizontal = abs(x1 - x0) >= abs(y1 - y0)
        s = rnd.random()
        uv = [(s, 0), (s + L / 2.0, 0), (s + L / 2.0, w / 2.0), (s, w / 2.0)] if horizontal else [(0, s), (0, s + L / 2.0), (w / 2.0, s + L / 2.0), (w / 2.0, s)]
        if horizontal:
            m.face([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], mat, out=(0, 0, 1), uv=uv)
        else:
            m.face([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], mat, out=(0, 0, 1), uv=[(0, s), (w / 2.0, s), (w / 2.0, s + L / 2.0), (0, s + L / 2.0)])

    def clear_of_cross(x0, x1):
        for xc in sorted(set(cross_l + cross_r)):
            if x1 > xc - SW / 2 - R - 12.5 and x0 < xc + SW / 2 + R + 12.5:
                return False
        return True
    # double yellow centre line, solid, broken only by the crosswalk bars (kept through intersections: the street is the through road)
    for i in range(int((L1 - L0) / 10)):
        x0 = L0 + i * 10
        for dy in (-0.14, 0.04):
            strip('line_y', x0, x0 + 10.0, dy, dy + 0.10, 'line_yellow')
    # parking T marks and lane edge dashes
    for side, cross in ((1, cross_l), (-1, cross_r)):
        x = L0 + 3
        while x < L1:
            if clear_of_cross(x - 0.1, x + 0.2) and not (gas and side == -1 and gas[0] - 4 < x < gas[1] + 4):
                yb = side * LANE
                strip('line_w', x, x + 0.12, min(yb, yb + side * 2.2), max(yb, yb + side * 2.2), 'line_white')       # stall ends: ticks across the parking lane
                strip('line_w', x - 0.0, x + 0.12, min(yb, yb + side * 0.05), max(yb, yb + side * 0.05), 'line_white') if False else None
            x += 6.6
        # parking lane boundary: long solid line with gaps at drives
        a = L0
        for xc in sorted(cross):
            strip('line_w', a, xc - SW / 2 - R - 1.0, min(side * LANE, side * LANE + side * 0.1), max(side * LANE, side * LANE + side * 0.1), 'line_white') if xc - SW / 2 - R - 1.0 > a else None
            a = xc + SW / 2 + R + 1.0
        strip('line_w', a, L1, min(side * LANE, side * LANE + side * 0.1), max(side * LANE, side * LANE + side * 0.1), 'line_white')
    # crosswalks (continental bars along the direction of traffic) on both sides of each crossing, and stop bars on the side streets
    allx = sorted(set(cross_l + cross_r))
    for xc in allx:
        for sx in (-1, 1):
            xcw = xc + sx * (SW / 2 + R + 1.6)
            for k in range(14):
                yy = -YK + 0.45 + k * 0.82
                strip('line_w', xcw - 1.2, xcw + 1.2, yy - 0.2, yy + 0.2, 'line_white')
        for side, cross in ((1, cross_l), (-1, cross_r)):
            if xc in cross:
                for sx in (-1, 1):                                                                # side-street stop bar on the lane that meets the main street, white 0.45 m
                    pass
                xs = xc + (0.1 if True else 0)
                # the lane entering the main street on the right of the side street's direction of travel
                ybar = side * (YK + 1.2)
                x0, x1 = (xc - SW / 2 + 0.2, xc) if side == 1 else (xc, xc + SW / 2 - 0.2)
                strip('line_w', x0, x1, min(ybar, ybar + side * 0.45), max(ybar, ybar + side * 0.45), 'line_white')
                for yy in range(0, 8):                                                              # dashed centre line of the side street
                    ya = side * (YK + 3 + yy * 5.0)
                    strip('line_y', xc - 0.05, xc + 0.05, min(ya, ya + side * 2.5), max(ya, ya + side * 2.5), 'line_yellow')


def build_decals(CH, cross_l, cross_r, gas):
    """Patches, cracks, oil stains, manholes, drain grates, skid marks in the atlas (decals_c.png, 4 x 4 cells of 512 px)."""
    rnd = random.Random(77)
    z = 0.007

    def cell(i, inset=0.003):
        c, r = i % 4, i // 4
        return (c * 0.25 + inset, 1 - (r + 1) * 0.25 + inset, c * 0.25 + 0.25 - inset, 1 - r * 0.25 - inset)

    def quad(x, y, w, h, ang, ci, zz=z, tone=None):
        m = CH.get('decal', x)
        r = cell(ci)
        ca, sa = math.cos(ang), math.sin(ang)
        pts = []
        for (dx, dy) in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
            pts.append((x + dx * ca - dy * sa, y + dx * sa + dy * ca, zz))
        m.face(pts, 'decals', out=(0, 0, 1), uv=[(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])])
    x = L0 + 4
    n_patch = 0
    while x < L1 - 4:
        # tar patches and cracks across the lanes
        yy = rnd.choice([-2.9, -1.6, -0.6, 0.7, 1.9, 3.0, -4.4, 4.5])
        k = rnd.random()
        if k < 0.28:
            quad(x, yy, rnd.uniform(1.4, 3.2), rnd.uniform(0.9, 1.9), rnd.uniform(-0.05, 0.05), 4, z)
            n_patch += 1
        elif k < 0.40:
            quad(x, rnd.choice([-1.0, 1.2]), rnd.uniform(0.7, 0.9), rnd.uniform(5.0, 9.0), math.pi / 2, 10, z)       # utility trench across the lane
        elif k < 0.62:
            quad(x, yy, rnd.uniform(2.5, 4.0), rnd.uniform(2.5, 4.0), rnd.uniform(0, 6.28), rnd.choice([2, 3, 8]), z + 0.001)
        elif k < 0.80:
            quad(x, yy, rnd.uniform(1.5, 2.8), rnd.uniform(1.5, 2.8), rnd.uniform(0, 6.28), rnd.choice([0, 1, 9]), z + 0.001)
        else:
            quad(x, rnd.choice([-2.0, 1.8]), rnd.uniform(1.0, 1.4), rnd.uniform(5, 8), rnd.uniform(-0.08, 0.08), 7, z + 0.001)
        x += rnd.uniform(5, 14)
    # oil drips in the parking lanes (where cars stand)
    x = L0 + 8
    while x < L1:
        for side in (1, -1):
            if rnd.random() < 0.45:
                quad(x + rnd.uniform(-1, 1), side * rnd.uniform(4.0, 5.0), rnd.uniform(0.7, 1.3), rnd.uniform(0.7, 1.3), rnd.uniform(0, 6.28), rnd.choice([0, 1, 9]), z + 0.002)
        x += 6.6
    # manholes: on the centre of the right and left lanes, every ~55 m
    x = L0 + 31
    while x < L1:
        quad(x, rnd.choice([-1.75, 1.75]) + rnd.uniform(-0.3, 0.3), 0.78, 0.78, rnd.uniform(0, 6.28), 5, 0.012)
        x += rnd.uniform(42, 70)
    # storm-drain inlets in the gutters, just before every crossing (downhill side) and mid-block
    for side, cross in ((1, cross_l), (-1, cross_r)):
        for xc in cross:
            for sx in (-1, 1):
                xx = xc + sx * (SW / 2 + R + 4.2)
                quad(xx, side * (YK - 0.3), 1.0, 0.5, 0.0, 6, 0.01) if not (gas and side == -1 and gas[0] - 1 < xx < gas[1] + 1) else None
        x = L0 + 50
        while x < L1:
            if not (gas and side == -1 and gas[0] - 1 < x < gas[1] + 1) and all(abs(x - xc) > 14 for xc in cross):
                quad(x, side * (YK - 0.3), 1.0, 0.5, 0.0, 6, 0.01)
            x += 62
    # crossings: heavier wear and skid marks at the stop line zones
    for xc in sorted(set(cross_l + cross_r)):
        for sx in (-1, 1):
            quad(xc + sx * 3.5, rnd.choice([-1.8, 1.8]), 1.0, rnd.uniform(5, 7), 0.0, 7, z + 0.001)
