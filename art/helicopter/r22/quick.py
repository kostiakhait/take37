# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Quick EEVEE stills of a .blend or .glb for checking the build: blender -b -P quick.py -- --in x.blend|x.glb --views side,top,front,three --out D:/temp/take37/heli/render/q [--hide Name,..] [--only Name,..]"""
import sys, math, pathlib
import bpy
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
arg = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
src = arg('--in')
if src.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=src)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    # the glb has the nose on +X: turn it into the build frame (nose -X, right +Y) so the view names mean the same for .blend and .glb
    from mathutils import Matrix as _M
    for o in [o for o in bpy.data.objects if o.parent is None]:
        o.matrix_world = _M.Rotation(math.pi, 4, 'Z') @ o.matrix_world
    bpy.context.view_layer.update()
for hn in ((arg('--hide', '') or '') + ',Collider_*').split(','):
    for o in list(bpy.data.objects):
        if hn and (o.name == hn or (hn.endswith('*') and o.name.startswith(hn[:-1]))):
            o.hide_render = True
# damage states: the nodes tagged state=damaged are hidden unless their group is listed in --dmg (or 'all'); the group's `replaces` hides the intact nodes
dmg = [x for x in (arg('--dmg', '') or '').split(',') if x]
def vis_set(o, show):
    o.hide_render = not show
    o.hide_viewport = not show
def descendants(o):
    out = [o]
    for c in o.children:
        out += descendants(c)
    return out
for o in bpy.data.objects:
    if o.get('state') == 'damaged' and o.type == 'MESH':
        show = ('all' in dmg) or (o.get('group') in dmg)
        o.hide_render = not show
        if show:
            g = bpy.data.objects.get(o.get('group'))
            for nm in (g.get('replaces', '') if g else '').split(','):
                t = bpy.data.objects.get(nm)
                if t:
                    for d in descendants(t):
                        d.hide_render = True
if '--bent' in argv:
    t = bpy.data.objects.get('TailGroup')
    if t:
        t.rotation_mode = 'XYZ'
        t.rotation_euler = tuple(math.radians(a) for a in t['bent_pose_euler_deg'])
if '--explode' in argv:
    from mathutils import Vector as _V
    cg = _V((0.0, 0.0, 1.2))
    for o in list(bpy.data.objects):
        if o.get('detach') and o.get('state') != 'damaged' and not (o.parent and o.parent.get('detach')):
            if o.name in ('Rotor_Hub', 'Mast', 'Engine_Mount'):
                continue
            w = o.matrix_world.translation.copy()
            d = (w - cg)
            d.z = max(d.z, 0.2 * d.length)
            d.normalize()
            o.matrix_world.translation = w + d * float(arg('--explode', 1.2))
only = [x for x in (arg('--only', '') or '').split(',') if x]
if only:
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.hide_render = not any(o.name.startswith(p) for p in only)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE_NEXT'
sc.render.resolution_x, sc.render.resolution_y = int(arg('--w', 1600)), int(arg('--h', 800))
sc.render.image_settings.file_format = 'PNG'
sc.render.film_transparent = '--transp' in argv
w = bpy.data.worlds.new('w'); w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.55, 0.62, 0.72, 1)
w.node_tree.nodes['Background'].inputs[1].default_value = 1.0
sc.world = w
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sun.data.energy = 4
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-30)); sc.collection.objects.link(sun)
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, -0.001))
g = bpy.context.active_object
gm = bpy.data.materials.new('g'); gm.diffuse_color = (0.3, 0.3, 0.28, 1); g.data.materials.append(gm)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
out = pathlib.Path(arg('--out')); out.parent.mkdir(parents=True, exist_ok=True)
ctr = Vector([float(x) for x in (arg('--ctr', '0.7,0,1.4')).split(',')])
for v in arg('--views', 'side').split(','):
    cd = cam.data
    if v in ('side', 'sideL', 'top', 'front', 'back', 'topU', 'below'):
        cd.type = 'ORTHO'; cd.ortho_scale = float(arg('--scale', 10.5))
        d = {'side': (0, -30, 0), 'sideL': (0, 30, 0), 'top': (0, 0, 40), 'topU': (0, 0, 40), 'below': (0, 0, -40), 'front': (-30, 0, 0), 'back': (30, 0, 0)}[v]
        cam.location = ctr + Vector(d)
        cam.rotation_euler = {'side': (math.radians(90), 0, 0), 'sideL': (math.radians(90), 0, math.radians(180)), 'topU': (0, 0, math.radians(-90)), 'below': (math.radians(180), 0, 0), 'top': (0, 0, 0), 'front': (math.radians(90), 0, math.radians(-90)), 'back': (math.radians(90), 0, math.radians(90))}[v]
    else:
        cd.type = 'PERSP'; cd.lens = float(arg('--lens', 35))
        a = {'three': (-1, -1, 0.5), 'rear3': (1, -1, 0.4), 'three_l': (-1, 1, 0.5), 'close': (-1, -1, 0.3), 'rear_r': (1, 1, 0.4), 'rear_l': (1, -1, 0.4), 'front_r': (-1, 1, 0.5), 'front_l': (-1, -1, 0.5), 'below_rear_r': (1, 1, -0.6), 'below_rear_l': (1, -1, -0.6), 'below_front': (-1, 0.8, -0.6)}[v]
        dist = float(arg('--dist', 11))
        cam.location = ctr + Vector(a).normalized() * dist
        cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
    g.hide_render = v.startswith('below')       # the ground plane would hide the belly
    sc.render.filepath = str(out) + '_' + v + '.png'
    bpy.ops.render.render(write_still=True)
