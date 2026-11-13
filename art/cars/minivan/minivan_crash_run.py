# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""One damaged minivan variant: blender -b -t 4 -P minivan_crash_run.py -- --type front --degree 2 [--side -1] --outdir <dir> [--blend X_final.blend] [--work <scratch dir>]
Same pipeline as ../_common/crash_run.py, with the table adapted to the minivan by minivan_profile.py."""
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
import crashkit  # noqa: E402
import crash_table  # noqa: E402
import crashglass  # noqa: E402
import minivan_geom as geom  # noqa: E402
import minivan_profile  # noqa: E402

crash_table.PROFILES['minivan'] = minivan_profile.PROFILE
crashglass.install()

cargen.use(geom.G)
t0 = time.time()
bpy.ops.wm.open_mainfile(filepath=arg('--blend', 'D:/temp/take37/claude/work/minivan_final.blend'))
root = bpy.data.objects[geom.G.ROOT]
kind, degree, side = arg('--type'), int(arg('--degree')), int(arg('--side', '1'))
crashkit.crash(root, minivan_profile.finish(crash_table.build(kind, degree, side, 'minivan')), log=lambda *a: print(*a, flush=True))
out = pathlib.Path(arg('--outdir'))
stem = f'{geom.G.ROOT.lower()}_{kind}{"_R" if side < 0 else ""}_d{degree}'
cargen.export(root, out / f'{stem}.glb')
cargen.export(root, out / f'{stem}_lod1.glb', lod=True)
work = arg('--work')
if work:
    bpy.ops.wm.save_as_mainfile(filepath=f'{work}/{stem}.blend', compress=True)
print('CK done', stem, round(time.time() - t0, 1), 's', flush=True)
