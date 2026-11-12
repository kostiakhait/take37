# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Minivan, American market, 1984-87 look (two swing front doors, a sliding right side door, a rear liftgate, front-drive; no marks, fictional plate).

Drawing: reference/plymouth-voyager-1984-outlines.png (getoutlines.com, 320 x 204 px, right side view; CC BY 4.0). Sizes: Wikipedia, Dodge Caravan (first generation, short wheelbase):
wheelbase 112.1 in, length 175.9 in, width 69.5 in, height 64.4 in.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / '_common'))
from geomkit import Geom  # noqa: E402

IN = 0.0254
NAME = 'minivan'
ROOT = 'Minivan86'
G = Geom(
    NAME=NAME, ROOT=ROOT,
    LENGTH=175.9 * IN, WIDTH=69.5 * IN, HEIGHT=64.4 * IN, WHEELBASE=112.1 * IN,
    TRACK_F=58.0 * IN, TRACK_R=57.5 * IN,
    R_TYRE=0.3166, W_TYRE=0.185, R_RIM=14 * IN / 2,
    ax_r=58.0, ax_f=262.0, row_ground=122.0, row_roof=6.0, px_tail=8.0, px_nose=299.0, px_rbump=4.0, px_fbump=316.0,
    top_px=[(8, 64), (11, 44), (18, 28), (28, 14), (40, 8), (60, 6), (100, 6), (150, 6), (190, 8), (205, 13), (215, 26), (225, 34), (236, 40), (250, 43), (275, 50), (299, 58)],
    bottom_px=[(8, 86), (30, 92), (100, 100), (215, 100), (240, 94), (299, 88)],
    row_belt=47.5, row_crease_rear=60, row_crease_front=62, row_roof_edge=14,
    col_backlight_base=14, col_c_pillar=30, col_roof_rear=36, col_roof_front=198, col_cowl=236,
    tumble_in=0.05, gh_y_roof=0.72,
    ROUND_TAIL=0.08, ROUND_NOSE=0.12, CAB_FLOOR=0.34,
    X_HUMP=(-1.25, -0.55),
    PLATE_TEXT='VAN 6158',
    TYRE_TEXT=[('P185/75R14', 270, 0.55, 0.016), ('STEEL BELTED RADIAL', 90, 0.55, 0.012), ('M+S', 30, 0.35, 0.010), ('TUBELESS', 200, 0.35, 0.008)],
    COLORS=[('beige', (214, 196, 156)), ('burgundy', (104, 30, 42)), ('dark_blue', (30, 44, 90)), ('silver', (178, 180, 182)), ('white', (232, 232, 226)),
            ('brown', (110, 76, 52))],
    DRIVE='fwd', WHEEL_STYLE='cover',
)
g = G
G.SIDE_WINDOWS = {
    'quarter': [(35, 15), (78, 15), (76, 47), (30, 46)],
    'slide': [(90, 15), (150, 15), (150, 47), (87, 47)],
    'front': [(160, 14), (197, 15), (224, 45), (160, 47)],
}
G.WINDOW_OWNER = {'quarter': False}
G.WINDOW_SIDES = {'slide': (1, -1)}
G.WS = dict(z0=g.Z(40.0) + 0.02, z1=g.Z(10.0), y0=0.66, y1=0.56, x0=0.05, x1=g.X_COWL - 0.004)
G.BL = dict(z0=g.Z(58.0), z1=g.Z(15.0), y0=0.52, y1=0.48, x0=g.X(4), x1=g.X(40), owner='Liftgate')
G.X_GH0 = g.X(14) - 0.02
G.CABIN_X0 = g.X_TAIL + 0.07
G.CABIN_X1 = g.X_COWL - 0.03
G.CAVITIES = [dict(x0=g.X_COWL + 0.05, x1=g.X_NOSE - 0.05, y=0.52, z0=0.32, off=0.045)]
G.ARCH_Y = g.W - 0.27
G.DOORS = {
    'F': dict(lower=[(153, 48), (232, 48), (236, 70), (234, 100), (153, 100)], wins=[[(160, 14), (197, 15), (224, 45), (160, 47)]], bottom_row=100, hinge_col=232, hinge_dx=-0.004,
              latch_col=155, handle=(170, 56), lock=(176, 59), mirror=228),
    'S': dict(sides=(-1,), lower=[(86, 48), (153, 48), (153, 100), (100, 100), (92, 78)], wins=[[(90, 15), (150, 15), (150, 47), (87, 47)]], bottom_row=100, hinge_col=153,
              hinge_dx=-0.004, latch_col=88, handle=(100, 56), lock=None),
}
G.PANELS = [
    dict(name='Hood', kind='top', poly=[(g.X_COWL + 0.012, -0.78), (g.X_COWL + 0.012, 0.78), (g.X_NOSE + 0.08, 0.70), (g.X_NOSE + 0.08, -0.70)], zlo=0.72,
         pivot=(g.X_COWL + 0.012, 0, 0.98)),
    dict(name='Liftgate', kind='rear', poly=[(g.X(-10), 0.62), (g.X(-10), g.Z(3) + 0.2), (g.X(36), g.Z(3) + 0.2), (g.X(36), 0.62)], y=0.72, pivot=(g.X(36), 0, g.Z(6))),
]
G.TRIM_X0, G.TRIM_X1 = g.X(30), g.X(232)
G.SIDE_STRIPS = [(g.X(12), g.X(232), g.Z(62), 0.04, 0.004, 'woodtrim'), (g.X(12), g.X(232), g.Z(66), 0.012, 0.004, 'chrome'), (g.X(30), g.X(232), g.Z(88), 0.05, 0.005, 'bumper'),
                 (g.X(100), g.X(232), g.Z(100), 0.08, 0.006, 'bumper')]
G.BUMP_F = dict(zt=0.60, zb=0.38, yc=0.60, R=0.15, kind='bumper', depth=0.14, bow=0.02, guard_y=0.5)
G.BUMP_R = dict(zt=0.60, zb=0.38, yc=0.60, R=0.15, kind='bumper', depth=0.14, bow=0.01, guard_y=0.5)
G.GRILLE = dict(y=0.30, z0=0.66, z1=0.80, kind='chrome', nv=13, nh=2)
G.HEAD = dict(lamps=[(0.57, 0.30, 0.14, 0.72)], dx=0.0)
G.PARK = dict(y=0.57, z=0.60, w=0.30, h=0.05)
G.MARK_F = (0.62, 0.74)
G.MARK_R = (0.76, 0.86)
G.TAIL = dict(y=0.66, w=0.16, z0=0.72, z1=1.02, rim='black')
G.PLATE_F = (g.X_FBUMP + 0.001, 0.49)
G.PLATE_R = (g.X_RBUMP - 0.001, 0.49)
G.SEATS = dict(front='bucket', x=0.38, z=0.60, rear=(-0.45, 0.50), rear2=(-1.30, 0.50))
G.CARGO = None
G.STEER = dict(c=(0.80, 0.37, 1.00), tilt=30, r=0.19)
G.SHIFTER = 'none'
G.HANDLE_KIND = 'black'
G.WINDOW_TRIM = 'black'
G.REVEAL = 'black'
