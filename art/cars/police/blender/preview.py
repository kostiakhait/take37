# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Preview stills of the Crown Victoria (Blender, headless, Cycles on the NVIDIA GPU; refuses to fall back to the CPU):

  blender -b <saved.blend> -P examples/crown-victoria/blender/preview.py -- --views side,front,rear,three,rear3,top,detail [--out build/prev.png] [--samples 64] [--w 1200 --h 700]

Opens a .blend saved by build_crownvic.py --blend (or builds the model when run without one), lights it with a physical sky and a sun over a grey asphalt plane, and renders each view
to build/prev_<view>.png. side, front, rear and top are orthographic.
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
VIEWS = arg('--views', 'side,front,rear,three,rear3,top').split(',')
SAMPLES = int(arg('--samples', '64'))
W, H = int(arg('--w', '1200')), int(arg('--h', '700'))
OUT = pathlib.Path(arg('--out', str(HERE.parent / 'build' / 'prev.png')))


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
    if not any(o.name == 'CrownVic87' for o in bpy.data.objects):
        import build_crownvic
        build_crownvic.build()
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    kind, names = gpu()
    print('DEVICE', kind, names)
    sc.cycles.device = 'GPU'
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = W, H
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Base Contrast'
    world = bpy.data.worlds.new('W')
    sc.world = world
    world.use_nodes = True
    nt = world.node_tree
    sky = nt.nodes.new('ShaderNodeTexSky')
    sky.sky_type = 'NISHITA'
    sky.sun_elevation = math.radians(38)
    sky.sun_rotation = math.radians(215)
    sky.sun_intensity = 0.6
    nt.links.new(sky.outputs['Color'], nt.nodes['Background'].inputs['Color'])
    nt.nodes['Background'].inputs['Strength'].default_value = 0.22
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, 0))
    gm = bpy.data.materials.new('asphalt')
    gm.use_nodes = True
    b = gm.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.10, 0.10, 0.10, 1)
    b.inputs['Roughness'].default_value = 0.85
    bpy.context.object.data.materials.append(gm)
    c = Vector((0, 0, 0.72))
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.clip_end = 300
    spec = {
        'side': (Vector((0, 40, 0.72)), 'ortho', 5.9),
        'right': (Vector((0, -40, 0.72)), 'ortho', 5.9),
        'front': (Vector((40, 0, 0.72)), 'ortho', 2.6),
        'rear': (Vector((-40, 0, 0.72)), 'ortho', 2.6),
        'top': (Vector((0, 0, 40)), 'ortho', 5.9),
        'three': (Vector((6.2, 4.6, 1.9)), 'persp', 40),
        'rear3': (Vector((-6.0, -4.4, 2.2)), 'persp', 40),
        'detail': (Vector((4.0, 2.2, 1.25)), 'persp', 50),
        'low': (Vector((5.0, 3.0, 0.55)), 'persp', 35),
        'inside': (Vector((-0.6, 2.3, 1.25)), 'persp', 30),
        'wheel': (Vector((2.2, 2.6, 0.45)), 'persp', 60),
        'tail': (Vector((-4.3, -1.4, 1.0)), 'persp', 50),
        'cabin': (Vector((-0.9, 1.6, 1.75)), 'persp', 26),
        'r3f': (Vector((2.6, -4.4, 1.7)), 'persp', 42),
        'r3b': (Vector((-2.4, -4.6, 1.6)), 'persp', 42),
        'r3h': (Vector((0.5, -3.2, 2.6)), 'persp', 45),
    }
    for v in VIEWS:
        loc, mode, val = spec[v]
        cam.location = loc
        tgt = Vector((0, 0, 0.0)) if v == 'top' else (Vector((1.6, 0.5, 0.7)) if v == 'detail' else (Vector((0.0, 0.3, 0.9)) if v == 'inside' else (Vector((1.45, 0.79, 0.34)) if v == 'wheel' else (Vector((-2.73, 0, 0.72)) if v == 'tail' else (Vector((0.2, 0.0, 0.85)) if v == 'cabin' else c)))))
        if v in ('r3f', 'r3b', 'r3h'):
            tgt = Vector((0.0, -0.8, 0.75))
        d = tgt - loc
        cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        if v == 'top':
            cam.rotation_euler = (0, 0, 0)
        cam.data.type = 'ORTHO' if mode == 'ortho' else 'PERSP'
        if mode == 'ortho':
            cam.data.ortho_scale = val
        else:
            cam.data.lens = val
        f = OUT.with_name(f'{OUT.stem}_{v}.png')
        sc.render.filepath = str(f)
        bpy.ops.render.render(write_still=True)
        print('frame', f)


main()
