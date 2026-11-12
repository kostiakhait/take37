# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Preview stills of a car glb (Blender, headless, Cycles on the NVIDIA GPU; refuses to fall back to the CPU):

  blender -b -P preview.py -- --glb car.glb --views three,side,front,rear,inside --out D:/temp/take37/<name>/prev.png [--samples 48] [--w 1280 --h 720] [--variant 2]
Lights the car with a physical sky and a sun over a grey asphalt plane; side/front/rear/top are orthographic.
"""
import math
import pathlib
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
arg = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d  # noqa: E731
VIEWS = arg('--views', 'three,side,front,rear').split(',')
SAMPLES = int(arg('--samples', '48'))
W, H = int(arg('--w', '1280')), int(arg('--h', '720'))
OUT = pathlib.Path(arg('--out'))
OUT.parent.mkdir(parents=True, exist_ok=True)


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
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=arg('--glb'))
    for hn in (arg('--hide', '') or '').split(','):
        if hn and hn in bpy.data.objects:
            bpy.data.objects[hn].hide_render = True
    mats = [m for m in bpy.data.materials if m.name.startswith('paint_')]
    vi = arg('--variant')
    if vi is not None and mats:
        pm = next(m for m in bpy.data.materials if m.name == 'M_paint')
        src = mats[int(vi)]
        pm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = src.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value
    cr = arg('--coatrough')
    if cr is not None:
        for m in bpy.data.materials:
            if m.use_nodes:
                for n in m.node_tree.nodes:
                    if n.type == 'BSDF_PRINCIPLED' and n.inputs['Coat Weight'].default_value > 0.9:
                        n.inputs['Coat Roughness'].default_value = float(cr)
    if '--cull' in argv:      # as the game draws them (Babylon culls back faces): EEVEE only
        for m in bpy.data.materials:
            m.use_backface_culling = True
    sc = bpy.context.scene
    if arg('--engine', 'cycles') == 'eevee':
        sc.render.engine = 'BLENDER_EEVEE_NEXT'
        sc.eevee.taa_render_samples = SAMPLES
        sc.eevee.use_raytracing = arg('--rt', '1') == '1'
    else:
        sc.render.engine = 'CYCLES'
        kind, names = gpu()
        print('DEVICE', kind, names, flush=True)
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
    nt.nodes['Background'].inputs['Strength'].default_value = 0.25
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, 0))
    gm = bpy.data.materials.new('asphalt')
    gm.use_nodes = True
    b = gm.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.10, 0.10, 0.10, 1)
    b.inputs['Roughness'].default_value = 0.85
    bpy.context.object.data.materials.append(gm)
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.clip_end = 300
    cam.data.clip_start = 0.05
    L = float(arg('--len', '4.8'))
    k = L / 4.8
    ctr = Vector((0, 0, 0.72))
    spec = {
        'side': (Vector((0, 40, 0.72)), ctr, 'ortho', 6.2 * k),
        'right': (Vector((0, -40, 0.72)), ctr, 'ortho', 6.2 * k),
        'front': (Vector((40, 0, 0.72)), ctr, 'ortho', 2.8),
        'rear': (Vector((-40, 0, 0.72)), ctr, 'ortho', 2.8),
        'top': (Vector((0, 0, 40)), Vector((0, 0, 0)), 'ortho', 6.2 * k),
        'three': (Vector((6.2 * k, 4.6 * k, 1.9)), ctr, 'persp', 40),
        'rear3': (Vector((-6.0 * k, -4.4 * k, 2.2)), ctr, 'persp', 40),
        'three_r': (Vector((6.2 * k, -4.6 * k, 1.9)), ctr, 'persp', 40),
        'rear3_l': (Vector((-6.0 * k, 4.4 * k, 2.2)), ctr, 'persp', 40),
        'fender_l': (Vector((3.6 * k, 3.0, 1.2)), Vector((1.5 * k, 0.6, 0.6)), 'persp', 45),
        'fender_r': (Vector((3.6 * k, -3.0, 1.2)), Vector((1.5 * k, -0.6, 0.6)), 'persp', 45),
        'low': (Vector((4.6 * k, 2.8 * k, 0.55)), ctr, 'persp', 35),
        'detail': (Vector((3.9 * k, 2.2 * k, 1.25)), Vector((1.5 * k, 0.5, 0.7)), 'persp', 50),
        'inside': (Vector((-0.5 * k, 2.4, 1.3)), Vector((0.2, 0.2, 0.85)), 'persp', 32),
        'cabin': (Vector((-1.0 * k, 0.55, 1.15)), Vector((0.6 * k, -0.2, 0.9)), 'persp', 55),
        'wheel': (Vector((2.0 * k, 2.5, 0.5)), Vector((1.4 * k, 0.8, 0.34)), 'persp', 55),
        'hood': (Vector((3.0 * k, 1.2, 1.6)), Vector((1.6 * k, 0.0, 0.8)), 'persp', 45),
        'tail': (Vector((-4.0 * k, -1.8, 1.1)), Vector((-2.4 * k, 0, 0.7)), 'persp', 50),
        'under': (Vector((3.0 * k, 2.0, 0.25)), Vector((0.0, 0.0, 0.2)), 'persp', 45),
        'engine': (Vector((3.4 * k, 1.5, 1.9)), Vector((1.6 * k, 0.0, 0.7)), 'persp', 50),
    }
    for v in VIEWS:
        loc, tgt, mode, val = spec[v]
        cam.location = loc
        cam.rotation_euler = (tgt - loc).to_track_quat('-Z', 'Y').to_euler()
        if v == 'top':
            cam.rotation_euler = (0, 0, math.radians(0))
        cam.data.type = 'ORTHO' if mode == 'ortho' else 'PERSP'
        if mode == 'ortho':
            cam.data.ortho_scale = val
        else:
            cam.data.lens = val
        f = OUT.with_name(f'{OUT.stem}_{v}.png')
        sc.render.filepath = str(f)
        bpy.ops.render.render(write_still=True)
        print('frame', f, flush=True)
        if arg('--engine', 'cycles') == 'eevee':
            import gpu as gpumod
            print('RENDERER', gpumod.platform.renderer_get(), flush=True)


main()
