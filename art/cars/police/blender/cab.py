# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""The cab of the 1987 police LTD Crown Victoria, worked out for a first-person camera (replaces build_interior of the library model; see ../SOURCES.md for what each part is based on).

Laid out after the owner's reference photographs of a 1983-87 LTD Crown Victoria's cab: a black padded top with a rounded edge over the instruments, a walnut strip with thin bright
edging across the whole width, a square ribbed vent left of the wheel, a wide ribbon speedometer under glass in a black frame, vents right of it, radio and climate block in a wooden
centre console, a long wooden panel and a vent before the passenger, black plastic below; a large thin-rimmed four-spoke wheel with a big rectangular pad; a grey velour bench.

Nodes added under the car root (existing nodes keep their names):
  Interior            seats, belts, pedals, visors, dome lamp
  Dash                instrument panel, cluster, vents, radio, climate, glove box, column shroud, selector lever, stalk
  SteeringWheel       rim, four spokes, the pad; origin at the hub on the column axis, turns about AXIS
  Equipment           the police radio rack, siren console, microphone, scanner
  PillarTrim          thin covers of the A, B, C pillars between the glass edges
  Mirror_Inner        the inside mirror's frame and stalk; Mirror_Inner_Glass its flat glass (one face, normal out of the glass)
Under each front door: Mirror_L / Mirror_R (chrome housing on a triangular base) and Mirror_L_Glass / Mirror_R_Glass; under each door DoorCard_xx.
Blender frame: x forward, y left (the driver, +y), z up; origin on the ground at the middle of the wheelbase.
"""
import math

import bmesh
from mathutils import Vector

V3 = Vector

# the driver's eye for the game's cab camera (this frame) and the steering wheel's hub and axis: also in the game (src/game/carspec.ts POLICE_CAB)
EYE = V3((-0.15, 0.37, 1.18))
HUB = V3((0.30, 0.37, 0.86))
ELEV = math.radians(25)                                    # the column rises 25 degrees toward the driver: the wheel's plane is 25 degrees from the vertical
AXIS = V3((-math.cos(ELEV), 0, math.sin(ELEV)))           # from the dash toward the driver
R_WHEEL = 0.195                                            # a 15.5 in wheel


def axes(deg):
    a = math.radians(deg)
    return V3((math.cos(a), 0, -math.sin(a))), V3((0, 1, 0)), V3((math.sin(a), 0, math.cos(a)))


def frame_of(n, up=V3((0, 0, 1))):
    """an orthonormal frame (ex, ey, ez) with ez = n and ey as level as possible"""
    ez = V3(n).normalized()
    ey = up.cross(ez).normalized() if abs(up.dot(ez)) < 0.99 else V3((0, 1, 0))
    ex = ey.cross(ez).normalized()
    return ex, ey, ez


def build_cab(B, root):
    CK, Mesh = B.CK, B.Mesh
    fix_doors(B)
    build_interior(B, CK, Mesh, root)
    build_dash(B, CK, Mesh, root)
    build_wheel(B, CK, Mesh, root)
    build_equipment(B, CK, Mesh, root)
    build_pillars(B, Mesh, root)
    build_door_cards(B, Mesh, root)
    build_mirrors(B, Mesh, root)


def wood_uv(B, ob):
    """the walnut picture covers 0.5 m: metres in the UVs times two"""
    B.metres_uv(ob, ('wood',))
    me = ob.data
    idx = {i for i, mm in enumerate(me.materials) if mm and mm.name == 'M_woodgrain'}
    uvl = me.uv_layers.active
    if not idx or uvl is None:
        return
    for p in me.polygons:
        if p.material_index in idx:
            for li in p.loop_indices:
                uvl.data[li].uv = uvl.data[li].uv * 2.0


# ---- the library's door parts that the cab replaces ---------------------------------------------------------------------------------------------------------------------------------
def fix_doors(B):
    """(1) The front doors' shells carry a band of seal faces lying in the windscreen's plane along the A-pillar (a by-product of the door split): seen from the seat it is a slab
    10-16 cm wide. Those faces are removed; the pillar is the thin PillarTrim between the windscreen's and the door glass's edges.
    (2) The library's outside mirrors (a round-cornered head on a stalk) are removed from Trim_FL / Trim_FR; Mirror_L / Mirror_R replace them."""
    import bpy
    G = B.G
    nws = V3((-0.64, 0, -0.77)).normalized()
    for k in ('FL', 'FR'):
        sh = bpy.data.objects.get('Door_' + k + '_shell')
        if sh is not None:
            bm = bmesh.new()
            bm.from_mesh(sh.data)
            mw = sh.matrix_world
            bad = []
            for f in bm.faces:
                c = mw @ f.calc_center_median()
                n = (mw.to_3x3() @ f.normal).normalized()
                if c.z > G.Z_BELT + 0.02 and c.x > 0.15 and abs(n.dot(nws)) > 0.85:
                    bad.append(f)
            bmesh.ops.delete(bm, geom=bad, context='FACES')
            bm.to_mesh(sh.data)
            bm.free()
            B.log('door', k, 'seal faces in the windscreen plane removed:', len(bad))
        tr = bpy.data.objects.get('Trim_' + k)
        if tr is not None:
            bm = bmesh.new()
            bm.from_mesh(tr.data)
            mw = tr.matrix_world
            seen, islands = set(), []
            for f in bm.faces:
                if f in seen:
                    continue
                isl, stack = [], [f]
                seen.add(f)
                while stack:
                    g = stack.pop()
                    isl.append(g)
                    for e in g.edges:
                        for h in e.link_faces:
                            if h not in seen:
                                seen.add(h)
                                stack.append(h)
                islands.append(isl)
            bad = []
            for isl in islands:
                vs = [mw @ v.co for f in isl for v in f.verts]
                lo = V3((min(v.x for v in vs), min(abs(v.y) for v in vs), min(v.z for v in vs)))
                hi = V3((max(v.x for v in vs), max(abs(v.y) for v in vs), max(v.z for v in vs)))
                if lo.x > 0.55 and hi.x < 0.80 and lo.y > 0.90 and lo.z > 0.88 and (hi - lo).length < 0.30:
                    bad += isl
            bad = set(bad)
            for f in bm.faces:       # whatever of the library mirror (head, stalk, foot) is still left outside the door
                if f not in bad and all(0.55 < (mw @ v.co).x < 0.82 and 0.925 < abs((mw @ v.co).y) < 1.16 and 0.84 < (mw @ v.co).z < 1.06 for v in f.verts):
                    bad.add(f)
            bmesh.ops.delete(bm, geom=list(bad), context='FACES')
            bm.to_mesh(tr.data)
            bm.free()
            B.log('door', k, 'library mirror faces removed:', len(bad))

    # the library's A-pillar spotlights (a black ball on a handle reaching into the cab, in the shared Trim object) are taken off: they read as a ball on a stick inside the cab
    tr = bpy.data.objects.get('Trim')
    if tr is not None:
        bm = bmesh.new()
        bm.from_mesh(tr.data)
        mw = tr.matrix_world
        bad = [f for f in bm.faces if all(0.45 < (mw @ v.co).x < 0.66 and 0.70 < abs((mw @ v.co).y) < 0.92 and 1.0 < (mw @ v.co).z < 1.22 for v in f.verts)]
        bad += [f for f in bm.faces if f not in bad and all(0.74 < (mw @ v.co).x < 0.83 and 0.15 < abs((mw @ v.co).y) < 0.70 and 0.98 < (mw @ v.co).z < 1.07 for v in f.verts)]   # the handles
        bad += [f for f in bm.faces if f not in bad and all(0.50 < (mw @ v.co).x < 0.62 and 0.58 < abs((mw @ v.co).y) < 0.78 and 1.04 < (mw @ v.co).z < 1.14 for v in f.verts)]   # a stub of the handle
        bmesh.ops.delete(bm, geom=bad, context='FACES')
        bm.to_mesh(tr.data)
        bm.free()
        B.log('door', 'Trim', 'spotlight faces removed:', len(bad))


# ---- seats, belts, pedals, visors -----------------------------------------------------------------------------------------------------------------------------------------------
def build_interior(B, CK, Mesh, root):
    m = Mesh()
    # the front bench, split with the centre armrest down; grey velour with lengthwise stitched channels
    for s in (1, -1):
        ex, ey, ez = axes(-5)
        CK.cushion(m, V3((-0.02, s * 0.35, 0.49)), ex, ey, ez, 0.52, 0.68, 0.13, pleats=7, kind='seatcloth', piping='seatcloth')
        ex, ey, ez = axes(-18)
        CK.cushion(m, V3((-0.31, s * 0.35, 0.80)), ez, ey, -ex, 0.56, 0.68, 0.13, pleats=8, kind='seatcloth', piping='seatcloth')
        CK.cushion(m, V3((-0.38, s * 0.38, 1.12)), ez, ey, -ex, 0.17, 0.26, 0.09, pleats=2, kind='seatcloth', piping='seatcloth')
        m.cyl(V3((-0.36, s * 0.31, 1.03)), V3((-0.37, s * 0.31, 1.08)), 0.006, 'brightwork', seg=8)
        m.cyl(V3((-0.36, s * 0.45, 1.03)), V3((-0.37, s * 0.45, 1.08)), 0.006, 'brightwork', seg=8)
        m.rbox(V3((-0.02, s * 0.35, 0.385)), (0.46, 0.05, 0.03), 0.006, 'black')
        m.cyl(V3((0.20, s * 0.14, 0.40)), V3((0.20, s * 0.56, 0.40)), 0.007, 'brightwork', seg=8)
    m.rbox(V3((-0.02, 0, 0.40)), (0.48, 1.36, 0.06), 0.01, 'black')
    m.rbox(V3((-0.22, 0, 0.66)), (0.46, 0.17, 0.085), 0.03, 'seatcloth')
    # the rear bench
    ex, ey, ez = axes(-4)
    CK.cushion(m, V3((-1.18, 0, 0.48)), ex, ey, ez, 0.50, 1.24, 0.13, pleats=12, kind='seatcloth', piping='seatcloth')
    ex, ey, ez = axes(-22)
    CK.cushion(m, V3((-1.47, 0, 0.77)), ez, ey, -ex, 0.52, 1.30, 0.12, pleats=13, kind='seatcloth', piping='seatcloth')
    # belts
    for s in (1, -1):
        a = V3((-0.36, s * 0.80, 1.17))
        b = V3((0.02, s * 0.08, 0.53))
        m.tube([a, a.lerp(b, 0.35) + V3((0.08, 0, 0.0)), a.lerp(b, 0.75) + V3((0.10, 0, -0.03)), b], 0.014, 'black', seg=4)
        m.rbox(a + V3((0.0, -s * 0.01, 0.06)), (0.03, 0.045, 0.07), 0.01, 'black')
        m.rbox(b, (0.05, 0.02, 0.03), 0.005, 'brightwork')
    # pedals
    for y, wd, h in ((0.30, 0.13, 0.06), (0.46, 0.06, 0.10), (0.66, 0.05, 0.05)):
        m.rbox(V3((0.70, y, 0.42)), (0.02, wd, h), 0.006, 'black', axes(-30))
        m.cyl(V3((0.71, y, 0.46)), V3((0.78, y, 0.64)), 0.009, 'black', seg=6)
    # the sun visors (black), their pivots
    for s in (1, -1):
        m.rbox(V3((0.10, s * 0.42, 1.315)), (0.16, 0.40, 0.022), 0.008, 'interior', axes(-25))
        m.cyl(V3((0.22, s * 0.22, 1.35)), V3((0.22, s * 0.22, 1.37)), 0.006, 'brightwork', seg=8)
    # the dome lamp
    m.rbox(V3((-0.55, 0, 1.357)), (0.12, 0.17, 0.014), 0.006, 'interior')
    m.rbox(V3((-0.55, 0, 1.349)), (0.10, 0.15, 0.006), 0.003, 'lamp_lens')
    ob = m.finish('Interior', root, sharp=40)
    B.metres_uv(ob, ('seatcloth',))
    return ob


# ---- the dash ----------------------------------------------------------------------------------------------------------------------------------------------------------------
XF = 0.50          # the face of the instrument panel (x)
ZW0, ZW1 = 0.745, 0.915   # the walnut band


def build_dash(B, CK, Mesh, root):
    m = Mesh()
    Y = 0.80
    # the body: padded top with a rounded edge over the face, the face, the lower panel; the ends curve back into the door pillars
    prof = [(0.88, 0.975), (0.66, 0.99), (0.54, 0.986), (0.50, 0.975), (0.476, 0.955), (0.472, 0.935), (0.485, 0.922), (XF, 0.918),
            (XF, 0.74), (0.505, 0.70), (0.52, 0.64), (0.56, 0.585), (0.66, 0.56), (0.88, 0.60)]
    rings = []
    for k in range(0, 41):
        y = -Y + 2 * Y * k / 40
        e = max(0.0, abs(y) - 0.70) / 0.10
        rings.append([V3((px + 0.04 * e * e, y, pz - 0.01 * e * e)) for px, pz in prof])
    vs = m.loft(rings, 'dash', closed=True, caps=True)
    # the top (the first six points of the profile) is the soft pad
    for f in m.bm.faces:
        if f.calc_center_median().z > 0.925:
            f.material_index = m.mi('pad')
    # the walnut band across the whole face, bright edging above and below
    m.rbox(V3((XF - 0.003, 0, 0.5 * (ZW0 + ZW1))), (0.006, 1.54, ZW1 - ZW0), 0.002, 'wood')
    for z in (ZW1 + 0.002, ZW0 - 0.002):
        m.rbox(V3((XF - 0.006, 0, z)), (0.006, 1.54, 0.005), 0.002, 'brightwork')
    # the cluster: a black frame, the face, a glass over it, in front of the driver
    cy, cz, cw, ch = 0.37, 0.835, 0.46, 0.135
    for dy in (-cw / 2, cw / 2):
        m.rbox(V3((XF - 0.012, cy + dy, cz)), (0.018, 0.018, ch + 0.018), 0.004, 'black')
    for dz in (-ch / 2, ch / 2):
        m.rbox(V3((XF - 0.012, cy, cz + dz)), (0.018, cw + 0.018, 0.018), 0.004, 'black')
    m.box(V3((XF - 0.0075, cy, cz)), (0.002, cw - 0.004, ch - 0.004), 'gauges')
    m.box(V3((XF - 0.016, cy, cz)), (0.001, cw, ch), 'glass_cluster')
    # vents: square, horizontal ribs; left of the wheel, right of the cluster (two), at the passenger's end
    for y, z in ((0.70, 0.83), (0.075, 0.83), (-0.74, 0.83)):
        _vent(m, y, z)
    # the centre console in walnut, down from the band: radio above, climate below
    cx = -0.06
    m.rbox(V3((XF - 0.004, cx, 0.68)), (0.008, 0.20, 0.13), 0.004, 'wood')
    for y in (cx - 0.10, cx + 0.10):
        m.rbox(V3((XF - 0.006, y, 0.73)), (0.006, 0.005, 0.37), 0.002, 'brightwork')
    m.rbox(V3((XF - 0.012, cx, 0.80)), (0.014, 0.18, 0.05), 0.004, 'radio')
    m.box(V3((XF - 0.0195, cx, 0.807)), (0.002, 0.10, 0.018), 'gauge')
    for y in (cx - 0.07, cx + 0.07):
        m.cyl(V3((XF - 0.018, y, 0.80)), V3((XF - 0.036, y, 0.80)), 0.010, 'brightwork', seg=12)
    for j in range(5):
        m.rbox(V3((XF - 0.021, cx - 0.04 + 0.02 * j, 0.785)), (0.006, 0.014, 0.008), 0.002, 'brightwork')
    m.rbox(V3((XF - 0.012, cx, 0.70)), (0.014, 0.18, 0.06), 0.004, 'radio')
    for j in range(3):
        m.box(V3((XF - 0.0195, cx - 0.05 + 0.04 * j, 0.706)), (0.002, 0.006, 0.035), 'black')
        m.rbox(V3((XF - 0.024, cx - 0.05 + 0.04 * j, 0.712 - 0.012 * j)), (0.008, 0.018, 0.012), 0.003, 'brightwork')
    m.cyl(V3((XF - 0.018, cx + 0.065, 0.69)), V3((XF - 0.034, cx + 0.065, 0.69)), 0.011, 'black', seg=12)
    m.rbox(V3((XF - 0.010, cx, 0.635)), (0.012, 0.16, 0.03), 0.004, 'black')
    # the long walnut panel before the passenger already lies on the band; the glove box below it, black plastic, its latch
    m.rbox(V3((XF + 0.002, -0.45, 0.67)), (0.012, 0.46, 0.11), 0.01, 'dash')
    m.rbox(V3((XF - 0.006, -0.45, 0.705)), (0.006, 0.07, 0.014), 0.003, 'brightwork')
    # the knee panel under the cluster, the headlamp switch and the trunk release at its foot
    m.rbox(V3((XF + 0.005, 0.40, 0.67)), (0.012, 0.66, 0.11), 0.01, 'dash')
    m.cyl(V3((XF - 0.004, 0.66, 0.70)), V3((XF - 0.03, 0.66, 0.70)), 0.012, 'brightwork', seg=12)
    m.rbox(V3((XF + 0.04, 0.62, 0.61)), (0.03, 0.045, 0.025), 0.006, 'black')
    # the column shroud from the hub into the dash, the selector lever (right, up, chrome with a ball) and the turn signal stalk (left)
    hub, ax = HUB, AXIS
    m.cyl(hub - ax * 0.055, hub - ax * 0.24, 0.040, 'dash', seg=20, r1=0.050)
    m.cyl(hub - ax * 0.24, hub - ax * 0.34, 0.050, 'dash', seg=20, r1=0.070)
    c = hub - ax * 0.16 + V3((0, -0.046, -0.012))
    m.cyl(c, c + V3((0.0, -0.012, 0)), 0.013, 'brightwork', seg=14)
    lev0 = hub - ax * 0.10 + V3((0, -0.045, 0.0))
    path = [lev0, lev0 + V3((-0.01, -0.08, 0.025)), lev0 + V3((-0.03, -0.15, 0.06)), lev0 + V3((-0.04, -0.19, 0.08))]
    m.tube(path, [0.009, 0.007, 0.006, 0.006], 'brightwork', seg=8)
    ball = path[-1] + V3((-0.004, -0.012, 0.006))
    m.rbox(ball, (0.03, 0.03, 0.03), 0.0149, 'black', seg=4)
    st = hub - ax * 0.10 + V3((0, 0.045, -0.005))
    m.tube([st, st + V3((-0.01, 0.09, -0.01)), st + V3((-0.02, 0.16, -0.015))], 0.005, 'brightwork', seg=6)
    m.rbox(st + V3((-0.02, 0.17, -0.015)), (0.014, 0.04, 0.014), 0.006, 'black')
    ob = m.finish('Dash', root, sharp=38)
    CK.planar_uv(ob, 'gauges', axes='yz', flip_u=True)
    wood_uv(B, ob)
    return ob


def _vent(m, y, z, s=0.085):
    m.rbox(V3((XF - 0.007, y, z)), (0.010, s + 0.012, s + 0.012), 0.004, 'brightwork')
    m.rbox(V3((XF - 0.010, y, z)), (0.004, s, s), 0.002, 'vent')
    for k in range(6):
        m.rbox(V3((XF - 0.015, y, z - s / 2 + s * (k + 0.5) / 6)), (0.012, s - 0.006, 0.004), 0.0015, 'vent')
    m.rbox(V3((XF - 0.022, y, z)), (0.008, 0.012, 0.012), 0.003, 'brightwork')


# ---- the steering wheel -------------------------------------------------------------------------------------------------------------------------------------------------------
def build_wheel(B, CK, Mesh, root):
    """A large thin-rimmed black wheel with four spokes: two out to the sides, two down and out with bright inserts; a big rectangular pad with an oval emblem.
    Its origin is the hub; the wheel turns about AXIS."""
    m = Mesh()
    hub, ax = HUB, AXIS
    u = V3((0, 1, 0))                          # the wheel's left in its plane
    w = ax.cross(u).normalized()               # the wheel's up in its plane
    if w.z < 0:
        w = -w
    R, n = R_WHEEL, 96
    m.tube([hub + (u * math.cos(2 * math.pi * k / n) + w * math.sin(2 * math.pi * k / n)) * R for k in range(n)],
           0.0115, 'dash', seg=12, loop=True)
    for ang, insert in ((5, False), (175, False), (-48, True), (-132, True)):
        d = u * math.cos(math.radians(ang)) + w * math.sin(math.radians(ang))
        a, b = hub + d * 0.075, hub + d * (R - 0.004)
        side = ax.cross(d).normalized()
        m.rbox((a + b) / 2 - ax * 0.008, ((b - a).length, 0.030 if insert else 0.024, 0.012), 0.005, 'dash', (d, side, ax))
        if insert:
            m.rbox((a + b) / 2 - ax * 0.0015, ((b - a).length - 0.02, 0.010, 0.002), 0.001, 'brightwork', (d, side, ax))
    # the pad: big, rectangular with rounded corners, a raised border; the oval emblem
    m.rbox(hub + ax * 0.012, (0.20, 0.135, 0.05), 0.025, 'dash', (u, w, ax))
    m.rbox(hub + ax * 0.034, (0.17, 0.105, 0.012), 0.012, 'pad', (u, w, ax))
    m.rbox(hub + ax * 0.041, (0.046, 0.022, 0.004), 0.010, 'brightwork', (u, w, ax))
    m.rbox(hub + ax * 0.0435, (0.038, 0.016, 0.003), 0.007, 'badge', (u, w, ax))
    m.cyl(hub - ax * 0.015, hub - ax * 0.055, 0.045, 'dash', seg=16)
    return m.finish('SteeringWheel', root, sharp=40, origin=hub)


# ---- mirrors ------------------------------------------------------------------------------------------------------------------------------------------------------------------
def _aim(at, target):
    """the normal of a flat mirror at `at` that shows the driver's eye the point `target`"""
    d = (at - EYE).normalized()
    r = (target - at).normalized()
    return (r - d).normalized()


def _rrect(cx, ex, ey, w, h, r, nseg=4):
    pts = []
    for (sx, sy, a0) in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        c = cx + ex * (sx * (w / 2 - r)) + ey * (sy * (h / 2 - r))
        for k in range(nseg + 1):
            a = math.radians(a0 + 90 * k / nseg)
            pts.append(c + (ex * math.cos(a) + ey * math.sin(a)) * r)
    return pts


def _glass(B, Mesh, name, centre, n, w, h, r, parent):
    """one flat face, normal n (out of the glass), its own node at its centre"""
    import bpy
    m = Mesh()
    ex, ey, ez = frame_of(n)
    pts = _rrect(centre, ey, ex, w, h, r)            # w along the level axis ey, h along ex
    vs = [m.bm.verts.new(p) for p in pts]
    f = m.face(vs, 'mirror')
    if f is not None and f.normal.dot(n) < 0:
        f.normal_flip()
    ob = m.finish(name, None, sharp=80, origin=centre)
    # finish() recalculates normals outward of a closed shell; one face: make sure it looks along n
    me = ob.data
    if me.polygons and me.polygons[0].normal.dot(n) < 0:
        bm = bmesh.new()
        bm.from_mesh(me)
        for f in bm.faces:
            f.normal_flip()
        bm.to_mesh(me)
        bm.free()
    mw = ob.matrix_world.copy()
    ob.parent = parent
    ob.matrix_parent_inverse = parent.matrix_world.inverted()
    ob.matrix_world = mw
    return ob


def build_mirrors(B, Mesh, root):
    import bpy
    glass = bpy.data.objects.get('Glass')
    # the inside mirror: hangs on a short stalk from the windscreen's top at the middle; 25 x 6 cm glass in a dark plastic frame
    top = None
    if glass is not None:
        vs = [glass.matrix_world @ v.co for v in glass.data.vertices]
        vs = [v for v in vs if v.x > 0.0 and abs(v.y) < 0.05 and v.z < 1.30]
        top = max(vs, key=lambda v: v.z) if vs else None
    top = top or V3((0.34, 0, 1.29))
    c = top + V3((-0.075, 0, -0.065))
    n = _aim(c, V3((-3.0, 0.0, 1.10)))
    ex, ey, ez = frame_of(n)
    m = Mesh()
    m.rbox(c - ez * 0.016, (0.075, 0.27, 0.03), 0.014, 'black', (ex, ey, ez))
    m.cyl(c - ez * 0.03, top + V3((-0.012, 0, -0.008)), 0.008, 'black', seg=10)
    m.rbox(top + V3((-0.012, 0, -0.004)), (0.03, 0.05, 0.012), 0.004, 'black')
    m.finish('Mirror_Inner', root, sharp=40)
    _glass(B, Mesh, 'Mirror_Inner_Glass', c + ez * 0.0002, n, 0.25, 0.06, 0.012, root)
    # the outside mirrors: on each front door at the foot of the A-pillar, a triangular base on the door, a chrome rectangular housing about 15 x 10 cm
    for s, k in ((1, 'L'), (-1, 'R')):
        door = bpy.data.objects.get('Door_F' + k)
        if door is None:
            continue
        base = V3((0.70, s * 0.925, 0.955))
        head = V3((0.66, s * 1.04, 0.985))          # low and out on the door: clear of the driver's spotlight lamp above it on the A-pillar
        n = _aim(head, V3((-12.0, s * 1.6, 1.0)))
        ex, ey, ez = frame_of(n)
        m = Mesh()
        tri = [base + V3((0.06, 0, -0.01)), base + V3((-0.07, 0, -0.01)), base + V3((0.03, 0, 0.07))]
        out = V3((0, s, 0))
        vs0 = [m.bm.verts.new(p) for p in tri]
        vs1 = [m.bm.verts.new(p + out * 0.02) for p in tri]
        m.face(vs1, 'brightwork')
        m.face(list(reversed(vs0)), 'brightwork')
        for i in range(3):
            m.face([vs0[i], vs0[(i + 1) % 3], vs1[(i + 1) % 3], vs1[i]], 'brightwork')
        m.cyl(base + out * 0.02 + V3((0.0, 0, 0.02)), head - ez * 0.03, 0.011, 'brightwork', seg=10)
        m.rbox(head - ez * 0.026, (0.106, 0.156, 0.05), 0.016, 'brightwork', (ex, ey, ez))
        m.rbox(head - ez * 0.002, (0.098, 0.148, 0.004), 0.010, 'black', (ex, ey, ez))
        ob = m.finish('Mirror_' + k, None, sharp=40)
        mw = ob.matrix_world.copy()
        ob.parent = door
        ob.matrix_parent_inverse = door.matrix_world.inverted()
        ob.matrix_world = mw
        _glass(B, Mesh, 'Mirror_' + k + '_Glass', head + ez * 0.0012, n, 0.14, 0.09, 0.008, door)


# ---- the police package's equipment -----------------------------------------------------------------------------------------------------------------------------------------------
def build_equipment(B, CK, Mesh, root):
    """The radio and the siren as a 1980s patrol car carried them (California Highway Patrol radio history, wb6nvh.com/CHP/CHP3a.htm): a welded steel rack over the transmission hump,
    braced to the dash, holding the radio's control head and the siren / lights console (slide volume control, switches lit through a blue lens, a blue pilot light on the upper edge),
    a hand microphone (grey with a black grille) on a clip with its coiled cord, and a scanner under the dash to the right of them. No make is modelled: plain units, no lettering."""
    m = Mesh()
    ex, ey, ez = axes(-38)                        # the faces tilt back toward the driver
    # the rack: two side plates on the hump, a front brace up to the lower dash, a floor plate
    for y in (-0.10, 0.10):
        m.box(V3((0.30, y, 0.47)), (0.26, 0.006, 0.10), 'steel')
        m.tube([V3((0.40, y, 0.50)), V3((0.44, y, 0.56)), V3((0.455, y, 0.585))], 0.008, 'steel', seg=6)
    m.box(V3((0.30, 0, 0.425)), (0.26, 0.21, 0.006), 'steel')
    # the radio control head, upper unit
    c1 = V3((0.335, 0, 0.585))
    m.rbox(c1, (0.10, 0.19, 0.065), 0.008, 'radio', (ex, ey, ez))
    f1 = c1 - ex * 0.051
    m.rbox(f1, (0.004, 0.175, 0.052), 0.004, 'black', (ex, ey, ez))
    m.box(f1 - ex * 0.003 + ez * 0.010 + ey * 0.04, (0.002, 0.06, 0.014), 'amber_lit', (ex, ey, ez))
    for k in range(4):
        m.rbox(f1 - ex * 0.006 - ez * 0.012 + ey * (-0.06 + 0.026 * k), (0.008, 0.018, 0.012), 0.002, 'brightwork', (ex, ey, ez))
    for y in (-0.068, 0.0):
        m.cyl(f1 + ey * y + ez * 0.010, f1 + ey * y + ez * 0.010 - ex * 0.018, 0.009, 'black', seg=12)
    # the siren / lights console, lower unit: a slide volume control, rocker switches, a blue pilot light
    c2 = V3((0.30, 0, 0.505))
    m.rbox(c2, (0.10, 0.19, 0.06), 0.008, 'radio', (ex, ey, ez))
    f2 = c2 - ex * 0.051
    m.rbox(f2, (0.004, 0.175, 0.048), 0.004, 'black', (ex, ey, ez))
    m.box(f2 - ex * 0.004 + ez * 0.012 + ey * 0.045, (0.003, 0.06, 0.005), 'brightwork', (ex, ey, ez))
    m.rbox(f2 - ex * 0.009 + ez * 0.012 + ey * 0.03, (0.010, 0.010, 0.012), 0.002, 'black', (ex, ey, ez))
    for k, kind in enumerate(('blue_lit', 'black', 'black', 'red_lit', 'black')):
        m.rbox(f2 - ex * 0.007 - ez * 0.010 + ey * (-0.075 + 0.026 * k), (0.010, 0.016, 0.020), 0.003, kind, (ex, ey, ez))
    m.cyl(c2 + ez * 0.032 + ey * 0.07, c2 + ez * 0.040 + ey * 0.07, 0.005, 'blue_lit', seg=10)
    # the microphone on its clip on the rack's left side plate, the coiled cord to the head
    mc = V3((0.27, 0.115, 0.50))
    m.rbox(mc, (0.035, 0.022, 0.075), 0.010, 'radio_grey')
    m.rbox(mc + V3((-0.0185, 0, 0.012)), (0.003, 0.018, 0.04), 0.003, 'black')
    m.rbox(mc + V3((0.0, -0.014, 0.0)), (0.02, 0.006, 0.03), 0.002, 'steel')
    cord = []
    for k in range(70):
        t = k / 69
        a = 2 * math.pi * 9 * t
        p = mc.lerp(V3((0.33, 0.06, 0.56)), t) + V3((0, 0, -0.07 * math.sin(math.pi * t)))
        cord.append(p + V3((0.0, 0.007 * math.cos(a), 0.007 * math.sin(a))))
    m.tube(cord, 0.0025, 'black', seg=5)
    # the scanner under the dash, right of the rack
    sc = V3((0.42, -0.24, 0.60))
    m.rbox(sc, (0.13, 0.17, 0.05), 0.006, 'radio')
    m.box(sc - V3((0.066, 0, -0.005)), (0.002, 0.08, 0.016), 'red_lit')
    for k in range(6):
        m.rbox(sc - V3((0.068, -0.03 + 0.012 * k, 0.012)), (0.006, 0.008, 0.007), 0.001, 'brightwork')
    for y in (-0.08, 0.08):
        m.box(sc + V3((0.0, y, 0.035)), (0.08, 0.004, 0.03), 'steel')
    ob = m.finish('Equipment', root, sharp=40)
    return ob


# ---- pillar trim -----------------------------------------------------------------------------------------------------------------------------------------------------------------
def _edge(obs, sel, key, zs, dz=0.02):
    """points of a glass edge: for each z the vertex of the selected glass (world frame) that is extreme by key, or None"""
    vs = [ob.matrix_world @ v.co for ob in obs for v in ob.data.vertices]
    vs = [v for v in vs if sel(v)]
    out = []
    for z in zs:
        near = [v for v in vs if abs(v.z - z) < dz]
        out.append(max(near, key=key) if near else None)
    return out


def build_pillars(B, Mesh, root):
    """Moulded trim covers on the A, B and C pillars, between the glass edges (the pillars of the photographs are covered in the interior's colour), with a soft crown toward the cabin."""
    import bpy
    G = B.G
    glass = bpy.data.objects.get('Glass')
    m = Mesh()
    for s in (1, -1):
        k = 'L' if s > 0 else 'R'
        fg, rg = bpy.data.objects.get('Glass_F' + k), bpy.data.objects.get('Glass_R' + k)
        if not (glass and fg and rg):
            continue
        side = lambda v, s=s: v.y * s > 0.2  # noqa: E731
        zs = [G.Z_BELT + 0.02 + (G.GH_Z_ROOF_EDGE - G.Z_BELT - 0.03) * i / 14 for i in range(15)]
        ws = _edge([glass], lambda v: v.x > 0.0 and side(v), lambda v: v.y * s, zs)           # the windscreen's side edge
        fr = _edge([fg], side, lambda v: v.x, zs)                                               # the front door glass, front edge (x forward)
        fd = _edge([fg], side, lambda v: -v.x, zs)                                              # ... its rear edge
        rf = _edge([rg], side, lambda v: v.x, zs)                                               # the rear door glass, front edge
        rd = _edge([rg], side, lambda v: -v.x, zs)                                              # ... its rear edge
        bl = _edge([glass], lambda v: v.x < -1.0 and side(v), lambda v: v.y * s, zs)          # the backlight's side edge
        for a, b, bulge in ((ws, fr, 0.012), (fd, rf, 0.015), (rd, bl, 0.02)):
            rows = []
            for pa, pb in zip(a, b):
                if pa is None or pb is None:
                    continue
                inn = V3((0, -s, 0))
                rows.append([pa.lerp(pb, -0.15 + 1.3 * j / 6) + inn * (0.008 + bulge * math.sin(math.pi * j / 6)) for j in range(7)])
            if len(rows) >= 3:
                m.grid(rows, 'headliner')
                m.grid([list(reversed(r)) for r in rows], 'headliner')
    return m.finish('PillarTrim', root, sharp=50)


# ---- door cards: what the driver sees of the door's inner panel ---------------------------------------------------------------------------------------------------------------------
def build_door_cards(B, Mesh, root):
    """Dark blue door trim with a horizontal walnut insert under bright edging, a bright pull handle, the pull strap, the switch plate on the armrest, a carpeted lower band.
    Each door's card is a child of its door node, so it opens and falls off with the door."""
    import bpy
    G = B.G
    for front in (True, False):
        for s in (1, -1):
            k = ('F' if front else 'R') + ('L' if s > 0 else 'R')
            door = bpy.data.objects.get('Door_' + k)
            if door is None:
                continue
            m = Mesh()
            x0, x1 = (G.X(735), G.X(870)) if front else (G.X(600), G.X(700))
            xm = 0.5 * (x0 + x1)
            y = s * 0.83                                       # the inner skin's face (ray test)
            # the upper bolster and the walnut insert with bright edges
            m.rbox(V3((xm, y - s * 0.006, 0.90)), (x1 - x0 - 0.02, 0.014, 0.06), 0.008, 'headliner')
            m.rbox(V3((xm, y - s * 0.014, 0.855)), (x1 - x0 - 0.06, 0.004, 0.032), 0.002, 'wood')
            for z in (0.873, 0.837):
                m.rbox(V3((xm, y - s * 0.015, z)), (x1 - x0 - 0.06, 0.004, 0.004), 0.0015, 'brightwork')
            # the inside handle (bright) in its cup, ahead of the strap
            hx = x1 - 0.12
            m.rbox(V3((hx, y - s * 0.004, 0.80)), (0.12, 0.012, 0.045), 0.008, 'black')
            m.rbox(V3((hx, y - s * 0.014, 0.80)), (0.10, 0.012, 0.022), 0.006, 'brightwork')
            # the pull strap with bright end caps
            for xe in (x0 + 0.10, x1 - 0.22):
                m.rbox(V3((xe, y - s * 0.010, 0.79)), (0.035, 0.012, 0.022), 0.005, 'brightwork')
            m.tube([V3((x0 + 0.12, y - s * 0.018, 0.79)), V3((0.5 * (x0 + x1 - 0.12), y - s * 0.032, 0.785)), V3((x1 - 0.24, y - s * 0.018, 0.79))], 0.011, 'interior', seg=8)
            m.rbox(V3((xm + 0.06, y - s * 0.03, 0.708)), (0.14, 0.05, 0.006), 0.002, 'brightwork')
            for j in range(4 if front else 2):
                m.rbox(V3((xm + 0.02 + 0.025 * j, y - s * 0.03, 0.713)), (0.012, 0.02, 0.006), 0.002, 'black')
            m.rbox(V3((xm, y - s * 0.002, 0.43)), (x1 - x0 - 0.04, 0.006, 0.14), 0.004, 'carpet')
            ob = m.finish('DoorCard_' + k, None, sharp=40)
            mw = ob.matrix_world.copy()
            ob.parent = door
            ob.matrix_parent_inverse = door.matrix_world.inverted()
            ob.matrix_world = mw
            B.metres_uv(ob, ('carpet',))
            wood_uv(B, ob)
