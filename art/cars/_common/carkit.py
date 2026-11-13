# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Detailed parts shared by the car models (runs inside Blender 4.2; imported by build_crownvic.py and examples/corvette-c4/blender/build_c4.py).

Everything adds geometry to a build_crownvic.Mesh in the model's metres: tyres with a real tread and raised sidewall lettering, wheels' hubs and studs, vented brake discs with calipers,
lamps (a paraboloid reflector, a bulb, a fluted lens), lettering as solid text, coil springs, dampers, wiper arms and blades, seats with pleats and piping, and planar UVs for decals.
"""
import math

import bmesh
import bpy
from mathutils import Vector

V3 = Vector
FONTS = 'C:/Windows/Fonts/'
_fonts = {}


# ---- solid text --------------------------------------------------------------------------------------------------------------------------------------------------------------------
def text_geometry(text, font='arialbd.ttf', spacing=1.0):
    """The text as a closed solid: vertices (x, y, z) with the capitals about 0.72 tall (font size 1), centred on x, baseline at y = 0, z in [-0.5, 0.5]; and faces."""
    if font not in _fonts:
        _fonts[font] = bpy.data.fonts.load(FONTS + font)
    cu = bpy.data.curves.new('txt', 'FONT')
    cu.body = text
    cu.font = _fonts[font]
    cu.size = 1.0
    cu.extrude = 0.5
    cu.align_x = 'CENTER'
    cu.space_character = spacing
    cu.resolution_u = 4
    ob = bpy.data.objects.new('txt', cu)
    bpy.context.scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = ob.evaluated_get(dg).to_mesh()
    verts = [v.co.copy() for v in me.vertices]
    faces = [tuple(p.vertices) for p in me.polygons]
    ob.evaluated_get(dg).to_mesh_clear()
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    return verts, faces


def add_text(m, text, kind, place, font='arialbd.ttf', spacing=1.0):
    """Add solid text; place(x, y, z) maps the text's own coordinates (see text_geometry) to the model."""
    verts, faces = text_geometry(text, font, spacing)
    mi = m.mi(kind)
    vs = [m.bm.verts.new(place(v.x, v.y, v.z)) for v in verts]
    for f in faces:
        try:
            nf = m.bm.faces.new([vs[i] for i in f])
            nf.material_index = mi
        except ValueError:
            pass


def text_on_plane(m, text, kind, origin, ex, ey, ez, height, depth, font='arialbd.ttf', spacing=1.0):
    """Text standing on a plane: ex along the line, ey up the letters, ez out of the plane; `height` the capitals' height, `depth` how far they stand out."""
    k = height / 0.72
    add_text(m, text, kind, lambda x, y, z: V3(origin) + ex * (x * k) + ey * (y * k) + ez * ((z + 0.5) * depth), font, spacing)


# ---- tyres and wheels ----------------------------------------------------------------------------------------------------------------------------------------------------------------
def tyre(m, s, R, Rr, W, tread, lettering=(), n=360, kind='tyre'):
    """A radial tyre about the Y axis (outer face toward s*Y), built about its centre.

    R outer radius, Rr the rim's radius, W the section width; tread(u, v) -> depth (m) of the tread at u in [0, 1) round the tyre and v in [-1, 1] across it (0 where rubber stands up);
    lettering: (text, angle_deg, radius_fraction_of_sidewall, cap_height) items raised 1 mm on the outer sidewall."""
    hw = W / 2
    sw = R - Rr
    # the section: bead at the rim, the sidewall's bulge, a rounded shoulder, the tread across
    side = [(hw - 0.024, Rr + 0.006), (hw - 0.014, Rr + 0.018), (hw - 0.004, Rr + 0.25 * sw), (hw, Rr + 0.50 * sw), (hw - 0.003, Rr + 0.72 * sw), (hw - 0.010, Rr + 0.86 * sw),
            (hw - 0.020, R - 0.012), (hw - 0.032, R - 0.003)]
    nv = 36
    across = [(-hw + 0.036 + (2 * hw - 0.072) * j / nv) for j in range(nv + 1)]
    prof = [(-y, r, None) for y, r in side] + [(y, R, y / (hw - 0.036)) for y in across] + [(y, r, None) for y, r in reversed(side)]
    rings = []
    for i in range(n):
        a = 2 * math.pi * i / n
        ca, sa = math.cos(a), math.sin(a)
        ring = []
        for y, r, v in prof:
            rr = r - (tread(i / n, v) if v is not None else 0.0)
            ring.append(V3((rr * ca, s * y, rr * sa)))
        rings.append(ring)
    m.loft(rings, kind, closed=False, loop=True)

    def side_y(r):
        for (y0, r0), (y1, r1) in zip(side, side[1:]):
            if r0 <= r <= r1:
                return y0 + (y1 - y0) * (r - r0) / (r1 - r0)
        return hw - 0.01

    for text, ang, frac, cap in lettering:
        rt = Rr + frac * sw
        k = cap / 0.72
        a0 = math.radians(ang)

        def place(x, y, z, rt=rt, k=k, a0=a0):
            r = rt + y * k
            a = a0 - x * k / rt
            return V3((r * math.cos(a), s * (side_y(r) + 0.0004 + (z + 0.5) * 0.0010), r * math.sin(a)))
        add_text(m, text, kind, place)


def tread_allseason(u, v, n_pitch=64):
    """A road tread: four circumferential grooves, lateral grooves between blocks, sipes in the blocks (depths in metres)."""
    av = abs(v)
    for g in (0.18, 0.58):
        if abs(av - g) < 0.045:
            return 0.008
    k = u * n_pitch
    fr = k - math.floor(k)
    shift = 0.25 if av > 0.58 else (0.5 if av > 0.18 else 0.0)
    f2 = (fr + shift) % 1.0
    if av > 0.62 and f2 < 0.12:
        return 0.007
    if 0.22 < av < 0.54 and f2 < 0.08:
        return 0.006
    if av < 0.14 and abs(f2 - 0.5) < 0.05:
        return 0.003
    if ((k * 2 + v * 3) % 1.0) < 0.05:
        return 0.0015
    return 0.0


def tread_gatorback(u, v, n_pitch=72):
    """The Goodyear 'Gatorback' look: one wide centre groove, V-shaped lateral grooves pointing the way the tyre turns (unidirectional), a closed shoulder."""
    av = abs(v)
    if av < 0.05:
        return 0.008
    if abs(av - 0.62) < 0.035:
        return 0.007
    k = (u + 0.10 * av) * n_pitch
    fr = k - math.floor(k)
    if av < 0.62 and fr < 0.14:
        return 0.007
    if av > 0.66 and fr < 0.06:
        return 0.004
    return 0.0


def brake_disc(m, s, r_out, r_in, y_face, thick, vanes=36, hat_r=None, kind='steel', vane_kind='black'):
    """A vented disc about Y: two plates with radial vanes between them, the hat that bolts to the hub. y_face: the disc's outer face (toward s*Y)."""
    yo, yi = s * y_face, s * (y_face - thick)
    pl = thick * 0.32
    for y0, y1 in ((yo, yo - s * pl), (yi + s * pl, yi)):
        _annulus(m, r_in, r_out, y0, y1, kind)
    for k in range(vanes):
        a = 2 * math.pi * k / vanes
        c = V3(((r_in + r_out) / 2 * math.cos(a), (yo + yi) / 2, (r_in + r_out) / 2 * math.sin(a)))
        m.box(c, (0.006, thick - 2 * pl, r_out - r_in), vane_kind, (V3((-math.sin(a), 0, math.cos(a))), V3((0, 1, 0)), V3((math.cos(a), 0, math.sin(a)))))
    hr = hat_r or r_in * 0.95
    m.cyl(V3((0, yo, 0)), V3((0, yo + s * 0.03, 0)), hr, kind, seg=40)


def _annulus(m, r0, r1, y0, y1, kind, n=64):
    rings = []
    for r, y in ((r0, y0), (r1, y0), (r1, y1), (r0, y1)):
        rings.append([V3((r * math.cos(2 * math.pi * k / n), y, r * math.sin(2 * math.pi * k / n))) for k in range(n)])
    # a closed torus-like solid: the four circles joined round
    vs = [[m.bm.verts.new(p) for p in r] for r in rings]
    mi = m.mi(kind)
    for a in range(4):
        b = (a + 1) % 4
        for k in range(n):
            try:
                f = m.bm.faces.new((vs[a][k], vs[a][(k + 1) % n], vs[b][(k + 1) % n], vs[b][k]))
                f.material_index = mi
            except ValueError:
                pass


def caliper(m, s, r_disc, y_face, thick, angle_deg, kind='caliper'):
    """A floating caliper straddling the disc's edge at angle_deg (0 = forward, 90 = up), with its bracket and two bleed nipples."""
    a = math.radians(angle_deg)
    rad = V3((math.cos(a), 0, math.sin(a)))
    tan = V3((-math.sin(a), 0, math.cos(a)))
    c = rad * (r_disc - 0.02) + V3((0, s * (y_face - thick / 2), 0))
    ax = (tan, V3((0, 1, 0)), rad)
    m.rbox(c + V3((0, s * (thick / 2 + 0.018), 0)), (0.13, 0.03, 0.07), 0.012, kind, ax)
    m.rbox(c - V3((0, s * (thick / 2 + 0.022), 0)), (0.15, 0.04, 0.08), 0.014, kind, ax)
    m.rbox(c + rad * 0.045, (0.14, thick + 0.07, 0.025), 0.01, kind, ax)
    for d in (-0.04, 0.04):
        p = c + tan * d + rad * 0.058 - V3((0, s * (thick / 2 + 0.03), 0))
        m.cyl(p, p + rad * 0.012, 0.004, 'steel', seg=6)


def hub(m, s, y, n_studs, pcd_r, stud_r=0.0065, nut=True, kind='steel'):
    """Wheel studs with conical nuts on a pitch circle in the plane y (toward s*Y)."""
    for k in range(n_studs):
        a = 2 * math.pi * k / n_studs + math.pi / 2
        c = V3((pcd_r * math.cos(a), s * y, pcd_r * math.sin(a)))
        if nut:
            m.cyl(c, c + V3((0, s * 0.014, 0)), 0.0115, kind, seg=6)
            m.cyl(c + V3((0, s * 0.014, 0)), c + V3((0, s * 0.020, 0)), 0.0105, kind, seg=12, r1=0.006)
        m.cyl(c + V3((0, s * 0.012, 0)), c + V3((0, s * 0.026, 0)), stud_r * 0.8, kind, seg=8)


def valve_stem(m, s, r, y, ang_deg=-60.0):
    a = math.radians(ang_deg)
    c = V3((r * math.cos(a), s * y, r * math.sin(a)))
    d = V3((math.cos(a) * 0.3, s * 1.0, math.sin(a) * 0.3)).normalized()
    m.cyl(c, c + d * 0.022, 0.0045, 'rubber', seg=8, r1=0.0035)
    m.cyl(c + d * 0.022, c + d * 0.032, 0.0040, 'chrome', seg=8)


# ---- lamps -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def reflector(m, c, ax, up, w, h, depth, kind='reflector', n=14):
    """A paraboloid reflector opening along ax (its rim w x h at c, its vertex `depth` behind)."""
    ax, up = V3(ax).normalized(), V3(up).normalized()
    rt = ax.cross(up).normalized()
    rows = []
    for j in range(n + 1):
        v = -1 + 2 * j / n
        row = []
        for i in range(n + 1):
            u = -1 + 2 * i / n
            rr = min(1.0, (u * u + v * v) / 2 + 0.5 * max(u * u, v * v))
            row.append(V3(c) + rt * (u * w / 2) + up * (v * h / 2) - ax * (depth * (1 - rr)))
        rows.append(row)
    m.grid(rows, kind)


def bulb(m, c, ax, r=0.009, kind='bulb'):
    ax = V3(ax).normalized()
    m.cyl(V3(c) - ax * 0.018, V3(c), 0.006, 'steel', seg=10)
    m.tube([V3(c) + ax * (r * (1 - math.cos(math.pi * k / 8))) for k in range(9)], [max(1e-4, r * math.sin(math.pi * k / 8)) for k in range(9)], kind, seg=12)


def fluted_lens(m, c, ax, up, w, h, depth, cols, rows, kind, pattern='flutes', bulge=0.004):
    """A lens w x h centred at c facing ax, `depth` thick: its outer face carries vertical flutes ('flutes'), a grid of small domes ('cells') or horizontal ribs ('ribs')."""
    ax, up = V3(ax).normalized(), V3(up).normalized()
    rt = ax.cross(up).normalized()
    nu, nv = cols * 6, rows * 6
    front = []
    for j in range(nv + 1):
        v = -1 + 2 * j / nv
        row = []
        for i in range(nu + 1):
            u = -1 + 2 * i / nu
            if pattern == 'flutes':
                d = 0.5 + 0.5 * math.cos(2 * math.pi * (i % 6) / 6)
            elif pattern == 'ribs':
                d = 0.5 + 0.5 * math.cos(2 * math.pi * (j % 6) / 6)
            else:
                d = (0.5 + 0.5 * math.cos(2 * math.pi * (i % 6) / 6)) * (0.5 + 0.5 * math.cos(2 * math.pi * (j % 6) / 6))
            dome = bulge * (1 - 0.5 * (u * u + v * v))
            row.append(V3(c) + rt * (u * w / 2) + up * (v * h / 2) + ax * (dome + 0.0012 * d))
        front.append(row)
    m.grid(front, kind)
    back = [[p - ax * depth for p in r] for r in front]
    m.grid([list(reversed(r)) for r in back], kind)
    edge_f = front[0] + [r[-1] for r in front[1:]] + list(reversed(front[-1][:-1])) + [r[0] for r in reversed(front[1:-1])]
    edge_b = [p - ax * depth for p in edge_f]
    m.loft([edge_f, edge_b], kind, loop=False)


# ---- suspension, wipers ----------------------------------------------------------------------------------------------------------------------------------------------------------------
def coil_spring(m, p0, p1, r_coil, r_wire, turns, kind='spring'):
    p0, p1 = V3(p0), V3(p1)
    ax = (p1 - p0)
    L = ax.length
    ax.normalize()
    up = V3((1, 0, 0)) if abs(ax.x) < 0.9 else V3((0, 1, 0))
    u = ax.cross(up).normalized()
    w = ax.cross(u).normalized()
    n = int(turns * 20)
    path = [p0 + ax * (L * k / n) + (u * math.cos(2 * math.pi * turns * k / n) + w * math.sin(2 * math.pi * turns * k / n)) * r_coil for k in range(n + 1)]
    m.tube(path, r_wire, kind, seg=8)


def damper(m, p0, p1, r_body=0.024, r_rod=0.008, kind='black'):
    p0, p1 = V3(p0), V3(p1)
    mid = p0.lerp(p1, 0.55)
    m.cyl(p0, mid, r_body, kind, seg=16)
    m.cyl(mid, p1, r_rod, 'chrome', seg=10)
    for p in (p0, p1):
        m.cyl(p - V3((0, 0.02, 0)), p + V3((0, 0.02, 0)), 0.014, 'rubber', seg=12)


def wiper(m, pivot, tip, up, blade_len, kind='black'):
    """A wiper: the arm from its pivot cap to the tip, the blade with its spine and yokes, lying along the glass (`up` the glass's normal)."""
    pivot, tip, up = V3(pivot), V3(tip), V3(up).normalized()
    m.cyl(pivot, pivot + up * 0.025, 0.017, kind, seg=14)
    arm = (tip - pivot)
    m.tube([pivot + up * 0.022, pivot + arm * 0.15 + up * 0.03, tip + up * 0.016], 0.006, kind, seg=6)
    d = arm.cross(up).normalized()
    a, b = tip - d * blade_len / 2, tip + d * blade_len / 2
    m.rbox((a + b) / 2 + up * 0.009, ((b - a).length, 0.010, 0.010), 0.002, kind, (d, d.cross(up).normalized(), up))
    m.rbox((a + b) / 2 + up * 0.003, ((b - a).length, 0.006, 0.006), 0.002, 'rubber', (d, d.cross(up).normalized(), up))
    for t in (0.2, 0.5, 0.8):
        p = a.lerp(b, t) + up * 0.016
        m.rbox(p, (0.05, 0.008, 0.008), 0.002, kind, (d, d.cross(up).normalized(), up))


# ---- seats -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def cushion(m, c, ex, ey, ez, lx, ly, lz, pleats=6, kind='interior', piping='interior', crown=0.012):
    """A seat cushion or back: a padded block with rounded edges, `pleats` sewn channels across ey (lengthwise along ex), piping round its face."""
    c, ex, ey, ez = V3(c), V3(ex).normalized(), V3(ey).normalized(), V3(ez).normalized()
    nu, nv = 40, 8 * pleats
    rows = []
    for j in range(nv + 1):
        v = -1 + 2 * j / nv
        row = []
        for i in range(nu + 1):
            u = -1 + 2 * i / nu
            ph = (j % 8) / 8
            dip = 0.0045 * max(0.0, math.cos(2 * math.pi * ph)) ** 8          # a sewn channel every 8 rows
            edge = min(1.0, (1 - abs(u)) * 6, (1 - abs(v)) * 6)
            hz = lz / 2 + crown * (1 - u * u) * (1 - v * v) - dip * edge - 0.012 * (1 - edge) ** 2
            row.append(c + ex * (u * lx / 2) + ey * (v * ly / 2) + ez * hz)
        rows.append(row)
    m.grid(rows, kind)
    # the sides and the bottom: a rounded box under the sewn top
    m.rbox(c - ez * 0.006, (lx, ly, lz - 0.012), min(0.03, lz * 0.35), kind, (ex, ey, ez))
    edge = rows[0] + [r[-1] for r in rows[1:]] + list(reversed(rows[-1][:-1])) + [r[0] for r in reversed(rows[1:-1])]
    m.tube(edge, 0.0035, piping, seg=5, loop=True)


# ---- UVs -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def planar_uv(ob, kind, axes='xy', flip_u=False, flip_v=False):
    """UVs for the faces of one material: the bounds of those faces in two axes mapped to [0, 1] (a picture over its patch)."""
    me = ob.data
    idx = [i for i, mm in enumerate(me.materials) if mm.name == 'M_' + kind]
    if not idx:
        return
    bm = bmesh.new()
    bm.from_mesh(me)
    uvl = bm.loops.layers.uv.verify()
    a0, a1 = ('xyz'.index(axes[0]), 'xyz'.index(axes[1]))
    fs = [f for f in bm.faces if f.material_index == idx[0]]
    if fs:
        vs = [v.co for f in fs for v in f.verts]
        lo = [min(v[a] for v in vs) for a in (a0, a1)]
        hi = [max(v[a] for v in vs) for a in (a0, a1)]
        for f in fs:
            for lp in f.loops:
                u = (lp.vert.co[a0] - lo[0]) / max(hi[0] - lo[0], 1e-6)
                v = (lp.vert.co[a1] - lo[1]) / max(hi[1] - lo[1], 1e-6)
                lp[uvl].uv = (1 - u if flip_u else u, 1 - v if flip_v else v)
    bm.to_mesh(me)
    bm.free()


def roll_edges(ob, width=0.0018, angle=40.0):
    """Round every sharp edge left by the cuts (gaps, openings, arch lips, caps) to a rolled radius, as pressed sheet and moulded panels have.
    The bevel leaves the large concave n-gons (the lofted body's end caps) folded over themselves, with a wrong normal: the game culled them (the sedan's tail panel between
    the lamps was gone). They are cut into triangles after the bevel: each triangle keeps the loop's winding, so it faces out (ear clipping keeps a folded outline whole;
    no recalculation of the normals: on the wagon it turned whole fenders inward)."""
    md = ob.modifiers.new('roll', 'BEVEL')
    md.width = width
    md.segments = 3
    md.limit_method = 'ANGLE'
    md.angle_limit = math.radians(angle)
    md.use_clamp_overlap = True
    md.miter_outer = 'MITER_ARC'
    with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
        bpy.ops.object.modifier_apply(modifier=md.name)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    ng = [f for f in bm.faces if len(f.verts) > 4]
    if ng:
        bmesh.ops.triangulate(bm, faces=ng, quad_method='BEAUTY', ngon_method='EAR_CLIP')
        bm.to_mesh(ob.data)
    bm.free()


def round_lamp(m, c, ax, r, depth, lens_kind, body_kind='chrome', rings=8, n=40):
    """A round lamp facing ax at c: a housing `depth` deep, a paraboloid reflector, a bulb, a lens of concentric rings in a rim."""
    c, ax = V3(c), V3(ax).normalized()
    up = V3((0, 0, 1)) if abs(ax.z) < 0.9 else V3((1, 0, 0))
    u = ax.cross(up).normalized()
    w = ax.cross(u).normalized()
    circ = lambda rr, k: (u * math.cos(2 * math.pi * k / n) + w * math.sin(2 * math.pi * k / n)) * rr    # noqa: E731
    m.loft([[c - ax * d + circ(rr, k) for k in range(n)] for d, rr in ((0.0, r * 1.06), (depth * 0.6, r * 1.04), (depth, r * 0.75), (depth * 1.15, r * 0.35))], body_kind, caps=True)
    m.loft([[c - ax * (0.002 + depth * 0.8 * (1 - (j / 9) ** 2)) + circ(max(r * j / 9, 1e-4), k) for k in range(n)] for j in range(10)], 'reflector')
    bulb(m, c - ax * depth * 0.55, ax, r * 0.18, 'bulb')
    m.loft([[c + ax * (0.004 * (1 - (j / (2 * rings)) ** 2) + 0.0012 * (j % 2)) + circ(max(r * (1 - j / (2 * rings)), 1e-4), k) for k in range(n)] for j in range(2 * rings + 1)],
           lens_kind)
    m.tube([c + ax * 0.002 + circ(r * 1.03, k) for k in range(n)], r * 0.06, body_kind, seg=8, loop=True)


# ---- glazing and trim strips -------------------------------------------------------------------------------------------------------------------------------------------------------------
def grid_normals(rows, toward=None):
    """Per-point unit normals of a grid of points (rows x cols), flipped to point toward `toward` (a direction) when given."""
    nr, nc = len(rows), len(rows[0])
    out = []
    for j in range(nr):
        row = []
        for i in range(nc):
            du = rows[j][min(i + 1, nc - 1)] - rows[j][max(i - 1, 0)]
            dv = rows[min(j + 1, nr - 1)][i] - rows[max(j - 1, 0)][i]
            n = du.cross(dv)
            n = n.normalized() if n.length > 1e-9 else V3((0, 0, 1))
            if toward is not None and n.dot(V3(toward)) < 0:
                n = -n
            row.append(n)
        out.append(row)
    return out


def border(rows):
    """The edge loop of a grid, in order round it."""
    nr, nc = len(rows), len(rows[0])
    return ([rows[0][i] for i in range(nc)] + [rows[j][nc - 1] for j in range(1, nr)] + [rows[nr - 1][i] for i in range(nc - 2, -1, -1)]
            + [rows[j][0] for j in range(nr - 2, 0, -1)])


def pane(m, rows, thick, toward, kind='glass'):
    """A sheet of glass: the grid `rows` is its outer face; the inner face `thick` behind it along the normals; the edge closed. toward: roughly the outward direction."""
    ns = grid_normals(rows, toward)
    inner = [[p - n * thick for p, n in zip(r, nr)] for r, nr in zip(rows, ns)]
    m.grid(rows, kind)
    m.grid([list(reversed(r)) for r in inner], kind)
    m.loft([border(rows), border(inner)], kind, loop=False)
    return ns


def strip(m, pts, nrms, width, thick, kind, loop=False, lift=0.0):
    """A flat moulding along a path lying on a surface (nrms: the surface's normals at the points): a rounded-top bar `width` wide and `thick` high."""
    n = len(pts)
    hw = width / 2
    prof = [(-hw, 0.0), (hw, 0.0), (hw, thick * 0.55), (hw - thick * 0.45, thick), (-hw + thick * 0.45, thick), (-hw, thick * 0.55)]
    rings = []
    for i, p in enumerate(pts):
        a = pts[(i + 1) % n] if loop else pts[min(i + 1, n - 1)]
        b = pts[(i - 1) % n] if loop else pts[max(i - 1, 0)]
        t = (a - b).normalized()
        nn = V3(nrms[i]).normalized()
        nn = (nn - t * nn.dot(t)).normalized()
        o = t.cross(nn).normalized()
        rings.append([p + nn * (lift + v) + o * u for u, v in prof])
    m.loft(rings, kind, caps=not loop, loop=loop)


def seal(m, rows, ns, width=0.016, thick=0.005, kind='seal'):
    """A rubber gasket round a pane's edge: a flat strip over the outer face's border, a quarter on the glass, the rest beyond it."""
    bo = border(rows)
    bn = border(ns)
    c = sum(bo, V3()) / len(bo)
    pts = []
    for p, nn in zip(bo, bn):
        o = (p - c)
        o = (o - nn * o.dot(nn)).normalized()
        pts.append(p + o * (width * 0.25))
    strip(m, pts, bn, width, thick, kind, loop=True)


# ---- wipers parked in tandem -------------------------------------------------------------------------------------------------------------------------------------------------------------------
def wiper_parked(m, pivot, along, glass_n, arm_len, blade_len, kind='black'):
    """A parked wiper: the pivot's cap, a flat tapered arm along the glass's foot (`along`, in the glass's plane), the blade parallel to it with its spine, three yokes and the
    rubber. Two of them with the same `along` and lengths are a tandem pair, parked parallel."""
    p0, d, n = V3(pivot), V3(along).normalized(), V3(glass_n).normalized()
    d = (d - n * d.dot(n)).normalized()
    v = n.cross(d).normalized()
    if v.z < 0:
        v = -v
    m.cyl(p0 - n * 0.01, p0 + n * 0.022, 0.018, kind, seg=16)
    m.cyl(p0 + n * 0.022, p0 + n * 0.028, 0.012, kind, seg=12)
    ax = (d, v, n)
    tip = p0 + d * arm_len + v * 0.012 + n * 0.022
    m.rbox(p0 + d * 0.035 + n * 0.024, (0.07, 0.022, 0.012), 0.004, kind, ax)
    m.rbox(p0.lerp(tip, 0.55) + n * 0.002, (arm_len * 0.85, 0.012, 0.006), 0.002, kind, ax)
    m.rbox(tip - d * 0.02, (0.05, 0.010, 0.010), 0.003, kind, ax)
    bc = tip - d * (blade_len * 0.45) + v * 0.012 - n * 0.008
    m.rbox(bc + n * 0.006, (blade_len, 0.009, 0.004), 0.0015, kind, ax)
    for t in (-0.36, 0.0, 0.36):
        m.rbox(bc + d * (blade_len * t) + n * 0.012, (blade_len * 0.26, 0.010, 0.006), 0.002, kind, ax)
    m.rbox(bc + n * 0.016, (0.04, 0.012, 0.010), 0.003, kind, ax)
    m.rbox(bc, (blade_len * 0.99, 0.004, 0.008), 0.0015, 'rubber', ax)


# ---- emergency lights -------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def beacon(m, r=0.085, h=0.115, lens_kind='lens_blue', n=64):
    """A rotating beacon about the local Z axis, its foot at the origin: a stepped chrome base with four screws and a gasket, a blue dome of vertical Fresnel ribs with a ribbed
    crown (a 3 mm shell), and inside the turning pair of paraboloid reflectors on their spindle, the lamp in its socket, the motor's can and the drive ring."""
    m.cyl(V3((0, 0, 0)), V3((0, 0, 0.010)), r + 0.010, 'chrome', seg=n)
    m.cyl(V3((0, 0, 0.010)), V3((0, 0, 0.042)), r + 0.004, 'chrome', seg=n, r1=r + 0.002)
    for k in range(4):
        a = 2 * math.pi * k / 4 + math.pi / 4
        c = V3(((r + 0.004) * math.cos(a), (r + 0.004) * math.sin(a), 0.026))
        m.cyl(c, c + V3((math.cos(a), math.sin(a), 0)) * 0.004, 0.005, 'steel', seg=10)
    m.cyl(V3((0, 0, 0.042)), V3((0, 0, 0.047)), r + 0.003, 'rubber', seg=n)
    z0 = 0.046

    def shell(off, ribs):
        rings = []
        nz = 20
        for j in range(nz + 1):
            t = j / nz
            if t < 0.72:
                z = z0 + (h * 0.72) * (t / 0.72)
                row = []
                for k in range(n):
                    a = 2 * math.pi * k / n
                    rr = r - off + (0.0022 * abs(math.cos(n / 2 * a)) if ribs else 0.0)
                    row.append(V3((rr * math.cos(a), rr * math.sin(a), z)))
            else:
                q = (t - 0.72) / 0.28
                ang = q * math.pi / 2
                rr = max((r - off) * math.cos(ang * 0.98), 1e-4)
                z = z0 + h * 0.72 + (h * 0.28 - off) * math.sin(ang) + (0.0012 * math.cos(12 * q * math.pi) if ribs else 0.0)
                row = [V3((rr * math.cos(2 * math.pi * k / n), rr * math.sin(2 * math.pi * k / n), z)) for k in range(n)]
            rings.append(row)
        return rings
    outer, inner = shell(0.0, True), shell(0.003, False)
    m.loft(outer, lens_kind)
    m.loft([list(reversed(r)) for r in inner], lens_kind)
    m.loft([outer[0], inner[0]], lens_kind)
    m.cyl(V3((0, 0, z0)), V3((0, 0, z0 + 0.030)), 0.032, 'black', seg=24)
    m.cyl(V3((0, 0, z0 + 0.030)), V3((0, 0, z0 + 0.036)), 0.045, 'steel', seg=32)
    m.cyl(V3((0, 0, z0 + 0.036)), V3((0, 0, z0 + 0.105)), 0.004, 'steel', seg=8)
    for d in (1, -1):
        reflector(m, V3((d * 0.006, 0, z0 + 0.072)), (d, 0, 0), (0, 0, 1), 0.105, 0.072, 0.038, 'reflector', n=14)
    m.cyl(V3((0, 0, z0 + 0.036)), V3((0, 0, z0 + 0.052)), 0.010, 'black', seg=12)
    bulb(m, V3((0, 0, z0 + 0.060)), (0, 0, 1), 0.011, 'bulb')


def siren_speaker(m, c, ax, r_mouth=0.125, depth=0.17, kind='chrome'):
    """A round siren speaker facing ax: the spun bell from the driver's throat to a rolled lip, a grille of horizontal bars across the mouth, the phase plug, the driver's can,
    the U-yoke it hangs in with its two bolts."""
    c, ax = V3(c), V3(ax).normalized()
    up = V3((0, 0, 1))
    u = ax.cross(up).normalized()
    nn = 48
    prof = [(-depth, 0.050), (-depth * 0.75, 0.060), (-depth * 0.5, 0.078), (-depth * 0.25, 0.100), (-0.02, 0.118), (0.0, r_mouth)]
    rings = [[c + ax * x + (u * math.cos(2 * math.pi * k / nn) + up * math.sin(2 * math.pi * k / nn)) * rr for k in range(nn)] for x, rr in prof]
    m.loft(rings, kind)
    m.loft([[p - ax * 0.002 for p in r] for r in reversed(rings)], 'black')
    m.tube([c + (u * math.cos(2 * math.pi * k / nn) + up * math.sin(2 * math.pi * k / nn)) * (r_mouth + 0.004) for k in range(nn)], 0.006, kind, seg=10, loop=True)
    for k in range(11):
        zz = -r_mouth * 0.9 + 1.8 * r_mouth * k / 10
        hw = math.sqrt(max(0.0, (r_mouth * 0.98) ** 2 - zz ** 2))
        if hw > 0.01:
            m.rbox(c - ax * 0.004 + up * zz, (0.004, 2 * hw, 0.006), 0.0015, kind, (ax, u, up))
    m.cyl(c - ax * 0.10, c - ax * 0.03, 0.035, 'black', seg=24, r1=0.004)
    m.cyl(c - ax * depth, c - ax * (depth + 0.07), 0.065, 'black', seg=32)
    m.cyl(c - ax * (depth + 0.07), c - ax * (depth + 0.075), 0.058, 'steel', seg=32)
    for sgn in (1, -1):
        p = c - ax * (depth * 0.6) + u * sgn * 0.085
        m.rbox(p - up * 0.05, (0.03, 0.008, 0.11), 0.003, 'steel', (ax, u, up))
        m.cyl(p - u * sgn * 0.012, p + u * sgn * 0.004, 0.009, 'steel', seg=6)
    m.rbox(c - ax * (depth * 0.6) - up * 0.105, (0.03, 0.18, 0.008), 0.003, 'steel', (ax, u, up))
