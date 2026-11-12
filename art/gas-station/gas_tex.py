# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Textures of the gas station drawn for the game (PIL; fictional fuel brand VALDOR, no real mark): pump face with seven-segment digits and grade stickers, pump header light box,
price stele with 1987 prices, shop fascia sign, sticker atlas, oil-can label.   python -I art/gas-station/gas_tex.py [--out D:/temp/take37/street/tex]"""
import math
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont

argv = sys.argv[1:]
OUT = pathlib.Path(argv[argv.index('--out') + 1] if '--out' in argv else 'D:/temp/take37/street/tex')
FONTS = pathlib.Path('D:/python310/lib/site-packages/matplotlib/mpl-data/fonts/ttf')
F = lambda s, b=True: ImageFont.truetype(str(FONTS / ('DejaVuSans-Bold.ttf' if b else 'DejaVuSans.ttf')), s)  # noqa: E731
RED, YEL, WHT, BLK, BLU = (196, 30, 36), (246, 196, 28), (244, 244, 240), (16, 16, 18), (24, 52, 112)
SEG = {'0': 'abcdef', '1': 'bc', '2': 'abdeg', '3': 'abcdg', '4': 'bcfg', '5': 'acdfg', '6': 'acdefg', '7': 'abc', '8': 'abcdefg', '9': 'abcdfg', ' ': ''}


def text(d, box, s, f, fill):
    d.text(((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), s, font=f, fill=fill, anchor='mm')


def digit(d, x, y, w, h, ch, on, off):
    t = w * 0.17
    r = {'a': (x + t, y, x + w - t, y + t), 'd': (x + t, y + h - t, x + w - t, y + h), 'g': (x + t, y + h / 2 - t / 2, x + w - t, y + h / 2 + t / 2),
         'b': (x + w - t, y + t * .6, x + w, y + h / 2 - t * .3), 'c': (x + w - t, y + h / 2 + t * .3, x + w, y + h - t * .6),
         'f': (x, y + t * .6, x + t, y + h / 2 - t * .3), 'e': (x, y + h / 2 + t * .3, x + t, y + h - t * .6)}
    for b in r.values():
        d.rectangle(b, fill=off)
    for k in SEG.get(ch, ''):
        d.rectangle(r[k], fill=on)


def number(d, x, y, w, h, s, on, off, gap=0.28):
    cx = x
    for ch in s:
        if ch == '.':
            d.rectangle((cx - w * 0.12, y + h - w * 0.2, cx + w * 0.08, y + h), fill=on)
            cx += w * 0.1
            continue
        digit(d, cx, y, w, h, '8', off, off)
        digit(d, cx, y, w, h, ch, on, off)
        cx += w * (1 + gap)


def logo(d, cx, cy, r, ring=YEL, field=RED, fg=WHT):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ring)
    d.ellipse((cx - r * .88, cy - r * .88, cx + r * .88, cy + r * .88), fill=field)
    d.polygon([(cx - r * .6, cy - r * .5), (cx - r * .26, cy - r * .5), (cx, cy + r * .12), (cx + r * .26, cy - r * .5), (cx + r * .6, cy - r * .5), (cx, cy + r * .62)], fill=fg)
    d.polygon([(cx - r * .3, cy - r * .62), (cx, cy - r * .22), (cx + r * .3, cy - r * .62), (cx, cy - r * .85)], fill=ring)


def oct_(cx, cy, r):
    return [(cx + r * math.cos(math.pi / 8 + k * math.pi / 4), cy + r * math.sin(math.pi / 8 + k * math.pi / 4)) for k in range(8)]


def pump_face():
    W, H = 1024, 810
    im = Image.new('RGB', (W, H), (236, 235, 230))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W - 1, H - 1), outline=(150, 150, 148), width=6)
    d.rectangle((70, 90, 954, 420), fill=(30, 31, 33))
    d.rectangle((88, 108, 936, 402), fill=(8, 8, 10))
    on, off = (255, 58, 40), (58, 14, 12)
    for lab, cur, val, y in (('SALE', '$', '03.89', 110), ('GALLONS', '', '04.37', 218), ('PRICE / GAL', '$', '0.89', 316)):
        d.text((112, y + 40), lab, font=F(26), fill=(220, 220, 215), anchor='lm')
        if cur:
            d.text((420, y + 50), cur, font=F(44), fill=on, anchor='mm')
        number(d, 470, y + 12, 52, 72, val, on, off)
    d.rectangle((86, 106, 938, 404), outline=(60, 60, 64), width=3)
    for i, (lab, col, pr) in enumerate((('REGULAR', (130, 130, 130), '0.84'), ('UNLEADED', (30, 130, 70), '0.89'), ('SUPER UNL.', RED, '0.99'))):
        x = 80 + i * 296
        d.rounded_rectangle((x, 450, x + 270, 560), 14, fill=col, outline=(40, 40, 40), width=4)
        text(d, (x, 456, x + 270, 508), lab, F(34), WHT)
        d.rectangle((x + 60, 512, x + 210, 548), fill=WHT)
        text(d, (x + 60, 512, x + 210, 548), '$' + pr, F(30), BLK)
    d.polygon(oct_(150, 690, 78), fill=(24, 120, 70), outline=WHT)
    text(d, (72, 650, 228, 700), 'UNLEADED', F(24), WHT)
    text(d, (72, 690, 228, 730), 'GASOLINE ONLY', F(14), WHT)
    d.rounded_rectangle((300, 620, 560, 760), 10, fill=YEL, outline=BLK, width=5)
    text(d, (300, 630, 560, 700), 'PAY FIRST', F(40), BLK)
    text(d, (300, 700, 560, 750), 'PREPAY AFTER 10 PM', F(20), BLK)
    d.ellipse((620, 622, 760, 762), fill=WHT, outline=RED, width=14)
    d.rectangle((650, 686, 730, 702), fill=BLK)
    d.rectangle((732, 686, 742, 702), fill=RED)
    d.line((636, 740, 746, 644), fill=RED, width=12)
    text(d, (800, 640, 1000, 690), 'STOP ENGINE', F(24), BLK)
    text(d, (800, 690, 1000, 730), 'NO SMOKING', F(24), RED)
    im.save(OUT / 'pumpface_c.png')


def pump_head():
    W, H = 1024, 448
    im = Image.new('RGB', (W, H), RED)
    d = ImageDraw.Draw(im)
    d.rectangle((14, 14, W - 15, H - 15), outline=WHT, width=10)
    d.rectangle((14, 330, W - 15, 360), fill=YEL)
    logo(d, 170, 190, 130)
    d.text((340, 120), 'VALDOR', font=F(120), fill=WHT, anchor='lm')
    d.text((344, 260), 'FUELS  SINCE 1951', font=F(52), fill=YEL, anchor='lm')
    d.text((W / 2, 395), 'SELF SERVE  -  PAY FIRST', font=F(34), fill=WHT, anchor='mm')
    im.save(OUT / 'pumphead_c.png')


def stele():
    W, H = 1024, 1792
    im = Image.new('RGB', (W, H), (232, 232, 228))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W - 1, 560), fill=RED)
    d.rectangle((0, 520, W - 1, 580), fill=YEL)
    logo(d, 512, 270, 210)
    d.text((512, 500), 'VALDOR', font=F(100), fill=WHT, anchor='mm')
    for i, (lab, pr, col) in enumerate((('REGULAR', '84', (150, 150, 150)), ('UNLEADED', '89', (30, 130, 70)), ('SUPER UNLEADED', '99', RED))):
        y = 600 + i * 390
        d.rectangle((24, y, W - 25, y + 372), fill=(12, 12, 14), outline=WHT, width=8)
        d.rectangle((24, y, W - 25, y + 78), fill=col)
        d.text((512, y + 40), lab + '  GAL', font=F(52), fill=WHT, anchor='mm')
        d.text((100, y + 235), '$', font=F(120), fill=(255, 235, 150), anchor='lm')
        d.text((190, y + 235), '.' + pr, font=F(280), fill=(255, 245, 210), anchor='lm')
        d.text((870, y + 150), '9', font=F(130), fill=(255, 245, 210), anchor='mm')
        d.text((190, y + 235), '0', font=F(280), fill=(255, 245, 210), anchor='rm') if False else None
    im.save(OUT / 'pricesign_c.png')


def fascia():
    W, H = 2048, 224
    im = Image.new('RGB', (W, H), WHT)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 34), fill=RED)
    d.rectangle((0, H - 34, W, H), fill=RED)
    d.rectangle((0, 34, W, 46), fill=YEL)
    logo(d, 150, H / 2, 82)
    d.text((270, H / 2 + 2), 'VALDOR', font=F(150), fill=RED, anchor='lm')
    d.text((1060, H / 2 - 36), 'MINI MART', font=F(86), fill=BLU, anchor='lm')
    d.text((1062, H / 2 + 52), 'OPEN 24 HOURS', font=F(52), fill=(60, 60, 64), anchor='lm')
    d.text((1810, H / 2), 'ICE  COFFEE', font=F(46), fill=RED, anchor='mm')
    im.save(OUT / 'shopfascia_c.png')


def decor():
    S = 256
    A = Image.new('RGBA', (4 * S, 4 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(A)
    cell = lambda i: ((i % 4) * S, (i // 4) * S)  # noqa: E731

    def c(i, bg, lines, fg=WHT, rr=24):
        x, y = cell(i)
        d.rounded_rectangle((x + 6, y + 6, x + S - 7, y + S - 7), rr, fill=bg, outline=fg, width=6)
        for k, (s, sz) in enumerate(lines):
            d.text((x + S / 2, y + 20 + (S - 40) * (k + 0.5) / len(lines)), s, font=F(sz), fill=fg, anchor='mm')
    x, y = cell(0)
    d.ellipse((x + 12, y + 12, x + S - 13, y + S - 13), fill=WHT, outline=RED, width=18)
    d.rectangle((x + 60, y + 118, x + 170, y + 138), fill=BLK)
    d.rectangle((x + 172, y + 118, x + 190, y + 138), fill=RED)
    d.line((x + 52, y + 204, x + 204, y + 52), fill=RED, width=16)
    c(1, YEL, [('PAY', 70), ('FIRST', 62)], BLK)
    c(2, BLU, [('COLD', 54), ('DRINKS', 46), ('& ICE', 42)])
    c(3, (240, 250, 255), [('PACKAGED', 34), ('ICE', 100)], BLU)
    c(4, (14, 14, 18), [('OPEN', 80)], (255, 70, 60), 4)
    c(5, RED, [('24', 110), ('HOURS', 48)])
    c(6, (24, 120, 70), [('SELF', 60), ('SERVE', 54)])
    c(7, BLU, [('REST', 56), ('ROOMS', 48)])
    c(8, (60, 60, 64), [('AIR', 80), ('25c', 80)])
    c(9, BLU, [('WATER', 56), ('FREE', 50)])
    c(10, (240, 230, 210), [('HOT', 60), ('COFFEE', 44), ('50c', 56)], RED)
    x, y = cell(11)
    logo(d, x + S / 2, y + S / 2, 118)
    c(12, RED, [('DRIVE', 56), ('SLOW', 64)])
    c(13, (240, 240, 235), [('ENTER', 48), ('>>', 90)], BLK)
    c(14, YEL, [('NO', 70), ('LOITERING', 30)], BLK)
    c(15, (250, 250, 245), [('LOTTO', 58), ('TICKETS', 42)], RED)
    A.save(OUT / 'decor_c.png')


def oilcan():
    S = 256
    im = Image.new('RGB', (S, S), (190, 192, 196))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 70, S, 256), fill=(20, 40, 100))
    d.rectangle((0, 70, S, 90), fill=YEL)
    d.rectangle((0, 236, S, 256), fill=YEL)
    d.text((S / 2, 135), 'VALDOR', font=F(50), fill=WHT, anchor='mm')
    d.text((S / 2, 188), '10W-40', font=F(46), fill=YEL, anchor='mm')
    d.text((S / 2, 222), 'MOTOR OIL  1 QT', font=F(20), fill=WHT, anchor='mm')
    im.save(OUT / 'oilcan_c.png')


for fn in (pump_face, pump_head, stele, fascia, decor, oilcan):
    fn()
print('gas textures in', OUT)
