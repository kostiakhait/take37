# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Fast loop for the cab: opens a .blend saved by build_crownvic.py --blend, rebuilds the cab (cab.py) and the cabin's materials without redoing the body's boolean cuts, then renders
frames from the driver's eye (EEVEE on the NVIDIA card) and/or exports a glb.
  blender -b base.blend -P interior_only.py -- --render D:/temp/take37/cab/prev [--out x.glb] [--blend y.blend] [--views sit,left,right,back,wheel,door]
"""
import math
import pathlib
import sys

import bpy
from mathutils import Vector

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
arg = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d  # noqa: E731
import importlib  # noqa: E402
import build_crownvic as B  # noqa: E402
import cab  # noqa: E402
importlib.reload(cab)

root = bpy.data.objects['CrownVic87']
for nm in ('Interior', 'Dash', 'SteeringWheel', 'Equipment', 'PillarTrim', 'DoorCard_FL', 'DoorCard_FR', 'DoorCard_RL', 'DoorCard_RR', 'Mirror_Inner', 'Mirror_Inner_Glass', 'Mirror_L', 'Mirror_R', 'Mirror_L_Glass', 'Mirror_R_Glass'):
    ob = bpy.data.objects.get(nm)
    if ob:
        bpy.data.objects.remove(ob, do_unlink=True)
# the cabin's materials: new colours and library textures in place of the old ones
REPL = ('interior', 'carpet', 'headliner', 'dash', 'seatcloth', 'pad', 'gauges', 'radio', 'mirror')
for k in REPL:
    old = bpy.data.materials.get('M_' + k)
    if old:
        old.name = 'old_' + k
B._mc.clear()
newm = {k: B.mat(k) for k in REPL if k != 'seatcloth'}
for ob in bpy.data.objects:
    if ob.type != 'MESH':
        continue
    for i, sl in enumerate(ob.material_slots):
        if sl.material and sl.material.name.startswith('old_'):
            ob.material_slots[i].material = newm[sl.material.name[4:]]
body = bpy.data.objects['Body']
B.metres_uv(body, ('carpet', 'headliner'))
B.build_interior(root)
for o in root.children:
    if o.name in ('Interior', 'Dash', 'SteeringWheel', 'Equipment', 'PillarTrim', 'Mirror_Inner', 'Mirror_Inner_Glass'):
        o.parent = root
for m in [m for m in bpy.data.materials if m.name.startswith('old_') or m.users == 0]:
    bpy.data.materials.remove(m)
if arg('--blend'):
    bpy.ops.wm.save_as_mainfile(filepath=arg('--blend'))
if arg('--out'):
    B.export(root, pathlib.Path(arg('--out')))
if arg('--lod1'):
    B.export(root, pathlib.Path(arg('--lod1')), lod_ratio=0.35)

if arg('--render'):
    out = pathlib.Path(arg('--render'))
    out.mkdir(parents=True, exist_ok=True)
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
    sc.render.resolution_x, sc.render.resolution_y = 1600, 900
    sc.eevee.taa_render_samples = 24
    # a dusk-ish sky, hemispheric fill like the game's, a sun
    w = bpy.data.worlds.new('w')
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.55, 0.62, 0.8, 1)
    bg.inputs['Strength'].default_value = 1.0
    sun = bpy.data.lights.new('sun', 'SUN')
    sun.energy = 2.0
    so = bpy.data.objects.new('sun', sun)
    sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(55), 0, math.radians(30))
    # glass to nothing for the preview (the game draws it nearly clear)
    for m in bpy.data.materials:
        if m.name == 'M_glass':
            m.node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value = 0.08
            m.blend_method = 'BLEND'
    cam = bpy.data.cameras.new('c')
    cam.sensor_fit = 'VERTICAL'
    cam.angle_y = 1.05
    co = bpy.data.objects.new('c', cam)
    sc.collection.objects.link(co)
    sc.camera = co
    E = cab.EYE
    views = {
        'sit': (E, Vector((1, 0, 0)), 0),
        'sit12': (E, Vector((1, 0, -0.2126)), 0),
        'hl60': (E, Vector((0.5, 0.866, -0.2126)), 0),
        'hr60': (E, Vector((0.5, -0.866, -0.2126)), 0),
        'left': (E, Vector((1, 0.35, -0.04)), 0),
        'right': (E, Vector((1, -0.35, -0.04)), 0),
        'back': (E, Vector((-1, 0, 0.0)), 0),
        'down': (E, Vector((1, 0, -0.45)), 0),
        'door': (E, Vector((0.0, 1, -0.2)), 0),
        'pass': (E, Vector((0.0, -1, -0.2)), 0),
        'hump': (E, Vector((1, -0.25, -0.75)), 0),
        'aleft': (E, Vector((0.6, 1, 0.1)), 0),
    }
    for v in (arg('--views', 'sit,left,right,back').split(',')):
        pos, d, _ = views[v]
        co.location = pos
        co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = str(out / f'{v}.png')
        bpy.ops.render.render(write_still=True)
        print('rendered', v)
