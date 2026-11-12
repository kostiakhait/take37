# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Drawn detail textures for the TAKE 37 street (system python with PIL + numpy), made for the game (no photographs, no brands, generic words only):

  python -I art/street/textures_detail.py [--out D:/temp/take37/street/tex]

  goods_c.png        4 x 4 cells of 256: product fronts (cans, boxes, bottles, books, shoe boxes, tapes, records ...), used on the shelves inside the shops
  wincontent_c.png   4 x 2 cells of 256 x 512: what is behind an upper-floor window (blinds, shades, curtains, dark room, lamp)
  windecals_c.png    4 x 4 cells of 256: shop-window decals (OPEN neon, SALE paper, hours plate, taped poster, ...), alpha
  wallart_c.png      4 x 4 cells of 512: ghost ads painted on brick, wheat-paste posters, graffiti tags, flyers; alpha
  litter_c.png       4 x 4 cells of 256: newspaper, cup, can, bag, wrapper, butts, leaf pile; alpha
  puddle_c.png       2 x 2 cells of 256: irregular puddle shapes (dark water, alpha edge)
  floor_tile_c.png   black and white / green and cream linoleum checker
"""
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

argv = sys.argv[1:]
OUT = pathlib.Path(argv[argv.index('--out') + 1] if '--out' in argv else 'D:/temp/take37/street/tex')
FONTS = pathlib.Path('D:/python310/lib/site-packages/matplotlib/mpl-data/fonts/ttf')
OUT.mkdir(parents=True, exist_ok=True)


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def ctext(d, box, text, f, fill):
    bb = d.textbbox((0, 0), text, font=f)
    x0, y0, x1, y1 = box
    d.text(((x0 + x1) / 2 - (bb[2] - bb[0]) / 2 - bb[0], (y0 + y1) / 2 - (bb[3] - bb[1]) / 2 - bb[1]), text, font=f, fill=fill)


def fit(d, text, name, w, size=120):
    f = font(name, size)
    while d.textlength(text, font=f) > w and f.size > 8:
        f = font(name, f.size - 4)
    return f


# ------------------------------------------------------------------------------------------------ goods: one product front per cell
def goods():
    S = 256
    A = Image.new('RGB', (4 * S, 4 * S), (60, 60, 60))
    r = np.random.default_rng(31)
    d = ImageDraw.Draw(A)

    def cell(i):
        return (i % 4) * S, (i // 4) * S

    def bars(x0, y0, w, h, col, n=3):
        for k in range(n):
            d.rectangle((x0 + 20, y0 + h - 70 + k * 18, x0 + w - 20 - int(r.integers(0, 60)), y0 + h - 60 + k * 18), fill=col)
    for i in range(16):
        x0, y0 = cell(i)
        if i in (0, 1, 2):                                               # cans: metal top and bottom, a wrapped label
            lab = [(190, 40, 35), (50, 120, 60), (230, 190, 50)][i]
            d.rectangle((x0, y0, x0 + S - 1, y0 + S - 1), fill=(170, 170, 172))
            d.rectangle((x0, y0 + 26, x0 + S - 1, y0 + S - 28), fill=lab)
            d.rectangle((x0, y0 + 100, x0 + S - 1, y0 + 150), fill=(245, 240, 225))
            ctext(d, (x0, y0 + 100, x0 + S, y0 + 150), ['SOUP', 'BEANS', 'CORN'][i], font('DejaVuSans-Bold.ttf', 40), lab)
        elif i in (3, 4, 5):                                             # packaged boxes
            bg = [(200, 50, 40), (40, 80, 150), (240, 200, 50)][i - 3]
            d.rectangle((x0, y0, x0 + S - 1, y0 + S - 1), fill=bg)
            d.ellipse((x0 + 50, y0 + 30, x0 + 206, y0 + 150), fill=(250, 240, 220))
            d.ellipse((x0 + 80, y0 + 55, x0 + 176, y0 + 125), fill=[(230, 170, 60), (220, 90, 70), (80, 140, 190)][i - 3])
            d.rectangle((x0, y0 + 190, x0 + S - 1, y0 + S - 1), fill=(250, 250, 245))
            ctext(d, (x0, y0 + 190, x0 + S, y0 + S), ['CEREAL', 'OATS', 'SOAP'][i - 3], font('DejaVuSans-Bold.ttf', 40), bg)
        elif i in (6, 7):                                                # bottles seen from the front: amber / green glass with a paper label
            g = [(120, 70, 25), (40, 110, 60)][i - 6]
            d.rectangle((x0, y0, x0 + S - 1, y0 + S - 1), fill=g)
            d.rectangle((x0 + 20, y0 + 70, x0 + S - 21, y0 + 190), fill=(235, 225, 195))
            d.rectangle((x0 + 20, y0 + 70, x0 + S - 21, y0 + 90), fill=(150, 30, 30))
            ctext(d, (x0, y0 + 100, x0 + S, y0 + 170), ['TONIC', 'LIME'][i - 6], font('DejaVuSerif-Bold.ttf', 40), (60, 40, 30))
        elif i == 8:                                                     # bread bag
            d.rectangle((x0, y0, x0 + S - 1, y0 + S - 1), fill=(240, 225, 190))
            for k in range(6):
                d.ellipse((x0 + 20 + k * 36, y0 + 30, x0 + 44 + k * 36, y0 + 54), fill=(200, 50, 40))
            d.rectangle((x0, y0 + 110, x0 + S - 1, y0 + 160), fill=(200, 50, 40))
            ctext(d, (x0, y0 + 110, x0 + S, y0 + 160), 'WHEAT', font('DejaVuSans-Bold.ttf', 40), (250, 240, 220))
        elif i == 9:                                                     # book spines, vertical
            x = x0
            while x < x0 + S:
                w = int(r.integers(10, 30))
                col = tuple(int(c) for c in r.integers(40, 220, 3))
                d.rectangle((x, y0, x + w, y0 + S - 1), fill=col)
                d.rectangle((x, y0 + 30, x + w, y0 + 44), fill=(235, 220, 160))
                d.rectangle((x, y0 + S - 50, x + w, y0 + S - 40), fill=(235, 220, 160))
                x += w + 1
        elif i == 10:                                                    # shoe box
            d.rectangle((x0, y0, x0 + S - 1, y0 + S - 1), fill=(215, 120, 40))
            d.rectangle((x0 + 20, y0 + 60, x0 + S - 21, y0 + 196), fill=(245, 235, 215))
            ctext(d, (x0, y0 + 60, x0 + S, y0 + 196), 'SHOES', font('DejaVuSans-Bold.ttf', 56), (120, 50, 20))
        elif i == 11:                                                    # toy box
            d.rectangle((x0, y0, x0 + S - 1, y0 + S - 1), fill=(60, 120, 200))
            for k in range(5):
                d.rectangle((x0 + 16 + k * 44, y0 + 40 + (k % 2) * 30, x0 + 52 + k * 44, y0 + 76 + (k % 2) * 30), fill=[(230, 60, 50), (240, 200, 40), (60, 170, 80), (240, 130, 30), (200, 80, 160)][k])
            ctext(d, (x0, y0 + 160, x0 + S, y0 + 240), 'TOYS', font('DejaVuSans-Bold.ttf', 60), (250, 230, 60))
        elif i == 12:                                                    # video tape: black case, white label strip
            d.rectangle((x0, y0, x0 + S - 1, y0 + S - 1), fill=(28, 28, 30))
            d.rectangle((x0 + 10, y0 + 20, x0 + S - 11, y0 + 110), fill=(240, 235, 225))
            d.rectangle((x0 + 10, y0 + 20, x0 + S - 11, y0 + 44), fill=(200, 40, 40))
            for k in range(3):
                d.rectangle((x0 + 24, y0 + 56 + k * 16, x0 + 24 + int(r.integers(80, 190)), y0 + 62 + k * 16), fill=(70, 70, 75))
            d.rectangle((x0 + 30, y0 + 150, x0 + S - 31, y0 + 210), fill=(46, 46, 50))
        elif i == 13:                                                    # record sleeve
            c = tuple(int(c) for c in r.integers(60, 200, 3))
            d.rectangle((x0, y0, x0 + S - 1, y0 + S - 1), fill=c)
            d.ellipse((x0 + 30, y0 + 30, x0 + S - 31, y0 + S - 31), fill=(20, 20, 24))
            d.ellipse((x0 + 90, y0 + 90, x0 + S - 91, y0 + S - 91), fill=(220, 190, 70))
        elif i == 14:                                                    # hardware blister pack on card
            d.rectangle((x0, y0, x0 + S - 1, y0 + S - 1), fill=(230, 200, 60))
            d.rectangle((x0 + 20, y0 + 40, x0 + S - 21, y0 + 160), fill=(205, 215, 220))
            d.rectangle((x0 + 50, y0 + 80, x0 + S - 51, y0 + 100), fill=(110, 110, 115))
            d.rectangle((x0 + 50, y0 + 100, x0 + 70, y0 + 140), fill=(180, 40, 30))
            ctext(d, (x0, y0 + 170, x0 + S, y0 + 240), 'TOOLS', font('DejaVuSans-Bold.ttf', 46), (40, 40, 40))
        else:                                                            # stationery pack
            d.rectangle((x0, y0, x0 + S - 1, y0 + S - 1), fill=(240, 240, 235))
            d.rectangle((x0, y0, x0 + S - 1, y0 + 70), fill=(40, 70, 150))
            for k in range(6):
                d.line((x0 + 20, y0 + 100 + k * 22, x0 + S - 20, y0 + 100 + k * 22), fill=(150, 190, 230), width=2)
            ctext(d, (x0, y0, x0 + S, y0 + 70), 'PAPER', font('DejaVuSans-Bold.ttf', 44), (250, 250, 250))
        d.rectangle((x0, y0, x0 + S - 1, y0 + S - 1), outline=(30, 30, 30), width=2)
    arr = np.asarray(A).astype(np.float32)
    arr *= (0.9 + 0.12 * r.random((4 * S, 4 * S, 1)))
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(OUT / 'goods_c.png')


# ------------------------------------------------------------------------------------------------ what is behind an upper window
def wincontent():
    W, H = 256, 512
    A = Image.new('RGB', (4 * W, 2 * H), (20, 20, 20))
    r = np.random.default_rng(41)
    for i in range(8):
        im = Image.new('RGB', (W, H), (0, 0, 0))
        d = ImageDraw.Draw(im)
        if i == 0:                                                       # venetian blind, half drawn
            d.rectangle((0, 0, W, H), fill=(70, 66, 60))
            for y in range(0, 300, 10):
                d.rectangle((0, y, W, y + 7), fill=(215, 205, 180))
                d.rectangle((0, y + 7, W, y + 10), fill=(120, 112, 95))
            d.rectangle((0, 300, W, H), fill=(55, 52, 50))
            d.rectangle((90, 250, 170, 512), fill=(40, 40, 46))
        elif i == 1:                                                     # roller shade down
            d.rectangle((0, 0, W, H), fill=(205, 190, 150))
            d.rectangle((0, 0, W, 20), fill=(140, 128, 100))
            d.rectangle((0, 440, W, 456), fill=(120, 108, 80))
            d.rectangle((W // 2 - 4, 456, W // 2 + 4, 480), fill=(110, 90, 60))
        elif i == 2:                                                     # sheer lace curtains, dark room
            d.rectangle((0, 0, W, H), fill=(40, 36, 34))
            d.rectangle((140, 200, 230, 400), fill=(70, 55, 45))
            a = np.asarray(im).astype(np.float32)
            yy, xx = np.mgrid[0:H, 0:W]
            lace = (np.sin(xx * 0.5) * np.sin(yy * 0.5) > 0.2) * 70
            a += lace[..., None] + 90
            im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
            d = ImageDraw.Draw(im)
        elif i == 3:                                                     # dark room, a shelf and a lamp shape
            d.rectangle((0, 0, W, H), fill=(30, 28, 30))
            d.rectangle((20, 220, 120, 232), fill=(70, 55, 40))
            d.rectangle((24, 160, 60, 220), fill=(80, 60, 50))
            d.polygon([(170, 250), (210, 250), (200, 300), (180, 300)], fill=(210, 180, 120))
            d.rectangle((188, 300, 192, 420), fill=(60, 55, 50))
        elif i == 4:                                                     # floral drapes pulled to the sides
            d.rectangle((0, 0, W, H), fill=(60, 50, 48))
            for side in (0, 1):
                x0 = 0 if side == 0 else W - 80
                d.rectangle((x0, 0, x0 + 80, H), fill=(170, 80, 80))
                for _ in range(26):
                    cx, cy = x0 + int(r.integers(6, 74)), int(r.integers(6, H - 6))
                    d.ellipse((cx - 8, cy - 8, cx + 8, cy + 8), fill=(235, 200, 190))
                for x in range(x0, x0 + 80, 14):
                    d.line((x, 0, x + 4, H), fill=(110, 40, 45), width=3)
        elif i == 5:                                                     # blue and white striped curtains drawn shut
            for x in range(0, W, 32):
                d.rectangle((x, 0, x + 16, H), fill=(70, 100, 160))
                d.rectangle((x + 16, 0, x + 32, H), fill=(235, 235, 235))
            d.rectangle((0, 0, W, 16), fill=(90, 70, 50))
        elif i == 6:                                                     # warm lit room: ceiling lamp, picture, wall
            d.rectangle((0, 0, W, H), fill=(190, 160, 115))
            d.rectangle((0, 380, W, H), fill=(95, 70, 50))
            d.ellipse((90, 20, 170, 80), fill=(255, 245, 210))
            d.rectangle((30, 130, 110, 200), fill=(80, 100, 120))
            d.rectangle((38, 138, 102, 192), fill=(150, 170, 150))
            d.rectangle((150, 250, 240, 400), fill=(110, 70, 60))
        else:                                                            # tied-back curtains, bright wall
            d.rectangle((0, 0, W, H), fill=(205, 195, 175))
            for side in (0, 1):
                x0 = 0 if side == 0 else W - 60
                d.polygon([(x0, 0), (x0 + 60, 0), (x0 + 45, 260), (x0 + 60, H), (x0, H)], fill=(120, 140, 110))
        im = im.filter(ImageFilter.GaussianBlur(0.8))
        A.paste(im, ((i % 4) * W, (i // 4) * H))
    A.save(OUT / 'wincontent_c.png')


# ------------------------------------------------------------------------------------------------ window decals (alpha)
def windecals():
    S = 256
    A = Image.new('RGBA', (4 * S, 4 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(A)

    def box(i):
        return (i % 4) * S, (i // 4) * S

    # 0: OPEN neon (red letters in a blue frame)
    x, y = box(0)
    d.rounded_rectangle((x + 8, y + 70, x + 248, y + 186), radius=18, outline=(70, 140, 255, 255), width=7)
    ctext(d, (x, y + 70, x + 256, y + 186), 'OPEN', font('DejaVuSans-Bold.ttf', 74), (255, 70, 60, 255))
    # 1: SALE paper sign, red on yellow
    x, y = box(1)
    d.rectangle((x + 20, y + 40, x + 236, y + 216), fill=(250, 220, 60, 255))
    ctext(d, (x + 20, y + 50, x + 236, y + 150), 'SALE', font('DejaVuSans-Bold.ttf', 84), (200, 30, 30, 255))
    ctext(d, (x + 20, y + 150, x + 236, y + 205), '50% OFF', font('DejaVuSans-Bold.ttf', 36), (40, 30, 30, 255))
    # 2: hours plate
    x, y = box(2)
    d.rectangle((x + 60, y + 30, x + 196, y + 226), fill=(245, 245, 240, 255), outline=(60, 60, 60, 255), width=3)
    ctext(d, (x + 60, y + 36, x + 196, y + 66), 'HOURS', font('DejaVuSans-Bold.ttf', 22), (40, 40, 40, 255))
    for k, t in enumerate(('MON-FRI', '9 - 6', 'SAT', '9 - 4', 'SUN', 'CLOSED')):
        ctext(d, (x + 60, y + 76 + k * 24, x + 196, y + 100 + k * 24), t, font('DejaVuSans.ttf', 17), (50, 50, 50, 255))
    # 3: taped poster (generic film flyer)
    x, y = box(3)
    d.rectangle((x + 40, y + 10, x + 216, y + 246), fill=(40, 30, 60, 255))
    d.ellipse((x + 70, y + 40, x + 186, y + 156), fill=(230, 160, 50, 255))
    d.polygon([(x + 40, y + 246), (x + 216, y + 246), (x + 216, y + 170), (x + 128, y + 150), (x + 40, y + 170)], fill=(60, 40, 90, 255))
    ctext(d, (x + 40, y + 176, x + 216, y + 220), 'LAST SHOW', font('DejaVuSans-Bold.ttf', 26), (250, 235, 200, 255))
    for cx in (x + 52, x + 204):
        d.rectangle((cx - 12, y + 4, cx + 12, y + 20), fill=(220, 210, 160, 200))
    # 4: COFFEE neon cup in amber
    x, y = box(4)
    ctext(d, (x, y + 70, x + 256, y + 190), 'COFFEE', font('DejaVuSans-Bold.ttf', 58), (255, 170, 60, 255))
    d.arc((x + 20, y + 60, x + 236, y + 200), 190, 350, fill=(255, 170, 60, 255), width=5)
    # 5: lettering on glass, gold with black outline (generic: 'EST. 1952')
    x, y = box(5)
    f = font('DejaVuSerif-Bold.ttf', 40)
    for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        ctext(d, (x + ox, y + 90 + oy, x + 256 + ox, y + 170 + oy), 'EST. 1952', f, (30, 25, 20, 255))
    ctext(d, (x, y + 90, x + 256, y + 170), 'EST. 1952', f, (235, 195, 80, 255))
    # 6: WELCOME card on a string
    x, y = box(6)
    d.rectangle((x + 40, y + 90, x + 216, y + 166), fill=(240, 235, 220, 255), outline=(90, 70, 50, 255), width=4)
    ctext(d, (x + 40, y + 90, x + 216, y + 166), 'WELCOME', font('DejaVuSans-Bold.ttf', 34), (150, 40, 40, 255))
    d.line((x + 128, y + 10, x + 70, y + 90), fill=(80, 70, 60, 255), width=2)
    d.line((x + 128, y + 10, x + 186, y + 90), fill=(80, 70, 60, 255), width=2)
    # 7: cards accepted stickers: three coloured discs (generic)
    x, y = box(7)
    for k, c in enumerate(((200, 40, 40), (40, 90, 190), (230, 180, 50))):
        d.ellipse((x + 20 + k * 74, y + 90, x + 84 + k * 74, y + 154), fill=c + (255,), outline=(240, 240, 240, 255), width=4)
    # 8: price list scribbled on paper
    x, y = box(8)
    d.rectangle((x + 30, y + 20, x + 226, y + 236), fill=(245, 240, 215, 255))
    for k in range(9):
        d.line((x + 44, y + 54 + k * 20, x + 44 + int(np.random.default_rng(k).integers(80, 160)), y + 54 + k * 20), fill=(60, 60, 90, 255), width=3)
    ctext(d, (x + 30, y + 20, x + 226, y + 50), 'TODAY', font('DejaVuSans-Bold.ttf', 22), (170, 40, 40, 255))
    # 9: blue/red barber stripes sign
    x, y = box(9)
    bs = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bs)
    bd.rectangle((20, 90, 236, 166), fill=(245, 245, 245, 255))
    for k in range(-3, 9):
        bd.polygon([(20 + k * 30, 166), (40 + k * 30, 166), (70 + k * 30, 90), (50 + k * 30, 90)], fill=(200, 40, 40, 255) if k % 2 else (40, 70, 170, 255))
    m_ = Image.new('L', (S, S), 0)
    ImageDraw.Draw(m_).rectangle((20, 90, 236, 166), fill=255)
    bs.putalpha(Image.fromarray(np.minimum(np.asarray(bs.split()[3]), np.asarray(m_))))
    ImageDraw.Draw(bs).rectangle((20, 90, 236, 166), outline=(30, 30, 30, 255), width=4)
    A.alpha_composite(bs, (x, y))
    # 10: dust and condensation: a soft white haze strip at the glass bottom
    x, y = box(10)
    haze = np.zeros((S, S, 4), np.uint8)
    haze[..., :3] = 235
    yy = np.arange(S)[:, None] / S
    haze[..., 3] = (np.clip((yy - 0.45) * 2, 0, 1) ** 1.6 * 120 * (0.7 + 0.3 * np.random.default_rng(3).random((S, S)))).astype(np.uint8)
    A.alpha_composite(Image.fromarray(haze, 'RGBA'), (x, y))
    # 11: fly-specked grime and a handprint-like smear
    x, y = box(11)
    sm = np.zeros((S, S, 4), np.uint8)
    rr = np.random.default_rng(9)
    for _ in range(90):
        cx, cy = rr.integers(8, S - 8, 2)
        sm[cy:cy + 1, cx:cx + 1] = (50, 46, 40, int(rr.integers(30, 80)))
    A.alpha_composite(Image.fromarray(sm, 'RGBA').filter(ImageFilter.GaussianBlur(0.6)), (x, y))
    A.save(OUT / 'windecals_c.png')


# ------------------------------------------------------------------------------------------------ wall art: ghost ads, posters, graffiti, flyers
def wallart():
    S = 512
    A = Image.new('RGBA', (4 * S, 4 * S), (0, 0, 0, 0))
    rr = np.random.default_rng(77)

    def put(i, im):
        A.alpha_composite(im, ((i % 4) * S, (i // 4) * S))

    def weather(im, amount=0.5, seed=1):
        """Fade and break up an image: noisy alpha holes (paint worn off brick)."""
        a = np.asarray(im).astype(np.float32)
        n = np.random.default_rng(seed).random((S // 8, S // 8))
        n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((S, S), Image.BICUBIC)).astype(np.float32) / 255.0
        g = np.random.default_rng(seed + 1).random((S, S))
        a[..., 3] *= np.clip((n - 0.25) * 2.2 * amount * 2, 0, 1) * (0.7 + 0.3 * g)
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')
    # 0-3: ghost ads painted on brick, lettering in white / cream / red, weathered
    ads = [(('DRINK', 'COLD SODA', '5 CENTS'), (240, 235, 220), (200, 50, 45)), (('SMOKE', 'PIPE & CIGAR', 'TOBACCO'), (235, 215, 160), (60, 90, 60)),
           (('HOME', 'LAUNDRY', 'SERVICE'), (230, 235, 240), (40, 80, 150)), (('FRESH', 'DAIRY', 'MILK & ICE'), (240, 240, 235), (170, 40, 50))]
    for i, (lines, fg, bg) in enumerate(ads):
        im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rectangle((16, 16, S - 17, S - 17), fill=bg + (255,))
        d.rectangle((30, 30, S - 31, S - 31), outline=fg + (255,), width=6)
        for k, t in enumerate(lines):
            f = fit(d, t, 'DejaVuSans-Bold.ttf', 400, 110 if k != 1 else 80)
            ctext(d, (30, 60 + k * 140, S - 30, 190 + k * 140), t, f, fg + (255,))
        put(i, weather(im, 0.62, 10 + i))
    # 4-7: wheat-paste posters (torn edges, bold colour fields, generic text)
    posters = [('CONCERT', 'LIVE TONIGHT', (30, 30, 60), (250, 120, 40)), ('LOST', 'CAT - REWARD', (245, 240, 220), (40, 40, 40)), ('VOTE', 'ELECTION DAY', (240, 240, 240), (50, 70, 150)),
               ('GARAGE SALE', 'SAT 8 AM', (250, 225, 70), (190, 40, 40))]
    for i, (t1, t2, bg, fg) in enumerate(posters):
        im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        x0, y0, x1, y1 = 60, 30, 450, 480
        d.rectangle((x0, y0, x1, y1), fill=bg + (255,))
        d.rectangle((x0 + 14, y0 + 14, x1 - 14, y1 - 14), outline=fg + (255,), width=5)
        f = fit(d, t1, 'DejaVuSans-Bold.ttf', 320, 120)
        ctext(d, (x0, y0 + 40, x1, y0 + 180), t1, f, fg + (255,))
        d.ellipse((x0 + 100, y0 + 190, x1 - 100, y0 + 330), fill=fg + (255,))
        d.ellipse((x0 + 130, y0 + 215, x1 - 130, y0 + 305), fill=bg + (255,))
        f = fit(d, t2, 'DejaVuSans-Bold.ttf', 320, 50)
        ctext(d, (x0, y0 + 350, x1, y0 + 420), t2, f, fg + (255,))
        a = np.asarray(im).astype(np.float32)
        edge = np.random.default_rng(100 + i).random((S, S))
        yy, xx = np.mgrid[0:S, 0:S]
        d0 = np.minimum.reduce([xx - x0, x1 - xx, yy - y0, y1 - yy]).astype(np.float32)
        a[..., 3] *= np.clip((d0 + (edge - 0.5) * 22) / 4.0, 0, 1)                                      # torn, ragged edge
        a[..., :3] *= (0.85 + 0.2 * np.random.default_rng(200 + i).random((S, S, 1)))
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')
        im = im.rotate(float(rr.uniform(-2, 2)), resample=Image.BICUBIC)
        put(4 + i, im)
    # 8-11: spray graffiti tags, a few colours, generic marks
    tags = [('RAT', (250, 70, 160), (20, 20, 30)), ('K2', (60, 220, 240), (20, 20, 30)), ('SKATE', (250, 230, 60), (30, 20, 20)), ('SPEED', (110, 240, 90), (20, 30, 20))]
    for i, (t, c, o) in enumerate(tags):
        im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        f = fit(d, t, 'DejaVuSans-Bold.ttf', 400, 190)
        for k in range(8, 0, -2):                                                                       # outline built from offsets
            for ox, oy in ((-k, 0), (k, 0), (0, -k), (0, k), (k, k), (-k, -k)):
                ctext(d, (ox, 150 + oy, S + ox, 350 + oy), t, f, o + (255,))
        ctext(d, (0, 150, S, 350), t, f, c + (255,))
        d.line([(60, 400), (180, 380), (300, 420), (450, 390)], fill=c + (255,), width=9)                   # underline swoosh
        for _ in range(26):                                                                             # spray dots
            cx, cy = rr.normal(256, 150), rr.normal(250, 100)
            d.ellipse((cx - 2, cy - 2, cx + 2, cy + 2), fill=c + (200,))
        for _ in range(7):                                                                              # drips
            dx = float(rr.integers(60, 450))
            d.line((dx, 300 + float(rr.integers(0, 30)), dx, 330 + float(rr.integers(10, 70))), fill=c + (230,), width=3)
        im = im.rotate(float(rr.uniform(-6, 6)), resample=Image.BICUBIC).filter(ImageFilter.GaussianBlur(0.9))
        put(8 + i, im)
    # 12: large wall mural-ish block: painted over patch (a square of off-colour paint, hides old graffiti)
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((70, 90, 450, 420), fill=(150, 140, 120, 235))
    for k in range(60):
        x = int(rr.integers(70, 440))
        d.line((x, 90, x + int(rr.integers(-4, 5)), 420), fill=(140, 130, 112, 200), width=int(rr.integers(2, 6)))
    put(12, weather(im, 0.9, 5))
    # 13: stencil / sticker: a star and bars
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for k in range(5):
        a = np.pi / 2 + k * 2 * np.pi * 2 / 5
        d.line((256 + 120 * np.cos(a), 256 - 120 * np.sin(a), 256 + 120 * np.cos(a + 4 * np.pi / 5), 256 - 120 * np.sin(a + 4 * np.pi / 5)), fill=(230, 230, 230, 255), width=14)
    put(13, im.filter(ImageFilter.GaussianBlur(0.8)))
    # 14: paper flyers taped in a cluster
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for k in range(5):
        x, y = 40 + (k % 3) * 150, 40 + (k // 3) * 220
        d.rectangle((x, y, x + 130, y + 190), fill=[(245, 240, 215), (250, 220, 90), (200, 230, 240), (245, 190, 190), (230, 240, 210)][k] + (255,))
        d.rectangle((x + 10, y + 14, x + 120, y + 46), fill=(60, 60, 60, 255))
        for q in range(5):
            d.line((x + 12, y + 66 + q * 22, x + 118 - int(rr.integers(0, 40)), y + 66 + q * 22), fill=(90, 90, 100, 255), width=3)
        d.rectangle((x + 40, y - 6, x + 90, y + 8), fill=(225, 215, 160, 200))
    put(14, im)
    # 15: grimy streaks on a wall (rain stains)
    im = np.zeros((S, S, 4), np.uint8)
    for _ in range(26):
        x = int(rr.integers(10, S - 10))
        h = int(rr.integers(120, 480))
        w = int(rr.integers(3, 12))
        im[0:h, x:x + w] = (20, 18, 14, int(rr.integers(30, 80)))
    put(15, Image.fromarray(im, 'RGBA').filter(ImageFilter.GaussianBlur(3)))
    A.save(OUT / 'wallart_c.png')


# ------------------------------------------------------------------------------------------------ litter and puddles
def litter():
    S = 256
    A = Image.new('RGBA', (4 * S, 4 * S), (0, 0, 0, 0))
    r = np.random.default_rng(5)

    def put(i, im):
        A.alpha_composite(im, ((i % 4) * S, (i // 4) * S))

    def new():
        im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
        return im, ImageDraw.Draw(im)

    def shadow(im):
        a = np.asarray(im.split()[3]).astype(np.float32)
        sh = Image.fromarray((a * 0.45).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5))
        base = Image.new('RGBA', im.size, (0, 0, 0, 0))
        base.putalpha(sh)
        base.alpha_composite(im)
        return base
    for i in range(3):                                           # 0-2: newspaper sheets (crumpled or flat), 1-2 torn pages
        im, d = new()
        pts = [(50 + r.integers(-10, 10), 70), (200 + r.integers(-10, 10), 60), (210, 190 + r.integers(-10, 10)), (45, 200)]
        d.polygon(pts, fill=(222 - i * 8, 218 - i * 8, 205 - i * 8, 255))
        for k in range(14):
            d.line((60, 80 + k * 8, 195 - int(r.integers(0, 40)), 78 + k * 8), fill=(70, 70, 70, 255), width=2)
        d.rectangle((62, 76, 190, 100), fill=(40, 40, 40, 255))
        if i:
            d.line((120, 70, 130, 195), fill=(180, 175, 165, 255), width=2)
        put(i, shadow(im.rotate(float(r.uniform(-20, 20)), resample=Image.BICUBIC)))
    im, d = new()                                                # 3: paper cup (white with red band), lying
    d.polygon([(60, 100), (190, 120), (190, 150), (60, 170)], fill=(240, 240, 235, 255))
    d.polygon([(60, 100), (80, 98), (80, 172), (60, 170)], fill=(200, 40, 40, 255))
    d.ellipse((46, 98, 76, 172), fill=(225, 225, 220, 255))
    put(3, shadow(im))
    im, d = new()                                                # 4: soda can lying
    d.rectangle((50, 100, 200, 150), fill=(190, 30, 35, 255))
    d.rectangle((50, 118, 200, 130), fill=(235, 235, 235, 255))
    d.ellipse((40, 100, 62, 150), fill=(180, 180, 185, 255))
    put(4, shadow(im.rotate(20, resample=Image.BICUBIC)))
    im, d = new()                                                # 5: crumpled paper bag
    d.polygon([(70, 120), (110, 80), (160, 90), (190, 130), (170, 175), (100, 180), (75, 160)], fill=(176, 138, 96, 255))
    for _ in range(14):
        a, b = r.integers(70, 190, 2)
        d.line((a, b, a + r.integers(-30, 30), b + r.integers(-30, 30)), fill=(130, 98, 66, 255), width=2)
    put(5, shadow(im))
    im, d = new()                                                # 6: candy wrapper, bright foil
    d.polygon([(70, 110), (110, 95), (185, 120), (120, 135)], fill=(240, 200, 50, 255))
    d.polygon([(70, 110), (50, 95), (60, 125)], fill=(210, 170, 40, 255))
    d.polygon([(185, 120), (205, 108), (200, 138)], fill=(210, 170, 40, 255))
    put(6, shadow(im))
    im, d = new()                                                # 7: cigarette butts scatter
    for _ in range(6):
        x, y = int(r.integers(40, 210)), int(r.integers(40, 210))
        ang = r.uniform(0, 6.28)
        d.line((x, y, x + 14 * np.cos(ang), y + 14 * np.sin(ang)), fill=(235, 230, 220, 255), width=4)
        d.line((x, y, x + 5 * np.cos(ang), y + 5 * np.sin(ang)), fill=(200, 140, 70, 255), width=4)
    put(7, im)
    im, d = new()                                                # 8: flattened cardboard box
    d.polygon([(40, 90), (200, 70), (215, 185), (55, 205)], fill=(180, 145, 100, 255))
    d.line((40, 90, 55, 205), fill=(150, 118, 80, 255), width=3)
    d.line((120, 80, 135, 195), fill=(155, 122, 85, 255), width=3)
    put(8, shadow(im.rotate(float(r.uniform(-15, 15)), resample=Image.BICUBIC)))
    im, d = new()                                                # 9: plastic bottle
    d.rounded_rectangle((50, 100, 190, 150), radius=22, fill=(190, 215, 225, 200), outline=(140, 170, 185, 255), width=2)
    d.rectangle((190, 112, 210, 138), fill=(60, 120, 190, 255))
    d.rectangle((90, 108, 150, 142), fill=(240, 240, 235, 220))
    put(9, shadow(im.rotate(-14, resample=Image.BICUBIC)))
    im, d = new()                                                # 10: food-wrapper (burger) paper, folded
    d.polygon([(60, 90), (170, 80), (200, 140), (150, 190), (70, 170)], fill=(235, 215, 120, 255))
    d.line((60, 90, 150, 190), fill=(200, 175, 80, 255), width=3)
    put(10, shadow(im))
    im, d = new()                                                # 11: plastic bag, ruffled
    d.polygon([(55, 130), (90, 80), (130, 110), (170, 70), (200, 125), (170, 175), (100, 170)], fill=(235, 235, 235, 150))
    d.line((90, 80, 100, 170), fill=(200, 200, 205, 200), width=2)
    d.line((170, 70, 150, 172), fill=(200, 200, 205, 200), width=2)
    put(11, shadow(im))
    for i in range(12, 16):                                      # 12-15: autumn leaf scatter (few leaves), colours of maple / elm / oak
        im, d = new()
        cols = [(190, 120, 40), (170, 60, 35), (200, 170, 60), (140, 80, 40)]
        for _ in range(int(r.integers(5, 10))):
            x, y = r.uniform(30, 226), r.uniform(30, 226)
            a = r.uniform(0, 6.28)
            L = r.uniform(18, 30)
            c = cols[int(r.integers(0, 4))]
            pts = [(x + L * np.cos(a) * t + 0.5 * L * np.sin(np.pi * t) * s * np.sin(a) * -1, y + L * np.sin(a) * t + 0.5 * L * np.sin(np.pi * t) * s * np.cos(a)) for s in (1,) for t in np.linspace(0, 1, 8)]
            pts2 = [(x + L * np.cos(a) * t - 0.5 * L * np.sin(np.pi * t) * np.sin(a) * -1, y + L * np.sin(a) * t - 0.5 * L * np.sin(np.pi * t) * np.cos(a)) for t in np.linspace(1, 0, 8)]
            d.polygon(pts + pts2, fill=c + (255,))
        put(i, shadow(im))
    A.save(OUT / 'litter_c.png')


def puddles():
    S = 256
    A = Image.new('RGBA', (2 * S, 2 * S), (0, 0, 0, 0))
    r = np.random.default_rng(15)
    for i in range(4):
        yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
        f = np.zeros((S, S), np.float32)
        for _ in range(5):
            cx, cy = r.uniform(0.3, 0.7) * S, r.uniform(0.35, 0.65) * S
            rx, ry = r.uniform(0.12, 0.3) * S, r.uniform(0.08, 0.2) * S
            f += np.exp(-(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2) * 1.2)
        n = np.asarray(Image.fromarray((r.random((16, 16)) * 255).astype(np.uint8)).resize((S, S), Image.BICUBIC)).astype(np.float32) / 255.0
        mask = np.clip((f + (n - 0.5) * 0.35 - 0.38) * 7.0, 0, 1)
        a = np.zeros((S, S, 4), np.uint8)
        a[..., :3] = (34, 38, 42)
        a[..., 3] = (mask * 255).astype(np.uint8)
        A.alpha_composite(Image.fromarray(a, 'RGBA').filter(ImageFilter.GaussianBlur(0.8)), ((i % 2) * S, (i // 2) * S))
    A.save(OUT / 'puddle_c.png')


def floor_tile():
    S = 512
    im = np.zeros((S, S, 3), np.float32)
    yy, xx = np.mgrid[0:S, 0:S]
    chk = ((xx // 64 + yy // 64) % 2).astype(np.float32)
    a = np.array([30, 30, 32], np.float32)
    b = np.array([220, 214, 200], np.float32)
    im[:] = a * (1 - chk[..., None]) + b * chk[..., None]
    n = np.random.default_rng(3).random((S, S, 1)) * 18
    grout = ((xx % 64 < 2) | (yy % 64 < 2))[..., None]
    im = np.where(grout, np.array([90, 88, 84], np.float32), im + n)
    Image.fromarray(np.clip(im, 0, 255).astype(np.uint8)).save(OUT / 'floor_tile_c.png')
    # a warm second variant (green and cream)
    im2 = np.where(chk[..., None] > 0, np.array([225, 215, 175], np.float32), np.array([70, 110, 85], np.float32)) + n
    im2 = np.where(grout, np.array([120, 118, 100], np.float32), im2)
    Image.fromarray(np.clip(im2, 0, 255).astype(np.uint8)).save(OUT / 'floor_tile2_c.png')


if __name__ == '__main__':
    goods()
    wincontent()
    windecals()
    wallart()
    litter()
    puddles()
    floor_tile()
    print('detail textures in', OUT)
