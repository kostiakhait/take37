# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Cockpit of the R22. Build frame: the NOSE POINTS TO -X and +Y is the aircraft's RIGHT (the export rotates the root 180 deg about Z: nose +X, left +Y as the other models).
Floor, two seats (pilot RIGHT = +Y, passenger LEFT = -Y) with three-point harnesses, instrument pod with gauges (textures in code), centre console, cyclic T-bar between the seats,
two collective levers, two sets of pedals, heater/vents, fuel bladders and filler caps, and the anchors for the characters."""
import math
import bpy
import bmesh
from mathutils import Vector, Matrix
from . import kit, params as P
from .fuselage import cabin_point

SEAT_Y = 0.275          # seat centre lines (+Y = right = pilot)
FLOOR_Z = 0.64
QUAD_UV = [(0, 0), (1, 0), (1, 1), (0, 1)]


def quad(name, pts, uvs, mat, parent, smooth=False):
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    vs = [bm.verts.new(Vector(p)) for p in pts]
    f = bm.faces.new(vs)
    for lp, uv in zip(f.loops, uvs):
        lp[uvl].uv = uv
    return kit.from_bm(name, bm, [mat], parent, smooth=smooth)


def rbox(bm, c, size, r=0.01, mat_idx=0, tilt=0.0):
    """box with rounded edges centred at c; tilt about Y in radians"""
    r0 = bmesh.ops.create_cube(bm, size=1.0)
    verts = r0['verts']
    for v in verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    if tilt:
        bmesh.ops.rotate(bm, verts=verts, cent=(0, 0, 0), matrix=Matrix.Rotation(tilt, 3, 'Y'))
    bmesh.ops.translate(bm, verts=verts, vec=Vector(c))
    faces = {f for v in verts for f in v.link_faces}
    if r > 0:
        edges = list({e for v in verts for e in v.link_edges})
        res = bmesh.ops.bevel(bm, geom=edges, offset=r, segments=2 if kit.DET >= 1 else 1, affect='EDGES', profile=0.6)
        faces = {f for f in faces if f.is_valid} | set(res['faces'])
    for f in faces:
        f.material_index = mat_idx
        f.smooth = True
    return verts


def strap(bm, p0, p1, w=0.046, th=0.004, mat_idx=0):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    dn = d.normalized()
    n = Vector((0, 0, 1)) if abs(dn.z) < 0.9 else Vector((1, 0, 0))
    wdir = dn.cross(n).normalized()
    nd = dn.cross(wdir).normalized()
    vs = []
    for sx in (0, 1):
        for sw in (-1, 1):
            for sn in (-1, 1):
                vs.append(bm.verts.new(p0 + d * sx + wdir * w / 2 * sw + nd * th / 2 * sn))
    for fi in [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]:
        f = bm.faces.new([vs[i] for i in fi])
        f.material_index = mat_idx
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))


def seat(root, M, name, y):
    """one seat: cushion, back with side bolsters, trim base, three-point belt"""
    bm = bmesh.new()
    rbox(bm, (0.10, y, 0.77), (0.48, 0.38, 0.15), 0.03, 0)
    rbox(bm, (0.10, y, 0.70), (0.44, 0.34, 0.06), 0.01, 1)
    ob_c = kit.from_bm(name + '_Cushion', bm, [M['velour'], M['seat_trim']], root)
    kit.box_uv(ob_c, 1.6)
    bm = bmesh.new()
    rbox(bm, (0.38, y, 1.12), (0.12, 0.39, 0.66), 0.035, 0, tilt=math.radians(-11))
    rbox(bm, (0.33, y - 0.185, 1.02), (0.14, 0.035, 0.46), 0.015, 1, tilt=math.radians(-11))
    rbox(bm, (0.33, y + 0.185, 1.02), (0.14, 0.035, 0.46), 0.015, 1, tilt=math.radians(-11))
    ob_b = kit.from_bm(name + '_Back', bm, [M['velour'], M['seat_trim']], root)
    kit.box_uv(ob_b, 1.6)
    node = kit.empty(name, (0.10, y, 0.86), root, kind='ARROWS', size=0.12, role=name.lower())
    kit.reparent(ob_c, node)
    kit.reparent(ob_b, node)
    inb = -1 if y > 0 else 1            # toward the centre line
    bx = (0.18, y + inb * 0.06, 0.88)
    bm = bmesh.new()
    strap(bm, (0.04, y - inb * 0.19, 0.86), bx)
    strap(bm, (0.04, y + inb * 0.19, 0.86), bx)
    strap(bm, (0.50, y - inb * 0.12, 1.40), (0.38, y - inb * 0.06, 1.22))
    strap(bm, (0.38, y - inb * 0.06, 1.22), bx)
    kit.bm_box(bm, bx, (0.05, 0.04, 0.02), mat_idx=1)
    ob = kit.from_bm(name + '_Belt', bm, [M['belt'], M['steel']], root, smooth=False)
    kit.reparent(ob, node)
    kit.tag(node, 'Zone_Cabin', 'intact', detach='part')
    return node


def build(ctx):
    root, M = ctx['root'], ctx['M']
    it = {}
    bm = bmesh.new()
    rbox(bm, (-0.25, 0.0, FLOOR_Z - 0.008), (2.00, 0.74, 0.016), 0.004, 0)
    it['floor'] = kit.from_bm('Cabin_Floor', bm, [M['carpet']], root)
    kit.box_uv(it['floor'], 1.2)
    bm = bmesh.new()
    rbox(bm, (0.70, 0.0, 0.92), (0.10, 0.80, 0.55), 0.01, 0)
    it['wall'] = kit.from_bm('Cabin_RearWall', bm, [M['int_dark']], root)
    bm = bmesh.new()
    for sgn in (1, -1):
        kit.bm_box(bm, (-0.25, sgn * 0.45, 0.73), (1.40, 0.06, 0.05), mat_idx=0)
    it['sills'] = kit.from_bm('Cabin_Sills', bm, [M['int_grey']], root, smooth=False)
    it['seat_p'] = seat(root, M, 'Seat_Pilot', SEAT_Y)
    it['seat_c'] = seat(root, M, 'Seat_Passenger', -SEAT_Y)
    # instrument pod (the six-hole panel of the Beta II): hood over the gauges, face plane with the gauge texture seen by the pilot (+X side)
    bm = bmesh.new()
    rbox(bm, (-0.43, 0.0, 1.07), (0.34, 0.66, 0.26), 0.05, 0, tilt=math.radians(-6))
    rbox(bm, (-0.36, 0.0, 1.22), (0.40, 0.70, 0.035), 0.016, 0)
    it['pod'] = kit.from_bm('Panel_Pod', bm, [M['plastic']], root)
    kit.box_uv(it['pod'], 2)
    fx = -0.43 + 0.17 + 0.003
    hw, hh, cz0 = 0.30, 0.15, 1.07
    pts = [(fx, -hw, cz0 - hh), (fx, +hw, cz0 - hh), (fx, +hw, cz0 + hh), (fx, -hw, cz0 + hh)]
    it['face'] = quad('Panel_Gauges', pts, QUAD_UV, M['panel_front'], root)
    it['face_glass'] = quad('Panel_Gauge_Glass', [(p[0] + 0.004, p[1], p[2]) for p in pts], QUAD_UV, M['gauge_glass'], root)
    bm = bmesh.new()
    rbox(bm, (-0.36, 0.0, 0.80), (0.28, 0.26, 0.34), 0.03, 0)
    it['console'] = kit.from_bm('Console', bm, [M['plastic']], root)
    kit.box_uv(it['console'], 2)
    cfx = -0.36 + 0.14 + 0.004
    it['console_face'] = quad('Console_Gauges', [(cfx, -0.115, 0.70), (cfx, 0.115, 0.70), (cfx, 0.115, 0.93), (cfx, -0.115, 0.93)], QUAD_UV, M['console'], root)
    bm = bmesh.new()
    for yy in (-0.22, 0.22):
        kit.bm_cyl(bm, (-0.285, yy, 0.93), (-0.25, yy, 0.93), 0.035, 0.03, n=14, mat_idx=0)
    kit.bm_cyl(bm, (-0.24, 0.07, 0.88), (-0.22, 0.07, 0.88), 0.014, 0.014, n=10, mat_idx=1)
    it['vent'] = kit.from_bm('Vent_Heater', bm, [M['plastic'], M['trim']], root)
    # cyclic: pivot at the base; column, T-bar, grips (the right one is the pilot's)
    cyc = kit.empty('Cyclic', (-0.18, 0.0, 0.67), root, kind='ARROWS', size=0.12, role='cyclic pivot (base of the column)')
    bm = bmesh.new()
    kit.bm_tube(bm, [(-0.18, 0, 0.67), (-0.18, 0, 0.86), (-0.20, 0, 0.99)], 0.02, n=14, mat_idx=0)
    kit.bm_tube(bm, [(-0.20, 0.40, 1.03), (-0.20, 0.30, 0.995), (-0.20, -0.30, 0.995), (-0.20, -0.40, 1.03)], 0.016, n=12, mat_idx=0)
    kit.bm_cyl(bm, (-0.20, 0.405, 0.92), (-0.20, 0.405, 1.03), 0.02, 0.019, n=12, mat_idx=2)
    kit.bm_cyl(bm, (-0.20, -0.405, 0.95), (-0.20, -0.405, 1.03), 0.02, 0.019, n=12, mat_idx=2)
    kit.bm_box(bm, (-0.215, 0.41, 1.0), (0.05, 0.05, 0.06), mat_idx=1)
    kit.bm_cyl(bm, (-0.18, 0, 0.64), (-0.18, 0, 0.74), 0.045, 0.03, n=14, mat_idx=1)
    ob = kit.from_bm('Cyclic_Stick', bm, [M['steel_dark'], M['plastic'], M['rubber']], root)
    kit.reparent(ob, cyc)
    it['cyclic'] = cyc
    for nm, yy in (('Collective_Pilot', 0.075), ('Collective_Passenger', -0.075)):
        piv = kit.empty(nm, (0.20, yy, 0.69), root, kind='ARROWS', size=0.1, role='collective pivot (aft end, on the floor)')
        bm = bmesh.new()
        kit.bm_tube(bm, [(0.20, yy, 0.69), (0.05, yy, 0.74), (-0.12, yy, 0.80)], 0.016, n=12, mat_idx=0)
        kit.bm_cyl(bm, (-0.12, yy, 0.80), (-0.30, yy, 0.82), 0.022, 0.021, n=14, mat_idx=1)
        kit.bm_box(bm, (-0.115, yy, 0.835), (0.04, 0.05, 0.025), mat_idx=0)
        ob = kit.from_bm(nm + '_Lever', bm, [M['steel_dark'], M['rubber']], root)
        kit.reparent(ob, piv)
        it[nm] = piv
    for set_name, yy in (('Pilot', SEAT_Y), ('Passenger', -SEAT_Y)):
        for side, dy in (('L', -0.085), ('R', 0.085)):          # +Y is right
            y = yy + dy
            piv = kit.empty('Pedal_%s_%s' % (set_name, side), (-0.80, y, 0.67), root, kind='ARROWS', size=0.08, role='pedal pivot')
            bm = bmesh.new()
            kit.bm_tube(bm, [(-0.80, y, 0.67), (-0.88, y, 0.73), (-0.98, y, 0.77)], 0.014, n=10, mat_idx=0)
            kit.bm_box(bm, (-1.0, y, 0.78), (0.03, 0.115, 0.15), mat_idx=1)
            ob = kit.from_bm('Pedal_%s_%s_Mesh' % (set_name, side), bm, [M['steel_dark'], M['rubber']], root)
            kit.reparent(ob, piv)
            it['pedal_%s_%s' % (set_name, side)] = piv
    # fuel bladders and filler caps (main on the right, auxiliary on the left)
    bm = bmesh.new()
    rbox(bm, (0.52, 0.34, 0.70), (0.34, 0.34, 0.20), 0.05, 0)
    it['tank_main'] = kit.from_bm('Tank_Main', bm, [M['fuel']], root)
    bm = bmesh.new()
    rbox(bm, (0.52, -0.34, 0.70), (0.34, 0.34, 0.20), 0.05, 0)
    it['tank_aux'] = kit.from_bm('Tank_Aux', bm, [M['fuel']], root)
    for nm, sgn in (('Fuel_Cap_Main', 1), ('Fuel_Cap_Aux', -1)):
        ang = math.radians(62)
        p = cabin_point(2.18, sgn * ang) if sgn > 0 else cabin_point(2.18, 2 * math.pi - ang)
        nrm = Vector((0, math.sin(ang) * sgn, math.cos(ang))).normalized()
        bm = bmesh.new()
        kit.bm_cyl(bm, p - nrm * 0.006, p + nrm * 0.008, 0.042, 0.042, n=24, mat_idx=0)
        kit.bm_cyl(bm, p + nrm * 0.008, p + nrm * 0.016, 0.03, 0.03, n=20, mat_idx=1)
        kit.bm_cyl(bm, p + nrm * 0.016, p + nrm * 0.024, 0.012, 0.012, n=8, mat_idx=1)
        it[nm] = kit.from_bm(nm, bm, [M['alu'], M['plastic']], root)
    A = {}
    A['Seat_Pilot_Anchor'] = kit.empty('Seat_Pilot_Anchor', (0.14, SEAT_Y, 0.86), root, role='pilot pelvis on the cushion (right seat)')
    A['Seat_Passenger_Anchor'] = kit.empty('Seat_Passenger_Anchor', (0.14, -SEAT_Y, 0.86), root, role='passenger pelvis (left seat)')
    A['Hand_Cyclic'] = kit.empty('Hand_Cyclic', (-0.20, 0.405, 1.00), root, kind='SPHERE', size=0.03, role='pilot right hand on the cyclic grip')
    A['Hand_Collective'] = kit.empty('Hand_Collective', (-0.21, 0.075, 0.815), root, kind='SPHERE', size=0.03, role='pilot left hand on the collective grip')
    A['Foot_Pedal_L'] = kit.empty('Foot_Pedal_L', (-0.99, SEAT_Y - 0.085, 0.83), root, kind='SPHERE', size=0.03, role='pilot left foot')
    A['Foot_Pedal_R'] = kit.empty('Foot_Pedal_R', (-0.99, SEAT_Y + 0.085, 0.83), root, kind='SPHERE', size=0.03, role='pilot right foot')
    A['Door_Exit_Passenger'] = kit.empty('Door_Exit_Passenger', (-0.45, -1.05, 0.0), root, kind='CUBE', size=0.15, role='ground point outside the left door where the passenger steps out')
    A['Door_Exit_Passenger_Sill'] = kit.empty('Door_Exit_Passenger_Sill', (-0.45, -0.62, 0.80), root, kind='CUBE', size=0.1, role='sill of the left door')
    A['Eye_Pilot'] = kit.empty('Eye_Pilot', (0.30, SEAT_Y, 1.46), root, kind='SPHERE', size=0.03, role='pilot eye point')
    ctx['interior'] = it
    ctx['anchors'] = A
    for k, o in it.items():
        if isinstance(o, bpy.types.Object) and o.type == 'MESH':
            kit.ensure_attr(o)
