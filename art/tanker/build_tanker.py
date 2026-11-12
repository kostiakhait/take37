# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""TAKE 37 fuel tanker: a 1980s American conventional tractor with a 9,000 US gallon aluminium tank semitrailer. Built in Blender 4.2 (headless), in short stages that each save a .blend.

  python -I prep_textures.py                                  (once: textures and livery into D:/temp/take37/tanker/tex)
  blender -b -P build_tanker.py -- --stage wheels            (new file)   -> D:/temp/take37/tanker/blend/tanker_wheels.blend
  blender -b <prev.blend> -P build_tanker.py -- --stage chassis
  ... stages in order: wheels chassis cab interior tank fittings lamps details
  blender -b <last.blend> -P build_tanker.py -- --stage export [--out art/tanker/tanker_1987.glb --lod1 art/tanker/tanker_1987_lod1.glb]

Frame: origin on the ground at the middle of the tractor's wheelbase, nose +X, up +Z, left +Y (glb: Y up, nose +X).
Nodes: Tanker > Tractor > (Chassis, Hood, Cab > doors, mirrors, steering wheel ..., Wheel_F*, Wheel_D*)   and   Tanker > Trailer (at the kingpin) > (TankShell, Hatch_1..5, fittings, Wheel_T*)
"""
import importlib
import pathlib
import sys

import bpy

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tkit as T  # noqa: E402
from tkit import V3  # noqa: E402

ORDER = ['wheels', 'chassis', 'cab', 'interior', 'tank', 'fittings', 'lamps', 'details']
MODULE = {'wheels': 'st_wheels', 'chassis': 'st_chassis', 'cab': 'st_cab', 'interior': 'st_interior', 'tank': 'st_tank', 'fittings': 'st_fittings', 'lamps': 'st_lamps', 'details': 'st_details'}


def init():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    import dims as D
    root = T.empty('Tanker', (0, 0, 0))
    T.empty('Tractor', (0, 0, 0), root)
    T.empty('Trailer', (D.KINGPIN_X, 0, 0), root)           # pivot at the kingpin: the game turns it about Z to jack-knife or releases it
    return root


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    arg = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d  # noqa: E731
    stage = arg('--stage')
    if stage == 'wheels':
        init()
    if stage == 'export':
        import export as E
        E.run(arg('--out', str(HERE / 'tanker_1987.glb')), arg('--lod1', str(HERE / 'tanker_1987_lod1.glb')))
        return
    mod = importlib.import_module(MODULE[stage])
    T.log('stage', stage)
    mod.run(T.find('Tanker'))
    p = T.save(stage)
    tris = sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')
    T.log('saved', p, 'faces', tris)


main()
