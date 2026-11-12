# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""The instrument cluster's face (textures_in/gauges_color.png): a horizontal ribbon speedometer 0-140 MPH over a km/h scale with 'CERTIFIED CALIBRATION' below (the police package's
speedometer was calibrated to 140 mph and carried that wording: Wikipedia 'Ford LTD Crown Victoria', Barn Finds 1985 LTD SSP), a fuel gauge on the left, a coolant temperature gauge on the right,
a row of warning lamps. Run: python -I gauges.py"""
from PIL import Image, ImageDraw, ImageFont
import pathlib
W, H = 2048, 512
im = Image.new('RGB', (W, H), (14, 15, 18))
d = ImageDraw.Draw(im)
F = lambda n: ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', n)  # noqa: E731
WH, GR, OR = (235, 235, 230), (150, 150, 150), (255, 110, 30)
# speedometer ribbon
x0, x1, y0 = 640, 1408, 150
d.rectangle((600, 60, 1448, 400), outline=(70, 72, 78), width=5)
d.text((1024, 92), 'MPH', font=F(34), fill=GR, anchor='mm')
d.line((x0, y0 + 34, x1, y0 + 34), fill=WH, width=4)
for v in range(0, 141, 5):
    x = x0 + (x1 - x0) * v / 140
    big = v % 20 == 0
    d.line((x, y0 + 34, x, y0 + 34 + (46 if big else 24 if v % 10 == 0 else 14)), fill=WH, width=4 if big else 3)
    if big:
        d.text((x, y0 + 112), str(v), font=F(36), fill=WH, anchor='mm')
d.line((x0, 300, x1, 300), fill=GR, width=3)
for k in range(0, 221, 10):
    x = x0 + (x1 - x0) * k / 220
    d.line((x, 300, x, 300 + (22 if k % 20 == 0 else 12)), fill=GR, width=3)
    if k % 40 == 0:
        d.text((x, 345), str(k), font=F(26), fill=GR, anchor='mm')
d.text((1425, 345), 'km/h', font=F(24), fill=GR, anchor='rm')
d.polygon([(x0 - 6, y0 + 8), (x0 + 6, y0 + 8), (x0 + 6, y0 + 70), (x0, y0 + 80), (x0 - 6, y0 + 70)], fill=OR)   # the needle at rest
d.text((1024, 436), 'CERTIFIED CALIBRATION', font=F(30), fill=GR, anchor='mm')
# round gauges: fuel (left), coolant temperature (right)
import math


def dial(cx, cy, r, lo, hi, labels, title):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(70, 72, 78), width=5)
    for k in range(7):
        a = math.radians(lo + (hi - lo) * k / 6)
        d.line((cx + math.cos(a) * r * 0.80, cy - math.sin(a) * r * 0.80, cx + math.cos(a) * r * 0.93, cy - math.sin(a) * r * 0.93), fill=WH, width=4)
    for (t, ang) in labels:
        a = math.radians(ang)
        d.text((cx + math.cos(a) * r * 0.55, cy - math.sin(a) * r * 0.55 + 20), t, font=F(38), fill=WH, anchor='mm')
    d.text((cx, cy + r * 0.62), title, font=F(24), fill=GR, anchor='mm')
    a = math.radians(lo + (hi - lo) * 0.5)
    d.line((cx, cy, cx + math.cos(a) * r * 0.78, cy - math.sin(a) * r * 0.78), fill=OR, width=7)
    d.ellipse((cx - 12, cy - 12, cx + 12, cy + 12), fill=(40, 40, 44))


dial(300, 230, 170, 150, 30, [('E', 142), ('F', 38)], 'FUEL')
dial(1748, 230, 170, 150, 30, [('C', 142), ('H', 38)], 'TEMP')
# warning lamps under the dials: brake, alternator, oil pressure, door/seat belt
for cx, col, t in ((250, (120, 20, 20), 'BRAKE'), (350, (110, 90, 20), 'ALT'), (1698, (110, 90, 20), 'OIL'), (1798, (20, 60, 110), 'HIGH')):
    d.ellipse((cx - 22, 456 - 22, cx + 22, 456 + 22), fill=col)
    d.text((cx, 492), t, font=F(18), fill=GR, anchor='mm')
im.save(pathlib.Path(__file__).parent / 'textures_in' / 'gauges_color.png')
print('written')
