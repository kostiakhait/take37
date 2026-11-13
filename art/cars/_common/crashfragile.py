# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Fragile parts of a crashed car: lamps, grille, mirrors, door handles, trim strips, bumpers, plates, glass. Part-level states from the data table (crash_table.FRAGILE):
  lamps   ok / cracked / broken / hanging (by its wires) / missing         per corner 'front_L' 'front_R' 'rear_L' 'rear_R' (all lamps at that corner)
  grille  ok / cracked / broken / missing        mirrors, handles, trim (strips along the side)  per side 'L' 'R':  ok / bent|hanging / missing
  bumper  ok / sag / hang / missing, per end 'F' 'R' with the end that stays attached         plate  ok / tilted / hanging, per end
  glass   ok / cracked / shattered / gone, per region
Everything is found in the car by material and place (no node numbers of one car)."""
import math

import bmesh
import numpy as np
from mathutils import Vector as V3

import crashkit as ck

LENS = ('M_lens_clear', 'M_lens_red', 'M_lens_amber')
GLASS_FRAC = {'ok': 0.0, 'cracked': 0.3, 'shattered': 0.8, 'gone': 1.0}
BUMPER_PRESETS = {'sag': dict(roll=7, yaw=3, bow=0.03, drop=-0.07, fold=0.0, fold_t=0.0),
                  'hang': dict(roll=34, yaw=12, bow=0.06, drop=-0.30, fold=0.35, fold_t=0.1, fold_w=0.5, fold_z=0.08)}


def comp_table(ob):
    """connected pieces of a mesh with their materials, centre and box (world)"""
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    names = [m.name if m else '' for m in me.materials]
    P = ck.world(ob)[0]
    seen = np.zeros(len(bm.verts), bool)
    out = []
    for v0 in bm.verts:
        if seen[v0.index]:
            continue
        seen[v0.index] = True
        st, idx, mt = [v0], [], set()
        while st:
            v = st.pop()
            idx.append(v.index)
            for f in v.link_faces:
                mt.add(names[f.material_index])
            for e in v.link_edges:
                w = e.other_vert(v)
                if not seen[w.index]:
                    seen[w.index] = True
                    st.append(w)
        pts = P[idx]
        out.append(dict(idx=idx, mats=mt, c=pts.mean(axis=0), lo=pts.min(axis=0), hi=pts.max(axis=0)))
    bm.free()
    return out


def delete_verts(ob, idx):
    if not idx:
        return
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in idx], context='VERTS')
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()


def move_verts(ob, idx, fn):
    P = ck.world(ob)[0]
    P[idx] = fn(P[idx])
    ck.put(ob, P)


def add_wire(ob, a, b, radius=0.006):
    """a thin black cable from a to b (world) added to the mesh `ob` (uses its M_black)"""
    a, b = np.array(a, dtype=float), np.array(b, dtype=float)
    d = b - a
    L = float(np.linalg.norm(d))
    if L < 0.02:
        return
    names = [m.name if m else '' for m in ob.data.materials]
    mi = names.index('M_black') if 'M_black' in names else 0
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=5, radius1=radius, radius2=radius, depth=L)
    q = V3((0, 0, 1)).rotation_difference(V3((d / L).tolist()))
    inv = ob.matrix_world.inverted()
    mid = V3(((a + b) / 2).tolist())
    for v in res['verts']:
        v.co = inv @ (q @ v.co + mid)
    for f in {f for v in res['verts'] for f in v.link_faces}:
        f.material_index = mi
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()


def lamp_members(obs, corner):
    end, side = corner.split('_')
    res = {}
    for nm in ('Lamps_Head', 'Lamps_Park', 'Lamps_Tail', 'Lamps_Marker', 'Ends'):
        ob = obs.get(nm)
        if ob is None:
            continue
        for c in comp_table(ob):
            m = c['mats']
            isl = bool(m & set(LENS)) or 'M_reflector' in m or 'M_bulb' in m
            if nm == 'Ends' and 'M_chrome' in m and max(c['hi'] - c['lo']) < 0.5 and abs(c['c'][1]) > 0.12 and 0.55 < c['c'][2] < 0.95 and abs(c['c'][0]) > 2.0:
                isl = True
            if not isl:
                continue
            if (c['c'][0] > 0) != (end == 'front') or (c['c'][1] > 0) != (side == 'L'):
                continue
            res.setdefault(nm, []).append(c)
    return res


def lamp_state(obs, corner, state, seed):
    if state == 'ok':
        return
    mem = lamp_members(obs, corner)
    allc = [c for cs in mem.values() for c in cs]
    if not allc:
        return
    lens = [c for c in allc if c['mats'] & set(LENS)]
    ctr = np.mean([c['c'] for c in (lens or allc)], axis=0)
    rad = max(0.2, max(float(np.max(c['hi'] - c['lo'])) for c in (lens or allc)) * 0.6)
    near = lambda p: np.linalg.norm(np.array(p[:]) - ctr) < rad   # noqa: E731
    frac = {'cracked': 0.3, 'broken': 0.85, 'hanging': 0.55, 'missing': 1.0}[state]
    for nm in mem:
        if any(c['mats'] & set(LENS) for c in mem[nm]):
            ck.break_glass(obs[nm], near, frac, seed, cells=14, tilt=16.0, mats=LENS)
    end, side = corner.split('_')
    sg = 1 if side == 'L' else -1
    mem = lamp_members(obs, corner)
    if state in ('cracked', 'broken'):
        if state == 'broken':
            for nm, cs in mem.items():
                idx = [i for c in cs for i in c['idx']]
                move_verts(obs[nm], idx, lambda X: ck.rot_about(X, ctr, (1, 0, 0), math.radians(7 * sg)) + np.array([0.0, 0.0, -0.01]))
        return
    if state == 'missing':
        for nm, cs in mem.items():
            kill = [i for c in cs if (c['mats'] & set(LENS)) or 'M_bulb' in c['mats'] or ('M_chrome' in c['mats'] and 'M_reflector' not in c['mats']) for i in c['idx']]
            delete_verts(obs[nm], kill)
        mem = lamp_members(obs, corner)
        for nm, cs in mem.items():
            idx = [i for c in cs for i in c['idx']]
            move_verts(obs[nm], idx, lambda X: ck.rot_about(X, ctr, (0, 1, 0), math.radians(25)) + np.array([0.0, 0.0, -0.02]))
        return
    piv = ctr + np.array([0.0, 0.0, rad * 0.6])
    off = np.array([0.06 * sg, 0.0, -0.24])
    for nm, cs in mem.items():
        idx = [i for c in cs for i in c['idx']]
        move_verts(obs[nm], idx, lambda X: ck.rot_about(ck.rot_about(X, piv, (1, 0, 0), math.radians(-sg * 65)), piv, (0, 1, 0), math.radians(40 if end == 'front' else -40)) + off)
    if 'Ends' in obs:
        add_wire(obs['Ends'], piv, piv + off)
        add_wire(obs['Ends'], piv + np.array([0.0, 0.03 * sg, 0.0]), piv + off + np.array([0.03 * sg, 0.03 * sg, -0.03]))


def grille_box(obs):
    ob = obs.get('Ends')
    if ob is None:
        return None
    best = None
    for c in comp_table(ob):
        if 'M_chrome' in c['mats'] and c['c'][0] > 1.5 and abs(c['c'][1]) < 0.12 and c['hi'][1] - c['lo'][1] > 0.3:
            if best is None or (c['hi'][1] - c['lo'][1]) > (best['hi'][1] - best['lo'][1]):
                best = c
    return best


def grille_state(obs, state, seed):
    g = grille_box(obs)
    if g is None or state == 'ok':
        return
    ob = obs['Ends']
    ctr = (g['lo'] + g['hi']) / 2
    rad = (g['hi'] - g['lo']) / 2 * 1.5 + np.array([0.03, 0.02, 0.02])
    rad[0] = min(rad[0], 0.06)
    frac = {'cracked': 0.25, 'broken': 0.55, 'missing': 1.0}[state]
    ck.tear(ob, ctr, rad, frac, seed, 14)
    if state != 'missing':
        P, _ = ck.world(ob)
        idx = np.where(np.sum(((P - ctr) / rad) ** 2, axis=1) < 1.0)[0]
        top = ctr + np.array([0.0, 0.0, (g['hi'] - g['lo'])[2] / 2])
        if state == 'broken':
            P[idx] = ck.rot_about(P[idx], top, (0, 1, 0), math.radians(-20)) + np.array([0.0, 0.0, -0.05])
            P[idx] = ck.rot_about(P[idx], ctr, (1, 0, 0), math.radians(8))
        else:
            P[idx] = ck.rot_about(P[idx], ctr, (1, 0, 0), math.radians(4))
        ck.put(ob, P)


def mirror_state(obs, side, state):
    if state == 'ok':
        return
    for nm in [n for n in obs if n.startswith('Trim_F')]:
        ob = obs[nm]
        tab = comp_table(ob)
        seeds = [c for c in tab if 'M_mirror' in c['mats'] and (c['c'][1] > 0) == (side == 'L')]
        if not seeds:
            continue
        sc = seeds[0]['c']
        grp = [c for c in tab if np.linalg.norm(c['c'] - sc) < 0.24 and c['c'][2] > 0.9 and max(c['hi'] - c['lo']) < 0.35]
        idx = [i for c in grp for i in c['idx']]
        P = ck.world(ob)[0][idx]
        base = P[np.abs(P[:, 1]) < np.abs(P[:, 1]).min() + 0.05].mean(axis=0)
        sg = 1 if side == 'L' else -1
        if state == 'missing':
            delete_verts(ob, idx)
        elif state == 'bent':
            move_verts(ob, idx, lambda X: ck.rot_about(ck.rot_about(X, base, (0, 0, 1), math.radians(-sg * 35)), base, (1, 0, 0), math.radians(-sg * 25)))
        else:
            move_verts(ob, idx, lambda X: ck.rot_about(ck.rot_about(X, base, (1, 0, 0), math.radians(-sg * 85)), base, (0, 0, 1), math.radians(-sg * 30)))
            add_wire(ob, base, base + np.array([0.02, 0.1 * sg, -0.26]))


def handle_state(obs, side, state):
    if state == 'ok':
        return
    for nm in [n for n in obs if n.startswith('Trim_F')]:
        ob = obs[nm]
        tab = comp_table(ob)
        seeds = [c for c in tab if 'M_chrome' in c['mats'] and (c['c'][1] > 0) == (side == 'L') and 0.08 < c['hi'][0] - c['lo'][0] < 0.25 and c['hi'][1] - c['lo'][1] < 0.03
                 and 0.5 < c['c'][2] < 1.0 and c['hi'][2] - c['lo'][2] < 0.06]
        if not seeds:
            continue
        sc = seeds[0]['c']
        grp = [c for c in tab if np.linalg.norm(c['c'] - sc) < 0.14 and max(c['hi'] - c['lo']) < 0.3]
        idx = [i for c in grp for i in c['idx']]
        sg = 1 if side == 'L' else -1
        if state == 'missing':
            delete_verts(ob, idx)
        else:
            front = np.array([seeds[0]['hi'][0], sc[1], sc[2]])
            move_verts(ob, idx, lambda X: ck.rot_about(X, front, (0, 0, 1), math.radians(sg * 55)) + np.array([0.0, 0.0, -0.03]))


def trim_state(obs, side, state):
    """long strips along a side (chrome, black, rub strips): hanging = the rear end swings off the body, missing = gone"""
    if state == 'ok':
        return
    sg = 1 if side == 'L' else -1
    for nm in [n for n in obs if n == 'Trim' or n.startswith('Trim_F')]:
        ob = obs[nm]
        grp = [c for c in comp_table(ob) if (c['c'][1] > 0) == (side == 'L') and c['hi'][0] - c['lo'][0] > 0.7 and c['hi'][1] - c['lo'][1] < 0.06 and c['hi'][2] - c['lo'][2] < 0.5
               and abs(c['c'][1]) > 0.8 and ('M_chrome' in c['mats'] or 'M_black' in c['mats'] or 'M_bumper' in c['mats'])]
        if not grp:
            continue
        if state == 'missing':
            delete_verts(ob, [i for c in grp for i in c['idx']])
        else:
            for c in grp:
                front = np.array([c['hi'][0], c['c'][1], c['c'][2]])
                move_verts(ob, c['idx'], lambda X, front=front: ck.rot_about(X, front, (0, 0, 1), math.radians(-sg * 2.5)) + np.array([0.0, sg * 0.01, -0.03]))


def plate_hangs(car, states):
    out = []
    for key, c in car.plates.items():
        st = states.get(key, 'ok')
        if st == 'ok':
            continue
        sg = -1 if key == 'front' else 1
        if st == 'tilted':
            out.append(dict(center=tuple(c), r=0.25, pitch=sg * 14, roll=10, pivot=(0, 0, 0.07), move=(-sg * 0.07, 0.0, 0.0)))
        else:
            out.append(dict(center=tuple(c), r=0.25, pitch=sg * 36, roll=24, pivot=(0, 0, 0.07), move=(-sg * 0.12, 0.0, -0.10)))
    return out


def apply_fragile(obs, fr, seed):
    for i, (corner, st) in enumerate(sorted(fr.get('lamps', {}).items())):
        lamp_state(obs, corner, st, seed + i)
    grille_state(obs, fr.get('grille', 'ok'), seed + 31)
    for side, st in fr.get('mirrors', {}).items():
        mirror_state(obs, side, st)
    for side, st in fr.get('handles', {}).items():
        handle_state(obs, side, st)
    for side, st in fr.get('trim', {}).items():
        trim_state(obs, side, st)


def resolve_fragile(spec, car):
    """glass, bumper and plate states become the glass fractions, the part ops, the tears and the hangs that crashkit.crash understands"""
    fr = spec.get('fragile')
    if not fr:
        return spec
    for k, st in fr.get('glass', {}).items():
        spec.setdefault('glass', {})[k] = max(GLASS_FRAC[st], spec.get('glass', {}).get(k, 0))
    for end, (st, frm) in fr.get('bumper', {}).items():
        nm = 'Bumper_' + end
        if st == 'missing':
            spec.setdefault('remove', []).append(nm)
        elif st in BUMPER_PRESETS:
            spec.setdefault('parts', {})[nm] = [dict(op='hang_bumper', **{'from': frm}, **BUMPER_PRESETS[st])]
            c = ((car.nose if end == 'F' else car.tail), -frm * 0.45, 0.5)
            spec.setdefault('tears', []).append(dict(node=nm, center=c, radii=(0.2, 0.28, 0.15), frac=0.45 if st == 'hang' else 0.25, cells=10))
    spec.setdefault('hangs', []).extend(plate_hangs(car, fr.get('plate', {})))
    return spec
