# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""One damaged variant of a car: blender -b -t 8 -P crash_run.py -- --car coupe --type front --degree 2 --outdir D:/.../damaged [--blend X_final.blend] [--side 1]
Writes <stem>_<type>[_R]_d<degree>.glb and ..._lod1.glb into --outdir (stem from the car's ROOT name, e.g. coupe84), and a scratch blend into D:/temp/take37/cars2/povrezhdeniya_primer/work.

Reuse for another car: the car needs its <car>_geom.py (G.ROOT) and the finished <car>_final.blend of cargen with the standard node names (Body, Hood, Trunk|Tailgate, Door_*, Bumper_F/R, Ends, Lamps_*,
Glass*, Trim*, Wheel_XX, Wheel_XX_mesh). Types: front, front_corner, rear, rear_corner, side, roll (--side -1 = mirror image); degrees 1-3 (the car's existing *_damaged.glb is front degree 1). Numbers are in
crash_table.py (written in the coupe's metres; the field and part frames are measured from the car by crashkit.Car). One variant (full + lod1 glb) takes 10-20 s on this machine (8 threads); the whole
set of 8 types x 3 degrees (24 variants) about 6 minutes, plus 35 s per 9-view catalog sheet (preview.py --engine eevee --cull)."""
import importlib
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
argv = sys.argv[sys.argv.index('--') + 1:]
arg = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d  # noqa: E731
car = arg('--car')
sys.path.insert(0, str(HERE.parent / car))
import bpy  # noqa: E402
import cargen  # noqa: E402
import crash_table  # noqa: E402
import crashkit  # noqa: E402

geom = importlib.import_module(f'{car}_geom')
cargen.use(geom.G)
t0 = time.time()
blend = arg('--blend', f'D:/temp/take37/claude/work/{car}_final.blend')
kind, degree = arg('--type'), int(arg('--degree'))
bpy.ops.wm.open_mainfile(filepath=blend)
root = bpy.data.objects[geom.G.ROOT]
crashkit.crash(root, crash_table.build(kind, degree, int(arg('--side', '1')), car), log=lambda *a: print(*a, flush=True))
out = pathlib.Path(arg('--outdir'))
stem = f'{geom.G.ROOT.lower()}_{kind}{"_R" if int(arg("--side", "1")) < 0 else ""}_d{degree}'
cargen.export(root, out / f'{stem}.glb')
cargen.export(root, out / f'{stem}_lod1.glb', lod=True)
bpy.ops.wm.save_as_mainfile(filepath=f'D:/temp/take37/cars2/povrezhdeniya_primer/work/{stem}.blend', compress=True)
print('CK done', stem, round(time.time() - t0, 1), 's', flush=True)
