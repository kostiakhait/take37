# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Robinson R22 Beta II for TAKE 37, built in Blender 4.2 headless and re-runnable:

  blender -b -t 8 -P art/helicopter/r22/r22_build.py -- [--out assets/borrowed/r22.glb] [--lod1 assets/borrowed/r22_lod1.glb] [--blend D:/temp/take37/heli/r22.blend] [--only cabin,boom]

Frame while building: nose +X, left +Y, up +Z, origin on the ground under the main rotor axis; the glb export turns it into Y up with the nose on +X (as the cars and the airwar aircraft).
Root node: R22 > zones (Zone_Cabin, Zone_Engine, Zone_TailBoom, Zone_MainRotor, Zone_TailRotor, Zone_Fuel, Zone_Skids), Colliders, Anchors (seats, hands, feet, exit, emitters), Damage (Dmg_*).
"""
import sys
import pathlib
import time
import importlib

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import bpy  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
arg = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d  # noqa: E731


def log(*a):
    print('[r22]', *a, flush=True)


def build(det):
    for m in ['r22.kit', 'r22.params', 'r22.textures', 'r22.materials', 'r22.fuselage', 'r22.interior', 'r22.mech', 'r22.damage', 'r22.zones']:
        if m in sys.modules:
            del sys.modules[m]
    from r22 import kit
    kit.DET = det
    kit.MATS.clear()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    from r22 import materials, fuselage, interior, mech, damage, zones, params as P
    M = materials.make()
    root = kit.empty('R22', (0, 0, 0), None, kind='PLAIN_AXES', size=0.3)
    ctx = dict(root=root, M=M, P=P, parts={})
    t0 = time.time()
    fuselage_parts = fuselage_build(ctx, fuselage)
    interior.build(ctx)
    mech.build(ctx)
    damage.build(ctx)
    zones.finish(ctx)
    log('built det', det, 'in %.1fs' % (time.time() - t0))
    return ctx


def fuselage_build(ctx, fuselage):
    root, M = ctx['root'], ctx['M']
    parts = ctx['parts']
    objs, Pt = fuselage.build_cabin(root, M)
    doors = fuselage.door_split(root, objs, Pt, M)
    parts['cabin'] = objs['skin']
    parts['wind'] = objs['wind']
    parts['bulkhead'] = objs['bulkhead']
    parts['doors'] = doors
    parts['pylon'] = fuselage.build_pylon(root, M)
    cowl = fuselage.build_cowl(root, M)
    from r22 import mech
    cowl['belly'] = fuselage.build_cowl_belly(root, M, mech.ENG_X0, mech.ENG_ZC)
    parts['cowl'] = cowl
    parts['boom_fwd'] = fuselage.build_boom(root, M, 1.34, 3.20, 'Boom_Fwd', end_cap=False)
    parts['boom_end'] = fuselage.build_boom(root, M, 3.20, 4.58, 'Boom_End')
    return parts


def export(ctx, path, only_vis=None):
    import bpy
    root = ctx['root']
    obs = [root] + list(root.children_recursive)
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in obs:
        o.select_set(True)
    path.parent.mkdir(parents=True, exist_ok=True)
    kw = dict(filepath=str(path), export_format='GLB', use_selection=True, export_yup=True, export_apply=True, export_image_format='WEBP',
              export_materials='EXPORT', export_extras=True, export_cameras=False, export_lights=False)
    props = bpy.ops.export_scene.gltf.get_rna_type().properties
    if 'export_vertex_color' in props:
        kw['export_vertex_color'] = 'ACTIVE'
    elif 'export_active_vertex_color_when_no_material' in props:
        kw['export_active_vertex_color_when_no_material'] = True
    bpy.ops.export_scene.gltf(**kw)
    from r22 import kit
    log('wrote', path, 'triangles', kit.tris([o for o in obs if o.type == 'MESH']))


if __name__ == '__main__':
    det = float(arg('--det', '1.0'))
    ctx = build(det)
    if arg('--blend'):
        pathlib.Path(arg('--blend')).parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=arg('--blend'))
    if arg('--out'):
        export(ctx, pathlib.Path(arg('--out')))
