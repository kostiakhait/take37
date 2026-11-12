# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Texture preparation for the TAKE 37 fuel tanker (plain Python with Pillow; run:  python -I prep_textures.py).

1. Takes the tiling textures borrowed from the shared asset library (steel, black metal, rust, brown leather, grey fabric, dust, soil), unpacks the .ferret archives (zip) and
   resizes them to 1024 px into D:/temp/take37/tanker/tex/<name>_{base,normal,orm}.png
2. Draws the livery sheet decals.png (company name, hazard placards, plates, signs) and the reflective tape tile tape.png, and atlas.json with the rectangles (made for the game).
The company 'Holloway Fuel & Oil' and the 'HLW' plates are invented; the hazard diamond follows the public US DOT placard rules (red, white flame, class number 3).
"""
import io
import json
import zipfile

from PIL import Image, ImageDraw, ImageFont

LIB = 'D:/REPO/ferret/lib/ferret-assets/'
OUT = 'D:/temp/take37/tanker/tex/'
FONTS = 'C:/Windows/Fonts/'
USE = ['metal-steel', 'metal-black', 'metal-rust', 'leather-brown', 'gray-fabric1', 'cloth-grey', 'dust', 'soil']


def library():
    cat = json.load(open(LIB + 'catalog.json'))['packages']
    for n in USE:
        z = zipfile.ZipFile(LIB + cat['tex-' + n]['url'])
        for nm in z.namelist():
            if nm.startswith('textures/'):
                kind = {'basecolor': 'base', 'normal': 'normal', 'orm': 'orm'}[nm.split('/')[-1].split('.')[0]]
                im = Image.open(io.BytesIO(z.read(nm))).convert('RGB').resize((1024, 1024), Image.LANCZOS)
                im.save(f'{OUT}{n}_{kind}.png')
                print('lib', n, kind)


def font(name, size):
    return ImageFont.truetype(FONTS + name, size)


RED = (178, 24, 28, 255)
NAVY = (22, 42, 92, 255)
BLACK = (12, 12, 12, 255)
WHITE = (255, 255, 255, 255)
RECTS = {}


def rect(name, x, y, w, h):
    RECTS[name] = [x, y, w, h]


def centered(d, box, text, f, fill):
    x0, y0, x1, y1 = box
    bb = d.textbbox((0, 0), text, font=f)
    d.text(((x0 + x1) / 2 - (bb[0] + bb[2]) / 2, (y0 + y1) / 2 - (bb[1] + bb[3]) / 2), text, font=f, fill=fill)


def flame(d, cx, cy, s, fill):
    d.polygon([(cx, cy - s), (cx + 0.55 * s, cy - 0.05 * s), (cx + 0.5 * s, cy + 0.45 * s), (cx + 0.2 * s, cy + 0.85 * s), (cx - 0.3 * s, cy + 0.85 * s),
               (cx - 0.55 * s, cy + 0.4 * s), (cx - 0.45 * s, cy - 0.1 * s), (cx - 0.2 * s, cy + 0.15 * s), (cx - 0.25 * s, cy - 0.45 * s)], fill=fill)


def decals():
    W = 2048
    im = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for row, name, col in ((0, 'name_red', RED), (1, 'name_white', WHITE)):
        y0 = row * 384
        rect(name, 0, y0, 1536, 384)
        centered(d, (0, y0 + 10, 1536, y0 + 250), 'HOLLOWAY', font('ariblk.ttf', 215), col)
        centered(d, (0, y0 + 255, 1536, y0 + 370), 'FUEL  &  OIL  CO.', font('arialbd.ttf', 88), col)
    # DOT flammable placard: black edge, white line, red field, white flame, class number 3
    rect('placard_flammable', 0, 768, 512, 512)
    ox, oy, c = 0, 768, 256
    for inset, fill in ((4, (8, 8, 8, 255)), (14, (236, 236, 236, 255)), (34, (200, 26, 30, 255))):
        d.polygon([(ox + c, oy + inset), (ox + 512 - inset, oy + c), (ox + c, oy + 512 - inset), (ox + inset, oy + c)], fill=fill)
    flame(d, ox + c, oy + 205, 105, WHITE)
    centered(d, (ox + 156, oy + 340, ox + 356, oy + 440), '3', font('arialbd.ttf', 120), WHITE)
    # orange panel with the ID number 1203 (gasoline)
    rect('panel_1203', 512, 768, 512, 256)
    d.rectangle([512, 768, 1023, 1023], fill=BLACK)
    d.rectangle([520, 776, 1015, 1015], fill=(240, 120, 12, 255))
    d.rectangle([532, 788, 1003, 1003], outline=BLACK, width=6)
    centered(d, (512, 768, 1024, 1024), '1203', font('arialbd.ttf', 150), BLACK)
    for name, x, txt, sub in (('plate', 1024, 'HLW 4417', 'COMMERCIAL  1987'), ('plate2', 1536, 'TLR 0912', 'TRAILER  1987')):
        rect(name, x, 768, 512, 256)
        d.rounded_rectangle([x, 768, x + 511, 1023], 18, fill=(245, 240, 215, 255))
        d.rounded_rectangle([x + 10, 778, x + 501, 1013], 12, outline=NAVY, width=8)
        centered(d, (x, 792, x + 512, 848), 'TAKE 37 STATE', font('arialbd.ttf', 38), NAVY)
        centered(d, (x, 848, x + 512, 968), txt, font('arialbd.ttf', 120), NAVY)
        centered(d, (x, 964, x + 512, 1008), sub, font('arialbd.ttf', 32), NAVY)
    rect('gasoline', 0, 1280, 1024, 192)
    centered(d, (0, 1280, 1024, 1472), 'GASOLINE', font('impact.ttf', 190), BLACK)
    rect('flammable_word', 1024, 1280, 1024, 192)
    centered(d, (1024, 1280, 2048, 1472), 'FLAMMABLE', font('impact.ttf', 180), RED)
    rect('nosmoking', 0, 1472, 1024, 256)
    d.rounded_rectangle([0, 1472, 1023, 1727], 22, fill=(235, 235, 232, 255), outline=RED, width=10)
    centered(d, (0, 1480, 1024, 1600), 'NO SMOKING', font('arialbd.ttf', 120), RED)
    centered(d, (0, 1600, 1024, 1720), 'NO OPEN FLAME', font('arialbd.ttf', 96), BLACK)
    rect('capacity', 1024, 1472, 1024, 160)
    centered(d, (1024, 1472, 2048, 1632), 'CAPACITY  9,000  GAL.', font('arialbd.ttf', 92), BLACK)
    rect('unit', 1024, 1632, 512, 256)
    d.rounded_rectangle([1024, 1632, 1535, 1887], 14, fill=BLACK)
    centered(d, (1024, 1632, 1536, 1888), 'UNIT 37', font('arialbd.ttf', 120), WHITE)
    rect('datapl', 0, 1728, 1024, 320)
    d.rectangle([0, 1728, 1023, 2047], fill=(182, 184, 188, 255), outline=(40, 40, 40, 255), width=6)
    for i, t in enumerate(['CARGO TANK  SPECIFICATION  MC 306', 'HOLLOWAY TANK WORKS  DUNMORE', 'ALUMINIUM ALLOY  5454  /  5083', 'NOM. CAPACITY  9,000 U.S. GAL', 'TEST PRESSURE  3 PSIG   BUILT 1986']):
        d.text((24, 1744 + i * 58), t, font=font('courbd.ttf', 42), fill=(20, 20, 20, 255))
    rect('danger', 1536, 1632, 512, 256)
    d.rectangle([1536, 1632, 2047, 1887], fill=(240, 240, 240, 255), outline=RED, width=8)
    d.rectangle([1544, 1640, 2039, 1740], fill=RED)
    centered(d, (1544, 1640, 2039, 1740), 'DANGER', font('arialbd.ttf', 84), WHITE)
    centered(d, (1544, 1745, 2039, 1880), 'NO SMOKING', font('arialbd.ttf', 50), BLACK)
    rect('stripe_blue', 1024, 1888, 1024, 64)
    d.rectangle([1024, 1888, 2047, 1951], fill=NAVY)
    rect('stripe_red', 1024, 1952, 1024, 64)
    d.rectangle([1024, 1952, 2047, 2015], fill=RED)
    im.save(OUT + 'decals.png')
    json.dump(RECTS, open(OUT + 'atlas.json', 'w'), indent=1)
    # reflective conspicuity tape tile: 0.30 m = 150 mm red + 150 mm white
    t = Image.new('RGB', (256, 64), (235, 235, 235))
    ImageDraw.Draw(t).rectangle([0, 0, 127, 63], fill=(205, 20, 25))
    t.save(OUT + 'tape.png')


def grime():
    """Road dirt overlays with alpha, made from the borrowed soil and dust textures: dirt thick at the bottom edge, streaked upwards, with noise. v = 0 is the bottom of the strip."""
    import numpy as np
    rng = np.random.default_rng(37)
    N = 1024
    for name, lib, tint, strength, up in (('grime', 'dust', (150, 140, 124), 0.80, 0.55), ('grime_mud', 'soil', (95, 80, 62), 0.97, 0.80)):
        base = Image.open(f'{OUT}{lib}_base.png').convert('RGB').resize((N, N))
        arr = np.asarray(base).astype(np.float32) / 255.0
        t = np.array(tint, np.float32) / 255.0
        arr = arr * (t / max(arr.mean(), 1e-3)) ** 0.8 * 1.0
        # noise: sum of octaves, stretched vertically for streaks
        def octave(f, sx, sy):
            g = rng.random((max(2, N // f // sy), max(2, N // f // sx)))
            im = Image.fromarray((g * 255).astype(np.uint8)).resize((N, N), Image.BICUBIC)
            return np.asarray(im).astype(np.float32) / 255.0
        n = 0.5 * octave(64, 1, 4) + 0.3 * octave(24, 1, 6) + 0.2 * octave(8, 1, 1)
        v = np.linspace(1, 0, N)[:, None]                       # 1 at the bottom (row N-1 is v=0 after the flip below)
        v = np.broadcast_to(v[::-1], (N, N))                    # top row = 0 (clean), bottom row = 1 (dirty)
        a = np.clip((v ** 1.3 * 1.25 + (n - 0.5) * 0.9) * strength, 0, 1) * np.clip(1.0 - (1 - v) * 0.0, 0, 1)
        a = np.where(v > up, np.clip(a * 1.15, 0, 1), a * ((v / up) ** 1.5))
        # tile seamlessly in u by blending the edges
        w = np.minimum(np.arange(N), N - 1 - np.arange(N)) / 40.0
        a = a * np.clip(np.broadcast_to(w[None, :], (N, N)) * 0.0 + 1.0, 0, 1)
        out = np.dstack([np.clip(arr, 0, 1), np.clip(a, 0, 1)])
        Image.fromarray((out * 255).astype(np.uint8), 'RGBA').save(f'{OUT}{name}.png')
        print('grime', name)


if __name__ == '__main__':
    library()
    decals()
    grime()
