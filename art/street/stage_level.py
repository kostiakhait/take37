# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Assembles the TAKE 37 main street: road, kerbs, sidewalks, markings, decals, buildings (LOD pairs), furniture, wires, film-crew barriers, parking slots, markers.

  blender -b -P art/street/stage_level.py -- [--blend D:/temp/take37/street/blend/level.blend] [--glb art/street/street_level.glb] [--kit art/street/street_kit.glb] [--cols art/street/street_colliders.glb]

Frame: street along +X (x = -40 .. 640), centre line y = 0, up +Z. Nodes (glb root 'StreetLevel'):
  Road_*_nn          road, gutter, kerb, sidewalk, marking and decal meshes in 100 m chunks (static)
  Buildings/Bld_*    one empty per building with LOD0 and LOD1 child meshes (static)
  Static/*           trees, utility wires, backdrops (static)
  Destructible/DEST_<Kind>_nnn   props the game may knock over / blow up; each an empty with LOD0/LOD1 children and extras (destructible, mass)
  Parking/PARK_L_nnn, PARK_R_nnn  empty slots along the kerb for parked cars (extras: size, heading)
  Markers/*          spawns, lane polylines, gas-station anchor
"""
import json
import math
import pathlib
import random
import sys

import bpy
from mathutils import Vector as V

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import buildings as B  # noqa: E402
import kitlib as K  # noqa: E402
import props_kit as PK  # noqa: E402
import street_geo as G  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
arg = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d  # noqa: E731
HERE = pathlib.Path(__file__).resolve().parent
BLEND = arg('--blend', 'D:/temp/take37/street/blend/level.blend')
GLB = arg('--glb', str(HERE / 'street_level.glb'))
KIT = arg('--kit', str(HERE / 'street_kit.glb'))
COLS = arg('--cols', str(HERE / 'street_colliders.glb'))
LITE = '--lite' in argv                    # skip buildings (quick road checks)
rnd = random.Random(1987)
STATS = {}


def log(*a):
    print('[level]', *a, flush=True)


def main():
    K.reset()
    sc = bpy.context.scene
    root = K.empty('StreetLevel', size=2.0)
    c_road = K.coll('Level_Road')
    c_bld = K.coll('Level_Buildings')
    c_static = K.coll('Level_Static')
    c_dest = K.coll('Level_Destructible')
    c_park = K.coll('Level_Parking')
    c_mark = K.coll('Level_Markers')
    c_kit = K.coll('Kit_Source')
    g_bld = K.empty('Buildings', parent=root, collection=c_bld)
    g_static = K.empty('Static', parent=root, collection=c_static)
    g_dest = K.empty('Destructible', parent=root, collection=c_dest)
    g_park = K.empty('Parking', parent=root, collection=c_park)
    g_mark = K.empty('Markers', parent=root, collection=c_mark)
    cols_objs = []

    # ---------------------------------------------------------------- props source meshes
    P = PK.all_props()
    for d in P.values():
        for o in d.values():
            for c in o.users_collection:
                c.objects.unlink(o)
            c_kit.objects.link(o)
    log('props built', sum(K.tris(o) for d in P.values() for o in d.values()))

    counters = {}

    def place(kind, x, y, rz=0.0, dest=True, parent=None, z=0.0, props=None, name=None, rx=0.0):
        n = counters.get(kind, 0)
        counters[kind] = n + 1
        pre = 'DEST_' if dest else ''
        nm = name or f'{pre}{kind}_{n:03d}'
        par = parent or (g_dest if dest else g_static)
        e = K.empty(nm, loc=(x, y, z), rot=(rx, 0, rz), parent=par, collection=c_dest if dest else c_static, size=0.25)
        e['kind'] = kind
        if dest:
            e['destructible'] = 1
            e['mass_kg'] = PK.DEST.get(kind.split('_')[0] if not kind.startswith('RoadSign') else 'RoadSign', 20)
        for k, v in (props or {}).items():
            e[k] = v
        for lod in (0, 1):
            src = P[kind][lod]
            o = K.dup(src, f'{nm}_LOD{lod}', parent=e, collection=c_dest if dest else c_static)
            o['lod'] = lod
        return e

    # ---------------------------------------------------------------- road geometry
    CH = G.Chunker('Road')
    G.build_road(CH, G.CROSS_L, G.CROSS_R, G.GAS, None)
    G.build_markings(CH, G.CROSS_L, G.CROSS_R, G.GAS)
    G.build_decals(CH, G.CROSS_L, G.CROSS_R, G.GAS)
    road_objs = CH.build_all(c_road, root)
    for o in road_objs:
        o['static'] = 1
    STATS['road_tris'] = sum(K.tris(o) for o in road_objs)
    log('road', len(road_objs), 'objects', STATS['road_tris'], 'tris')

    # ground under everything: verge, 10 m tone cells
    gm = K.MB('Ground', seed=3, uvshift=False)
    gm.tone = lambda p: (0.75 + 0.35 * K.fbm(p * 0.05, 9, 1.0), 0.8 + 0.3 * K.fbm(p * 0.05, 10, 1.0), 0.7)
    for ix in range(0, 17):
        for iy in range(0, 8):
            x0, y0 = G.L0 - 60 + ix * 48, -190 + iy * 48 * 1.0
            if abs(y0 + 24) < 1e-9:
                pass
            gm.face([(x0, y0, -0.04), (x0 + 48, y0, -0.04), (x0 + 48, y0 + 48, -0.04), (x0, y0 + 48, -0.04)], 'verge', out=(0, 0, 1))
    gnd = gm.build('Ground', collection=c_road, parent=root)
    gnd['static'] = 1

    # ---------------------------------------------------------------- buildings
    designs = B.make_designs(36)
    for d in designs:
        d['D'] = 16.0
    side_designs = []
    for i, d in enumerate(B.make_designs(14)):
        d = dict(d)
        d.update(name=f'S{i:02d}', D=8.0, floors=2, fire_escape=False, seed=900 + i * 3)
        side_designs.append(d)
    if not LITE:
        BO = {}
        for d in designs + side_designs:
            BO[d['name']] = {lod: B.make_building(d, lod) for lod in (0, 1)}
            for lod, o in BO[d['name']].items():
                for c in o.users_collection:
                    c.objects.unlink(o)
                c_kit.objects.link(o)
        STATS['designs'] = {n: [K.tris(v[0]), K.tris(v[1])] for n, v in BO.items()}
        log('buildings built', len(BO))
    bcount = [0]
    placed = []        # (name, x0, x1, side)

    def place_building(d, x, y, rz, side_tag):
        i = bcount[0]
        bcount[0] += 1
        nm = f"Bld_{side_tag}_{i:03d}_{d['name']}"
        e = K.empty(nm, loc=(x, y, 0), rot=(0, 0, rz), parent=g_bld, collection=c_bld, size=0.5)
        e['design'] = d['name']
        e['width'] = d['W']
        e['floors'] = d['floors']
        e['static'] = 1
        if not LITE:
            for lod in (0, 1):
                o = K.dup(BO[d['name']][lod], f'{nm}_LOD{lod}', parent=e, collection=c_bld)
                o['lod'] = lod
        # collider box
        cm = K.MB(f'COL_{nm}', uvshift=False)
        H = 4.3 + 3.4 * (d['floors'] - 1) + 0.6
        cm.box(-d['D'], -d['W'] / 2, 0, 0, d['W'] / 2, H, 'tar')
        co = cm.build(f'COL_{nm}', collection=c_mark)
        co.location = (x, y, 0)
        co.rotation_euler = (0, 0, rz)
        cols_objs.append(co)
        return e

    def fill_row(a, b, side, designs_pool, reserved=None):
        """Pick designs to fill x in [a, b]; leftover becomes alleys. Returns list of (design, x_centre)."""
        out, used, prev = [], 0.0, None
        L = b - a
        pool = list(designs_pool)
        while True:
            fits = [d for d in pool if d['W'] <= L - used - 0.1 and d['name'] != prev]
            if not fits:
                break
            d = rnd.choice(fits)
            out.append(d)
            used += d['W']
            prev = d['name']
        gap = L - used
        gaps = [0.0] * (len(out) + 1)
        if gap > 0.2:
            k = rnd.randrange(1, max(2, len(out)))
            if gap > 4.5 and len(out) > 1:
                gaps[k] = min(gap * 0.7, 6.0)
                rest = gap - gaps[k]
            else:
                rest = gap
            gaps[0] += rest / 2
            gaps[-1] += rest / 2
        x = a
        res = []
        for i, d in enumerate(out):
            x += gaps[i]
            res.append((d, x + d['W'] / 2))
            x += d['W']
        return res, gaps

    row_last_first = {}
    for side, cross in ((1, G.CROSS_L), (-1, G.CROSS_R)):
        edges = []
        cur = G.L0
        for xc in cross:
            edges.append((cur, xc - G.SW / 2 - G.R))
            cur = xc + G.SW / 2 + G.R
        edges.append((cur, G.L1))
        for (a, b) in edges:
            if side == -1 and a < G.GAS[1] and b > G.GAS[0]:
                parts = [(a, G.GAS[0] - 1.0)] if G.GAS[0] - 1.0 - a > 6.0 else []
                parts += [(G.GAS[1] + 1.0, b)] if b - (G.GAS[1] + 1.0) > 6.0 else []
            else:
                parts = [(a, b)]
            for (pa, pb) in parts:
                row, gaps = fill_row(pa, pb, side, designs)
                for (d, xc_) in row:
                    place_building(d, xc_, side * G.BL, rz=(-math.pi / 2 if side == 1 else math.pi / 2), side_tag='L' if side == 1 else 'R')
                    placed.append((d['name'], xc_ - d['W'] / 2, xc_ + d['W'] / 2, side))
                # sidewalk collider
                cm = K.MB(f'COL_SW_{side}_{int(pa)}', uvshift=False)
                cm.box(pa, min(side * (G.YK + G.KW), side * G.BL), 0, pb, max(side * (G.YK + G.KW), side * G.BL), G.ZK, 'tar')
                co = cm.build(f'COL_Sidewalk_{"L" if side == 1 else "R"}_{int(pa):03d}', collection=c_mark)
                cols_objs.append(co)
    # buildings along the side streets, starting behind the 16 m deep corner buildings, 8 m deep, fronts facing the street
    for side, cross in ((1, G.CROSS_L), (-1, G.CROSS_R)):
        for xc in cross:
            for sx in (-1, 1):
                y_a = G.BL + 16.0
                y_b = G.YK + G.SIDE_LEN - 0.5
                xf = xc + sx * (G.SW / 2 + G.R)
                row, gaps = fill_row(y_a, y_b, side, side_designs)
                for (d, yc) in row:
                    e = place_building(d, xf, side * yc, rz=(0.0 if sx == -1 else math.pi), side_tag='S')
                    # the design's local Y runs along world Y (west) or -Y (east): symmetric, so centre placement is fine
    log('buildings placed', bcount[0])

    # backdrops closing the side streets (plain brick walls, fronts at the street end)
    for side, cross in ((1, G.CROSS_L), (-1, G.CROSS_R)):
        for xc in cross:
            bm = K.MB(f'Backdrop_{side}_{int(xc)}', seed=int(xc), uvshift=False)
            bm.tone = B.tone_fn(int(xc))
            yend = side * (G.YK + G.SIDE_LEN)
            bm.box(xc - 12, yend, 0, xc + 12, yend + side * 0.6, 14.0, 'brick_old', skip=('-y' if side == 1 else '+y',))
            o = bm.build(f'Backdrop_{"L" if side == 1 else "R"}_{int(xc):03d}', collection=c_static, parent=g_static)
            o['static'] = 1

    # ---------------------------------------------------------------- street furniture
    def on_cross_side(x, side, margin=12.5):
        for xc in (G.CROSS_L if side == 1 else G.CROSS_R):
            if abs(x - xc) < G.SW / 2 + G.R + margin * 0.5 + 1:
                return True
        # the cross streets on the other side matter for crosswalks too (they span the whole road)
        for xc in sorted(set(G.CROSS_L + G.CROSS_R)):
            if abs(x - xc) < G.SW / 2 + G.R + 5.0:
                return True
        return False

    def in_gas(x, side, m=0.0):
        return side == -1 and G.GAS[0] - m < x < G.GAS[1] + m

    face_street = lambda side: (-math.pi / 2 if side == 1 else math.pi / 2)  # noqa: E731  (local +X toward the roadway)
    face_traffic = lambda side: (0.0 if side == 1 else math.pi)               # noqa: E731  (sign face toward approaching traffic)
    tree_x = {1: [], -1: []}
    lamp_x = {1: [], -1: []}
    for side in (1, -1):
        x = G.L0 + 14 + (11 if side == -1 else 0)
        while x < G.L1 - 5:
            if not on_cross_side(x, side) and not in_gas(x, side, 2):
                place('LampAcorn', x, side * 6.5, face_street(side))
                lamp_x[side].append(x)
            x += 23.0
        x = G.L0 + 8 + (6 if side == -1 else 0)
        while x < G.L1 - 5:
            if not on_cross_side(x, side, 16) and not in_gas(x, side, 3) and all(abs(x - lx) > 3.0 for lx in lamp_x[side]):
                place(f'StreetTree{rnd.randint(1, 3)}', x, side * 7.3, rnd.uniform(0, 6.28), dest=False)
                tree_x[side].append(x)
            x += 17.0
        # meters: one per parking stall, 0.3 m behind the kerb face line at the middle of the stall
        x = G.L0 + 6.3
        while x < G.L1 - 3:
            if not on_cross_side(x, side, 14) and not in_gas(x, side, 4) and all(abs(x - lx) > 1.2 for lx in lamp_x[side] + tree_x[side]):
                place('Meter', x, side * 6.3, face_street(side))
            x += 6.6
    # hydrants every ~90 m, alternating sides, no meter within 3 m
    hx = [(46.0, 1), (131.0, -1), (232.0, 1), (338.0, -1), (446.0, 1), (560.0, 1), (612.0, -1)]
    hydrants = []
    for (x, side) in hx:
        if in_gas(x, side, 1):
            continue
        place('Hydrant', x, side * 6.5, face_street(side))
        hydrants.append((x, side))
    # utility poles on the left kerb every 42 m, and the wires between them
    pole_x = []
    x = G.L0 + 18
    while x < G.L1:
        if not on_cross_side(x, 1, 8):
            place('UtilityPole', x, 6.75, 0.0)
            pole_x.append(x)
        x += 42.0
    wm = K.MB('Wires', uvshift=False)
    for xa, xb in zip(pole_x[:-1], pole_x[1:]):
        if xb - xa > 60:
            continue
        for yo, zo in ((-1.15, 9.98), (-0.55, 9.98), (0.0, 9.98), (0.55, 9.98), (1.15, 9.98)):
            pts = []
            n = 8
            for i in range(n + 1):
                t = i / n
                sag = 0.45 * 4 * t * (1 - t)
                pts.append((xa + (xb - xa) * t, 6.75 + yo, zo - sag + 0.12))
            wm.tube(pts, 0.009, 'cable', seg=4, caps=False)
        # a service drop from every pole's transformer to the building line
    wo = wm.build('Wires', collection=c_static, parent=g_static)
    wo['static'] = 1
    # mailboxes, news boxes, benches, bins, phone booths, planters near the shops: along the building-side of each walk, away from tree pits
    walk_in = 8.35
    for side in (1, -1):
        x = G.L0 + 20
        k = 0
        while x < G.L1 - 10:
            x += rnd.uniform(14, 26)
            if on_cross_side(x, side, 10) or in_gas(x, side, 3):
                continue
            kind = ['Bench', 'Bin', 'NewsBox', 'Planter', 'Bench', 'Mailbox', 'PhoneBooth', 'Bin', 'TrashBags'][k % 9]
            k += 1
            y = side * (walk_in - (0.5 if kind in ('Bench',) else 0.0))
            if kind == 'Mailbox':
                y = side * 6.55
            if kind == 'Bin':
                y = side * 6.5
            place(kind, x, y, face_street(side))
            if kind == 'NewsBox':
                place('NewsBox', x + 0.6, y, face_street(side))
    # corner mailboxes and bins at crossings
    for xc in sorted(set(G.CROSS_L + G.CROSS_R)):
        for side in (1, -1):
            if (xc in G.CROSS_L and side == 1) or (xc in G.CROSS_R and side == -1):
                place('Mailbox', xc + (G.SW / 2 + G.R + 2.3), side * 6.5, face_street(side))
                place('Bin', xc - (G.SW / 2 + G.R + 2.3), side * 6.5, face_street(side))
    # ---------------------------------------------------------------- traffic signals at the two four-way crossings, signs
    names = ['main_st', 'elm_st', 'oak_st', 'mill_st', 'church_st', 'walnut_st']
    for xc in (200.0, 410.0):
        for side in (1, -1):
            for sx in (-1, 1):
                place('TrafficLight', xc + sx * (G.SW / 2 + G.R + 0.8), side * 6.3, face_street(side))
    for i, xc in enumerate(sorted(set(G.CROSS_L + G.CROSS_R))):
        for side, cross in ((1, G.CROSS_L), (-1, G.CROSS_R)):
            if xc in cross:
                # stop sign on the right-hand kerb of the side street approach, above the stop bar
                sxx = xc - G.SW / 2 - 0.9 if side == 1 else xc + G.SW / 2 + 0.9
                place('RoadSign_stop', sxx, side * 9.6, math.pi / 2 if side == 1 else -math.pi / 2)
                place('RoadSign_' + 'blade_' + names[i % len(names)], xc + (G.SW / 2 + 0.9) * (1 if side == 1 else -1), side * 6.35, face_street(side) if False else (math.pi / 2 if side == 1 else -math.pi / 2) + math.pi) if False else None
        # pedestrian crossing signs just before each crosswalk (driver's right)
        place('RoadSign_xwalk', xc - (G.SW / 2 + G.R + 3.9), -6.4, math.pi)
        place('RoadSign_xwalk', xc + (G.SW / 2 + G.R + 3.9), 6.4, 0.0)
        # street name blade at the north-east corner post
        nm = 'blade_' + names[(i + 1) % len(names)]
        place('RoadSign_' + nm, xc + G.SW / 2 + G.R + 0.7, -6.4 if xc not in G.CROSS_L else 6.4, math.pi if xc not in G.CROSS_L else 0.0, name=f'DEST_RoadSign_{nm}_{i}')
    for x in (60.0, 335.0, 560.0):
        place('RoadSign_speed25', x, 6.5, 0.0)
    for x in (92.0, 300.0, 470.0, 380.0):
        place('RoadSign_nopark', x, -6.5, math.pi)
    for x in (180.0, 370.0):
        place('RoadSign_oneway', x, 6.5, 0.0)

    # ---------------------------------------------------------------- film-crew closures: crowd barriers, sawhorses, cones
    def closure(x0, x1, y0, y1, along):
        """Barrier line from (x0, y0) to (x1, y1)."""
        L = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(round(L / 2.15)))
        ang = math.atan2(y1 - y0, x1 - x0) + math.pi / 2          # barrier length along local Y
        for i in range(n):
            t = (i + 0.5) / n
            place('CrowdBarrier', x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, ang)
        for t in (0.25, 0.75):
            place('Sawhorse', x0 + (x1 - x0) * t - math.cos(ang - math.pi / 2 + math.pi / 2) * 0.0, y0 + (y1 - y0) * t + 1.2 * along, ang + (math.pi if along < 0 else 0.0))
            for dx in (-0.8, 0.0, 0.8):
                pass
        for t in (0.1, 0.4, 0.6, 0.9):
            place('Cone', x0 + (x1 - x0) * t, y0 + (y1 - y0) * t + 2.4 * along, rnd.uniform(0, 6.28))
    for side, cross in ((1, G.CROSS_L), (-1, G.CROSS_R)):
        for xc in cross:
            closure(xc - G.SW / 2 - G.R, xc + G.SW / 2 + G.R, side * (G.YK + 12.0), side * (G.YK + 12.0), -side)
    closure(G.L0 + 6, G.L0 + 6, -9.3, 9.3, 1)
    closure(G.L1 - 6, G.L1 - 6, -9.3, 9.3, 1)

    # ---------------------------------------------------------------- parking slots
    npk = {1: 0, -1: 0}
    for side in (1, -1):
        x = G.L0 + 9.0
        while x < G.L1 - 9.0:
            blocked = (on_cross_side(x, side, 10) or in_gas(x, side, 4) or any(h[1] == side and abs(h[0] - x) < 6.0 for h in hydrants) or
                       any(abs(x - px) < 1.2 for px in (pole_x if side == 1 else [])))
            if not blocked:
                e = K.empty(f'PARK_{"L" if side == 1 else "R"}_{npk[side]:03d}', loc=(x, side * 4.55, 0), rot=(0, 0, math.pi if side == 1 else 0.0), parent=g_park, collection=c_park, size=0.8)
                e['slot_len'] = 6.0
                e['slot_wid'] = 2.3
                e['heading'] = '-X' if side == 1 else '+X'
                npk[side] += 1
            x += 6.6
    STATS['parking'] = dict(npk)
    # markers
    K.empty('SPAWN_Player', loc=(30, -1.7, 0), rot=(0, 0, 0), parent=g_mark, collection=c_mark, size=1.5)
    K.empty('SPAWN_Pursuit', loc=(12, -1.7, 0), rot=(0, 0, 0), parent=g_mark, collection=c_mark, size=1.5)
    for lane, y, h in (('R', -1.7, 0.0), ('L', 1.7, math.pi)):
        for i, x in enumerate(range(0, 601, 25)):
            e = K.empty(f'TRAFFIC_{lane}_{i:02d}', loc=(x, y, 0), rot=(0, 0, h), parent=g_mark, collection=c_mark, size=0.6)
            e['lane'] = lane
    ga = K.empty('GasStation_Anchor', loc=(sum(G.GAS) / 2, -G.BL, 0), rot=(0, 0, math.pi / 2), parent=g_mark, collection=c_mark, size=3.0)
    ga['note'] = 'place gas_station.glb here (its +X faces the street); lot x range %s..%s, no kerb or sidewalk between' % G.GAS
    log('furniture placed', sum(counters.values()))
    STATS['placed'] = dict(counters)
    K.save_blend(BLEND)

    # ---------------------------------------------------------------- export
    objs = K.descendants(root)
    K.export_glb(objs, GLB)
    allobjs = [o for o in objs if o.type == 'MESH']
    tri_total = sum(K.tris(o) for o in allobjs)
    tri_lod0 = sum(K.tris(o) for o in allobjs if o.get('lod', 0) != 1)
    STATS['tris_instanced_all_lods'] = tri_total
    STATS['tris_instanced_lod0'] = tri_lod0
    STATS['tris_instanced_lod1_replacing'] = tri_lod0 - sum(K.tris(o) for o in allobjs if o.get('lod') == 0) + sum(K.tris(o) for o in allobjs if o.get('lod') == 1)
    cm = [o for o in cols_objs]
    K.export_glb(cm, COLS, jpeg=False)
    json.dump(STATS, open('D:/temp/take37/street/level_stats.json', 'w'), indent=1)
    log('exported', GLB)


main()
