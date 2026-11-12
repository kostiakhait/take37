# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Shared Blender helpers for the TAKE 37 street kit and gas station (Blender 4.2, headless).

Frame: street runs along +X, left side +Y, up +Z, origin on the ground (glb: Y up). Materials come from textures_prep.py's output ($TAKE37_TEX, default D:/temp/take37/street/tex).
MB is a small mesh builder (welded vertices, box-projected UVs in metres, chamfered boxes, lathes, extrusions, tubes, per-corner tone for weathering).
"""
import hashlib
import json
import math
import os
import pathlib

import bmesh
import bpy
from mathutils import Matrix, Vector, noise

TEX = pathlib.Path(os.environ.get('TAKE37_TEX', 'D:/temp/take37/street/tex'))
V = Vector

# ---- materials -------------------------------------------------------------------------------------------------------------------------------------------------------
# name: dict(tex=<texture id>, tile=metres per texture repeat, rough/metal when the texture has no ORM, mode=OPAQUE|BLEND|CLIP, color=sRGB tuple for texture-less, emit=(rgb, strength))
MATS = {
    'asphalt': dict(tex='asphalt', tile=2.6), 'asphalt_worn': dict(tex='asphalt_worn', tile=3.1, rough=0.85, nrm='asphalt'),
    'sidewalk': dict(tex='sidewalk', tile=1.5), 'kerb': dict(tex='concrete_found', tile=0.9), 'concrete': dict(tex='concrete_found', tile=1.2),
    'brick_red': dict(tex='brick_red', tile=0.75), 'brick_brown': dict(tex='brick_brown', tile=0.75), 'brick_buff': dict(tex='brick_buff', tile=0.75), 'brick_old': dict(tex='brick_old', tile=1.0),
    'plaster_cream': dict(tex='plaster_cream', tile=2.0), 'plaster_sage': dict(tex='plaster_sage', tile=2.0), 'plaster_grey': dict(tex='plaster_grey', tile=2.0),
    'plaster_rose': dict(tex='plaster_rose', tile=2.0), 'plaster_white': dict(tex='plaster_white', tile=2.0), 'trim_white': dict(tex='trim_white', tile=1.0),
    'clap_white': dict(tex='clap_white', tile=1.2, nrm='clap'), 'clap_cream': dict(tex='clap_cream', tile=1.2, nrm='clap'), 'clap_blue': dict(tex='clap_blue', tile=1.2, nrm='clap'),
    'clap_sage': dict(tex='clap_sage', tile=1.2, nrm='clap'), 'clap_yellow': dict(tex='clap_yellow', tile=1.2, nrm='clap'), 'clap_grey': dict(tex='clap_grey', tile=1.2, nrm='clap'),
    'clap_red': dict(tex='clap_red', tile=1.2, nrm='clap'),
    'wood_pine': dict(tex='wood_pine', tile=1.0), 'wood_brown': dict(tex='wood_brown', tile=1.0), 'wood_dark': dict(tex='wood_dark', tile=1.0), 'wood_oak': dict(tex='wood_oak', tile=1.0),
    'wood_blue': dict(tex='wood_blue', tile=1.0), 'bark': dict(tex='bark', tile=1.0, rough=0.95), 'bark2': dict(tex='bark2', tile=1.0, rough=0.95),
    'grass': dict(tex='grass', tile=1.5), 'verge': dict(tex='verge', tile=1.5, rough=0.95), 'soil': dict(tex='soil', tile=1.0), 'slate': dict(tex='slate', tile=1.0),
    'steel': dict(tex='steel', tile=1.0), 'rust': dict(tex='rust', tile=1.0, rough=0.8, metal=0.6), 'black_metal': dict(tex='black_metal', tile=1.0),
    'paint_green': dict(tex='paint_green', tile=1.0), 'paint_grey': dict(tex='paint_grey', tile=1.0), 'paint_dark': dict(tex='paint_dark', tile=1.0), 'paint_red': dict(tex='paint_red', tile=1.0),
    'paint_blue': dict(tex='paint_blue', tile=1.0), 'paint_yellow': dict(tex='paint_yellow', tile=1.0), 'paint_white': dict(tex='paint_white', tile=1.0), 'paint_orange': dict(tex='paint_orange', tile=1.0),
    'paint_cream': dict(tex='paint_cream', tile=1.0), 'paint_sage': dict(tex='paint_sage', tile=1.0),
    'awn_red': dict(tex='awn_red', tile=0.5), 'awn_green': dict(tex='awn_green', tile=0.5), 'awn_navy': dict(tex='awn_navy', tile=0.5), 'awn_cream': dict(tex='awn_cream', tile=0.5),
    'awn_gold': dict(tex='awn_gold', tile=0.5), 'awn_burg': dict(tex='awn_burg', tile=0.5), 'awn_white': dict(tex='awn_white', tile=0.5),
    'line_white': dict(tex='line_white', tile=1.0, mode='BLEND', rough=0.6, uv='explicit'), 'line_yellow': dict(tex='line_yellow', tile=1.0, mode='BLEND', rough=0.6, uv='explicit'),
    'decals': dict(tex='decals', tile=1.0, mode='BLEND', rough=0.8, uv='explicit'), 'signs': dict(tex='signs', tile=1.0, mode='CLIP', rough=0.35, metal=0.0, uv='explicit'),
    'shopsigns': dict(tex='shopsigns', tile=1.0, rough=0.4, uv='explicit'), 'interiors': dict(tex='interiors', tile=1.0, rough=0.9, uv='explicit', emit=((255, 255, 255), 0.5, 'tex')),
    'leaves': dict(tex='leaves', tile=1.0, mode='CLIP', rough=0.8, uv='explicit'),
    'leaf_maple': dict(tex='leaf_maple', tile=1.0, mode='CLIP', rough=0.6, uv='explicit', emit=((255, 255, 255), 0.07, 'tex')), 'leaf_elm': dict(tex='leaf_elm', tile=1.0, mode='CLIP', rough=0.6, uv='explicit', emit=((255, 255, 255), 0.07, 'tex')),
    'leaf_oak': dict(tex='leaf_oak', tile=1.0, mode='CLIP', rough=0.6, uv='explicit', emit=((255, 255, 255), 0.07, 'tex')),
    'leaf_maple_a': dict(tex='leaf_maple_a', tile=1.0, mode='CLIP', rough=0.6, uv='explicit', emit=((255, 255, 255), 0.07, 'tex')), 'leaf_elm_a': dict(tex='leaf_elm_a', tile=1.0, mode='CLIP', rough=0.6, uv='explicit', emit=((255, 255, 255), 0.07, 'tex')),
    'leaf_oak_a': dict(tex='leaf_oak_a', tile=1.0, mode='CLIP', rough=0.6, uv='explicit', emit=((255, 255, 255), 0.07, 'tex')),
    'glass_shop': dict(color=(205, 220, 225), rough=0.1, metal=0.0, alpha=0.07, mode='BLEND', ior=1.5),
    'shopwall': dict(color=(228, 218, 192), rough=0.8, metal=0.0, emit=((228, 218, 192), 0.9)),
    'shopfloor': dict(color=(168, 140, 100), rough=0.5, metal=0.0, emit=((168, 140, 100), 0.6)),
    'redband': dict(color=(120, 8, 14), rough=0.4, metal=0.0),
    'glass': dict(color=(170, 195, 205), rough=0.04, metal=0.0, alpha=0.22, mode='BLEND', ior=1.5),
    'glass_tint': dict(color=(24, 34, 44), rough=0.05, metal=0.0, alpha=0.34, mode='BLEND', ior=1.5),        # tinted shop glass: the room behind reads dark and deep at a distance
    'glass_shade': dict(color=(4, 5, 8), rough=0.5, metal=0.0, alpha=0.5, mode='BLEND'),                    # the shade under the lintel and awning at the top of the pane
    'glass_refl': dict(color=(214, 230, 244), rough=0.03, metal=0.0, alpha=0.2, mode='BLEND', ior=1.5),     # sky reflection streaks on the pane
    'glass_dirty': dict(color=(160, 175, 180), rough=0.2, metal=0.0, alpha=0.42, mode='BLEND', ior=1.5),
    'rubber': dict(color=(24, 24, 24), rough=0.85, metal=0.0), 'tar': dict(color=(78, 75, 70), rough=0.92, metal=0.0),
    'lamp_glass': dict(color=(255, 240, 200), rough=0.1, metal=0.0, alpha=0.6, mode='BLEND', emit=((255, 230, 170), 1.2)),
    'red_lens': dict(color=(210, 20, 20), rough=0.1, metal=0.0, emit=((255, 20, 10), 0.4)), 'amber_lens': dict(color=(240, 160, 10), rough=0.1, metal=0.0, emit=((255, 150, 0), 0.4)),
    'green_lens': dict(color=(20, 180, 90), rough=0.1, metal=0.0, emit=((20, 255, 110), 0.4)),
    'chrome': dict(color=(220, 222, 225), rough=0.12, metal=1.0), 'cable': dict(color=(14, 14, 14), rough=0.7, metal=0.0),
    'white_plastic': dict(color=(228, 228, 224), rough=0.35, metal=0.0, tex=None), 'sun_paper': dict(color=(230, 215, 150), rough=0.9, metal=0.0),
    'pumpface': dict(tex='pumpface', tile=1.0, rough=0.3, uv='explicit'), 'pumphead': dict(tex='pumphead', tile=1.0, rough=0.35, uv='explicit', emit=((255, 255, 255), 0.2, 'tex')),
    'pricesign': dict(tex='pricesign', tile=1.0, rough=0.35, uv='explicit', emit=((255, 255, 255), 0.12, 'tex')), 'shopfascia': dict(tex='shopfascia', tile=1.0, rough=0.35, uv='explicit', emit=((255, 255, 255), 0.15, 'tex')),
    'decor': dict(tex='decor', tile=1.0, mode='CLIP', rough=0.4, uv='explicit'), 'oilcan': dict(tex='oilcan', tile=1.0, rough=0.4, uv='explicit'),
    'goods': dict(tex='paint_white', tile=1.0, rough=0.5, metal=0.0), 'fluor': dict(color=(255, 252, 240), rough=0.3, metal=0.0, emit=((255, 250, 235), 3.0)),
    'flame': dict(color=(255, 120, 20), rough=1.0, metal=0.0, emit=((255, 110, 20), 8.0)),
}
# ---- interiors, wall art, litter (textures_detail.py); interior surfaces carry a little emission of their own so that the room reads as lit without any light probes -----------------
_E = lambda s: ((255, 255, 255), s, 'tex')  # noqa: E731
MATS.update({
    'shelfgoods': dict(tex='goods', tile=1.0, rough=0.55, uv='explicit', emit=_E(0.5)),
    'wincontent': dict(tex='wincontent', tile=1.0, rough=0.9, uv='explicit', emit=_E(0.35)),
    'windecals': dict(tex='windecals', tile=1.0, mode='BLEND', rough=0.3, uv='explicit', emit=_E(0.5)),
    'wallart': dict(tex='wallart', tile=1.0, mode='BLEND', rough=0.9, uv='explicit'),
    'litter': dict(tex='litter', tile=1.0, mode='BLEND', rough=0.85, uv='explicit'),
    'puddle': dict(tex='puddle', tile=1.0, mode='BLEND', rough=0.03, uv='explicit'),
    'floor_tile': dict(tex='floor_tile', tile=2.4, rough=0.35, emit=_E(0.35)), 'floor_tile2': dict(tex='floor_tile2', tile=2.4, rough=0.35, emit=_E(0.35)),
    'int_cream': dict(tex='plaster_cream', tile=2.0, emit=_E(0.4)), 'int_sage': dict(tex='plaster_sage', tile=2.0, emit=_E(0.4)), 'int_rose': dict(tex='plaster_rose', tile=2.0, emit=_E(0.4)),
    'int_grey': dict(tex='plaster_grey', tile=2.0, emit=_E(0.4)), 'int_ceil': dict(tex='plaster_white', tile=2.0, emit=_E(0.45)),
    'int_oak': dict(tex='wood_oak', tile=1.0, emit=_E(0.3)), 'int_dark': dict(tex='wood_dark', tile=1.0, emit=_E(0.3)), 'int_brown': dict(tex='wood_brown', tile=1.0, emit=_E(0.3)),
    'int_pine': dict(tex='wood_pine', tile=1.0, emit=_E(0.3)),
    'formica': dict(color=(226, 222, 208), rough=0.3, metal=0.0, emit=((226, 222, 208), 0.25)), 'velvet': dict(color=(70, 22, 34), rough=0.95, metal=0.0, emit=((70, 22, 34), 0.2)),
    'leather': dict(color=(110, 40, 30), rough=0.5, metal=0.0, emit=((110, 40, 30), 0.15)), 'fabric_blue': dict(color=(70, 90, 130), rough=0.9, metal=0.0, emit=((70, 90, 130), 0.2)),
    'fabric_green': dict(color=(80, 110, 80), rough=0.9, metal=0.0, emit=((80, 110, 80), 0.2)), 'fabric_ochre': dict(color=(190, 150, 70), rough=0.9, metal=0.0, emit=((190, 150, 70), 0.2)),
    'mirror': dict(color=(205, 210, 215), rough=0.03, metal=1.0), 'fluor_int': dict(color=(255, 250, 235), rough=0.3, metal=0.0, emit=((255, 246, 225), 4.0)),
    'tvscreen': dict(color=(120, 160, 210), rough=0.1, metal=0.0, emit=((140, 180, 255), 1.6)), 'brass': dict(color=(200, 160, 70), rough=0.25, metal=1.0),
    'gold': dict(color=(240, 195, 80), rough=0.2, metal=1.0), 'plant': dict(color=(50, 100, 45), rough=0.8, metal=0.0, emit=((50, 100, 45), 0.2)),
    'petal_red': dict(color=(200, 40, 50), rough=0.7, metal=0.0, emit=((200, 40, 50), 0.2)), 'petal_yellow': dict(color=(240, 200, 50), rough=0.7, metal=0.0, emit=((240, 200, 50), 0.2)),
    'petal_pink': dict(color=(235, 130, 170), rough=0.7, metal=0.0, emit=((235, 130, 170), 0.2)), 'petal_white': dict(color=(240, 238, 230), rough=0.7, metal=0.0, emit=((240, 238, 230), 0.2)),
    'enamel_white': dict(color=(238, 238, 234), rough=0.25, metal=0.0, emit=((238, 238, 234), 0.25)), 'lampshade': dict(color=(250, 225, 170), rough=0.8, metal=0.0, emit=((255, 225, 160), 1.2)),
    'rug_red': dict(color=(120, 40, 40), rough=1.0, metal=0.0, emit=((120, 40, 40), 0.2)), 'poster_int': dict(tex='windecals', tile=1.0, rough=0.5, uv='explicit', emit=_E(0.4)),
})

for _k, _v in MATS.items():                  # painted metals: a quieter bump, larger repeat
    if _k.startswith('paint_') or _k in ('steel', 'black_metal'):
        _v.setdefault('nstr', 0.3)
        _v['tile'] = 2.2
    if _k.startswith('paint_') or _k == 'black_metal':          # painted sheet metal is a dielectric; the library's steel ORM would make it a mirror
        _v['rough'] = 0.42 if _k.startswith('paint_') else 0.5
        _v['metal'] = 0.0
MATS['sidewalk']['tile'] = 1.65
TILE = {k: v.get('tile', 1.0) for k, v in MATS.items()}
EXPLICIT = {k for k, v in MATS.items() if v.get('uv') == 'explicit'}
_mats, _imgs = {}, {}


def lin(c):
    return tuple((x / 255.0) ** 2.2 for x in c)


def _img(file, nc=False):
    p = TEX / file
    if not p.exists():
        return None
    h = hashlib.md5(p.read_bytes()).hexdigest()
    if (h, nc) in _imgs:
        return _imgs[(h, nc)]
    im = bpy.data.images.load(str(p))
    im.name = p.stem
    im.colorspace_settings.name = 'Non-Color' if nc else 'sRGB'
    _imgs[(h, nc)] = im
    return im


def mat(name, extra=None):
    if name in _mats:
        return _mats[name]
    sp = MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.name != 'Material Output':
            nt.nodes.remove(n)
    out = nt.nodes['Material Output']
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    tex = sp.get('tex')
    base_src = None
    if tex:
        ci = _img(f'{tex}_c.png')
        tn = nt.nodes.new('ShaderNodeTexImage')
        tn.image = ci
        tn.interpolation = 'Smart'
        base_src = tn.outputs['Color']
        vc = nt.nodes.new('ShaderNodeVertexColor')          # per-corner tone: weathering and macro variation against tiling
        vc.layer_name = 'Color'
        mx = nt.nodes.new('ShaderNodeMix')
        mx.data_type = 'RGBA'
        mx.blend_type = 'MULTIPLY'
        mx.inputs[0].default_value = 1.0
        nt.links.new(base_src, mx.inputs[6])
        nt.links.new(vc.outputs['Color'], mx.inputs[7])
        nt.links.new(mx.outputs[2], b.inputs['Base Color'])
        if sp.get('mode') in ('BLEND', 'CLIP'):
            nt.links.new(tn.outputs['Alpha'], b.inputs['Alpha'])
        nsrc = sp.get('nrm', tex)
        ni = _img(f'{nsrc}_n.png', True)
        if ni:
            nn = nt.nodes.new('ShaderNodeTexImage')
            nn.image = ni
            nm = nt.nodes.new('ShaderNodeNormalMap')
            nm.inputs['Strength'].default_value = sp.get('nstr', 1.0)
            nt.links.new(nn.outputs['Color'], nm.inputs['Color'])
            nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
        oi = _img(f'{nsrc}_orm.png', True) if 'rough' not in sp else None
        if oi:
            on = nt.nodes.new('ShaderNodeTexImage')
            on.image = oi
            sep = nt.nodes.new('ShaderNodeSeparateColor')
            nt.links.new(on.outputs['Color'], sep.inputs['Color'])
            nt.links.new(sep.outputs['Green'], b.inputs['Roughness'])
            nt.links.new(sep.outputs['Blue'], b.inputs['Metallic'])
        else:
            b.inputs['Roughness'].default_value = sp.get('rough', 0.8)
            b.inputs['Metallic'].default_value = sp.get('metal', 0.0)
    else:
        b.inputs['Base Color'].default_value = lin(sp['color']) + (1,)
        b.inputs['Roughness'].default_value = sp.get('rough', 0.6)
        b.inputs['Metallic'].default_value = sp.get('metal', 0.0)
        if 'alpha' in sp:
            b.inputs['Alpha'].default_value = sp['alpha']
        if 'ior' in sp:
            b.inputs['IOR'].default_value = sp['ior']
    if 'emit' in sp:
        e = sp['emit']
        if len(e) > 2 and base_src is not None:
            nt.links.new(base_src, b.inputs['Emission Color'])
        else:
            b.inputs['Emission Color'].default_value = lin(e[0]) + (1,)
        b.inputs['Emission Strength'].default_value = e[1]
    m.blend_method = sp.get('mode', 'OPAQUE') if sp.get('mode') in ('BLEND', 'CLIP') else 'OPAQUE'
    if m.blend_method == 'CLIP':
        m.alpha_threshold = 0.5
    m.use_backface_culling = sp.get('mode') != 'CLIP' and sp.get('mode') != 'BLEND'
    if sp.get('mode') == 'CLIP':
        m.use_backface_culling = False
    _mats[name] = m
    return m


# ---- scene ------------------------------------------------------------------------------------------------------------------------------------------------------------
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _mats.clear()
    _imgs.clear()


def coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def empty(name, loc=(0, 0, 0), rot=(0, 0, 0), parent=None, props=None, collection=None, size=0.3):
    o = bpy.data.objects.new(name, None)
    o.empty_display_size = size
    o.location = loc
    o.rotation_euler = rot
    (collection or bpy.context.scene.collection).objects.link(o)
    if parent is not None:
        o.parent = parent
    for k, v in (props or {}).items():
        o[k] = v
    return o


def dup(obj, name, loc=(0, 0, 0), rot=(0, 0, 0), parent=None, collection=None, scale=(1, 1, 1)):
    """Linked duplicate: same mesh data, so the glb stores the mesh once."""
    o = bpy.data.objects.new(name, obj.data)
    o.location, o.rotation_euler, o.scale = loc, rot, scale
    (collection or bpy.context.scene.collection).objects.link(o)
    if parent is not None:
        o.parent = parent
    for k in obj.keys():
        o[k] = obj[k]
    return o


def tris(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons) if obj.type == 'MESH' else 0


def bbox(objs):
    pts = []
    for o in objs:
        if o.type == 'MESH':
            pts += [o.matrix_world @ V(c) for c in o.bound_box]
    if not pts:
        return None
    return V(min(p.x for p in pts) for _ in [0]) if False else (V((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))), V((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))))


def export_glb(objs, path, jpeg=True):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True, export_yup=True, export_apply=False, export_extras=True, export_cameras=False,
                              export_lights=False, export_image_format='JPEG' if jpeg else 'AUTO', export_jpeg_quality=86, export_texcoords=True, export_normals=True,
                              export_materials='EXPORT', export_vertex_color='ACTIVE', export_active_vertex_color_when_no_material=True, export_animations=False,
                              export_attributes=True)


def descendants(root):
    out = [root]
    for c in root.children_recursive:
        out.append(c)
    return out


# ---- mesh builder -------------------------------------------------------------------------------------------------------------------------------------------------
def newell(P):
    n = V((0, 0, 0))
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        n += V(((a.y - b.y) * (a.z + b.z), (a.z - b.z) * (a.x + b.x), (a.x - b.x) * (a.y + b.y)))
    return n


class MB:
    def __init__(self, name, seed=0, uvshift=True):
        self.name = name
        self.bm = bmesh.new()
        self.uvl = self.bm.loops.layers.uv.new('UVMap')
        self.cl = self.bm.loops.layers.color.new('Color')
        self.slots, self.vmap = [], {}
        self.T = Matrix.Identity(4)
        self.stack = []
        self.tone = None
        self.seed = seed
        r = abs(noise.hash_vector_float(V((seed * 7.31, seed * 1.7, 3.3)))) if False else None
        self.uvo = (((seed * 0.6180339) % 1.0), ((seed * 0.3819660) % 1.0)) if uvshift else (0.0, 0.0)

    # transform stack
    def push(self, m):
        self.stack.append(self.T)
        self.T = self.T @ m

    def pop(self):
        self.T = self.stack.pop()

    def at(self, x=0, y=0, z=0, rz=0.0, rx=0.0, ry=0.0, s=1.0):
        m = Matrix.Translation((x, y, z)) @ Matrix.Rotation(rz, 4, 'Z') @ Matrix.Rotation(ry, 4, 'Y') @ Matrix.Rotation(rx, 4, 'X') @ Matrix.Scale(s, 4)
        self.push(m)
        return self

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.pop()

    def mi(self, name):
        if name not in self.slots:
            self.slots.append(name)
        return self.slots.index(name)

    def _v(self, p):
        k = (round(p.x * 20000), round(p.y * 20000), round(p.z * 20000))
        v = self.vmap.get(k)
        if v is None:
            v = self.bm.verts.new(p)
            self.vmap[k] = v
        return v

    def face(self, pts, mat_name, inside=None, out=None, uv=None, smooth=False, color=None):
        P = [self.T @ V(p) for p in pts]
        if inside is not None:
            ins = self.T @ V(inside)
        # remove consecutive duplicates
        keep = []
        for i, p in enumerate(P):
            if not keep or (p - keep[-1]).length > 1e-6:
                keep.append(p)
        if len(keep) > 1 and (keep[0] - keep[-1]).length <= 1e-6:
            keep.pop()
        if len(keep) < 3:
            return None
        UV = list(uv) if uv is not None else None
        if UV is not None and len(UV) == len(P) and len(keep) != len(P):
            UV = None
        P = keep
        n = newell(P)
        if n.length < 1e-10:
            return None
        flip = False
        if inside is not None:
            c = sum(P, V((0, 0, 0))) / len(P)
            flip = n.dot(c - ins) < 0
        elif out is not None:
            flip = n.dot(self.T.to_3x3() @ V(out)) < 0
        if flip:
            P.reverse()
            n = -n
            if UV is not None:
                UV.reverse()
        n.normalize()
        vs = [self._v(p) for p in P]
        if len(set(vs)) < len(vs):
            return None
        try:
            f = self.bm.faces.new(vs)
        except ValueError:
            return None
        f.material_index = self.mi(mat_name)
        f.smooth = smooth
        tile = TILE.get(mat_name, 1.0)
        explicit = mat_name in EXPLICIT
        for i, l in enumerate(f.loops):
            p = P[i]
            if UV is not None:
                l[self.uvl].uv = UV[i]
            elif explicit:
                l[self.uvl].uv = (0.0, 0.0)
            else:
                ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
                if az >= ax and az >= ay:
                    u, v = p.x, p.y
                elif ay >= ax:
                    u, v = p.x * (1 if n.y < 0 else -1), p.z
                else:
                    u, v = p.y * (1 if n.x > 0 else -1), p.z
                l[self.uvl].uv = (u / tile + self.uvo[0], v / tile + self.uvo[1])
            c = color(p) if color else (self.tone(p) if self.tone else (1, 1, 1))
            l[self.cl] = (c[0], c[1], c[2], 1.0)
        return f

    def uvrect(self, pts, mat_name, rect, out=None, inside=None):
        """Quad 0..3 (bottom-left, bottom-right, top-right, top-left of the picture) with UVs from an atlas rectangle (u0, v0, u1, v1)."""
        u0, v0, u1, v1 = rect
        return self.face(pts, mat_name, out=out, inside=inside, uv=[(u0, v0), (u1, v0), (u1, v1), (u0, v1)])

    # primitives
    def box(self, x0, y0, z0, x1, y1, z1, mat_name, bv=0.0, skip=(), mats=None):
        mats = mats or {}
        x0, x1 = min(x0, x1), max(x0, x1)
        y0, y1 = min(y0, y1), max(y0, y1)
        z0, z1 = min(z0, z1), max(z0, z1)
        c = V(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
        lo, hi = (x0, y0, z0), (x1, y1, z1)
        b = min(bv, (x1 - x0) / 2.1, (y1 - y0) / 2.1, (z1 - z0) / 2.1)

        def corner(ix, iy, iz, axis):
            p = [hi[0] if ix else lo[0], hi[1] if iy else lo[1], hi[2] if iz else lo[2]]
            if b > 0:
                s = (1 if ix else -1, 1 if iy else -1, 1 if iz else -1)
                for a in range(3):
                    if a != axis:
                        p[a] -= s[a] * b
            return V(p)
        names = ['x', 'y', 'z']
        for axis in range(3):
            for side in (0, 1):
                key = ('+' if side else '-') + names[axis]
                if key in skip:
                    continue
                pts = []
                a1, a2 = [a for a in range(3) if a != axis]
                for i1, i2 in ((0, 0), (1, 0), (1, 1), (0, 1)):
                    idx = [0, 0, 0]
                    idx[axis], idx[a1], idx[a2] = side, i1, i2
                    pts.append(corner(*idx, axis))
                self.face(pts, mats.get(key, mat_name), inside=c)
        if b > 0:
            for a in range(3):                                   # edge strips: edges parallel to axis a join the faces of the two other axes
                a1, a2 = [q for q in range(3) if q != a]
                for s1 in (0, 1):
                    for s2 in (0, 1):
                        k1 = ('+' if s1 else '-') + names[a1]
                        k2 = ('+' if s2 else '-') + names[a2]
                        if k1 in skip or k2 in skip:
                            continue
                        pts = []
                        for sa in (0, 1):
                            idx1 = [0, 0, 0]
                            idx1[a], idx1[a1], idx1[a2] = sa, s1, s2
                            pts.append(corner(*idx1, a1))
                            pts.append(corner(*idx1, a2))
                        self.face([pts[0], pts[1], pts[3], pts[2]], mats.get(k1, mat_name), inside=c)
            for ix in (0, 1):
                for iy in (0, 1):
                    for iz in (0, 1):
                        ks = [('+' if i else '-') + n for i, n in zip((ix, iy, iz), names)]
                        if any(k in skip for k in ks):
                            continue
                        self.face([corner(ix, iy, iz, 0), corner(ix, iy, iz, 1), corner(ix, iy, iz, 2)], mat_name, inside=c)

    def lathe(self, profile, mat_name, x=0, y=0, seg=16, smooth=True, closed_inside=None, sharp=35.0, uvr=None):
        """Revolve [(r, z), ...] (traversed bottom to top on the outside) about the vertical axis at (x, y)."""
        ring = lambda r, z, k: V((x + r * math.cos(2 * math.pi * k / seg), y + r * math.sin(2 * math.pi * k / seg), z))  # noqa: E731
        C = 2 * math.pi * max(r for r, _ in profile)
        tile = TILE.get(mat_name, 1.0)
        for i in range(len(profile) - 1):
            (r0, z0), (r1, z1) = profile[i], profile[i + 1]
            for k in range(seg):
                pts = [ring(r0, z0, k), ring(r0, z0, k + 1), ring(r1, z1, k + 1), ring(r1, z1, k)]
                dr, dz = r1 - r0, z1 - z0
                nrm2 = V((dz, -dr, 0))
                mid = (k + 0.5) * 2 * math.pi / seg
                out = V((nrm2.x * math.cos(mid), nrm2.x * math.sin(mid), nrm2.y))
                if mat_name in EXPLICIT:
                    uv = None
                else:
                    ua, ub = (k / seg) * C / tile, ((k + 1) / seg) * C / tile
                    seglen = math.hypot(dr, dz) / tile
                    vb = sum(math.hypot(profile[j + 1][0] - profile[j][0], profile[j + 1][1] - profile[j][1]) for j in range(i)) / tile
                    uv = [(ua + self.uvo[0], vb + self.uvo[1]), (ub + self.uvo[0], vb + self.uvo[1]), (ub + self.uvo[0], vb + seglen + self.uvo[1]), (ua + self.uvo[0], vb + seglen + self.uvo[1])]
                f = self.face(pts, mat_name, out=out, smooth=smooth, uv=uv)
        if smooth:                                                            # hard profile corners stay sharp
            for i in range(1, len(profile) - 1):
                a = V((profile[i][0] - profile[i - 1][0], profile[i][1] - profile[i - 1][1], 0))
                b2 = V((profile[i + 1][0] - profile[i][0], profile[i + 1][1] - profile[i][1], 0))
                if a.length > 0 and b2.length > 0 and math.degrees(a.angle(b2)) > sharp:
                    r, z = profile[i]
                    for k in range(seg):
                        v0, v1 = self._v(self.T @ ring(r, z, k)), self._v(self.T @ ring(r, z, k + 1))
                        e = self.bm.edges.get((v0, v1))
                        if e:
                            e.smooth = False

    def cyl(self, x, y, z0, z1, r, mat_name, seg=16, r1=None, caps=(True, True), smooth=True):
        r1 = r if r1 is None else r1
        prof = []
        if caps[0]:
            prof.append((0.0, z0))
        prof += [(r, z0), (r1, z1)]
        if caps[1]:
            prof.append((0.0, z1))
        self.lathe(prof, mat_name, x, y, seg, smooth)

    def extrude(self, poly, axis, a0, a1, mat_name, caps=True):
        """Prism from a 2D polygon (CCW in the plane spanned by the other two axes in x,y,z order) between a0 and a1 along `axis` ('x','y','z')."""
        ai = 'xyz'.index(axis)
        o1, o2 = [i for i in range(3) if i != ai]

        def p3(pq, a):
            v = [0.0, 0.0, 0.0]
            v[ai], v[o1], v[o2] = a, pq[0], pq[1]
            return V(v)
        area = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))
        if area < 0:
            poly = poly[::-1]
        n = len(poly)
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            dp, dq = b[0] - a[0], b[1] - a[1]
            outv = p3((dq, -dp), 0)
            outv[ai] = 0
            self.face([p3(a, a0), p3(b, a0), p3(b, a1), p3(a, a1)], mat_name, out=outv)
        if caps:
            for a, sgn in ((a0, -1), (a1, 1)):
                d = V((0, 0, 0))
                d[ai] = sgn
                self.face([p3(q, a) for q in poly], mat_name, out=d)

    def tube(self, pts, r, mat_name, seg=6, smooth=True, caps=True):
        P = [V(p) for p in pts]
        rings = []
        for i, p in enumerate(P):
            t = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized()
            u = t.cross(V((0, 0, 1)))
            if u.length < 1e-4:
                u = t.cross(V((0, 1, 0)))
            u.normalize()
            w = t.cross(u)
            rings.append([p + (u * math.cos(2 * math.pi * k / seg) + w * math.sin(2 * math.pi * k / seg)) * r for k in range(seg)])
        for i in range(len(P) - 1):
            mid = (P[i] + P[i + 1]) / 2
            for k in range(seg):
                self.face([rings[i][k], rings[i][(k + 1) % seg], rings[i + 1][(k + 1) % seg], rings[i + 1][k]], mat_name, inside=mid, smooth=smooth,
                          uv=[(k / seg, i), ((k + 1) / seg, i), ((k + 1) / seg, i + 1), (k / seg, i + 1)] if mat_name not in EXPLICIT else None)
        if caps:
            self.face(rings[0][::-1], mat_name, out=P[0] - P[1])
            self.face(rings[-1], mat_name, out=P[-1] - P[-2])

    def quad(self, p0, p1, p2, p3, mat_name, out=None, uv=None):
        return self.face([p0, p1, p2, p3], mat_name, out=out, uv=uv)

    def grid(self, origin, du, dv, nu, nv, mat_name, out, color=None, cell=None):
        """Plane patch origin + a*du + b*dv, a in 0..nu cells, b in 0..nv cells (each cell a quad: vertex colours need density)."""
        o, du, dv = V(origin), V(du), V(dv)
        for a in range(nu):
            for b in range(nv):
                p = [o + du * a + dv * b, o + du * (a + 1) + dv * b, o + du * (a + 1) + dv * (b + 1), o + du * a + dv * (b + 1)]
                self.face(p, mat_name, out=out, color=color)

    def build(self, name=None, collection=None, parent=None, loc=(0, 0, 0), props=None):
        me = bpy.data.meshes.new(name or self.name)
        self.bm.to_mesh(me)
        self.bm.free()
        for s in self.slots:
            me.materials.append(mat(s))
        for p in me.polygons:
            pass
        o = bpy.data.objects.new(name or self.name, me)
        o.location = loc
        (collection or bpy.context.scene.collection).objects.link(o)
        if parent is not None:
            o.parent = parent
        for k, v in (props or {}).items():
            o[k] = v
        return o


def fbm(p, seed=0, scale=1.0):
    return noise.fractal(V((p.x * scale + seed * 13.1, p.y * scale + seed * 7.7, p.z * scale + seed * 3.3)), 0.5, 2.0, 3, noise_basis='PERLIN_NEW') * 0.5 + 0.5


def save_blend(path):
    bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=True)
