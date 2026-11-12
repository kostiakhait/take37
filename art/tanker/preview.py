# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Preview stills of the tanker (Blender headless, Cycles on the NVIDIA GPU; refuses to fall back to the CPU):

  blender -b <saved.blend> -P preview.py -- --views side,front,rear,three,rear3,top,cab,wheel [--out D:/temp/take37/tanker/prev/p.png] [--samples 48] [--w 1400 --h 800]
  views are named in SPEC below: name -> (camera location, target, lens or ortho scale, 'persp'/'ortho'). Extra: --cam x,y,z,tx,ty,tz,lens for one custom view named 'c'.
"""
import math
import pathlib
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
arg = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d  # noqa: E731
VIEWS = arg('--views', 'three,side').split(',')
SAMPLES = int(arg('--samples', '48'))
W, H = int(arg('--w', '1400')), int(arg('--h', '800'))
OUT = pathlib.Path(arg('--out', 'D:/temp/take37/tanker/prev/p.png'))


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


def V(*a):
    return Vector(a)


SPEC = {
    'side': (V(-4, 60, 1.8), V(-4, 0, 1.8), 17.5, 'ortho'),
    'front': (V(60, 0, 1.8), V(0, 0, 1.8), 4.6, 'ortho'),
    'rear': (V(-60, 0, 1.8), V(0, 0, 1.8), 4.6, 'ortho'),
    'top': (V(-4, 0, 60), V(-4, 0, 0), 17.5, 'ortho'),
    'three': (V(11, 12, 4.4), V(-3, 0, 1.4), 38, 'persp'),
    'rear3': (V(-19, -9, 4.0), V(-5, 0, 1.4), 38, 'persp'),
    'front3': (V(9, -7, 2.4), V(1, 0, 1.4), 40, 'persp'),
    'tractor': (V(7.5, 6.5, 2.8), V(0.5, 0, 1.5), 40, 'persp'),
    'cab': (V(2.8, 3.6, 2.2), V(0.2, 0, 1.9), 35, 'persp'),
    'inside': (V(-0.35, -0.55, 2.05), V(0.8, 0.45, 1.55), 32, 'persp'),
    'inside2': (V(-0.45, 0.50, 2.20), V(0.8, -0.1, 1.60), 36, 'persp'),
    'seat': (V(0.35, -0.2, 2.2), V(-0.3, 0.5, 1.45), 40, 'persp'),
    'wheel': (V(-0.6, 3.2, 0.9), V(-2.2, 1.0, 0.6), 45, 'persp'),
    'wheelf': (V(3.6, 3.0, 0.9), V(2.2, 1.0, 0.55), 45, 'persp'),
    'under': (V(-2.0, 2.6, 0.35), V(-3.2, 0.0, 0.9), 40, 'persp'),
    'top3': (V(-6, 5, 5.4), V(-6, 0, 2.7), 40, 'persp'),
    'valves': (V(-7.0, 3.6, 1.0), V(-6.0, 1.3, 1.0), 40, 'persp'),
    'rearend': (V(-14.0, 2.6, 1.4), V(-11.5, 0.0, 1.1), 40, 'persp'),
    'ladder': (V(-13.0, -3.0, 2.6), V(-11.5, -0.4, 2.2), 40, 'persp'),
    'domes': (V(-3.0, 3.8, 5.0), V(-5.5, 0.0, 3.0), 40, 'persp'),
    'chassis': (V(3, 7, 1.4), V(-1.0, 0.0, 0.9), 40, 'persp'),
    'fifth': (V(-0.8, 3.5, 1.8), V(-1.9, 0.0, 1.2), 40, 'persp'),
}


def main():
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
    sky.sun_elevation = math.radians(40)
    sky.sun_rotation = math.radians(215)
    sky.sun_intensity = 0.6
    nt.links.new(sky.outputs['Color'], nt.nodes['Background'].inputs['Color'])
    nt.nodes['Background'].inputs['Strength'].default_value = 0.25
    bpy.ops.mesh.primitive_plane_add(size=300, location=(0, 0, 0))
    gm = bpy.data.materials.new('asphalt')
    gm.use_nodes = True
    b = gm.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.09, 0.09, 0.09, 1)
    b.inputs['Roughness'].default_value = 0.85
    bpy.context.object.data.materials.append(gm)
    if arg('--cablight'):
        ld = bpy.data.lights.new('cabl', 'POINT')
        ld.energy = 120
        ld.shadow_soft_size = 0.3
        lo = bpy.data.objects.new('cabl', ld)
        sc.collection.objects.link(lo)
        lo.location = (0.1, 0.0, 2.70)
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.clip_end = 400
    cam.data.clip_start = 0.05
    spec = dict(SPEC)
    if arg('--cam'):
        v = [float(x) for x in arg('--cam').split(',')]
        spec['c'] = (V(*v[:3]), V(*v[3:6]), v[6], 'persp')
    for name in VIEWS:
        loc, tgt, val, mode = spec[name]
        cam.location = loc
        if name == 'top':
            cam.rotation_euler = (0, 0, 0)
        else:
            cam.rotation_euler = (tgt - loc).to_track_quat('-Z', 'Y').to_euler()
        cam.data.type = 'ORTHO' if mode == 'ortho' else 'PERSP'
        if mode == 'ortho':
            cam.data.ortho_scale = val
        else:
            cam.data.lens = val
        f = OUT.with_name(f'{OUT.stem}_{name}.png')
        sc.render.filepath = str(f)
        bpy.ops.render.render(write_still=True)
        print('frame', f)


main()
