# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""1987 Ford LTD Crown Victoria police sedan, Chicago Police Department, built in Blender 4.2 (headless) from the drawing and the photographs listed in cv_geom.py, livery.py and README.md.

  python -I examples/crown-victoria/blender/livery.py
  blender -b -P examples/crown-victoria/blender/build_crownvic.py -- [--out examples/crown-victoria/assets/crown_victoria_cpd87.glb] [--lod1 <path>] [--blend <path>]

How it is made. The body is one solid: the lower body lofted through sections read off the drawing (top centre line, shoulder bevel, crease, side, rocker), united with the greenhouse lofted
through its own sections (the roof line, the side glass leaning in, the A- and C-pillars as the corners of those sections). From that solid the exact boolean cuts the cabin, the window
openings, the wheel houses and 4 mm panel gaps (doors, hood, trunk lid, fuel door); the cut faces take the cutters' materials (interior, rubber, wheel house, gap). The glass, the
mouldings, the lamps, the bumpers, the light rack, the interior and the wheels are separate meshes laid on the body's surface by ray casts. The paint's colour comes from livery.py's
atlas through side-projected UVs.

Frame: origin on the ground at the middle of the wheelbase, nose +X, up +Z, the left (driver's) side +Y (glb: Y up, nose +X, left -Z).
Nodes: CrownVic87 (root) > Body, Glass, Trim, Lamps_Head, Lamps_Park, Lamps_Tail, Lamps_Marker, Interior, Underbody, Rack, Beacon_L, Beacon_R, Speaker, Wheel_FL/FR/RL/RR (pivot at
the wheel centre; spin about Y, the front ones steer about Z).
"""
import json
import math
import pathlib
import zipfile
import sys
import time

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cv_geom as G  # noqa: E402
import carkit as CK  # noqa: E402

V3 = Vector
ROOT = HERE.parent
TEX = ROOT / 'textures_in'
LIB = pathlib.Path('D:/REPO/ferret/lib/ferret-assets')
SCRATCH = pathlib.Path('D:/temp/take37/cab')
T0 = time.time()


def log(*a):
    print(f'[{time.time() - T0:6.1f}s]', *a, flush=True)


# ---- materials ---------------------------------------------------------------------------------------------------------------------------------------------------------------
# (sRGB colour, metallic, roughness, extra). Colours of things not seen in the photographs are estimates (README).
MATS = {
    'paint': ((243, 243, 240), 0.0, 0.30, {'tex': 'livery_color.png', 'coat': 1.0, 'coat_rough': 0.04}),
    'under': ((30, 30, 30), 0.0, 0.9, {}),
    'gap': ((6, 6, 6), 0.0, 0.9, {}),
    'well': ((16, 16, 16), 0.0, 0.95, {}),
    'seal': ((12, 12, 12), 0.0, 0.6, {}),
    'interior': ((60, 60, 64), 0.0, 0.45, {'name': 'M_vinyl', 'emit': (0.10, 0.10, 0.105)}),         # black vinyl of the pillars and door panels (the blue interior of the 1987 patrol car in the Barn Finds photograph)
    'carpet': ((90, 98, 130), 0.0, 1.0, {'lib': 'rug', 'tile': 0.6, 'tint': (0.50, 0.50, 0.51), 'name': 'M_floor', 'emit': (0.07, 0.07, 0.072)}),     # grey carpet
    'headliner': ((170, 176, 195), 0.0, 0.95, {'lib': 'gray-fabric1', 'tile': 0.4, 'tint': (0.78, 0.78, 0.80), 'name': 'M_roofcloth', 'emit': (0.20, 0.20, 0.205)}),
    'seatcloth': ((120, 128, 160), 0.0, 0.92, {'lib': 'cloth-grey', 'tile': 0.18, 'tint': (0.58, 0.58, 0.60), 'name': 'M_cloth', 'emit': (0.12, 0.12, 0.125)}),    # grey velour
    'dash': ((44, 44, 47), 0.0, 0.4, {'name': 'M_panel', 'emit': (0.07, 0.07, 0.075)}),
    'bezel': ((120, 122, 128), 0.8, 0.32, {}),
    'pad': ((18, 18, 20), 0.0, 0.5, {'name': 'M_pad', 'emit': (0.035, 0.035, 0.04)}),          # the soft black top of the dash
    'wood': ((110, 55, 28), 0.0, 0.35, {'name': 'M_woodgrain', 'tex': 'walnut_color.png', 'emit_tex': 0.30}),   # walnut-grain trim (gauges.py draws it)
    'brightwork': ((205, 207, 212), 0.6, 0.2, {'name': 'M_brightwork', 'emit': (0.13, 0.13, 0.14)}),   # the cab's bright trim (no environment map in the cab)
    'vent': ((28, 30, 36), 0.0, 0.6, {'name': 'M_ventgrille', 'emit': (0.02, 0.022, 0.03)}),
    'glass_cluster': ((12, 13, 15), 0.0, 0.05, {'name': 'M_glass_cluster', 'alpha': 0.25}),
    'amber_lit': ((255, 150, 20), 0.0, 0.3, {}),
    'blue_lit': ((40, 90, 230), 0.0, 0.3, {}),
    'lamp_lens': ((235, 232, 220), 0.0, 0.3, {}),
    'radio_grey': ((120, 122, 126), 0.0, 0.5, {}),
    'red_lit': ((220, 30, 25), 0.0, 0.3, {}),
    'gauge': ((8, 8, 10), 0.0, 0.2, {}),
    'chrome': ((235, 235, 235), 1.0, 0.07, {}),
    'black': ((14, 14, 15), 0.0, 0.45, {}),
    'rubber': ((20, 20, 20), 0.0, 0.85, {}),
    'tyre': ((24, 24, 24), 0.0, 0.88, {}),
    'wheel': ((12, 12, 13), 0.3, 0.35, {}),
    'steel': ((60, 60, 62), 0.6, 0.5, {}),
    'glass': ((232, 244, 238), 0.0, 0.0, {'trans': 1.0, 'ior': 1.52}),          # float glass, a faint green
    'mirror': ((200, 206, 215), 0.5, 0.08, {'emit': (0.22, 0.25, 0.32)}),        # no environment map in the cab: an emissive sky tint stands for the reflection
    'lens_clear': ((250, 250, 250), 0.0, 0.02, {'trans': 1.0, 'ior': 1.49}),
    'reflector': ((210, 210, 210), 1.0, 0.12, {}),
    'lens_amber': ((255, 135, 10), 0.0, 0.03, {'trans': 1.0, 'ior': 1.49}),
    'lens_red': ((215, 12, 10), 0.0, 0.03, {'trans': 1.0, 'ior': 1.49}),
    'lens_blue': ((40, 95, 255), 0.0, 0.03, {'trans': 1.0, 'ior': 1.49}),
    'badge': ((22, 50, 140), 0.3, 0.25, {}),
    'plate': ((255, 255, 255), 0.0, 0.4, {'tex': 'plate_color.png'}),
    'bulb': ((250, 250, 245), 0.0, 0.05, {'alpha': 0.5}),
    'caliper': ((58, 58, 60), 0.4, 0.5, {}),
    'drum': ((52, 50, 48), 0.6, 0.55, {}),
    'spring': ((30, 30, 32), 0.3, 0.45, {}),
    'gauges': ((255, 255, 255), 0.0, 0.25, {'tex': 'gauges_color.png', 'emit_tex': 0.8}),        # the cluster is lit from behind
    'radio': ((30, 32, 34), 0.3, 0.4, {}),
}
_mc = {}


def lin(c):
    return tuple(((x / 255 + 0.055) / 1.055) ** 2.4 if x / 255 > 0.04045 else x / 255 / 12.92 for x in c)


_img = {}


def lib_image(name, kind):
    key = (name, kind)
    if key in _img:
        return _img[key]
    cat = json.load(open(LIB / 'catalog.json'))['packages']
    zf = zipfile.ZipFile(LIB / cat['tex-' + name]['url'])
    member = f'textures/{name}/{kind}.webp'
    if member not in zf.namelist():
        _img[key] = None
        return None
    d = SCRATCH / 'libcache'
    d.mkdir(parents=True, exist_ok=True)
    p = d / f'{name}_{kind}.webp'
    p.write_bytes(zf.read(member))
    im = bpy.data.images.load(str(p))
    im.name = f'{name}_{kind}'
    if max(im.size) > 1024:
        im.scale(1024, 1024)
    im.pack()
    _img[key] = im
    return im


def _lib_nodes(nt, b, ex, met):
    """A material of the shared library: base colour (tinted), normal and roughness maps; the UVs are in metres, 'tile' metres per repeat."""
    name = ex['lib']
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1 / ex.get('tile', 0.5),) * 3
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nt.links.new(tc.outputs['UV'], mp.inputs['Vector'])
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = lib_image(name, 'basecolor')
    t.image.colorspace_settings.name = 'sRGB'
    nt.links.new(mp.outputs['Vector'], t.inputs['Vector'])
    col = t.outputs['Color']
    if 'tint' in ex:
        mx = nt.nodes.new('ShaderNodeMix')
        mx.data_type = 'RGBA'
        mx.blend_type = 'MULTIPLY'
        mx.inputs['Factor'].default_value = 1.0
        nt.links.new(col, mx.inputs['A'])
        mx.inputs['B'].default_value = (*lin([int(255 * v) for v in ex['tint']]), 1)
        col = mx.outputs['Result']
    nt.links.new(col, b.inputs['Base Color'])
    nim = lib_image(name, 'normal')
    if nim is not None:
        nn = nt.nodes.new('ShaderNodeTexImage')
        nn.image = nim
        nn.image.colorspace_settings.name = 'Non-Color'
        nt.links.new(mp.outputs['Vector'], nn.inputs['Vector'])
        nm = nt.nodes.new('ShaderNodeNormalMap')
        nt.links.new(nn.outputs['Color'], nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    oim = lib_image(name, 'orm')
    if oim is not None:
        o = nt.nodes.new('ShaderNodeTexImage')
        o.image = oim
        o.image.colorspace_settings.name = 'Non-Color'
        nt.links.new(mp.outputs['Vector'], o.inputs['Vector'])
        sp = nt.nodes.new('ShaderNodeSeparateColor')
        nt.links.new(o.outputs['Color'], sp.inputs['Color'])
        nt.links.new(sp.outputs['Green'], b.inputs['Roughness'])


def metres_uv(ob, kinds):
    """UVs in metres by a box projection for the faces whose materials come from the library."""
    me = ob.data
    names = {MATS[k][3].get('name', 'M_' + k) for k in kinds}
    idx = {i for i, mm in enumerate(me.materials) if mm and mm.name in names}
    if not idx:
        return
    bm = bmesh.new()
    bm.from_mesh(me)
    uvl = bm.loops.layers.uv.verify()
    for f in bm.faces:
        if f.material_index in idx:
            n = f.normal
            ax = max(range(3), key=lambda i: abs(n[i]))
            a, b = [(1, 2), (0, 2), (0, 1)][ax]
            for lp in f.loops:
                lp[uvl].uv = (lp.vert.co[a], lp.vert.co[b])
    bm.to_mesh(me)
    bm.free()


def mat(kind):
    if kind in _mc:
        return _mc[kind]
    c, met, rough, ex = MATS[kind]
    m = bpy.data.materials.new(ex.get('name', 'M_' + kind))      # cab materials have their own names and emissive fill (the game's generic fill matches the library's names)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*lin(c), 1)
    b.inputs['Metallic'].default_value = met
    b.inputs['Roughness'].default_value = rough
    if 'lib' in ex:
        _lib_nodes(nt, b, ex, met)
    if 'tex' in ex:
        im = nt.nodes.new('ShaderNodeTexImage')
        im.image = bpy.data.images.load(str(TEX / ex['tex']))
        im.image.colorspace_settings.name = 'sRGB'
        nt.links.new(im.outputs['Color'], b.inputs['Base Color'])
        if 'emit_tex' in ex:
            nt.links.new(im.outputs['Color'], b.inputs['Emission Color'])
            b.inputs['Emission Strength'].default_value = ex['emit_tex']
    if 'trans' in ex:                                       # glass and lenses: transmission (glTF KHR_materials_transmission + ior), tinted by the base colour
        b.inputs['Transmission Weight'].default_value = ex['trans']
        b.inputs['IOR'].default_value = ex.get('ior', 1.5)
    if 'coat' in ex:
        b.inputs['Coat Weight'].default_value = ex['coat']
        b.inputs['Coat Roughness'].default_value = ex['coat_rough']
    if 'emit' in ex:
        b.inputs['Emission Color'].default_value = (*ex['emit'], 1)
        b.inputs['Emission Strength'].default_value = 1.0
    if 'alpha' in ex:
        b.inputs['Alpha'].default_value = ex['alpha']
        if hasattr(m, 'surface_render_method'):
            m.surface_render_method = 'BLENDED'
        m.blend_method = 'BLEND'
    _mc[kind] = m
    return m


# ---- mesh building -----------------------------------------------------------------------------------------------------------------------------------------------------------
class Mesh:
    def __init__(self):
        self.bm = bmesh.new()
        self.kinds = []

    def mi(self, kind):
        if kind not in self.kinds:
            self.kinds.append(kind)
        return self.kinds.index(kind)

    def face(self, vs, kind):
        try:
            f = self.bm.faces.new(vs)
        except ValueError:
            return None
        f.material_index = self.mi(kind)
        return f

    def loft(self, rings, kind, closed=True, caps=False, loop=False):
        """Rings of points (same count) joined in order; closed: each ring is a loop; caps: n-gon ends; loop: the last ring joins the first."""
        vs = [[self.bm.verts.new(p) for p in r] for r in rings]
        n = len(rings[0])
        m = n if closed else n - 1
        pairs = list(zip(vs, vs[1:])) + ([(vs[-1], vs[0])] if loop else [])
        for ra, rb in pairs:
            for k in range(m):
                self.face((ra[k], ra[(k + 1) % n], rb[(k + 1) % n], rb[k]), kind)
        if caps:
            self.face(list(reversed(vs[0])), kind)
            self.face(vs[-1], kind)
        return vs

    def grid(self, rows, kind):
        return self.loft(rows, kind, closed=False)

    def tube(self, path, r, kind, seg=8, cap=True, loop=False):
        rings = []
        n = len(path)
        for i, p in enumerate(path):
            a = path[(i + 1) % n] if loop else path[min(i + 1, n - 1)]
            b = path[(i - 1) % n] if loop else path[max(i - 1, 0)]
            t = (a - b).normalized()
            up = V3((0, 0, 1)) if abs(t.z) < 0.9 else V3((1, 0, 0))
            u = t.cross(up).normalized()
            w = t.cross(u).normalized()
            rr = r[i] if isinstance(r, (list, tuple)) else r
            rings.append([p + (u * math.cos(2 * math.pi * k / seg) + w * math.sin(2 * math.pi * k / seg)) * rr for k in range(seg)])
        return self.loft(rings, kind, caps=cap and not loop, loop=loop)

    def cyl(self, p0, p1, r, kind, seg=16, cap=True, r1=None):
        p0, p1 = V3(p0), V3(p1)
        return self.tube([p0, p1], [r, r if r1 is None else r1], kind, seg=seg, cap=cap)

    def box(self, c, size, kind, axes=None):
        return self.rbox(c, size, 0.0, kind, axes)

    def rbox(self, c, size, r, kind, axes=None, seg=2):
        """A box with its edges rounded by r (0: sharp), centred at c with the sizes along the (orthonormal) axes."""
        ex, ey, ez = axes or (V3((1, 0, 0)), V3((0, 1, 0)), V3((0, 0, 1)))
        M = Matrix((
            (ex.x * size[0], ey.x * size[1], ez.x * size[2], c[0]),
            (ex.y * size[0], ey.y * size[1], ez.y * size[2], c[1]),
            (ex.z * size[0], ey.z * size[1], ez.z * size[2], c[2]),
            (0, 0, 0, 1)))
        tmp = bmesh.new()
        bmesh.ops.create_cube(tmp, size=1.0, matrix=M)
        if r > 0:
            bmesh.ops.bevel(tmp, geom=list(tmp.edges) + list(tmp.verts), offset=min(r, 0.49 * min(size)), offset_type='OFFSET', segments=seg, profile=0.5, affect='EDGES',
                            clamp_overlap=True)
        self.merge(tmp, kind)

    def merge(self, tmp, kind):
        mi = self.mi(kind)
        vmap = {v: self.bm.verts.new(v.co) for v in tmp.verts}
        for f in tmp.faces:
            try:
                nf = self.bm.faces.new([vmap[v] for v in f.verts])
                nf.material_index = mi
            except ValueError:
                pass
        tmp.free()

    def disc(self, c, normal, r, kind, seg=24):
        """A flat disc (a fan) at c facing `normal`."""
        n = V3(normal).normalized()
        up = V3((0, 0, 1)) if abs(n.z) < 0.9 else V3((1, 0, 0))
        u = n.cross(up).normalized()
        w = n.cross(u).normalized()
        ring = [self.bm.verts.new(V3(c) + (u * math.cos(2 * math.pi * k / seg) + w * math.sin(2 * math.pi * k / seg)) * r) for k in range(seg)]
        self.face(ring, kind)

    def finish(self, name, parent=None, sharp=35.0, origin=None):
        bm = self.bm
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        for k in self.kinds:
            me.materials.append(mat(k))
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        if origin is not None:
            me.transform(Matrix.Translation(-V3(origin)))
            ob.location = V3(origin)
        if parent is not None:
            ob.parent = parent
        smooth(ob, sharp)
        return ob


def smooth(ob, angle):
    with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle))


def empty(name, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    e.location = loc
    e.parent = parent
    return e


def boolean(ob, cutters, op, solver='EXACT', self_test=False):
    """Apply a boolean (exact by default) of ob with the cutter objects (deleted afterwards); the new faces take the cutters' materials."""
    col = bpy.data.collections.new('cutters_' + op)
    bpy.context.scene.collection.children.link(col)
    for c in cutters:
        col.objects.link(c)
        c.hide_render = True
    md = ob.modifiers.new('bool', 'BOOLEAN')
    md.operation = op
    md.solver = solver
    md.operand_type = 'COLLECTION'
    md.collection = col
    if solver == 'EXACT':
        md.material_mode = 'TRANSFER'
        md.use_hole_tolerant = True
        md.use_self = self_test
    with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
        bpy.ops.object.modifier_apply(modifier=md.name)
    for c in cutters:
        bpy.data.objects.remove(c, do_unlink=True)
    bpy.data.collections.remove(col)


def bvh_of(obs):
    bm = bmesh.new()
    for ob in obs:
        me = ob.data.copy()
        me.transform(ob.matrix_world)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    bm.normal_update()
    return BVHTree.FromBMesh(bm)


# ---- the sections -------------------------------------------------------------------------------------------------------------------------------------------------------------
def chaikin(pts, it=2):
    for _ in range(it):
        out = [pts[0]]
        for (ay, az), (by, bz) in zip(pts, pts[1:]):
            out.append((0.75 * ay + 0.25 * by, 0.75 * az + 0.25 * bz))
            out.append((0.25 * ay + 0.75 * by, 0.25 * az + 0.75 * bz))
        out.append(pts[-1])
        pts = out
    return pts


def lower_half(x):
    """The lower body's half section at x, (y, z) from the top of the centre line out over the shoulder, down the side and under the rocker to the bottom of the centre line."""
    w = G.plan_half_width(x)
    ye = G.Y_EDGE - (G.W - w)
    zt, zc, zb = G.top_z(x), G.crease_z(x), G.bottom_z(x)
    crown = 0.0 if G.X_C_PILLAR <= x < G.X_COWL else 0.016
    ze = max(zt - crown, zc + 0.03)
    zt = max(zt, ze)
    pts = [(0.0, zt), (0.45 * ye, zt - crown * 0.2), (0.86 * ye, ze + crown * 0.03), (ye, ze), (ye + 0.38 * (w - ye), ze - 0.22 * (ze - zc)), (w - 0.003, zc + 0.008),
           (w, zc - 0.006), (w - 0.003, zc - 0.11), (w - 0.009, 0.5 * (zc + zb) + 0.05), (w - 0.017, zb + 0.10), (w - 0.040, zb + 0.022), (w - 0.10, zb), (0.5 * w, zb), (0.0, zb)]
    return chaikin(pts, 3)


def gh_half(x, inset=0.0):
    """The greenhouse's half section at x: the top (roof, windscreen or backlight) and the side glass's plane down to under the belt. Outside its own span it is sunk under the deck
    and the hood so the union has no coplanar faces."""
    zt = G.roof_z(x) - inset
    if x > G.X_COWL - 0.004 or x < G.X_BACKLIGHT_BASE + 0.004:
        zt -= 0.012
    zb = G.Z_BELT - 0.045
    zre = max(min(G.GH_Z_ROOF_EDGE - inset, zt - 0.022), zb + 0.02)
    crown = 0.010 + 0.012 * min(max((zt - 1.30) / 0.08, 0.0), 1.0)
    ys = G.gh_side_y(zre) - inset
    zm = 0.5 * (zb + zre)
    pts = [(0.0, zt), (0.5 * ys, zt - 0.3 * crown), (ys - 0.05, zt - crown), (ys, zre), (G.gh_side_y(zm) - inset, zm), (G.gh_side_y(zb) - inset, zb), (0.5 * ys, zb), (0.0, zb)]
    return chaikin(pts, 3)


X_HUMP = (G.X(470.0), G.X(625.0))       # the rear wheel houses stand into the cabin between these


def cabin_half(x):
    """The cabin's half section (what the boolean takes out): 35 mm inside the greenhouse, the door's inner skin at 0.83 m, the floor at 0.36 m; narrower over the rear wheel houses."""
    t = 0.035
    zt = G.roof_z(x) - t
    zre = max(min(G.GH_Z_ROOF_EDGE - t, zt - 0.022), G.Z_BELT + 0.01)
    ys = G.gh_side_y(zre) - t
    yd = 0.60 if X_HUMP[0] < x < X_HUMP[1] else 0.83
    pts = [(0.0, zt), (0.5 * ys, zt - 0.004), (ys - 0.05, zt - 0.012), (ys, zre), (G.GH_Y_BELT - t, G.Z_BELT), (0.83, G.Z_BELT - 0.06), (0.83, 0.80), (yd, 0.77), (yd, 0.42),
           (yd - 0.06, 0.36), (0.0, 0.36)]
    return chaikin(pts, 1)


def ring3(x, half):
    return [V3((x, y, z)) for y, z in half] + [V3((x, -y, z)) for y, z in reversed(half[1:-1])]


def stations(x0, x1, step, dense=0.12, fine=0.01):
    xs, x = [], x0
    while x < x1 - 1e-6:
        xs.append(x)
        x += fine if min(x - x0, x1 - x) < dense else step
    xs.append(x1)
    return xs


def at_z(half, z, outer=True):
    """The largest y where the half section crosses the height z."""
    best = None
    for (ay, az), (by, bz) in zip(half, half[1:]):
        if (az - z) * (bz - z) <= 0 and az != bz:
            y = ay + (by - ay) * (z - az) / (bz - az)
            best = y if best is None else max(best, y)
    return best if best is not None else half[0][0]


def at_y(half, y):
    """The highest z where the half section crosses the half width y."""
    best = None
    for (ay, az), (by, bz) in zip(half, half[1:]):
        if (ay - y) * (by - y) <= 0 and ay != by:
            z = az + (bz - az) * (y - ay) / (by - ay)
            best = z if best is None else max(best, z)
    return best if best is not None else half[0][1]


def side_y(x, z):
    return at_z(lower_half(x), z)


def top_at(x, y):
    return at_y(lower_half(x), abs(y))


def densify(path, step=0.015):
    out = []
    for a, b in zip(path, path[1:]):
        n = max(1, int(math.ceil((V3(b) - V3(a)).length / step)))
        for k in range(n):
            out.append(V3(a).lerp(V3(b), k / n))
    out.append(V3(path[-1]))
    return out


def px_path(pairs):
    return [V3((G.X(a), 0.0, G.Z(b))) for a, b in pairs]


# ---- cutters -------------------------------------------------------------------------------------------------------------------------------------------------------------------
def prism_y(poly_xz, y0, y1, kind, name):
    """A polygon in XZ (as V3 with y ignored) extruded from y0 to y1."""
    m = Mesh()
    m.loft([[V3((p.x, y0, p.z)) for p in poly_xz], [V3((p.x, y1, p.z)) for p in poly_xz]], kind, caps=True)
    return m.finish(name)


def prism_x(poly_yz, x0, x1, kind, name):
    m = Mesh()
    m.loft([[V3((x0, y, z)) for y, z in poly_yz], [V3((x1, y, z)) for y, z in poly_yz]], kind, caps=True)
    return m.finish(name)


def side_groove(m, path, s, w=0.0022, depth=0.010, loop=False, z_floor=None):
    """A 4 mm gap cut along a path in XZ on the side s (+1 left, -1 right): a thin slab from `depth` under the body's side out past it."""
    path = densify(path) if not loop else densify(path + [path[0]])[:-1]
    rings = []
    n = len(path)
    for i, p in enumerate(path):
        a = path[(i + 1) % n] if loop else path[min(i + 1, n - 1)]
        b = path[(i - 1) % n] if loop else path[max(i - 1, 0)]
        t = V3((a.x - b.x, 0, a.z - b.z)).normalized()
        nn = V3((-t.z, 0, t.x))
        yin = side_y(p.x, p.z) - depth
        pa, pb = p + nn * w, p - nn * w
        rings.append([V3((pa.x, s * yin, pa.z)), V3((pb.x, s * yin, pb.z)), V3((pb.x, s * 1.4, pb.z)), V3((pa.x, s * 1.4, pa.z))])
    m.loft(rings, 'gap', caps=not loop, loop=loop)


def top_groove(m, path_xy, w=0.0022, depth=0.010, tail_floor=None):
    path = densify(path_xy)
    rings = []
    n = len(path)
    for i, p in enumerate(path):
        a, b = path[min(i + 1, n - 1)], path[max(i - 1, 0)]
        t = V3((a.x - b.x, a.y - b.y, 0)).normalized()
        nn = V3((-t.y, t.x, 0))
        zin = top_at(p.x, p.y) - depth
        if tail_floor is not None and p.x < G.X_TAIL + 0.02:
            zin = min(zin, tail_floor)
        pa, pb = p + nn * w, p - nn * w
        rings.append([V3((pa.x, pa.y, zin)), V3((pb.x, pb.y, zin)), V3((pb.x, pb.y, 1.7)), V3((pa.x, pa.y, 1.7))])
    m.loft(rings, 'gap', caps=True)


def rrect_path(x0, z0, x1, z1, r, n=4):
    pts = []
    for cx, cz, a0 in ((x1 - r, z1 - r, 0), (x0 + r, z1 - r, 90), (x0 + r, z0 + r, 180), (x1 - r, z0 + r, 270)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append(V3((cx + r * math.cos(a), 0, cz + r * math.sin(a))))
    return pts


# ---- the body ------------------------------------------------------------------------------------------------------------------------------------------------------------------
def build_body(root):
    m = Mesh()
    xs = stations(G.X_TAIL, G.X_NOSE, 0.012, fine=0.006)
    m.loft([ring3(x, lower_half(x)) for x in xs], 'paint', caps=True)
    body = m.finish('Body', root, sharp=40)
    g = Mesh()
    xg = stations(G.X_BACKLIGHT_BASE - 0.03, G.X_COWL + 0.03, 0.008, dense=0.0)
    g.loft([ring3(x, gh_half(x)) for x in xg], 'paint', caps=True)
    gh = g.finish('Greenhouse', root)
    log('body lofted', len(body.data.polygons), 'greenhouse', len(gh.data.polygons))
    boolean(body, [gh], 'UNION')
    log('union', len(body.data.polygons))
    return body


def body_cutters():
    cut = []
    # the cabin
    c = Mesh()
    xc = stations(G.X_BACKLIGHT_BASE + 0.10, G.X_COWL - 0.03, 0.02, dense=0.0)
    c.loft([ring3(x, cabin_half(x)) for x in xc], 'interior', caps=True)
    cut.append(c.finish('cut_cabin'))
    # the side windows (the sill 3 mm over the belt so no face is coplanar with the shoulder's top)
    for nm, poly in (('front', G.WIN_FRONT_PX), ('rear', G.WIN_REAR_PX), ('vent', G.WIN_VENT_PX)):
        pts = [V3((G.X(a), 0, max(G.Z(b), G.Z_BELT + 0.003))) for a, b in poly]
        for s in (1, -1):
            ob = prism_y(pts if s > 0 else list(reversed(pts)), s * 0.45, s * 1.4, 'seal', f'cut_win_{nm}_{s}')
            cut.append(ob)
    # the windscreen and the backlight: their outlines seen along X, extruded over their spans
    for nm, d, x0, x1 in (('ws', G.WS, 0.05, G.X_COWL - 0.004), ('bl', G.BL, G.X_BACKLIGHT_BASE + 0.004, G.X(588) + 0.10)):
        poly = [(d['y0'], d['z0']), (d['y1'], d['z1']), (-d['y1'], d['z1']), (-d['y0'], d['z0'])]
        cut.append(prism_x(poly, x0, x1, 'seal', 'cut_' + nm))
    # the wheel houses
    for nm, arch in (('r', G.ARCH_R), ('f', G.ARCH_F)):
        poly = [V3((x, 0, z)) for x, z in arch]
        poly = [V3((arch[0][0], 0, -0.2))] + poly + [V3((arch[-1][0], 0, -0.2))]
        for s in (1, -1):
            cut.append(prism_y(poly if s > 0 else list(reversed(poly)), s * 0.66, s * 1.4, 'well', f'cut_well_{nm}_{s}'))
    # the panel gaps
    gm = Mesh()
    for s in (1, -1):
        side_groove(gm, px_path(G.DOOR_F_FRONT_PX), s)
        side_groove(gm, px_path(G.DOOR_SPLIT_PX), s)
        side_groove(gm, px_path(G.DOOR_R_REAR_PX), s)
        side_groove(gm, [V3((G.X(615.5), 0, G.Z_DOOR_BOTTOM)), V3((G.X(882.5), 0, G.Z_DOOR_BOTTOM))], s)
    fx0, fz0, fx1, fz1 = G.FUEL_PX
    side_groove(gm, rrect_path(G.X(fx0), G.Z(fz1), G.X(fx1), G.Z(fz0), 0.02), -1, loop=True)      # the drawing shows the right side
    # the hood: its rear edge across the cowl, its sides from the cowl's corners in to the grille's width at the nose
    xh = G.X_COWL + 0.012
    top_groove(gm, [V3((xh, -0.87, 0)), V3((xh, 0.87, 0))])
    for s in (1, -1):
        top_groove(gm, [V3((xh - 0.004, s * 0.865, 0)), V3((G.X_NOSE - 0.30, s * 0.70, 0)), V3((G.X_NOSE + 0.05, s * 0.545, 0))])
    # the trunk lid: across in front of the backlight's foot, down both sides, and across the tail panel under its edge
    xt = G.X_BACKLIGHT_BASE - 0.025
    top_groove(gm, [V3((xt, -0.745, 0)), V3((xt, 0.745, 0))])
    for s in (1, -1):
        top_groove(gm, [V3((xt + 0.004, s * 0.742, 0)), V3((G.X_TAIL - 0.06, s * 0.742, 0))], tail_floor=G.top_z(G.X_TAIL) - 0.045)
    gm.box(V3((G.X_TAIL - 0.05, 0, G.top_z(G.X_TAIL) - 0.047)), (0.12, 1.488, 0.0044), 'gap')
    cut.append(gm.finish('cut_gaps'))
    return cut


def uv_paint(body):
    """The paint's UVs: faces that look sideways take the livery atlas by a side projection (see livery.py), the others a white corner; the underside goes to 'under'; the cabin's
    faces split into carpet (floor), headliner (roof) and the vinyl of the rest."""
    me = body.data
    names = [m.name for m in me.materials]

    def slot(kind):
        m = mat(kind)
        if m.name not in names:
            me.materials.append(m)
            names.append(m.name)
        return names.index(m.name)

    ip, iu, ii, ic, ih = slot('paint'), slot('under'), slot('interior'), slot('carpet'), slot('headliner')
    bm = bmesh.new()
    bm.from_mesh(me)
    uvl = bm.loops.layers.uv.verify()
    U0, U1, Z0, Z1 = -2.95, 2.95, 0.15, 1.15
    for f in bm.faces:
        n = f.normal
        if f.material_index == ii:
            c = f.calc_center_median()
            if n.z > 0.7 and c.z < 0.5:
                f.material_index = ic
            elif n.z < -0.7 and c.z > 1.15:
                f.material_index = ih
            continue
        if f.material_index != ip:
            continue
        if n.z < -0.55:
            f.material_index = iu
            continue
        for lp in f.loops:
            p = lp.vert.co
            if abs(n.y) > 0.30:
                zz = min(max(p.z, Z0), Z1)
                if n.y > 0:
                    lp[uvl].uv = ((U1 - p.x) / (U1 - U0), 1.0 - 0.5 * (Z1 - zz) / (Z1 - Z0))
                else:
                    lp[uvl].uv = ((p.x - U0) / (U1 - U0), 0.5 - 0.5 * (Z1 - zz) / (Z1 - Z0))
            else:
                lp[uvl].uv = (0.002, 0.25)
    bm.to_mesh(me)
    bm.free()


# ---- parts: meshes that belong to the body or to one door --------------------------------------------------------------------------------------------------------------------------------
class Parts(dict):
    """Meshes by owner: 'body' or a door key ('FL', 'RL', 'FR', 'RR': front/rear, left/right)."""

    def __missing__(self, k):
        self[k] = Mesh()
        return self[k]


def door_key(front, s):
    return ('F' if front else 'R') + ('L' if s > 0 else 'R')


def seam_px(path_px, row):
    """The column of a door's edge path (pixel pairs, top to bottom) at a pixel row."""
    return interp([(b, a) for a, b in sorted(path_px, key=lambda p: p[1])], row)


def seam_x(edge, z):
    """X of a door seam at height z: 'front' the front door's front edge, 'split' between the doors, 'rear' the rear door's rear edge."""
    row = 223.0 - z * G.K_Z
    if edge == 'split':
        return G.X(725.5)
    return G.X(seam_px(G.DOOR_F_FRONT_PX if edge == 'front' else G.DOOR_R_REAR_PX, row))


def interp(pts, x):
    return G.interp(pts, x)


def owner_spans(xa, xb, z, gap=0.003):
    """Split [xa, xb] at the door seams at height z: (x0, x1, owner) pieces; owner None = body, else (front, ...)."""
    cuts = [(seam_x('rear', z), None, False), (seam_x('split', z), False, True), (seam_x('front', z), True, None)]
    edges = [xa] + [c[0] for c in cuts] + [xb]
    owners = ['body', 'R', 'F', 'body']
    out = []
    for (x0, x1), ow in zip(zip(edges, edges[1:]), owners):
        lo, hi = max(x0, xa), min(x1, xb)
        if hi - lo > 2 * gap:
            out.append((lo + (gap if x0 != xa else 0), hi - (gap if x1 != xb else 0), ow))
    return out


def offset_poly(pts, d):
    """A convex polygon (list of (x, z)) grown by d."""
    n = len(pts)
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
    sgn = 1 if area > 0 else -1
    lines = []
    for i in range(n):
        (x0, z0), (x1, z1) = pts[i], pts[(i + 1) % n]
        tx, tz = x1 - x0, z1 - z0
        ln = math.hypot(tx, tz)
        nx, nz = sgn * tz / ln, -sgn * tx / ln
        lines.append(((x0 + nx * d, z0 + nz * d), (tx, tz)))
    out = []
    for i in range(n):
        (p, t), (q, u) = lines[i - 1], lines[i]
        den = t[0] * u[1] - t[1] * u[0]
        if abs(den) < 1e-12:
            out.append(q)
            continue
        k = ((q[0] - p[0]) * u[1] - (q[1] - p[1]) * u[0]) / den
        out.append((p[0] + t[0] * k, p[1] + t[1] * k))
    return out


DOOR_WINDOWS = {True: [G.WIN_FRONT_PX], False: [G.WIN_REAR_PX, G.WIN_VENT_PX]}
HULL_R_PX = [(590, 77.5), (701, 77.5), (701, 18.5), (633, 18.5), (624, 22.5)]


def door_cutter(front, s, name):
    """The solid a door is cut out by: its lower part (seam to seam, sill to belt, from inside its inner skin out) and its window frame (the window's outline grown by 18 mm,
    from inside the greenhouse's shell out)."""
    zt, zb = G.Z_BELT + 0.004, G.Z_DOOR_BOTTOM
    if front:
        lower = [(G.X(725.5), zt), (G.X(725.5), zb)] + [(G.X(a), G.Z(b)) for a, b in reversed(G.DOOR_F_FRONT_PX)] + [(G.X(893), zt)]
        win = [(G.X(a), G.Z(b)) for a, b in G.WIN_FRONT_PX]
    else:
        lower = [(G.X(725.5), zt), (G.X(581), zt)] + [(G.X(a), G.Z(b)) for a, b in G.DOOR_R_REAR_PX] + [(G.X(725.5), zb)]
        win = [(G.X(a), G.Z(b)) for a, b in HULL_R_PX]
    up = [(x, max(z, G.Z_BELT - 0.002)) for x, z in offset_poly(win, 0.018)]
    lo_pts = [V3((x, 0, z)) for x, z in lower]
    up_pts = [V3((x, 0, z)) for x, z in up]
    # a closed solid needs its outline wound the same way seen from outside on both sides: the right side's runs the other way round
    area = lambda pts: sum(p.x * q.z - q.x * p.z for p, q in zip(pts, pts[1:] + pts[:1]))     # noqa: E731
    if (area(lo_pts) > 0) != (s > 0):
        lo_pts.reverse()
    if (area(up_pts) > 0) != (s > 0):
        up_pts.reverse()
    lo = prism_y(lo_pts, s * 0.80, s * 1.4, 'interior', name)      # the cut faces (the jambs, the doors' inner skins) take this: trim, not body paint
    hi = prism_y(up_pts, s * 0.50, s * 1.4, 'seal', name + '_frame')
    boolean(lo, [hi], 'UNION')
    return lo


def hinge_point(front, s):
    x = G.X(890.0) + 0.004 if front else G.X(725.5) - 0.004
    return V3((x, s * (G.W - 0.012), 0.60))


def split_doors(body, root):
    """Cut the four doors out of the body (each its own node on its front hinge's axis) and the openings into it."""
    doors, cutters = {}, []
    for front in (True, False):
        for s in (1, -1):
            k = door_key(front, s)
            c = door_cutter(front, s, 'cut_door_' + k)
            # the exact solver now and then returns nothing for a sound pair: then again with its self-intersection test on (found for the right front door), then nudged
            for nudge, self_test in ((0.0, False), (0.0, True), (0.00023, True)):
                dup = bpy.data.objects.new('Door_' + k + '_shell', body.data.copy())
                bpy.context.scene.collection.objects.link(dup)
                c2 = bpy.data.objects.new(c.name + '_b', c.data.copy())
                bpy.context.scene.collection.objects.link(c2)
                c2.location = (nudge, nudge * 0.7, -nudge * 0.5)
                bpy.context.view_layer.update()
                boolean(dup, [c2], 'INTERSECT', self_test=self_test)
                if len(dup.data.polygons) > 100:
                    break
                bpy.data.objects.remove(dup, do_unlink=True)
            cutters.append(c)
            e = empty('Door_' + k, hinge_point(front, s), root)
            doors[k] = (e, dup)
            log('door', k, len(dup.data.polygons))
    boolean(body, cutters, 'DIFFERENCE')
    bpy.context.view_layer.update()
    for k, (e, ob) in doors.items():
        attach(ob, e)
        smooth(ob, 40)
    return {k: e for k, (e, _) in doors.items()}


def attach(ob, parent):
    """Parent keeping the world placement."""
    bpy.context.view_layer.update()
    ob.parent = parent
    ob.matrix_parent_inverse = parent.matrix_world.inverted()


def finish_parts(parts, name, root, doors, sharp=50):
    obs = {}
    for k, m in parts.items():
        if not m.kinds:
            continue
        ob = m.finish(name if k == 'body' else f'{name}_{k}', root, sharp=sharp)
        if k != 'body':
            attach(ob, doors[k])
        obs[k] = ob
    return obs


# ---- glass ---------------------------------------------------------------------------------------------------------------------------------------------------------------------
def build_glass(bvh):
    """Each pane a 5 mm sheet laid 6 mm inside the body's surface, in a rubber gasket; the windscreen and the backlight with bright reveal mouldings round the gaskets."""
    parts = Parts()
    inset = 0.006

    def ray(o, d):
        hit, nrm, _, _ = bvh.ray_cast(V3(o), V3(d).normalized(), 4.0)
        return hit, nrm

    for front, polys in ((True, [G.WIN_FRONT_PX]), (False, [G.WIN_REAR_PX, G.WIN_VENT_PX])):
        for poly in polys:
            pts = [(G.X(a), G.Z(b)) for a, b in poly]
            if len(pts) == 3:
                pts = [pts[0], pts[1], pts[2], pts[2]]
            cx = sum(p[0] for p in pts) / 4
            cz = sum(p[1] for p in pts) / 4
            grow = [(x + 0.009 * math.copysign(1, x - cx), max(z + 0.009 * math.copysign(1, z - cz), G.Z_BELT - 0.03)) for x, z in pts]
            for s in (1, -1):
                rows = []
                nu, nv = 20, 14
                for j in range(nv + 1):
                    v = j / nv
                    row = []
                    for i in range(nu + 1):
                        u = i / nu
                        a = V3((grow[0][0], 0, grow[0][1])).lerp(V3((grow[1][0], 0, grow[1][1])), u)
                        b = V3((grow[3][0], 0, grow[3][1])).lerp(V3((grow[2][0], 0, grow[2][1])), u)
                        p = a.lerp(b, v)
                        hit, nrm = ray((p.x, s * 1.5, p.z), (0, -s, 0))
                        if hit is None or abs(hit.y) < 0.4:
                            hit, nrm = V3((p.x, s * G.gh_side_y(p.z), p.z)), V3((0, s, 0))
                        row.append(hit - nrm * inset)
                    rows.append(row)
                m = parts[door_key(front, s)]
                ns = CK.pane(m, rows, 0.005, (0, s, 0))
                CK.seal(m, rows, ns, 0.016, 0.005)
    for d, xa, xb, toward in ((G.WS, 0.15, G.X_COWL, (0.6, 0, 1)), (G.BL, G.X_BACKLIGHT_BASE, G.X(600), (-0.6, 0, 1))):
        xs = [xa + (xb - xa) * k / 200 for k in range(201)]
        xs = [x for x in xs if d['z0'] - 0.012 <= G.roof_z(x) <= d['z1'] + 0.012]
        x0, x1 = min(xs), max(xs)
        rows = []
        nu, nv = 30, 24
        for j in range(nu + 1):
            x = x0 + (x1 - x0) * j / nu
            z = min(max(G.roof_z(x), d['z0']), d['z1'])
            hw = d['y0'] + (d['y1'] - d['y0']) * (z - d['z0']) / (d['z1'] - d['z0']) + 0.010
            row = []
            for i in range(nv + 1):
                y = -hw + 2 * hw * i / nv
                hit, nrm = ray((x, y, 2.5), (0, 0, -1))
                row.append(hit - nrm * inset if hit is not None else V3((x, y, z)))
            rows.append(row)
        m = parts['body']
        ns = CK.pane(m, rows, 0.005, toward)
        CK.seal(m, rows, ns, 0.020, 0.005)
        bo, bn = CK.border(rows), CK.border(ns)
        c = sum(bo, V3()) / len(bo)
        rev = []
        for p, nn in zip(bo, bn):
            o = (p - c)
            o = (o - nn * o.dot(nn)).normalized()
            rev.append(p + o * 0.022 + nn * inset)
        CK.strip(m, rev, bn, 0.012, 0.003, 'chrome', loop=True)
    return parts


# ---- trim: mouldings, frames, handles, mirrors, spotlight, antenna, wipers -------------------------------------------------------------------------------------------------------
def on_side(bvh, x, z, s, lift=0.003):
    hit, nrm, _, _ = bvh.ray_cast(V3((x, s * 1.5, z)), V3((0, -s, 0)), 3.0)
    if hit is None:
        return V3((x, s * side_y(x, z), z)), V3((0, s, 0))
    return hit + nrm * lift, nrm


def on_top(bvh, x, y, lift=0.003):
    hit, nrm, _, _ = bvh.ray_cast(V3((x, y, 2.5)), V3((0, 0, -1)), 3.0)
    if hit is None:
        return V3((x, y, top_at(x, y))), V3((0, 0, 1))
    return hit + nrm * lift, nrm


def side_strip(parts, bvh, s, xa, xb, z, width, thick, kind, owner_override=None, lift=0.0):
    """A flat moulding along the side at height z from xa to xb, split at the door seams so each piece goes with its door."""
    for x0, x1, ow in owner_spans(min(xa, xb), max(xa, xb), z):
        key = owner_override or ('body' if ow == 'body' else door_key(ow == 'F', s))
        xs = [x0 + (x1 - x0) * k / max(2, int((x1 - x0) / 0.02)) for k in range(max(2, int((x1 - x0) / 0.02)) + 1)]
        hits = [on_side(bvh, x, z, s, lift) for x in xs]
        CK.strip(parts[key], [p for p, _ in hits], [n for _, n in hits], width, thick, kind)


def build_trim(bvh):
    parts = Parts()
    for s in (1, -1):
        # window frames: flat bright mouldings round the side openings (the doors' frames)
        for front, polys in ((True, [G.WIN_FRONT_PX]), (False, [G.WIN_REAR_PX, G.WIN_VENT_PX])):
            for poly in polys:
                pts = [(G.X(a), max(G.Z(b), G.Z_BELT + 0.003)) for a, b in poly]
                if len(pts) == 3:
                    pass
                pts = offset_poly(pts, 0.009)
                path = densify([V3((x, 0, z)) for x, z in pts + [pts[0]]], 0.012)[:-1]
                hits = [on_side(bvh, p.x, p.z, s, 0.0) for p in path]
                CK.strip(parts[door_key(front, s)], [p for p, _ in hits], [n for _, n in hits], 0.014, 0.003, 'chrome', loop=True)
            # the vent glass's division bar
        p0 = on_side(bvh, G.X(628.5), G.Z_BELT + 0.004, s, 0.0)
        p1 = on_side(bvh, G.X(628.5), G.Z(20.5), s, 0.0)
        path = [p0[0].lerp(p1[0], k / 12) for k in range(13)]
        CK.strip(parts[door_key(False, s)], path, [p0[1]] * 13, 0.016, 0.004, 'chrome')
        # the belt moulding (split at the doors), the drip rail over the side glass
        side_strip(parts, bvh, s, G.X(584), G.X(889), G.Z_BELT - 0.008, 0.012, 0.005, 'chrome')
        zr = G.GH_Z_ROOF_EDGE + 0.004
        xs = [x for x in [G.X(590) + (G.X(806) - G.X(590)) * k / 120 for k in range(121)] if G.roof_z(x) > zr + 0.01]
        hits = [on_side(bvh, x, zr, s, 0.0) for x in xs]
        CK.strip(parts['body'], [p for p, _ in hits], [n for _, n in hits], 0.010, 0.007, 'chrome')
        # the B-pillar's black appliqué between the door glasses
        rows = []
        for j in range(9):
            z = G.Z_BELT + 0.004 + (G.Z(18.0) - G.Z_BELT) * j / 8
            rows.append([on_side(bvh, x, z, s, 0.0015)[0] for x in (G.X(703.5), G.X(714.5), G.X(725.0))])
        parts['body'].grid(rows if s > 0 else [list(reversed(r)) for r in rows], 'black')
        # the thin side moulding at mid door and the bright lower moulding, each split at the door seams
        for a, b in G.SIDE_MOLD_SEGS_PX:
            side_strip(parts, bvh, s, G.X(a), G.X(b), G.SIDE_MOLD_Z, 0.010, 0.003, 'chrome')
        for a, b in G.MOLDING_SEGS_PX:
            side_strip(parts, bvh, s, G.X(a), G.X(b), 0.5 * (G.MOLDING_Z[0] + G.MOLDING_Z[1]), G.MOLDING_Z[1] - G.MOLDING_Z[0], 0.004, 'chrome')
        # the wheel lip mouldings: flat bright strips round each opening, 1 cm out from its edge
        for arch in (G.ARCH_R, G.ARCH_F):
            cx = sum(x for x, z in arch) / len(arch)
            path = []
            for x, z in arch:
                dd = V3((x - cx, 0, z - G.ZC))
                dd = dd.normalized() * 0.013 if dd.length > 1e-6 else V3()
                path.append(V3((x + dd.x, 0, z + dd.z)))
            path = densify(path, 0.012)
            hits = [on_side(bvh, p.x, p.z, s, 0.0) for p in path]
            CK.strip(parts['body'], [p for p, _ in hits], [n for _, n in hits], 0.022, 0.004, 'chrome')
        # pull handles and the front doors' lock cylinders
        for front, (hx, hz) in ((True, G.HANDLE_F_PX), (False, G.HANDLE_R_PX)):
            m = parts[door_key(front, s)]
            p, n = on_side(bvh, G.X(hx), G.Z(hz), s, 0.0)
            m.rbox(p + n * 0.004, (0.155, 0.010, 0.036), 0.005, 'chrome')
            m.rbox(p + n * 0.006 - V3((0, 0, 0.004)), (0.125, 0.006, 0.014), 0.002, 'black')
            m.rbox(p + n * 0.012 + V3((0, 0, 0.004)), (0.12, 0.006, 0.010), 0.003, 'chrome')
        m = parts[door_key(True, s)]
        p, n = on_side(bvh, G.X(G.LOCK_PX[0]), G.Z(G.LOCK_PX[1]), s, 0.0)
        m.cyl(p, p + n * 0.006, 0.012, 'chrome', seg=16)
        m.cyl(p + n * 0.006, p + n * 0.0065, 0.007, 'black', seg=12)
        # mirrors on the front doors: a chrome head on a stalk, its glass facing back, standing on the door's top ahead of the glass
        base, _ = on_top(bvh, 0.70, s * 0.94, 0.0)
        m.rbox(base + V3((0, 0, 0.012)), (0.085, 0.045, 0.026), 0.008, 'chrome')
        head = V3((0.665, s * 1.035, base.z + 0.085))
        m.cyl(base + V3((0, 0, 0.02)), head + V3((0.01, -s * 0.03, -0.03)), 0.011, 'chrome', seg=10)
        m.rbox(head, (0.055, 0.165, 0.098), 0.02, 'chrome')
        m.rbox(head + V3((-0.0285, 0, 0)), (0.004, 0.150, 0.083), 0.006, 'black')
        m.box(head + V3((-0.0305, 0, 0)), (0.002, 0.140, 0.074), 'mirror')
    m = parts['body']
    # the driver's spotlight on the left A-pillar (its make not known): the lamp aimed forward on its post, the bracket on the pillar, the handle's shaft through it
    zs = 1.13
    xs_ = min((x for x in [0.3 + 0.6 * k / 300 for k in range(301)] if G.roof_z(x) <= zs), default=0.55)
    p, n = on_side(bvh, xs_ - 0.03, zs, 1, 0.0)
    c = p + V3((0.0, 0.085, 0.0))
    CK.round_lamp(m, c + V3((0.06, 0, 0)), (1, 0, 0), 0.066, 0.13, 'lens_clear')
    m.cyl(c + V3((-0.03, 0, -0.068)), c + V3((-0.03, 0, -0.10)), 0.012, 'chrome', seg=10)
    m.rbox(c + V3((-0.03, 0, -0.105)), (0.05, 0.03, 0.02), 0.006, 'chrome')
    m.tube([c + V3((-0.03, 0, -0.105)), c + V3((-0.03, -0.04, -0.10)), p + V3((-0.02, -0.005, -0.04))], 0.009, 'chrome', seg=8)
    m.rbox(p + V3((-0.02, 0.0, -0.04)), (0.07, 0.02, 0.05), 0.008, 'chrome')
    m.cyl(p + V3((-0.02, -0.01, -0.04)), p + V3((-0.02, -0.10, -0.04)), 0.008, 'chrome', seg=8)
    # the radio antenna on the left fender by the cowl
    p, _ = on_top(bvh, G.X_COWL + 0.12, 0.79, 0.0)
    m.cyl(p, p + V3((0, 0, 0.02)), 0.012, 'chrome', seg=10)
    m.cyl(p + V3((0, 0, 0.02)), p + V3((-0.08, 0, 0.80)), 0.0025, 'black', seg=6, r1=0.0015)
    # wipers parked in tandem along the windscreen's foot: both pivots on the cowl, both arms and blades lying parallel toward the passenger's side
    zw = G.WS['z0'] + 0.035
    xw = min((x for x in [0.3 + 0.6 * k / 300 for k in range(301)] if G.roof_z(x) <= zw), default=0.75)
    a, na = on_top(bvh, xw, 0.3, 0.0)
    b, _ = on_top(bvh, xw, -0.3, 0.0)
    along = (b - a).normalized()
    xp = min((x for x in [0.3 + 0.6 * k / 600 for k in range(601)] if G.roof_z(x) <= G.WS['z0'] + 0.004), default=0.80)
    for py in (0.66, 0.06):
        piv, _ = on_top(bvh, xp, py, 0.0)
        CK.wiper_parked(m, piv, along, na, 0.43, 0.46)
    for y in (-0.30, 0.30):
        p, nrm = on_top(bvh, G.X_COWL + 0.06, y, 0.0)
        m.rbox(p + nrm * 0.006, (0.03, 0.018, 0.012), 0.004, 'black')
        m.cyl(p + nrm * 0.010 + V3((-0.012, 0, 0)), p + nrm * 0.010 + V3((-0.02, 0, 0.002)), 0.0025, 'black', seg=6)
    # door hardware on the body: two hinges at each door's front edge, the striker at its rear edge, rubber weatherstrip round each opening's lower part
    for front in (True, False):
        for s in (1, -1):
            h = hinge_point(front, s)
            for z in (0.45, 0.80):
                m.rbox(V3((h.x + 0.004, s * (G.W - 0.06), z)), (0.035, 0.07, 0.055), 0.006, 'black')
            xs = G.X(725.5) - 0.006 if front else G.X(581.0) + 0.006
            m.rbox(V3((xs, s * (G.W - 0.07), 0.82)), (0.012, 0.04, 0.05), 0.004, 'chrome')
            m.cyl(V3((xs + (0.002 if front else -0.002), s * (G.W - 0.08), 0.82)), V3((xs + (0.02 if front else -0.02), s * (G.W - 0.08), 0.82)), 0.006, 'chrome', seg=10)
    return parts


def door_inner(parts):
    """What the doors carry inside: armrests, pulls, window cranks, lock knobs, the inside handles, kick plates."""
    for front in (True, False):
        for s in (1, -1):
            m = parts[door_key(front, s)]
            x0, x1 = (G.X(735), G.X(870)) if front else (G.X(600), G.X(700))
            xm = 0.5 * (x0 + x1)
            m.rbox(V3((xm, s * 0.80, 0.68)), (x1 - x0, 0.07, 0.05), 0.02, 'interior')
            m.rbox(V3((xm + 0.05, s * 0.815, 0.74)), (0.14, 0.03, 0.03), 0.01, 'black')
            c = V3((xm - 0.05, s * 0.826, 0.55))
            m.cyl(c, c - V3((0, s * 0.02, 0)), 0.02, 'chrome', seg=12)
            m.tube([c - V3((0, s * 0.02, 0)), c - V3((-0.07, s * 0.02, 0.04))], 0.006, 'chrome', seg=6)
            m.cyl(c - V3((-0.07, s * 0.02, 0.04)), c - V3((-0.07, s * 0.05, 0.04)), 0.008, 'black', seg=8)
            m.cyl(V3((x1 - 0.06, s * 0.83, 0.93)), V3((x1 - 0.06, s * 0.83, 0.97)), 0.006, 'chrome', seg=8)
            m.rbox(V3((x1 - 0.12, s * 0.826, 0.80)), (0.10, 0.02, 0.03), 0.006, 'chrome')
            m.rbox(V3((xm, s * 0.828, 0.36)), (x1 - x0 - 0.04, 0.008, 0.08), 0.004, 'black')
            for k in range(3):
                m.rbox(V3((xm, s * 0.826, 0.62 - 0.08 * k)), (x1 - x0 - 0.10, 0.006, 0.004), 0.001, 'dash')


# ---- front and rear ends ---------------------------------------------------------------------------------------------------------------------------------------------------------
def bumper(m, front):
    """A chrome bumper: a closed profile swept along a plan path that is nearly straight and wraps back round both corners."""
    sx = 1 if front else -1
    xf = G.X_FBUMP if front else G.X_RBUMP
    zt, zb = (G.Z(138.0), G.Z(170.0)) if front else (G.Z(135.0), G.Z(167.0))
    R, yc = 0.13, 0.88
    path = []
    for k in range(9):
        a = math.radians(80 - 80 * k / 8)
        path.append((xf - sx * (0.03 + R - R * math.cos(a)), -(yc + R * math.sin(a)), V3((sx * math.cos(a), -math.sin(a), 0))))
    for k in range(1, 30):
        y = -yc + 2 * yc * k / 30
        path.append((xf - sx * 0.03 * (y / yc) ** 2, y, V3((sx, 0, 0))))
    for k in range(9):
        a = math.radians(80 * k / 8)
        path.append((xf - sx * (0.03 + R - R * math.cos(a)), yc + R * math.sin(a), V3((sx * math.cos(a), math.sin(a), 0))))
    h = zt - zb
    prof = [(-0.17, zt - 0.006), (-0.02, zt), (0.0, zt - 0.010), (0.006, zt - 0.05), (0.006, zb + 0.07), (0.0, zb + 0.03), (-0.03, zb), (-0.17, zb)]
    rings = []
    for x, y, n in path:
        rings.append([V3((x, y, 0)) + n * dx + V3((0, 0, z)) for dx, z in prof])
    m.loft(rings, 'chrome', caps=True)
    strip = []
    for x, y, n in path[4:-4]:
        strip.append([V3((x, y, 0)) + n * dx + V3((0, 0, z)) for dx, z in ((0.004, zt - 0.075), (0.016, zt - 0.072), (0.016, zt - 0.052), (0.004, zt - 0.049))])
    m.loft(strip, 'rubber', caps=True)
    for s in (1, -1):
        m.rbox(V3((xf + sx * 0.012, s * 0.585, zb + 0.5 * h - 0.02)), (0.11, 0.085, h + 0.06), 0.02, 'rubber')


def build_front_rear(root):
    m = Mesh()
    x = G.X_NOSE
    # grille: black back, chrome egg-crate 12 x 6, chrome surround, the header bar over it, a blue oval
    m.box(V3((x + 0.006, 0, 0.68)), (0.012, 1.00, 0.215), 'black')
    for k in range(13):
        m.box(V3((x + 0.024, -0.49 + 0.98 * k / 12, 0.68)), (0.034, 0.0065, 0.205), 'chrome')
    for k in range(7):
        m.box(V3((x + 0.024, 0, 0.578 + 0.204 * k / 6)), (0.034, 0.98, 0.0065), 'chrome')
    for i in range(12):                                      # each cell's inner cross (the drawing's '+' pattern)
        for j in range(6):
            yc, zc = -0.49 + 0.98 * (i + 0.5) / 12, 0.578 + 0.204 * (j + 0.5) / 6
            m.box(V3((x + 0.018, yc, zc)), (0.020, 0.004, 0.022), 'chrome')
            m.box(V3((x + 0.018, yc, zc)), (0.020, 0.050, 0.004), 'chrome')
    m.tube([V3((x + 0.04, p.x, p.z)) for p in rrect_path(-0.505, 0.570, 0.505, 0.790, 0.015)], 0.011, 'chrome', seg=8, loop=True)
    m.rbox(V3((x + 0.01, 0, 0.802)), (0.075, 1.08, 0.024), 0.008, 'chrome')
    m.rbox(V3((x + 0.046, 0.33, 0.685)), (0.012, 0.10, 0.038), 0.015, 'badge')
    lamps_h, lamps_p, lamps_m = Mesh(), Mesh(), Mesh()
    for s in (1, -1):
        # the headlamp bezel with two rectangular sealed beams and the amber parking lamp under them
        m.rbox(V3((x + 0.004, s * 0.70, 0.684)), (0.026, 0.355, 0.200), 0.01, 'chrome')
        m.box(V3((x + 0.0045, s * 0.70, 0.684)), (0.004, 0.335, 0.180), 'black')
        for yc in (0.615, 0.785):
            # a 4 x 6 in halogen sealed beam: the paraboloid reflector, the filament's shield, a lens of small prisms
            CK.reflector(m, V3((x + 0.022, s * yc, 0.722)), (1, 0, 0), (0, 0, 1), 0.156, 0.092, 0.030, 'reflector', n=16)
            CK.bulb(m, V3((x + 0.004, s * yc, 0.722)), (1, 0, 0), 0.010, 'bulb')
            m.cyl(V3((x + 0.020, s * yc, 0.722)), V3((x + 0.024, s * yc, 0.722)), 0.013, 'reflector', seg=14)
            CK.fluted_lens(lamps_h, V3((x + 0.030, s * yc, 0.722)), (1, 0, 0), (0, 0, 1), 0.158, 0.094, 0.004, 12, 7, 'lens_clear', 'cells', bulge=0.005)
        m.box(V3((x + 0.024, s * 0.70, 0.671)), (0.016, 0.335, 0.006), 'chrome')
        CK.reflector(m, V3((x + 0.014, s * 0.70, 0.622)), (1, 0, 0), (0, 0, 1), 0.322, 0.040, 0.010, 'reflector', n=10)
        for yb in (0.62, 0.78):
            CK.bulb(m, V3((x + 0.006, s * yb, 0.622)), (1, 0, 0), 0.008, 'bulb')
        CK.fluted_lens(lamps_p, V3((x + 0.024, s * 0.70, 0.622)), (1, 0, 0), (0, 0, 1), 0.330, 0.044, 0.004, 30, 1, 'lens_amber', 'flutes', bulge=0.002)
        # the corner lamp: an amber lens round the fender's rounded corner, in a chrome frame
        r = 0.11
        cx, cy = G.X_NOSE - r, s * (G.W - r)
        rows, frame_t, frame_b = [], [], []
        for j in range(5):
            z = 0.585 + 0.185 * j / 4
            row = []
            for k in range(13):
                a = math.radians(8 + 74 * k / 12)
                d = V3((math.cos(a), s * math.sin(a), 0))
                row.append(V3((cx, cy, z)) + d * (r + 0.004 + 0.0014 * (k % 2)))
            rows.append(row)
        refl = [[p - (p - V3((cx, cy, p.z))).normalized() * 0.012 for p in row] for row in rows]
        m.grid(refl if s > 0 else [list(reversed(rr)) for rr in refl], 'reflector')
        CK.bulb(m, V3((cx, cy, 0.68)) + V3((math.cos(0.7), s * math.sin(0.7), 0)) * (r - 0.02), V3((math.cos(0.7), s * math.sin(0.7), 0)), 0.009, 'bulb')
        lamps_m.grid(rows if s > 0 else [list(reversed(rr)) for rr in rows], 'lens_amber')
        fr = [rows[0][0]] + rows[0] + [rows[-1][-1]]
        m.tube([p + V3((0, 0, 0)) for p in rows[0]], 0.006, 'chrome', seg=6)
        m.tube([p for p in rows[-1]], 0.006, 'chrome', seg=6)
        m.tube([rr[0] for rr in rows], 0.006, 'chrome', seg=6)
        m.tube([rr[-1] for rr in rows], 0.006, 'chrome', seg=6)
    bumper(m, True)
    bumper(m, False)
    # the tail: lamps with ribbed red lenses in chrome bezels, the plate in its recess, a small oval
    xt = G.X_TAIL
    lamps_t = Mesh()
    for s in (1, -1):
        m.rbox(V3((xt - 0.004, s * 0.838, 0.73)), (0.022, 0.150, 0.300), 0.008, 'chrome')
        CK.reflector(m, V3((xt - 0.011, s * 0.838, 0.73)), (-1, 0, 0), (0, 0, 1), 0.126, 0.272, 0.022, 'reflector', n=14)
        for zb in (0.66, 0.80):
            CK.bulb(m, V3((xt + 0.004, s * 0.838, zb)), (-1, 0, 0), 0.011, 'bulb')
        lamps_t.rbox(V3((xt - 0.016, s * 0.838, 0.73)), (0.010, 0.130, 0.280), 0.006, 'lens_red')
        for k in range(12):
            lamps_t.box(V3((xt - 0.022, s * 0.838, 0.604 + 0.0229 * k)), (0.004, 0.126, 0.006), 'lens_red')
    m.rbox(V3((xt - 0.002, 0, 0.678)), (0.012, 0.345, 0.185), 0.01, 'black')
    m.box(V3((xt - 0.010, 0, 0.678)), (0.003, 0.305, 0.152), 'plate')
    m.tube([V3((xt - 0.012, p.x, p.z)) for p in rrect_path(-0.160, 0.596, 0.160, 0.760, 0.012)], 0.005, 'chrome', seg=6, loop=True)
    for yb in (-0.10, 0.10):
        m.cyl(V3((xt - 0.012, yb, 0.742)), V3((xt - 0.017, yb, 0.742)), 0.007, 'chrome', seg=10)
    m.rbox(V3((xt - 0.006, -0.38, 0.625)), (0.010, 0.10, 0.038), 0.015, 'badge')
    # the red rear side markers
    lm = lamps_m
    return m, (lamps_h, lamps_p, lamps_t, lm)


def plate_uv(ob):
    """The plate's UVs: its back face (looking -X) takes the whole picture, seen from behind the car (left of the picture on the car's right, -Y)."""
    me = ob.data
    idx = [i for i, mm in enumerate(me.materials) if mm.name == 'M_plate']
    if not idx:
        return
    bm = bmesh.new()
    bm.from_mesh(me)
    uvl = bm.loops.layers.uv.verify()
    for f in bm.faces:
        if f.material_index == idx[0]:
            for lp in f.loops:
                p = lp.vert.co
                lp[uvl].uv = ((-p.y + 0.1525) / 0.305 if f.normal.x < 0 else 0.5, (p.z - (0.678 - 0.076)) / 0.152)
    bm.to_mesh(me)
    bm.free()


# ---- roof equipment (the 7126 photograph): a chrome rack over the front door with two blue beacons, a siren speaker and two forward lamps --------------------------------------
def build_rack(root):
    """The roof equipment of the 7126 photograph: a bright channel bar across the roof over the front doors on two gutter clamps, a rotating beacon at each end, the siren
    speaker in the middle, two round forward lamps with blue lenses, the control box, red lenses at the bar's ends, a whip on the right."""
    xr = -0.25
    zr = G.roof_z(xr)
    zb = zr + 0.105
    rack = Mesh()
    # the bar: a channel 56 x 38 mm with rolled lips, its end caps
    prof = [(-0.028, -0.019), (0.028, -0.019), (0.028, 0.019), (0.022, 0.019), (0.022, -0.012), (-0.022, -0.012), (-0.022, 0.019), (-0.028, 0.019)]
    rack.loft([[V3((xr + a, y, zb + b)) for a, b in prof] for y in (-0.71, 0.71)], 'chrome', caps=True)
    for s in (1, -1):
        rack.rbox(V3((xr, s * 0.712, zb)), (0.060, 0.006, 0.040), 0.004, 'black')
        # the gutter clamp: a foot hooked over the drip rail, the post, the thumb screw
        foot = V3((xr, s * (G.GH_Y_ROOF + 0.014), G.GH_Z_ROOF_EDGE + 0.006))
        rack.rbox(foot, (0.07, 0.035, 0.02), 0.005, 'black')
        rack.rbox(foot + V3((0, s * 0.018, -0.015)), (0.07, 0.006, 0.03), 0.002, 'black')
        rack.cyl(foot + V3((0, 0, 0.01)), V3((xr, s * 0.62, zb - 0.019)), 0.011, 'chrome', seg=12)
        rack.cyl(foot + V3((0, -s * 0.02, 0.0)), foot + V3((0, -s * 0.045, 0.0)), 0.005, 'steel', seg=8)
        rack.cyl(foot + V3((0, -s * 0.045, 0.0)), foot + V3((0, -s * 0.050, 0.0)), 0.012, 'black', seg=12)
        rack.rbox(V3((xr + 0.029, s * 0.69, zb + 0.004)), (0.008, 0.045, 0.030), 0.004, 'black')
        CK.fluted_lens(rack, V3((xr + 0.034, s * 0.69, zb + 0.004)), (1, 0, 0), (0, 0, 1), 0.040, 0.025, 0.003, 6, 1, 'lens_red', 'flutes', bulge=0.0)
    rack.cyl(V3((xr, -0.69, zb + 0.019)), V3((xr, -0.69, zb + 0.34)), 0.005, 'chrome', seg=8, r1=0.003)
    rack.rbox(V3((xr, -0.41, zb + 0.053)), (0.10, 0.12, 0.065), 0.01, 'black')
    for k in range(3):
        rack.cyl(V3((xr + 0.051, -0.44 + 0.03 * k, zb + 0.06)), V3((xr + 0.058, -0.44 + 0.03 * k, zb + 0.06)), 0.006, 'chrome', seg=10)
    # the forward lamps: round lamps with blue lenses on short brackets
    for y, r in ((0.15, 0.055), (-0.32, 0.045)):
        c = V3((xr + 0.06, y, zb + 0.019 + r + 0.01))
        CK.round_lamp(rack, c, (1, 0, 0), r, 0.13, 'lens_blue')
        rack.rbox(c + V3((-0.06, 0, -r - 0.005)), (0.05, 0.03, 0.02), 0.004, 'chrome')
    ob = rack.finish('Rack', root, sharp=40)
    sp = Mesh()
    CK.siren_speaker(sp, V3((xr + 0.07, -0.12, zb + 0.15)), (1, 0, 0))
    sp.cyl(V3((xr + 0.06, -0.12, zb + 0.15)), V3((xr + 0.07, -0.12, zb + 0.15)), 0.022, 'lens_red', seg=16)
    sp.finish('Speaker', root, sharp=40)
    for nm, y in (('Beacon_L', 0.60), ('Beacon_R', -0.60)):
        e = empty(nm, V3((xr, y, zb + 0.019)), root)
        b = Mesh()
        CK.beacon(b)
        b.finish(nm + '_mesh', e, sharp=40)
    return ob


# ---- the interior: cab.py (Interior, Dash, SteeringWheel, Equipment) ----
def build_interior(root):
    import cab
    cab.build_cab(sys.modules[__name__], root)


def build_under(root):
    """Under the body (the Panther platform is body on frame): the frame's rails and cross members, the front coil springs and dampers in the control arms, the live rear axle on
    its coil springs and links, the driveshaft, the transmission and the oil pan, the fuel tank ahead of the rear axle, the exhaust with its muffler and resonator."""
    m = Mesh()
    xr, xf = -G.WHEELBASE / 2, G.WHEELBASE / 2
    for s in (1, -1):
        m.tube([V3((2.20, s * 0.42, 0.33)), V3((1.20, s * 0.42, 0.30)), V3((0.80, s * 0.62, 0.25)), V3((-0.90, s * 0.64, 0.25)), V3((-1.30, s * 0.52, 0.36)),
                V3((-2.55, s * 0.50, 0.40))], 0.045, 'black', seg=4)
    for x in (2.05, 1.45, 0.50, -0.55, -1.20, -2.00):
        m.rbox(V3((x, 0, 0.29 if x > 0 else 0.33)), (0.08, 1.20, 0.07), 0.01, 'black')
    for s in (1, -1):
        m.tube([V3((xf + 0.18, s * 0.38, 0.27)), V3((xf, s * 0.70, 0.25))], 0.020, 'black', seg=8)
        m.tube([V3((xf - 0.18, s * 0.38, 0.27)), V3((xf, s * 0.70, 0.25))], 0.020, 'black', seg=8)
        m.tube([V3((xf + 0.10, s * 0.45, 0.52)), V3((xf, s * 0.68, 0.52))], 0.016, 'black', seg=8)
        CK.coil_spring(m, V3((xf - 0.02, s * 0.55, 0.27)), V3((xf - 0.02, s * 0.52, 0.52)), 0.055, 0.008, 6.5)
        CK.damper(m, V3((xf + 0.05, s * 0.55, 0.26)), V3((xf + 0.05, s * 0.52, 0.55)))
        CK.coil_spring(m, V3((xr + 0.05, s * 0.52, G.ZC + 0.04)), V3((xr + 0.05, s * 0.52, 0.56)), 0.06, 0.009, 5.5)
        CK.damper(m, V3((xr - 0.12, s * 0.45, G.ZC)), V3((xr - 0.18, s * 0.42, 0.56)))
        m.tube([V3((xr, s * 0.48, G.ZC - 0.06)), V3((xr + 0.60, s * 0.52, 0.30))], 0.020, 'black', seg=8)
        m.tube([V3((xr + 0.05, s * 0.15, G.ZC + 0.08)), V3((xr + 0.50, s * 0.35, 0.40))], 0.018, 'black', seg=8)
    m.cyl(V3((xr, -0.66, G.ZC)), V3((xr, 0.66, G.ZC)), 0.045, 'steel', seg=16)
    m.cyl(V3((xr - 0.05, 0, G.ZC)), V3((xr + 0.16, 0, G.ZC)), 0.13, 'steel', seg=20, r1=0.06)
    m.cyl(V3((xr - 0.06, 0, G.ZC)), V3((xr - 0.05, 0, G.ZC)), 0.14, 'steel', seg=20)
    m.cyl(V3((xr + 0.16, 0, G.ZC + 0.01)), V3((0.45, 0, 0.30)), 0.04, 'steel', seg=12)
    m.rbox(V3((0.85, 0, 0.32)), (0.70, 0.36, 0.22), 0.06, 'steel')
    m.rbox(V3((1.55, 0, 0.30)), (0.55, 0.42, 0.12), 0.04, 'black')
    m.rbox(V3((-0.95, 0, 0.37)), (0.55, 1.05, 0.20), 0.04, 'black')
    m.tube([V3((1.40, -0.25, 0.26)), V3((0.4, -0.30, 0.27)), V3((-0.4, -0.40, 0.27)), V3((-1.25, -0.45, 0.29)), V3((-2.2, -0.55, 0.30)), V3((-2.86, -0.55, 0.31))],
           0.026, 'steel', seg=10)
    m.cyl(V3((-0.20, -0.38, 0.29)), V3((-0.80, -0.41, 0.29)), 0.075, 'steel', seg=16)
    m.cyl(V3((-1.80, -0.50, 0.30)), V3((-2.20, -0.53, 0.30)), 0.055, 'steel', seg=14)
    for x in (-0.95, -1.65, -2.55):
        m.cyl(V3((x, -0.50, 0.33)), V3((x, -0.50, 0.40)), 0.008, 'rubber', seg=6)
    m.cyl(V3((-2.86, -0.55, 0.31)), V3((-2.90, -0.55, 0.31)), 0.030, 'steel', seg=16)
    return m.finish('Underbody', root, sharp=40)


# ---- wheels ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def wheel_mesh(s, front):
    """A P215/70R15 all-season radial (no maker named: the department's tyres are not known) on a black 15 x 7 steel wheel with a chrome dog-dish cap; behind it a vented disc and
    caliper (front) or a finned drum (rear); built about the wheel's centre, outer face toward s*Y."""
    m = Mesh()
    R, Rr = G.R_TYRE, G.R_RIM
    CK.tyre(m, s, R, Rr, G.W_TYRE, CK.tread_allseason,
            [('STEEL BELTED RADIAL', 90, 0.55, 0.012), ('P215/70R15', 270, 0.55, 0.016), ('TUBELESS', 30, 0.35, 0.008), ('M+S', 210, 0.35, 0.010)])
    sec = [(-0.096, Rr + 0.013), (-0.090, Rr + 0.015), (-0.085, Rr + 0.003), (-0.080, Rr - 0.006), (0.080, Rr - 0.006), (0.085, Rr + 0.003), (0.090, Rr + 0.015),
           (0.096, Rr + 0.013), (0.094, Rr + 0.002), (0.088, Rr - 0.004)]
    m.loft([[V3((r * math.cos(2 * math.pi * k / 96), s * y, r * math.sin(2 * math.pi * k / 96))) for y, r in sec] for k in range(96)], 'wheel', closed=False, loop=True)
    # the stamped face: a dished centre, a raised ring with eight oval vents through it, the lug circle (under the cap)
    face = []
    for r, y in ((Rr - 0.006, 0.084), (0.17, 0.074), (0.155, 0.066), (0.145, 0.062), (0.13, 0.054), (0.0, 0.050)):
        face.append([V3((r * math.cos(2 * math.pi * k / 96), s * y, r * math.sin(2 * math.pi * k / 96))) for k in range(96)])
    m.loft(face, 'wheel')
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        c = V3((0.162 * math.cos(a), s * 0.072, 0.162 * math.sin(a)))
        m.rbox(c, (0.026, 0.006, 0.040), 0.010, 'black', (V3((math.cos(a), 0, math.sin(a))), V3((0, 1, 0)), V3((-math.sin(a), 0, math.cos(a)))))
    CK.hub(m, s, 0.050, 5, 0.0572)
    cap = []
    for r, y in ((0.140, 0.058), (0.136, 0.072), (0.118, 0.084), (0.082, 0.091), (0.040, 0.094), (0.0, 0.095)):
        cap.append([V3((r * math.cos(2 * math.pi * k / 72), s * y, r * math.sin(2 * math.pi * k / 72))) for k in range(72)])
    m.loft(cap, 'chrome')
    CK.valve_stem(m, s, 0.178, 0.080)
    if front:
        CK.brake_disc(m, s, 0.140, 0.075, 0.030, 0.028)
        CK.caliper(m, s, 0.140, 0.030, 0.028, 200)
    else:
        m.cyl(V3((0, s * 0.03, 0)), V3((0, -s * 0.06, 0)), 0.150, 'drum', seg=48)
        for k in range(24):
            a = 2 * math.pi * k / 24
            m.box(V3((0.152 * math.cos(a), -s * 0.015, 0.152 * math.sin(a))), (0.006, 0.07, 0.008), 'drum',
                  (V3((-math.sin(a), 0, math.cos(a))), V3((0, 1, 0)), V3((math.cos(a), 0, math.sin(a)))))
        m.cyl(V3((0, -s * 0.06, 0)), V3((0, -s * 0.07, 0)), 0.165, 'black', seg=48)
    return m


def build_wheels(root):
    for nm, x, y in (('FL', G.WHEELBASE / 2, G.TRACK_F / 2), ('FR', G.WHEELBASE / 2, -G.TRACK_F / 2), ('RL', -G.WHEELBASE / 2, G.TRACK_R / 2), ('RR', -G.WHEELBASE / 2, -G.TRACK_R / 2)):
        e = empty(f'Wheel_{nm}', V3((x, y, G.ZC)), root)
        wheel_mesh(1 if y > 0 else -1, nm[0] == 'F').finish(f'Wheel_{nm}_mesh', e, sharp=40)


# ---- all -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def build(level=False):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _mc.clear()
    root = empty('CrownVic87')
    body = build_body(root)
    bvh = bvh_of([body])
    glass = build_glass(bvh)
    trim = build_trim(bvh)
    door_inner(trim)
    log('glass, trim')
    boolean(body, body_cutters(), 'DIFFERENCE')
    log('cuts', len(body.data.polygons))
    CK.roll_edges(body)
    uv_paint(body)
    metres_uv(body, ('carpet', 'headliner'))
    doors = split_doors(body, root)
    smooth(body, 40)
    log('doors', len(body.data.polygons))
    finish_parts(glass, 'Glass', root, doors, sharp=60)
    finish_parts(trim, 'Trim', root, doors, sharp=50)
    fr, lamps = build_front_rear(root)
    ends = fr.finish('Ends', root, sharp=40)
    plate_uv(ends)
    lh, lp, lt, lm = lamps
    lh.finish('Lamps_Head', root)
    lp.finish('Lamps_Park', root)
    lt.finish('Lamps_Tail', root)
    # the rear side markers go with the corner lamps
    for sd in (1, -1):
        x0, z1, x1, z0 = G.MARKER_R_PX
        rows = []
        for j in range(4):
            z = G.Z(z0) + (G.Z(z1) - G.Z(z0)) * j / 3
            rows.append([on_side(bvh, G.X(x0) + (G.X(x1) - G.X(x0)) * k / 4, z, sd, 0.003)[0] for k in range(5)])
        lm.grid(rows if sd > 0 else [list(reversed(r)) for r in rows], 'lens_red')
    lm.finish('Lamps_Marker', root)
    build_rack(root)
    build_interior(root)
    build_under(root)
    build_wheels(root)
    log('done')
    return root


def export(root, path, lod_ratio=None):
    bpy.ops.object.select_all(action='DESELECT')
    obs = [root] + list(root.children_recursive)
    mods = []
    if lod_ratio:
        for ob in obs:
            if ob.type == 'MESH' and len(ob.data.polygons) > 400:
                md = ob.modifiers.new('lod', 'DECIMATE')
                md.ratio = lod_ratio
                mods.append((ob, md))
    for ob in obs:
        ob.select_set(True)
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True, export_yup=True, export_apply=True, export_image_format='WEBP',
                              export_materials='EXPORT', export_extras=False, export_cameras=False, export_lights=False)
    for ob, md in mods:
        ob.modifiers.remove(md)
    tris = sum(len(o.data.polygons) for o in obs if o.type == 'MESH')
    log('wrote', path, 'polygons', tris)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    arg = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d  # noqa: E731
    out = pathlib.Path(arg('--out', str(ROOT / 'assets' / 'crown_victoria_cpd87.glb')))
    r = build()
    if arg('--blend'):
        bpy.ops.wm.save_as_mainfile(filepath=str(pathlib.Path(arg('--blend')).resolve()))
    export(r, out)
    if arg('--lod1'):
        export(r, pathlib.Path(arg('--lod1')), lod_ratio=0.35)
