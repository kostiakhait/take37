# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Zone groups, tail group pivot, colliders, centre of mass, emitters, final frame (nose +X, left +Y) and the root's metadata."""
import math
import bpy
import bmesh
from mathutils import Vector, Matrix
from . import kit, params as P
from .fuselage import boom_centre

ZONES = ['Zone_Cabin', 'Zone_Engine', 'Zone_TailBoom', 'Zone_MainRotor', 'Zone_TailRotor', 'Zone_Fuel', 'Zone_Skids']
RULES = [
    ('Zone_Fuel', ('Tank_', 'Fuel_Cap')),
    ('Zone_Skids', ('Skid_', 'Cross_', 'Step_', 'GroundWheel_')),
    ('Zone_TailRotor', ('TailRotor_', 'TR_')),
    ('Zone_MainRotor', ('Rotor_', 'Mast', 'Pylon_')),
    ('Zone_TailBoom', ('Boom_', 'Fin', 'Tail_Guard', 'Stab', 'Driveshaft', 'Beacon_', 'Light_Beacon', 'Light_Nav_White', 'Decal_Reg', 'TailGroup')),
    ('Zone_Engine', ('Engine_', 'Cowl_', 'Antenna')),
]


def zone_of(name):
    for z, prefixes in RULES:
        if name.startswith(prefixes):
            return z
    return 'Zone_Cabin'


def box_collider(root, M, name, c, size, kind='box', note=''):
    bm = bmesh.new()
    kit.bm_box(bm, c, size)
    ob = kit.from_bm(name, bm, [M['collider']], root, smooth=False)
    ob.display_type = 'WIRE'
    ob['collider'] = kind
    ob['size'] = [round(s, 3) for s in size]
    if note:
        ob['note'] = note
    return ob


def cyl_collider(root, M, name, p0, p1, r, n=12):
    bm = bmesh.new()
    kit.bm_cyl(bm, p0, p1, r, r, n=n, mat_idx=0)
    ob = kit.from_bm(name, bm, [M['collider']], root, smooth=False)
    ob.display_type = 'WIRE'
    ob['collider'] = 'capsule'
    ob['radius'] = r
    return ob


def finish(ctx):
    root, M = ctx['root'], ctx['M']
    parts = ctx['parts']
    bpy.context.view_layer.update()
    # --- tail group: the break plane of the boom (x = 3.20): everything behind it hangs under one pivot node that the game can bend, tear off and drop as one piece
    z3 = boom_centre(3.20).z
    tail = kit.empty('TailGroup', (3.20, 0.0, z3), root, kind='ARROWS', size=0.2, detach='boom_end', note='pivot on the break plane; rotate it to bend the boom, detach it to lose the tail',
                     bent_pose_euler_deg=[0, -16, 12])
    tail['zone'] = 'Zone_TailBoom'
    tail['state'] = 'intact'
    names = ['Boom_End', 'Fin', 'Tail_Guard', 'Stabilizer', 'StabPlate_R', 'StabPlate_L', 'Stab_Bracket', 'TR_Gearbox', 'TailRotor_Spin', 'Beacon_Base', 'Light_Beacon', 'Light_Nav_White_Tail', 'Driveshaft']
    for n in names:
        o = bpy.data.objects.get(n)
        if o is not None:
            kit.reparent(o, tail)
    # --- zone groups
    groups = {z: kit.empty(z, (0, 0, 0), root, kind='PLAIN_AXES', size=0.1, zone=z, state='intact') for z in ZONES}
    glass_grp = kit.empty('Zone_Cabin_Glass', (0, 0, 0), root, kind='PLAIN_AXES', size=0.1, zone='Zone_Cabin', state='intact', note='transparent panels, can be broken and removed independently')
    kit.reparent(glass_grp, groups['Zone_Cabin'])
    anchors_grp = kit.empty('Anchors', (0, 0, 0), root, kind='PLAIN_AXES', size=0.1)
    skip = set(ZONES) | {'Zone_Cabin_Glass', 'Anchors', 'Colliders', 'Emitters', 'Damage_States'}
    for o in list(root.children):
        if o.name in skip or o.name == 'TailGroup' and False:
            continue
        if o.name in ctx.get('anchors_names', ()):
            continue
        if o.name in [a.name for a in ctx['anchors'].values()]:
            kit.reparent(o, anchors_grp)
            continue
        if o.name.startswith('Glass_'):
            kit.reparent(o, glass_grp)
            continue
        z = o.get('zone') or zone_of(o.name)
        kit.reparent(o, groups[z])
        o['zone'] = z
    # doors' glass panels belong to the Glass group but travel with the door (children of the door node, tagged)
    for side in ('R', 'L'):
        g = bpy.data.objects.get('Door_%s_Glass' % side)
        if g is not None:
            g['zone'] = 'Zone_Cabin'
            g['glass'] = True
    # --- centre of mass and anchors
    com = kit.empty('CenterOfMass', (0.02, 0.0, 1.02), root, kind='SPHERE', size=0.08, mass_kg=P.EMPTY_KG, note='empty airframe CG near the mast axis (R22 CG range sits at the rotor axis); add 2 occupants + fuel in the game')
    # --- emitters (smoke / fire / sparks / fuel) for the destruction logic and effects
    em = kit.empty('Emitters', (0, 0, 0), root, kind='PLAIN_AXES', size=0.1)
    E = [('Emit_Smoke_Engine', (1.25, 0.0, 1.05), 'Zone_Engine'), ('Emit_Fire_Engine', (1.20, 0.25, 0.80), 'Zone_Engine'), ('Emit_Fire_Exhaust', (1.60, 0.22, 0.52), 'Zone_Engine'),
         ('Emit_Smoke_TailBoom', (3.20, 0.0, z3), 'Zone_TailBoom'), ('Emit_Fuel_Leak_Main', (0.52, 0.34, 0.60), 'Zone_Fuel'), ('Emit_Fuel_Leak_Aux', (0.52, -0.34, 0.60), 'Zone_Fuel'),
         ('Emit_Fire_Fuel', (0.52, 0.34, 0.75), 'Zone_Fuel'), ('Emit_Sparks_Cabin', (-0.80, 0.0, 1.20), 'Zone_Cabin'), ('Emit_Glass_Windshield', (-1.20, 0.0, 1.30), 'Zone_Cabin'),
         ('Emit_Debris_MainRotor', tuple(Vector((0, 0, P.HUB_Z - 0.06))), 'Zone_MainRotor'), ('Emit_Sparks_TailRotor', tuple(ctx['tr_hub']), 'Zone_TailRotor'),
         ('Emit_Dust_Skid_L', (-0.4, -0.925, 0.0), 'Zone_Skids'), ('Emit_Dust_Skid_R', (-0.4, 0.925, 0.0), 'Zone_Skids')]
    for n, p, z in E:
        e = kit.empty(n, p, em, kind='SPHERE', size=0.06, zone=z, emitter=n.split('_')[1].lower())
    # --- colliders: simplified physics bodies for the fall as one rigid body
    cg = kit.empty('Colliders', (0, 0, 0), root, kind='PLAIN_AXES', size=0.1, note='boxes/capsules, hide in the render; the whole fuselage is one rigid body (mass 399 kg empty + occupants)')
    cols = [
        box_collider(cg, M, 'Collider_Cabin', (-0.40, 0.0, 1.15), (2.50, 1.06, 1.20), note='cabin shell'),
        box_collider(cg, M, 'Collider_Engine', (1.22, 0.0, 0.88), (0.80, 0.82, 0.70), note='engine bay + cowl'),
        box_collider(cg, M, 'Collider_Pylon', (0.30, 0.0, 2.00), (0.95, 0.40, 0.90), note='mast fairing + hub'),
        cyl_collider(cg, M, 'Collider_Boom', (1.36, 0, boom_centre(1.36).z), (4.60, 0, boom_centre(4.60).z), 0.13),
        box_collider(cg, M, 'Collider_Fin', (4.45, 0.0, 1.85), (0.36, 0.06, 1.10), note='fin + tail guard'),
        box_collider(cg, M, 'Collider_Skid_R', (-0.45, 0.925, 0.06), (2.40, 0.10, 0.12), note='skid right'),
        box_collider(cg, M, 'Collider_Skid_L', (-0.45, -0.925, 0.06), (2.40, 0.10, 0.12), note='skid left'),
        box_collider(cg, M, 'Collider_Stab', (3.68, 0.0, 1.66), (0.22, 0.90, 0.05), note='stabiliser'),
    ]
    # --- soot/dirt layer: every mesh gets a Color attribute (white = clean, darker toward the belly and the engine bay, speckled)
    import numpy as np
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.name.startswith('Collider_'):
            continue
        extra = None
        if o.name.startswith(('Engine_', 'Cowl_')):
            extra = lambda co: 0.25
        kit.ensure_attr(o)
        me = o.data
        ca = me.color_attributes['Color']
        rs = np.random.RandomState(abs(hash(o.name)) % 9999)
        ow = o.matrix_world
        for p in me.polygons:
            for li in p.loop_indices:
                co = ow @ me.vertices[me.loops[li].vertex_index].co
                t = min(max((co.z - 0.5) / 1.0, 0.0), 1.0)
                v = (0.62 + 0.38 * t) * (0.96 + 0.04 * rs.rand())
                if extra:
                    v *= 0.75
                ca.data[li].color = (v, v, v * 0.97, 1.0)
    # --- the export frame: nose +X, left +Y (rotate the whole content 180 deg about the vertical; the root itself stays identity)
    bpy.context.view_layer.update()
    rot = Matrix.Rotation(math.pi, 4, 'Z')
    for o in list(root.children):
        o.matrix_world = rot @ o.matrix_world
    bpy.context.view_layer.update()
    root['asset'] = 'Robinson R22 Beta II'
    root['frame'] = 'glb: Y up, nose +X, left -Z (like the cars); metres; origin on the ground under the main rotor axis'
    root['mass_kg'] = P.EMPTY_KG
    root['registration'] = P.REG
    root['main_rotor'] = 'axis +Y, counter-clockwise seen from above, 530 rpm nominal, radius 3.835 m; node Rotor_Spin spins, Rotor_Teeter inside it teeters about the fore-aft axis'
    root['tail_rotor'] = 'left side of the boom; node TailRotor_Spin spins about the lateral axis; direction unverified'
    root['livery'] = 'colours are material factors: R22_paint_main, R22_paint_accent, R22_paint_red'
    root['damage'] = 'nodes under Damage_States are hidden by default; each group lists `replaces` (intact nodes to hide) when shown'
