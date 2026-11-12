# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Reusable detailed parts for the tanker (inside Blender): bolts, welds, perforated plates, channels, capsules, leaf springs, straps, grilles, hose runs. All append to a tkit.Mesh."""
import math

import bmesh
from mathutils import Matrix, Vector

V3 = Vector
X, Y, Z = V3((1, 0, 0)), V3((0, 1, 0)), V3((0, 0, 1))


def frame_of(d, up_hint=Z):
    """An orthonormal frame (ex, ey, ez) with ez = d (normalised)."""
    ez = V3(d).normalized()
    h = up_hint if abs(ez.dot(up_hint)) < 0.95 else X
    ex = h.cross(ez).normalized()
    ey = ez.cross(ex).normalized()
    return ex, ey, ez


def hex_bolt(m, c, nrm, r=0.011, h=0.008, kind='steel', washer=True):
    """A hex bolt head (6 sides, chamfer ring) standing on a surface at c with normal nrm."""
    ex, ey, ez = frame_of(nrm)
    c = V3(c)
    if washer:
        m.cyl(c, c + ez * 0.0015, r * 1.55, kind, seg=12)
        c = c + ez * 0.0015
    ring0 = [c + (ex * math.cos(math.pi / 3 * k) + ey * math.sin(math.pi / 3 * k)) * r for k in range(6)]
    ring1 = [p + ez * h for p in ring0]
    ring2 = [c + ez * (h + 0.0012) + (ex * math.cos(math.pi / 3 * k) + ey * math.sin(math.pi / 3 * k)) * r * 0.78 for k in range(6)]
    m.loft([ring0, ring1, ring2], kind, caps=True)


def rivet(m, c, nrm, r=0.006, kind='steel', seg=8):
    """A domed rivet head: rings up a dome closed by a tip vertex."""
    ex, ey, ez = frame_of(nrm)
    c = V3(c)
    rings = []
    for rr, hh in ((r, 0.0), (r * 0.98, r * 0.30), (r * 0.80, r * 0.62), (r * 0.45, r * 0.86)):
        rings.append([c + ez * hh + (ex * math.cos(2 * math.pi * k / seg) + ey * math.sin(2 * math.pi * k / seg)) * rr for k in range(seg)])
    vs = m.loft(rings, kind, caps=False)
    tip = m.bm.verts.new(c + ez * r * 0.95)
    for k in range(seg):
        m.face((vs[-1][k], vs[-1][(k + 1) % seg], tip), kind)


def capsule(m, p0, p1, r, kind, seg=32, dome=None, rings=4):
    """A cylinder with domed (elliptical) ends from p0 to p1; dome: depth of each end cap (default 0.4 r)."""
    p0, p1 = V3(p0), V3(p1)
    ex, ey, ez = frame_of(p1 - p0)
    L = (p1 - p0).length
    dome = 0.4 * r if dome is None else dome
    prof = []
    for k in range(rings + 1):                      # start cap, from the tip out to the barrel
        a = (math.pi / 2) * (1 - k / rings)
        prof.append((r * math.cos(a), -dome * math.sin(a)))
    prof.append((r, 0.0))
    prof.append((r, L))
    for k in range(rings + 1):
        a = (math.pi / 2) * (k / rings)
        prof.append((r * math.cos(a), L + dome * math.sin(a)))
    rows = []
    for rr, z in prof:
        if rr < 1e-6:
            rr = 1e-5
        rows.append([p0 + ez * z + (ex * math.cos(2 * math.pi * k / seg) + ey * math.sin(2 * math.pi * k / seg)) * rr for k in range(seg)])
    m.loft(rows, kind)


def band(m, c, axis, r, w, t, kind, seg=48, gap_deg=0.0):
    """A strap (a ring) round a cylinder: centre c, axis direction, inner radius r, width w, thickness t."""
    ex, ey, ez = frame_of(axis)
    c = V3(c)
    rows = []
    for rr in (r, r + t):
        for z in (-w / 2, w / 2):
            rows.append((rr, z))
    rings = [[c + ez * z + (ex * math.cos(2 * math.pi * k / seg) + ey * math.sin(2 * math.pi * k / seg)) * rr for k in range(seg)] for rr, z in
             ((r, -w / 2), (r + t, -w / 2), (r + t, w / 2), (r, w / 2))]
    m.loft(rings, kind, loop=True)


def perforated_plate(m, x0, x1, z0, z1, y, t, pitch, hole_r, kind, sides=12, side=1):
    """A vertical plate in the plane y (thickness t toward `side`), spanning x0..x1, z0..z1, with a row of round holes every `pitch` along x (centred in z): the faces round each hole
    are built as a ring of quads from the cell's rectangle to the circle, the hole's wall joins the two faces."""
    zc = 0.5 * (z0 + z1)
    hh = 0.5 * (z1 - z0)
    n = max(1, int((x1 - x0) / pitch))
    pitch = (x1 - x0) / n
    hw = pitch / 2

    def rect_pt(k):
        a = 2 * math.pi * (k + 0.5) / sides
        ca, sa = math.cos(a), math.sin(a)
        s = min(hw / max(abs(ca), 1e-9), hh / max(abs(sa), 1e-9))
        return ca * s, sa * s

    for i in range(n):
        cx = x0 + (i + 0.5) * pitch
        outer = [rect_pt(k) for k in range(sides)]
        for face_y, flip in ((y, False), (y + side * t, True)):
            o = [m.bm.verts.new((cx + u, face_y, zc + v)) for u, v in outer]
            ii = [m.bm.verts.new((cx + hole_r * math.cos(2 * math.pi * (k + 0.5) / sides), face_y, zc + hole_r * math.sin(2 * math.pi * (k + 0.5) / sides))) for k in range(sides)]
            for k in range(sides):
                quad = [o[k], o[(k + 1) % sides], ii[(k + 1) % sides], ii[k]]
                m.face(list(reversed(quad)) if flip != (side < 0) else quad, kind)
        a_ring = [m.bm.verts.new((cx + hole_r * math.cos(2 * math.pi * (k + 0.5) / sides), y, zc + hole_r * math.sin(2 * math.pi * (k + 0.5) / sides))) for k in range(sides)]
        b_ring = [m.bm.verts.new((cx + hole_r * math.cos(2 * math.pi * (k + 0.5) / sides), y + side * t, zc + hole_r * math.sin(2 * math.pi * (k + 0.5) / sides))) for k in range(sides)]
        for k in range(sides):
            quad = [a_ring[k], b_ring[k], b_ring[(k + 1) % sides], a_ring[(k + 1) % sides]]
            m.face(quad if side > 0 else list(reversed(quad)), kind)


def leaf_pack(m, c, length, width, leaves, thick, camber, kind='steel_dark', seg=10):
    """A semi-elliptic leaf spring along X: `leaves` leaves (each 11% shorter, stacked under the main one), each an arched strip; c = centre of the underside of the main leaf at the ends."""
    c = V3(c)
    for i in range(leaves):
        L = length * (1 - 0.115 * i)
        z0 = c.z - i * thick * 1.03
        rows = []
        for k in range(seg + 1):
            u = -1 + 2 * k / seg
            top = V3((c.x + u * L / 2, c.y, z0 + camber * (1 - u * u) + thick))
            bot = top - Z * thick
            rows.append([top - Y * width / 2, top + Y * width / 2, bot + Y * width / 2, bot - Y * width / 2])
        m.loft(rows, kind, caps=True)


def ibeam(m, p0, p1, h, w, tf, tw, kind, up=Z):
    """An I-beam along p0->p1: height h, flange width w, flange thickness tf, web thickness tw."""
    p0, p1 = V3(p0), V3(p1)
    ex, ey, ez = frame_of(p1 - p0, up)
    # section in the (ex, ey) plane, extruded along ez
    c = (p0 + p1) / 2
    L = (p1 - p0).length
    prof = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, -h / 2 + tf), (tw / 2, -h / 2 + tf), (tw / 2, h / 2 - tf), (w / 2, h / 2 - tf), (w / 2, h / 2), (-w / 2, h / 2),
            (-w / 2, h / 2 - tf), (-tw / 2, h / 2 - tf), (-tw / 2, -h / 2 + tf), (-w / 2, -h / 2 + tf)]
    r0 = [p0 + ex * a + ey * b for a, b in prof]
    r1 = [p1 + ex * a + ey * b for a, b in prof]
    m.loft([r0, r1], kind, caps=True)


def channel(m, p0, p1, h, w, t, kind, open_dir=1):
    """A C-channel along p0->p1 (x axis assumed), web in the plane facing -/+y, flanges toward `open_dir` in y; profile in (y, z): web at y=0, flanges to +open_dir*w."""
    p0, p1 = V3(p0), V3(p1)
    s = open_dir
    prof = [(0, -h / 2), (s * w, -h / 2), (s * w, -h / 2 + t), (s * t, -h / 2 + t), (s * t, h / 2 - t), (s * w, h / 2 - t), (s * w, h / 2), (0, h / 2)]
    r0 = [V3((p0.x, p0.y + a, p0.z + b)) for a, b in prof]
    r1 = [V3((p1.x, p1.y + a, p1.z + b)) for a, b in prof]
    m.loft([r0, r1], kind, caps=True)


def weld_bead(m, pts, r=0.0035, kind='steel_dark', seg=6):
    """A weld seam: a thin tube along the polyline, with ripples (a slightly wavy radius)."""
    path = [V3(p) for p in pts]
    # subdivide so that the ripple shows
    dense = []
    for a, b in zip(path, path[1:]):
        n = max(2, int((b - a).length / 0.008))
        for k in range(n):
            dense.append(a.lerp(b, k / n))
    dense.append(path[-1])
    radii = [r * (1.0 + 0.28 * math.sin(i * 1.9)) for i in range(len(dense))]
    m.tube(dense, radii, kind, seg=seg, cap=True)


def grille_bars(m, x, y0, y1, z0, z1, n, kind, depth=0.03, w=0.012):
    """Vertical bars of a grille in the plane x between y0..y1 and z0..z1."""
    for k in range(n):
        y = y0 + (y1 - y0) * (k + 0.5) / n
        m.rbox(V3((x, y, 0.5 * (z0 + z1))), (depth, w, z1 - z0), min(w, depth) * 0.4, kind)


def coil_hose(m, p0, p1, r_coil, r_wire, turns, kind, seg=6, sag=0.0):
    """A coiled air line (pigtail) along p0->p1: a helix of tube."""
    p0, p1 = V3(p0), V3(p1)
    ex, ey, ez = frame_of(p1 - p0)
    pts = []
    n = int(turns * 16)
    for i in range(n + 1):
        t = i / n
        a = 2 * math.pi * turns * t
        pts.append(p0.lerp(p1, t) + (ex * math.cos(a) + ey * math.sin(a)) * r_coil - Z * (sag * 4 * t * (1 - t)))
    m.tube(pts, r_wire, kind, seg=seg, cap=True)


def ring_torus(m, c, axis, R, r, kind, seg=32, tseg=8):
    ex, ey, ez = frame_of(axis)
    c = V3(c)
    rows = []
    for k in range(seg):
        a = 2 * math.pi * k / seg
        d = ex * math.cos(a) + ey * math.sin(a)
        rows.append([c + d * (R + r * math.cos(2 * math.pi * j / tseg)) + ez * (r * math.sin(2 * math.pi * j / tseg)) for j in range(tseg)])
    m.loft(rows, kind, loop=True)
