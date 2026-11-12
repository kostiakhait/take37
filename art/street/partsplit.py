# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Splits a building into its shell and the parts that break (shop window panes, the door, the transom, the sign board, the awning).

`Router` stands in for the builder `m` of buildings.make_building: geometry made inside `with m.part('tag'):` goes to a mesh of its own, the rest to the shell. The code of the building is the same,
so the shell plus the parts are exactly the building that the street has, with the same random numbers. `cut` slices a part along the street into sections (a window pane per mullion bay,
the awning every few metres) so that a car or a blast breaks the pane it meets, not the whole shop front.
"""
import bmesh
import bpy
from mathutils import Matrix

import kitlib as K

LAST = {}          # the parts of the last split building: tag -> MB (not yet built)


class Router:
    def __init__(self, base):
        self.base = base
        self.parts = {}
        self.tag = None

    def _mb(self, tag):
        if tag is None:
            return self.base
        mb = self.parts.get(tag)
        if mb is None:
            b = self.base
            mb = K.MB(f'{b.name}_{tag}', b.seed)
            mb.uvo = b.uvo
            mb.tone = b.tone
            mb.T = Matrix(b.T)
            mb.stack = [Matrix(t) for t in b.stack]
            self.parts[tag] = mb
        return mb

    def part(self, tag):
        r = self

        class _Ctx:
            def __enter__(s):
                s.old = r.tag
                r.tag = tag

            def __exit__(s, *a):
                r.tag = s.old
        return _Ctx()

    def push(self, m):
        for mb in [self.base] + list(self.parts.values()):
            mb.push(m)

    def pop(self):
        for mb in [self.base] + list(self.parts.values()):
            mb.pop()

    def at(self, *a, **k):
        for mb in [self.base] + list(self.parts.values()):
            mb.at(*a, **k)
        return self

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.pop()

    def __getattr__(self, name):
        return getattr(self._mb(self.tag), name)

    def build(self, name=None, collection=None, parent=None, loc=(0, 0, 0), props=None):
        LAST.clear()
        LAST.update(self.parts)
        return self.base.build(name, collection, parent, loc, props)


def cut(mb, bounds, axis=1):
    """Slice the geometry of a part builder at the coordinates `bounds` along `axis` and give back one list of faces per section (by the centre of the face): [(lo, hi, bmesh copy)]."""
    bm = mb.bm
    for c in bounds:
        no = [0, 0, 0]
        no[axis] = 1
        co = [0, 0, 0]
        co[axis] = c
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no, clear_inner=False, clear_outer=False)
    edges = [-1e9] + list(bounds) + [1e9]
    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        b2 = bm.copy()
        kill = [f for f in b2.faces if not (lo <= sum(v.co[axis] for v in f.verts) / len(f.verts) < hi)]
        bmesh.ops.delete(b2, geom=kill, context='FACES')
        loose = [v for v in b2.verts if not v.link_faces]
        bmesh.ops.delete(b2, geom=loose, context='VERTS')
        if b2.faces:
            out.append((lo, hi, b2))
        else:
            b2.free()
    return out


def to_object(bm, slots, name, collection=None, parent=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for s in slots:
        me.materials.append(K.mat(s))
    o = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(o)
    if parent is not None:
        o.parent = parent
    return o
