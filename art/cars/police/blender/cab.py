# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""The cab of the 1987 police LTD Crown Victoria, worked out for a first-person camera (replaces build_interior of the library model; see ../SOURCES.md for what each part is based on).

Nodes added under the car root (existing nodes keep their names):
  Interior       seats (front split bench, rear bench), belts, pedals, mirror, visors, dome lamp, spotlight handle (as before, in more detail)
  Dash           instrument panel: padded pad, cluster with its hood and face, vents, radio, heater controls, glovebox, column shroud, trunk release
  SteeringWheel  rim and two spokes with the horn pad; its origin is the hub on the column axis, the wheel turns about AXIS (see AXIS below)
  Equipment      the police package's equipment: radio control head and handset, siren and light controller on its bracket on the transmission hump
Blender frame: x forward, y left (the driver, +y), z up; origin on the ground at the middle of the wheelbase.
"""
import math

from mathutils import Vector

V3 = Vector

# the driver's eye for the game's cab camera (this frame) and the steering wheel's hub and axis: also exported to the game (src/game/carspec.ts)
EYE = V3((-0.15, 0.37, 1.13))
HUB = V3((0.25, 0.37, 0.80))
ELEV = math.radians(48)                                    # the column's rake: the wheel's plane is 42 degrees from the horizontal
AXIS = V3((-math.cos(ELEV), 0, math.sin(ELEV)))           # from the dash toward the driver


def axes(deg):
    a = math.radians(deg)
    return V3((math.cos(a), 0, -math.sin(a))), V3((0, 1, 0)), V3((math.sin(a), 0, math.cos(a)))


def build_cab(B, root):
    CK, Mesh = B.CK, B.Mesh
    build_interior(B, CK, Mesh, root)
    build_dash(B, CK, Mesh, root)
    build_wheel(B, CK, Mesh, root)
    build_equipment(B, CK, Mesh, root)
    build_pillars(B, Mesh, root)
    build_door_cards(B, Mesh, root)


# ---- seats, belts, pedals, mirror, visors -------------------------------------------------------------------------------------------------------------------------------------------
def build_interior(B, CK, Mesh, root):
    m = Mesh()
    # the front bench, split 50/50 with a centre armrest folded down between the halves (the 1987 police car in the Barn Finds photograph: ribbed cloth, armrest down)
    for s in (1, -1):
        ex, ey, ez = axes(-5)
        CK.cushion(m, V3((-0.02, s * 0.35, 0.49)), ex, ey, ez, 0.52, 0.68, 0.13, pleats=7, kind='seatcloth', piping='interior')
        ex, ey, ez = axes(-18)
        CK.cushion(m, V3((-0.31, s * 0.35, 0.80)), ez, ey, -ex, 0.56, 0.68, 0.13, pleats=8, kind='seatcloth', piping='interior')
        CK.cushion(m, V3((-0.38, s * 0.38, 1.12)), ez, ey, -ex, 0.17, 0.26, 0.09, pleats=2, kind='seatcloth', piping='interior')
        m.cyl(V3((-0.36, s * 0.31, 1.03)), V3((-0.37, s * 0.31, 1.08)), 0.006, 'chrome', seg=8)
        m.cyl(V3((-0.36, s * 0.45, 1.03)), V3((-0.37, s * 0.45, 1.08)), 0.006, 'chrome', seg=8)
        # seat track and the adjuster bar under the front edge
        m.rbox(V3((-0.02, s * 0.35, 0.385)), (0.46, 0.05, 0.03), 0.006, 'black')
        m.cyl(V3((0.20, s * 0.14, 0.40)), V3((0.20, s * 0.56, 0.40)), 0.007, 'chrome', seg=8)
    m.rbox(V3((-0.02, 0, 0.40)), (0.48, 1.36, 0.06), 0.01, 'black')
    # the centre armrest: down, between the halves; a pad on a hinge at the back of the bench
    m.rbox(V3((-0.22, 0, 0.66)), (0.46, 0.17, 0.085), 0.03, 'interior')
    m.rbox(V3((-0.22, 0, 0.705)), (0.40, 0.14, 0.012), 0.005, 'seatcloth')
    m.cyl(V3((-0.43, -0.07, 0.69)), V3((-0.43, 0.07, 0.69)), 0.012, 'chrome', seg=10)
    # the rear bench (cloth), its belts' buckles
    ex, ey, ez = axes(-4)
    CK.cushion(m, V3((-1.18, 0, 0.48)), ex, ey, ez, 0.50, 1.24, 0.13, pleats=12, kind='seatcloth', piping='interior')
    ex, ey, ez = axes(-22)
    CK.cushion(m, V3((-1.47, 0, 0.77)), ez, ey, -ex, 0.52, 1.30, 0.12, pleats=13, kind='seatcloth', piping='interior')
    # lap and shoulder belts of the front seats: the B-pillar's loop, the belt across to the buckle on the cushion's inner side, a retractor cover low on the pillar
    for s in (1, -1):
        a = V3((-0.36, s * 0.80, 1.17))
        b = V3((0.02, s * 0.08, 0.53))
        m.tube([a, a.lerp(b, 0.35) + V3((0.08, 0, 0.0)), a.lerp(b, 0.75) + V3((0.10, 0, -0.03)), b], [0.014, 0.014, 0.014, 0.014], 'black', seg=4)
        m.rbox(a + V3((0.0, -s * 0.01, 0.06)), (0.03, 0.045, 0.07), 0.01, 'black')
        m.rbox(b, (0.05, 0.02, 0.03), 0.005, 'chrome')
        m.rbox(b + V3((0.0, 0, 0.03)), (0.03, 0.016, 0.06), 0.004, 'red_lit')
    # pedals: the brake's wide pad, the accelerator, the parking brake's foot pedal at the left kick panel (Panther); rubber pads
    for y, wd, h in ((0.30, 0.13, 0.06), (0.46, 0.06, 0.10), (0.66, 0.05, 0.05)):
        m.rbox(V3((0.66, y, 0.42)), (0.02, wd, h), 0.006, 'black', axes(-30))
        m.cyl(V3((0.67, y, 0.46)), V3((0.74, y, 0.64)), 0.009, 'black', seg=6)
    # the inside mirror: a housing on a stalk with a day/night lever, glass facing the driver
    xm = B.G.X(808)
    m.rbox(V3((xm, 0, 1.27)), (0.035, 0.25, 0.07), 0.012, 'black')
    m.rbox(V3((xm - 0.0185, 0, 1.27)), (0.003, 0.225, 0.052), 0.004, 'mirror')
    m.cyl(V3((xm + 0.03, 0, 1.30)), V3((xm + 0.08, 0, 1.33)), 0.007, 'black', seg=6)
    m.cyl(V3((xm - 0.005, 0, 1.232)), V3((xm - 0.03, 0, 1.222)), 0.004, 'black', seg=6)
    # the sun visors, with their pivot arms and clips
    for s in (1, -1):
        m.rbox(V3((0.08, s * 0.42, 1.31)), (0.16, 0.40, 0.022), 0.008, 'interior', axes(-25))
        m.cyl(V3((0.20, s * 0.22, 1.345)), V3((0.20, s * 0.22, 1.37)), 0.006, 'chrome', seg=8)
    # the dome lamp on the headliner between the visors and the mirror
    m.rbox(V3((-0.55, 0, 1.357)), (0.12, 0.17, 0.014), 0.006, 'bezel')
    m.rbox(V3((-0.55, 0, 1.349)), (0.10, 0.15, 0.006), 0.003, 'lamp_lens')
    # the spotlight's inside handle on the driver's A-pillar (the lamp is outside, see Trim): a chrome stem through the pillar, a black grip
    m.cyl(V3((0.18, 0.76, 1.12)), V3((0.04, 0.70, 1.10)), 0.008, 'chrome', seg=8)
    m.rbox(V3((0.0, 0.69, 1.095)), (0.05, 0.035, 0.03), 0.01, 'black')
    ob = m.finish('Interior', root, sharp=40)
    B.metres_uv(ob, ('seatcloth',))
    return ob


# ---- the dash --------------------------------------------------------------------------------------------------------------------------------------------------------------------
def build_dash(B, CK, Mesh, root):
    m = Mesh()
    Y = 0.80
    prof = [(0.95, 0.90), (0.70, 0.925), (0.52, 0.915), (0.445, 0.895), (0.425, 0.865), (0.425, 0.80), (0.432, 0.72), (0.455, 0.64), (0.50, 0.585), (0.60, 0.56), (0.90, 0.62)]
    rings = []
    for k in range(0, 33):
        y = -Y + 2 * Y * k / 32
        e = max(0.0, abs(y) - 0.70) / 0.10                                       # the ends curve away into the door pillars
        rings.append([V3((px + 0.05 * e * e, y, pz - 0.015 * e * e)) for px, pz in prof])
    m.loft(rings, 'dash', closed=True, caps=True)
    # the padded top: a thin cover over the pad (an 'interior' vinyl) with the defroster grille in front
    m.rbox(V3((0.72, 0.0, 0.917)), (0.40, 1.50, 0.012), 0.004, 'interior')
    for k in range(9):
        m.rbox(V3((0.88, -0.70 + 0.175 * k, 0.926)), (0.045, 0.14, 0.004), 0.001, 'black')
    # the cluster: a rectangular pod in front of the dash face under a hood, a satin frame round the face (the 'gauges' picture), no lens (it would hide the face in the game)
    cy = 0.37
    m.rbox(V3((0.445, cy, 0.948)), (0.15, 0.66, 0.040), 0.015, 'dash')
    m.rbox(V3((0.43, cy, 0.845)), (0.03, 0.66, 0.15), 0.01, 'dash')
    for dy in (-0.315, 0.315):
        m.rbox(V3((0.411, cy + dy, 0.845)), (0.012, 0.02, 0.14), 0.004, 'bezel')
    for z in (0.775, 0.915):
        m.rbox(V3((0.411, cy, z)), (0.012, 0.65, 0.016), 0.004, 'bezel')
    m.box(V3((0.4135, cy, 0.845)), (0.002, 0.61, 0.125), 'gauges')
    # the driver's vents at the outer end of the dash, the passenger's at both ends of the right half
    for y in (0.68, 0.755):
        _vent(m, y, 0.84)
    for y in (-0.22, -0.74):
        _vent(m, y, 0.82)
    # the centre stack: radio (AM/FM, two knobs, push buttons, dial), heater and air conditioning controls (levers and knobs), ashtray and lighter
    cx = -0.03
    m.rbox(V3((0.4285, cx, 0.775)), (0.014, 0.19, 0.075), 0.006, 'radio')
    m.box(V3((0.4205, cx, 0.785)), (0.003, 0.115, 0.022), 'gauge')
    for y in (cx - 0.07, cx + 0.07):
        m.cyl(V3((0.4285, y, 0.768)), V3((0.405, y, 0.768)), 0.011, 'chrome', seg=12)
    for k in range(5):
        m.rbox(V3((0.4225, cx - 0.06 + 0.03 * k, 0.755)), (0.006, 0.018, 0.010), 0.002, 'chrome')
    m.rbox(V3((0.4285, cx, 0.695)), (0.014, 0.19, 0.06), 0.006, 'bezel')
    for k in range(3):
        m.box(V3((0.4225, cx - 0.06 + 0.04 * k, 0.705)), (0.004, 0.006, 0.035), 'black')
        m.rbox(V3((0.4195, cx - 0.06 + 0.04 * k, 0.705 - 0.01 * k)), (0.009, 0.018, 0.012), 0.003, 'chrome')
    for y in (cx + 0.065, cx + 0.09):
        m.cyl(V3((0.4285, y, 0.675)), V3((0.409, y, 0.675)), 0.009, 'black', seg=10)
    m.rbox(V3((0.4285, cx, 0.625)), (0.014, 0.19, 0.05), 0.006, 'bezel')
    m.cyl(V3((0.4285, cx - 0.05, 0.625)), V3((0.405, cx - 0.05, 0.625)), 0.011, 'black', seg=10)
    m.rbox(V3((0.42, cx + 0.02, 0.625)), (0.006, 0.08, 0.018), 0.004, 'black')
    # the glove box: lid, latch, the shadow gap round it
    m.rbox(V3((0.4375, -0.50, 0.70)), (0.016, 0.50, 0.15), 0.01, 'interior')
    m.rbox(V3((0.427, -0.50, 0.745)), (0.012, 0.07, 0.016), 0.004, 'chrome')
    # the lower panel under the cluster: a knee bolster, a trunk release lever at its foot (the car had it low on the driver's side of the dash), a pull knob
    m.rbox(V3((0.485, 0.40, 0.605)), (0.05, 0.62, 0.07), 0.015, 'dash')
    m.rbox(V3((0.45, 0.66, 0.605)), (0.03, 0.045, 0.03), 0.006, 'black')
    m.cyl(V3((0.45, 0.66, 0.605)), V3((0.40, 0.66, 0.600)), 0.007, 'black', seg=8)
    for y in (0.58, 0.50):
        m.cyl(V3((0.435, y, 0.74)), V3((0.405, y, 0.74)), 0.012, 'chrome', seg=12)
        m.cyl(V3((0.405, y, 0.74)), V3((0.395, y, 0.74)), 0.016, 'black', seg=12)
    # the steering column's shroud (a tapering cover from the dash to the wheel) and the ignition lock ring on its right side
    hub = HUB
    ax = AXIS
    m.cyl(hub - ax * 0.05, hub - ax * 0.30, 0.038, 'dash', seg=20, r1=0.050)
    m.cyl(hub - ax * 0.30, hub - ax * 0.50, 0.050, 'dash', seg=20, r1=0.075)
    c = hub - ax * 0.22 + V3((0, -0.045, -0.01))
    m.cyl(c, c + V3((0.0, -0.014, 0)), 0.014, 'chrome', seg=14)
    # the column's shift lever (right of the column, a chrome stem and a black knob) and the turn signal / wiper stalk (left, a chrome stem with a black end)
    lev0 = hub - ax * 0.20 + V3((0, -0.05, -0.005))
    m.tube([lev0, lev0 + V3((-0.02, -0.12, -0.02)), lev0 + V3((-0.05, -0.19, -0.04))], 0.006, 'chrome', seg=6)
    m.rbox(lev0 + V3((-0.055, -0.205, -0.045)), (0.03, 0.045, 0.022), 0.008, 'black')
    st = hub - ax * 0.17 + V3((0, 0.05, 0.005))
    m.tube([st, st + V3((-0.01, 0.10, 0.0)), st + V3((-0.02, 0.17, 0.01))], 0.005, 'chrome', seg=6)
    m.rbox(st + V3((-0.02, 0.175, 0.01)), (0.014, 0.05, 0.014), 0.005, 'black')
    ob = m.finish('Dash', root, sharp=38)
    CK.planar_uv(ob, 'gauges', axes='yz', flip_u=True)
    return ob


def _vent(m, y, z):
    m.rbox(V3((0.4295, y, z)), (0.012, 0.062, 0.05), 0.005, 'bezel')
    m.rbox(V3((0.4225, y, z)), (0.003, 0.050, 0.038), 0.002, 'black')
    for k in range(4):
        m.rbox(V3((0.4195, y, z - 0.014 + 0.0093 * k)), (0.003, 0.050, 0.0035), 0.001, 'bezel')


# ---- the steering wheel ----------------------------------------------------------------------------------------------------------------------------------------------------------
def build_wheel(B, CK, Mesh, root):
    """A two-spoke wheel with the large rectangular horn pad (the horn moved to the hub in 1985; Wikipedia), a vinyl rim. Its origin is the hub; the wheel turns about AXIS."""
    m = Mesh()
    hub, ax = HUB, AXIS
    u = V3((0, 1, 0))
    w = ax.cross(u).normalized()
    R = 0.19
    n = 72
    m.tube([hub + (u * math.cos(2 * math.pi * k / n) + w * math.sin(2 * math.pi * k / n)) * R for k in range(n)],
           [0.0155 + 0.0012 * math.cos(8 * 2 * math.pi * k / n) for k in range(n)], 'black', seg=14, loop=True)
    # two spokes a little below the horizontal, each a flat strap blending into the rim
    for sgn in (1, -1):
        d = (u * sgn * math.cos(math.radians(-12)) + w * math.sin(math.radians(-12)))
        pts = [hub + d * 0.05, hub + d * 0.11, hub + d * 0.17, hub + d * (R - 0.005)]
        m.tube(pts, [0.017, 0.015, 0.013, 0.014], 'dash', seg=10)
    # the horn pad: a wide rounded rectangle with a blue oval badge (no lettering)
    m.rbox(hub + ax * 0.018, (0.17, 0.115, 0.045), 0.02, 'dash', (u, w, ax))
    m.rbox(hub + ax * 0.043, (0.034, 0.016, 0.004), 0.006, 'badge', (u, w, ax))
    m.cyl(hub - ax * 0.02, hub - ax * 0.05, 0.05, 'dash', seg=16)
    ob = m.finish('SteeringWheel', root, sharp=40, origin=hub)
    return ob

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
        m.rbox(f1 - ex * 0.006 - ez * 0.012 + ey * (-0.06 + 0.026 * k), (0.008, 0.018, 0.012), 0.002, 'bezel', (ex, ey, ez))
    for y in (-0.068, 0.0):
        m.cyl(f1 + ey * y + ez * 0.010, f1 + ey * y + ez * 0.010 - ex * 0.018, 0.009, 'black', seg=12)
    # the siren / lights console, lower unit: a slide volume control, rocker switches, a blue pilot light
    c2 = V3((0.30, 0, 0.505))
    m.rbox(c2, (0.10, 0.19, 0.06), 0.008, 'radio', (ex, ey, ez))
    f2 = c2 - ex * 0.051
    m.rbox(f2, (0.004, 0.175, 0.048), 0.004, 'black', (ex, ey, ez))
    m.box(f2 - ex * 0.004 + ez * 0.012 + ey * 0.045, (0.003, 0.06, 0.005), 'bezel', (ex, ey, ez))
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
        m.rbox(sc - V3((0.068, -0.03 + 0.012 * k, 0.012)), (0.006, 0.008, 0.007), 0.001, 'bezel')
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
        for a, b, bulge in ((ws, fr, 0.022), (fd, rf, 0.018), (rd, bl, 0.022)):
            rows = []
            for pa, pb in zip(a, b):
                if pa is None or pb is None:
                    continue
                inn = V3((0, -s, 0))
                rows.append([pa.lerp(pb, j / 6) + inn * (0.010 + bulge * math.sin(math.pi * j / 6)) for j in range(7)])
            if len(rows) >= 3:
                m.grid(rows, 'interior')
                m.grid([list(reversed(r)) for r in rows], 'interior')
    return m.finish('PillarTrim', root, sharp=50)


# ---- door cards: what the driver sees of the door's inner panel ---------------------------------------------------------------------------------------------------------------------
def build_door_cards(B, Mesh, root):
    """The 1983-87 door trim panel seen in the Curbside Classic photograph: a long horizontal pull strap with chrome end caps, an armrest with a chrome switch plate, a carpeted
    lower band, a stitched upper bolster. Each door's card is a child of its door node, so it opens and falls off with the door."""
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
            for xe in (x0 + 0.10, x1 - 0.12):
                m.rbox(V3((xe, y - s * 0.010, 0.80)), (0.035, 0.012, 0.022), 0.005, 'chrome')
            m.tube([V3((x0 + 0.12, y - s * 0.018, 0.80)), V3((xm, y - s * 0.032, 0.795)), V3((x1 - 0.14, y - s * 0.018, 0.80))], 0.011, 'interior', seg=8)
            m.rbox(V3((xm + 0.06, y - s * 0.03, 0.708)), (0.14, 0.05, 0.006), 0.002, 'chrome')
            for j in range(4 if front else 2):
                m.rbox(V3((xm + 0.02 + 0.025 * j, y - s * 0.03, 0.713)), (0.012, 0.02, 0.006), 0.002, 'black')
            m.rbox(V3((xm, y - s * 0.004, 0.90)), (x1 - x0 - 0.02, 0.012, 0.05), 0.008, 'interior')
            m.rbox(V3((xm, y - s * 0.002, 0.43)), (x1 - x0 - 0.04, 0.006, 0.14), 0.004, 'carpet')
            ob = m.finish('DoorCard_' + k, None, sharp=40)
            mw = ob.matrix_world.copy()
            ob.parent = door
            ob.matrix_parent_inverse = door.matrix_world.inverted()
            ob.matrix_world = mw
            B.metres_uv(ob, ('carpet',))
