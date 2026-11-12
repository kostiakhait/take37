# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Compact five-door hatchback, American market, 1981-87 look (front-drive; no marks, fictional plate).

Drawing: reference/ford-escort-mk-iii-5-door-1980-outlines.png (getoutlines.com, 500 x 385 px, side view top; CC BY 4.0). Sizes: Wikipedia, Ford Escort (North America, first
generation): wheelbase 94.2 in, length 169.4 in, width 65.9 in, height 53.7 in (hatchback).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / '_common'))
from geomkit import Geom  # noqa: E402

IN = 0.0254
NAME = 'hatchback'
ROOT = 'Hatchback85'
G = Geom(
    NAME=NAME, ROOT=ROOT,
    LENGTH=169.4 * IN, WIDTH=65.9 * IN, HEIGHT=53.7 * IN, WHEELBASE=94.2 * IN,
    TRACK_F=54.7 * IN, TRACK_R=55.0 * IN,
    R_TYRE=0.2970, W_TYRE=0.165, R_RIM=13 * IN / 2,
    ax_r=95.0, ax_f=400.0, row_ground=163.0, row_roof=11.0, px_tail=12.0, px_nose=472.0, px_rbump=5.0, px_fbump=487.0,
    top_px=[(12, 62), (25, 60), (43, 58), (60, 47), (80, 32), (100, 19), (112, 13), (135, 11), (200, 11), (260, 12), (280, 15), (300, 28), (320, 46), (335, 58), (360, 63), (400, 72),
            (440, 80), (472, 90)],
    bottom_px=[(12, 118), (40, 130), (60, 138), (150, 148), (330, 148), (440, 140), (472, 130)],
    row_belt=70.5, row_crease_rear=82, row_crease_front=84, row_roof_edge=22,
    col_backlight_base=22, col_c_pillar=60, col_roof_rear=112, col_roof_front=270, col_cowl=335,
    tumble_in=0.06, gh_y_roof=0.58,
    ROUND_TAIL=0.06, ROUND_NOSE=0.10, CAB_FLOOR=0.30,
    X_HUMP=(-1.15, -0.55),
    PLATE_TEXT='HCH 9046',
    TYRE_TEXT=[('P165/80R13', 270, 0.55, 0.015), ('STEEL BELTED RADIAL', 90, 0.55, 0.011), ('M+S', 30, 0.35, 0.010)],
    COLORS=[('red', (158, 30, 28)), ('white', (232, 232, 226)), ('light_blue', (108, 146, 182)), ('silver', (176, 178, 180)), ('yellow', (214, 178, 52)),
            ('dark_green', (34, 64, 50))],
    DRIVE='fwd', WHEEL_STYLE='dogdish', LUGS=4, PCD=0.050,
)
g = G
G.SIDE_WINDOWS = {
    'front': [(215, 21), (267, 21), (325, 70), (215, 70)],
    'rear': [(147, 21), (203, 21), (203, 70), (143, 70)],
    'quarter': [(70, 66), (126, 24), (134, 28), (135, 68)],
}
G.WINDOW_OWNER = {'quarter': False}
G.WS = dict(z0=g.Z(58.0) + 0.02, z1=g.Z(14.0), y0=0.58, y1=0.50, x0=0.05, x1=g.X_COWL - 0.004)
G.BL = dict(z0=g.Z(57.0), z1=g.Z(15.0), y0=0.52, y1=0.46, x0=g.X(25), x1=g.X(125), owner='Hatch')
G.X_GH0 = g.X(22) - 0.03
G.CABIN_X0 = g.X_TAIL + 0.07
G.CABIN_X1 = g.X_COWL - 0.03
G.CAVITIES = [dict(x0=g.X_COWL + 0.05, x1=g.X_NOSE - 0.05, y=0.48, z0=0.30, off=0.045)]
G.ARCH_Y = g.W - 0.26
G.DOORS = {
    'F': dict(lower=[(212, 71), (335, 71), (338, 100), (340, 148), (214, 148)], wins=[[(215, 21), (267, 21), (325, 70), (215, 70)]], bottom_row=148, hinge_col=338, hinge_dx=-0.004,
              latch_col=214, handle=(228, 82), lock=(234, 85), mirror=330),
    'R': dict(lower=[(138, 71), (212, 71), (214, 148), (138, 148)], wins=[[(147, 21), (203, 21), (203, 70), (143, 70)]], bottom_row=148, hinge_col=212, hinge_dx=-0.004,
              latch_col=140, handle=(160, 82)),
}
G.PANELS = [
    dict(name='Hood', kind='top', poly=[(g.X_COWL + 0.012, -0.72), (g.X_COWL + 0.012, 0.72), (g.X_NOSE + 0.08, 0.64), (g.X_NOSE + 0.08, -0.64)], zlo=0.66, pivot=(g.X_COWL + 0.012, 0, 0.92)),
    dict(name='Hatch', kind='rear', poly=[(g.X(-5), 0.58), (g.X(-5), g.Z(8) + 0.2), (g.X(118), g.Z(8) + 0.2), (g.X(118), 0.58)], y=0.64, pivot=(g.X(118), 0, g.Z(12))),
]
G.TRIM_X0, G.TRIM_X1 = g.X(138), g.X(338)
G.SIDE_STRIPS = [(g.X(140), g.X(338), g.Z(84), 0.012, 0.004, 'black'), (g.X(140), g.X(338), g.Z(120), 0.05, 0.010, 'bumper'), (g.X(110), g.X(338), g.Z(146), 0.07, 0.006, 'bumper')]
G.BUMP_F = dict(zt=0.52, zb=0.34, yc=0.55, R=0.13, kind='bumper', depth=0.12, bow=0.02, guard_y=0.45)
G.BUMP_R = dict(zt=0.52, zb=0.34, yc=0.55, R=0.13, kind='bumper', depth=0.12, bow=0.01, guard_y=0.45)
G.GRILLE = dict(y=0.26, z0=0.58, z1=0.70, kind='black', nv=9, nh=2, frame='chrome')
G.HEAD = dict(lamps=[(0.56, 0.28, 0.12, 0.65)], dx=0.0)
G.PARK = dict(y=0.56, z=0.55, w=0.26, h=0.045)
G.MARK_F = (0.58, 0.66)
G.MARK_R = (0.64, 0.74)
G.TAIL = dict(y=0.58, w=0.22, z0=0.66, z1=0.84, rim='black')
G.PLATE_F = (g.X_FBUMP + 0.001, 0.43)
G.PLATE_R = (g.X_RBUMP - 0.001, 0.43)
G.SEATS = dict(front='bucket', x=-0.10, z=0.44, rear=(-0.80, 0.45))
G.CARGO = (g.X_TAIL + 0.06, -1.15, 0.50, 0.58)
G.STEER = dict(c=(0.36, 0.37, 0.82), tilt=26, r=0.18)
G.SHIFTER = 'console'
G.HANDLE_KIND = 'black'
G.WINDOW_TRIM = 'black'
G.REVEAL = 'black'
