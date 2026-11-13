# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Crash kit: damaged variants of a finished car, driven by data (see crash_table.py); no hand sculpting.

World axes of the car: +X forward, +Y left, +Z up. The kit works on the finished car in Blender (the *_final.blend of cargen) and changes the meshes in place; the node names,
materials, vertex-colour layer, part split and pivots stay as in the clean car, so the glb drops into the game's damaged-car path unchanged.

Style: spectacular, not accurate (cartoon / hollywood): large readable deformations made of a few clean primitives, never noise, never sine ripples:

  Crush   a ram with a flat-topped lateral profile pushes the end of the car inward; the push dies out with depth into the car (monotone map, so surfaces never cross);
          the end also sags, bows and bends sideways (banana); a few STRAIGHT ridges (tent profile, slanted, parallel, not fanning from any point) buckle the skin.
  Roof    a rollover crushes the greenhouse down (uniform compression above the belt line), dishes and leans it, with transverse tent ridges and pillar buckles.
  Hinge   a rigid panel (hood, trunk lid) folds along a straight crease with a narrow rounded radius: tents, Z-folds, a hood standing up on its hinge.
  Rigid   doors swing on their hinge and sag, a bumper hangs from one end, lamps, grille and plate (small parts) move as SOLID pieces: the Jacobian of the field gives each
          connected piece one rigid motion, so the licence plate letters stay readable; a plate and its ink always move together.
  Glass   removed per material in Voronoi shards (broken pane) or wholly (gone); no holes in painted panels, so there are no black voids.
  Colour  smoke-black scorch and scrape marks multiply the existing 'Color' layer (the game multiplies it into the paint).

Entry point: `crash(root, spec)`; spec comes from crash_table.build(car, type, degree)."""
import math
import random
import zlib

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector as V3


def ssn(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def tent(w):
    return np.maximum(0.0, 1.0 - np.abs(w))


def world(ob):
    me = ob.data
    n = len(me.vertices)
    co = np.empty(n * 3, dtype=np.float64)
    me.vertices.foreach_get('co', co)
    co = co.reshape(n, 3)
    nm = np.empty(n * 3, dtype=np.float64)
    me.vertices.foreach_get('normal', nm)
    nm = nm.reshape(n, 3)
    mw = np.array(ob.matrix_world)
    p = co @ mw[:3, :3].T + mw[:3, 3]
    nn = nm @ np.linalg.inv(mw[:3, :3])
    nn /= np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-9)
    return p, nn


def put(ob, p):
    mw = np.array(ob.matrix_world)
    inv = np.linalg.inv(mw)
    co = p @ inv[:3, :3].T + inv[:3, 3]
    ob.data.vertices.foreach_set('co', co.ravel())
    ob.data.update()


def rot_about(P, origin, axis, ang):
    """rotate points about the line through origin; ang may be an array (per point)"""
    a = np.array(axis, dtype=float)
    a /= np.linalg.norm(a)
    o = np.array(origin, dtype=float)
    ang = np.broadcast_to(np.asarray(ang, dtype=float), (len(P),))
    d = P - o
    c, s = np.cos(ang)[:, None], np.sin(ang)[:, None]
    return o + d * c + np.cross(a, d) * s + a * (d @ a)[:, None] * (1 - c)


class Car:
    """measures that the clean car gives by itself (no per-car numbers)"""
    def __init__(self, root):
        self.root = root
        bpy.context.view_layer.update()
        self.obs = {o.name: o for o in root.children_recursive}
        allp = lambda names: np.concatenate([world(self.obs[n])[0] for n in names if n in self.obs])   # noqa: E731
        self.nose = float(allp(['Bumper_F', 'Body'])[:, 0].max())
        self.tail = float(allp(['Bumper_R', 'Body'])[:, 0].min())
        body = allp(['Body'])
        self.hw = float(np.abs(body[:, 1]).max())
        self.zroof = float(body[:, 2].max())
        gl = [n for n in self.obs if n.startswith('Glass_F')]
        self.belt = float(min(world(self.obs[n])[0][:, 2].min() for n in gl)) if gl else 0.68 * self.zroof
        self.hinge_x = float(world(self.obs['Hood'])[0][:, 0].min()) if 'Hood' in self.obs else 0.0
        self.wheels = {n[6:8]: self.obs[n] for n in self.obs if n.startswith('Wheel_') and len(n) == 8}
        self.plates = {}
        if 'Ends' in self.obs:
            import crashfragile
            for c in crashfragile.comp_table(self.obs['Ends']):
                if 'M_plate' in c['mats']:
                    self.plates['front' if c['c'][0] > 0 else 'rear'] = [float(x) for x in c['c']]
        g = world(self.obs['Glass'])[0] if 'Glass' in self.obs else body
        self.xcab0, self.xcab1 = float(g[:, 0].min()), float(g[:, 0].max())


# ---- the fields -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class Crush:
    """A ram pushes one end (or side) of the car inward. d: end front|rear|left|right, depth, length (crumple depth into the car), t0 (lateral centre), width, base (share of the
    push that the rest of the face gets), zc/zh/zbase (ram height), gamma (rad: the push slants sideways), bend (m: the end shoved sideways), sag (m), rise (m: top skin buckles up),
    pinch (0..1: the face narrows), ridges: list of dict(theta, c, lam, amp, t, span) straight tent ridges along the skin (theta: slant from the push axis, c: position along the
    push axis from the face in metres, t: lateral position; amp metres along the surface normal, negative = in)."""
    def __init__(self, car, d):
        self.car, self.d = car, d
        self.end = d['end']
        self.L = d['length']
        self.depth = min(d['depth'], 0.78 * self.L)
        body = world(car.obs['Body'])[0]
        # parts that stand in front of the body skin (bumper, plate, lamps) move like the skin behind them: u is measured from the skin
        self.u0 = {'front': car.nose - float(body[:, 0].max()), 'rear': float(body[:, 0].min()) - car.tail}.get(self.end, 0.0)

    def frame(self, P):
        c, e = self.car, self.end
        if e == 'front':
            return c.nose - P[:, 0], P[:, 1], np.array([-1.0, 0, 0]), np.array([0, 1.0, 0])
        if e == 'rear':
            return P[:, 0] - c.tail, P[:, 1], np.array([1.0, 0, 0]), np.array([0, 1.0, 0])
        if e == 'left':
            return c.hw - P[:, 1], P[:, 0], np.array([0, -1.0, 0]), np.array([1.0, 0, 0])
        return P[:, 1] + c.hw, P[:, 0], np.array([0, 1.0, 0]), np.array([1.0, 0, 0])

    def mask(self, P):
        u, _, _, _ = self.frame(P)
        return u < self.L * 1.15

    def __call__(self, P, N):
        d = self.d
        u, t, din, dlat = self.frame(P)
        u = np.maximum(u, self.u0)
        z = P[:, 2]
        L = self.L
        g = np.clip(1.0 - np.maximum(u, 0) / L, 0, 1) ** 1.3
        dt = t - d.get('t0', 0.0)
        base = d.get('base', 0.25)
        pt = base + (1 - base) * np.exp(-(np.abs(dt) / d.get('width', 0.7)) ** 2.4)
        bz = d.get('zbase', 0.35)
        pz = bz + (1 - bz) * np.exp(-((z - d.get('zc', 0.65)) / d.get('zh', 0.5)) ** 2)
        s = self.depth * pt * pz * g
        gam = d.get('gamma', 0.0)
        dirv = din * math.cos(gam) + dlat * math.sin(gam)
        D = s[:, None] * dirv[None, :]
        D[:, 2] -= d.get('sag', 0.0) * pt * g ** 1.5
        bump = np.sin(np.pi * np.clip(u / L, 0, 1)) ** 1.2
        D[:, 2] += d.get('rise', 0.0) * pt * ssn(0.62, 0.9, z) * bump
        D += dlat[None, :] * (d.get('bend', 0.0) * ssn(0, 1, 1 - np.maximum(u, 0) / (1.2 * L)) ** 1.5)[:, None]
        D += dlat[None, :] * (-(dt) * d.get('pinch', 0.0) * g * pt)[:, None]
        R = np.zeros(len(P))
        env = ssn(0.0, 0.12, u / L) * (1 - ssn(0.88, 1.0, u / L))
        for r in d.get('ridges', []):
            th = r['theta']
            w = (u * math.cos(th) + (t - r.get('t', 0.0)) * math.sin(th) - r['c']) / r['lam']
            lat = np.exp(-(np.abs(t - r.get('t', 0.0)) / r.get('span', 1.2)) ** 2.4)
            R += r['amp'] * tent(w) * lat * env
        return P + D + R[:, None] * N


class Roof:
    """Rollover: the greenhouse above the belt line is pressed down (c = share of its height lost), dished, leaned and buckled. d: c, dish, lean, lean_tw, push, twist,
    ridges[(x, lam, amp)] (transverse tent ridges of the roof), pillars[(z, lam, amp)] (the pillars fold inward at that height)."""
    def __init__(self, car, d):
        self.car, self.d = car, d

    def mask(self, P):
        return P[:, 2] > self.car.belt - 0.06

    def __call__(self, P, N):
        c, d = self.car, self.d
        zb, zr = c.belt, c.zroof
        z = P[:, 2]
        h = np.clip((z - zb) / (zr - zb), 0, 1)
        above = z > zb
        out = P.copy()
        out[:, 2] = z - d['c'] * (np.minimum(z, zr) - zb) * above
        xm = 0.5 * (c.xcab0 + c.xcab1)
        xh = 0.5 * (c.xcab1 - c.xcab0) + 0.2
        xp = np.exp(-(((P[:, 0] - xm) / xh) ** 2) * 1.4)
        out[:, 2] -= d.get('dish', 0.0) * np.exp(-(P[:, 1] / (c.hw * 0.8)) ** 2) * ssn(0, 1, h) * xp
        out[:, 1] += d.get('lean', 0.0) * h ** 1.5 * (1.0 + d.get('lean_tw', 0.0) * (P[:, 0] - xm) / xh)
        out[:, 0] += d.get('push', 0.0) * h ** 1.5 + d.get('twist', 0.0) * np.sign(P[:, 1]) * h ** 1.5
        top = ssn(0.35, 0.8, N[:, 2])
        for (x, lam, amp) in d.get('ridges', []):
            out[:, 2] += amp * tent((P[:, 0] - x) / lam) * top * ssn(0.5, 0.9, h) * xp
        for (zk, lam, amp) in d.get('pillars', []):
            out[:, 1] -= np.sign(P[:, 1]) * amp * tent((z - zk) / lam) * (np.abs(P[:, 1]) > 0.35)
        return out


# ---- mesh helpers ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def subdivide(ob, where, edge=0.035, rounds=4):
    """midpoint cuts of the long edges whose both ends lie in the region (where: world points -> bool array)"""
    me = ob.data
    mw = ob.matrix_world
    bm = bmesh.new()
    bm.from_mesh(me)
    for _ in range(rounds):
        bm.verts.ensure_lookup_table()
        pts = np.array([(mw @ v.co)[:] for v in bm.verts])
        inz = where(pts)
        es = [e for e in bm.edges if e.calc_length() > edge and inz[e.verts[0].index] and inz[e.verts[1].index]]
        if not es:
            break
        bmesh.ops.subdivide_edges(bm, edges=es, cuts=1, use_grid_fill=True)
    bm.to_mesh(me)
    bm.free()
    me.update()


def smooth_by_angle(ob, deg=38):
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.selected_objects:
        o.select_set(False)
    ob.select_set(True)
    try:
        bpy.ops.mesh.customdata_custom_splitnormals_clear()
    except Exception:
        pass
    for e in ob.data.edges:
        e.use_edge_sharp = False
    ob.data.polygons.foreach_set('use_smooth', [True] * len(ob.data.polygons))
    ob.data.update()
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(deg))


def components(ob):
    """connected pieces of a mesh as index lists (a licence plate and its ink are merged into one piece)"""
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    seen, comps = set(), []
    for v0 in bm.verts:
        if v0.index in seen:
            continue
        seen.add(v0.index)
        stack, comp = [v0], []
        while stack:
            v = stack.pop()
            comp.append(v.index)
            for e in v.link_edges:
                w = e.other_vert(v)
                if w.index not in seen:
                    seen.add(w.index)
                    stack.append(w)
        comps.append(comp)
    plate = set()
    names = [m.name if m else '' for m in me.materials]
    for f in bm.faces:
        if names[f.material_index].startswith('M_plate'):
            plate.update(v.index for v in f.verts)
    bm.free()
    pl = [c for c in comps if plate.intersection(c)]
    if len(pl) > 1:
        P = world(ob)[0]
        used = [False] * len(pl)
        for i in range(len(pl)):
            if used[i]:
                continue
            ci = P[pl[i]].mean(axis=0)
            for j in range(i + 1, len(pl)):
                if not used[j] and np.linalg.norm(ci - P[pl[j]].mean(axis=0)) < 0.3:
                    pl[i] = pl[i] + pl[j]
                    used[j] = True
        comps = [c for c in comps if not plate.intersection(c)] + [c for i, c in enumerate(pl) if not used[i]]
    return comps


def nearest_rotation(J):
    R = J.copy()
    for _ in range(8):
        R = 0.5 * (R + np.linalg.inv(R).T)
    return R


def rigid_pieces(ob, fields, hangs, maxrot=math.radians(50)):
    """small parts follow the fields as solid pieces (one motion per piece): the field's displacement at the centre and its local rotation (nearest rotation of the Jacobian)"""
    P, N = world(ob)
    Q = P.copy()
    up = np.array([[0, 0, 1.0]])

    def F(x):
        y = x[None, :]
        for f in fields:
            y = f(y, up)
        return y[0]
    for comp in components(ob):
        pts = P[comp]
        c = pts.mean(axis=0)
        f0 = F(c)
        dlt = 0.04
        J = np.stack([(F(c + np.eye(3)[i] * dlt) - f0) / dlt for i in range(3)], axis=1)
        R = nearest_rotation(J) if np.all(np.isfinite(J)) and abs(np.linalg.det(J)) > 1e-3 else np.eye(3)
        q = Matrix(R.tolist()).to_quaternion()
        if q.angle > maxrot:
            q = Quaternion(q.axis, maxrot)
        Rm = np.array(q.to_matrix())
        Pn = (pts - c) @ Rm.T + f0
        for h in hangs:
            if np.linalg.norm(c - np.array(h['center'])) < h['r']:
                piv = f0 + np.array(h.get('pivot', (0, 0, 0.04)))
                for ax, key in (((0, 1.0, 0), 'pitch'), ((1.0, 0, 0), 'roll'), ((0, 0, 1.0), 'yaw')):
                    if h.get(key):
                        Pn = rot_about(Pn, piv, ax, math.radians(h[key]))
                Pn = Pn + np.array(h.get('move', (0, 0, 0)))
        Q[comp] = Pn
    put(ob, Q)


def rigid_subset(ob, P0, idx, fields):
    """one stiff piece of a mesh (the aerial) rides the fields as a solid rod: it turns about its foot with the Jacobian there and is neither sheared nor stretched"""
    up = np.array([[0, 0, 1.0]])

    def F(x):
        y = x[None, :]
        for f in fields:
            y = f(y, up)
        return y[0]
    pts = P0[idx]
    foot = pts[np.argmin(pts[:, 2])]
    f0 = F(foot)
    dlt = 0.04
    J = np.stack([(F(foot + np.eye(3)[i] * dlt) - f0) / dlt for i in range(3)], axis=1)
    R = nearest_rotation(J) if np.all(np.isfinite(J)) and abs(np.linalg.det(J)) > 1e-3 else np.eye(3)
    P = world(ob)[0]
    P[idx] = (pts - foot) @ R.T + f0
    put(ob, P)


def warp(ob, fn):
    P, N = world(ob)
    put(ob, fn(P, N))


def hinge_op(P, op):
    """fold the part along a straight crease: points ahead of it (side + of its normal) rotate about it by angle (deg, + = nose down) with a narrow rounded radius r"""
    a = op.get('alpha', 0.0)
    nrm = np.array([math.cos(a), math.sin(a), 0.0])
    axis = np.array([-math.sin(a), math.cos(a), 0.0])
    o = np.array([op['x'], op.get('y', 0.0), op.get('z', 0.9)])
    w = ssn(-op.get('r', 0.05), op.get('r', 0.05), (P - o) @ nrm)
    return rot_about(P, o, axis, math.radians(op['angle']) * w)


def crumple_op(P, op):
    """a rigid lid (hood, tailgate) is crumpled instead of standing flat: it curls (rolled up progressively from its hinge), twists, narrows like a concertina and buckles along straight
    slanted tent ridges. op: x (hinge), len (m, the lid's length from the hinge), dir (+1 lid lies ahead of the hinge, -1 behind), curl (deg at the free end), twist (deg at the free end,
    left up / right down), shrink (0..1 narrowing of the free end), ridges [(s, lam, amp, theta)] (s = share of the length, amp m along z, theta rad slant)."""
    d = op.get('dir', 1)
    L = op.get('len', 1.2)
    s = np.clip(d * (P[:, 0] - op['x']) / L, 0.0, 1.5)
    o = np.array([op['x'], 0.0, op.get('z', 0.9)])
    out = rot_about(P, o, (0, 1, 0), math.radians(op.get('curl', 0.0)) * d * s ** 1.6)
    out[:, 2] += math.radians(op.get('twist', 0.0)) * out[:, 1] * s
    out[:, 1] *= 1.0 - op.get('shrink', 0.0) * s ** 1.4
    for (ss, lam, amp, th) in op.get('ridges', []):
        w = ((s - ss) * L * math.cos(th) + out[:, 1] * math.sin(th)) / lam
        out[:, 2] += amp * tent(w) * ssn(0.0, 0.25, s)
    return out


def swing_door(P, op, hx, hw, side):
    """a door on its front hinge: opens by `open` deg, sags (its rear edge drops) by `sag` deg, rolls about the hinge axis, drops by `drop` m"""
    hy = side * (hw - 0.03)
    o = (hx, hy, 0.6)
    Q = rot_about(P, o, (0, 0, 1), -side * math.radians(op.get('open', 0)))
    if op.get('sag'):
        Q = rot_about(Q, o, (0, 1, 0), math.radians(op['sag']))
    if op.get('roll'):
        Q = rot_about(Q, o, (1, 0, 0), side * math.radians(op['roll']))
    return Q + np.array([0, 0, -op.get('drop', 0.0)])


def hang_bumper(P, op, car, front):
    """a bumper hangs from one end (`from` = +1 left, -1 right): rolls about that end so the other end drops, yaws, sags in the middle by `bow`"""
    end = op.get('from', 1)
    xb = car.nose if front else car.tail
    o = (xb, end * 0.72, 0.5)
    Q = rot_about(P, o, (1, 0, 0), -end * math.radians(op.get('roll', 0)))
    Q = rot_about(Q, o, (0, 0, 1), end * math.radians(op.get('yaw', 0)))
    Q = rot_about(Q, o, (0, 1, 0), math.radians(op.get('pitch', 0)))
    Q[:, 2] -= op.get('bow', 0.0) * np.exp(-(Q[:, 1] / 0.5) ** 2)
    if op.get('fold'):       # the bar is bent in plan around a point on it: a V that points inward, its far end swung forward
        f, ft, fw = op['fold'], op.get('fold_t', 0.0), op.get('fold_w', 0.5)
        Q[:, 0] -= f * tent((Q[:, 1] - ft) / fw) * (1 if front else -1)
        Q[:, 2] -= op.get('fold_z', 0.0) * tent((Q[:, 1] - ft) / fw)
    Q[:, 0] += op.get('move_x', 0.0)
    return Q + np.array([0, 0, op.get('drop', 0.0)])


def bowls(P, items):
    Q = P.copy()
    for b in items:
        c = np.array(b['center'])
        d = np.array(b.get('dir', (0, 0, -1.0)))
        d = d / np.linalg.norm(d)
        w = np.exp(-(np.linalg.norm((P - c) * np.array(b.get('squash', (1, 1, 1))), axis=1) / b['r']) ** 2)
        Q += w[:, None] * b['depth'] * d[None, :]
    return Q


def break_glass(ob, region, frac, seed, cells=170, tilt=7.0, mats=('M_glass',)):
    """shatter the glass faces (M_glass only) of the region: Voronoi cells of the pane whose borders are CUT as straight cracks (bisector planes of neighbouring seeds, so the shards
    have clean polygon outlines instead of staircases of mesh faces); frac < 1 = a cracked pane (that share of the cells is out, the rest stay as tilted shards with gaps between them),
    frac 1 = gone (only some cells on the frame stay as jagged teeth). The frame (seal, chrome) is never moved."""
    me = ob.data
    mw = ob.matrix_world
    bm = bmesh.new()
    bm.from_mesh(me)
    lay = bm.faces.layers.int.new('cell')
    sel = bm.faces.layers.int.new('sel')
    bm.faces.ensure_lookup_table()
    names = [m.name if m else '' for m in me.materials]
    fs = [f for f in bm.faces if names[f.material_index] in mats and region(mw @ f.calc_center_median())]
    if not fs:
        bm.free()
        return 0
    for f in fs:
        f[sel] = 1
    cs = np.array([(mw @ f.calc_center_median())[:] for f in fs])
    area = sum(f.calc_area() for f in fs)
    rnd = random.Random(seed)
    n = min(cells, max(3, int(area / 0.011)))
    seeds = cs[[rnd.randrange(len(fs)) for _ in range(n)]]
    # straight cracks: cut the pane along the bisector plane of every near pair of seeds
    K = min(5, n - 1)
    pairs = set()
    for i in range(n):
        d = np.linalg.norm(seeds - seeds[i], axis=1)
        for j in np.argsort(d)[1:K + 1]:
            pairs.add((min(i, int(j)), max(i, int(j))))
    mwi = mw.inverted()
    m3t = mw.to_3x3().transposed()

    def nearest(c, ids):
        return min(ids, key=lambda k: (c - seeds[k]) @ (c - seeds[k]))
    for f, c in zip(fs, cs):                      # every face starts in the cell of its nearest seed
        f[lay] = int(np.argmin(((seeds - c) ** 2).sum(axis=1)))
    for i, j in sorted(pairs):
        a, b = V3(seeds[i].tolist()), V3(seeds[j].tolist())
        if (b - a).length < 1e-5:
            continue
        sub = [f for f in bm.faces if f.is_valid and f[sel] == 1 and f[lay] in (i, j)]     # the crack is cut only where the two cells meet: no grid of full-pane cuts
        if not sub:
            continue
        geom = list(sub) + list({e for f in sub for e in f.edges}) + list({v for f in sub for v in f.verts})
        bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=mwi @ ((a + b) * 0.5), plane_no=(m3t @ (b - a)).normalized())
        for f in bm.faces:
            if f.is_valid and f[sel] == 1 and f[lay] in (i, j):
                f[lay] = nearest(np.array((mw @ f.calc_center_median())[:]), (i, j))
    bm.faces.ensure_lookup_table()
    bm.faces.index_update()
    fs = [f for f in bm.faces if f.is_valid and f[sel] == 1]
    sset = set(f.index for f in fs)
    cs = np.array([(mw @ f.calc_center_median())[:] for f in fs])
    cell = np.argmin(((cs[:, None, :] - seeds[None, :, :]) ** 2).sum(axis=2), axis=1) if len(fs) * n < 4_000_000 else np.concatenate(
        [np.argmin(((cs[k:k + 800, None, :] - seeds[None, :, :]) ** 2).sum(axis=2), axis=1) for k in range(0, len(fs), 800)])
    onframe = [any(len(e.link_faces) == 1 or any(lf.index not in sset for lf in e.link_faces) for e in f.edges) for f in fs]
    frame_cells = set(int(c) for c, o in zip(cell, onframe) if o)
    if frac >= 0.999:
        gone = {k for k in range(n) if not (k in frame_cells and rnd.random() < 0.5)}
    else:
        gone = {k for k in range(n) if rnd.random() < frac}
    for f, c in zip(fs, cell):
        f[lay] = int(c)
    kill = [f for f, c in zip(fs, cell) if int(c) in gone]
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    keep = [f for f in fs if f.is_valid]
    cut = [e for e in {e for f in keep for e in f.edges if len(e.link_faces) == 2 and e.link_faces[0].index in sset and e.link_faces[1].index in sset and e.link_faces[0][lay] != e.link_faces[1][lay]}]
    bmesh.ops.split_edges(bm, edges=cut)
    frame_v = set()
    for f in bm.faces:
        if f.index not in sset and f.is_valid:
            frame_v.update(v.index for v in f.verts)
    bm.verts.ensure_lookup_table()
    byc = {}
    for f in keep:
        if f.is_valid:
            byc.setdefault(f[lay], []).append(f)
    for c, faces in byc.items():
        vs = {v for f in faces for v in f.verts if v.index not in frame_v}
        if not vs:
            continue
        ctr = sum((mw @ v.co for v in vs), V3()) / len(vs)
        nrm = sum((mw.to_3x3() @ f.normal for f in faces), V3()).normalized()
        axis = V3((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized()
        q = Quaternion(axis, math.radians(rnd.uniform(0.4, 1.0) * tilt * (2.2 if frac >= 0.999 else 1.0)))
        off = nrm * rnd.uniform(-0.012, 0.012)
        inv = mw.inverted()
        for v in vs:
            w = mw @ v.co
            v.co = inv @ (ctr + q @ (w - ctr) + off)
    bm.faces.layers.int.remove(sel)
    bm.faces.layers.int.remove(lay)
    bm.to_mesh(me)
    bm.free()
    me.update()
    return len(kill)


def tear(ob, center, radii, frac, seed, cells=24):
    """tear a ragged hole in a painted mesh: every face whose centre lies in the ellipsoid belongs to a Voronoi cell; `frac` of the cells are removed (outer skin and inner lining together)"""
    me = ob.data
    mw = ob.matrix_world
    bm = bmesh.new()
    bm.from_mesh(me)
    c0, r0 = np.array(center), np.array(radii)
    fs, cs = [], []
    for f in bm.faces:
        p = np.array((mw @ f.calc_center_median())[:])
        if np.sum(((p - c0) / r0) ** 2) < 1.0:
            fs.append(f)
            cs.append(p)
    if len(fs) < 4:
        bm.free()
        return 0
    cs = np.array(cs)
    rnd = random.Random(seed)
    seeds = cs[[rnd.randrange(len(fs)) for _ in range(cells)]]
    cell = np.concatenate([np.argmin(((cs[i:i + 4000, None, :] - seeds[None, :, :]) ** 2).sum(axis=2), axis=1) for i in range(0, len(cs), 4000)])
    out = {k for k in range(cells) if rnd.random() < frac}
    kill = [f for f, c in zip(fs, cell) if int(c) in out]
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    bm.to_mesh(me)
    bm.free()
    me.update()
    return len(kill)


def colors(ob, scorch, scrapes, tint=(1.0, 0.92, 0.85)):
    """smoke-black scorch (soft ellipsoids) and scrape streaks (parallel dark lines at fixed heights along the side that met the ground) multiply the 'Color' layer"""
    me = ob.data
    ca = me.color_attributes.get('Color')
    if ca is None:
        ca = me.color_attributes.new('Color', 'BYTE_COLOR', 'CORNER')
        ca.data.foreach_set('color', [1.0] * (4 * len(me.loops)))
    n = len(me.loops)
    col = np.empty(n * 4)
    ca.data.foreach_get('color', col)
    col = col.reshape(n, 4)
    vi = np.empty(n, dtype=np.int64)
    me.loops.foreach_get('vertex_index', vi)
    P, _ = world(ob)
    p = P[vi]
    k = np.ones(n)
    for s in scorch:
        c = np.array(s['center'])
        sc = np.array(s.get('scale', (1, 1, 1)))
        k *= 1.0 - s['strength'] * np.exp(-(np.linalg.norm((p - c) * sc, axis=1) / s['r']) ** 2)
    for sc in scrapes:
        on = ssn(0.0, 0.3, sc['side'] * p[:, 1] - 0.55)
        zb = np.exp(-(((p[:, 2] - sc['z']) / sc['h']) ** 2))
        xs = ssn(sc['x0'], sc['x0'] + 0.3, p[:, 0]) * (1 - ssn(sc['x1'] - 0.3, sc['x1'], p[:, 0]))
        stripes = 0.5 + 0.5 * np.sign(np.sin(p[:, 2] * sc.get('freq', 55.0)) + 0.35)
        k *= 1.0 - sc['strength'] * on * zb * xs * (0.55 + 0.45 * stripes)
    col[:, 0] *= k * tint[0]
    col[:, 1] *= k * tint[1]
    col[:, 2] *= k * tint[2]
    ca.data.foreach_set('color', col.ravel())
    me.update()


PAINTED = ('Body', 'Door_', 'Hood', 'Trunk', 'Tailgate', 'Liftgate', 'Bumper')
RIGID = ('Ends', 'Lamps_Head', 'Lamps_Park', 'Lamps_Tail', 'Lamps_Marker')


def mesh_obs(root):
    return {o.name: o for o in root.children_recursive if o.type == 'MESH'}


def crash(root, spec, log=print):
    import crashfragile
    car = Car(root)
    obs = mesh_obs(root)
    seed = spec.get('seed', 7)
    spec = crashfragile.resolve_fragile(spec, car)
    fields = [Crush(car, spec[k]) for k in ('crush', 'crush2') if spec.get(k)]
    if spec.get('roof'):
        fields.append(Roof(car, spec['roof']))
    bowl_items = spec.get('bowls', [])

    def field_all(P, N):
        Q = P
        for f in fields:
            Q = f(Q, N)
        return bowls(Q, bowl_items) if bowl_items else Q
    def zone(pts):
        z = np.logical_or.reduce([f.mask(pts) for f in fields]) if fields else np.zeros(len(pts), bool)
        for b in bowl_items:
            z = z | (np.linalg.norm(pts - np.array(b['center']), axis=1) < b['r'] * 1.7)
        return z
    glass_fine = bool(spec.get('glass'))
    dense = ['Body', 'Hood', 'Trunk', 'Tailgate', 'Liftgate', 'Bumper_F', 'Bumper_R', 'Trim', 'Glass', 'Interior'] + [n for n in obs if n.startswith(('Door_', 'Glass_', 'Trim_'))]
    for nm in dense:
        if nm in obs:
            before = len(obs[nm].data.vertices)
            subdivide(obs[nm], (lambda pts: np.ones(len(pts), bool)) if (glass_fine and nm.startswith('Glass')) else zone, spec.get('glass_edge', 0.032) if nm.startswith('Glass') else spec.get('edge', 0.035))
            log('CK subdivided', nm, before, '->', len(obs[nm].data.vertices))
    from mathutils.kdtree import KDTree
    bP, bN = world(obs['Body'])
    kd = KDTree(len(bP))
    for i, p in enumerate(bP):
        kd.insert(p.tolist(), i)
    kd.balance()

    def skin_normals(P, N):
        """strips and trim lie on the skin: they take the skin's normal there, so a ridge pushes strip and panel the same way (no strips floating off the dents)"""
        N2 = N.copy()
        for i, p in enumerate(P):
            _, j, dist = kd.find(p.tolist())
            if dist < 0.09:
                N2[i] = bN[j]
        return N2
    for nm, ob in obs.items():
        if nm in RIGID or nm == 'SteeringWheel':
            rigid_pieces(ob, fields, spec.get('hangs', []) if nm in RIGID else [])
        elif not nm.startswith('Wheel_'):
            P0 = world(ob)[0] if nm == 'Trim' else None
            if nm == 'Trim' or nm.startswith('Trim_'):
                P, N = world(ob)
                put(ob, field_all(P, skin_normals(P, N)))
            else:
                warp(ob, field_all)
            if nm == 'Trim':       # the aerial is a stiff rod: it rides the fields rigidly (never stretched by the skin normals)
                ant = [c for c in components(ob) if P0[c][:, 2].max() > car.zroof + 0.2]
                for c in ant:
                    rigid_subset(ob, P0, c, fields)
    for key, e in car.wheels.items():       # wheels follow the structure
        p = field_all(np.array([[e.location.x, e.location.y, e.location.z]]), np.array([[0, 0, 1.0]]))[0]
        e.location = V3(p.tolist())
    # the parts' own events
    for nm, ops in spec.get('parts', {}).items():
        if nm not in obs:
            continue
        hx = float(world(obs[nm])[0][:, 0].max())
        for ob in [obs[nm]] + [o for o in obs[nm].children_recursive if o.type == 'MESH']:
            P, N = world(ob)
            for op in ops:
                k = op['op']
                if k == 'hinge':
                    P = hinge_op(P, op)
                elif k == 'door':
                    P = swing_door(P, op, op.get('hinge_x', hx), car.hw, 1 if nm.endswith('L') else -1)
                elif k == 'crumple':
                    P = crumple_op(P, op)
                elif k == 'hang_bumper':
                    P = hang_bumper(P, op, car, nm.endswith('F'))
                elif k == 'rigid':
                    P = rot_about(P, op['pivot'], op['axis'], math.radians(op['angle'])) + np.array(op.get('move', (0, 0, 0)))
            put(ob, P)
    for key, w in spec.get('wheels', {}).items():
        e = car.wheels.get(key)
        mesh = obs.get('Wheel_%s_mesh' % key)
        if e is None:
            continue
        if w == 'remove':
            if mesh is not None:
                bpy.data.objects.remove(mesh, do_unlink=True)
            continue
        e.location += V3((w.get('dx', 0.0), w.get('dy', 0.0), w.get('dz', 0.0)))
        e.rotation_euler = (math.radians(w.get('camber', 0.0)), 0.0, math.radians(w.get('toe', 0.0)))
        if w.get('wobble') and mesh is not None:
            me = mesh.data
            co = np.empty(len(me.vertices) * 3)
            me.vertices.foreach_get('co', co)
            co = rot_about(co.reshape(-1, 3), (0, 0, 0), (1, 0, 0), math.radians(w['wobble']))
            me.vertices.foreach_set('co', co.ravel())
            me.update()
    bpy.context.view_layer.update()
    # glass: region by name; door glass by its own node name
    regions = {'wind': lambda p: p.x > 0.08 and abs(p.y) < 0.95, 'rear': lambda p: p.x < -1.0, 'opera': lambda p: -1.0 <= p.x <= 0.08 and abs(p.y) > 0.55,
               'quarter_L': lambda p: p.x < -1.0 and p.y > 0.0, 'quarter_R': lambda p: p.x < -1.0 and p.y < 0.0}
    for rn, (rx0, rx1, ry0, ry1) in spec.get('regions', {}).items():       # a car with another glass layout names its panes by x range and |y| range
        regions[rn] = (lambda p, rx0=rx0, rx1=rx1, ry0=ry0, ry1=ry1: rx0 <= p.x <= rx1 and ry0 <= abs(p.y) <= ry1)
    for gname, frac in spec.get('glass', {}).items():
        if gname in regions:
            ob, reg = obs.get('Glass'), regions[gname]
        else:
            ob, reg = obs.get(gname), (lambda p: True)
        if ob is not None:
            n = break_glass(ob, reg, frac, seed + zlib.crc32(gname.encode()) % 97, cells=spec.get('glass_cells', 170))
            log('CK glass', gname, 'removed faces', n)
    obs = mesh_obs(root)
    crashfragile.apply_fragile(obs, spec.get('fragile', {}), seed)
    for t in spec.get('tears', []):
        ob = obs.get(t['node'])
        if ob is not None:
            log('CK tear', t['node'], tear(ob, t['center'], t['radii'], t['frac'], seed + 5, t.get('cells', 24)))
    for nm in spec.get('remove', []):
        o = bpy.data.objects.get(nm)
        if o is not None:
            for c in list(o.children_recursive) + [o]:
                bpy.data.objects.remove(c, do_unlink=True)
    obs = mesh_obs(root)
    for nm, ob in obs.items():
        painted = nm.startswith(PAINTED) and 'Glass' not in nm and 'Trim' not in nm
        if painted:
            colors(ob, spec.get('scorch', []), spec.get('scrape', []))
        elif nm.startswith(('Trim', 'Engine', 'Underbody')):
            colors(ob, spec.get('scorch', []), [])
        if nm.startswith(PAINTED + ('Trim', 'Glass', 'Interior', 'Underbody')):
            smooth_by_angle(ob, spec.get('smooth', 38))
    bpy.context.view_layer.update()
