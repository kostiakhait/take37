# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Damaged variants of the wagon with the shared crash kit (../_common/crashkit.py, crash_table.py): the wagon's own numbers live here, not in the shared files.
    blender -b -t 4 -P crash_wagon.py -- --type front --degree 2 [--side -1] --outdir D:/.../damaged [--blend wagon_final.blend]
The wagon differs from the coupe's table in: a tailgate (hinged at the roof, pops open backward) instead of a trunk lid, four doors, a tailgate window and two cargo quarter windows
(panes of the 'Glass' node, left and right), a longer greenhouse. Output: wagon82_<type>[_R]_d<N>.glb and _lod1.glb."""
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
COMMON = HERE.parent / '_common'
sys.path.insert(0, str(COMMON))
sys.path.insert(0, str(HERE))
argv = sys.argv[sys.argv.index('--') + 1:]
arg = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d  # noqa: E731


def wagon_adapt(spec, kind, d):
    """left-hand row of the generic table -> the wagon's parts"""
    parts = spec.setdefault('parts', {})
    pick = lambda a: a[d - 1]   # noqa: E731
    # tailgate in place of the trunk lid: top hinge (x of its upper edge, z of its top), the bottom swings out backward; a wrecked gate also twists on its hinge
    ops = parts.pop('Trunk', [])
    pops = [abs(o['angle']) for o in ops if o.get('op') == 'hinge' and o.get('r') == 0.01]
    creases = [abs(o['angle']) for o in ops if o.get('op') == 'hinge' and o.get('r') != 0.01]
    piv = (-2.04, 0.0, 1.36)
    ang = 2.8 * (pops[0] if pops else 2.0) + (0.2 * max(creases) if creases else 0.0)
    if kind in ('front', 'front_corner'):
        ang = pick([3.0, 6.0, 11.0])
    parts['Tailgate'] = [dict(op='rigid', pivot=piv, axis=(0, 1, 0), angle=ang, move=(-0.015, 0.0, 0.0))]
    if kind in ('rear', 'rear_corner', 'roll') and d == 3:
        parts['Tailgate'].append(dict(op='rigid', pivot=piv, axis=(1, 0, 0), angle=12.0))
    # rear doors follow the front ones on the same side (hinge on their own front edge)
    k = 0.3 if kind in ('front', 'front_corner') else 0.8
    for a, b in (('Door_FL', 'Door_RL'), ('Door_FR', 'Door_RR')):
        if a in parts and b not in parts:
            parts[b] = [dict(o, open=o['open'] * k, sag=o.get('sag', 0) * k, roll=o.get('roll', 0) * k) if o.get('op') == 'door' else dict(o) for o in parts[a]]
    spec['remove'] = list(spec.get('remove', [])) + [n.replace('_F', '_R') for n in spec.get('remove', []) if n.startswith('Door_F')]
    # glass: the tailgate window is its own node; the cargo quarter windows are panes of 'Glass' at x < -1; the rear doors' glass follows the front doors'
    g = spec['fragile']['glass']
    g['Glass_Tailgate'] = g.pop('rear')
    g['quarter_L'] = g['Glass_RL'] = g.get('opera', 'cracked')
    g['quarter_R'] = g['Glass_RR'] = g.get('Glass_FR', 'ok')
    g.pop('opera', None)
    return spec


def main():
    import bpy
    import cargen
    import crash_profiles
    import crash_table
    import crashkit
    import wagon_geom
    crash_profiles.PROFILES['wagon'] = dict(hood_x=0.83, hood_len=1.33, trunk_x=None, adapt=wagon_adapt)
    crash_table._SWAP.update(quarter_L='quarter_R', quarter_R='quarter_L')
    cargen.use(wagon_geom.G)
    t0 = time.time()
    kind, degree, side = arg('--type'), int(arg('--degree')), int(arg('--side', '1'))
    bpy.ops.wm.open_mainfile(filepath=arg('--blend', 'D:/temp/take37/claude/work/wagon_final.blend'))
    root = bpy.data.objects[wagon_geom.G.ROOT]
    spec = crash_table.build(kind, degree, side, 'wagon')
    spec['glass_cells'] = 60
    spec['glass_edge'] = 0.024
    crashkit.crash(root, spec, log=lambda *a: print(*a, flush=True))
    out = pathlib.Path(arg('--outdir'))
    stem = f'{wagon_geom.G.ROOT.lower()}_{kind}{"_R" if side < 0 else ""}_d{degree}'
    cargen.export(root, out / f'{stem}.glb')
    cargen.export(root, out / f'{stem}_lod1.glb', lod=True)
    work = pathlib.Path('D:/temp/take37/cars2/wagon_dmg/work')
    work.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(work / f'{stem}.blend'), compress=True)
    print('CK done', stem, round(time.time() - t0, 1), 's', flush=True)


main()
