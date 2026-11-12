# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Large two-door coupe of the early-80s American "boat" kind (formal roof with an opera window, long hood and deck, rear-drive; no marks, fictional plate).

Drawing: reference/chevrolet-monte-carlo-ss-1986-outlines.png (getoutlines.com, 1888 x 2366 px, the second side view, nose to the right; CC BY 4.0). Sizes: Wikipedia, Chevrolet
Monte Carlo (1980-87): wheelbase 108.0 in, length 200.4 in, width 71.8 in, height 54.0 in. The drawing's lowered stance and oversize wheels are not taken over: stock tyres.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / '_common'))
from geomkit import Geom  # noqa: E402

IN = 0.0254
NAME = 'coupe'
ROOT = 'Coupe84'
G = Geom(
    NAME=NAME, ROOT=ROOT,
    LENGTH=200.4 * IN, WIDTH=71.8 * IN, HEIGHT=54.0 * IN, WHEELBASE=108.0 * IN,
    TRACK_F=58.5 * IN, TRACK_R=57.8 * IN,
    R_TYRE=0.3213, W_TYRE=0.205, R_RIM=14 * IN / 2,
    ax_r=470.0, ax_f=1475.0, row_ground=1555.0, row_roof=1098.0, px_tail=65.0, px_nose=1832.0, px_rbump=34.0, px_fbump=1872.0,
    top_px=[(65, 1262), (90, 1250), (130, 1246), (300, 1241), (440, 1237), (456, 1232), (500, 1170), (540, 1118), (570, 1103), (640, 1099), (800, 1097), (1000, 1099), (1050, 1103),
            (1080, 1114), (1150, 1152), (1230, 1215), (1272, 1240), (1310, 1243), (1400, 1250), (1500, 1258), (1600, 1270), (1700, 1285), (1780, 1300), (1832, 1325)],
    bottom_px=[(65, 1480), (300, 1486), (560, 1490), (1400, 1490), (1700, 1478), (1832, 1450)],
    row_belt=1243, row_crease_rear=1285, row_crease_front=1292, row_roof_edge=1125,
    col_backlight_base=455, col_c_pillar=600, col_roof_rear=545, col_roof_front=1050, col_cowl=1274,
    tumble_in=0.085, gh_y_roof=0.60,
    ROUND_TAIL=0.08, ROUND_NOSE=0.11, CAB_FLOOR=0.34,
    X_HUMP=(-1.75, -1.0),
    PLATE_TEXT='CPE 5518',
    TYRE_TEXT=[('P205/70R14', 270, 0.55, 0.016), ('STEEL BELTED RADIAL', 90, 0.55, 0.012), ('M+S', 30, 0.35, 0.010), ('TUBELESS', 200, 0.35, 0.008)],
    COLORS=[('black', (22, 22, 24)), ('burgundy', (92, 24, 36)), ('silver', (176, 178, 180)), ('dark_blue', (24, 36, 80)), ('gold', (170, 138, 84)), ('white', (232, 232, 226))],
    DRIVE='rwd', WHEEL_STYLE='slot',
)
g = G
G.SIDE_WINDOWS = {
    'door': [(748, 1130), (1045, 1128), (1195, 1240), (748, 1243)],
    'opera': [(640, 1135), (708, 1133), (712, 1240), (603, 1230)],
}
G.WINDOW_OWNER = {'opera': False}
G.WINDOW_SIDES = {}
G.WS = dict(z0=g.Z(1241.0) + 0.02, z1=g.Z(1118.0), y0=0.64, y1=0.54, x0=0.05, x1=g.X_COWL - 0.004)
G.BL = dict(z0=g.Z(1236.0), z1=g.Z(1120.0), y0=0.60, y1=0.50, x0=g.X(455) + 0.004, x1=g.X(560) + 0.10)
G.X_GH0 = g.X(455) - 0.03
G.CABIN_X0 = g.X(455) + 0.10
G.CABIN_X1 = g.X_COWL - 0.03
G.CAVITIES = [dict(x0=g.X_COWL + 0.05, x1=g.X_NOSE - 0.05, y=0.55, z0=0.30, off=0.045), dict(x0=g.X_TAIL + 0.06, x1=g.X(455) - 0.06, y=0.52, z0=0.28, off=0.045)]
G.ARCH_Y = g.W - 0.28
G.DOORS = {
    'F': dict(lower=[(742, 1243), (1262, 1243), (1275, 1330), (1280, 1485), (742, 1485)], wins=[[(748, 1130), (1045, 1128), (1195, 1240), (748, 1243)]], bottom_row=1485, hinge_col=1262,
              hinge_dx=-0.004, latch_col=744, handle=(790, 1272), lock=(808, 1290), mirror=1215),
}
G.PANELS = [
    dict(name='Hood', kind='top', poly=[(g.X_COWL + 0.012, -0.86), (g.X_COWL + 0.012, 0.86), (g.X_NOSE + 0.08, 0.76), (g.X_NOSE + 0.08, -0.76)], zlo=0.80, pivot=(g.X_COWL + 0.012, 0, 0.98)),
    dict(name='Trunk', kind='top', poly=[(g.X(455) - 0.025, -0.84), (g.X(455) - 0.025, 0.84), (g.X_TAIL - 0.08, 0.84), (g.X_TAIL - 0.08, -0.84)], zlo=0.90, pivot=(g.X(455) - 0.025, 0, 0.96)),
]
G.TRIM_X0, G.TRIM_X1 = g.X(742), g.X(1262)
G.SIDE_STRIPS = [(g.X(140), g.X(1262), g.Z(1380), 0.012, 0.004, 'chrome'), (g.X(760), g.X(1262), g.Z(1465), 0.05, 0.006, 'chrome'), (g.X(140), g.X(1262), g.Z(1305), 0.012, 0.004, 'black')]
G.BUMP_F = dict(zt=0.60, zb=0.40, yc=0.62, R=0.15, kind='bumper', depth=0.14, bow=0.03, guard_y=0.5)
G.BUMP_R = dict(zt=0.60, zb=0.40, yc=0.62, R=0.15, kind='bumper', depth=0.14, bow=0.03, guard_y=0.5)
G.GRILLE = dict(y=0.28, z0=0.60, z1=0.79, kind='chrome', nv=15, nh=4)
G.HEAD = dict(lamps=[(0.70, 0.20, 0.09, 0.72), (0.48, 0.20, 0.09, 0.72)], dx=0.0)
G.PARK = dict(y=0.62, z=0.62, w=0.36, h=0.05)
G.MARK_F = (0.64, 0.76)
G.MARK_R = (0.72, 0.82)
G.TAIL = dict(y=0.68, w=0.34, z0=0.68, z1=0.88, rim='black')
G.PLATE_F = (g.X_FBUMP + 0.001, 0.50)
G.PLATE_R = (g.X_RBUMP - 0.001, 0.50)
G.SEATS = dict(front='bench', x=-0.15, z=0.44, rear=(-1.02, 0.46))
G.STEER = dict(c=(0.42, 0.37, 0.86), tilt=24, r=0.20)
G.SHIFTER = 'none'
G.HANDLE_KIND = 'chrome'
G.WINDOW_TRIM = 'chrome'
G.REVEAL = 'chrome'
