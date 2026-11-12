# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Texture preparation for the TAKE 37 street kit and the gas station (system python with PIL + numpy):

  python -I art/street/textures_prep.py [--out D:/temp/take37/street/tex] [--lib D:/temp/take37/street/lib]

1. Unpacks the library textures that are used (D:/REPO/ferret/lib/ferret-assets, catalog.json; each tex-* package is a zip) into --lib.
2. Resizes them to at most 1024 px and writes tinted variants (bricks, plasters, awnings, painted metal) as <id>_c.png / <id>_n.png / <id>_orm.png.
3. Draws what the library does not have (made for the game): asphalt mottling, sidewalk slabs with joints, clapboard siding (library wood grain under paint),
   road decal atlas, lane paint, road-sign atlas, shop-sign atlas, shop interiors, leaf cards.
Fonts: DejaVu (free licence, matplotlib's copy).
"""
import json
import pathlib
import sys
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

argv = sys.argv[1:]
arg = lambda k, d: argv[argv.index(k) + 1] if k in argv else d  # noqa: E731
OUT = pathlib.Path(arg('--out', 'D:/temp/take37/street/tex'))
LIB = pathlib.Path(arg('--lib', 'D:/temp/take37/street/lib'))
FERRET = pathlib.Path('D:/REPO/ferret/lib/ferret-assets')
FONTS = pathlib.Path('D:/python310/lib/site-packages/matplotlib/mpl-data/fonts/ttf')
OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(1987)

USED = ['brick-clay-new-material-sphere-2', 'brick-clay-old', 'concrete-312', 'concrete', 'concrete-block', 'stucko-wa1', 'column-plaster-311',
        'wood-beige', 'wood-blue', 'wood-pine', 'wood-brown', 'wood-dark-brown', 'wood-oak', 'bark01', 'bark02', 'grass', 'ground-grass', 'soil',
        'metal-rust', 'metal-steel', 'metal-black', 'cloth-white-rough', 'rock-slate']


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def unpack():
    cat = json.load(open(FERRET / 'catalog.json'))['packages']
    for n in USED:
        d = LIB / f'tex-{n}'
        if not d.exists():
            zipfile.ZipFile(FERRET / cat[f'tex-{n}']['url']).extractall(d)


def lib(n, kind='basecolor', size=1024):
    f = next((LIB / f'tex-{n}/textures').glob(f'*/{kind}.webp'), None)
    if f is None:
        return None
    im = Image.open(f).convert('RGB')
    return im.resize((size, size), Image.LANCZOS) if im.size[0] != size else im


def save(im, name):
    if isinstance(im, np.ndarray):
        im = Image.fromarray(np.clip(im, 0, 255).astype(np.uint8))
    im.save(OUT / name)


def tileable_noise(n, beta=2.0, seed=0):
    r = np.random.default_rng(seed)
    f = np.fft.fftfreq(n)
    fx, fy = np.meshgrid(f, f)
    k = np.sqrt(fx ** 2 + fy ** 2)
    k[0, 0] = 1
    spec = (r.normal(size=(n, n)) + 1j * r.normal(size=(n, n))) / k ** (beta / 2)
    spec[0, 0] = 0
    a = np.real(np.fft.ifft2(spec))
    return (a - a.min()) / (a.max() - a.min())


def normal_from_height(h, strength=2.0):
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * strength
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * strength
    nx, ny, nz = -gx, gy, np.ones_like(h)
    L = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    return np.stack([(nx / L * .5 + .5) * 255, (ny / L * .5 + .5) * 255, (nz / L * .5 + .5) * 255], -1)


def tint(im, rgb, gain=1.0, desat=0.0):
    a = np.asarray(im).astype(np.float32)
    lum = a.mean(-1, keepdims=True)
    a = a * (1 - desat) + lum * desat
    return a * (np.array(rgb, np.float32) / 255.0) * gain


def variant(src, vid, rgb, gain=1.0, desat=0.0, norm=True, orm=True):
    save(tint(lib(src), rgb, gain, desat), f'{vid}_c.png')
    if norm and (n := lib(src, 'normal')) is not None:
        save(n, f'{vid}_n.png')
    if orm and (o := lib(src, 'orm')) is not None:
        save(o, f'{vid}_orm.png')


# ---- library variants -------------------------------------------------------------------------------------------------------------------------------------------------
def lib_variants():
    # facing brick: the library's clay brick, three firings
    variant('brick-clay-new-material-sphere-2', 'brick_red', (235, 150, 130), 1.45)
    variant('brick-clay-new-material-sphere-2', 'brick_brown', (215, 175, 150), 1.75)
    variant('brick-clay-new-material-sphere-2', 'brick_buff', (255, 215, 160), 1.9, 0.25)
    variant('brick-clay-old', 'brick_old', (255, 190, 165), 1.35)
    for vid, rgb, g in (('plaster_cream', (245, 232, 200), 0.95), ('plaster_sage', (190, 205, 180), 0.9), ('plaster_grey', (200, 202, 205), 0.85), ('plaster_rose', (230, 190, 180), 0.9),
                        ('plaster_white', (250, 250, 248), 1.0)):
        variant('stucko-wa1', vid, rgb, g * 1.0)
    variant('column-plaster-311', 'trim_white', (252, 252, 250), 1.0)
    variant('concrete-block', 'concrete_found', (200, 200, 195), 1.0)
    variant('concrete', 'concrete_plain', (255, 255, 255), 1.0, norm=False, orm=False)
    for vid, src in (('wood_pine', 'wood-pine'), ('wood_brown', 'wood-brown'), ('wood_dark', 'wood-dark-brown'), ('wood_oak', 'wood-oak')):
        variant(src, vid, (255, 255, 255), 1.0)
    variant('wood-blue', 'wood_blue', (255, 255, 255), 1.0)
    variant('bark01', 'bark', (255, 255, 255), 1.0, orm=False)
    variant('bark02', 'bark2', (255, 255, 255), 1.0, orm=False)
    variant('grass', 'grass', (255, 255, 255), 1.0)
    variant('ground-grass', 'verge', (255, 255, 255), 1.0, orm=False)
    variant('soil', 'soil', (255, 255, 255), 1.0)
    variant('rock-slate', 'slate', (255, 255, 255), 0.8)
    for vid, rgb in (('paint_green', (60, 95, 75)), ('paint_grey', (120, 125, 128)), ('paint_dark', (45, 47, 50)), ('paint_red', (170, 35, 30)), ('paint_blue', (40, 70, 130)),
                     ('paint_yellow', (220, 175, 30)), ('paint_white', (230, 230, 228)), ('paint_orange', (230, 110, 25)), ('paint_cream', (225, 215, 175)),
                     ('paint_sage', (120, 150, 130))):
        variant('metal-steel', vid, rgb, 1.15)
    variant('metal-rust', 'rust', (255, 255, 255), 1.0, orm=False)
    variant('metal-steel', 'steel', (255, 255, 255), 0.9)
    variant('metal-black', 'black_metal', (255, 255, 255), 1.0)
    for vid, rgb in (('awn_red', (190, 40, 40)), ('awn_green', (40, 110, 70)), ('awn_navy', (35, 55, 110)), ('awn_cream', (240, 232, 205)), ('awn_gold', (215, 170, 60)),
                     ('awn_burg', (110, 30, 45)), ('awn_white', (245, 245, 242))):
        variant('cloth-white-rough', vid, rgb, 1.35)


# ---- made for the game ---------------------------------------------------------------------------------------------------------------------------------------------------
def asphalt():
    base = np.asarray(lib('concrete-312')).astype(np.float32)
    lum = base.mean(-1, keepdims=True)
    big = tileable_noise(1024, 2.6, 7)[..., None]
    med = tileable_noise(1024, 1.6, 8)[..., None]
    c = (lum * 0.62 + 12) * (0.78 + 0.45 * big) * (0.92 + 0.16 * med)
    c = c * np.array([0.97, 0.98, 1.02]) + 4
    save(c, 'asphalt_c.png')
    save(lib('concrete-312', 'normal'), 'asphalt_n.png')
    o = np.zeros((1024, 1024, 3), np.float32)
    o[..., 0] = 255
    o[..., 1] = 215 - 35 * big[..., 0]
    save(o, 'asphalt_orm.png')
    c2 = (lum * 0.70 + 30) * (0.85 + 0.3 * big)             # the rubbed middle of a lane: lighter
    save(c2 * np.array([0.97, 0.98, 1.0]), 'asphalt_worn_c.png')


def sidewalk():
    # 1.5 m slab on 1024 px: library concrete, light broom texture, a tooled joint all round
    a = np.asarray(lib('concrete')).astype(np.float32) * np.array([1.0, 0.99, 0.95])
    broom = tileable_noise(1024, 0.8, 3)
    mott = tileable_noise(1024, 2.8, 4)[..., None]
    a = a * (0.86 + 0.25 * mott)
    hh = 0.5 + 0.12 * (broom - 0.5)
    for d in range(-5, 6):
        v = (1 - abs(d) / 6) * 0.35
        hh[d % 1024, :] -= v
        hh[:, d % 1024] -= v
    a = a * (1 - (0.5 - hh).clip(0) * 1.0)[..., None]
    save(a, 'sidewalk_c.png')
    save(normal_from_height(hh, 6.0), 'sidewalk_n.png')
    o = np.zeros((1024, 1024, 3), np.float32)
    o[..., 0] = 255
    o[..., 1] = 225
    save(o, 'sidewalk_orm.png')


def clapboard():
    # horizontal lap siding, 8 boards per 1.2 m tile (150 mm exposure): library wood grain under paint, shadow line under each board, a thickening lap
    grain = np.asarray(lib('wood-beige')).astype(np.float32).mean(-1)
    grain = (grain - grain.min()) / (grain.max() - grain.min())
    n_b = 8
    ph = 1024 // n_b
    hgt = np.zeros((1024, 1024), np.float32)
    shade = np.ones((1024, 1024), np.float32)
    for y in range(1024):
        t = (y % ph) / ph
        hgt[y, :] = 0.15 + 0.85 * t
        if t > 0.93:
            shade[y, :] = 0.42 + (1 - t) * 3.0
        elif t < 0.03:
            shade[y, :] = 1.08
    seams = np.ones((1024, 1024), np.float32)
    for b in range(n_b):
        for _ in range(2):
            x = int(rng.integers(0, 1024))
            seams[b * ph + 2:(b + 1) * ph - 4, x:x + 2] = 0.55
    gr = 0.86 + 0.28 * grain
    for k, (vid, rgb) in enumerate((('clap_white', (236, 234, 226)), ('clap_cream', (232, 214, 168)), ('clap_blue', (143, 170, 190)), ('clap_sage', (160, 180, 150)),
                                    ('clap_yellow', (226, 196, 110)), ('clap_grey', (170, 172, 168)), ('clap_red', (150, 55, 45)))):
        c = (np.array(rgb, np.float32)[None, None, :]) * (gr * shade * seams)[..., None]
        wear = tileable_noise(1024, 2.4, 100 + k)[..., None]
        save(c * (0.88 + 0.2 * wear), f'{vid}_c.png')
    save(normal_from_height(hgt + 0.03 * grain, 6.0), 'clap_n.png')
    o = np.zeros((1024, 1024, 3), np.float32)
    o[..., 0] = 255
    o[..., 1] = 190
    save(o, 'clap_orm.png')


def worn_alpha(n, seed, wear=0.35):
    a = tileable_noise(n, 1.8, seed)
    b = tileable_noise(n, 0.6, seed + 1)
    return np.clip(1.0 - wear * np.clip((a - 0.45) * 5, 0, 1) - 0.25 * np.clip((b - 0.6) * 4, 0, 1), 0.15, 1)


def paint():
    for vid, rgb, seed in (('line_white', (232, 232, 226), 31), ('line_yellow', (226, 178, 30), 32)):
        a = worn_alpha(512, seed)
        im = np.zeros((512, 512, 4), np.uint8)
        im[..., :3] = np.array(rgb, np.uint8)
        im[..., 3] = (a * 255).astype(np.uint8)
        Image.fromarray(im, 'RGBA').save(OUT / f'{vid}_c.png')


def decals():
    S = 512
    atlas = Image.new('RGBA', (4 * S, 4 * S), (0, 0, 0, 0))

    def put(i, im):
        atlas.alpha_composite(im, ((i % 4) * S, (i // 4) * S))

    def blank():
        return Image.new('RGBA', (S, S), (0, 0, 0, 0))

    def stain(seed, base=(10, 8, 6)):
        r = np.random.default_rng(seed)
        im = np.zeros((S, S), np.float32)
        yy, xx = np.mgrid[0:S, 0:S]
        for _ in range(8):
            cx, cy = r.uniform(0.25, 0.75) * S, r.uniform(0.25, 0.75) * S
            rr = r.uniform(0.07, 0.2) * S
            im += np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (rr ** 2)))
        im += 0.25 * (tileable_noise(S, 2.0, seed) - 0.5) * im.max()
        im = np.clip(im / im.max(), 0, 1) ** 1.2
        al = np.zeros((S, S, 4), np.uint8)
        al[..., :3] = base
        al[..., 3] = (im * 175).astype(np.uint8)
        return Image.fromarray(al, 'RGBA')

    def cracks(seed, branches=5):
        im = blank()
        d = ImageDraw.Draw(im)
        r = np.random.default_rng(seed)
        for _ in range(branches):
            x, y = r.uniform(0.1, 0.9) * S, r.uniform(0.1, 0.9) * S
            ang = r.uniform(0, 6.28)
            pts = [(x, y)]
            for _k in range(int(r.integers(10, 22))):
                ang += r.normal(0, 0.45)
                x += np.cos(ang) * r.uniform(8, 22)
                y += np.sin(ang) * r.uniform(8, 22)
                pts.append((x, y))
                if r.random() < 0.12:
                    d.line([(x, y), (x + r.normal(0, 40), y + r.normal(0, 40))], fill=(6, 6, 6, 150), width=1)
            d.line(pts, fill=(6, 6, 6, 215), width=int(r.integers(1, 4)))
        return im.filter(ImageFilter.GaussianBlur(0.7))

    put(0, stain(1))
    put(1, stain(2))
    put(2, cracks(3))
    put(3, cracks(4, 8))
    pn = tileable_noise(S, 1.4, 9)                              # 4: patch of newer asphalt with a tar-sealed edge
    patch = np.zeros((S, S, 4), np.uint8)
    patch[..., :3] = (np.array([66, 66, 69]) * (0.82 + 0.4 * pn[..., None])).astype(np.uint8)   # newer asphalt is only a little darker than the road (asphalt_c is 77): a near-black patch read as a hole
    yy, xx = np.mgrid[0:S, 0:S]
    edge = np.minimum(np.minimum(xx, S - 1 - xx), np.minimum(yy, S - 1 - yy)) / 36.0       # irregular, torn edge: noise bites into the rectangle
    bite = tileable_noise(S, 1.2, 21)
    patch[..., 3] = (np.clip((edge + (bite - 0.5) * 1.6) * 3.0, 0, 1) * 0.8 * 255).astype(np.uint8)
    im = Image.fromarray(patch.copy(), 'RGBA')
    d = ImageDraw.Draw(im)
    d.rectangle((14, 14, S - 15, S - 15), outline=(40, 40, 42, 200), width=5)   # the tar-sealed edge, a thin dark line
    for _ in range(3000):
        x, y = rng.integers(8, S - 8, 2)
        v = int(rng.integers(45, 95))
        d.point((int(x), int(y)), fill=(v, v, v + 2, 255))
    put(4, im)
    im = blank()                                                  # 5: manhole cover, cast iron, round
    d = ImageDraw.Draw(im)
    d.ellipse((6, 6, S - 7, S - 7), fill=(24, 22, 20, 255))
    d.ellipse((22, 22, S - 23, S - 23), fill=(52, 46, 42, 255))
    d.ellipse((34, 34, S - 35, S - 35), outline=(34, 30, 28, 255), width=4)
    for k in range(-12, 13):
        for m in range(-12, 13):
            cx, cy = S / 2 + k * 18 + (m % 2) * 9, S / 2 + m * 15
            if (cx - S / 2) ** 2 + (cy - S / 2) ** 2 < (S / 2 - 58) ** 2:
                d.polygon([(cx, cy - 6), (cx + 6, cy), (cx, cy + 6), (cx - 6, cy)], fill=(72, 66, 60, 255))
    d.rectangle((S / 2 - 70, S / 2 - 15, S / 2 + 70, S / 2 + 15), fill=(30, 28, 26, 255))
    d.text((S / 2 - 62, S / 2 - 14), 'WATER  DEPT', font=font('DejaVuSans-Bold.ttf', 22), fill=(86, 80, 74, 255))
    put(5, im)
    im = Image.new('RGBA', (S, S), (22, 21, 20, 255))             # 6: storm-drain inlet, cast frame with bars
    d = ImageDraw.Draw(im)
    d.rectangle((14, 14, S - 15, S - 15), fill=(5, 5, 5, 255))
    for k in range(7):
        x = 40 + k * 62
        d.rectangle((x, 20, x + 28, S - 21), fill=(48, 44, 40, 255))
    put(6, im)
    im = blank()                                                  # 7: tyre skid marks
    d = ImageDraw.Draw(im)
    for off in (180, 330):
        d.line([(off + 30 * np.sin(t / 90.0), t) for t in range(0, S, 6)], fill=(8, 8, 8, 170), width=22)
    put(7, im.filter(ImageFilter.GaussianBlur(2.5)))
    put(8, cracks(5, 3))
    put(9, stain(6, (14, 10, 6)))
    im = Image.fromarray(patch.copy(), 'RGBA')                    # 10: utility-cut trench strip
    ImageDraw.Draw(im).rectangle((0, 0, S - 1, S - 1), outline=(40, 40, 42, 200), width=4)
    put(10, im)
    atlas.save(OUT / 'decals_c.png')


def signs():
    """Road signs after the US MUTCD shapes and colours (federal, public domain). Atlas 2048 x 2048, 256 px cells; blades take two cells wide."""
    S = 256
    A = Image.new('RGBA', (2048, 2048), (0, 0, 0, 0))
    reg = {}
    fb = lambda s: font('DejaVuSans-Bold.ttf', s)  # noqa: E731

    def cell(name, col, row, w=1, h=1):
        reg[name] = [col * S / 2048, 1 - (row + h) * S / 2048, (col + w) * S / 2048, 1 - row * S / 2048]
        return (col * S, row * S, (col + w) * S, (row + h) * S)

    def centered(d, box, text, f, fill):
        x0, y0, x1, y1 = box
        bb = d.textbbox((0, 0), text, font=f)
        d.text(((x0 + x1) / 2 - (bb[2] - bb[0]) / 2 - bb[0], (y0 + y1) / 2 - (bb[3] - bb[1]) / 2 - bb[1]), text, font=f, fill=fill)

    d = ImageDraw.Draw(A)
    b = cell('stop', 0, 0)
    cx, cy, R = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2, 124
    oct_ = lambda r: [(cx + r * np.cos(np.pi / 8 + k * np.pi / 4), cy + r * np.sin(np.pi / 8 + k * np.pi / 4)) for k in range(8)]  # noqa: E731
    d.polygon(oct_(R), fill=(240, 240, 240, 255))
    d.polygon(oct_(R - 9), fill=(196, 28, 36, 255))
    centered(d, b, 'STOP', fb(76), (255, 255, 255, 255))
    b = cell('speed25', 1, 0)
    d.rounded_rectangle((b[0] + 14, b[1] + 6, b[2] - 14, b[3] - 6), 14, fill=(255, 255, 255, 255), outline=(10, 10, 10, 255), width=6)
    centered(d, (b[0], b[1] + 14, b[2], b[1] + 74), 'SPEED', fb(36), (10, 10, 10, 255))
    centered(d, (b[0], b[1] + 70, b[2], b[1] + 124), 'LIMIT', fb(36), (10, 10, 10, 255))
    centered(d, (b[0], b[1] + 120, b[2], b[3] - 14), '25', fb(104), (10, 10, 10, 255))
    b = cell('nopark', 2, 0)
    d.rounded_rectangle((b[0] + 24, b[1] + 6, b[2] - 24, b[3] - 6), 12, fill=(255, 255, 255, 255), outline=(190, 30, 36, 255), width=6)
    centered(d, (b[0], b[1] + 8, b[2], b[1] + 100), 'P', fb(110), (40, 70, 160, 255))
    d.ellipse((b[0] + 66, b[1] + 22, b[0] + 190, b[1] + 146), outline=(200, 30, 36, 255), width=10)
    d.line((b[0] + 82, b[1] + 40, b[0] + 174, b[1] + 130), fill=(200, 30, 36, 255), width=10)
    centered(d, (b[0], b[1] + 150, b[2], b[1] + 200), 'NO PARKING', fb(26), (190, 30, 36, 255))
    centered(d, (b[0], b[1] + 196, b[2], b[3] - 12), '8AM - 6PM', fb(22), (190, 30, 36, 255))
    b = cell('oneway', 3, 0)
    d.rectangle((b[0] + 4, b[1] + 60, b[2] - 4, b[3] - 60), fill=(10, 10, 10, 255), outline=(255, 255, 255, 255), width=4)
    d.polygon([(b[0] + 24, b[1] + 112), (b[0] + 150, b[1] + 112), (b[0] + 150, b[1] + 86), (b[0] + 232, b[1] + 128), (b[0] + 150, b[1] + 170), (b[0] + 150, b[1] + 144), (b[0] + 24, b[1] + 144)], fill=(255, 255, 255, 255))
    b = cell('xwalk', 4, 0)
    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    d.polygon([(cx, b[1] + 3), (b[2] - 3, cy), (cx, b[3] - 3), (b[0] + 3, cy)], fill=(214, 232, 40, 255), outline=(10, 10, 10, 255))
    d.ellipse((cx - 11, cy - 58, cx + 11, cy - 36), fill=(10, 10, 10, 255))
    d.line((cx, cy - 36, cx - 6, cy + 14), fill=(10, 10, 10, 255), width=14)
    d.line((cx - 4, cy - 28, cx + 28, cy - 4), fill=(10, 10, 10, 255), width=10)
    d.line((cx - 6, cy + 12, cx - 22, cy + 56), fill=(10, 10, 10, 255), width=11)
    d.line((cx - 4, cy + 12, cx + 20, cy + 54), fill=(10, 10, 10, 255), width=11)
    b = cell('closed', 5, 0)
    d.rectangle((b[0] + 4, b[1] + 40, b[2] - 4, b[3] - 40), fill=(238, 112, 20, 255), outline=(10, 10, 10, 255), width=5)
    centered(d, (b[0], b[1] + 44, b[2], b[1] + 128), 'ROAD', fb(54), (10, 10, 10, 255))
    centered(d, (b[0], b[1] + 124, b[2], b[3] - 44), 'CLOSED', fb(54), (10, 10, 10, 255))
    b = cell('set', 6, 0)
    d.rectangle((b[0] + 4, b[1] + 30, b[2] - 4, b[3] - 30), fill=(250, 250, 250, 255), outline=(190, 30, 36, 255), width=8)
    centered(d, (b[0], b[1] + 34, b[2], b[1] + 100), 'FILM SET', fb(42), (190, 30, 36, 255))
    centered(d, (b[0], b[1] + 98, b[2], b[1] + 160), 'NO ENTRY', fb(42), (10, 10, 10, 255))
    centered(d, (b[0], b[1] + 158, b[2], b[3] - 34), 'CREW ONLY', fb(28), (10, 10, 10, 255))
    b = cell('dne', 7, 0)
    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    d.ellipse((b[0] + 6, b[1] + 6, b[2] - 6, b[3] - 6), fill=(255, 255, 255, 255))
    d.ellipse((b[0] + 14, b[1] + 14, b[2] - 14, b[3] - 14), fill=(196, 28, 36, 255))
    d.rectangle((cx - 90, cy - 20, cx + 90, cy + 20), fill=(255, 255, 255, 255))
    names = ['MAIN ST', 'ELM ST', 'OAK ST', 'MILL ST', 'CHURCH ST', 'WALNUT ST', 'MAPLE AVE', 'DEPOT ST', 'RIVER RD', 'PARK AVE', '1ST AVE', 'LINCOLN ST']
    for i, nm in enumerate(names):
        col, row = (i % 4) * 2, 1 + i // 4
        box = cell('blade_' + nm.replace(' ', '_').lower(), col, row, 2, 1)
        b = (box[0], box[1] + 64, box[2], box[3] - 64)
        d.rounded_rectangle((b[0] + 4, b[1], b[2] - 4, b[3]), 8, fill=(18, 94, 58, 255), outline=(255, 255, 255, 255), width=4)
        centered(d, b, nm, fb(56), (255, 255, 255, 255))
    b = cell('meter', 0, 4)
    d.rounded_rectangle((b[0] + 40, b[1] + 20, b[2] - 40, b[3] - 20), 30, fill=(60, 64, 68, 255))
    d.rounded_rectangle((b[0] + 70, b[1] + 46, b[2] - 70, b[1] + 130), 16, fill=(205, 210, 205, 255))
    d.line((b[0] + 128, b[1] + 130, b[0] + 128, b[1] + 70), fill=(190, 20, 20, 255), width=4)
    centered(d, (b[0] + 70, b[1] + 135, b[2] - 70, b[1] + 175), 'EXPIRED', fb(18), (200, 200, 200, 255))
    b = cell('tape', 0, 5, 4, 1)
    d.rectangle((b[0], b[1] + 92, b[2], b[1] + 164), fill=(245, 205, 20, 255))
    for k in range(5):
        centered(d, (b[0] + k * 204, b[1] + 92, b[0] + (k + 1) * 204, b[1] + 164), 'FILM LINE', fb(40), (10, 10, 10, 255))
    A.save(OUT / 'signs_c.png')
    json.dump(reg, open(OUT / 'signs_atlas.json', 'w'), indent=1)


SHOP_NAMES = ['HARDWARE', 'FIVE & DIME', 'DINER', 'DRUG STORE', 'BARBER SHOP', 'BAKERY', 'SHOES', 'BOOKS & NEWS', 'JEWELERS', 'FURNITURE', 'TV & RADIO', 'SAVINGS BANK', 'HOTEL', 'LAUNDROMAT',
              'FLORIST', 'GROCERY', 'CAFE', 'THEATER', 'PHARMACY', 'LIQUORS', 'OFFICE SUPPLY', 'REAL ESTATE', 'INSURANCE', 'VIDEO RENTAL', 'RECORDS', 'PIZZA', 'SPORTING GOODS', 'TOYS',
              'TAVERN', 'DRY CLEANERS', 'FEED & SEED', 'ANTIQUES']


def shop_signs():
    """32 generic shop boards, 1024 x 128 each in a 2048 x 2048 atlas (2 columns, 16 rows); no real names."""
    A = Image.new('RGB', (2048, 2048), (0, 0, 0))
    d = ImageDraw.Draw(A)
    styles = [((30, 60, 40), (240, 230, 190), 'DejaVuSerif-Bold.ttf'), ((140, 25, 30), (245, 240, 230), 'DejaVuSans-Bold.ttf'), ((240, 235, 220), (30, 40, 90), 'DejaVuSerif-Bold.ttf'),
              ((25, 35, 70), (240, 200, 90), 'DejaVuSans-Bold.ttf'), ((235, 190, 50), (35, 30, 30), 'DejaVuSans-Bold.ttf'), ((40, 40, 44), (240, 240, 235), 'DejaVuSans-Bold.ttf'),
              ((70, 100, 120), (250, 250, 245), 'DejaVuSans-Bold.ttf'), ((110, 60, 35), (245, 225, 170), 'DejaVuSerif-Bold.ttf')]
    for i, nm in enumerate(SHOP_NAMES):
        col, row = i % 2, i // 2
        bg, fg, fn = styles[(i * 3 + i // 4) % len(styles)]
        x0, y0 = col * 1024, row * 128
        d.rectangle((x0, y0, x0 + 1023, y0 + 127), fill=bg)
        d.rectangle((x0 + 8, y0 + 8, x0 + 1015, y0 + 119), outline=fg, width=3)
        f = font(fn, 84)
        while d.textlength(nm, font=f) > 940:
            f = font(fn, f.size - 4)
        bb = d.textbbox((0, 0), nm, font=f)
        d.text((x0 + 512 - (bb[2] - bb[0]) / 2 - bb[0], y0 + 64 - (bb[3] - bb[1]) / 2 - bb[1]), nm, font=f, fill=fg)
    A.save(OUT / 'shopsigns_c.png')


def interiors():
    """Shop-window backdrops 512 x 256 (what is seen through the glass): dim warm room, shelves with goods, a counter; four variants."""
    A = Image.new('RGB', (1024, 512), (0, 0, 0))
    d = ImageDraw.Draw(A)
    r = np.random.default_rng(5)
    for v in range(4):
        x0, y0 = (v % 2) * 512, (v // 2) * 256
        wall = [(120, 100, 80), (110, 120, 105), (130, 105, 100), (95, 100, 120)][v]
        d.rectangle((x0, y0, x0 + 511, y0 + 255), fill=wall)
        d.rectangle((x0, y0 + 200, x0 + 511, y0 + 255), fill=(70, 55, 40))
        d.rectangle((x0, y0, x0 + 511, y0 + 22), fill=(190, 180, 150))
        for s in range(4):
            sy = y0 + 40 + s * 40
            d.rectangle((x0 + 12, sy + 28, x0 + 500, sy + 33), fill=(60, 45, 30))
            x = x0 + 16
            while x < x0 + 490:
                w, h = int(r.integers(10, 36)), int(r.integers(14, 28))
                col = tuple(int(c) for c in r.integers(60, 230, 3))
                d.rectangle((x, sy + 28 - h, x + w, sy + 28), fill=col)
                x += w + int(r.integers(2, 8))
        d.rectangle((x0 + 120, y0 + 170, x0 + 400, y0 + 210), fill=(88, 64, 44))
        for k in range(6):
            d.rectangle((x0 + 140 + k * 40, y0 + 160, x0 + 160 + k * 40, y0 + 172), fill=tuple(int(c) for c in r.integers(90, 230, 3)))
    A = A.filter(ImageFilter.GaussianBlur(1.3))
    Image.fromarray((np.asarray(A).astype(np.float32) * 0.55).astype(np.uint8)).save(OUT / 'interiors_c.png')


def leaves():
    """Leaf card, 512 x 512 RGBA: a spray of broad leaves, alpha cut-out (alphaMode MASK)."""
    S = 512
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = np.random.default_rng(11)
    greens = [(52, 88, 34), (64, 104, 38), (78, 120, 44), (46, 78, 30), (92, 130, 52)]
    for _ in range(260):
        x, y = r.uniform(30, S - 30), r.uniform(30, S - 30)
        if (x - S / 2) ** 2 + (y - S / 2) ** 2 > (S / 2 - 26) ** 2:
            continue
        a = r.uniform(0, 6.28)
        L, W = r.uniform(34, 60), r.uniform(16, 28)
        up = [(t * L, W * np.sin(np.pi * t) ** 0.8) for t in np.linspace(0, 1, 9)]
        pts = up + [(px, -py) for px, py in up[::-1]]
        c, s = np.cos(a), np.sin(a)
        poly = [(x + px * c - py * s, y + px * s + py * c) for px, py in pts]
        col = greens[int(r.integers(0, len(greens)))]
        d.polygon(poly, fill=col + (255,))
        d.line([(x, y), (x + L * c, y + L * s)], fill=(col[0] + 25, col[1] + 25, col[2] + 10, 255), width=1)
    im.save(OUT / 'leaves_c.png')


# ---- tree leaves: painted leaf sprigs, one 1024 x 1024 atlas per species and season (2 x 2 cells of 512: four sprig variants), ONE colour per tree ----------------------------------
LEAF_PAL = {   # (base, light) per species and season; every tree uses one of these, no mixed colours
    'maple': {'s': ((64, 106, 40), (88, 130, 50)), 'a': ((196, 72, 30), (226, 112, 38))},
    'elm': {'s': ((78, 112, 42), (102, 138, 52)), 'a': ((212, 168, 58), (234, 198, 88))},
    'oak': {'s': ((58, 88, 36), (78, 108, 44)), 'a': ((152, 90, 40), (180, 114, 52))},
}


def leaf_outline(kind, r):
    """Leaf outline in unit coordinates: petiole at the origin, blade along +x (length about 1), width in y. Returns the outline points and the vein segments."""
    pts, veins = [], []
    if kind == 'maple':                                   # palmate, five pointed lobes with teeth
        tips = [(-76, 0.72), (-38, 0.92), (0, 1.0), (38, 0.92), (76, 0.72)]
        notch = 0.62
        poly = [(0.04, 0.0)]
        for i, (a, rr) in enumerate(tips):
            if i:
                am = (tips[i - 1][0] + a) / 2
                poly.append((0.40 + notch * 0.55 * np.cos(np.radians(am)), notch * 0.75 * np.sin(np.radians(am))))
            for j in range(3):
                aa = a + (j - 1) * 13
                rl = rr * (1.0 if j == 1 else 0.78)
                poly.append((0.40 + rl * 0.62 * np.cos(np.radians(aa)), rl * 0.62 * np.sin(np.radians(aa)) * 1.25))
        poly.append((0.04, 0.0))
        pts = [(x * 1.0, y) for x, y in poly]
        for a, rr in tips:
            veins.append(((0.04, 0.0), (0.40 + rr * 0.55 * np.cos(np.radians(a)), rr * 0.55 * np.sin(np.radians(a)))))
    else:
        n = 36
        xs = np.linspace(0, 1, n)
        if kind == 'elm':
            w = 0.46 * np.sin(np.pi * xs ** 0.78) ** 0.85
            w = w * (1 + 0.07 * (((xs * 16) % 1.0) - 0.5))
            up, dn = w * 1.06, w * 0.88
        else:
            w = 0.40 * np.sin(np.pi * xs ** 0.9) ** 0.8 * (0.62 + 0.38 * np.abs(np.cos(np.pi * 4.5 * xs + 0.6)))
            up, dn = w, w * 0.96
        pts = [(x, y) for x, y in zip(xs, up)] + [(x, -y) for x, y in zip(xs[::-1], dn[::-1])]
        veins.append(((0.0, 0.0), (0.96, 0.0)))
        for k in range(1, 8):
            x = k * 0.115
            wk = np.interp(x, xs, w)
            veins.append(((x, 0.0), (x + 0.12, wk * 0.85)))
            veins.append(((x, 0.0), (x + 0.12, -wk * 0.85)))
    return pts, veins


def sprig_cell(kind, pal, seed, S=512, ss=3):
    """One sprig card: a fan of leafy twigs rising from the bottom centre (the point that sits on the branch tip). About 30 leaves of one colour, light variation only
    (9 percent lightness per leaf, darker back layer), vein lines, thin twig, alpha between the leaves, so that branches and sky show through a crown of many cards."""
    r = np.random.default_rng(seed)
    N = S * ss
    base, hi = (np.array(c, np.float32) for c in pal)
    rgb = Image.new('RGB', (N, N), tuple(int(c) for c in base))
    al = Image.new('L', (N, N), 0)
    dr, da = ImageDraw.Draw(rgb), ImageDraw.Draw(al)
    Lf = {'maple': 0.15, 'elm': 0.125, 'oak': 0.14}[kind] * N
    o = np.array([N * 0.5, N * 0.94])
    twig = []
    nb = int(r.integers(6, 9))
    leaves = []
    for b in range(nb):
        a = np.radians(-90 + (b - (nb - 1) / 2) * r.uniform(17, 23) + r.normal(0, 5))
        ln = r.uniform(0.5, 0.68) * N * (1.0 - 0.3 * abs(b - (nb - 1) / 2) / nb)
        p = o.copy()
        pts = [p.copy()]
        for k in range(7):
            a += r.normal(0, 0.08)
            p = p + np.array([np.cos(a), np.sin(a)]) * ln / 7
            pts.append(p.copy())
        twig.append(pts)
        for k in range(1, len(pts)):
            for side in (-1, 1):
                if r.random() < 0.8:
                    q = pts[k]
                    la = a + side * np.radians(r.uniform(40, 80)) + r.normal(0, 0.2)
                    leaves.append((q, la, r.uniform(0.78, 1.15)))
        leaves.append((pts[-1], a + r.normal(0, 0.25), r.uniform(0.9, 1.2)))
    leaves.sort(key=lambda l: l[0][1])
    for pts in twig:
        dr.line([tuple(p) for p in pts], fill=(70, 52, 34), width=3 * ss)
        da.line([tuple(p) for p in pts], fill=255, width=3 * ss)
    for (q, la, sc) in leaves:
        for layer, shade in ((0, 0.8), (1, 1.0)):
            if layer == 0 and r.random() < 0.5:
                continue
            ang = la + (0.0 if layer else r.normal(0, 0.1))
            pts, veins = leaf_outline(kind, r)
            ca, sa = np.cos(ang), np.sin(ang)
            s_ = Lf * sc * (0.9 if layer == 0 else 1.0)
            tr = lambda p: (q[0] + p[0] * s_ * ca - p[1] * s_ * 0.8 * sa, q[1] + p[0] * s_ * sa + p[1] * s_ * 0.8 * ca)  # noqa: E731
            poly = [tr(p) for p in pts]
            t = r.random()
            col = (base * (1 - t) + hi * t) * shade * r.uniform(0.93, 1.07)
            dr.polygon(poly, fill=tuple(int(min(255, c)) for c in col))
            da.polygon(poly, fill=255)
            dr.line(poly + [poly[0]], fill=tuple(int(c * 0.8) for c in col), width=max(1, ss))
            vc = tuple(int(min(255, c * 1.2 + 8)) for c in col)
            for a_, b_ in veins:
                dr.line([tr(a_), tr(b_)], fill=vc, width=max(1, ss // 2 + 1))
    rgb = rgb.resize((S, S), Image.LANCZOS)
    alpha = al.resize((S, S), Image.LANCZOS)
    out = rgb.convert('RGBA')
    out.putalpha(alpha)
    return out


def tree_leaves():
    for kind, pals in LEAF_PAL.items():
        for season, pal in pals.items():
            A = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
            for i in range(4):
                cell = sprig_cell(kind, pal, {'maple': 100, 'elm': 200, 'oak': 300}[kind] + i * 7 + (50 if season == 'a' else 0))
                A.alpha_composite(cell, ((i % 2) * 512, (i // 2) * 512))
            A.save(OUT / (f'leaf_{kind}_c.png' if season == 's' else f'leaf_{kind}_a_c.png'))


STEPS = [('lib', lambda: (unpack(), lib_variants())), ('asphalt', asphalt), ('sidewalk', sidewalk), ('clapboard', clapboard), ('paint', paint), ('decals', decals), ('signs', signs),
         ('shopsigns', shop_signs), ('interiors', interiors), ('leaves', leaves), ('treeleaves', tree_leaves)]

if __name__ == '__main__':
    only = arg('--only', '')
    for nm, fn in STEPS:
        if not only or nm in only.split(','):
            fn()
    print('textures in', OUT, len(list(OUT.glob('*'))))
