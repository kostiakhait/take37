# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""The shape of the 1987 Ford LTD Crown Victoria sedan read off its drawing (pure python; imported by build_crownvic.py inside Blender and by livery.py outside it).

Source: reference/ltd_crown_victoria_1986_outlines.png (Outlines, getoutlines.com, "1986 Ford LTD Crown Victoria Sedan", CC BY 4.0): a front and a right side view (the nose to the right), 1139 x 229 px. The 1983-87
sedans share the body; the 1988 restyle changed the nose and the tail.

Scale. The drawing has no dimension line and is about 1.5 % out against the listed sizes, so every listed size is honoured and the drawing gives the shape between them:
  X (length): the axles at px 546.5 and 985.0 are put at the listed wheelbase 114.3 in (2.903 m, 151.05 px/m); the overhangs (px 333 -> 546.5 and 985 -> 1131) are scaled together to the
              listed overall length 211.0 in (5.359 m), 146.4 px/m.
  Z (height): the ground line at px row 223 and the roof at row 3.5 are put at the listed height 55.6 in (1.412 m): 155.7 px/m.
  Y (width):  the front view's body (px 11.7 -> 312) at the listed width 77.5 in (1.969 m): 152.4 px/m; its centre line at px 161.9.
Track 62.2 in front, 62.0 in rear (listed); the drawing gives 1.61 m. The tyre: P215/70R15 (radius 0.341 m; the drawing gives 0.345 m and a 0.22 m section).

Frame: origin on the ground at the middle of the wheelbase, nose +X, up +Z, the driver's (left) side +Y. The drawing's side view shows the right side (-Y).
"""
import math

# ---- the drawing -> metres -------------------------------------------------------------------------------------------------------------------------------------------------
AX_R, AX_F = 546.5, 985.0                       # the axles' pixel columns
K_WB = (AX_F - AX_R) / 2.903                    # 151.05 px/m inside the wheelbase
K_OH = ((AX_R - 333.0) + (1131.0 - AX_F)) / (5.359 - 2.903)    # 146.4 px/m on the overhangs
HWB = 2.903 / 2
K_Z = (223.0 - 3.5) / 1.412                     # 155.5 px/m
K_Y = (312.0 - 11.7) / 1.969
FRONT_CY = 161.9


def X(px):
    """A side-view pixel column -> X in metres."""
    if px < AX_R:
        return -HWB - (AX_R - px) / K_OH
    if px > AX_F:
        return HWB + (px - AX_F) / K_OH
    return (px - (AX_R + AX_F) / 2) / K_WB


def Z(py):
    """A pixel row (side or front view) -> Z in metres above the ground."""
    return (223.0 - py) / K_Z


def Yf(px):
    """A front-view pixel column -> |Y| in metres from the centre line."""
    return abs(px - FRONT_CY) / K_Y


def interp(pts, x):
    """Piecewise-linear through (x, y) pairs sorted by x, clamped at the ends."""
    if x <= pts[0][0]:
        return pts[0][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x <= x1:
            t = (x - x0) / (x1 - x0) if x1 > x0 else 0.0
            return y0 + (y1 - y0) * t
    return pts[-1][1]


def smooth(pts, x, h=0.05):
    """interp() averaged over +-h (a box filter), so the piecewise lines read off pixels lose their kinks."""
    n = 6
    return sum(interp(pts, x + h * (2 * k / n - 1)) for k in range(n + 1)) / (n + 1)


def M(pairs):
    """Pixel pairs (column, row) -> (X, Z) pairs in metres."""
    return [(X(a), Z(b)) for a, b in pairs]


# ---- the main sizes ---------------------------------------------------------------------------------------------------------------------------------------------------------
LENGTH, WIDTH, HEIGHT, WHEELBASE = 5.359, 1.969, 1.412, 2.903
TRACK_F, TRACK_R = 62.2 * 0.0254, 62.0 * 0.0254
R_TYRE = 0.341                                   # P215/70R15: 15 in rim + 2 x 70 % of 215 mm
W_TYRE = 0.215
R_RIM = 15 * 0.0254 / 2
ZC = R_TYRE                                      # the axle height (unladen, tyre touching z = 0)
W = WIDTH / 2                                    # the half width of the body at the shoulder crease

X_TAIL = X(359.0)                                # the tail panel (behind it only the bumper)
X_NOSE = X(1112.0)                               # the grille / header face
X_RBUMP = X(333.0)                               # the bumpers' outer faces
X_FBUMP = X(1131.0)

# the side silhouette's top: the deck, the backlight, the roof, the windscreen, the cowl and the hood (px)
TOP_PX = [(359, 81), (365, 80), (380, 76), (410, 72), (440, 68.5), (470, 66), (495, 64), (515, 50), (530, 39), (545, 29), (560, 20), (575, 9.5), (590, 6), (605, 5), (650, 4),
          (700, 3.5), (760, 4), (790, 5), (803, 7), (815, 18), (830, 29), (845, 40), (860, 50), (875, 61), (890, 71), (893, 72), (905, 72.5), (950, 74), (1000, 76.5), (1050, 81),
          (1090, 86.5), (1105, 90), (1112, 92)]
TOP = M(TOP_PX)
X_BACKLIGHT_BASE, X_ROOF_REAR, X_ROOF_FRONT, X_COWL = X(495), X(588), X(804), X(893)
Z_ROOF = Z(3.5)
Z_BELT = Z(77.5)                                 # the window sill (belt) line
Z_CREASE_REAR = Z(89.0)                          # the shoulder crease along the deck and the doors
Z_CREASE_FRONT = Z(101.0)                        # ... falling forward along the front fender to the nose

# the bottom edge of the body side (the rocker and the lower quarters), px
BOTTOM_PX = [(359, 172), (380, 172.5), (470, 174), (500, 180), (560, 187), (900, 187), (950, 182), (1060, 171), (1112, 173)]
BOTTOM = M(BOTTOM_PX)

# the wheel openings, read round the arch from the lower rear corner over the top to the lower front corner (px)
ARCH_R_PX = [(480, 174), (484, 150), (491, 133), (503, 121), (520, 113), (546, 109.5), (570, 111), (590, 117), (604, 127), (611, 143), (614, 162), (615, 182)]
ARCH_F_PX = [(927, 187), (929, 160), (934, 136), (945, 121), (962, 112.5), (985, 109.5), (1010, 110), (1032, 114), (1046, 123), (1052, 140), (1055, 160), (1056, 172)]
ARCH_R = M(ARCH_R_PX)
ARCH_F = M(ARCH_F_PX)

# the side glass (px); the openings in the body are these outlines, the glass reaches 8 mm under the frame
WIN_FRONT_PX = [(728, 77.5), (881, 77.5), (812.5, 18.5), (728, 18.5)]
WIN_REAR_PX = [(633, 77.5), (701, 77.5), (701, 18.5), (633, 18.5)]
WIN_VENT_PX = [(590, 77.5), (624, 77.5), (624, 22.5)]
# the windscreen seen from the front (front view px rows; half widths in metres) and the backlight (estimated from the 1986 Marion County photo: the drawing has no rear view)
WS = {'z0': Z(68.0), 'z1': Z(18.0), 'y0': Yf(55.0), 'y1': Yf(85.0)}
BL = {'z0': Z(60.0), 'z1': Z(10.0), 'y0': 0.64, 'y1': 0.50}

# the greenhouse's section (front view): the A-pillar leans in from the cowl (px 33 at row 68) to the roof's edge (px 72 at row 12, half width 0.607 m); carried down that line to the belt the
# side glass stands at a half width of 0.88 m, which the 7126 photograph agrees with (the stripe's top reaches the window sill: there is no flat ledge outside the glass)
GH_Y_ROOF = Yf(72.0)
GH_Y_BELT = Yf(33.0) + (Yf(33.0) - GH_Y_ROOF) * (Z(68.0) - Z(77.5)) / (Z(12.0) - Z(68.0))
GH_Z_ROOF_EDGE = Z(12.0)


def gh_side_y(z):
    """The half width of the greenhouse at the height z (the side glass's plane)."""
    t = (z - Z_BELT) / (GH_Z_ROOF_EDGE - Z_BELT)
    return GH_Y_BELT + (GH_Y_ROOF - GH_Y_BELT) * t


# the doors' and lids' cut lines (px; the drawing's lines)
DOOR_F_FRONT_PX = [(893, 78), (891, 110), (889, 140), (885, 165), (882, 180)]
DOOR_SPLIT_PX = [(725.5, 78), (725.5, 180)]
DOOR_R_REAR_PX = [(581, 78), (581, 104), (588, 112), (600, 119), (608, 128), (612, 142), (614, 160), (615, 180)]
Z_DOOR_BOTTOM = Z(180.0)
HANDLE_F_PX, HANDLE_R_PX = (754, 91), (608, 91)       # the pull handles' centres
LOCK_PX = (733, 93)
FUEL_PX = (475, 85, 500, 109)                          # the fuel filler door (right rear quarter: the drawing shows the right side)
MARKER_R_PX = (361, 103, 373, 125)                     # the red rear side marker
MARKER_F_PX = (1100, 103, 1112, 133)                   # the amber front side marker (wraps round the corner)
MOLDING_Z = (Z(162.0), Z(150.0))                       # the bright lower body moulding, bottom and top
MOLDING_SEGS_PX = [(383, 476), (618, 924), (1060, 1105)]
SIDE_MOLD_Z = Z(122.5)                                 # the thin body side moulding at mid door
SIDE_MOLD_SEGS_PX = [(373, 479), (616, 926), (1057, 1100)]
Y_EDGE = GH_Y_BELT + 0.004                             # where the body's top surface turns down into the shoulder bevel (the glass stands on it)


X_C_PILLAR = X(583.0)                            # the C-pillar's foot: the rear door's window starts here


def top_z(x):
    """The height of the body's top along the centre line: the deck, the hood; under the greenhouse the belt. Beside the C-pillar (backlight base -> rear door) the quarter's top falls
    from the deck's height to the belt in a smooth step, so the shoulder outside the greenhouse has no cliff."""
    if X_C_PILLAR <= x < X_COWL:
        return Z_BELT
    if X_BACKLIGHT_BASE < x < X_C_PILLAR:
        zd = smooth(TOP, X_BACKLIGHT_BASE, 0.03)
        t = (x - X_BACKLIGHT_BASE) / (X_C_PILLAR - X_BACKLIGHT_BASE)
        t = t * t * (3 - 2 * t)
        return zd + (Z_BELT - zd) * t
    return smooth(TOP, x, 0.03)


def roof_z(x):
    """The greenhouse's top along the centre line (the silhouette), from the backlight's base to the cowl."""
    return smooth(TOP, x, 0.025)


def crease_z(x):
    """The shoulder crease: level from the tail to the cowl, falling along the front fender."""
    if x <= X_COWL:
        return Z_CREASE_REAR
    t = (x - X_COWL) / (X_NOSE - X_COWL)
    return Z_CREASE_REAR + (Z_CREASE_FRONT - Z_CREASE_REAR) * t


def bottom_z(x):
    return smooth(BOTTOM, x, 0.08)


def plan_half_width(x, w=W):
    """The body's half width in plan: straight, with the corners rounded at the tail (r 0.07 m) and the nose (r 0.11 m) (estimated from photographs; no top view)."""
    for xe, r, s in ((X_TAIL, 0.07, 1), (X_NOSE, 0.11, -1)):
        d = (x - xe) * s                      # distance inwards from the end
        if d < r:
            d = max(d, 0.0)
            return w - r + math.sqrt(max(r * r - (r - d) ** 2, 0.0))
    return w
