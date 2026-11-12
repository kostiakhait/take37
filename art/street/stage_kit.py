# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""The reusable kit as one glb: every street prop (LOD0 + LOD1), 12 of the building designs (LOD0 + LOD1), a 20 m straight road module and a four-way intersection module.
  blender -b -P art/street/stage_kit.py -- [--kit art/street/street_kit.glb] [--blend D:/temp/take37/street/blend/kit.blend]
Nodes: Kit_<Name> empties (children <Name>_LOD0 / _LOD1). Road modules: Module_Straight20, Module_Cross (origin at the crossing centre, street along X, side street along +Y/-Y).
"""
import pathlib
import sys

import bpy

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import buildings as B  # noqa: E402
import kitlib as K  # noqa: E402
import props_kit as PK  # noqa: E402
import street_geo as G  # noqa: E402
import stage_props as SP  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
arg = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d  # noqa: E731
KIT = arg('--kit', str(pathlib.Path(__file__).resolve().parent / 'street_kit.glb'))
BLEND = arg('--blend', 'D:/temp/take37/street/blend/kit.blend')

K.reset()
root = K.empty('StreetKit', size=2.0)
col = K.coll('Kit')
P = PK.all_props()
tot = SP.layout(P, col)
for o in list(col.objects):
    if o.parent is None and o.name.startswith('Kit_'):
        o.parent = root
x = sum(2.5 if n.startswith('StreetTree') else (3.0 if n in ('CrowdBarrier', 'Sawhorse', 'LampCobra', 'TrafficLight') else 1.8) for n in P) + 6
BT = {}
for i, d in enumerate(B.make_designs(36)[::3]):
    d = dict(d)
    d['D'] = 16.0
    e = K.empty(f"Kit_Building_{d['name']}", loc=(x + d['W'] / 2, 20, 0), parent=root, collection=col)
    for lod in (0, 1):
        o = B.make_building(d, lod)
        for c in o.users_collection:
            c.objects.unlink(o)
        col.objects.link(o)
        o.parent = e
        o.location = (0, 0, 0)
        o['lod'] = lod
        o['kit'] = f"Building_{d['name']}"
    BT[d['name']] = (K.tris(e.children[0]), K.tris(e.children[1]))
    x += d['W'] + 3
# road modules
for name, (l0, l1, cl, cr, off) in (('Module_Straight20', (0.0, 20.0, [], [], (0, 40, 0))), ('Module_Cross', (-30.0, 30.0, [0.0], [0.0], (0, 100, 0)))):
    G.L0, G.L1 = l0, l1
    G.SIDE_LEN = 20.0
    CH = G.Chunker(name)
    G.build_road(CH, cl, cr, None, None)
    G.build_markings(CH, cl, cr, None)
    G.build_decals(CH, cl, cr, None)
    em = K.empty(name, loc=off, parent=root, collection=col)
    for o in CH.build_all(col, em):
        pass
K.save_blend(BLEND)
K.export_glb(K.descendants(root), KIT)
print('KIT_TRIS_PROPS', tot)
print('KIT_TRIS_BUILDINGS', BT)
