# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Shared car builder for the TAKE 37 civilian traffic cars (runs inside Blender 4.2). A car is described by a geometry module (see geomkit.py); build_car() makes the
solid body from lofted sections, cuts the openings and splits the doors, hood, trunk lid or tailgate into their own nodes, then adds glass, trim, lamps, bumpers, interior, underbody and wheels.
Frame: origin on the ground at the middle of the wheelbase, nose +X, up +Z, the left (driver's) side +Y (glb: Y up, nose +X, left -Z)."""
import math
import pathlib
import sys
import time
import json
import zipfile

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import carkit as CK  # noqa: E402

V3 = Vector
G = None
T0 = time.time()
SCRATCH = pathlib.Path('D:/temp/take37/claude')
LIB = pathlib.Path('D:/REPO/ferret/lib/ferret-assets')


def use(g):
    global G
    G = g


def log(*a):
    print(f'[{time.time() - T0:6.1f}s]', *a, flush=True)


def lin(c):
    return tuple(((x / 255 + 0.055) / 1.055) ** 2.4 if x / 255 > 0.04045 else x / 255 / 12.92 for x in c)


# ---- mesh building (see the notes in carkit.py) ---------------------------------------------------------------------------------------------------------------------------------
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
    """Apply a boolean (exact by default) of ob with the cutter objects (deleted afterwards); the new faces take the cutters' materials. Several cutters are applied one after the
    other (a collection operand unites them first, which does not terminate for cutters that overlap)."""
    for c in cutters:
        c.hide_render = True
        md = ob.modifiers.new('bool', 'BOOLEAN')
        md.operation = op
        md.solver = solver
        md.operand_type = 'OBJECT'
        md.object = c
        if solver == 'EXACT':
            md.material_mode = 'TRANSFER'
            md.use_hole_tolerant = True
            md.use_self = self_test
        with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
            bpy.ops.object.modifier_apply(modifier=md.name)
    for c in cutters:
        bpy.data.objects.remove(c, do_unlink=True)
    drop_origin_junk(ob)


def drop_origin_junk(ob):
    """The exact solver with hole tolerance leaves stray vertices at the origin (a fan of slivers under the car): remove them."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    mw = ob.matrix_world
    bad = [v for v in bm.verts if v.co.length < 2e-3 or (mw @ v.co).length < 2e-3]
    if bad:
        bmesh.ops.delete(bm, geom=bad, context='VERTS')
        bm.to_mesh(ob.data)
    bm.free()


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
    return chaikin(pts, 2)


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
    return chaikin(pts, 2)





def cabin_half(x):
    """The cabin's half section (what the boolean takes out): 35 mm inside the greenhouse, the door's inner skin at 0.83 m, the floor at 0.36 m; narrower over the rear wheel houses."""
    t = 0.035
    zt = G.roof_z(x) - t
    zre = max(min(G.GH_Z_ROOF_EDGE - t, zt - 0.022), G.Z_BELT + 0.01)
    ys = G.gh_side_y(zre) - t
    yd = 0.60 if G.X_HUMP[0] < x < G.X_HUMP[1] else 0.83
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




def attach(ob, parent):
    """Parent keeping the world placement."""
    bpy.context.view_layer.update()
    ob.parent = parent
    ob.matrix_parent_inverse = parent.matrix_world.inverted()




# ---- materials ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# (sRGB colour, metallic, roughness, extra). 'lib': a material of the shared asset library (textures basecolor / normal / orm), 'tile': metres per repeat, 'tint': multiplies the picture.
MATS = {
    'paint': ((120, 120, 125), 0.0, 0.32, {'coat': 1.0, 'coat_rough': 0.15}),
    'under': ((26, 26, 27), 0.0, 0.9, {}),
    'gap': ((6, 6, 6), 0.0, 0.9, {}),
    'well': ((14, 14, 14), 0.0, 0.95, {}),
    'seal': ((12, 12, 12), 0.0, 0.6, {}),
    'interior': ((60, 52, 44), 0.0, 0.6, {}),
    'carpet': ((90, 80, 70), 0.0, 1.0, {'lib': 'rug', 'tile': 0.6, 'tint': (0.62, 0.55, 0.48)}),
    'headliner': ((150, 140, 125), 0.0, 0.95, {'lib': 'gray-fabric1', 'tile': 0.4, 'tint': (1.0, 0.92, 0.78)}),
    'cloth': ((140, 120, 100), 0.0, 0.9, {'lib': 'cloth-grey', 'tile': 0.25, 'tint': (1.0, 0.82, 0.62)}),
    'vinyl': ((70, 56, 44), 0.0, 0.5, {}),
    'dash': ((44, 38, 32), 0.0, 0.55, {}),
    'gauge': ((8, 8, 10), 0.0, 0.2, {}),
    'chrome': ((235, 235, 235), 1.0, 0.07, {}),
    'black': ((14, 14, 15), 0.0, 0.45, {}),
    'rubber': ((20, 20, 20), 0.0, 0.85, {}),
    'tyre': ((24, 24, 24), 0.0, 0.88, {}),
    'wheel': ((14, 14, 15), 0.3, 0.35, {}),
    'wheel_body': ((150, 150, 152), 0.7, 0.3, {}),
    'steel': ((60, 60, 62), 0.6, 0.5, {}),
    'chassis': ((40, 40, 42), 0.5, 0.6, {'lib': 'metal-black', 'tile': 0.5}),
    'raw_steel': ((150, 150, 152), 0.8, 0.5, {'lib': 'metal-steel', 'tile': 0.5}),
    'glass': ((222, 238, 232), 0.0, 0.0, {'trans': 1.0, 'ior': 1.52}),
    'mirror': ((215, 220, 225), 1.0, 0.02, {}),
    'lens_clear': ((250, 250, 250), 0.0, 0.02, {'trans': 1.0, 'ior': 1.49}),
    'reflector': ((210, 210, 210), 1.0, 0.12, {}),
    'lens_amber': ((255, 135, 10), 0.0, 0.03, {'trans': 1.0, 'ior': 1.49}),
    'lens_red': ((215, 12, 10), 0.0, 0.03, {'trans': 1.0, 'ior': 1.49}),
    'bulb': ((250, 250, 245), 0.0, 0.05, {'alpha': 0.5}),
    'caliper': ((58, 58, 60), 0.4, 0.5, {}),
    'drum': ((52, 50, 48), 0.6, 0.55, {}),
    'spring': ((30, 30, 32), 0.3, 0.45, {}),
    'plate': ((240, 240, 236), 0.0, 0.35, {}),
    'plate_ink': ((20, 40, 110), 0.0, 0.4, {}),
    'bumper': ((54, 54, 56), 0.0, 0.7, {}),
    'wood': ((90, 52, 28), 0.0, 0.55, {'lib': 'wood-walnut', 'tile': 0.45, 'tint': (1.0, 0.85, 0.75), 'coat': 0.35, 'coat_rough': 0.15}),
    'woodtrim': ((30, 20, 12), 0.0, 0.5, {}),
    'engine': ((70, 72, 74), 0.5, 0.55, {}),
    'radio': ((30, 32, 34), 0.3, 0.4, {}),
}
_mc = {}
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


def mat(kind):
    if kind in _mc:
        return _mc[kind]
    c, met, rough, ex = MATS[kind]
    if kind == 'paint' and hasattr(G, 'COLORS'):
        c = G.COLORS[0][1]
    m = bpy.data.materials.new('M_' + kind)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*lin(c), 1)
    b.inputs['Metallic'].default_value = met
    b.inputs['Roughness'].default_value = rough
    if 'lib' in ex:
        name = ex['lib']
        im = lib_image(name, 'basecolor')
        mp = nt.nodes.new('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (1 / ex.get('tile', 0.5),) * 3
        tc = nt.nodes.new('ShaderNodeTexCoord')
        nt.links.new(tc.outputs['UV'], mp.inputs['Vector'])
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = im
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
            if met > 0.3:
                nt.links.new(sp.outputs['Blue'], b.inputs['Metallic'])
    if 'trans' in ex:
        b.inputs['Transmission Weight'].default_value = ex['trans']
        b.inputs['IOR'].default_value = ex.get('ior', 1.5)
    if 'coat' in ex:
        b.inputs['Coat Weight'].default_value = ex['coat']
        b.inputs['Coat Roughness'].default_value = ex['coat_rough']
    if 'alpha' in ex:
        b.inputs['Alpha'].default_value = ex['alpha']
        if hasattr(m, 'surface_render_method'):
            m.surface_render_method = 'BLENDED'
        m.blend_method = 'BLEND'
    _mc[kind] = m
    return m


def metres_uv(ob, kinds=('carpet', 'headliner', 'cloth', 'wood', 'chassis', 'raw_steel')):
    """UVs in metres by a box projection for the faces whose materials come from the library."""
    me = ob.data
    idx = {i for i, mm in enumerate(me.materials) if mm and mm.name[2:] in kinds}
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


# ---- the cabin (overrides the generic section above: widths come from the car's geometry) ----------------------------------------------------------------------------------------
def cabin_half(x):
    """The cabin's half section: SHELL inside the greenhouse, the door's inner skin at CAB_Y, the floor at CAB_FLOOR; narrower over the rear wheel houses (X_HUMP)."""
    t = G.SHELL
    zt = G.roof_z(x) - t
    zre = max(min(G.GH_Z_ROOF_EDGE - t, zt - 0.022), G.Z_BELT + 0.01)
    ys = G.gh_side_y(zre) - t
    cy = G.CAB_Y
    yd = G.HUMP_Y if G.X_HUMP[0] < x < G.X_HUMP[1] else cy
    zs = G.Z_BELT - 0.06
    pts = [(0.0, zt), (0.5 * ys, zt - 0.004), (ys - 0.05, zt - 0.012), (ys, zre), (G.GH_Y_BELT - t, G.Z_BELT), (cy, zs), (cy, G.Z_BELT - 0.2), (yd, G.Z_BELT - 0.23),
           (yd, G.CAB_FLOOR + 0.06), (yd - 0.06, G.CAB_FLOOR), (0.0, G.CAB_FLOOR)]
    return chaikin(pts, 1)


def build_body(root):
    m = Mesh()
    xs = stations(G.X_TAIL, G.X_NOSE, 0.040, fine=0.010)
    m.loft([ring3(x, lower_half(x)) for x in xs], 'paint', caps=True)
    body = m.finish('Body', root, sharp=40)
    g = Mesh()
    xg = stations(G.X_GH0, G.X_COWL + 0.03, 0.030, dense=0.0)
    g.loft([ring3(x, gh_half(x)) for x in xg], 'paint', caps=True)
    gh = g.finish('Greenhouse', root)
    log('body lofted', len(body.data.polygons), 'greenhouse', len(gh.data.polygons))
    boolean(body, [gh], 'UNION')
    log('union', len(body.data.polygons))
    return body


def to_m(poly_px):
    return [(G.X(a), G.Z(b)) for a, b in poly_px]


def box_cut(x0, x1, y0, y1, z0, z1, kind, name):
    m = Mesh()
    pts = [V3((x0, y0, z0)), V3((x1, y0, z0)), V3((x1, y1, z0)), V3((x0, y1, z0))]
    m.loft([pts, [V3((p.x, p.y, z1)) for p in pts]], kind, caps=True)
    return m.finish(name)


def cavity_cut(cv, name):
    """A hollow under a lid: a box, or (top following the body's top surface `off` below it) a loft of rectangular rings."""
    if 'box' in cv:
        x0, x1, y0, y1, z0, z1 = cv['box']
        return box_cut(x0, x1, y0, y1, z0, z1, cv.get('kind', 'well'), name)
    m = Mesh()
    xs = stations(cv['x0'], cv['x1'], 0.03, dense=0.0)
    rings = []
    for x in xs:
        zt = G.top_z(x) - cv.get('off', 0.045)
        y = cv['y']
        rings.append([V3((x, -y, cv['z0'])), V3((x, y, cv['z0'])), V3((x, y, zt)), V3((x, -y, zt))])
    m.loft(rings, cv.get('kind', 'well'), caps=True)
    return m.finish(name)


def body_cutters():
    cut = []
    c = Mesh()
    xc = stations(G.CABIN_X0, G.CABIN_X1, 0.02, dense=0.0)
    c.loft([ring3(x, cabin_half(x)) for x in xc], 'interior', caps=True)
    cut.append(c.finish('cut_cabin'))
    # the side glass openings (the sill 3 mm over the belt so no face is coplanar with the shoulder)
    for nm, poly in G.SIDE_WINDOWS.items():
        pts = [V3((x, 0, max(z, G.Z_BELT + 0.003))) for x, z in to_m(poly)]
        for s in G.WINDOW_SIDES.get(nm, (1, -1)):
            cut.append(prism_y(pts if s > 0 else list(reversed(pts)), s * 0.45, s * 1.4, 'seal', f'cut_win_{nm}_{s}'))
    for nm, d in (('ws', G.WS), ('bl', G.BL)):
        if d is None:
            continue
        poly = [(d['y0'], d['z0']), (d['y1'], d['z1']), (-d['y1'], d['z1']), (-d['y0'], d['z0'])]
        cut.append(prism_x(poly, d['x0'], d['x1'], 'seal', 'cut_' + nm))
    for nm, (xc_, ) in (('r', (-G.HWB, )), ('f', (G.HWB, ))):
        poly = arch_poly(xc_)
        for s in (1, -1):
            cut.append(prism_y(poly if s > 0 else list(reversed(poly)), s * G.ARCH_Y, s * 1.4, 'well', f'cut_well_{nm}_{s}'))
    for i, cv in enumerate(G.CAVITIES):
        cut.append(cavity_cut(cv, f'cut_cav{i}'))
    return cut


def arch_poly(xc):
    """A wheel opening: from the lower rear corner over the top to the lower front corner (an arch with a flat-ish crown and a flare), as XZ points (V3 with y ignored)."""
    R = G.R_TYRE + G.ARCH_GAP
    pts = []
    for k in range(0, 25):
        a = math.radians(180 - 180 * k / 24)
        pts.append(V3((xc + R * 1.03 * math.cos(a), 0, G.ZC + R * math.sin(a) * 0.98)))
    return [V3((pts[0].x - 0.015, 0, -0.2))] + pts + [V3((pts[-1].x + 0.015, 0, -0.2))]


# ---- doors, lids: parts cut out of the body, each its own node ---------------------------------------------------------------------------------------------------------------
def door_cutter(dk, d, s, name):
    zt, zb = G.Z_BELT + 0.004, G.Z(d['bottom_row'])
    lower = [(max(z, zb) if False else x, z) for x, z in to_m(d['lower'])]
    wins = [offset_poly(to_m(w), 0.018) for w in d['wins']]
    area = lambda pts: sum(p.x * q.z - q.x * p.z for p, q in zip(pts, pts[1:] + pts[:1]))     # noqa: E731
    lo_pts = [V3((x, 0, z)) for x, z in lower]
    if (area(lo_pts) > 0) != (s > 0):
        lo_pts.reverse()
    lo = prism_y(lo_pts, s * (G.CAB_Y - 0.03), s * 1.4, 'interior', name)
    his = []
    for i, up in enumerate(wins):
        up = [(x, max(z, G.Z_BELT - 0.002)) for x, z in up]
        up_pts = [V3((x, 0, z)) for x, z in up]
        if (area(up_pts) > 0) != (s > 0):
            up_pts.reverse()
        his.append(prism_y(up_pts, s * 0.50, s * 1.4, 'seal', name + f'_frame{i}'))
    if his:
        boolean(lo, his, 'UNION')
    return lo


def grown_prism(ob_pts_fn):
    return ob_pts_fn()


def dup_obj(ob, name):
    d = bpy.data.objects.new(name, ob.data.copy())
    bpy.context.scene.collection.objects.link(d)
    return d


def intersect_part(body, cutter, name):
    """body AND cutter, as a new object; retried with the exact solver's self-test and a nudge when it returns nothing (found with the right front door of the large sedan)."""
    for nudge, self_test in ((0.0, False), (0.0, True), (0.00023, True)):
        dup = dup_obj(body, name)
        c2 = bpy.data.objects.new(cutter.name + '_b', cutter.data.copy())
        bpy.context.scene.collection.objects.link(c2)
        c2.location = (nudge, nudge * 0.7, -nudge * 0.5)
        bpy.context.view_layer.update()
        boolean(dup, [c2], 'INTERSECT', self_test=self_test)
        if len(dup.data.polygons) > 60:
            return dup
        bpy.data.objects.remove(dup, do_unlink=True)
    raise RuntimeError('part ' + name + ' came out empty')


def set_origin(ob, p, parent):
    ob.data.transform(Matrix.Translation(-V3(p)))
    ob.location = V3(p)
    ob.parent = parent


def split_doors(body, root):
    doors, cutters = {}, []
    for dk, d in G.DOORS.items():
        for s in d.get('sides', (1, -1)):
            k = dk + ('L' if s > 0 else 'R')
            c = door_cutter(dk, d, s, 'cut_door_' + k)
            part = intersect_part(body, c, 'Door_' + k)
            cutters.append(grow_cutter(c, 0.0022))
            hx = G.X(d['hinge_col']) + d.get('hinge_dx', -0.004)
            doors[k] = (part, V3((hx, s * (G.W - 0.012), d.get('hinge_z', 0.60))))
            log('door', k, len(part.data.polygons))
            bpy.data.objects.remove(c, do_unlink=True)
    boolean(body, cutters, 'DIFFERENCE')
    bpy.context.view_layer.update()
    out = {}
    for k, (ob, hp) in doors.items():
        set_origin(ob, hp, root)
        smooth(ob, 40)
        out[k] = ob
    return out


def grow_cutter(c, g):
    """A copy of the cutter object scaled out from its centre by g on every side (about)."""
    d = dup_obj(c, c.name + '_gap')
    bb = [V3(v) for v in d.bound_box]
    ctr = sum(bb, V3()) / 8
    size = [max(b[i] for b in bb) - min(b[i] for b in bb) for i in range(3)]
    d.data.transform(Matrix.Translation(-ctr))
    d.data.transform(Matrix.Diagonal((1 + 2 * g / size[0], 1 + 2 * g / size[1], 1 + 2 * g / size[2], 1.0)))
    d.data.transform(Matrix.Translation(ctr))
    return d


def panel_cutter(p):
    if p['kind'] == 'top':
        pts = [V3((x, y, 0)) for x, y in p['poly']]
        m = Mesh()
        m.loft([[V3((q.x, q.y, p['zlo'])) for q in pts], [V3((q.x, q.y, 2.2)) for q in pts]], 'interior', caps=True)
        return m.finish('cut_' + p['name'])
    pts = [V3((x, 0, z)) for x, z in p['poly']]                  # 'rear': an XZ outline extruded across the car
    m = Mesh()
    m.loft([[V3((q.x, -p['y'], q.z)) for q in pts], [V3((q.x, p['y'], q.z)) for q in pts]], 'interior', caps=True)
    return m.finish('cut_' + p['name'])


def split_panels(body, root):
    out = {}
    for p in G.PANELS:
        c = panel_cutter(p)
        part = intersect_part(body, c, p['name'])
        g = Mesh()
        gp = p['poly']
        if p['kind'] == 'top':
            pts = [V3((x, y, 0)) for x, y in gp]
            gg = offset_poly([(q.x, q.y) for q in pts], 0.0022)
            g.loft([[V3((x, y, p['zlo'] - 0.001)) for x, y in gg], [V3((x, y, 2.3)) for x, y in gg]], 'interior', caps=True)
        else:
            gg = offset_poly(list(gp), 0.0022)
            g.loft([[V3((x, -p['y'] - 0.0022, z)) for x, z in gg], [V3((x, p['y'] + 0.0022, z)) for x, z in gg]], 'interior', caps=True)
        gc = g.finish('cut_' + p['name'] + '_gap')
        bpy.data.objects.remove(c, do_unlink=True)
        boolean(body, [gc], 'DIFFERENCE')
        set_origin(part, V3(p['pivot']), root)
        smooth(part, 40)
        out[p['name']] = part
        log('panel', p['name'], len(part.data.polygons))
    return out


def retag_cabin(ob):
    """The cut faces of the cabin took the 'interior' material: floors become carpet, the roof's underside the headliner, the rest stays the vinyl of the door cards."""
    me = ob.data
    names = [mm.name for mm in me.materials]

    def slot(kind):
        m = mat(kind)
        if m.name not in names:
            me.materials.append(m)
            names.append(m.name)
        return names.index(m.name)
    ii = names.index('M_interior') if 'M_interior' in names else None
    if ii is None:
        return
    ic, ih = slot('carpet'), slot('headliner')
    bm = bmesh.new()
    bm.from_mesh(me)
    for f in bm.faces:
        if f.material_index == ii:
            if f.normal.z > 0.75 and f.calc_center_median().z < 0.6:
                f.material_index = ic
            elif f.normal.z < -0.6 and f.calc_center_median().z > 1.0:
                f.material_index = ih
    bm.to_mesh(me)
    bm.free()


# ---- parts that belong to the body or to one door / lid ---------------------------------------------------------------------------------------------------------------------------
class Parts(dict):
    def __missing__(self, k):
        self[k] = Mesh()
        return self[k]


def attach_to(ob, parent):
    bpy.context.view_layer.update()
    ob.parent = parent
    ob.matrix_parent_inverse = parent.matrix_world.inverted()


def finish_parts(parts, name, root, owners, sharp=50):
    obs = {}
    for k, m in parts.items():
        if not m.kinds:
            continue
        ob = m.finish(name if k == 'body' else f'{name}_{k}', root, sharp=sharp)
        if k != 'body':
            attach_to(ob, owners[k])
        obs[k] = ob
    return obs


def ray_to(bvh, o, d, far=6.0):
    hit, nrm, _, _ = bvh.ray_cast(V3(o), V3(d).normalized(), far)
    return hit, nrm


def on_side(bvh, x, z, s, lift=0.003):
    hit, nrm = ray_to(bvh, (x, s * 1.6, z), (0, -s, 0), 3.2)
    if hit is None:
        return V3((x, s * side_y(x, z), z)), V3((0, s, 0))
    return hit + nrm * lift, nrm


def on_top(bvh, x, y, lift=0.003):
    hit, nrm = ray_to(bvh, (x, y, 2.6), (0, 0, -1), 3.2)
    if hit is None:
        return V3((x, y, top_at(x, y))), V3((0, 0, 1))
    return hit + nrm * lift, nrm


def owner_of(x, z, s):
    """Which part owns the side-surface point (x, z): a door's key or 'body'."""
    for dk, d in G.DOORS.items():
        if s not in d.get('sides', (1, -1)):
            continue
        poly = to_m(d['lower'])
        if G.Z(d['bottom_row']) <= z <= G.Z_BELT + 0.5 and point_in(poly, x, z):
            return dk + ('L' if s > 0 else 'R')
    return 'body'


def point_in(poly, x, z):
    inside = False
    n = len(poly)
    for i in range(n):
        (x0, z0), (x1, z1) = poly[i], poly[(i + 1) % n]
        if (z0 > z) != (z1 > z) and x < (x1 - x0) * (z - z0) / (z1 - z0) + x0:
            inside = not inside
    return inside


def side_strip(parts, bvh, s, xa, xb, z, width, thick, kind, lift=0.0):
    """A flat moulding along the side at height z from xa to xb; each short piece goes to the part (door or body) that owns its middle."""
    n = max(2, int(abs(xb - xa) / 0.02))
    xs = [xa + (xb - xa) * k / n for k in range(n + 1)]
    run = [xs[0]]
    cur = owner_of(0.5 * (xs[0] + xs[1]), z, s)
    for a, b in zip(xs, xs[1:]):
        ow = owner_of(0.5 * (a + b), z, s)
        if ow != cur:
            _emit(parts, bvh, s, run, z, width, thick, kind, lift, cur)
            run, cur = [a], ow
        run.append(b)
    _emit(parts, bvh, s, run, z, width, thick, kind, lift, cur)


def _emit(parts, bvh, s, xs, z, width, thick, kind, lift, owner):
    if len(xs) < 2:
        return
    hits = [on_side(bvh, x, z, s, lift) for x in xs]
    CK.strip(parts[owner], [p for p, _ in hits], [n for _, n in hits], width, thick, kind)


def build_glass(bvh):
    """Each pane a 5 mm sheet laid 6 mm inside the body's surface, in a rubber gasket."""
    parts = Parts()
    inset = 0.006
    for nm, poly in G.SIDE_WINDOWS.items():
        pts = [(x, z) for x, z in to_m(poly)]
        if len(pts) == 3:
            pts = [pts[0], pts[1], pts[2], pts[2]]
        cx = sum(p[0] for p in pts) / 4
        cz = sum(p[1] for p in pts) / 4
        grow = [(x + 0.009 * math.copysign(1, x - cx), max(z + 0.009 * math.copysign(1, z - cz), G.Z_BELT - 0.03)) for x, z in pts]
        for s in G.WINDOW_SIDES.get(nm, (1, -1)):
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
                    hit, nrm = ray_to(bvh, (p.x, s * 1.6, p.z), (0, -s, 0), 3.2)
                    if hit is None or abs(hit.y) < 0.4:
                        hit, nrm = V3((p.x, s * G.gh_side_y(p.z), p.z)), V3((0, s, 0))
                    row.append(hit - nrm * inset)
                rows.append(row)
            owner = owner_of(cx, G.Z_BELT - 0.03, s) if G.WINDOW_OWNER.get(nm, True) else 'body'
            m = parts[owner]
            ns = CK.pane(m, rows, 0.005, (0, s, 0))
            CK.seal(m, rows, ns, 0.016, 0.005)
    for nm, d, toward, direction in (('ws', G.WS, (0.6, 0, 1), -1), ('bl', G.BL, (-0.6, 0, 1), 1)):
        if d is None:
            continue
        rows = []
        nu, nv = 24, 30
        owner = d.get('owner', 'body')
        for j in range(nu + 1):
            z = d['z0'] + (d['z1'] - d['z0']) * j / nu
            hw = d['y0'] + (d['y1'] - d['y0']) * (z - d['z0']) / (d['z1'] - d['z0']) + 0.010
            row = []
            for i in range(nv + 1):
                y = -hw + 2 * hw * i / nv
                hit, nrm = ray_to(bvh, (direction * 6.0 * (-1) if False else (6.0 if nm == 'ws' else -6.0), y, z), (-1 if nm == 'ws' else 1, 0, 0), 12.0)
                if hit is None:
                    hit, nrm = V3((d['x0'], y, z)), V3(toward)
                row.append(hit - nrm * inset)
            rows.append(row)
        # the rows run bottom to top: wind them so the outer face looks out
        m = parts[owner]
        ns = CK.pane(m, rows, 0.005, toward)
        CK.seal(m, rows, ns, 0.020, 0.005)
        bo, bn = CK.border(rows), CK.border(ns)
        c = sum(bo, V3()) / len(bo)
        rev = []
        for p, nn in zip(bo, bn):
            o = (p - c)
            o = (o - nn * o.dot(nn)).normalized()
            rev.append(p + o * 0.022 + nn * inset)
        CK.strip(m, rev, bn, 0.012, 0.003, G.REVEAL, loop=True)
    return parts


def build_trim(bvh):
    parts = Parts()
    for s in (1, -1):
        # window frames round the side openings
        for nm, poly in G.SIDE_WINDOWS.items():
            if s not in G.WINDOW_SIDES.get(nm, (1, -1)):
                continue
            pts = [(x, max(z, G.Z_BELT + 0.003)) for x, z in to_m(poly)]
            pts = offset_poly(pts, 0.009) if len(pts) > 3 else pts
            path = densify([V3((x, 0, z)) for x, z in pts + [pts[0]]], 0.012)[:-1]
            hits = [on_side(bvh, p.x, p.z, s, 0.0) for p in path]
            owner = owner_of(sum(p[0] for p in pts) / len(pts), G.Z_BELT - 0.03, s)
            CK.strip(parts[owner], [p for p, _ in hits], [n for _, n in hits], 0.014, 0.003, G.WINDOW_TRIM, loop=True)
        # belt moulding
        side_strip(parts, bvh, s, G.TRIM_X0, G.TRIM_X1, G.Z_BELT - 0.008, 0.012, 0.005, G.WINDOW_TRIM)
        # lower side mouldings (rub strips) and the rocker
        for (xa, xb, zz, w, t, kind) in G.SIDE_STRIPS:
            side_strip(parts, bvh, s, xa, xb, zz, w, t, kind)
        # wheel lip mouldings
        for xc in (-G.HWB, G.HWB):
            pp = arch_poly(xc)[1:-1]
            path = []
            for q in pp:
                dd = V3((q.x - xc, 0, q.z - G.ZC))
                dd = dd.normalized() * 0.013 if dd.length > 1e-6 else V3()
                path.append(V3((q.x + dd.x, 0, q.z + dd.z)))
            path = densify(path, 0.012)
            hits = [on_side(bvh, p.x, p.z, s, 0.0) for p in path]
            CK.strip(parts['body'], [p for p, _ in hits], [n for _, n in hits], 0.020, 0.004, 'bumper')
        # door handles, locks and side mirrors
        for dk, d in G.DOORS.items():
            if s not in d.get('sides', (1, -1)):
                continue
            key = dk + ('L' if s > 0 else 'R')
            hx, hz = d['handle']
            p, n = on_side(bvh, G.X(hx), G.Z(hz), s, 0.0)
            m = parts[key]
            m.rbox(p + n * 0.004, (0.14, 0.010, 0.030), 0.005, G.HANDLE_KIND)
            m.rbox(p + n * 0.006 - V3((0, 0, 0.004)), (0.115, 0.006, 0.014), 0.002, 'black')
            if d.get('lock'):
                lp, ln = on_side(bvh, G.X(d['lock'][0]), G.Z(d['lock'][1]), s, 0.0)
                m.cyl(lp, lp + ln * 0.006, 0.011, 'chrome', seg=16)
                m.cyl(lp + ln * 0.006, lp + ln * 0.0065, 0.006, 'black', seg=12)
            if d.get('mirror'):
                mx = G.X(d['mirror'])
                bz = G.Z_BELT
                m.rbox(V3((mx, s * (G.GH_Y_BELT + 0.02), bz + 0.012)), (0.08, 0.04, 0.026), 0.008, 'black')
                head = V3((mx - 0.02, s * (G.W + 0.085), bz + 0.075))
                m.tube([V3((mx, s * (G.GH_Y_BELT + 0.02), bz + 0.02)), V3((mx - 0.012, s * (G.W + 0.02), bz + 0.05)), head], 0.010, 'black', seg=8)
                m.rbox(head, (0.060, 0.150, 0.100), 0.022, 'black')
                m.rbox(head + V3((-0.0305, 0, 0)), (0.004, 0.130, 0.082), 0.006, 'black')
                m.box(head + V3((-0.0325, 0, 0)), (0.002, 0.120, 0.074), 'mirror')
    m = parts['body']
    # radio antenna on the roof's rear, on a rubber base sunk into the skin
    xa = G.X(G.col_roof_rear) + 0.30
    p, _ = on_top(bvh, xa, 0.0, -0.004)
    m.cyl(p, p + V3((0, 0, 0.022)), 0.022, 'black', seg=14, r1=0.016)
    m.cyl(p + V3((0, 0, 0.022)), p + V3((-0.10, 0, 0.78)), 0.0025, 'black', seg=6, r1=0.0015)
    if G.WS is not None:
        # wipers parked on the glass: the pivots at the windscreen's foot, the arms along its surface
        zf = G.WS['z0'] + 0.05
        for py in (0.40, -0.12):
            hit, nrm = ray_to(bvh, (6.0, py, zf), (-1, 0, 0), 12.0)
            if hit is None:
                continue
            piv = hit + nrm * 0.004
            CK.wiper_parked(m, piv, V3((0, -1, 0)), nrm, 0.40, 0.42)
    # door hardware on the body: two hinges at each hinged door's edge, the striker at the latch edge
    for dk, d in G.DOORS.items():
        for s in d.get('sides', (1, -1)):
            hx = G.X(d['hinge_col'])
            for z in (0.45, 0.80):
                m.rbox(V3((hx + d.get('hinge_dx', -0.004), s * (G.W - 0.06), z)), (0.035, 0.07, 0.055), 0.006, 'black')
            xs = G.X(d['latch_col'])
            m.rbox(V3((xs, s * (G.W - 0.07), 0.82)), (0.012, 0.04, 0.05), 0.004, 'chrome')
    return parts


def door_inner(parts):
    """What the doors carry inside: armrests, pulls, window cranks, lock knobs, the inside handles, map pockets."""
    for dk, d in G.DOORS.items():
        for s in d.get('sides', (1, -1)):
            m = parts[dk + ('L' if s > 0 else 'R')]
            xs = [G.X(a) for a, _ in d['lower']]
            x0, x1 = min(xs) + 0.10, max(xs) - 0.08
            xm = 0.5 * (x0 + x1)
            y_in = s * (G.CAB_Y - 0.02)
            m.rbox(V3((xm, y_in, G.Z_BELT - 0.22)), (x1 - x0, 0.07, 0.05), 0.02, 'vinyl')
            m.rbox(V3((xm + 0.05, y_in - s * 0.015, G.Z_BELT - 0.17)), (0.14, 0.03, 0.03), 0.01, 'black')
            c = V3((xm - 0.05, y_in - s * 0.01, G.Z_BELT - 0.36))
            m.cyl(c, c - V3((0, s * 0.02, 0)), 0.02, 'chrome', seg=12)
            m.tube([c - V3((0, s * 0.02, 0)), c - V3((-0.07, s * 0.02, 0.04))], 0.006, 'chrome', seg=6)
            m.cyl(c - V3((-0.07, s * 0.02, 0.04)), c - V3((-0.07, s * 0.05, 0.04)), 0.008, 'black', seg=8)
            m.cyl(V3((x1 - 0.06, y_in, G.Z_BELT - 0.02)), V3((x1 - 0.06, y_in, G.Z_BELT + 0.02)), 0.006, 'chrome', seg=8)
            m.rbox(V3((x1 - 0.12, y_in, G.Z_BELT - 0.13)), (0.10, 0.02, 0.03), 0.006, 'chrome')
            m.rbox(V3((xm, y_in + s * 0.002, 0.40)), (x1 - x0 - 0.04, 0.012, 0.08), 0.004, 'black')
            for k in range(3):
                m.rbox(V3((xm, y_in, G.Z_BELT - 0.30 - 0.08 * k)), (x1 - x0 - 0.10, 0.006, 0.004), 0.001, 'dash')


# ---- bumpers, grille, lamps, plates ------------------------------------------------------------------------------------------------------------------------------------------------
def bumper_mesh(front):
    """A bumper: a profile swept along a plan path that is nearly straight and wraps back round both corners (a node of its own, to be torn off)."""
    B = G.BUMP_F if front else G.BUMP_R
    sx = 1 if front else -1
    xf = G.X_FBUMP if front else G.X_RBUMP
    zt, zb = B['zt'], B['zb']
    R, yc = B.get('R', 0.13), B['yc']
    kind = B['kind']
    path = []
    for k in range(9):
        a = math.radians(80 - 80 * k / 8)
        path.append((xf - sx * (0.03 + R - R * math.cos(a)), -(yc + R * math.sin(a)), V3((sx * math.cos(a), -math.sin(a), 0))))
    for k in range(1, 30):
        y = -yc + 2 * yc * k / 30
        path.append((xf - sx * B.get('bow', 0.03) * (y / yc) ** 2, y, V3((sx, 0, 0))))
    for k in range(9):
        a = math.radians(80 * k / 8)
        path.append((xf - sx * (0.03 + R - R * math.cos(a)), yc + R * math.sin(a), V3((sx * math.cos(a), math.sin(a), 0))))
    m = Mesh()
    h = zt - zb
    prof = [(-B.get('depth', 0.16), zt - 0.006), (-0.02, zt), (0.0, zt - 0.010), (0.006, zt - 0.12 * h), (0.006, zb + 0.22 * h), (0.0, zb + 0.08 * h), (-0.03, zb), (-B.get('depth', 0.16), zb)]
    rings = []
    for x, y, n in path:
        rings.append([V3((x, y, 0)) + n * dx + V3((0, 0, z)) for dx, z in prof])
    m.loft(rings, kind, caps=True)
    if B.get('rub', True):
        strip = []
        for x, y, n in path[4:-4]:
            strip.append([V3((x, y, 0)) + n * dx + V3((0, 0, z)) for dx, z in ((0.004, zt - 0.40 * h), (0.016, zt - 0.38 * h), (0.016, zt - 0.62 * h), (0.004, zt - 0.60 * h))])
        m.loft(strip, 'rubber', caps=True)
    for s in (1, -1):
        m.rbox(V3((xf - sx * 0.030, s * B.get('guard_y', 0.58), zb + 0.5 * h - 0.02)), (0.08, 0.08, h + 0.03), 0.02, 'rubber')
    return m


def plate(m, x, z, front, text):
    """A fictional plate (no state, no marks): a white pressed plate with an embossed border and the number in raised blue characters."""
    sx = 1 if front else -1
    w, h = 0.305, 0.152
    m.rbox(V3((x + sx * 0.002, 0, z)), (0.006, w + 0.03, h + 0.03), 0.006, 'black')
    m.rbox(V3((x + sx * 0.006, 0, z)), (0.004, w, h), 0.004, 'plate')
    pts = [V3((x + sx * 0.0085, p[0], p[1])) for p in CK_rrect(-w / 2 + 0.008, z - h / 2 + 0.008, w / 2 - 0.008, z + h / 2 - 0.008, 0.008)]
    m.tube(pts, 0.0012, 'plate_ink', seg=4, loop=True)
    ex = V3((0, -sx, 0)) if False else V3((0, sx if False else (-1 if front else 1) * 0 + 1, 0))
    # the text runs along the car's Y seen from outside: from the front, left of the picture is the car's +Y; from behind, left is -Y
    d = V3((0, 1 if front else -1, 0))
    CK.text_on_plane(m, text, 'plate_ink', V3((x + sx * 0.0078, 0, z - 0.034)) - d * 0.0, d, V3((0, 0, 1)), V3((sx, 0, 0)), 0.070, 0.002, 'arialbd.ttf', 1.0)
    CK.text_on_plane(m, 'AMERICA', 'plate_ink', V3((x + sx * 0.0078, 0, z + 0.052)), d, V3((0, 0, 1)), V3((sx, 0, 0)), 0.016, 0.0015, 'arialbd.ttf', 1.0)


def CK_rrect(x0, z0, x1, z1, r, n=3):
    pts = []
    for cx, cz, a0 in ((x1 - r, z1 - r, 0), (x0 + r, z1 - r, 90), (x0 + r, z0 + r, 180), (x1 - r, z0 + r, 270)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return pts


def headlamp(m, lens_m, c, w, h, kind_rim='chrome'):
    """A rectangular headlamp: bezel, paraboloid reflector, bulb, lens of small prisms (lens goes to its own mesh)."""
    x, y, z = c
    m.rbox(V3((x + 0.002, y, z)), (0.024, w + 0.020, h + 0.020), 0.008, kind_rim)
    m.box(V3((x + 0.0045, y, z)), (0.004, w + 0.004, h + 0.004), 'black')
    CK.reflector(m, V3((x + 0.022, y, z)), (1, 0, 0), (0, 0, 1), w, h, 0.032, 'reflector', n=16)
    CK.bulb(m, V3((x + 0.004, y, z)), (1, 0, 0), 0.010, 'bulb')
    m.cyl(V3((x + 0.020, y, z)), V3((x + 0.024, y, z)), 0.013, 'reflector', seg=14)
    CK.fluted_lens(lens_m, V3((x + 0.030, y, z)), (1, 0, 0), (0, 0, 1), w, h, 0.004, max(4, int(w / 0.012)), max(3, int(h / 0.012)), 'lens_clear', 'cells', bulge=0.005)


def round_headlamp(m, lens_m, c, r):
    x, y, z = c
    CK.round_lamp(m, V3((x + 0.004, y, z)), (1, 0, 0), r, 0.06, 'lens_clear')


def build_front_rear(root):
    m = Mesh()
    x = G.X_NOSE
    Gr = G.GRILLE
    zc = 0.5 * (Gr['z0'] + Gr['z1'])
    hh = Gr['z1'] - Gr['z0']
    yh = Gr['y']
    m.box(V3((x + 0.006, 0, zc)), (0.012, 2 * yh, hh), 'black')
    nb = Gr.get('nv', 13)
    for k in range(nb):
        m.box(V3((x + 0.024, -yh + 2 * yh * k / (nb - 1), zc)), (0.030, 0.006, hh - 0.01), Gr['kind'])
    for k in range(Gr.get('nh', 5)):
        m.box(V3((x + 0.020, 0, Gr['z0'] + 0.01 + (hh - 0.02) * k / max(Gr.get('nh', 5) - 1, 1))), (0.026, 2 * yh - 0.01, 0.006), Gr['kind'])
    m.tube([V3((x + 0.04, p[0], p[1])) for p in CK_rrect(-yh - 0.005, Gr['z0'] - 0.005, yh + 0.005, Gr['z1'] + 0.005, 0.015)], 0.010, Gr.get('frame', 'chrome'), seg=8, loop=True)
    lamps_h, lamps_p, lamps_t, lamps_m = Mesh(), Mesh(), Mesh(), Mesh()
    Hd = G.HEAD
    for s in (1, -1):
        for (yc_, w_, h_, z_) in Hd['lamps']:
            headlamp(m, lamps_h, (x + Hd.get('dx', 0.0), s * yc_, z_), w_, h_, Hd.get('rim', 'chrome'))
        # parking / turn lamp
        Pk = G.PARK
        CK.reflector(m, V3((x + 0.014, s * Pk['y'], Pk['z'])), (1, 0, 0), (0, 0, 1), Pk['w'], Pk['h'], 0.010, 'reflector', n=10)
        CK.bulb(m, V3((x + 0.006, s * Pk['y'], Pk['z'])), (1, 0, 0), 0.008, 'bulb')
        CK.fluted_lens(lamps_p, V3((x + 0.024, s * Pk['y'], Pk['z'])), (1, 0, 0), (0, 0, 1), Pk['w'], Pk['h'], 0.004, max(4, int(Pk['w'] / 0.012)), 1, 'lens_amber', 'flutes', bulge=0.002)
        m.rbox(V3((x + 0.016, s * Pk['y'], Pk['z'])), (0.010, Pk['w'] + 0.012, Pk['h'] + 0.012), 0.004, 'chrome')
        # the corner / side marker lamp wrapping the fender's corner
        r = G.ROUND_NOSE
        cx, cy = G.X_NOSE - r, s * (G.W - r)
        Mk = G.MARK_F
        rows = []
        for j in range(4):
            z = Mk[0] + (Mk[1] - Mk[0]) * j / 3
            row = []
            for k in range(11):
                a = math.radians(10 + 70 * k / 10)
                d = V3((math.cos(a), s * math.sin(a), 0))
                row.append(V3((cx, cy, z)) + d * (r + 0.003 + 0.0012 * (k % 2)))
            rows.append(row)
        refl = [[p - (p - V3((cx, cy, p.z))).normalized() * 0.012 for p in row] for row in rows]
        m.grid(refl if s > 0 else [list(reversed(rr)) for rr in refl], 'reflector')
        lamps_m.grid(rows if s > 0 else [list(reversed(rr)) for rr in rows], 'lens_amber')
        for rr in (rows[0], rows[-1]):
            m.tube(list(rr), 0.005, 'chrome', seg=6)
        # tail lamp
        T = G.TAIL
        xt = G.X_TAIL + T.get('dx', 0.0)
        yc_, w_, z0, z1 = T['y'], T['w'], T['z0'], T['z1']
        zc2, hh2 = 0.5 * (z0 + z1), z1 - z0
        m.rbox(V3((xt - 0.004, s * yc_, zc2)), (0.022, w_ + 0.020, hh2 + 0.020), 0.008, T.get('rim', 'black'))
        CK.reflector(m, V3((xt - 0.011, s * yc_, zc2)), (-1, 0, 0), (0, 0, 1), w_ - 0.01, hh2 - 0.01, 0.022, 'reflector', n=12)
        for zb in (zc2 - hh2 * 0.22, zc2 + hh2 * 0.22):
            CK.bulb(m, V3((xt + 0.004, s * yc_, zb)), (-1, 0, 0), 0.010, 'bulb')
        lamps_t.rbox(V3((xt - 0.016, s * yc_, zc2 + hh2 * 0.16)), (0.010, w_, hh2 * 0.66), 0.006, 'lens_red')
        lamps_t.rbox(V3((xt - 0.016, s * yc_, zc2 - hh2 * 0.34)), (0.010, w_, hh2 * 0.28), 0.006, 'lens_clear')
        for k in range(int(hh2 / 0.02)):
            lamps_t.box(V3((xt - 0.022, s * yc_, z0 + hh2 * 0.35 + 0.02 * k)), (0.004, w_ - 0.004, 0.005), 'lens_red')
    # the front plate on the bumper's face or the nose, the rear plate in its recess
    plate(m, G.PLATE_F[0], G.PLATE_F[1], True, G.PLATE_TEXT)
    plate(m, G.PLATE_R[0], G.PLATE_R[1], False, G.PLATE_TEXT)
    for s in (1, -1):
        mk = G.MARK_R
        rows = []
        for j in range(3):
            z = mk[0] + (mk[1] - mk[0]) * j / 2
            rows.append([on_side_rear(s, G.X_TAIL + 0.012 + (0.10) * k / 4, z) for k in range(5)])
        lamps_m.grid(rows if s > 0 else [list(reversed(rr)) for rr in rows], 'lens_red')
    return m, (lamps_h, lamps_p, lamps_t, lamps_m)


_BVH = {}


def on_side_rear(s, x, z):
    p, _ = on_side(_BVH['body'], x, z, s, 0.003)
    return p


# ---- the engine bay, underbody and chassis ---------------------------------------------------------------------------------------------------------------------------------------------
def build_engine(root):
    m = Mesh()
    xc = G.ENGINE_X
    z0 = 0.42
    # block, heads, air cleaner, radiator and fan, battery, hoses, strut towers
    m.rbox(V3((xc, 0, z0 + 0.12)), (0.50, 0.40, 0.30), 0.03, 'engine')
    for s in (1, -1):
        m.rbox(V3((xc, s * 0.20, z0 + 0.30)), (0.44, 0.17, 0.12), 0.02, 'engine')
        m.rbox(V3((xc, s * 0.22, z0 + 0.375)), (0.46, 0.15, 0.03), 0.01, 'black')
        for k in range(4):
            m.cyl(V3((xc - 0.17 + 0.11 * k, s * 0.235, z0 + 0.39)), V3((xc - 0.17 + 0.11 * k, s * 0.235, z0 + 0.43)), 0.012, 'black', seg=10)
            m.tube([V3((xc - 0.17 + 0.11 * k, s * 0.235, z0 + 0.43)), V3((xc - 0.17 + 0.11 * k, s * 0.16, z0 + 0.46)), V3((xc - 0.1, s * 0.05, z0 + 0.45))], 0.006, 'black', seg=6)
    m.cyl(V3((xc - 0.02, 0, z0 + 0.36)), V3((xc - 0.02, 0, z0 + 0.44)), 0.17, 'steel', seg=32)
    m.cyl(V3((xc - 0.02, 0, z0 + 0.44)), V3((xc - 0.02, 0, z0 + 0.455)), 0.15, 'black', seg=32)
    xr = G.X_NOSE - 0.12
    m.rbox(V3((xr, 0, z0 + 0.22)), (0.05, 0.72, 0.46), 0.01, 'steel')
    for k in range(18):
        m.box(V3((xr + 0.027, -0.34 + 0.04 * k, z0 + 0.22)), (0.004, 0.006, 0.42), 'black')
    m.cyl(V3((xr - 0.04, 0, z0 + 0.22)), V3((xr - 0.07, 0, z0 + 0.22)), 0.20, 'rubber', seg=24)
    for k in range(5):
        a = 2 * math.pi * k / 5
        m.rbox(V3((xr - 0.06, 0.09 * math.cos(a), z0 + 0.22 + 0.09 * math.sin(a))), (0.004, 0.10, 0.04), 0.003, 'black',
               (V3((1, 0, 0)), V3((math.cos(a), math.sin(a), 0)).cross(V3((1, 0, 0))) if False else V3((0, math.cos(a), math.sin(a))), V3((0, -math.sin(a), math.cos(a)))))
    m.rbox(V3((xc - 0.1, -0.5, z0 + 0.14)), (0.19, 0.13, 0.17), 0.01, 'black')
    for yb in (-0.46, -0.54):
        m.cyl(V3((xc - 0.1, yb, z0 + 0.23)), V3((xc - 0.1, yb, z0 + 0.25)), 0.013, 'chrome', seg=8)
    for s in (1, -1):
        m.cyl(V3((xc - 0.12, s * 0.68, z0 + 0.06)), V3((xc - 0.12, s * 0.68, z0 + 0.42)), 0.09, 'steel', seg=20)
    m.tube([V3((xr - 0.02, 0.2, z0 + 0.38)), V3((xc + 0.15, 0.2, z0 + 0.42)), V3((xc + 0.1, 0.18, z0 + 0.38))], 0.022, 'rubber', seg=10)
    ob = m.finish('Engine', root, sharp=40)
    # keep everything under the hood: squash the bay's height to the lowest hood surface over the bay, less a margin
    xs = [G.X_COWL + 0.02 + (G.X_NOSE - 0.03 - G.X_COWL - 0.02) * k / 20 for k in range(21)]
    limit = min(G.top_z(x) for x in xs) - 0.10
    zmax = max(v.co.z for v in ob.data.vertices)
    zlo = 0.25
    if zmax > limit:
        f = max(0.3, (limit - zlo) / (zmax - zlo))
        for v in ob.data.vertices:
            v.co.z = zlo + (v.co.z - zlo) * f
    return ob


def build_under(root):
    m = Mesh()
    L0, L1 = G.X_TAIL + 0.15, G.X_NOSE - 0.10
    zb = G.bottom_z(0.0) + 0.02
    # the floor pan with its tunnel and two cross members
    m.loft([[V3((x, -0.62, zb + 0.005)), V3((x, -0.10, zb + 0.005)), V3((x, -0.08, zb + 0.10)), V3((x, 0.08, zb + 0.10)), V3((x, 0.10, zb + 0.005)), V3((x, 0.62, zb + 0.005))]
            for x in (L0 + 0.5 + k * (L1 - L0 - 1.0) / 20 for k in range(21))], 'chassis', closed=False)
    for xx in (G.WHEELBASE * 0.18, -G.WHEELBASE * 0.12):
        m.rbox(V3((xx, 0, zb + 0.02)), (0.10, 1.24, 0.05), 0.01, 'chassis')
    for s in (1, -1):
        m.rbox(V3((0.0, s * 0.60, zb + 0.04)), (G.WHEELBASE + 0.7, 0.07, 0.10), 0.02, 'chassis')
    # exhaust: pipe from the manifold, a catalyst, the muffler, the tail pipe out behind the bumper
    path = [V3((G.ENGINE_X + 0.05, 0.12, 0.45)), V3((G.ENGINE_X - 0.25, 0.20, zb + 0.06)), V3((-0.1, 0.20, zb + 0.04)), V3((-G.HWB + 0.15, 0.28, zb + 0.04)), V3((G.X_TAIL + 0.18, 0.40, zb + 0.06)),
            V3((G.X_RBUMP + 0.10, 0.46, zb + 0.10))]
    m.tube(path, 0.026, 'raw_steel', seg=12)
    m.cyl(V3((-0.2, 0.2, zb + 0.04)), V3((0.2, 0.2, zb + 0.04)), 0.045, 'raw_steel', seg=14)
    m.rbox(V3((-G.HWB + 0.55, 0.30, zb + 0.06)), (0.70, 0.22, 0.14), 0.05, 'raw_steel')
    m.cyl(V3((G.X_RBUMP + 0.10, 0.46, zb + 0.10)), V3((G.X_RBUMP + 0.02, 0.46, zb + 0.10)), 0.032, 'chrome', seg=14)
    # fuel tank and its straps
    xf = -G.HWB + 0.60
    m.rbox(V3((xf, -0.2, zb + 0.10)), (0.80, 0.55, 0.20), 0.05, 'chassis')
    # axles: a beam with a differential (rear) or a subframe (front), control arms, springs and dampers
    for xa, fr in ((-G.HWB, False), (G.HWB, True)):
        tr = (G.TRACK_F if fr else G.TRACK_R) / 2
        if fr:
            m.rbox(V3((xa, 0, G.ZC - 0.08)), (0.30, 1.0, 0.07), 0.02, 'chassis')
            m.rbox(V3((xa - 0.1, 0, G.ZC - 0.06)), (0.28, 0.40, 0.22), 0.04, 'chassis')
        else:
            if G.DRIVE == 'rwd':
                m.cyl(V3((xa, -tr + 0.1, G.ZC)), V3((xa, tr - 0.1, G.ZC)), 0.04, 'chassis', seg=14)
                m.rbox(V3((xa, 0, G.ZC)), (0.30, 0.28, 0.24), 0.06, 'chassis')
            else:
                m.cyl(V3((xa, -tr + 0.1, G.ZC + 0.05)), V3((xa, tr - 0.1, G.ZC + 0.05)), 0.05, 'chassis', seg=14)
        for s in (1, -1):
            m.rbox(V3((xa, s * 0.5, G.ZC - 0.02)), (0.07, 0.65, 0.04), 0.01, 'chassis')
            CK.coil_spring(m, V3((xa + 0.02, s * (tr - 0.20), G.ZC + 0.02)), V3((xa + 0.02, s * (tr - 0.20), G.ZC + 0.30)), 0.060, 0.007, 7, 'spring')
            CK.damper(m, V3((xa - 0.10, s * (tr - 0.12), G.ZC - 0.05)), V3((xa - 0.10, s * (tr - 0.16), G.ZC + 0.35)))
            m.cyl(V3((xa, s * (tr - 0.05), G.ZC)), V3((xa, s * (tr - 0.20), G.ZC)), 0.03, 'chassis', seg=14)
    if G.DRIVE == 'rwd':
        m.cyl(V3((G.ENGINE_X - 0.3, 0, zb + 0.07)), V3((-G.HWB, 0, zb + 0.09)), 0.035, 'raw_steel', seg=14)
    # brake lines and parking brake cable
    for s in (1, -1):
        m.tube([V3((G.HWB - 0.3, s * 0.35, zb + 0.07)), V3((0.0, s * 0.36, zb + 0.07)), V3((-G.HWB + 0.3, s * 0.38, zb + 0.07)), V3((-G.HWB, s * 0.7, G.ZC + 0.1))], 0.004, 'steel', seg=5)
    return m.finish('Underbody', root, sharp=40)


# ---- wheels ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def wheel_mesh(s, front):
    m = Mesh()
    R, Rr = G.R_TYRE, G.R_RIM
    CK.tyre(m, s, R, Rr, G.W_TYRE, CK.tread_allseason, G.TYRE_TEXT, n=144)
    sec = [(-0.090, Rr + 0.013), (-0.085, Rr + 0.015), (-0.080, Rr + 0.003), (-0.075, Rr - 0.006), (0.075, Rr - 0.006), (0.080, Rr + 0.003), (0.085, Rr + 0.015),
           (0.090, Rr + 0.013), (0.088, Rr + 0.002), (0.082, Rr - 0.004)]
    m.loft([[V3((r * math.cos(2 * math.pi * k / 96), s * y, r * math.sin(2 * math.pi * k / 96))) for y, r in sec] for k in range(96)], 'wheel', closed=False, loop=True)
    face = []
    for r, y in ((Rr - 0.006, 0.080), (0.155, 0.070), (0.140, 0.062), (0.130, 0.058), (0.110, 0.050), (0.0, 0.046)):
        face.append([V3((r * math.cos(2 * math.pi * k / 96), s * y, r * math.sin(2 * math.pi * k / 96))) for k in range(96)])
    m.loft(face, 'wheel')
    nl = G.LUGS
    CK.hub(m, s, 0.046, nl, G.PCD)
    style = G.WHEEL_STYLE
    if style == 'dogdish':
        cap = [(0.130, 0.056), (0.126, 0.068), (0.108, 0.080), (0.075, 0.087), (0.036, 0.090), (0.0, 0.091)]
        m.loft([[V3((r * math.cos(2 * math.pi * k / 72), s * y, r * math.sin(2 * math.pi * k / 72)) ) for k in range(72)] for r, y in cap], 'chrome')
    elif style == 'cover':
        # a full wheel cover: a stamped steel disc with a rim ring and ring of oblong vents
        face2 = [(Rr - 0.004, 0.088), (Rr - 0.020, 0.094), (0.170, 0.088), (0.150, 0.078), (0.120, 0.086), (0.060, 0.090), (0.030, 0.094), (0.0, 0.095)]
        m.loft([[V3((r * math.cos(2 * math.pi * k / 96), s * y, r * math.sin(2 * math.pi * k / 96))) for k in range(96)] for r, y in face2], 'chrome')
        for k in range(20):
            a = 2 * math.pi * (k + 0.5) / 20
            m.rbox(V3((0.150 * math.cos(a), s * 0.087, 0.150 * math.sin(a))), (0.030, 0.006, 0.014), 0.005, 'black',
                   (V3((math.cos(a), 0, math.sin(a))), V3((0, 1, 0)), V3((-math.sin(a), 0, math.cos(a)))))
    else:
        # a styled steel wheel: a bright trim ring, slots and a centre cap
        face2 = [(Rr - 0.004, 0.084), (Rr - 0.016, 0.090), (0.150, 0.080), (0.120, 0.086), (0.050, 0.092), (0.0, 0.094)]
        m.loft([[V3((r * math.cos(2 * math.pi * k / 96), s * y, r * math.sin(2 * math.pi * k / 96))) for k in range(96)] for r, y in face2], 'wheel_body')
        for k in range(10):
            a = 2 * math.pi * (k + 0.5) / 10
            m.rbox(V3((0.115 * math.cos(a), s * 0.0895, 0.115 * math.sin(a))), (0.060, 0.006, 0.026), 0.010, 'black',
                   (V3((math.cos(a), 0, math.sin(a))), V3((0, 1, 0)), V3((-math.sin(a), 0, math.cos(a)))))
        m.cyl(V3((0, s * 0.092, 0)), V3((0, s * 0.100, 0)), 0.045, 'chrome', seg=24, r1=0.040)
    CK.valve_stem(m, s, 0.178, 0.080)
    if front:
        CK.brake_disc(m, s, 0.130, 0.075, 0.030, 0.026)
        CK.caliper(m, s, 0.130, 0.030, 0.026, 200)
    else:
        m.cyl(V3((0, s * 0.03, 0)), V3((0, -s * 0.06, 0)), 0.140, 'drum', seg=48)
        for k in range(24):
            a = 2 * math.pi * k / 24
            m.box(V3((0.142 * math.cos(a), -s * 0.015, 0.142 * math.sin(a))), (0.006, 0.07, 0.008), 'drum',
                  (V3((-math.sin(a), 0, math.cos(a))), V3((0, 1, 0)), V3((math.cos(a), 0, math.sin(a)))))
        m.cyl(V3((0, -s * 0.06, 0)), V3((0, -s * 0.07, 0)), 0.155, 'black', seg=48)
    return m


def build_wheels(root):
    for nm, x, y in (('FL', G.WHEELBASE / 2, G.TRACK_F / 2), ('FR', G.WHEELBASE / 2, -G.TRACK_F / 2), ('RL', -G.WHEELBASE / 2, G.TRACK_R / 2), ('RR', -G.WHEELBASE / 2, -G.TRACK_R / 2)):
        e = empty(f'Wheel_{nm}', V3((x, y, G.ZC)), root)
        wheel_mesh(1 if y > 0 else -1, nm[0] == 'F').finish(f'Wheel_{nm}_mesh', e, sharp=40)


# ---- the interior -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def seat(m, x, y, z, width, back_h=0.62, recline=14.0, kind='cloth', head=True, pleats=5):
    """A seat: the cushion, the back leaning by `recline` degrees, a headrest; piping in vinyl."""
    ex, ey, ez = V3((1, 0, 0)), V3((0, 1, 0)), V3((0, 0, 1))
    CK.cushion(m, V3((x, y, z)), ex, ey, ez, 0.50, width, 0.12, pleats=3, kind=kind, piping='vinyl', crown=0.012)
    t = math.radians(recline)
    bz = V3((math.cos(t), 0, math.sin(t)))
    bx = V3((-math.sin(t), 0, math.cos(t)))
    c = V3((x - 0.24, y, z + 0.06 + back_h / 2 * math.cos(t)))
    CK.cushion(m, c, bx, ey, bz, back_h, width, 0.13, pleats=pleats, kind=kind, piping='vinyl', crown=0.015)
    if head:
        h = c + bx * (back_h / 2 + 0.07) + bz * 0.0
        m.rbox(h, (0.14, min(0.30, width * 0.7), 0.10), 0.03, 'vinyl', (bx, ey, bz))
        for sy in (-0.07, 0.07):
            m.cyl(h - bx * 0.07 + ey * sy, h - bx * 0.16 + ey * sy, 0.006, 'chrome', seg=8)


def steering_wheel(root):
    m = Mesh()
    S = G.STEER
    c = V3(S['c'])
    tilt = math.radians(S.get('tilt', 25))
    ax = V3((-math.cos(tilt), 0, math.sin(tilt)))              # the wheel's axis points back at the driver, tilted up
    ax = V3((-math.cos(tilt), 0, -math.sin(tilt) * -1)).normalized()
    up = V3((0, 0, 1))
    u = ax.cross(up).normalized()
    w = ax.cross(u).normalized()
    r = S.get('r', 0.19)
    ring = [c + (u * math.cos(2 * math.pi * k / 48) + w * math.sin(2 * math.pi * k / 48)) * r for k in range(48)]
    m.tube(ring, 0.0125, 'black', seg=12, loop=True)
    m.cyl(c - ax * 0.01, c + ax * 0.02, 0.05, 'black', seg=24)
    for k in (0, 1, 2):
        a = math.radians(90 + 120 * k + 0)
        d = u * math.cos(a) + w * math.sin(a)
        m.tube([c, c + d * r * 0.5, c + d * r], 0.009, 'black', seg=8)
    m.cyl(c - ax * 0.35, c - ax * 0.02, 0.028, 'black', seg=14)
    m.rbox(c - ax * 0.12 + V3((0, 0, -0.085)), (0.12, 0.10, 0.10), 0.02, 'black')
    return m.finish('SteeringWheel', root, sharp=40)


def build_interior(root):
    m = Mesh()
    Sx = G.SEATS
    zc = Sx['z']
    cab = G.CAB_Y
    yb = cab - 0.12
    ex, ey, ez = V3((1, 0, 0)), V3((0, 1, 0)), V3((0, 0, 1))
    # front seats
    if Sx['front'] == 'bench':
        seat(m, Sx['x'], 0.0, zc, 2 * yb - 0.25, head=False, pleats=9)
        for sy in (0.36, -0.36):
            seat(m, Sx['x'] - 0.02, sy, zc + 0.01, 0.50, back_h=0.60, recline=18.0, pleats=4) if False else None
        for sy in (0.37, -0.37):
            m.rbox(V3((Sx['x'] - 0.34, sy, zc + 0.64)), (0.12, 0.30, 0.10), 0.03, 'vinyl')
    else:
        for sy in (0.37, -0.37):
            seat(m, Sx['x'], sy, zc, 0.50, back_h=0.64)
    if Sx.get('rear'):
        rx, rz = Sx['rear']
        seat(m, rx, 0.0, rz, 2 * yb - 0.12, back_h=0.56, recline=16.0, head=False, pleats=9)
        for sy in (0.36, -0.36):
            m.rbox(V3((rx - 0.20, sy, rz + 0.62)), (0.10, 0.28, 0.09), 0.03, 'vinyl')
    if Sx.get('rear2'):
        rx, rz = Sx['rear2']
        seat(m, rx, 0.0, rz, 2 * yb - 0.12, back_h=0.56, recline=16.0, head=False, pleats=9)
    for (x0, x1, y0, y1, z0, z1) in Sx.get('extra_seats', []):
        m.rbox(V3(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)), (x1 - x0, y1 - y0, z1 - z0), 0.03, 'cloth')
    cg = G.CARGO
    if cg:
        x0, x1, z, y = cg
        m.box(V3(((x0 + x1) / 2, 0, z)), (x1 - x0, 2 * y, 0.02), 'carpet')
        for s in (1, -1):
            m.rbox(V3(((x0 + x1) / 2, s * (y + 0.02), z + 0.14)), (x1 - x0, 0.04, 0.28), 0.01, 'vinyl')
    # the dash: the pad, the binnacle, the centre stack, the glove box, vents
    xd = G.X_COWL - 0.08
    zd = G.WS['z0'] - 0.02 if G.WS else 0.95
    m.rbox(V3((xd - 0.17, 0, zd - 0.10)), (0.40, 2 * (cab - 0.06), 0.20), 0.05, 'dash')
    m.rbox(V3((xd - 0.15, 0, zd - 0.32)), (0.30, 2 * (cab - 0.12), 0.30), 0.03, 'dash')
    bx = xd - 0.05
    m.rbox(V3((bx, 0.37, zd + 0.01)), (0.15, 0.48, 0.17), 0.04, 'dash')
    for k, (dy, r) in enumerate(((0.52, 0.045), (0.40, 0.045), (0.28, 0.045))):
        m.cyl(V3((bx + 0.075, dy, zd - 0.01)), V3((bx + 0.078, dy, zd - 0.01)), r, 'gauge', seg=24)
        m.tube([V3((bx + 0.079, dy + r * 1.02 * math.cos(2 * math.pi * j / 24), zd - 0.01 + r * 1.02 * math.sin(2 * math.pi * j / 24)) ) for j in range(24)], 0.0025, 'chrome', seg=4, loop=True)
        m.box(V3((bx + 0.079, dy, zd - 0.01 + 0.015)), (0.002, 0.003, 0.03), 'plate')
    m.rbox(V3((bx + 0.075, 0.37, zd + 0.045)), (0.004, 0.40, 0.03), 0.002, 'gauge')
    m.rbox(V3((xd - 0.02, 0.0, zd - 0.17)), (0.10, 0.19, 0.26), 0.02, 'radio')
    m.rbox(V3((xd - 0.020, 0.0, zd - 0.115)), (0.104, 0.17, 0.045), 0.006, 'black')
    for k in range(5):
        m.cyl(V3((xd + 0.03, -0.065 + 0.0325 * k, zd - 0.19)), V3((xd + 0.037, -0.065 + 0.0325 * k, zd - 0.19)), 0.009, 'chrome', seg=12)
    m.rbox(V3((xd - 0.02, -0.40, zd - 0.19)), (0.06, 0.36, 0.20), 0.02, 'black')
    for sy in (0.0, 0.7, -0.7):
        if abs(sy) < cab - 0.05:
            for k in range(5):
                m.box(V3((xd - 0.15 + 0.0, sy, zd - 0.005 - 0.006 * k)), (0.004, 0.10, 0.003), 'black')
    # the floor console / shifter, pedals
    sh = G.SHIFTER
    if sh == 'console':
        m.rbox(V3((Sx['x'] + 0.10, 0.0, G.CAB_FLOOR + 0.10)), (0.9, 0.22, 0.22), 0.05, 'dash')
        m.cyl(V3((Sx['x'] + 0.20, 0.0, G.CAB_FLOOR + 0.20)), V3((Sx['x'] + 0.20, 0.0, G.CAB_FLOOR + 0.42)), 0.011, 'chrome', seg=10)
        m.rbox(V3((Sx['x'] + 0.20, 0.0, G.CAB_FLOOR + 0.45)), (0.06, 0.035, 0.07), 0.015, 'black')
    elif sh == 'floor':
        m.cyl(V3((Sx['x'] + 0.28, 0.0, G.CAB_FLOOR + 0.15)), V3((Sx['x'] + 0.30, 0.0, G.CAB_FLOOR + 0.48)), 0.012, 'chrome', seg=10)
        m.cyl(V3((Sx['x'] + 0.30, 0.0, G.CAB_FLOOR + 0.48)), V3((Sx['x'] + 0.31, 0.0, G.CAB_FLOOR + 0.54)), 0.025, 'black', seg=14)
    px = xd - 0.30
    for k, dy in enumerate((0.45, 0.36, 0.28)):
        m.rbox(V3((px, dy, G.CAB_FLOOR + 0.30 - 0.0)), (0.012, 0.05 if k < 2 else 0.12, 0.10), 0.004, 'rubber')
    # rear view mirror and sun visors
    if G.WS is None:
        mx, zr = G.X_COWL - 0.30, 1.2
    else:
        # up under the header: where the glass reaches its top edge, a little inside the cabin
        zr = G.WS['z1'] - 0.07
        xg = G.X_COWL
        while xg > G.X_COWL - 1.2 and G.roof_z(xg) < zr:
            xg -= 0.004
        mx = xg - 0.09
    m.rbox(V3((mx, 0.0, zr - 0.07)), (0.03, 0.24, 0.07), 0.01, 'black')
    m.cyl(V3((mx - 0.005, 0, zr - 0.035)), V3((mx - 0.045, 0, zr - 0.005)), 0.007, 'black', seg=8)
    for sy in (0.37, -0.37):
        m.rbox(V3((mx - 0.10, sy, zr - 0.03)), (0.18, 0.34, 0.012), 0.005, 'vinyl')
    return m.finish('Interior', root, sharp=45)


# ---- dirt, dents ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def dirt_colors(ob, seed=1):
    """Light road dirt as vertex colours (white clean, a warm grey-brown where road spray reaches): lower body, wheel arches and the rear end."""
    bpy.context.view_layer.update()
    me = ob.data
    if me.color_attributes.get('Color') is None:
        me.color_attributes.new('Color', 'BYTE_COLOR', 'CORNER')
    attr = me.color_attributes['Color']
    mw = ob.matrix_world
    import random
    rnd = random.Random(seed)
    ph = [rnd.random() * 6.28 for _ in range(3)]
    vals = []
    for lp in me.loops:
        p = mw @ me.vertices[lp.vertex_index].co
        k = max(0.0, 1.0 - max(p.z - 0.12, 0.0) / 0.42)
        k = k * k
        n = 0.5 + 0.5 * math.sin(p.x * 9 + ph[0]) * math.sin(p.y * 13 + ph[1]) * math.sin(p.z * 7 + ph[2])
        wheel = max(0.0, 1.0 - min(abs(p.x - G.HWB), abs(p.x + G.HWB)) / 0.55) * max(0.0, 1.0 - max(p.z - G.ZC, 0.0) / 0.35)
        d = min(0.40, 0.30 * k * (0.55 + 0.7 * n) + 0.12 * wheel)
        if p.z > 0.58:
            d = 0.0
        vals.append((1 - d * 0.55, 1 - d * 0.65, 1 - d * 0.85, 1.0))
    flat = [c for v in vals for c in v]
    attr.data.foreach_set('color', flat)


def dent(ob, centre, radius, depth, seed=0):
    """Push the vertices of ob (world space) near `centre` inward along the direction to the car's middle, with a crumpled ripple."""
    import random
    rnd = random.Random(seed)
    me = ob.data
    mw = ob.matrix_world
    inv = mw.inverted()
    c = V3(centre)
    ph = rnd.random() * 6.28
    for v in me.vertices:
        p = mw @ v.co
        d = (p - c).length
        if d < radius * 1.6:
            f = math.exp(-(d / radius) ** 2)
            ripple = 0.55 + 0.45 * math.sin(p.x * 40 + p.z * 31 + ph) * math.cos(p.y * 37 + ph)
            toward = (V3((0, 0, 0.6)) - p)
            toward.z *= 0.2
            toward = toward.normalized()
            q = p + toward * depth * f * ripple + V3((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * 0.004 * f
            v.co = inv @ q


def make_damaged(root, seed=7):
    """The wrecked set of the same nodes: crumpled front-left and rear-right quarters, a bent hood and trunk, loose bumpers, scuffed paint."""
    tops = {o.name: o for o in root.children_recursive if o.type == 'MESH'}
    nm = lambda s: [o for n, o in tops.items() if n.startswith(s)]      # noqa: E731
    bpy.context.view_layer.update()
    xn, xt, w = G.X_NOSE, G.X_TAIL, G.W
    hits = [((xn - 0.1, 0.45, 0.75), 0.45, 0.22), ((xn - 0.3, 0.8, 0.75), 0.35, 0.14), ((xt + 0.15, -0.6, 0.85), 0.40, 0.16), ((0.3, w, 0.75), 0.35, 0.07),
            ((-0.9, -w, 0.7), 0.30, 0.06)]
    for k, (c, r, dp) in enumerate(hits):
        for o in nm('Body') + nm('Door_') + nm('Hood') + nm('Trunk') + nm('Tailgate') + nm('Bumper'):
            if o.type == 'MESH' and 'Glass' not in o.name and 'Trim' not in o.name:
                dent(o, c, r, dp, seed + k)
    for o in nm('Bumper_F'):
        o.rotation_euler = (math.radians(4), math.radians(-7), math.radians(5))
        o.location += V3((0.0, 0.01, -0.06))
    for o in nm('Bumper_R'):
        o.rotation_euler = (0.0, math.radians(9), math.radians(-6))
        o.location += V3((0.01, 0.0, -0.05))
    for o in tops.values():
        if o.name.startswith(('Hood',)):
            o.rotation_euler = (0, math.radians(-9), 0)
        if o.name.startswith(('Trunk',)):
            o.rotation_euler = (0, math.radians(7), 0)
        if o.name.startswith(('Door_FL',)) and o.parent == root:
            o.rotation_euler = (0, 0, math.radians(-14))
    for o in tops.values():
        if o.name.startswith(('Body', 'Door_', 'Hood', 'Trunk', 'Tailgate', 'Bumper')):
            dirt_colors(o, seed + 3)


# ---- assemble ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def checkpoint(tag):
    p = SCRATCH / 'work' / f'{G.NAME}_{tag}.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(p), compress=True)
    log('checkpoint', p.name)


def build_car():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _mc.clear()
    _img.clear()
    root = empty(G.ROOT)
    body = build_body(root)
    bvh = bvh_of([body])
    _BVH['body'] = bvh
    glass = build_glass(bvh)
    trim = build_trim(bvh)
    door_inner(trim)
    log('glass, trim')
    checkpoint('s1_body')
    boolean(body, body_cutters(), 'DIFFERENCE')
    log('cuts', len(body.data.polygons))
    retag_cabin(body)
    doors = split_doors(body, root)
    panels = split_panels(body, root)
    CK.roll_edges(body)
    for ob in list(doors.values()) + list(panels.values()):
        CK.roll_edges(ob)
    drop_origin_junk(body)
    smooth(body, 40)
    owners = dict(doors)
    owners.update(panels)
    log('parts', len(body.data.polygons))
    checkpoint('s2_parts')
    finish_parts(glass, 'Glass', root, owners, sharp=60)
    finish_parts(trim, 'Trim', root, owners, sharp=50)
    fr, lamps = build_front_rear(root)
    fr.finish('Ends', root, sharp=40)
    for nm_, lm in zip(('Lamps_Head', 'Lamps_Park', 'Lamps_Tail', 'Lamps_Marker'), lamps):
        lm.finish(nm_, root)
    bumper_mesh(True).finish('Bumper_F', root, sharp=40)
    bumper_mesh(False).finish('Bumper_R', root, sharp=40)
    build_interior(root)
    steering_wheel(root)
    build_engine(root)
    build_under(root)
    build_wheels(root)
    for ob in root.children_recursive:
        if ob.type == 'MESH':
            metres_uv(ob)
    log('details')
    checkpoint('s3_full')
    return root


def inject_variants(path, colors, default_name):
    """Write KHR_materials_variants into the glb: the paint material gets one variant per colour (the body's colour as a material variant, not separate meshes)."""
    import struct
    data = pathlib.Path(path).read_bytes()
    jl, _ = struct.unpack('<II', data[12:20])
    js = json.loads(data[20:20 + jl])
    rest = data[20 + jl:]
    mats = js['materials']
    pi = next(i for i, mm in enumerate(mats) if mm['name'] == 'M_paint')
    new = []
    for nm_, c in colors:
        mm = json.loads(json.dumps(mats[pi]))
        mm['name'] = 'paint_' + nm_
        lc = lin(c)
        mm['pbrMetallicRoughness']['baseColorFactor'] = [lc[0], lc[1], lc[2], 1.0]
        mats.append(mm)
        new.append(len(mats) - 1)
    js.setdefault('extensionsUsed', []).append('KHR_materials_variants')
    js.setdefault('extensions', {})['KHR_materials_variants'] = {'variants': [{'name': n} for n, _ in colors]}
    for me in js['meshes']:
        for pr in me['primitives']:
            if pr.get('material') == pi:
                pr.setdefault('extensions', {})['KHR_materials_variants'] = {'mappings': [{'material': mi, 'variants': [vi]} for vi, mi in enumerate(new)]}
    jb = json.dumps(js, separators=(',', ':')).encode()
    jb += b' ' * ((4 - len(jb) % 4) % 4)
    out = struct.pack('<4sII', b'glTF', 2, 12 + 8 + len(jb) + len(rest)) + struct.pack('<I4s', len(jb), b'JSON') + jb + rest
    pathlib.Path(path).write_bytes(out)


def export(root, path, lod=False):
    bpy.ops.object.select_all(action='DESELECT')
    obs = [root] + list(root.children_recursive)
    mods = []
    if lod:
        for ob in obs:
            if ob.type == 'MESH' and len(ob.data.polygons) > 300:
                md = ob.modifiers.new('lod', 'DECIMATE')
                r = 0.08 if ob.name.startswith(('Underbody', 'Engine')) else (0.45 if ob.name.startswith(('Body', 'Door_', 'Hood', 'Trunk', 'Tailgate', 'Glass')) else 0.2)
                md.ratio = r
                mods.append((ob, md))
    for ob in obs:
        ob.select_set(True)
    path.parent.mkdir(parents=True, exist_ok=True)
    kw = dict(filepath=str(path), export_format='GLB', use_selection=True, export_yup=True, export_apply=True, export_image_format='WEBP', export_materials='EXPORT',
              export_extras=False, export_cameras=False, export_lights=False)
    props = bpy.ops.export_scene.gltf.get_rna_type().properties
    if 'export_vertex_color' in props:
        kw['export_vertex_color'] = 'ACTIVE'
    elif 'export_active_vertex_color_when_no_material' in props:
        kw['export_active_vertex_color_when_no_material'] = True
    bpy.ops.export_scene.gltf(**kw)
    tris = 0
    for o in obs:
        if o.type == 'MESH':
            dg = bpy.context.evaluated_depsgraph_get()
            me = o.evaluated_get(dg).to_mesh()
            me.calc_loop_triangles()
            tris += len(me.loop_triangles)
            o.evaluated_get(dg).to_mesh_clear()
    for ob, md in mods:
        ob.modifiers.remove(md)
    inject_variants(path, G.COLORS, G.COLORS[0][0])
    log('wrote', path, 'triangles', tris)
    return tris


def run(geom):
    use(geom)
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    arg = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d  # noqa: E731
    out = pathlib.Path(arg('--out'))
    if arg('--from-blend'):
        bpy.ops.wm.open_mainfile(filepath=arg('--from-blend'))
        root = bpy.data.objects[G.ROOT]
        _mc.clear()
    else:
        root = build_car()
    bpy.context.view_layer.update()
    for ob in root.children_recursive:
        if ob.type == 'MESH':
            drop_origin_junk(ob)
    for ob in root.children_recursive:
        if ob.type == 'MESH' and ob.name.startswith(('Body', 'Door_', 'Hood', 'Trunk', 'Tailgate', 'Bumper')) and 'Glass' not in ob.name and 'Trim' not in ob.name:
            dirt_colors(ob, 5)
    bpy.ops.wm.save_as_mainfile(filepath=str(SCRATCH / 'work' / f'{G.NAME}_final.blend'), compress=True)
    t1 = export(root, out)
    t2 = export(root, pathlib.Path(arg('--lod1')), lod=True)
    log('triangles full', t1, 'lod1', t2)
    if arg('--damaged'):
        make_damaged(root)
        export(root, pathlib.Path(arg('--damaged')))
        bpy.ops.wm.save_as_mainfile(filepath=str(SCRATCH / 'work' / f'{G.NAME}_damaged.blend'), compress=True)
