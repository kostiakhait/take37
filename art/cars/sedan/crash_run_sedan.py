# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""One damaged sedan variant: blender -b -t 4 -P crash_run_sedan.py -- --type front --degree 2 [--side -1] --outdir <dir> [--blend X_final.blend] [--work <scratch dir>]
Same pipeline as ../_common/crash_run.py with the shared table (crash_table.py, written in the coupe's metres) adapted to the sedan by the profile below: its own hood and trunk hinge
lines, four doors (the rear doors and their glass follow the hit), the fast glass shatter of crashglass.py."""
import copy
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / '_common'))
sys.path.insert(0, str(HERE))
argv = sys.argv[sys.argv.index('--') + 1:]
arg = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d  # noqa: E731
import bpy  # noqa: E402
import cargen  # noqa: E402
import crash_table  # noqa: E402
import crashglass  # noqa: E402
import crashkit  # noqa: E402
import sedan_geom as geom  # noqa: E402

# the sedan: hood hinge x 0.91 .. nose 2.16 (the coupe: 0.835 .. 2.38), trunk lid hinge x -1.67 .. -2.33
HOOD_X, HOOD_END, TRUNK_X, TRUNK_END = 0.91, 2.16, -1.67, -2.33
CH, CE = 0.835, 2.38


def adapt(spec, kind, d):
    parts = spec.setdefault('parts', {})
    pick = lambda a: a[d - 1]   # noqa: E731
    for o in parts.get('Hood', []):
        if o['op'] == 'hinge':
            o['x'] = HOOD_X if abs(o['x'] - CH) < 1e-6 else HOOD_X + (o['x'] - CH) / (CE - CH) * (HOOD_END - HOOD_X)
    for o in parts.get('Trunk', []):
        if o['op'] == 'hinge':
            o['x'] = TRUNK_X if abs(o['x'] + 1.439) < 1e-6 else TRUNK_X + (o['x'] + 1.439) / 1.0 * (TRUNK_END - TRUNK_X) * 0.9
        elif o['op'] == 'crumple':
            o['x'], o['len'] = TRUNK_X, 0.66
    # rear doors: dented by the side hit and the rollover, follow the front door of their side otherwise
    k = {'side': 0.0, 'roll': 0.8}.get(kind, 0.45)
    for a, b in (('Door_FL', 'Door_RL'), ('Door_FR', 'Door_RR')):
        if a in parts and b not in parts:
            parts[b] = [dict(o, open=o['open'] * k, sag=o.get('sag', 0) * k, roll=o.get('roll', 0) * k) if o.get('op') == 'door' else dict(o) for o in copy.deepcopy(parts[a])]
    if kind == 'side':
        parts['Door_RL'] = [crash_table.door(pick([3, 10, 28]), pick([0.5, 2, 5]), pick([0, 1, 4]))]
    g = spec['fragile']['glass']
    for key, src in (('Glass_RL', 'Glass_FL'), ('Glass_RR', 'Glass_FR')):
        g[key] = g.get(src, 'ok') if kind != 'side' or key == 'Glass_RL' else 'ok'
    if kind == 'side':
        g['Glass_RL'] = pick(['cracked', 'shattered', 'gone'])
    return spec


crash_table.PROFILES['sedan'] = dict(hood_x=HOOD_X, hood_len=HOOD_END - HOOD_X, trunk_x=TRUNK_X, trunk_len=0.66, adapt=adapt)
crashglass.install()
cargen.use(geom.G)
t0 = time.time()
bpy.ops.wm.open_mainfile(filepath=arg('--blend', 'D:/temp/take37/claude/work/sedan_final.blend'))
root = bpy.data.objects[geom.G.ROOT]
kind, degree, side = arg('--type'), int(arg('--degree')), int(arg('--side', '1'))
spec = crash_table.build(kind, degree, side, 'sedan')
spec['glass_cells'] = 60
spec['glass_edge'] = 0.03
crashkit.crash(root, spec, log=lambda *a: print(*a, flush=True))
out = pathlib.Path(arg('--outdir'))
stem = f'{geom.G.ROOT.lower()}_{kind}{"_R" if side < 0 else ""}_d{degree}'
cargen.export(root, out / f'{stem}.glb')
cargen.export(root, out / f'{stem}_lod1.glb', lod=True)
work = pathlib.Path(arg('--work', 'D:/temp/take37/cars2/sedan_work/blends'))
work.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(work / f'{stem}.blend'), compress=True)
print('CK done', stem, round(time.time() - t0, 1), 's', flush=True)
