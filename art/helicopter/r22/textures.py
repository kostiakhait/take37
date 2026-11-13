# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Procedural textures of the R22 (numpy only, nothing copied from a photograph): the skin's panel lines and rivets (albedo multiplier + normal), the instrument panel with its gauges,
registration letters, blade stripes, the seat fabric and carpet weaves."""
import math
import numpy as np
from . import kit

FONT = {
    '0': ['01110', '10001', '10011', '10101', '11001', '10001', '01110'], '1': ['00100', '01100', '00100', '00100', '00100', '00100', '01110'],
    '2': ['01110', '10001', '00001', '00010', '00100', '01000', '11111'], '3': ['11110', '00001', '00001', '01110', '00001', '00001', '11110'],
    '4': ['00010', '00110', '01010', '10010', '11111', '00010', '00010'], '5': ['11111', '10000', '11110', '00001', '00001', '10001', '01110'],
    '6': ['00110', '01000', '10000', '11110', '10001', '10001', '01110'], '7': ['11111', '00001', '00010', '00100', '01000', '01000', '01000'],
    '8': ['01110', '10001', '10001', '01110', '10001', '10001', '01110'], '9': ['01110', '10001', '10001', '01111', '00001', '00010', '01100'],
    'A': ['01110', '10001', '10001', '11111', '10001', '10001', '10001'], 'B': ['11110', '10001', '10001', '11110', '10001', '10001', '11110'],
    'C': ['01110', '10001', '10000', '10000', '10000', '10001', '01110'], 'D': ['11110', '10001', '10001', '10001', '10001', '10001', '11110'],
    'E': ['11111', '10000', '10000', '11110', '10000', '10000', '11111'], 'F': ['11111', '10000', '10000', '11110', '10000', '10000', '10000'],
    'G': ['01110', '10001', '10000', '10111', '10001', '10001', '01111'], 'H': ['10001', '10001', '10001', '11111', '10001', '10001', '10001'],
    'I': ['01110', '00100', '00100', '00100', '00100', '00100', '01110'], 'K': ['10001', '10010', '10100', '11000', '10100', '10010', '10001'],
    'L': ['10000', '10000', '10000', '10000', '10000', '10000', '11111'], 'M': ['10001', '11011', '10101', '10101', '10001', '10001', '10001'],
    'N': ['10001', '11001', '10101', '10011', '10001', '10001', '10001'], 'O': ['01110', '10001', '10001', '10001', '10001', '10001', '01110'],
    'P': ['11110', '10001', '10001', '11110', '10000', '10000', '10000'], 'R': ['11110', '10001', '10001', '11110', '10100', '10010', '10001'],
    'S': ['01111', '10000', '10000', '01110', '00001', '00001', '11110'], 'T': ['11111', '00100', '00100', '00100', '00100', '00100', '00100'],
    'U': ['10001', '10001', '10001', '10001', '10001', '10001', '01110'], 'V': ['10001', '10001', '10001', '10001', '10001', '01010', '00100'],
    'W': ['10001', '10001', '10001', '10101', '10101', '11011', '10001'], 'X': ['10001', '10001', '01010', '00100', '01010', '10001', '10001'],
    'Y': ['10001', '10001', '01010', '00100', '00100', '00100', '00100'], 'Z': ['11111', '00001', '00010', '00100', '01000', '10000', '11111'],
    '-': ['00000', '00000', '00000', '11111', '00000', '00000', '00000'], ' ': ['00000'] * 7, '.': ['00000'] * 6 + ['00100'], '%': ['11001', '11010', '00010', '00100', '01000', '01011', '10011'],
}


def text_mask(txt, h, w=None, gap=0.25):
    """a float mask of the text, glyph height h px (bitmap font scaled with bilinear smoothing)"""
    gw = int(h * 5 / 7)
    gp = int(gw * gap)
    W = len(txt) * (gw + gp)
    out = np.zeros((h, W), np.float32)
    for i, ch in enumerate(txt):
        g = FONT.get(ch.upper(), FONT[' '])
        a = np.array([[int(c) for c in row] for row in g], np.float32)
        yy, xx = np.mgrid[0:h, 0:gw]
        sy, sx = yy * 7 / h, xx * 5 / gw
        iy, ix = np.minimum(sy.astype(int), 6), np.minimum(sx.astype(int), 4)
        out[:, i * (gw + gp):i * (gw + gp) + gw] = a[iy, ix]
    return out


def put_text(img, txt, x, y, h, col, anchor='c'):
    m = text_mask(txt, h)
    hh, ww = m.shape
    if anchor == 'c':
        x -= ww // 2
        y -= hh // 2
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + ww, img.shape[1]), min(y + hh, img.shape[0])
    if x1 <= x0 or y1 <= y0:
        return
    mm = m[y0 - y:y1 - y, x0 - x:x1 - x][..., None]
    img[y0:y1, x0:x1, :3] = img[y0:y1, x0:x1, :3] * (1 - mm) + np.array(col[:3]) * mm


# ---------------------------------------------------------------- skin

def skin_textures(size=1024):
    """tileable panel-line / rivet texture, 2 m x 1 m per tile (u along the airframe in metres / 2, v / 1); returns (albedo image, normal image)"""
    W, H = size * 2, size
    hgt = np.zeros((H, W), np.float32)
    alb = np.ones((H, W, 3), np.float32)
    rs = np.random.RandomState(kit.SEED)
    px_m = size  # pixels per metre
    # panel seams: vertical every 0.62 m and 0.9 m, horizontal at 0.33 and 0.7 m; with a double row of rivets either side
    lines_x = [0.0, 0.62, 1.24, 1.76]
    lines_y = [0.0, 0.33, 0.70]
    yy, xx = np.mgrid[0:H, 0:W]
    for lx in lines_x:
        d = np.abs(xx - lx * px_m)
        d = np.minimum(d, W - d)
        hgt -= np.exp(-(d / 1.4) ** 2) * 0.9
        alb *= (1 - 0.28 * np.exp(-(d / 1.6) ** 2))[..., None]
    for ly in lines_y:
        d = np.abs(yy - ly * px_m)
        d = np.minimum(d, H - d)
        hgt -= np.exp(-(d / 1.4) ** 2) * 0.9
        alb *= (1 - 0.28 * np.exp(-(d / 1.6) ** 2))[..., None]
    rivets = []
    for lx in lines_x:
        for t in np.arange(0.02, 1.0, 0.035):
            for o in (-0.012, 0.012):
                rivets.append(((lx + o) * px_m, t * px_m))
    for ly in lines_y:
        for t in np.arange(0.02, 2.0, 0.035):
            for o in (-0.012, 0.012):
                rivets.append((t * px_m, (ly + o) * px_m))
    for (cx, cy) in rivets:
        ix, iy = int(cx) % W, int(cy) % H
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                r2 = dx * dx + dy * dy
                if r2 <= 7:
                    hgt[(iy + dy) % H, (ix + dx) % W] += 0.55 * (1 - r2 / 8)
                    alb[(iy + dy) % H, (ix + dx) % W] *= 0.97
    # a few access panels with a little darker outline and a fastener
    for (x0, y0, w, h) in [(0.18, 0.08, 0.28, 0.17), (1.30, 0.42, 0.30, 0.2)]:
        for (a, b, c, d) in [(x0, y0, x0 + w, y0 + 0.0015), (x0, y0 + h, x0 + w, y0 + h + 0.0015), (x0, y0, x0 + 0.0015, y0 + h), (x0 + w, y0, x0 + w + 0.0015, y0 + h)]:
            hgt[int(b * px_m):int(d * px_m) + 2, int(a * px_m):int(c * px_m) + 2] -= 0.8
        for fx, fy in [(x0 + 0.02, y0 + 0.02), (x0 + w - 0.02, y0 + 0.02), (x0 + 0.02, y0 + h - 0.02), (x0 + w - 0.02, y0 + h - 0.02)]:
            for dx in range(-4, 5):
                for dy in range(-4, 5):
                    if dx * dx + dy * dy <= 16:
                        hgt[int(fy * px_m) + dy, int(fx * px_m) + dx] += 0.4
    n1, n2 = kit.noise(W, H, 64, 5), kit.noise(W, H, 12, 6)
    alb *= (0.94 + 0.06 * n1 - 0.03 * n2)[..., None]
    hgt += (n2 - 0.5) * 0.08
    a4 = np.concatenate([np.clip(alb, 0, 1), np.ones((H, W, 1), np.float32)], -1)
    # kit's noise is not tileable; blend the seam so repeats do not show a line
    return kit.image_from_array('skin_albedo', a4), kit.image_from_array('skin_normal', kit.height_to_normal(hgt, 1.6), srgb=False)


def weave_tex(name, base, size=256, scale=3, depth=0.2, seed=2):
    n = kit.noise(size, size, scale, seed)
    yy, xx = np.mgrid[0:size, 0:size]
    w = 0.5 + 0.5 * np.sin(xx * 0.5) * np.sin(yy * 0.5)
    v = 1 - depth * (0.6 * w + 0.4 * n)
    a = np.stack([v * base[0], v * base[1], v * base[2], np.ones_like(v)], -1)
    return kit.image_from_array(name, a)


def velour_tex(base):
    """seat velour: lengthwise stitch ribs"""
    size = 512
    n = kit.noise(size, size, 2, 4)
    yy, xx = np.mgrid[0:size, 0:size]
    rib = 0.5 + 0.5 * np.cos(xx * 2 * math.pi / 64)
    v = 0.78 + 0.18 * rib + 0.08 * (n - 0.5)
    a = np.stack([v * base[0], v * base[1], v * base[2], np.ones_like(v)], -1)
    return kit.image_from_array('velour', np.clip(a, 0, 1))


# ---------------------------------------------------------------- instruments

def disk(img, cx, cy, r, col, aa=1.2):
    H, W = img.shape[:2]
    x0, x1, y0, y1 = int(cx - r - 3), int(cx + r + 3), int(cy - r - 3), int(cy + r + 3)
    x0, y0 = max(x0, 0), max(y0, 0)
    x1, y1 = min(x1, W), min(y1, H)
    yy, xx = np.mgrid[y0:y1, x0:x1]
    d = np.hypot(xx - cx, yy - cy)
    a = np.clip((r - d) / aa + 0.5, 0, 1)[..., None]
    img[y0:y1, x0:x1, :3] = img[y0:y1, x0:x1, :3] * (1 - a) + np.array(col[:3]) * a


def ring(img, cx, cy, r, w, col, aa=1.2):
    H, W = img.shape[:2]
    x0, x1, y0, y1 = int(cx - r - 4), int(cx + r + 4), int(cy - r - 4), int(cy + r + 4)
    x0, y0 = max(x0, 0), max(y0, 0)
    x1, y1 = min(x1, W), min(y1, H)
    yy, xx = np.mgrid[y0:y1, x0:x1]
    d = np.abs(np.hypot(xx - cx, yy - cy) - r)
    a = np.clip((w / 2 - d) / aa + 0.5, 0, 1)[..., None]
    img[y0:y1, x0:x1, :3] = img[y0:y1, x0:x1, :3] * (1 - a) + np.array(col[:3]) * a


def line(img, x0, y0, x1, y1, w, col, aa=1.2):
    H, W = img.shape[:2]
    xa, xb = int(min(x0, x1) - w - 3), int(max(x0, x1) + w + 3)
    ya, yb = int(min(y0, y1) - w - 3), int(max(y0, y1) + w + 3)
    xa, ya = max(xa, 0), max(ya, 0)
    xb, yb = min(xb, W), min(yb, H)
    yy, xx = np.mgrid[ya:yb, xa:xb]
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy + 1e-9
    t = np.clip(((xx - x0) * dx + (yy - y0) * dy) / L2, 0, 1)
    d = np.hypot(xx - (x0 + t * dx), yy - (y0 + t * dy))
    a = np.clip((w / 2 - d) / aa + 0.5, 0, 1)[..., None]
    img[ya:yb, xa:xb, :3] = img[ya:yb, xa:xb, :3] * (1 - a) + np.array(col[:3]) * a


def arc_ticks(img, cx, cy, r, a0, a1, n, length, w, col, labels=None, lh=0, lr=0.0, major_every=1, minor_scale=0.55):
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        major = (i % major_every == 0)
        l = length if major else length * minor_scale
        ca, sa = math.sin(a), -math.cos(a)  # angle 0 at 12 o'clock, clockwise positive
        line(img, cx + ca * r, cy + sa * r, cx + ca * (r - l), cy + sa * (r - l), w, col)
        if labels and major and (i // major_every) < len(labels):
            put_text(img, labels[i // major_every], int(cx + ca * (r - length - lr)), int(cy + sa * (r - length - lr)), lh, col)


def needle(img, cx, cy, ang, length, w, col):
    a = math.radians(ang)
    line(img, cx - math.sin(a) * length * 0.18, cy + math.cos(a) * length * 0.18, cx + math.sin(a) * length, cy - math.cos(a) * length, w, col)


def gauge(img, cx, cy, R, kind):
    """one round instrument face of the R22 panel"""
    white, black = (0.93, 0.93, 0.9), (0.04, 0.04, 0.04)
    disk(img, cx, cy, R, black)
    ring(img, cx, cy, R * 0.98, R * 0.05, (0.35, 0.35, 0.36))
    lh = max(8, int(R * 0.17))
    if kind == 'airspeed':
        arc_ticks(img, cx, cy, R * 0.88, 20, 340, 10, R * 0.17, 2, white, ['0', '20', '40', '60', '80', '100', '120', '140', '160', '180'], lh, R * 0.02, 1)
        ring(img, cx, cy, R * 0.78, R * 0.04, (0.1, 0.7, 0.2))
        put_text(img, 'AIRSPEED', int(cx), int(cy + R * 0.35), lh, white)
        put_text(img, 'KNOTS', int(cx), int(cy + R * 0.55), lh, white)
        needle(img, cx, cy, 168, R * 0.8, 3, white)
    elif kind == 'altimeter':
        arc_ticks(img, cx, cy, R * 0.88, 0, 360, 50, R * 0.12, 1.5, white, None, 0, 0, 5)
        for i in range(10):
            a = math.radians(i * 36)
            put_text(img, str(i), int(cx + math.sin(a) * R * 0.66), int(cy - math.cos(a) * R * 0.66), lh, white)
        put_text(img, 'ALT', int(cx), int(cy + R * 0.3), lh, white)
        needle(img, cx, cy, 70, R * 0.78, 3, white)
        needle(img, cx, cy, 250, R * 0.5, 5, white)
    elif kind == 'tach':   # dual rotor/engine tachometer
        arc_ticks(img, cx, cy, R * 0.88, -120, 120, 12, R * 0.15, 2, white, ['0', '', '20', '', '40', '', '60', '', '80', '', '100', '', '120'], lh, R * 0.03, 1)
        ring(img, cx, cy, R * 0.74, R * 0.05, (0.1, 0.75, 0.2))
        line(img, cx + math.sin(math.radians(80)) * R * 0.88, cy - math.cos(math.radians(80)) * R * 0.88, cx + math.sin(math.radians(100)) * R * 0.88, cy - math.cos(math.radians(100)) * R * 0.88, 5, (0.8, 0.1, 0.1))
        put_text(img, 'RPM %', int(cx), int(cy + R * 0.42), lh, white)
        needle(img, cx, cy, 95, R * 0.8, 3, (0.9, 0.85, 0.2))
        needle(img, cx, cy, 98, R * 0.8, 4, white)
    elif kind == 'manifold':
        arc_ticks(img, cx, cy, R * 0.88, -140, 140, 14, R * 0.15, 2, white, ['10', '', '15', '', '20', '', '25', '', '30', '', '35', '', '', '', ''], lh, R * 0.03, 1)
        put_text(img, 'MAN PRESS', int(cx), int(cy + R * 0.45), lh, white)
        put_text(img, 'IN HG', int(cx), int(cy + R * 0.65), lh, white)
        needle(img, cx, cy, 30, R * 0.8, 3, white)
    elif kind == 'vsi':
        arc_ticks(img, cx, cy, R * 0.88, -170, 170, 12, R * 0.14, 2, white, None)
        put_text(img, 'VERT SPEED', int(cx), int(cy - R * 0.35), lh, white)
        put_text(img, 'FPM', int(cx), int(cy + R * 0.5), lh, white)
        needle(img, cx, cy, 90, R * 0.8, 3, white)
    elif kind == 'fuel':
        disk(img, cx, cy, R * 0.02, white)
        arc_ticks(img, cx, cy, R * 0.86, -60, 60, 4, R * 0.15, 2, white, ['E', '', 'H', '', 'F'], lh, 0, 1)
        put_text(img, 'FUEL', int(cx), int(cy + R * 0.5), lh, white)
        needle(img, cx, cy, -20, R * 0.7, 3, white)
    elif kind == 'oil':
        arc_ticks(img, cx, cy, R * 0.86, -90, 90, 6, R * 0.15, 2, white, None)
        put_text(img, 'OIL', int(cx), int(cy + R * 0.5), lh, white)
        needle(img, cx, cy, 20, R * 0.7, 3, white)
    elif kind == 'cht':
        arc_ticks(img, cx, cy, R * 0.86, -90, 90, 6, R * 0.15, 2, white, None)
        put_text(img, 'CHT', int(cx), int(cy + R * 0.5), lh, white)
        needle(img, cx, cy, -10, R * 0.7, 3, white)
    elif kind == 'amp':
        arc_ticks(img, cx, cy, R * 0.86, -70, 70, 4, R * 0.15, 2, white, None)
        put_text(img, 'AMPS', int(cx), int(cy + R * 0.5), lh, white)
        needle(img, cx, cy, 8, R * 0.7, 3, white)
    elif kind == 'carb':
        arc_ticks(img, cx, cy, R * 0.86, -90, 90, 6, R * 0.15, 2, white, None)
        put_text(img, 'CARB', int(cx), int(cy + R * 0.5), lh, white)
        needle(img, cx, cy, 15, R * 0.7, 3, white)
    elif kind == 'clock':
        arc_ticks(img, cx, cy, R * 0.86, 0, 360, 12, R * 0.12, 2, white, None)
        needle(img, cx, cy, 120, R * 0.55, 4, white)
        needle(img, cx, cy, 20, R * 0.8, 2, white)


def panel_texture(w=1024, h=512):
    """front of the instrument panel as seen by the pilot: a black moulded panel with the six large round gauges in the main block (layout of the R22 Beta II photograph: top row
    manifold pressure / R22 plug / airspeed / altimeter-style fuel? ... see README), a caution-light row on top, the smaller engine gauges on the lower console"""
    img = np.zeros((h, w, 4), np.float32)
    img[..., :3] = (0.05, 0.05, 0.055)
    img[..., 3] = 1
    n = kit.noise(w, h, 3, 9)
    img[..., :3] += (n[..., None] - 0.5) * 0.02
    R = 128
    # main block: 2 columns x 3 rows like the photograph: left column tach (top), manifold pressure (mid)... here upper-left tach, mid-left manifold, top-middle airspeed,
    # mid-middle VSI?, right column altimeter. Plugs ('R22') where there is no gauge.
    layout = [(210, 175, 'tach'), (210, 345, 'manifold'), (512, 140, 'airspeed'), (512, 330, 'altimeter'), (815, 175, 'vsi'), (815, 345, 'clock')]
    for cx, cy, k in layout:
        gauge(img, cx, cy, R, k)
    # caution lights row
    for i in range(10):
        x = 120 + i * 85
        disk(img, x, 22, 9, (0.95, 0.55, 0.05) if i not in (3,) else (0.2, 0.2, 0.2))
    for i, t in enumerate(['CLUTCH', 'LOW RPM', 'GEN', 'STARTER', 'LOW FUEL', 'OIL', 'ALT', 'BRAKE', 'CHIP', 'TEMP']):
        put_text(img, t, 120 + i * 85, 48, 8, (0.8, 0.8, 0.78))
    return kit.image_from_array('panel_front', img)


def console_texture(w=512, h=512):
    img = np.zeros((h, w, 4), np.float32)
    img[..., :3] = (0.045, 0.045, 0.05)
    img[..., 3] = 1
    for i, (k, x, y) in enumerate([('fuel', 130, 120), ('oil', 380, 120), ('cht', 130, 330), ('amp', 380, 330)]):
        gauge(img, x, y, 90, k)
    put_text(img, 'R22 BETA II', 256, 470, 22, (0.85, 0.85, 0.8))
    return kit.image_from_array('console_gauges', img)


def reg_texture(text='F-GT37', w=1536, h=256, col=(0.05, 0.08, 0.2)):
    m = text_mask(text, 200, gap=0.3)
    img = np.zeros((h, w, 4), np.float32)
    img[..., :3] = col
    hh, ww = m.shape
    a = np.zeros((h, w), np.float32)
    y0, x0 = (h - hh) // 2, (w - ww) // 2
    a[y0:y0 + hh, x0:x0 + ww] = m[:min(hh, h), :min(ww, w - x0)]
    img[..., 3] = a
    return kit.image_from_array('registration', img)


def hole_texture():
    """bullet hole decal: dark centre, petals of torn bright metal around it, soot ring; alpha"""
    S = 256
    img = np.zeros((S, S, 4), np.float32)
    yy, xx = np.mgrid[0:S, 0:S]
    cx = cy = S / 2
    dx, dy = xx - cx, yy - cy
    r = np.hypot(dx, dy)
    ang = np.arctan2(dy, dx)
    rs = np.random.RandomState(11)
    petals = 7
    rad = 38 + 26 * np.abs(np.sin(ang * petals / 2 + 0.7)) ** 3 + 6 * np.sin(ang * 3)
    soot = np.clip(1 - r / 110, 0, 1) ** 1.5
    metal = (r < rad + 14)
    hole = r < 22 + 5 * np.sin(ang * 5)
    img[..., :3] = (0.03, 0.03, 0.03)
    img[..., 3] = soot * 0.55
    mcol = np.array([0.72, 0.72, 0.7])
    img[metal, :3] = mcol[None, :] * (0.8 + 0.1 * np.sin(ang[metal] * 9 + r[metal] * 0.2))[:, None]
    img[metal, 3] = 1
    img[hole, :3] = 0.0
    img[hole, 3] = 1
    return kit.image_from_array('bullet_hole', img)


def blade_tex():
    """main rotor blade: black with yellow and white tip bands along u (root..tip)"""
    W, H = 512, 64
    img = np.zeros((H, W, 4), np.float32)
    img[..., :3] = (0.04, 0.04, 0.045)
    img[..., 3] = 1
    for a, b, c in [(0.62, 0.74, (0.9, 0.7, 0.05)), (0.74, 0.86, (0.92, 0.92, 0.9)), (0.86, 0.95, (0.9, 0.7, 0.05)), (0.95, 1.0, (0.92, 0.92, 0.9))]:
        img[:, int(a * W):int(b * W), :3] = c
    n = kit.noise(W, H, 4, 3)
    img[..., :3] *= (0.92 + 0.1 * n)[..., None]
    return kit.image_from_array('blade_bands', img)


def tail_blade_tex():
    W, H = 128, 64
    img = np.zeros((H, W, 4), np.float32)
    img[..., :3] = (0.04, 0.04, 0.045)
    img[..., 3] = 1
    for k in range(5):
        img[:, int((0.15 + k * 0.17) * W):int((0.15 + k * 0.17 + 0.085) * W), :3] = (0.92, 0.92, 0.9)
    return kit.image_from_array('tail_blade_bands', img)


def disc_texture(name='rotor_blur', size=256, peak=0.22, inner=0.15):
    """rotor blur: a radial alpha ramp (clear at the hub, strongest around 0.75 R, soft at the rim); white colour"""
    yy, xx = np.mgrid[0:size, 0:size]
    r = np.hypot(xx - size / 2 + 0.5, yy - size / 2 + 0.5) / (size / 2)
    a = np.where(r < 1.0, np.clip((r - inner) / (0.8 - inner), 0, 1) ** 1.2 * np.clip((1.0 - r) / 0.12, 0, 1), 0.0) * peak
    img = np.ones((size, size, 4), np.float32)
    img[..., 3] = a
    return kit.image_from_array(name, img)


def soot_texture():
    """soft black scorch with an irregular edge (alpha), for burnt patches around hits and the engine bay"""
    S = 256
    yy, xx = np.mgrid[0:S, 0:S]
    r = np.hypot(xx - S / 2 + 0.5, yy - S / 2 + 0.5) / (S / 2)
    n = kit.noise(S, S, 16, 21) * 0.5 + kit.noise(S, S, 6, 22) * 0.35 + kit.noise(S, S, 2, 23) * 0.15
    a = np.clip((1.0 - r * (0.75 + 0.5 * n)) * 1.8, 0, 1) ** 1.4 * 0.9
    img = np.zeros((S, S, 4), np.float32)
    img[..., :3] = (0.02, 0.018, 0.016)
    img[..., 3] = a
    return kit.image_from_array('soot_decal', img)
