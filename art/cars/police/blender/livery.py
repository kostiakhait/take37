# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""The Chicago Police Department markings of 1987 as textures (system python: PIL; run before build_crownvic.py):

  python -I examples/crown-victoria/blender/livery.py [--unit 7126] [--plate "M 76 810"]

  build/textures/livery_color.png   4096 x 2048: the paint's colour seen from the sides. Top half: the left (driver's) side seen from the left, front to the left; bottom half: the right
                                    side seen from the right, front to the right. U runs over X in [-2.95, 2.95] m, each half over Z in [0.15, 1.15] m (see build_crownvic.uv_paint).
  build/textures/plate_color.png    512 x 256: the rear plate (Illinois, municipal "M" series).

The layout is the one on the right side of CPD unit 7126, a 1983-87 LTD Crown Victoria in the department's livery (photograph by Terry Spirek, Flickr 14662314287, all rights reserved; used here only as
a reference for where things go, not copied): a medium blue band under the side windows from the tail to the front door, sweeping down along the front fender over the wheel opening and
cut on a slant short of the corner lamp; "CHICAGO" on the rear door and "POLICE" on the front door in red under the band; "WE SERVE AND PROTECT" small in white in the band on the rear door;
the unit number in white with a red outline on the band on the fender; the City of Chicago flag at the band's rear end. The red is measured off the Commons photograph of the CPD Caprice 8535
(Raymond Wambsgans, CC BY-SA 2.0), the blue off the 7126 photograph; both are estimates of the paint, not swatches.
Not known and so chosen: the left side's word order (here "CHICAGO" on the front door so that it reads CHICAGO POLICE from the left as on the right side), the lettering's typeface
(Arial Bold for a Helvetica-like grotesque) and the plate's characters (those of the Caprice 8535).
"""
import math
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cv_geom as G  # noqa: E402

TEX = HERE.parent / 'build' / 'textures'
U0, U1, Z0, Z1 = -2.95, 2.95, 0.15, 1.15       # the atlas' extent (keep in step with build_crownvic.uv_paint)
TW, TH = 4096, 2048
PPM = 1024                                      # the drawing canvas: px per metre, isotropic; resized to the atlas afterwards

WHITE = (243, 243, 240)
BLUE = (45, 125, 200)
RED = (200, 38, 34)
DARKBLUE = (22, 52, 110)
FONTS = pathlib.Path('C:/Windows/Fonts')


def font(name, size_m):
    """A TrueType font whose capitals are size_m metres tall on the canvas."""
    f = ImageFont.truetype(str(FONTS / name), 100)
    cap = f.getbbox('H')[3] - f.getbbox('H')[1]
    return ImageFont.truetype(str(FONTS / name), max(4, int(round(100 * size_m * PPM / cap))))


class Side:
    """One side's canvas as seen from that side: the front is on the left for the left side and on the right for the right side."""

    def __init__(self, left):
        self.left = left
        self.w = int(round((U1 - U0) * PPM))
        self.h = int(round((Z1 - Z0) * PPM))
        self.im = Image.new('RGB', (self.w, self.h), WHITE)
        self.d = ImageDraw.Draw(self.im)

    def px(self, x, z):
        u = (U1 - x) if self.left else (x - U0)
        return (u * PPM, (Z1 - z) * PPM)

    def poly(self, pts, fill):
        self.d.polygon([self.px(x, z) for x, z in pts], fill=fill)

    def text(self, s, x, z, fnt, fill, stroke=0.0, stroke_fill=None, skew=0.0):
        """s centred on (x, z) (model metres); stroke in metres; skew: an italic slant (tan of the angle)."""
        bb = fnt.getbbox(s)
        sw = int(round(stroke * PPM))
        tw, th = bb[2] - bb[0] + 2 * sw + 8, bb[3] - bb[1] + 2 * sw + 8
        pad = int(abs(skew) * th) + 4
        lay = Image.new('RGBA', (tw + 2 * pad, th), (0, 0, 0, 0))
        ImageDraw.Draw(lay).text((pad + sw + 4 - bb[0], sw + 4 - bb[1]), s, font=fnt, fill=fill, stroke_width=sw, stroke_fill=stroke_fill)
        if skew:
            lay = lay.transform(lay.size, Image.AFFINE, (1, skew, -skew * th / 2, 0, 1, 0), resample=Image.BICUBIC)
        cx, cy = self.px(x, z)
        self.im.paste(lay, (int(round(cx - lay.width / 2)), int(round(cy - lay.height / 2))), lay)

    def chicago_flag(self, x0, x1, z0, z1):
        """The City of Chicago flag: white, two light blue bars at a sixth from the top and the bottom, four red six-pointed stars across the middle."""
        a, b = self.px(x0, z1), self.px(x1, z0)
        l, r = min(a[0], b[0]), max(a[0], b[0])
        t, bo = a[1], b[1]
        h = bo - t
        self.d.rectangle((l, t, r, bo), fill=(250, 250, 250))
        for k in (1, 4):
            self.d.rectangle((l, t + h * k / 6, r, t + h * (k + 1) / 6), fill=(140, 200, 235))
        cy = t + h / 2
        rr = h * 0.12
        for i in range(4):
            cx = l + (r - l) * (0.2 + 0.2 * i)
            pts = []
            for k in range(12):
                rad = rr if k % 2 == 0 else rr * 0.5
                ang = math.pi / 2 + k * math.pi / 6
                pts.append((cx + rad * math.cos(ang), cy - rad * math.sin(ang)))
            self.d.polygon(pts, fill=(230, 30, 40))


# ---- the band (model metres) -------------------------------------------------------------------------------------------------------------------------------------------------
X_DOOR_F = G.X(890.0)                 # the front door's front edge: here the band starts down the fender
X_END_TOP, X_END_BOT = G.X(1100.0), G.X(1092.0)
Z_BAND_BOT = 0.815                    # under the door handles (their bottom is at px row 95, 0.823 m)
Z_SIDE_TOP = 1.05                     # above the side's top edge: the top surface is mapped white anyway
Z_FENDER_END_TOP, Z_FENDER_END_BOT = 0.800, 0.665


def edge_z(x):
    """The height of the side's top edge (where the shoulder bevel meets the top): the band goes up to it and no further, so the C-pillar stays white."""
    crown = 0.0 if G.X_C_PILLAR <= x < G.X_COWL else 0.016
    return max(G.top_z(x) - crown, G.crease_z(x) + 0.03) + 0.004


def band_poly():
    n = 120
    top = [(G.X_TAIL - 0.2 + (X_DOOR_F - G.X_TAIL + 0.2) * k / n, 0.0) for k in range(n + 1)]
    top = [(x, edge_z(max(x, G.X_TAIL))) for x, _ in top]
    return top + [(X_DOOR_F, band_top(X_DOOR_F)), (X_END_TOP, Z_FENDER_END_TOP), (X_END_BOT, Z_FENDER_END_BOT), (X_DOOR_F, Z_BAND_BOT), (G.X_TAIL - 0.2, Z_BAND_BOT)]


def band_bottom(x):
    if x <= X_DOOR_F:
        return Z_BAND_BOT
    return Z_BAND_BOT + (Z_FENDER_END_BOT - Z_BAND_BOT) * (x - X_DOOR_F) / (X_END_BOT - X_DOOR_F)


def band_top(x):
    if x <= X_DOOR_F:
        return Z_SIDE_TOP
    t = (x - X_DOOR_F) / (X_END_TOP - X_DOOR_F)
    return G.crease_z(X_DOOR_F) + 0.07 + (Z_FENDER_END_TOP - G.crease_z(X_DOOR_F) - 0.07) * t


def make(unit, plate):
    TEX.mkdir(parents=True, exist_ok=True)
    x_rear_door = 0.5 * (G.X(581.0) + G.X(725.5))
    x_front_door = 0.5 * (G.X(725.5) + G.X(890.0))
    z_words = 0.725                                  # the words' centre: between the band (0.815) and the side moulding (0.646)
    words = font('arialbd.ttf', 0.100)
    motto = font('arialbi.ttf', 0.026)
    numf = font('arialbd.ttf', 0.092)
    sides = []
    for left in (True, False):
        s = Side(left)
        s.poly(band_poly(), BLUE)
        # the words: right side CHICAGO (rear door) POLICE (front door) as photographed; left side the same reading order from the viewer's left
        if not left:
            s.text('CHICAGO', x_rear_door, z_words, words, RED, stroke=0.0025, stroke_fill=DARKBLUE)
            s.text('POLICE', x_front_door, z_words, words, RED, stroke=0.0025, stroke_fill=DARKBLUE)
        else:
            s.text('CHICAGO', x_front_door, z_words, words, RED, stroke=0.0025, stroke_fill=DARKBLUE)
            s.text('POLICE', x_rear_door, z_words, words, RED, stroke=0.0025, stroke_fill=DARKBLUE)
        s.text('WE SERVE AND PROTECT', x_rear_door + 0.08, Z_BAND_BOT + 0.024, motto, (250, 250, 250), skew=-0.0)
        # the unit number on the fender: white with a red outline, upright, centred in the band
        xn = G.X(1040.0)
        zn = 0.5 * (band_bottom(xn) + band_top(xn)) - 0.004
        s.text(unit, xn, zn, numf, (250, 250, 250), stroke=0.0075, stroke_fill=RED, skew=-0.12 if left else -0.12)
        # the city flag at the band's rear end
        fx0 = G.X_TAIL + 0.07
        s.chicago_flag(fx0, fx0 + 0.105, Z_BAND_BOT + 0.012, Z_BAND_BOT + 0.082)
        sides.append(s.im.resize((TW, TH // 2), Image.LANCZOS))
    atlas = Image.new('RGB', (TW, TH), WHITE)
    atlas.paste(sides[0], (0, 0))
    atlas.paste(sides[1], (0, TH // 2))
    atlas.save(TEX / 'livery_color.png')

    # the plate: Illinois, white, dark blue characters, "Land of Lincoln" over, "ILLINOIS" under (as on the Caprice 8535's plate)
    pl = Image.new('RGB', (512, 256), (238, 238, 232))
    d = ImageDraw.Draw(pl)
    d.rectangle((4, 4, 507, 251), outline=(40, 50, 90), width=4)
    f1 = ImageFont.truetype(str(FONTS / 'arialbd.ttf'), 120)
    f2 = ImageFont.truetype(str(FONTS / 'ariali.ttf'), 30)
    f3 = ImageFont.truetype(str(FONTS / 'arialbd.ttf'), 30)
    for txt, f, y in ((plate, f1, 128), ('Land of Lincoln', f2, 30), ('ILLINOIS', f3, 226)):
        bb = d.textbbox((0, 0), txt, font=f)
        d.text((256 - (bb[2] - bb[0]) / 2 - bb[0], y - (bb[3] - bb[1]) / 2 - bb[1]), txt, font=f, fill=(30, 40, 110))
    for x in (60, 452):
        d.ellipse((x - 9, 21, x + 9, 39), fill=(150, 150, 150))
    pl.save(TEX / 'plate_color.png')
    # the cluster's faces (a generic analogue cluster of the time; the 1987 police cluster's exact faces are not known): a horizontal-sweep speedometer to 120 mph in the
    # middle, fuel and temperature dials either side, warning lamps
    g = Image.new('RGB', (1024, 256), (14, 14, 18))
    d = ImageDraw.Draw(g)
    fs = ImageFont.truetype(str(FONTS / 'arial.ttf'), 20)
    d.rectangle((300, 40, 724, 200), outline=(90, 90, 96), width=3)
    for k in range(25):
        x = 320 + 384 * k / 24
        d.line((x, 120, x, 140 if k % 2 else 150), fill=(220, 220, 220), width=3)
        if k % 4 == 0:
            d.text((x - 12, 155), str(k * 5), font=fs, fill=(220, 220, 220))
    d.text((480, 60), 'MPH', font=fs, fill=(200, 200, 200))
    d.line((320, 115, 704, 115), fill=(200, 200, 200), width=2)
    d.polygon([(330, 100), (336, 100), (333, 130)], fill=(230, 80, 30))
    for cx, lab in ((150, 'F   E'), (874, 'C   H')):
        d.ellipse((cx - 90, 40, cx + 90, 220), outline=(90, 90, 96), width=3)
        for k in range(7):
            a = math.radians(210 - 40 * k)
            d.line((cx + 70 * math.cos(a), 130 - 70 * math.sin(a), cx + 82 * math.cos(a), 130 - 82 * math.sin(a)), fill=(220, 220, 220), width=3)
        d.text((cx - 30, 170), lab, font=fs, fill=(220, 220, 220))
        d.line((cx, 130, cx - 40, 100), fill=(230, 80, 30), width=4)
    for k, col in enumerate(((180, 30, 30), (30, 160, 60), (200, 160, 30), (40, 90, 200))):
        d.ellipse((440 + 40 * k, 210, 460 + 40 * k, 230), fill=tuple(c // 3 for c in col))
    g.save(TEX / 'gauges_color.png')
    print('wrote', TEX / 'livery_color.png', TEX / 'plate_color.png', TEX / 'gauges_color.png')


if __name__ == '__main__':
    a = sys.argv[1:]
    make(a[a.index('--unit') + 1] if '--unit' in a else '7126', a[a.index('--plate') + 1] if '--plate' in a else 'M 76 810')
