# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Wood-panel station wagon, American market, 1981-83 look (four doors and a rear tailgate, rear-drive; no marks, fictional plate).

Drawing: reference/chevrolet-malibu-station-wagon-1981-outlines.png (getoutlines.com, 2503 x 780 px side view; CC BY 4.0). Sizes: Wikipedia, Chevrolet Malibu (1978-83 generation,
wagon): wheelbase 108 in, length 193.4 in, width 71.2 in, height 54.5 in. The simulated wood panels use the library's walnut.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / '_common'))
from geomkit import Geom  # noqa: E402

IN = 0.0254
NAME = 'wagon'
ROOT = 'Wagon82'
G = Geom(
    NAME=NAME, ROOT=ROOT,
    LENGTH=193.4 * IN, WIDTH=71.2 * IN, HEIGHT=54.5 * IN, WHEELBASE=108.0 * IN,
    TRACK_F=58.5 * IN, TRACK_R=57.8 * IN,
    R_TYRE=0.3241, W_TYRE=0.195, R_RIM=14 * IN / 2,
    ax_r=628.0, ax_f=2050.0, row_ground=738.0, row_roof=8.0, px_tail=90.0, px_nose=2432.0, px_rbump=15.0, px_fbump=2492.0,
    top_px=[(90, 395), (95, 330), (110, 275), (130, 238), (180, 160), (230, 85), (280, 22), (300, 13), (400, 10), (600, 8), (900, 8), (1200, 9), (1400, 10), (1450, 18), (1480, 34),
            (1600, 100), (1700, 160), (1750, 212), (1765, 222), (1800, 228), (1900, 235), (2000, 242), (2150, 258), (2300, 280), (2400, 295), (2432, 300)],
    bottom_px=[(90, 520), (250, 535), (400, 548), (500, 585), (850, 612), (1780, 612), (1900, 600), (2250, 575), (2432, 545)],
    row_belt=225, row_crease_rear=292, row_crease_front=300, row_roof_edge=55,
    col_backlight_base=100, col_c_pillar=140, col_roof_rear=300, col_roof_front=1440, col_cowl=1765,
    tumble_in=0.06, gh_y_roof=0.66,
    ROUND_TAIL=0.06, ROUND_NOSE=0.10, CAB_FLOOR=0.36,
    X_HUMP=(-1.70, -0.95),
    PLATE_TEXT='WGN 2205',
    TYRE_TEXT=[('P195/75R14', 270, 0.55, 0.016), ('STEEL BELTED RADIAL', 90, 0.55, 0.012), ('M+S', 30, 0.35, 0.010), ('TUBELESS', 200, 0.35, 0.008)],
    COLORS=[('beige', (196, 178, 140)), ('forest_green', (36, 70, 52)), ('brown', (92, 58, 40)), ('light_blue', (120, 152, 182)), ('burgundy', (100, 28, 38)),
            ('white', (232, 232, 226))],
    DRIVE='rwd', WHEEL_STYLE='cover',
)
g = G
G.SIDE_WINDOWS = {
    'quarter': [(325, 66), (790, 58), (740, 220), (243, 214)],
    'vent': [(838, 64), (905, 62), (865, 215), (803, 215)],
    'rear': [(925, 60), (1120, 60), (1150, 225), (880, 225)],
    'front': [(1195, 58), (1420, 58), (1640, 225), (1235, 228)],
}
G.WINDOW_OWNER = {'quarter': False}
G.WS = dict(z0=g.Z(222.0) + 0.02, z1=g.Z(40.0), y0=0.62, y1=0.56, x0=0.05, x1=g.X_COWL - 0.004)
G.BL = dict(z0=g.Z(214.0), z1=g.Z(30.0), y0=0.60, y1=0.54, x0=g.X(95), x1=g.X(330), owner='Tailgate')
G.X_GH0 = g.X(100) - 0.03
G.CABIN_X0 = g.X_TAIL + 0.07
G.CABIN_X1 = g.X_COWL - 0.03
G.CAVITIES = [dict(x0=g.X_COWL + 0.05, x1=g.X_NOSE - 0.05, y=0.55, z0=0.30, off=0.045)]
G.ARCH_Y = g.W - 0.27
G.DOORS = {
    'F': dict(lower=[(1182, 228), (1745, 228), (1762, 420), (1790, 598), (1192, 598)], wins=[[(1195, 58), (1420, 58), (1640, 225), (1235, 228)]], bottom_row=598, hinge_col=1745,
              hinge_dx=-0.004, latch_col=1185, handle=(1250, 295), lock=(1262, 322), mirror=1660),
    'R': dict(lower=[(790, 225), (1182, 225), (1192, 598), (838, 598), (824, 520), (800, 430)], wins=[[(925, 60), (1120, 60), (1150, 225), (880, 225)]], bottom_row=598,
              hinge_col=1182, hinge_dx=-0.004, latch_col=800, handle=(1000, 295), lock=None),
}
G.PANELS = [
    dict(name='Hood', kind='top', poly=[(g.X_COWL + 0.012, -0.80), (g.X_COWL + 0.012, 0.80), (g.X_NOSE + 0.08, 0.70), (g.X_NOSE + 0.08, -0.70)], zlo=0.76,
         pivot=(g.X_COWL + 0.012, 0, 0.98)),
    dict(name='Tailgate', kind='rear', poly=[(g.X(40), 0.64), (g.X(40), g.Z(2) + 0.2), (g.X(330), g.Z(2) + 0.2), (g.X(330), 0.64)], y=0.76,
         pivot=(g.X(40), 0, 0.64)),
]
G.TRIM_X0, G.TRIM_X1 = g.X(800), g.X(1745)
wood_rows = [0.40, 0.47, 0.54, 0.61, 0.68, 0.75, 0.82]
G.SIDE_STRIPS = [(g.X(130), g.X(790), zz, 0.068, 0.004, 'wood') for zz in wood_rows] + [(g.X(800), g.X(1745), zz, 0.068, 0.004, 'wood') for zz in wood_rows]
G.SIDE_STRIPS += [(g.X(130), g.X(1745), 0.355, 0.015, 0.005, 'woodtrim'), (g.X(130), g.X(1745), 0.865, 0.015, 0.005, 'woodtrim'), (g.X(130), g.X(1745), g.Z(618), 0.07, 0.005, 'chrome')]
G.BUMP_F = dict(zt=0.60, zb=0.40, yc=0.62, R=0.15, kind='chrome', depth=0.14, bow=0.025, guard_y=0.5)
G.BUMP_R = dict(zt=0.60, zb=0.40, yc=0.62, R=0.15, kind='chrome', depth=0.14, bow=0.020, guard_y=0.5)
G.GRILLE = dict(y=0.36, z0=0.70, z1=0.86, kind='chrome', nv=19, nh=3)
G.HEAD = dict(lamps=[(0.56, 0.22, 0.11, 0.79), (0.56, 0.22, 0.11, 0.66)], dx=0.0)
G.PARK = dict(y=0.60, z=0.575, w=0.30, h=0.05)
G.MARK_F = (0.64, 0.72)
G.MARK_R = (0.70, 0.78)
G.TAIL = dict(y=0.66, w=0.30, z0=0.66, z1=0.82, rim='chrome')
G.PLATE_F = (g.X_FBUMP + 0.001, 0.50)
G.PLATE_R = (g.X_RBUMP - 0.001, 0.50)
G.SEATS = dict(front='bench', x=0.10, z=0.46, rear=(-0.80, 0.46))
G.CARGO = (g.X_TAIL + 0.10, -1.30, 0.50, 0.62)
G.STEER = dict(c=(0.58, 0.37, 0.88), tilt=24, r=0.19)
G.SHIFTER = 'none'
G.HANDLE_KIND = 'chrome'
G.WINDOW_TRIM = 'chrome'
G.REVEAL = 'chrome'
