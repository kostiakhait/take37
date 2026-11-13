# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Pictures of the cab (textures_in/): run  python -I gauges.py [--top 85]

gauges_color.png  the cluster's face as in the owner's reference photograph of a 1983-87 LTD Crown Victoria: a wide horizontal ribbon speedometer (MPH, the km/h scale under it),
                  an orange needle, the PRNDL indicator of the four-speed automatic under the scale (P R N, the overdrive D in a circle, D, 1), a fuel gauge on the left and a coolant
                  temperature gauge on the right. --top: the end of the MPH scale (85 on the reference; a police car's certified speedometer read to 140, see SOURCES.md).
walnut_color.png  dark walnut wood grain (red-brown with fine dark lines), drawn procedurally, for the trim strips (0.5 m of wood per picture).
"""
import math
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).parent
TOP = int(sys.argv[sys.argv.index('--top') + 1]) if '--top' in sys.argv else 85
F = lambda n: ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', n)  # noqa: E731
WH, GR, OR = (232, 232, 226), (150, 152, 156), (255, 105, 25)

# ---- the cluster's face ----
W, H = 2048, 512
im = Image.new('RGB', (W, H), (10, 11, 13))
d = ImageDraw.Draw(im)
x0, x1 = 560, 1488
lo = 5 if TOP <= 90 else 0
step_big = 10 if TOP <= 90 else 20
d.text((x1 + 20, 90), 'MPH', font=F(30), fill=GR, anchor='lm')
yb = 170
d.line((x0, yb, x1, yb), fill=WH, width=4)
for v in range(lo, TOP + 1, 5):
    x = x0 + (x1 - x0) * (v - lo) / (TOP - lo)
    big = v % step_big == 0
    d.line((x, yb, x, yb - (44 if big else 22)), fill=WH, width=5 if big else 3)
    if big:
        d.text((x, yb - 80), str(v), font=F(40), fill=WH, anchor='mm')
kmh_top = TOP * 1.609
for k in range(0, int(kmh_top) + 1, 10):
    x = x0 + (x1 - x0) * (k / 1.609 - lo) / (TOP - lo)
    if x < x0 - 1:
        continue
    d.line((x, yb + 10, x, yb + (34 if k % 20 == 0 else 22)), fill=GR, width=3)
    if k % 20 == 0:
        d.text((x, yb + 58), str(k), font=F(26), fill=GR, anchor='mm')
d.text((x1 + 20, yb + 58), 'km/h', font=F(24), fill=GR, anchor='lm')
# the needle: a vertical orange bar resting at the start of the ribbon
d.rectangle((x0 + 6, yb - 60, x0 + 18, yb + 36), fill=OR)
# PRNDL under the scale: P R N (D) D 1, the selected P lit
yp = 330
for i, t in enumerate(['P', 'R', 'N', 'D', 'D', '1']):
    x = 1024 + (i - 2.5) * 70
    d.text((x, yp), t, font=F(38), fill=(OR if i == 0 else GR), anchor='mm')
    if i == 3:
        d.ellipse((x - 26, yp - 26, x + 26, yp + 26), outline=GR, width=3)
d.rectangle((500, 20, 1590, 400), outline=(40, 42, 46), width=6)


def dial(cx, cy, r, labels, title):
    d.arc((cx - r, cy - r, cx + r, cy + r), 200, 340, fill=(90, 92, 96), width=5)
    for k in range(5):
        a = math.radians(200 + 140 * k / 4)
        d.line((cx + math.cos(a) * r * 0.80, cy + math.sin(a) * r * 0.80, cx + math.cos(a) * r, cy + math.sin(a) * r), fill=WH, width=4)
    for t, ang in labels:
        a = math.radians(ang)
        d.text((cx + math.cos(a) * r * 0.62, cy + math.sin(a) * r * 0.62), t, font=F(36), fill=WH, anchor='mm')
    d.text((cx, cy + 60), title, font=F(24), fill=GR, anchor='mm')
    a = math.radians(270)
    d.line((cx, cy, cx + math.cos(a) * r * 0.85, cy + math.sin(a) * r * 0.85), fill=OR, width=7)
    d.ellipse((cx - 12, cy - 12, cx + 12, cy + 12), fill=(40, 40, 44))


dial(270, 230, 150, [('E', 210), ('F', 330)], 'FUEL')
dial(1778, 230, 150, [('C', 210), ('H', 330)], 'TEMP')
for cx, col in ((210, (120, 22, 20)), (330, (110, 90, 20)), (1718, (110, 90, 20)), (1838, (20, 60, 120))):
    d.ellipse((cx - 18, 440 - 18, cx + 18, 440 + 18), fill=col)
im.save(HERE / 'textures_in' / 'gauges_color.png')

# ---- walnut ----
rng = np.random.default_rng(7)
N = 1024
y, x = np.mgrid[0:N, 0:N].astype(np.float32) / N
# a low-frequency warp of the grain lines, then many fine lines along x (the long direction of the strips)
warp = np.zeros_like(x)
for k in range(1, 6):
    warp += rng.uniform(0.004, 0.02) / k * np.sin(2 * np.pi * (k * 1.3 * x + rng.uniform())) * np.cos(2 * np.pi * (k * 0.7 * y + rng.uniform()))
f = (y + warp) * 140
lines = (0.5 + 0.5 * np.sin(f + 1.8 * np.sin(f * 0.13))) ** 3
fine = rng.normal(0, 1, (N, N)).astype(np.float32)
fine = (fine + np.roll(fine, 1, 1) + np.roll(fine, 2, 1) + np.roll(fine, 3, 1) + np.roll(fine, 4, 1)) / 5   # streaks along x
patch = 0.5 + 0.5 * np.sin(2 * np.pi * (x * 0.8 + 0.3 * np.sin(2 * np.pi * y * 1.5)))
t = np.clip(0.55 + 0.25 * patch - 0.35 * lines + 0.08 * fine, 0, 1)
dark, light = np.array([46, 20, 10], np.float32), np.array([128, 62, 32], np.float32)
img = dark[None, None, :] * (1 - t[..., None]) + light[None, None, :] * t[..., None]
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(HERE / 'textures_in' / 'walnut_color.png')
print('written gauges_color.png (top', TOP, 'mph) and walnut_color.png')
