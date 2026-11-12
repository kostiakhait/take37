# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Mesh-building helpers for the fuel tanker (runs inside Blender 4.2): materials (plain, library-textured, decal), the Mesh builder, empties, booleans, ray helpers, glb export.

Frame: origin on the ground at the middle of the tractor's wheelbase, nose +X, up +Z, left side +Y. (glb: Y up.)
"""
import json
import math
import pathlib

import bmesh
import bpy
from mathutils import Matrix, Vector

V3 = Vector
TEX = pathlib.Path('D:/temp/take37/tanker/tex')
SCRATCH = pathlib.Path('D:/temp/take37/tanker')
ATLAS = json.loads((TEX / 'atlas.json').read_text()) if (TEX / 'atlas.json').exists() else {}

# kind: (sRGB colour, metallic, roughness, extra). extra: lib=<library texture>, tile=<metres per repeat>, tint=<sRGB multiply>, tex=<file in TEX>, clip, trans, ior, coat
MATS = {
    # borrowed library textures
    'alu': ((255, 255, 255), 0.0, 0.0, {'lib': 'metal-steel', 'tile': 2.2, 'tint': (214, 217, 221), 'metal': 1.0, 'rough': 0.30}),     # the tank's aluminium: brushed, polished
    'frame': ((255, 255, 255), 0.0, 0.0, {'lib': 'metal-black', 'tile': 0.8, 'tint': (150, 150, 150)}),                                   # chassis steel, black painted and worn
    'stain': ((255, 255, 255), 0.0, 0.0, {'lib': 'metal-steel', 'tile': 0.6, 'tint': (150, 152, 156), 'metal': 1.0, 'rough': 0.28}),                      # stainless / heat shields
    'rust': ((255, 255, 255), 0.0, 0.0, {'lib': 'metal-rust', 'tile': 0.5, 'tint': (230, 230, 230)}),                                     # muffler heat shields
    'seat': ((255, 255, 255), 0.0, 0.6, {'lib': 'leather-brown', 'tile': 0.45, 'tint': (150, 125, 100)}),                                 # vinyl seat
    'fabric': ((255, 255, 255), 0.0, 0.95, {'lib': 'gray-fabric1', 'tile': 0.3, 'tint': (210, 205, 195)}),                                # door cards, headliner
    'cloth': ((255, 255, 255), 0.0, 0.95, {'lib': 'cloth-grey', 'tile': 0.3, 'tint': (110, 108, 104)}),                                   # floor mat
    'mud': ((255, 255, 255), 0.0, 0.0, {'lib': 'soil', 'tile': 0.4, 'tint': (110, 100, 85)}),                                             # mud inside the wheel arches and flaps
    # made for the game
    'paint': ((168, 22, 26), 0.0, 0.28, {'coat': 1.0, 'coat_rough': 0.05}),
    'paint_white': ((226, 226, 220), 0.0, 0.30, {'coat': 1.0, 'coat_rough': 0.05}),
    'paint_navy': ((20, 36, 84), 0.0, 0.30, {'coat': 1.0, 'coat_rough': 0.05}),
    'chrome': ((235, 235, 235), 1.0, 0.07, {}),
    'steel': ((150, 150, 154), 1.0, 0.42, {}),
    'steel_dark': ((70, 70, 74), 1.0, 0.5, {}),
    'alu_wheel': ((225, 226, 228), 1.0, 0.16, {}),
    'black': ((14, 14, 15), 0.0, 0.45, {}),
    'blackmat': ((18, 18, 18), 0.0, 0.85, {}),
    'rubber': ((20, 20, 20), 0.0, 0.85, {}),
    'tyre': ((24, 24, 24), 0.0, 0.88, {}),
    'hose': ((28, 28, 30), 0.0, 0.55, {}),
    'brass': ((196, 150, 62), 1.0, 0.3, {}),
    'valve_red': ((180, 25, 25), 0.0, 0.4, {}),
    'safety_yellow': ((230, 185, 20), 0.0, 0.5, {}),
    'glass': ((222, 238, 232), 0.0, 0.0, {'trans': 1.0, 'ior': 1.52}),
    'glass_tint': ((120, 150, 140), 0.0, 0.0, {'trans': 0.9, 'ior': 1.52}),
    'mirror': ((215, 220, 225), 1.0, 0.02, {}),
    'lens_clear': ((250, 250, 250), 0.0, 0.02, {'trans': 1.0, 'ior': 1.49}),
    'lens_amber': ((255, 135, 10), 0.0, 0.03, {'trans': 1.0, 'ior': 1.49}),
    'lens_red': ((215, 12, 10), 0.0, 0.03, {'trans': 1.0, 'ior': 1.49}),
    'reflector_red': ((200, 10, 10), 0.0, 0.1, {}),
    'reflector': ((210, 210, 210), 1.0, 0.12, {}),
    'bulb': ((250, 250, 245), 0.0, 0.05, {}),
    'seal': ((12, 12, 12), 0.0, 0.6, {}),
    'dash': ((30, 30, 32), 0.0, 0.55, {}),
    'gauge': ((8, 8, 10), 0.0, 0.2, {}),
    'interior': ((70, 66, 58), 0.0, 0.7, {}),
    'headliner': ((150, 145, 130), 0.0, 0.95, {}),
    'wood': ((92, 64, 40), 0.0, 0.5, {}),
    'cab_in': ((120, 25, 28), 0.0, 0.5, {}),
    'tape': ((255, 255, 255), 0.0, 0.3, {'tex': 'tape.png'}),
    'grime': ((255, 255, 255), 0.0, 0.9, {'tex': 'grime.png', 'blend': True}),
    'grime_mud': ((255, 255, 255), 0.0, 0.95, {'tex': 'grime_mud.png', 'blend': True}),
    'decal': ((255, 255, 255), 0.0, 0.45, {'tex': 'decals.png', 'clip': 0.5}),
    'plate_m': ((255, 255, 255), 0.0, 0.4, {'tex': 'decals.png', 'clip': 0.5}),
}
LIBK = {k for k, v in MATS.items() if 'lib' in v[3]}
_cache = {}


def lin(c):
    return tuple(((x / 255 + 0.055) / 1.055) ** 2.4 if x / 255 > 0.04045 else x / 255 / 12.92 for x in c)


def _img(path, srgb=True):
    p = str(path)
    for im in bpy.data.images:
        if im.filepath == p:
            return im
    im = bpy.data.images.load(p)
    im.colorspace_settings.name = 'sRGB' if srgb else 'Non-Color'
    return im


def mat(kind):
    name = 'M_' + kind
    if kind in _cache and name in bpy.data.materials:
        return bpy.data.materials[name]
    if name in bpy.data.materials:
        _cache[kind] = bpy.data.materials[name]
        return _cache[kind]
    c, met, rough, ex = MATS[kind]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*lin(c), 1)
    b.inputs['Metallic'].default_value = met
    b.inputs['Roughness'].default_value = rough
    if 'lib' in ex:
        n = ex['lib']
        base = nt.nodes.new('ShaderNodeTexImage')
        base.image = _img(TEX / f'{n}_base.png')
        out = base.outputs['Color']
        if 'tint' in ex:
            mx = nt.nodes.new('ShaderNodeMix')
            mx.data_type = 'RGBA'
            mx.blend_type = 'MULTIPLY'
            mx.inputs['Factor'].default_value = 1.0
            nt.links.new(out, mx.inputs['A'])
            mx.inputs['B'].default_value = (*lin(ex['tint']), 1)
            out = mx.outputs['Result']
        nt.links.new(out, b.inputs['Base Color'])
        if (TEX / f'{n}_normal.png').exists():
            nim = nt.nodes.new('ShaderNodeTexImage')
            nim.image = _img(TEX / f'{n}_normal.png', False)
            nm = nt.nodes.new('ShaderNodeNormalMap')
            nt.links.new(nim.outputs['Color'], nm.inputs['Color'])
            nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
        if (TEX / f'{n}_orm.png').exists():
            oim = nt.nodes.new('ShaderNodeTexImage')
            oim.image = _img(TEX / f'{n}_orm.png', False)
            sp = nt.nodes.new('ShaderNodeSeparateColor')
            nt.links.new(oim.outputs['Color'], sp.inputs['Color'])
            nt.links.new(sp.outputs['Green'], b.inputs['Roughness'])
            nt.links.new(sp.outputs['Blue'], b.inputs['Metallic'])
        else:
            b.inputs['Metallic'].default_value = ex.get('metal', 0.0)
            b.inputs['Roughness'].default_value = ex.get('rough', rough)
    if 'tex' in ex:
        im = nt.nodes.new('ShaderNodeTexImage')
        im.image = _img(TEX / ex['tex'])
        nt.links.new(im.outputs['Color'], b.inputs['Base Color'])
        if ex.get('blend'):
            nt.links.new(im.outputs['Alpha'], b.inputs['Alpha'])
            m.blend_method = 'BLEND'
            if hasattr(m, 'surface_render_method'):
                m.surface_render_method = 'BLENDED'
        if 'clip' in ex:
            nt.links.new(im.outputs['Alpha'], b.inputs['Alpha'])
            m.blend_method = 'CLIP'
            m.alpha_threshold = ex['clip']
            if hasattr(m, 'surface_render_method'):
                m.surface_render_method = 'DITHERED'
    if 'trans' in ex:
        b.inputs['Transmission Weight'].default_value = ex['trans']
        b.inputs['IOR'].default_value = ex.get('ior', 1.5)
    if 'coat' in ex:
        b.inputs['Coat Weight'].default_value = ex['coat']
        b.inputs['Coat Roughness'].default_value = ex['coat_rough']
    _cache[kind] = m
    return m


# ---- mesh building -------------------------------------------------------------------------------------------------------------------------------------------------------------
class Mesh:
    def __init__(self, custom_uv=()):
        self.bm = bmesh.new()
        self.uvl = self.bm.loops.layers.uv.new('UVMap')
        self.kinds = []
        self.custom = set(custom_uv) | {'decal', 'tape', 'plate_m', 'grime', 'grime_mud'}

    def mi(self, kind):
        if kind not in self.kinds:
            self.kinds.append(kind)
        return self.kinds.index(kind)

    def face(self, vs, kind, uvs=None):
        try:
            f = self.bm.faces.new(vs)
        except ValueError:
            return None
        f.material_index = self.mi(kind)
        if uvs:
            for lp, uv in zip(f.loops, uvs):
                lp[self.uvl].uv = uv
        return f

    def loft(self, rings, kind, closed=True, caps=False, loop=False):
        vs = [[self.bm.verts.new(p) for p in r] for r in rings]
        n = len(rings[0])
        m = n if closed else n - 1
        pairs = list(zip(vs, vs[1:])) + ([(vs[-1], vs[0])] if loop else [])
        for ra, rb in pairs:
            for k in range(m):
                self.face((ra[k], ra[(k + 1) % n], rb[(k + 1) % n], rb[k]), kind)
        if caps:
            self.face(list(reversed(vs[0])), kind)
            self.face(vs[-1], kind)
        return vs

    def grid(self, rows, kind):
        return self.loft(rows, kind, closed=False)

    def tube(self, path, r, kind, seg=8, cap=True, loop=False):
        rings = []
        n = len(path)
        for i, p in enumerate(path):
            a = path[(i + 1) % n] if loop else path[min(i + 1, n - 1)]
            b = path[(i - 1) % n] if loop else path[max(i - 1, 0)]
            t = (a - b).normalized()
            up = V3((0, 0, 1)) if abs(t.z) < 0.9 else V3((1, 0, 0))
            u = t.cross(up).normalized()
            w = t.cross(u).normalized()
            rr = r[i] if isinstance(r, (list, tuple)) else r
            rings.append([p + (u * math.cos(2 * math.pi * k / seg) + w * math.sin(2 * math.pi * k / seg)) * rr for k in range(seg)])
        return self.loft(rings, kind, caps=cap and not loop, loop=loop)

    def cyl(self, p0, p1, r, kind, seg=16, cap=True, r1=None):
        return self.tube([V3(p0), V3(p1)], [r, r if r1 is None else r1], kind, seg=seg, cap=cap)

    def box(self, c, size, kind, axes=None):
        self.rbox(c, size, 0.0, kind, axes)

    def rbox(self, c, size, r, kind, axes=None, seg=2):
        ex, ey, ez = axes or (V3((1, 0, 0)), V3((0, 1, 0)), V3((0, 0, 1)))
        M = Matrix(((ex.x * size[0], ey.x * size[1], ez.x * size[2], c[0]), (ex.y * size[0], ey.y * size[1], ez.y * size[2], c[1]),
                    (ex.z * size[0], ey.z * size[1], ez.z * size[2], c[2]), (0, 0, 0, 1)))
        tmp = bmesh.new()
        bmesh.ops.create_cube(tmp, size=1.0, matrix=M)
        if r > 0:
            bmesh.ops.bevel(tmp, geom=list(tmp.edges) + list(tmp.verts), offset=min(r, 0.49 * min(size)), offset_type='OFFSET', segments=seg, profile=0.5, affect='EDGES',
                            clamp_overlap=True)
        self.merge(tmp, kind)

    def merge(self, tmp, kind):
        mi = self.mi(kind)
        vmap = {v: self.bm.verts.new(v.co) for v in tmp.verts}
        for f in tmp.faces:
            try:
                nf = self.bm.faces.new([vmap[v] for v in f.verts])
                nf.material_index = mi
            except ValueError:
                pass
        tmp.free()

    def disc(self, c, normal, r, kind, seg=24):
        n = V3(normal).normalized()
        up = V3((0, 0, 1)) if abs(n.z) < 0.9 else V3((1, 0, 0))
        u = n.cross(up).normalized()
        w = n.cross(u).normalized()
        self.face([self.bm.verts.new(V3(c) + (u * math.cos(2 * math.pi * k / seg) + w * math.sin(2 * math.pi * k / seg)) * r) for k in range(seg)], kind)

    def prism(self, poly, axis_a, axis_b, extrude_axis, lo, hi, kind):
        """A solid: polygon given as (a, b) pairs in two axes ('xyz' indexes), extruded along the third from lo to hi."""
        vs0, vs1 = [], []
        for pa, pb in poly:
            p0, p1 = [0, 0, 0], [0, 0, 0]
            p0[axis_a] = p1[axis_a] = pa
            p0[axis_b] = p1[axis_b] = pb
            p0[extrude_axis], p1[extrude_axis] = lo, hi
            vs0.append(self.bm.verts.new(p0))
            vs1.append(self.bm.verts.new(p1))
        n = len(poly)
        for k in range(n):
            self.face((vs0[k], vs0[(k + 1) % n], vs1[(k + 1) % n], vs1[k]), kind)
        self.face(list(reversed(vs0)), kind)
        self.face(vs1, kind)

    def decal(self, name, c, ex, ey, w, h, kind='decal', nrm=None, lift=0.0, flip=False):
        """A flat decal quad of the livery sheet rectangle `name`, centred at c, ex along its width, ey up its height (the sheet's rectangle is drawn with y down)."""
        x, y, rw, rh = ATLAS[name]
        S = 2048.0
        u0, u1 = x / S, (x + rw) / S
        v0, v1 = 1 - (y + rh) / S, 1 - y / S
        ex, ey = V3(ex).normalized(), V3(ey).normalized()
        n = V3(nrm) if nrm is not None else ex.cross(ey)
        c = V3(c) + n.normalized() * lift
        pts = [c - ex * (w / 2) - ey * (h / 2), c + ex * (w / 2) - ey * (h / 2), c + ex * (w / 2) + ey * (h / 2), c - ex * (w / 2) + ey * (h / 2)]
        uvs = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
        if flip:
            pts = list(reversed(pts))
            uvs = list(reversed(uvs))
        self.face([self.bm.verts.new(p) for p in pts], kind, uvs)

    def tape(self, p0, p1, width, lift_n, kind='tape'):
        """A strip of conspicuity tape from p0 to p1 (width across, offset along lift_n) with the tile repeating every 0.30 m."""
        p0, p1, ln = V3(p0), V3(p1), V3(lift_n).normalized()
        t = (p1 - p0)
        L = t.length
        t.normalize()
        wv = t.cross(ln).normalized() * (width / 2)
        a = [p0 - wv + ln * 0.002, p0 + wv + ln * 0.002, p1 + wv + ln * 0.002, p1 - wv + ln * 0.002]
        u = L / 0.30
        self.face([self.bm.verts.new(p) for p in a], kind, [(0, 0), (0, 1), (u, 1), (u, 0)])

    def finish(self, name, parent=None, sharp=35.0, origin=None, box_uv=True):
        bm = self.bm
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
        bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if self.kinds[f.material_index] not in ('decal', 'tape', 'plate_m', 'grime', 'grime_mud')])
        if box_uv:
            for f in bm.faces:
                k = self.kinds[f.material_index]
                if k in LIBK and k not in self.custom:
                    tile = MATS[k][3]['tile']
                    n = f.normal
                    ax = max(range(3), key=lambda i: abs(n[i]))
                    a, b = [(1, 2), (0, 2), (0, 1)][ax]
                    for lp in f.loops:
                        co = lp.vert.co
                        lp[self.uvl].uv = (co[a] / tile, co[b] / tile)
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        for k in self.kinds:
            me.materials.append(mat(k))
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        po = V3(parent.matrix_world.translation) if parent is not None else V3((0, 0, 0))
        org = V3(origin) if origin is not None else po
        me.transform(Matrix.Translation(-org))
        ob.location = org - po
        if parent is not None:
            ob.parent = parent
        smooth(ob, sharp)
        return ob


def smooth(ob, angle):
    with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle))


def empty(name, loc=(0, 0, 0), parent=None):
    """An empty at the WORLD point loc (the model's frame), child of parent (parents carry no rotation at build time)."""
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    po = V3(parent.matrix_world.translation) if parent is not None else V3((0, 0, 0))
    e.location = V3(loc) - po
    if parent is not None:
        e.parent = parent
    bpy.context.view_layer.update()
    return e


def find(name):
    return bpy.data.objects[name]


def boolean(ob, cutters, op, solver='EXACT'):
    col = bpy.data.collections.new('cutters_' + op)
    bpy.context.scene.collection.children.link(col)
    for c in cutters:
        col.objects.link(c)
        c.hide_render = True
    md = ob.modifiers.new('bool', 'BOOLEAN')
    md.operation = op
    md.solver = solver
    md.operand_type = 'COLLECTION'
    md.collection = col
    if solver == 'EXACT':
        md.material_mode = 'TRANSFER'
        md.use_hole_tolerant = True
    with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
        bpy.ops.object.modifier_apply(modifier=md.name)
    for c in cutters:
        bpy.data.objects.remove(c, do_unlink=True)
    bpy.data.collections.remove(col)


def temp_solid(name, mesh_fn, kind='black'):
    """A temporary object (boolean operand) from a Mesh-filling function."""
    m = Mesh()
    mesh_fn(m)
    ob = m.finish(name, box_uv=False)
    return ob


def chaikin(pts, it=2):
    for _ in range(it):
        out = [pts[0]]
        for (ay, az), (by, bz) in zip(pts, pts[1:]):
            out.append((0.75 * ay + 0.25 * by, 0.75 * az + 0.25 * bz))
            out.append((0.25 * ay + 0.75 * by, 0.25 * az + 0.75 * bz))
        out.append(pts[-1])
        pts = out
    return pts


def save(stage):
    p = SCRATCH / 'blend' / f'tanker_{stage}.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(p))
    return p


def log(*a):
    import time
    print(time.strftime('[%H:%M:%S]'), *a, flush=True)
