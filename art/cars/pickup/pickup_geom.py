# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Full-size pickup truck, American market, 1987 look (regular cab, short bed, rear-drive; no marks, fictional plate).

Drawing: reference/ford-f-150-1987-outlines.png (getoutlines.com, 327 x 428 px, the upper side view; CC BY 4.0). Sizes: Wikipedia, Ford F-Series (eighth generation): wheelbase 117 in,
length 194.1 in (regular cab, 6.75 ft box), width 79 in; the height is not listed there, it is taken from the drawing's proportions (1.78 m, drawing 1.77 m at the listed length).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / '_common'))
from geomkit import Geom  # noqa: E402

IN = 0.0254
NAME = 'pickup'
ROOT = 'Pickup87'
G = Geom(
    NAME=NAME, ROOT=ROOT,
    LENGTH=194.1 * IN, WIDTH=79.0 * IN, HEIGHT=1.78, WHEELBASE=117.0 * IN,
    TRACK_F=1.70, TRACK_R=1.69,
    R_TYRE=0.3858, W_TYRE=0.235, R_RIM=15 * IN / 2,
    ax_r=80.0, ax_f=273.0, row_ground=114.0, row_roof=3.5, px_tail=12.0, px_nose=312.0, px_rbump=8.0, px_fbump=320.0,
    top_px=[(12, 40), (20, 39.3), (60, 38.6), (120, 38.2), (150, 37.8), (153, 34), (155, 12), (158, 6), (165, 3.8), (172, 3.5), (195, 3.5), (203, 5), (215, 16), (228, 28), (232, 30),
            (240, 31), (260, 31.5), (285, 32.5), (300, 34), (308, 37), (312, 41)],
    bottom_px=[(12, 82), (45, 83), (70, 86), (95, 88), (255, 88), (285, 84), (312, 80)],
    row_belt=36.5, row_crease_rear=52, row_crease_front=52, row_roof_edge=7,
    col_backlight_base=150, col_c_pillar=153, col_roof_rear=158, col_roof_front=205, col_cowl=232,
    tumble_in=0.085, gh_y_roof=0.80,
    ROUND_TAIL=0.05, ROUND_NOSE=0.10,
    CAB_FLOOR=0.52, CAB_Y=0.84, HUMP_Y=0.84,
    PLATE_TEXT='TRK 7391',
    TYRE_TEXT=[('P235/75R15', 270, 0.55, 0.018), ('ALL SEASON', 90, 0.55, 0.014), ('M+S', 30, 0.35, 0.010), ('TUBELESS', 200, 0.35, 0.008)],
    COLORS=[('two_tone_blue', (34, 52, 98)), ('red', (150, 28, 26)), ('white', (232, 232, 226)), ('brown_metallic', (92, 62, 44)), ('light_blue', (110, 150, 184)),
            ('forest_green', (38, 72, 56))],
    LUGS=5, PCD=0.0572, DRIVE='rwd', WHEEL_STYLE='slot',
)
g = G
G.SIDE_WINDOWS = {'door': [(170, 10), (200, 10), (216, 36), (170, 36)]}
G.WS = dict(z0=g.Z(31.0) + 0.02, z1=g.Z(6.5), y0=0.78, y1=0.70, x0=0.05, x1=g.X_COWL - 0.004)
G.BL = dict(z0=g.Z(33.0), z1=g.Z(12.0), y0=0.62, y1=0.62, x0=g.X(151) - 0.02, x1=g.X(151) + 0.22)
G.X_GH0 = g.X(150) - 0.03
G.CABIN_X0 = g.X(156) + 0.08
G.CABIN_X1 = g.X_COWL - 0.03
bed_x0 = g.X(158) + 0.03
bed_x1 = g.X_TAIL + 0.075
fl = 0.80
G.CAVITIES = [
    dict(x0=g.X_COWL + 0.05, x1=g.X_NOSE - 0.05, y=0.56, z0=0.40, off=0.045),
    dict(box=(bed_x0, -g.HWB - 0.46, -0.87, 0.87, fl, 2.2)),
    dict(box=(-g.HWB - 0.46, -g.HWB + 0.46, -0.62, 0.62, fl, 2.2)),
    dict(box=(-g.HWB + 0.46, bed_x1, -0.87, 0.87, fl, 2.2)),
]
G.ARCH_Y = 0.72
G.DOORS = {
    'F': dict(lower=[(156, 36.5), (230, 36.5), (230, 86), (156, 86)], wins=[[(170, 10), (200, 10), (216, 36), (170, 36)]], bottom_row=86, hinge_col=230, hinge_dx=-0.004, latch_col=157,
              handle=(214, 45), lock=(218, 47), mirror=214),
}
G.PANELS = [
    dict(name='Hood', kind='top', poly=[(g.X_COWL + 0.012, -0.92), (g.X_COWL + 0.012, 0.92), (g.X_NOSE + 0.08, 0.84), (g.X_NOSE + 0.08, -0.84)], zlo=0.80,
         pivot=(g.X_COWL + 0.012, 0, 1.0)),
    dict(name='Tailgate', kind='rear', poly=[(g.X_TAIL - 0.10, 0.60), (g.X_TAIL + 0.05, 0.60), (g.X_TAIL + 0.05, 1.26), (g.X_TAIL - 0.10, 1.26)], y=0.87,
         pivot=(g.X_TAIL, 0, 0.62)),
]
G.TRIM_X0, G.TRIM_X1 = g.X(158), g.X(228)
G.SIDE_STRIPS = [(g.X(14), g.X(150), g.Z(72), 0.05, 0.006, 'chrome'), (g.X(158), g.X(228), g.Z(72), 0.05, 0.006, 'chrome'), (g.X(110), g.X(228), g.Z(86), 0.07, 0.006, 'chrome')]
G.BUMP_F = dict(zt=0.70, zb=0.52, yc=0.80, R=0.10, kind='chrome', depth=0.12, bow=0.015, guard_y=0.62)
G.BUMP_R = dict(zt=0.72, zb=0.54, yc=0.80, R=0.10, kind='chrome', depth=0.12, bow=0.0, rub=False, guard_y=0.7)
G.GRILLE = dict(y=0.50, z0=0.72, z1=0.97, kind='black', nv=11, nh=4, frame='chrome')
G.HEAD = dict(lamps=[(0.745, 0.26, 0.14, 0.88)], dx=0.0)
G.PARK = dict(y=0.745, z=0.735, w=0.26, h=0.05)
G.MARK_F = (0.78, 0.86)
G.MARK_R = (0.8, 0.9)
G.TAIL = dict(y=0.86, w=0.09, z0=0.70, z1=0.99, rim='black')
G.PLATE_F = (g.X_FBUMP + 0.001, 0.61)
G.PLATE_R = (g.X_RBUMP - 0.001, 0.63)
G.SEATS = dict(front='bench', x=0.30, z=0.64, rear=None)
G.STEER = dict(c=(0.66, 0.38, 1.08), tilt=22, r=0.20)
G.SHIFTER = 'floor'
G.HANDLE_KIND = 'chrome'
G.WINDOW_TRIM = 'black'
G.REVEAL = 'chrome'
G.ENGINE_X = g.X_NOSE - 0.6
G.X_HUMP = (1.0, 0.0)
