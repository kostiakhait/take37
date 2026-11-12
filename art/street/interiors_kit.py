# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Real shop interiors for the TAKE 37 street (LOD0 buildings): a room behind the display windows with floor, walls, ceiling and lit fluorescent fixtures, shelving with product fronts
(goods atlas), counters and stools, mirrors, display cases, TV racks, washers ... chosen by the shop board (SHOP_NAMES order). Everything is drawn here, no library models.

Frame: the building's local frame (+X out of the front, shop front plane x = 0, glass at x = -0.22, the room runs back along -X, Y across, Z up).
The room is as wide as the shopfront between its piers and 5.5 - 7 m deep; the entrance aisle in front of the door is kept clear.
"""
import math
import random

import kitlib as K

# shop board index -> interior kind (indices follow textures_prep.SHOP_NAMES)
KIND = {0: 'hardware', 1: 'store', 2: 'diner', 3: 'drug', 4: 'barber', 5: 'bakery', 6: 'shoes', 7: 'books', 8: 'jewel', 9: 'furniture', 10: 'tv', 11: 'bank', 12: 'lobby', 13: 'laundry',
        14: 'florist', 15: 'grocery', 16: 'diner', 17: 'lobby', 18: 'drug', 19: 'liquor', 20: 'office', 21: 'office', 22: 'office', 23: 'video', 24: 'records', 25: 'diner', 26: 'store',
        27: 'toys', 28: 'tavern', 29: 'counter', 30: 'store', 31: 'antique'}
CELLS = {'grocery': [0, 1, 2, 3, 4, 5, 8, 6, 7, 0, 1, 2], 'store': [15, 3, 4, 5, 11, 14, 0, 6], 'hardware': [14, 14, 14, 15, 0, 5], 'drug': [5, 6, 7, 4, 15, 3, 5], 'shoes': [10, 10, 10, 11],
         'books': [9, 9, 9, 15], 'liquor': [6, 7, 6, 7, 6], 'toys': [11, 11, 3, 4, 11], 'video': [12], 'records': [13], 'bakery': [8, 8, 5], 'antique': [9, 14, 5, 10], 'office': [15, 9, 15],
         'diner': [5, 6, 7, 0, 2], 'tavern': [6, 7, 6, 7], 'counter': [15, 8, 5], 'florist': [15], 'laundry': [5, 4]}
STYLE = {  # wall, floor, back-wall wainscot
    'hardware': ('int_cream', 'int_oak', 'int_dark'), 'store': ('int_sage', 'floor_tile2', 'int_pine'), 'diner': ('int_cream', 'floor_tile', 'int_sage'), 'drug': ('int_ceil', 'floor_tile', 'int_pine'),
    'barber': ('int_sage', 'floor_tile', 'int_dark'), 'bakery': ('int_cream', 'floor_tile2', 'int_pine'), 'shoes': ('int_grey', 'int_oak', 'int_dark'), 'books': ('int_rose', 'int_oak', 'int_dark'),
    'jewel': ('int_grey', 'int_dark', 'int_dark'), 'furniture': ('int_cream', 'int_oak', 'int_pine'), 'tv': ('int_grey', 'floor_tile', 'int_dark'), 'bank': ('int_cream', 'floor_tile', 'int_dark'),
    'lobby': ('int_rose', 'int_oak', 'int_dark'), 'laundry': ('int_ceil', 'floor_tile', 'int_sage'), 'florist': ('int_sage', 'floor_tile2', 'int_pine'), 'grocery': ('int_cream', 'floor_tile2', 'int_pine'),
    'liquor': ('int_cream', 'floor_tile', 'int_dark'), 'office': ('int_grey', 'int_oak', 'int_dark'), 'video': ('int_grey', 'floor_tile', 'int_dark'), 'records': ('int_cream', 'int_oak', 'int_dark'),
    'toys': ('int_cream', 'floor_tile2', 'int_pine'), 'tavern': ('int_rose', 'int_oak', 'int_dark'), 'counter': ('int_cream', 'floor_tile', 'int_sage'), 'antique': ('int_rose', 'int_oak', 'int_brown'),
}


def gcell(i, e=0.004):
    c, r = i % 4, i // 4
    return (c / 4 + e, 1 - (r + 1) / 4 + e, (c + 1) / 4 - e, 1 - r / 4 - e)


def item(m, y, z, w, h, d, cell, x=0.0):
    """A product (packet, tin, box): front face carries the atlas cell, top face takes its colour. Front toward +X at x + d."""
    xf = x + d
    m.uvrect([(xf, y, z), (xf, y + w, z), (xf, y + w, z + h), (xf, y, z + h)], 'shelfgoods', gcell(cell), out=(1, 0, 0))
    u0, v0, u1, v1 = gcell(cell)
    uu, vv = u0 + (u1 - u0) * 0.3, v1 - (v1 - v0) * 0.08
    m.face([(x, y, z + h), (xf, y, z + h), (xf, y + w, z + h), (x, y + w, z + h)], 'shelfgoods', out=(0, 0, 1), uv=[(uu, vv)] * 4)
    m.face([(x, y + w, z), (xf, y + w, z), (xf, y + w, z + h), (x, y + w, z + h)], 'shelfgoods', out=(0, 1, 0), uv=[(uu, vv)] * 4)


def shelf_unit(m, w, h, d, cells, rnd, levels=5, bay=0.0, two_sided=False, clear_to=0.0):
    """Shelving: back at x = 0, front at x = d, y -w/2 .. w/2, z 0 .. h. Product rows on every board. clear_to: leave the bottom gap empty."""
    wood = 'int_dark'
    m.box(0.0, -w / 2, 0.0, 0.03, w / 2, h, wood)                                        # back
    for s in (-1, 1):
        m.box(0.0, s * w / 2 - 0.015, 0.0, d, s * w / 2 + 0.015, h, wood)                # uprights
    m.box(0.0, -w / 2, 0.0, d, w / 2, 0.12, wood)                                         # plinth
    gap = (h - 0.12) / levels
    for k in range(levels):
        z = 0.12 + k * gap
        m.box(0.03, -w / 2, z, d, w / 2, z + 0.025, 'int_pine')
        y = -w / 2 + 0.03
        while y < w / 2 - 0.12:
            if rnd.random() < 0.08:
                y += rnd.uniform(0.1, 0.25)
                continue
            pw = rnd.uniform(0.07, 0.17)
            if y + pw > w / 2 - 0.03:
                break
            ph = min(gap - 0.06, rnd.uniform(0.55, 0.95) * gap)
            pd = rnd.uniform(0.6, 0.95) * (d - 0.05)
            c = cells[rnd.randrange(len(cells))]
            item(m, y, z + 0.025, pw, ph, 0.05 + pd, c)
            y += pw + rnd.uniform(0.005, 0.03)
    m.box(0.0, -w / 2, h, d + 0.02, w / 2, h + 0.03, wood)                                # top


def counter(m, y0, y1, x0, x1, h=1.0, top='formica', body='int_dark', reg=True, stools=0, rnd=None):
    m.box(x0, y0, 0.0, x1, y1, h - 0.04, body)
    m.box(x0 - 0.04, y0 - 0.03, h - 0.04, x1 + 0.04, y1 + 0.03, h, top)
    if reg:
        yc = (y0 + y1) / 2
        m.box(x0 + 0.1, yc - 0.2, h, x0 + 0.5, yc + 0.2, h + 0.18, 'paint_cream', bv=0.01)         # cash register
        m.box(x0 + 0.12, yc - 0.14, h + 0.18, x0 + 0.4, yc + 0.14, h + 0.3, 'paint_dark')
        m.box(x0 + 0.5, yc - 0.17, h + 0.07, x0 + 0.52, yc + 0.17, h + 0.13, 'steel')
    for i in range(stools):
        yy = y0 + (y1 - y0) * (i + 0.5) / stools
        stool(m, x1 + 0.35, yy)


def stool(m, x, y):
    m.cyl(x, y, 0.0, 0.04, 0.2, 'chrome', seg=10, caps=(False, True))
    m.cyl(x, y, 0.04, 0.62, 0.025, 'chrome', seg=6)
    m.cyl(x, y, 0.62, 0.7, 0.19, 'leather', seg=12)


def fixtures(m, rm, rows=2):
    xs = [rm['xf'] - 1.3 - k * 2.6 for k in range(rows)]
    for x in xs:
        if x < rm['xb'] + 0.6:
            continue
        y = rm['ya'] + 1.0
        while y < rm['yb'] - 0.6:
            m.box(x - 0.15, y - 0.6, rm['zc'] - 0.06, x + 0.15, y + 0.6, rm['zc'], 'fluor_int')
            y += 3.0


def room(m, rm, kind, rnd):
    wall, floor, wain = STYLE[kind]
    xf, xb, ya, yb, zf, zc = rm['xf'], rm['xb'], rm['ya'], rm['yb'], rm['zf'], rm['zc']
    m.face([(xf, ya, zf), (xb, ya, zf), (xb, yb, zf), (xf, yb, zf)], floor, out=(0, 0, 1))
    m.face([(xf, ya, zc), (xf, yb, zc), (xb, yb, zc), (xb, ya, zc)], 'int_ceil', out=(0, 0, -1))
    m.face([(xb, ya, zf), (xb, ya, zc), (xb, yb, zc), (xb, yb, zf)], wall, out=(1, 0, 0))
    m.face([(xf, ya, zf), (xf, ya, zc), (xb, ya, zc), (xb, ya, zf)], wall, out=(0, 1, 0))
    m.face([(xb, yb, zf), (xb, yb, zc), (xf, yb, zc), (xf, yb, zf)], wall, out=(0, -1, 0))
    m.box(xb, ya, zf, xb + 0.02, yb, zf + 1.0, wain)                                           # wainscot
    m.box(xb, ya, zf + 1.0, xb + 0.04, yb, zf + 1.05, 'int_dark')
    m.box(xb, ya, zc - 0.12, xb + 0.12, yb, zc, 'trim_white')                                  # cove
    fixtures(m, rm)
    # a back-room door
    yd = (ya + yb) / 2 + rnd.uniform(-1.0, 1.0)
    m.box(xb, yd - 0.45, zf, xb + 0.06, yd + 0.45, zf + 2.05, 'int_dark')


def display_platform(m, rm, a, b, zb, cells, rnd, style):
    """Raised window display deck with the goods of the shop standing on it."""
    xf = rm['xf']
    m.box(xf - 1.25, a, rm['zf'], xf, b, zb - 0.02, 'int_dark')
    m.box(xf - 1.25, a, zb - 0.02, xf, b, zb, 'int_oak')
    y = a + 0.25
    while y < b - 0.3:
        k = rnd.random()
        h0 = zb
        if k < 0.35:                                                                           # a plinth with a larger piece on top
            ph = rnd.uniform(0.15, 0.4)
            m.box(xf - 0.9, y, h0, xf - 0.4, y + 0.5, h0 + ph, 'velvet' if style in ('jewel', 'shoes') else 'int_pine')
            h0 += ph
            item(m, y + 0.08, h0, 0.34, rnd.uniform(0.25, 0.5), 0.3, cells[rnd.randrange(len(cells))], x=xf - 0.85)
            y += 0.65
        else:
            for _ in range(rnd.randint(2, 4)):
                w = rnd.uniform(0.12, 0.22)
                hh = rnd.uniform(0.15, 0.32)
                item(m, y, h0, w, hh, rnd.uniform(0.1, 0.2), cells[rnd.randrange(len(cells))], x=xf - rnd.uniform(0.5, 0.95))
                y += w + 0.02
            y += rnd.uniform(0.1, 0.4)


# ---------------------------------------------------------------------------------------------------------------------------- generators by kind
def store_like(m, rm, kind, door, rnd, cells):
    xf, xb, ya, yb = rm['xf'], rm['xb'], rm['ya'], rm['yb']
    # back wall shelving
    wcount = int((yb - ya - 0.3) // 1.2)
    y = ya + 0.15
    for i in range(wcount):
        m.at(xb + 0.0, y + 0.6, rm['zf'], rz=0.0)
        shelf_unit(m, 1.2, 2.3, 0.4, cells, rnd, levels=5)
        m.pop()
        y += 1.2
    # side walls: units facing inward
    for (yy, rz) in ((ya, -math.pi / 2), (yb, math.pi / 2)):
        x = xf - 1.7
        while x > xb + 2.0:
            m.at(x, yy, rm['zf'], rz=math.pi / 2 if yy == ya else -math.pi / 2)
            shelf_unit(m, 1.2, 1.9, 0.35, cells, rnd, levels=4)
            m.pop()
            x -= 1.3
    # a low gondola parallel to the window, two-sided
    gx = xf - 3.0
    y = ya + 0.8
    while y < yb - 1.2:
        if abs(y + 0.9 - door) < 1.2:
            y += 1.8
            continue
        m.at(gx, y + 0.9, rm['zf'], rz=0.0)
        shelf_unit(m, 1.8, 1.25, 0.45, cells, rnd, levels=3)
        m.pop()
        m.at(gx - 0.9, y + 0.9, rm['zf'], rz=math.pi)
        shelf_unit(m, 1.8, 1.25, 0.45, cells, rnd, levels=3)
        m.pop()
        y += 2.2
    # checkout counter by the door
    side = 1 if door < (ya + yb) / 2 else -1
    cy = door + side * 2.4
    cy = min(max(cy, ya + 1.0), yb - 1.0)
    counter(m, cy - 0.9, cy + 0.9, xf - 1.6, xf - 1.0, rnd=rnd)


def diner(m, rm, door, rnd):
    xf, xb, ya, yb, zf = rm['xf'], rm['xb'], rm['ya'], rm['yb'], rm['zf']
    cx = xf - 3.3
    m.box(cx - 0.45, ya + 0.4, zf, cx + 0.05, yb - 0.4, zf + 1.05, 'int_dark')              # the long counter parallel to the street
    m.box(cx - 0.55, ya + 0.35, zf + 1.05, cx + 0.15, yb - 0.35, zf + 1.1, 'formica')
    m.box(cx - 0.3, ya + 0.4, zf + 0.5, cx + 0.04, yb - 0.4, zf + 0.54, 'chrome')
    n = int((yb - ya - 0.8) / 0.75)
    for i in range(n):
        yy = ya + 0.4 + (i + 0.5) * (yb - ya - 0.8) / n
        if abs(yy - door) < 0.8:
            continue
        stool(m, cx + 0.5, yy)
    # back bar: shelf with cups, a coffee urn, the pie case
    m.box(xb + 0.0, ya + 0.3, zf, xb + 0.7, yb - 0.3, zf + 1.0, 'int_pine')
    m.box(xb + 0.0, ya + 0.3, zf + 1.0, xb + 0.75, yb - 0.3, zf + 1.04, 'formica')
    for k in range(6):
        yy = ya + 1.2 + k * ((yb - ya - 2.4) / 6)
        if k % 2 == 0:
            m.cyl(xb + 0.4, yy, zf + 1.04, zf + 1.5, 0.13, 'chrome', seg=10)
        else:
            m.box(xb + 0.12, yy, zf + 1.04, xb + 0.55, yy + 0.55, zf + 1.35, 'glass')
            m.box(xb + 0.2, yy + 0.05, zf + 1.1, xb + 0.5, yy + 0.5, zf + 1.18, 'petal_yellow')
    m.box(xb, ya + 0.3, zf + 1.65, xb + 0.3, yb - 0.3, zf + 1.7, 'int_pine')                  # shelf of cups
    y = ya + 0.5
    while y < yb - 0.6:
        item(m, y, zf + 1.7, 0.14, 0.12, 0.14, 2, x=xb + 0.05)
        y += 0.2
    m.box(xb, ya + 0.3, zf + 1.4, xb + 0.02, yb - 0.3, zf + 2.4, 'mirror')                      # mirror behind the bar
    # booths along the window: two benches with a table each, seen from outside
    for yy in (ya + 1.0, yb - 2.6):
        if abs(yy + 0.8 - door) < 1.3:
            continue
        m.box(xf - 1.35, yy, zf, xf - 0.55, yy + 1.6, zf + 0.45, 'leather')
        m.box(xf - 1.35, yy, zf + 0.45, xf - 1.25, yy + 1.6, zf + 1.15, 'leather')
        m.box(xf - 0.75, yy + 0.3, zf + 0.7, xf - 0.1, yy + 1.3, zf + 0.74, 'formica')
        m.cyl(xf - 0.42, yy + 0.8, zf, zf + 0.7, 0.03, 'chrome', seg=6)
    # menu board
    m.uvrect([(xb + 0.05, yb - 3.8, zf + 1.7), (xb + 0.05, yb - 2.2, zf + 1.7), (xb + 0.05, yb - 2.2, zf + 2.6), (xb + 0.05, yb - 3.8, zf + 2.6)], 'poster_int', (0.0, 0.5 - 0.0, 0.25, 0.75), out=(1, 0, 0))


def barber(m, rm, door, rnd):
    xf, xb, ya, yb, zf = rm['xf'], rm['xb'], rm['ya'], rm['yb'], rm['zf']
    for i in range(3):
        yy = ya + 1.2 + i * 2.2
        if yy > yb - 1.0 or abs(yy - door) < 0.9:
            continue
        m.at(xb + 1.3, yy, zf, rz=math.pi)
        m.lathe([(0.0, 0.0), (0.3, 0.0), (0.3, 0.04), (0.08, 0.1), (0.07, 0.4)], 'chrome', seg=12)       # barber chair: base, hydraulic post
        m.box(-0.28, -0.3, 0.4, 0.28, 0.3, 0.5, 'leather', bv=0.04)
        m.box(-0.32, -0.3, 0.5, -0.22, 0.3, 1.2, 'leather', bv=0.04)
        m.box(-0.3, 0.32, 0.5, 0.2, 0.37, 0.7, 'chrome')
        m.box(-0.3, -0.37, 0.5, 0.2, -0.32, 0.7, 'chrome')
        m.pop()
    m.box(xb, ya + 0.2, zf + 0.9, xb + 0.5, yb - 0.2, zf + 0.95, 'formica')                       # counter under the mirror
    m.box(xb, ya + 0.2, zf, xb + 0.45, yb - 0.2, zf + 0.9, 'int_dark')
    m.box(xb + 0.0, ya + 0.2, zf + 0.95, xb + 0.03, yb - 0.2, zf + 2.4, 'mirror')
    for k in range(12):
        yy = ya + 0.5 + k * ((yb - ya - 1.0) / 12)
        m.cyl(xb + 0.25, yy, zf + 0.95, zf + 1.2, 0.035, 'amber_lens' if k % 3 == 0 else ('green_lens' if k % 3 == 1 else 'glass'), seg=8)
    # a waiting bench and magazines
    m.box(xf - 1.6, ya + 0.6, zf, xf - 1.0, ya + 2.4, zf + 0.45, 'leather')
    m.box(xf - 1.6, ya + 0.6, zf + 0.45, xf - 1.5, ya + 2.4, zf + 0.95, 'leather')
    # the barber pole in the display window
    m.cyl(xf - 0.5, yb - 0.5, 0.55, 1.75, 0.1, 'enamel_white', seg=14)
    for k in range(5):
        m.cyl(xf - 0.5, yb - 0.5, 0.6 + k * 0.25, 0.7 + k * 0.25, 0.102, 'red_lens' if k % 2 == 0 else 'paint_blue', seg=14, caps=(False, False))


def jewel(m, rm, door, rnd):
    xf, xb, ya, yb, zf = rm['xf'], rm['xb'], rm['ya'], rm['yb'], rm['zf']
    for row, x in enumerate((xf - 1.8, xf - 4.0)):
        y = ya + 0.7
        while y < yb - 2.0:
            if abs(y + 0.9 - door) < 1.4:
                y += 1.8
                continue
            m.box(x - 0.35, y, zf, x + 0.35, y + 1.7, zf + 0.9, 'int_dark')                       # case
            m.box(x - 0.33, y + 0.02, zf + 0.9, x + 0.33, y + 1.68, zf + 0.95, 'velvet')
            for k in range(6):
                m.cyl(x + rnd.uniform(-0.2, 0.2), y + 0.2 + k * 0.26, zf + 0.95, zf + 0.97, rnd.uniform(0.03, 0.06), 'gold' if k % 2 else 'chrome', seg=8)
            m.box(x - 0.35, y, zf + 0.95, x + 0.35, y + 0.015, zf + 1.2, 'glass')
            m.box(x - 0.35, y + 1.685, zf + 0.95, x + 0.35, y + 1.7, zf + 1.2, 'glass')
            m.box(x - 0.35, y, zf + 1.2, x + 0.35, y + 1.7, zf + 1.22, 'glass')
            m.box(x + 0.34, y, zf + 0.95, x + 0.35, y + 1.7, zf + 1.2, 'glass')
            y += 2.1
    m.box(xb, ya + 0.3, zf + 0.9, xb + 0.03, yb - 0.3, zf + 2.4, 'mirror')
    for k in range(5):                                                                              # wall clock and display shelves
        m.box(xb + 0.03, ya + 0.5 + k * ((yb - ya - 1.2) / 5), zf + 1.5, xb + 0.2, ya + 0.5 + k * ((yb - ya - 1.2) / 5) + 0.6, zf + 1.53, 'glass')
    m.at(xb + 0.1, (ya + yb) / 2 + 1.5, zf + 2.3, ry=math.pi / 2)
    m.lathe([(0.0, 0.0), (0.22, 0.0), (0.22, 0.04), (0.0, 0.04)], 'enamel_white', seg=18)
    m.pop()


def furniture(m, rm, door, rnd):
    xf, xb, ya, yb, zf = rm['xf'], rm['xb'], rm['ya'], rm['yb'], rm['zf']
    mats = ['fabric_blue', 'fabric_green', 'fabric_ochre', 'leather']
    y = ya + 0.8
    k = 0
    while y < yb - 2.2:
        if abs(y + 1.0 - door) < 1.4:
            y += 2.0
            continue
        fm = mats[k % 4]
        x = xf - 2.2 - (k % 2) * 1.2
        m.box(x - 0.45, y - 0.02, zf + 0.0, x + 0.45, y + 2.1, zf + 0.12, 'int_dark')              # a sofa: base, seat, back, arms
        m.box(x - 0.45, y, zf + 0.12, x + 0.45, y + 2.1, zf + 0.45, fm, bv=0.06)
        m.box(x - 0.5, y, zf + 0.45, x - 0.3, y + 2.1, zf + 0.95, fm, bv=0.06)
        m.box(x - 0.45, y - 0.02, zf + 0.45, x + 0.45, y + 0.18, zf + 0.65, fm, bv=0.05)
        m.box(x - 0.45, y + 1.92, zf + 0.45, x + 0.45, y + 2.12, zf + 0.65, fm, bv=0.05)
        # rug and coffee table
        m.box(x + 0.6, y + 0.1, zf, x + 1.7, y + 1.9, zf + 0.012, 'rug_red')
        m.box(x + 0.8, y + 0.6, zf + 0.3, x + 1.4, y + 1.4, zf + 0.34, 'int_oak')
        for yy in (0.62, 1.38):
            for xx in (0.82, 1.38):
                m.cyl(x + xx, y + yy, zf, zf + 0.3, 0.02, 'int_dark', seg=5)
        y += 2.8
        k += 1
    # lamps and a bookcase on the back wall
    for yy in (ya + 1.0, yb - 1.0):
        m.cyl(xb + 0.5, yy, zf, zf + 1.1, 0.02, 'brass', seg=6)
        m.lathe([(0.12, 0.0), (0.22, 0.25), (0.2, 0.28)], 'lampshade', x=xb + 0.5, y=yy, seg=12) if False else None
        m.at(xb + 0.5, yy, zf + 1.1)
        m.lathe([(0.1, 0.0), (0.2, 0.26)], 'lampshade', seg=12)
        m.pop()
    m.at(xb, (ya + yb) / 2, zf)
    shelf_unit(m, 2.0, 2.2, 0.4, CELLS['books'], rnd, levels=5)
    m.pop()


def tv(m, rm, door, rnd):
    xf, xb, ya, yb, zf = rm['xf'], rm['xb'], rm['ya'], rm['yb'], rm['zf']
    y = ya + 0.2
    while y < yb - 1.4:
        if abs(y + 0.7 - door) < 1.2:
            y += 1.6
            continue
        for tier in range(3):                                                                      # a pyramid rack of TV sets
            z0 = zf + tier * 0.58
            if tier == 0:
                m.box(xf - 2.2, y, zf, xf - 1.1, y + 1.4, zf + 0.03, 'int_dark')
            w = 0.62
            for j in range(2 if tier < 2 else 1):
                yy = y + 0.05 + j * (w + 0.06) + (0.34 if tier == 2 else 0.0)
                m.box(xf - 2.15, yy, z0 + 0.03, xf - 1.2, yy + w, z0 + 0.03 + 0.52, 'int_dark', bv=0.02)             # cabinet
                m.face([(xf - 1.2 + 0.001, yy + 0.05, z0 + 0.09), (xf - 1.2 + 0.001, yy + w - 0.05, z0 + 0.09), (xf - 1.2 + 0.001, yy + w - 0.05, z0 + 0.5), (xf - 1.2 + 0.001, yy + 0.05, z0 + 0.5)], 'tvscreen', out=(1, 0, 0))
        y += 1.7
    for k in range(3):                                                                              # speakers and radios on the back wall shelves
        m.at(xb, ya + 1.2 + k * 2.4, zf)
        shelf_unit(m, 2.0, 2.2, 0.45, [11, 12, 5, 13], rnd, levels=4)
        m.pop()
    counter(m, door - 3.2, door - 1.4, xf - 3.4, xf - 2.7, rnd=rnd)


def bank(m, rm, door, rnd):
    xf, xb, ya, yb, zf = rm['xf'], rm['xb'], rm['ya'], rm['yb'], rm['zf']
    cx = xf - 3.2
    m.box(cx - 0.5, ya + 0.4, zf, cx + 0.4, yb - 0.4, zf + 1.1, 'int_dark')                            # teller counter with glass partitions
    m.box(cx - 0.6, ya + 0.35, zf + 1.1, cx + 0.5, yb - 0.35, zf + 1.15, 'formica')
    n = int((yb - ya - 1.0) / 2.0)
    for i in range(n + 1):
        yy = ya + 0.5 + i * (yb - ya - 1.0) / max(1, n)
        m.box(cx - 0.55, yy, zf + 1.15, cx + 0.45, yy + 0.03, zf + 1.9, 'glass')
        m.box(cx - 0.55, yy, zf + 1.15, cx - 0.5, yy + 0.03, zf + 1.9, 'brass')
    m.box(cx - 0.55, ya + 0.4, zf + 1.85, cx + 0.45, yb - 0.4, zf + 1.9, 'brass')
    m.at(xb + 0.05, (ya + yb) / 2, zf + 1.25, ry=-math.pi / 2)                                          # a round vault door at the back
    m.lathe([(0.0, 0.0), (0.9, 0.0), (0.9, 0.18), (0.0, 0.18)], 'steel', seg=24)
    m.lathe([(0.0, 0.18), (0.6, 0.18), (0.6, 0.24), (0.0, 0.24)], 'chrome', seg=24)
    m.pop()
    m.at(xb + 0.04, (ya + yb) / 2 + 2.6, zf + 2.3, ry=math.pi / 2)
    m.lathe([(0.0, 0.0), (0.3, 0.0), (0.3, 0.05), (0.0, 0.05)], 'enamel_white', seg=18)                 # wall clock
    m.pop()
    for (yy, d) in ((ya + 1.0, 1.0), (yb - 1.0, -1.0)):                                                 # desks with chairs
        m.box(xf - 1.8, yy - 0.5, zf, xf - 1.0, yy + 0.5, zf + 0.75, 'int_dark')


def laundry(m, rm, door, rnd):
    xf, xb, ya, yb, zf = rm['xf'], rm['xb'], rm['ya'], rm['yb'], rm['zf']
    n = int((yb - ya - 0.6) // 0.8)
    for i in range(n):
        y = ya + 0.4 + i * 0.8
        for (x, hh) in ((xb + 0.05, zf), (xf - 4.2, zf)):
            m.box(x, y, hh, x + 0.7, y + 0.72, hh + 0.95, 'enamel_white', bv=0.02)
            m.at(x + 0.7, y + 0.36, hh + 0.5, ry=math.pi / 2)
            m.lathe([(0.0, 0.0), (0.24, 0.0), (0.24, 0.03), (0.2, 0.03), (0.0, 0.03)], 'steel', seg=16)
            m.lathe([(0.0, 0.03), (0.2, 0.03), (0.0, 0.08)], 'glass', seg=16)
            m.pop()
            m.box(x + 0.7, y + 0.1, hh + 0.82, x + 0.72, y + 0.62, hh + 0.9, 'paint_blue')
    m.box(xf - 2.6, ya + 0.6, zf + 0.8, xf - 1.8, yb - 0.6, zf + 0.85, 'formica')                       # folding table
    for yy in (ya + 0.65, yb - 0.65):
        for xx in (xf - 2.55, xf - 1.85):
            m.cyl(xx, yy, zf, zf + 0.8, 0.025, 'chrome', seg=5)
    for k in range(4):                                                                                  # molded chairs along the window
        yy = ya + 1.0 + k * 1.6
        if abs(yy - door) > 0.9:
            m.box(xf - 0.7, yy, zf + 0.4, xf - 0.3, yy + 0.4, zf + 0.45, 'paint_orange')
            m.box(xf - 0.72, yy, zf + 0.45, xf - 0.66, yy + 0.4, zf + 0.85, 'paint_orange')
            for (xx, y2) in ((xf - 0.65, yy + 0.04), (xf - 0.35, yy + 0.04), (xf - 0.65, yy + 0.36), (xf - 0.35, yy + 0.36)):
                m.cyl(xx, y2, zf, zf + 0.4, 0.015, 'chrome', seg=4)


def florist(m, rm, door, rnd):
    xf, xb, ya, yb, zf = rm['xf'], rm['xb'], rm['ya'], rm['yb'], rm['zf']
    petals = ['petal_red', 'petal_yellow', 'petal_pink', 'petal_white']
    for (x, rowz) in ((xf - 1.8, 0.0), (xf - 3.3, 0.0)):
        y = ya + 0.6
        while y < yb - 0.6:
            if abs(y - door) < 0.9:
                y += 0.8
                continue
            m.lathe([(0.0, 0.0), (0.16, 0.0), (0.2, 0.35), (0.0, 0.35)], 'steel', x=x, y=y, seg=10)
            pm = petals[rnd.randrange(4)]
            for q in range(7):
                a = rnd.uniform(0, 6.28)
                r = rnd.uniform(0.0, 0.13)
                zz = rnd.uniform(0.55, 0.9)
                m.tube([(x + r * math.cos(a) * 0.3, y + r * math.sin(a) * 0.3, 0.3), (x + r * math.cos(a), y + r * math.sin(a), zz)], 0.006, 'plant', seg=3, caps=False)
                m.lathe([(0.0, 0.0), (0.045, 0.0), (0.05, 0.04), (0.0, 0.07)], pm, x=x + r * math.cos(a), y=y + r * math.sin(a), seg=6) if False else None
                m.at(x + r * math.cos(a), y + r * math.sin(a), zz)
                m.lathe([(0.0, -0.01), (0.05, 0.0), (0.045, 0.05), (0.0, 0.07)], pm, seg=6)
                m.pop()
            y += 0.55
    m.at(xb, (ya + yb) / 2, zf)
    shelf_unit(m, min(4.0, yb - ya - 0.6), 2.2, 0.5, [15, 4], rnd, levels=4)
    m.pop()
    counter(m, door + 1.6, door + 3.0, xf - 4.4, xf - 3.7, rnd=rnd)


def office(m, rm, door, rnd):
    xf, xb, ya, yb, zf = rm['xf'], rm['xb'], rm['ya'], rm['yb'], rm['zf']
    y = ya + 0.8
    while y < yb - 1.8:
        if abs(y + 0.8 - door) < 1.2:
            y += 1.9
            continue
        m.box(xf - 2.6, y, zf + 0.7, xf - 1.6, y + 1.6, zf + 0.75, 'int_oak')                         # desk
        m.box(xf - 2.6, y, zf, xf - 2.5, y + 1.6, zf + 0.7, 'int_dark')
        m.box(xf - 1.7, y + 0.05, zf, xf - 1.6, y + 0.55, zf + 0.7, 'int_dark')
        m.box(xf - 2.1, y + 0.6, zf + 0.75, xf - 1.9, y + 1.0, zf + 1.05, 'paint_cream', bv=0.02)    # a monitor
        m.box(xf - 1.2, y + 0.4, zf + 0.42, xf - 0.7, y + 0.9, zf + 0.47, 'fabric_blue', bv=0.02)    # chair seat
        m.box(xf - 0.75, y + 0.4, zf + 0.47, xf - 0.7, y + 0.9, zf + 0.95, 'fabric_blue', bv=0.02)
        m.cyl(xf - 0.95, y + 0.65, zf, zf + 0.42, 0.025, 'chrome', seg=5)
        y += 2.2
    for k in range(4):                                                                              # filing cabinets and a listings board on the back wall
        m.box(xb, ya + 0.3 + k * 0.5, zf, xb + 0.55, ya + 0.78 + k * 0.5, zf + 1.3, 'paint_grey', bv=0.01)
    m.uvrect([(xb + 0.06, (ya + yb) / 2, zf + 1.2), (xb + 0.06, (ya + yb) / 2 + 2.4, zf + 1.2), (xb + 0.06, (ya + yb) / 2 + 2.4, zf + 2.5), (xb + 0.06, (ya + yb) / 2, zf + 2.5)], 'wallart', (0.0, 0.0, 0.25, 0.25), out=(1, 0, 0))


def lobby(m, rm, door, rnd):
    xf, xb, ya, yb, zf = rm['xf'], rm['xb'], rm['ya'], rm['yb'], rm['zf']
    cy = (ya + yb) / 2 + 2.0
    m.box(xb + 0.8, cy - 1.4, zf, xb + 1.6, cy + 1.4, zf + 1.1, 'int_dark')                          # reception desk and key rack
    m.box(xb + 0.7, cy - 1.5, zf + 1.1, xb + 1.7, cy + 1.5, zf + 1.15, 'int_oak')
    m.box(xb, cy - 1.2, zf + 0.8, xb + 0.05, cy + 1.2, zf + 2.3, 'int_dark')
    for k in range(18):
        m.box(xb + 0.05, cy - 1.0 + (k % 9) * 0.22, zf + 1.4 + (k // 9) * 0.5, xb + 0.09, cy - 0.85 + (k % 9) * 0.22, zf + 1.5 + (k // 9) * 0.5, 'brass')
    for (yy, k) in ((ya + 1.0, 0), (ya + 3.4, 1)):                                                   # armchairs and a plant
        if abs(yy - door) < 1.2 or yy > yb - 1.0:
            continue
        fm = ['fabric_green', 'leather'][k]
        m.box(xf - 2.3, yy, zf, xf - 1.5, yy + 0.9, zf + 0.45, fm, bv=0.05)
        m.box(xf - 2.35, yy, zf + 0.45, xf - 2.15, yy + 0.9, zf + 1.0, fm, bv=0.05)
    m.lathe([(0.0, 0.0), (0.2, 0.0), (0.24, 0.5), (0.0, 0.5)], 'paint_red', x=xf - 0.6, y=ya + 0.6, seg=12)
    for q in range(8):
        a = q * 0.8
        m.tube([(xf - 0.6, ya + 0.6, 0.5), (xf - 0.6 + 0.35 * math.cos(a), ya + 0.6 + 0.35 * math.sin(a), 1.4 + 0.12 * q)], 0.012, 'plant', seg=3, caps=False)
        m.at(xf - 0.6 + 0.35 * math.cos(a), ya + 0.6 + 0.35 * math.sin(a), 1.4 + 0.12 * q)
        m.lathe([(0.0, 0.0), (0.2, 0.0), (0.0, 0.18)], 'plant', seg=6)
        m.pop()
    m.cyl(xf - 3.0, (ya + yb) / 2 - 1.0, zc_of(rm) - 0.6, zc_of(rm) - 0.02, 0.01, 'brass', seg=4)         # a pendant lamp
    m.at(xf - 3.0, (ya + yb) / 2 - 1.0, zc_of(rm) - 0.9)
    m.lathe([(0.05, 0.0), (0.3, 0.3)], 'lampshade', seg=12)
    m.pop()


def zc_of(rm):
    return rm['zc']


def tavern(m, rm, door, rnd):
    xf, xb, ya, yb, zf = rm['xf'], rm['xb'], rm['ya'], rm['yb'], rm['zf']
    bx = xf - 3.6
    m.box(bx - 0.5, ya + 0.5, zf, bx + 0.4, yb - 0.5, zf + 1.05, 'int_dark')
    m.box(bx - 0.6, ya + 0.45, zf + 1.05, bx + 0.55, yb - 0.45, zf + 1.1, 'int_brown')
    n = int((yb - ya - 1.0) / 0.8)
    for i in range(n):
        yy = ya + 0.5 + (i + 0.5) * (yb - ya - 1.0) / n
        if abs(yy - door) > 0.8:
            stool(m, bx + 0.9, yy)
    m.at(xb, (ya + yb) / 2, zf)
    shelf_unit(m, min(5.0, yb - ya - 0.6), 2.2, 0.35, [6, 7, 6, 7, 6], rnd, levels=4)
    m.pop()
    m.box(xb + 0.36, ya + 0.4, zf + 0.9, xb + 0.38, yb - 0.4, zf + 2.3, 'mirror')
    for yy in (ya + 1.2, yb - 2.4):                                                                  # round tables
        if abs(yy - door) > 1.1:
            m.cyl(xf - 1.0, yy, zf + 0.72, zf + 0.76, 0.4, 'int_brown', seg=12)
            m.cyl(xf - 1.0, yy, zf, zf + 0.72, 0.04, 'paint_dark', seg=6)


def shelves_kind(m, rm, kind, door, rnd):
    store_like(m, rm, kind, door, rnd, CELLS.get(kind, CELLS['store']))


def build_interior(m, spec, x0, y0, y1, zb, zt, door, rnd, hi):
    """Interior behind the whole shopfront between its piers. x0 = front plane; zb/zt = glass bottom/top; door = door centre (y)."""
    kind = KIND.get(spec['shop'] % 32, 'store')
    rm = dict(xf=x0 - 0.26, xb=x0 - 0.26 - rnd.choice([5.2, 6.0, 6.8]), ya=y0 + 0.36, yb=y1 - 0.36, zf=0.12, zc=zt - 0.04)
    room(m, rm, kind, rnd)
    cells = CELLS.get(kind, CELLS['store'])
    fn = {'diner': diner, 'barber': barber, 'jewel': jewel, 'furniture': furniture, 'tv': tv, 'bank': bank, 'laundry': laundry, 'florist': florist, 'office': office,
          'lobby': lobby, 'tavern': tavern}.get(kind)
    if fn:
        fn(m, rm, door, rnd)
    else:
        shelves_kind(m, rm, kind, door, rnd)
    return rm, kind, cells
