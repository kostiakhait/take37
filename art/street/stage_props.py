# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Stage 1: the street-furniture kit laid out on a catalog plate (LOD0 row, LOD1 row behind it). Saves a .blend checkpoint.
  blender -b -P art/street/stage_props.py -- [--blend D:/temp/take37/street/blend/props.blend]
"""
import pathlib
import sys

import bpy

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import kitlib as K  # noqa: E402
import props_kit as PK  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
BLEND = argv[argv.index('--blend') + 1] if '--blend' in argv else 'D:/temp/take37/street/blend/props.blend'


def layout(P, col):
    x = 0.0
    total = {}
    for name, d in P.items():
        w = 2.5 if name.startswith('StreetTree') else (3.0 if name in ('CrowdBarrier', 'Sawhorse', 'LampCobra', 'TrafficLight') else 1.8)
        root = K.empty(f'Kit_{name}', loc=(x, 0, 0), collection=col)
        for lod, o in d.items():
            col.objects.link(o) if o.name not in col.objects else None
            for c in o.users_collection:
                if c != col:
                    c.objects.unlink(o)
            o.parent = root
            o.location = (0, 6 * lod, 0)
            o['lod'] = lod
            o['kit'] = name
            if name.split('_')[0].rstrip('0123456789') in PK.DEST or name in PK.DEST:
                o['destructible'] = 1
        total[name] = (K.tris(d[0]), K.tris(d[1]))
        x += w
    return total


def _main():
    K.reset()
    col = K.coll('Kit_Props')
    P = PK.all_props()
    tot = layout(P, col)
    for k, v in tot.items():
        print('TRIS', k, v)
    K.save_blend(BLEND)


if __name__ == '__main__':
    _main()
