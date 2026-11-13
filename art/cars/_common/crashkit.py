# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Frontal crash deformation of a finished car (Blender, world axes: +X forward, +Y left, +Z up).

One smooth analytic field, no noise: the structure ahead of the cowl is pushed back (crushed) by an amount that peaks on the struck side and falls to a small push across
the rest of the nose, the upper skin buckles into chevron folds that run from the stiffened edges towards the middle (hood and fender tops), the flanks ripple along the
body bead, the bumper, grille, plate and headlights go with it (the headlamp is also dropped and canted), the wheel on the struck side is pushed back and turned.
Reference: 1980s frontal and offset-frontal crash photographs (hood buckled in two chevron creases behind the grille, fender folded along its top edge and the bead,
bumper bar bent back and sheared, radiator support pushed to the engine, doors still shut and gaps closing at the A-pillar).
`crash_front(root, side=1, depth=0.5)` changes the meshes in place; the node names, the part split and the pivots stay."""
import math

import bmesh
import bpy
from mathutils import Vector as V3


def _ss(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


class Field:
    def __init__(self, side=1, depth=0.5, x0=1.0, xn=2.5, yc=0.35, hw=0.62, base=0.16):
        self.s, self.depth, self.x0, self.xn, self.yc, self.hw, self.base = side, depth, x0, xn, side * yc, hw, base

    def dy(self, y):
        """how much of the full crush depth the point at lateral position y gets"""
        return self.base + (1 - self.base) * math.exp(-(((y - self.yc) / self.hw) ** 2))

    def u(self, x):
        return max(0.0, min(1.0, (x - self.x0) / (self.xn - self.x0)))

    def shift(self, x, y):
        return self.depth * self.dy(y) * self.u(x) ** 1.5

    def fold_z(self, x, y, amp, lam, phase=0.0):
        """chevron buckles of the upper skin: the creases run diagonally from the stiffened outer edges to the middle of the struck side"""
        u = self.u(x)
        d = self.dy(y)
        q = (x - self.x0 - 0.32 * abs(y - self.yc)) / lam
        w = 2 * math.pi * q + phase
        crease = math.sin(w) - 0.28 * math.sin(3 * w)          # flat panels between sharper creases
        return amp * d * (u ** 0.9) * crease * _ss(0.0, 0.25, u) * (self.depth / 0.5)


def clean_normals(ob):
    """drop custom split normals and sharp marks so the shading follows the deformed surface"""
    me = ob.data
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.selected_objects:
        o.select_set(False)
    ob.select_set(True)
    try:
        bpy.ops.mesh.customdata_custom_splitnormals_clear()
    except Exception:
        pass
    for e in me.edges:
        e.use_edge_sharp = False
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    me.update()


def subdivide_front(ob, x0, edge=0.045, rounds=4):
    clean_normals(ob)
    """cut the long edges of the front region so that the folds are smooth (no new random vertices: midpoints only)"""
    mw = ob.matrix_world
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    for _ in range(rounds):
        es = [e for e in bm.edges if e.calc_length() > edge and max((mw @ v.co).x for v in e.verts) > x0 - 0.05]
        if not es:
            break
        bmesh.ops.subdivide_edges(bm, edges=es, cuts=1, use_grid_fill=True)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()


def _deform(ob, f, kind):
    me = ob.data
    mw = ob.matrix_world
    inv = mw.inverted()
    n3 = mw.to_3x3()
    for v in me.vertices:
        p = mw @ v.co
        if p.x < f.x0 - 0.02:
            continue
        nrm = n3 @ v.normal
        dx = -f.shift(p.x, p.y)
        u = f.u(p.x)
        dz = -0.05 * (f.depth / 0.5) * f.dy(p.y) * u ** 2          # the nose sags
        dy = 0.0
        top = _ss(0.15, 0.65, nrm.z)
        flank = _ss(0.35, 0.8, abs(nrm.y))
        if kind == 'hood':
            dz += f.fold_z(p.x, p.y, 0.085, 0.42)
            dz += 0.10 * (f.depth / 0.5) * f.dy(p.y) * math.exp(-(((p.x - 1.85) / 0.45) ** 2))      # the middle of the hood arches up
        elif kind == 'body':
            dz += top * f.fold_z(p.x, p.y, 0.03, 0.34, math.pi)
            bead = 1.0 + 1.4 * math.exp(-(((p.z - 0.62) / 0.06) ** 2))
            wave = math.sin(2 * math.pi * (p.x - f.x0) / 0.50 + 0.6 * abs(p.y - f.yc))
            dy += flank * math.copysign(1.0, nrm.y) * 0.006 * bead * wave * f.dy(p.y) * _ss(0.0, 0.25, u) * (f.depth / 0.5)
        elif kind == 'lamp':
            dz += -0.07 * (f.depth / 0.5) * f.dy(p.y) * u
        q = V3((p.x + dx, p.y + dy, p.z + dz))
        v.co = inv @ q
    me.update()


def _rigid(ob, f, canted=False):
    """small parts (plate, lamps, grille, chrome) move as solid pieces: one shift per connected piece (the ink of the plate must stay on the plate)"""
    me = ob.data
    mw = ob.matrix_world
    inv = mw.inverted()
    bm = bmesh.new()
    bm.from_mesh(me)
    seen = set()
    for v0 in bm.verts:
        if v0.index in seen:
            continue
        comp, stack = [], [v0]
        seen.add(v0.index)
        while stack:
            v = stack.pop()
            comp.append(v)
            for e in v.link_edges:
                w = e.other_vert(v)
                if w.index not in seen:
                    seen.add(w.index)
                    stack.append(w)
        c = sum((mw @ v.co for v in comp), V3((0, 0, 0))) / len(comp)
        if c.x < f.x0:
            continue
        yb = 0.0 if abs(c.y) < 0.45 else math.copysign(0.7, c.y)       # pieces within 0.5 m of each other share one shift
        sh = f.shift(c.x, yb)
        dz = -0.05 * (f.depth / 0.5) * f.dy(yb) * f.u(c.x) ** 2
        ang = math.radians(9) * f.dy(c.y) * (f.depth / 0.5) * f.s if canted and abs(c.y - f.yc) < 0.45 else 0.0
        ca, sa = math.cos(ang), math.sin(ang)
        for v in comp:
            p = mw @ v.co - c
            q = V3((p.x * ca - p.z * sa, p.y, p.x * sa + p.z * ca)) + c + V3((-sh, 0.0, dz - (0.06 * f.dy(yb) if canted else 0.0)))
            v.co = inv @ q
    bm.to_mesh(me)
    bm.free()
    me.update()


def _tint(ob, f):
    """road dirt stays; the crushed zone darkens (soot, bare metal, oil), smoothly with the crush"""
    me = ob.data
    ca = me.color_attributes.get('Color')
    if ca is None:
        return
    mw = ob.matrix_world
    for lp in me.loops:
        p = mw @ me.vertices[lp.vertex_index].co
        w = f.dy(p.y) * f.u(p.x + f.shift(p.x, p.y)) ** 1.2
        k = 1.0 - 0.25 * w
        c = ca.data[lp.index].color
        ca.data[lp.index].color = (c[0] * k, c[1] * k, c[2] * k, c[3])


def crash_front(root, side=1, depth=0.5):
    import time
    t0 = time.time()
    f = Field(side, depth)
    bpy.context.view_layer.update()
    obs = {o.name: o for o in root.children_recursive if o.type == 'MESH'}
    for nm in ('Hood', 'Body', 'Bumper_F', 'Trim'):
        if nm in obs:
            subdivide_front(obs[nm], f.x0)
            print('CK subdivided', nm, len(obs[nm].data.vertices), round(time.time() - t0, 1), flush=True)
    for nm, o in obs.items():
        if nm == 'Hood':
            _deform(o, f, 'hood')
        elif nm in ('Body', 'Trim'):
            _deform(o, f, 'body')
        elif nm in ('Lamps_Head', 'Lamps_Park'):
            _rigid(o, f, canted=True)
        elif nm == 'Ends':
            _rigid(o, f)
        elif nm in ('Bumper_F', 'Engine', 'Underbody'):
            _deform(o, f, 'plain')
        if nm in ('Hood', 'Body', 'Bumper_F'):
            _tint(o, f)
    for nm, o in obs.items():
        o.data.update()
        if nm in ('Hood', 'Body', 'Bumper_F', 'Trim'):
            o.data.polygons.foreach_set('use_smooth', [True] * len(o.data.polygons))
    # the wheels: pushed back with the structure; the struck side turned
    for e in root.children:
        if e.name in ('Wheel_FL', 'Wheel_FR'):
            sgn = 1 if e.name.endswith('FL') else -1
            e.location.x -= f.shift(e.location.x, e.location.y) * 0.9
            if sgn == side:
                e.rotation_euler = (0.0, 0.0, math.radians(-16 * side))
    bpy.context.view_layer.update()
    return f
