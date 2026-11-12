# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""The model's right-side silhouette over the drawing (Blender headless for the silhouette, then system python for the overlay):

  blender -b <saved.blend> -P examples/crown-victoria/blender/qa_overlay.py         -> build/qa_sil_right.png (orthographic, 200 px/m, the model's frame)
  python -I examples/crown-victoria/blender/qa_overlay.py                          -> build/qa_right.png (the drawing, the silhouette's edge in red)

The overlay maps every drawing pixel through cv_geom.X / Z (the same piecewise scales the model was built with), so the red line lies on the drawing's outline where they agree.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
BUILD = HERE.parent / 'build'
PPM, XC, ZC0, WPX, HPX = 200, 0.0, 0.8, 1300, 400        # silhouette frame: centre x 0, centre z 0.8, 6.5 x 2.0 m

try:
    import bpy
except ImportError:
    bpy = None
if bpy is not None:
    from mathutils import Vector
    sc = bpy.context.scene
    for o in list(bpy.data.objects):
        if o.name in ('Plane', 'Cam', 'Sun'):
            bpy.data.objects.remove(o)
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.render.film_transparent = True
    sc.render.resolution_x, sc.render.resolution_y = WPX, HPX
    sc.display.shading.light = 'FLAT'
    sc.display.shading.color_type = 'SINGLE'
    sc.display.shading.single_color = (1, 0, 0)
    sc.view_settings.view_transform = 'Standard'
    cam = bpy.data.objects.new('QCam', bpy.data.cameras.new('QCam'))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = WPX / PPM
    cam.location = Vector((XC, -30, ZC0))
    cam.rotation_euler = (Vector((XC, 0, ZC0)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    for o in bpy.data.objects:                       # the rack and the antennas stand above the drawing's car: leave them out
        if any(k in o.name for k in ('Rack', 'Beacon', 'Speaker')):
            o.hide_render = True
    sc.render.filepath = str(BUILD / 'qa_sil_right.png')
    bpy.ops.render.render(write_still=True)
else:
    import numpy as np
    from PIL import Image
    sys.path.insert(0, str(HERE))
    import cv_geom as G
    sil = np.array(Image.open(BUILD / 'qa_sil_right.png').convert('RGBA'))[:, :, 3] > 128
    dr = Image.open(HERE.parent / 'reference' / 'ltd_crown_victoria_1986_outlines.png').convert('RGB')
    W, H = dr.size
    big = dr.resize((W * 3, H * 3), Image.NEAREST)
    a = np.array(big)
    inside = np.zeros((H * 3, W * 3), bool)
    for py in range(H * 3):
        z = G.Z(py / 3.0)
        r = int(round((ZC0 - z) * PPM + HPX / 2))
        if not 0 <= r < HPX:
            continue
        for px in range(330 * 3, W * 3):
            x = G.X(px / 3.0)
            c = int(round(WPX / 2 + (x - XC) * PPM))       # the camera stands at -Y looking +Y: the nose (+X) is on the picture's right, as in the drawing
            if 0 <= c < WPX:
                inside[py, px] = sil[r, c]
    edge = inside ^ np.roll(inside, 1, 0) | inside ^ np.roll(inside, 1, 1)
    a[edge] = (230, 20, 20)
    Image.fromarray(a).save(BUILD / 'qa_right.png')
    print('wrote', BUILD / 'qa_right.png')
