# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Mid-size sedan, American market, 1982-87 look (a four-door front-drive notchback of the period; no marks, fictional plate).

Drawing: reference/oldsmobile-cutlass-ciera-1989-outlines.png (getoutlines.com, 318 x 201 px, side view top-left; CC BY 4.0). Sizes: Wikipedia, Oldsmobile Cutlass Ciera
(wheelbase 104.9 in, length 190.3 in, width 69.5 in, height 54.1 in). Every listed size is honoured, the drawing gives the shape between them (geomkit.py).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / '_common'))
from geomkit import Geom  # noqa: E402

IN = 0.0254
NAME = 'sedan'
ROOT = 'Sedan87'
G = Geom(
    NAME=NAME, ROOT=ROOT,
    LENGTH=190.3 * IN, WIDTH=69.5 * IN, HEIGHT=54.1 * IN, WHEELBASE=104.9 * IN,
    TRACK_F=58.7 * IN, TRACK_R=57.0 * IN,
    R_TYRE=0.3166, W_TYRE=0.185, R_RIM=14 * IN / 2,
    ax_r=70.0, ax_f=252.0, row_ground=97.5, row_roof=4.5, px_tail=12.0, px_nose=300.0, px_rbump=5.0, px_fbump=313.0,
    top_px=[(12, 37), (20, 35.5), (35, 32.5), (50, 30), (53, 28.5), (60, 24), (75, 15), (88, 8.5), (95, 6.2), (110, 5), (150, 4.5), (175, 6), (185, 10), (200, 20), (215, 29),
            (222, 31), (240, 32.5), (260, 34.5), (280, 37), (295, 39.5), (300, 41)],
    bottom_px=[(12, 74), (40, 78), (60, 84), (95, 86), (225, 86), (240, 83), (290, 78), (300, 76)],
    row_belt=32.5, row_crease_rear=41, row_crease_front=42.5, row_roof_edge=10,
    col_backlight_base=52, col_c_pillar=97, col_roof_rear=90, col_roof_front=178, col_cowl=222,
    tumble_in=0.075, gh_y_roof=0.55,
    X_HUMP=(-1.72, -0.95),
    PLATE_TEXT='KXR 482',
    TYRE_TEXT=[('P185/75R14', 270, 0.55, 0.016), ('STEEL BELTED RADIAL', 90, 0.55, 0.012), ('M+S', 30, 0.35, 0.010), ('TUBELESS', 200, 0.35, 0.008)],
    COLORS=[('silver', (176, 178, 180)), ('midnight_blue', (26, 40, 84)), ('maroon', (104, 26, 36)), ('desert_tan', (190, 168, 126)), ('white', (232, 232, 226)),
            ('forest_green', (36, 68, 52))],
)
g = G
G.SIDE_WINDOWS = {'front': [(153, 9), (177, 9), (219, 31.5), (153, 31.5)], 'rear': [(113, 9), (140, 9), (140, 31.5), (95, 31.5)]}
G.WS = dict(z0=g.Z(31.0) + 0.02, z1=g.Z(8.5), y0=0.60, y1=0.52, x0=0.05, x1=g.X_COWL - 0.004)
G.BL = dict(z0=g.Z(33.0), z1=g.Z(9.0), y0=0.58, y1=0.50, x0=g.X(52) + 0.004, x1=g.X(90) + 0.10)
G.CAVITIES = [dict(x0=g.X_COWL + 0.05, x1=g.X_NOSE - 0.05, y=0.53, z0=0.30, off=0.045), dict(x0=g.X_TAIL + 0.06, x1=g.X_BACKLIGHT_BASE - 0.06, y=0.50, z0=0.28, off=0.045)]
G.ARCH_Y = g.W - 0.30
G.DOORS = {
    'F': dict(lower=[(151, 33), (222, 33), (222, 60), (219, 77), (153, 77)], wins=[[(153, 9), (177, 9), (219, 31.5), (153, 31.5)]], bottom_row=77, hinge_col=222, hinge_dx=-0.004,
              latch_col=153, handle=(200, 38.5), lock=(204, 41), mirror=205),
    'R': dict(lower=[(151, 33), (93, 33), (94, 45), (100, 58), (106, 68), (108, 77), (153, 77)], wins=[[(113, 9), (140, 9), (140, 31.5), (95, 31.5)]], bottom_row=77, hinge_col=151,
              hinge_dx=-0.004, latch_col=95, handle=(122, 38.5)),
}
G.PANELS = [
    dict(name='Hood', kind='top', poly=[(g.X_COWL + 0.012, -0.83), (g.X_COWL + 0.012, 0.83), (g.X_NOSE + 0.08, 0.74), (g.X_NOSE + 0.08, -0.74)], zlo=0.78, pivot=(g.X_COWL + 0.012, 0, 0.98)),
    dict(name='Trunk', kind='top', poly=[(g.X_BACKLIGHT_BASE - 0.025, -0.80), (g.X_BACKLIGHT_BASE - 0.025, 0.80), (g.X_TAIL - 0.08, 0.80), (g.X_TAIL - 0.08, -0.80)], zlo=0.80,
         pivot=(g.X_BACKLIGHT_BASE - 0.025, 0, 0.92)),
]
G.TRIM_X0, G.TRIM_X1 = g.X(95), g.X(220)
G.SIDE_STRIPS = [(g.X(100), g.X(220), g.Z(61), 0.045, 0.012, 'bumper'), (g.X(100), g.X(220), g.Z(41), 0.012, 0.004, 'black'), (g.X(110), g.X(221), g.Z(79), 0.09, 0.006, 'bumper')]
G.BUMP_F = dict(zt=0.57, zb=0.37, yc=0.70, R=0.15, kind='paint', depth=0.14)
G.BUMP_R = dict(zt=0.57, zb=0.37, yc=0.70, R=0.15, kind='paint', depth=0.14)
G.GRILLE = dict(y=0.34, z0=0.62, z1=0.79, kind='chrome', nv=17, nh=3)
G.HEAD = dict(lamps=[(0.575, 0.30, 0.10, 0.705)], dx=0.0)
G.PARK = dict(y=0.575, z=0.60, w=0.30, h=0.045)
G.MARK_F = (0.62, 0.74)
G.MARK_R = (0.66, 0.76)
G.TAIL = dict(y=0.62, w=0.38, z0=0.64, z1=0.80, rim='black')
G.PLATE_F = (g.X_FBUMP + 0.001, 0.47)
G.PLATE_R = (g.X_RBUMP - 0.001, 0.47)
G.SEATS = dict(front='bench', x=-0.10, z=0.44, rear=(-0.95, 0.43))
G.STEER = dict(c=(0.52, 0.37, 0.86), tilt=25, r=0.19)
G.SHIFTER = 'none'
G.HANDLE_KIND = 'chrome'
G.WINDOW_TRIM = 'black'
G.REVEAL = 'chrome'
