# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""The breakable parts of a building's shop front as a glb of their own (BUILDINGS-DESTRUCTION).

  blender -b -P art/street/shopfront_parts.py -- --designs 18,24 [--out art/street/shops]

For each main-street design the building is made again by buildings.make_building with the same code and random numbers, but split (partsplit.py): the shell (the building without its shop windows,
door, transom, sign board and awning) at both levels of detail, and the parts of the full level as meshes of their own:
  Part_ShopWindow_<k>_<j>   one pane of display window k between two mullions
  Part_ShopTransom_0        the glass over the door
  Part_ShopDoorLeaf_0       the wooden door with its handle and kick plate;  Part_ShopDoorGlass_0 its glass
  Part_ShopSign_0           the sign board (atlas picture)
  Part_ShopAwning_<j>       the awning in sections of about 3 m (canvas, valence, arms)
Frame of the building (as in the street glb): origin on the ground at the middle of the front, +X out of the front, building runs back along -X. The game puts the file where the street's Bld node
stands. The glb has no textures: the game takes the street's own materials by name (the same brick, glass, wood and canvas).
"""
import pathlib
import sys

import bmesh
import bpy

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import buildings as B  # noqa: E402
import kitlib as K  # noqa: E402
import partsplit as PS  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
arg = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d  # noqa: E731
HERE = pathlib.Path(__file__).resolve().parent
OUT = pathlib.Path(arg('--out', str(HERE / 'shops')))
NAMES = arg('--designs', '18').split(',')
MULLION = 1.6            # buildings.shopfront: a mullion every 1.6 m of window
AWNING_SECTION = 3.0


def ybounds(mb):
    ys = [v.co.y for v in mb.bm.verts]
    return min(ys), max(ys)


def export(objs, path):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True, export_yup=True, export_apply=False, export_extras=True, export_cameras=False, export_lights=False,
                              export_image_format='NONE', export_texcoords=True, export_normals=True, export_materials='EXPORT', export_vertex_color='ACTIVE',
                              export_active_vertex_color_when_no_material=True, export_animations=False, export_attributes=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    designs = {d['name']: d for d in B.make_designs(36)}
    for name in NAMES:
        K.reset()
        d = dict(designs[name])
        d['D'] = 16.0
        col = K.coll('Shop')
        root = K.empty(f'ShopBld_{name}', size=1.0, collection=col)
        root['design'] = name
        shells = {}
        parts0 = None
        for lod in (1, 0):
            d['split'] = lod == 0            # the far level keeps its shop front in the shell (the parts exist at the full level only)
            sh = B.make_building(d, lod)
            for c in sh.users_collection:
                c.objects.unlink(sh)
            col.objects.link(sh)
            sh.name = sh.data.name = f'Shell_LOD{lod}'
            sh.parent = root
            sh['lod'] = lod
            shells[lod] = sh
            if lod == 0:
                parts0 = dict(PS.LAST)
        objs = [root, shells[0], shells[1]]
        tags = sorted(parts0)
        info = {}
        for tag in tags:
            mb = parts0[tag]
            if tag.startswith('pane'):
                lo, hi = ybounds(mb)
                n = int((hi - lo) / MULLION)
                cuts = [lo + (hi - lo) * k / (n + 1) for k in range(1, n + 1)]
                k = int(tag[4:])
                kind, label = 'ShopWindow', lambda j, k=k: f'{k}_{j}'
            elif tag == 'awning':
                lo, hi = ybounds(mb)
                n = max(1, round((hi - lo) / AWNING_SECTION))
                cuts = [lo + (hi - lo) * k / n for k in range(1, n)]
                kind, label = 'ShopAwning', lambda j: f'{j}'
            else:
                cuts = []
                kind = {'door': 'ShopDoorLeaf', 'doorglass': 'ShopDoorGlass', 'transom': 'ShopTransom', 'sign': 'ShopSign'}[tag]
                label = lambda j: '0'
            for j, (a, b, bm) in enumerate(PS.cut(mb, cuts) if cuts else [(-1e9, 1e9, mb.bm)]):
                o = PS.to_object(bm, mb.slots, f'Part_{kind}_{label(j)}', col, root)
                o['kind'] = kind
                o['lod'] = 0
                objs.append(o)
            if cuts:
                mb.bm.free()
            info[tag] = len(cuts) + 1
        path = OUT / f'shop_{name}.glb'
        export(objs, path)
        print('[shop]', name, 'parts', info, 'tris shell0/1', K.tris(shells[0]), K.tris(shells[1]), 'parts', sum(K.tris(o) for o in objs[3:]), '->', path, flush=True)


main()
