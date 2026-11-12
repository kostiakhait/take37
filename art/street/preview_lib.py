# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Preview stills (Blender, headless, Cycles on the NVIDIA GPU; refuses to fall back to the CPU).

  blender -b <saved.blend> -P art/street/preview_lib.py -- --views views.json --out D:/temp/take37/street/prev [--samples 48] [--w 1280 --h 720] [--ground]

views.json: [{"name": "three", "loc": [x, y, z], "target": [x, y, z], "lens": 35}, ...]
"""
import json
import math
import pathlib
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
arg = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d  # noqa: E731


def gpu():
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for kind in ('OPTIX', 'CUDA'):
        try:
            prefs.compute_device_type = kind
            prefs.get_devices()
            devs = [d for d in prefs.devices if d.type == kind and 'NVIDIA' in d.name]
            if devs:
                for d in prefs.devices:
                    d.use = d in devs
                return kind, [d.name for d in devs]
        except Exception:
            pass
    raise SystemExit('no NVIDIA GPU for Cycles: refusing to render on the CPU')


def main():
    views = json.load(open(arg('--views')))
    out = pathlib.Path(arg('--out'))
    out.mkdir(parents=True, exist_ok=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    kind, names = gpu()
    print('DEVICE', kind, names)
    sc.cycles.device = 'GPU'
    sc.cycles.samples = int(arg('--samples', '48'))
    sc.cycles.use_denoising = True
    sc.cycles.transparent_max_bounces = 12
    sc.render.resolution_x, sc.render.resolution_y = int(arg('--w', '1280')), int(arg('--h', '720'))
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Base Contrast'
    world = bpy.data.worlds.new('W')
    sc.world = world
    world.use_nodes = True
    nt = world.node_tree
    sky = nt.nodes.new('ShaderNodeTexSky')
    sky.sky_type = 'NISHITA'
    sky.sun_elevation = math.radians(float(arg('--sun', '34')))
    sky.sun_rotation = math.radians(float(arg('--sunrot', '200')))
    sky.sun_intensity = 0.7
    nt.links.new(sky.outputs['Color'], nt.nodes['Background'].inputs['Color'])
    nt.nodes['Background'].inputs['Strength'].default_value = 0.45
    if '--ground' in argv:
        bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, -0.002))
        gm = bpy.data.materials.new('g')
        gm.use_nodes = True
        gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.12, 0.12, 0.12, 1)
        gm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.9
        bpy.context.object.data.materials.append(gm)
    for o in bpy.data.objects:                      # colliders and the unplaced kit sources are not part of the picture
        if o.name.startswith('COL_') or any(c.name in ('Kit_Source', 'Gas_Source') for c in o.users_collection):
            o.hide_render = True
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.clip_end = 2000
    for v in views:
        cam.location = Vector(v['loc'])
        d = Vector(v['target']) - cam.location
        cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        cam.data.lens = v.get('lens', 35)
        sc.render.filepath = str(out / f"{v['name']}.png")
        bpy.ops.render.render(write_still=True)
        print('frame', sc.render.filepath)


main()
