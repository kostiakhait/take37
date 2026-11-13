# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""Per-car numbers of the damage table, only where the picture asks (crash_table.PROFILES[<car folder name>]). The coupe table is written in the coupe's metres and parts; a car with another
layout (a pickup: a cab, an open bed and a tailgate instead of a trunk lid) gives its own measures here: where the hood hinges, which glass pane lies where, which lid it has at the rear.
Each profile: hood_x, hood_len (hood hinge and length), trunk_x=None (no trunk lid), adapt(spec, kind, degree) -> spec (the car's changes of the generic row, left-hand side)."""
import copy

# ---- pickup (Ford F-150 1987 look): cab x -0.38..0.86, hood hinge 0.87 .. nose 2.13, bumper 2.27, bed floor z 0.80 up to the box rim 1.2, tailgate at x -2.6 (z 0.6..1.2), roof 1.78 ----------
PK_HOOD_X, PK_HOOD_LEN = 0.87, 1.26
PK_TAIL = -2.57


def _map_x(x, a0, a1, b0, b1):
    return b0 + (x - a0) * (b1 - b0) / (a1 - a0)


def pickup_adapt(spec, kind, d):
    pick = lambda a: a[d - 1]   # noqa: E731
    sp = spec
    # glass panes by place: the windscreen and the back light are the two panes of the 'Glass' node; no quarter windows
    sp['regions'] = dict(wind=(-0.05, 1.0, 0.0, 0.95), rear=(-1.0, -0.05, 0.0, 0.95), opera=(9.0, 9.0, 9.0, 9.0))
    # the hood: the coupe's hinge and crease positions are scaled onto the pickup's shorter hood
    parts = sp.setdefault('parts', {})
    for o in parts.get('Hood', []):
        if o['op'] == 'hinge':
            o['x'] = PK_HOOD_X if abs(o['x'] - 0.835) < 1e-6 else _map_x(o['x'], 0.835, 2.2, PK_HOOD_X, 2.05)
    # no trunk lid: the tailgate hangs open on its chains the harder the rear is hit
    parts.pop('Trunk', None)
    gate = {'rear': [6, 35, 80], 'rear_corner': [4, 25, 70], 'roll': [4, 12, 30], 'side': [0, 0, 8]}.get(kind)
    if gate and gate[d - 1]:
        depth = {'rear': [0.5, 0.95, 1.35], 'rear_corner': [0.5, 0.95, 1.35]}.get(kind, [0, 0, 0])[d - 1]
        parts['Tailgate'] = [dict(op='rigid', pivot=(PK_TAIL + 0.72 * depth, 0.0, 0.62), axis=(0, 1, 0), angle=-gate[d - 1])]
    elif kind in ('front', 'front_corner'):
        parts['Tailgate'] = [dict(op='rigid', pivot=(PK_TAIL, 0.0, 0.62), axis=(0, 1, 0), angle=-pick([0, 3, 7]))]
    # the roof: pillars and ridges of the coupe's greenhouse mapped onto the pickup's cab (belt 1.23, roof 1.78, cab centre x 0.24)
    r = sp.get('roof')
    if r:
        r['pillars'] = [(1.23 + (z - 0.92) * 1.28, lam * 1.2, amp) for (z, lam, amp) in r.get('pillars', [])]
        r['ridges'] = [(_map_x(x, -0.3, 0.9, 0.24, 0.84), lam * 0.7, amp) for (x, lam, amp) in r.get('ridges', [])]
    # the cab: a side hit lands on the cab door (lateral centre = x of the door), not on the coupe's door position
    c = sp.get('crush')
    if kind == 'side' and c:
        c['t0'] = 0.25
        c['zc'] = 1.0
        c['zh'] = 0.6
    # beaten metal: the roof and floor dents of the coupe's list land where this car has them (roof 1.78, bed floor 0.80, bed walls up to 1.2, hood 1.0-1.3)
    bw = []
    for b in sp.get('bowls', []):
        b = copy.deepcopy(b)
        x, y, z = b['center']
        if b['dir'][2] < 0 and z > 1.3:                     # roof dents: into the cab roof
            b['center'] = (_map_x(x, -0.3, 0.3, 0.05, 0.6), y * 0.9, 1.76)
        elif b['dir'][2] < 0 and x < -1.2:                  # bed: the floor is dented
            b['center'] = (x, y, 0.80)
        elif b['dir'][2] < 0 and x > 1.2:                   # hood
            b['center'] = (min(x, 1.9), y, 1.18)
        elif abs(b['dir'][1]) > 0.5 and x < -0.6:           # side dents of the bed: on the box walls
            b['center'] = (x, y, 1.0)
        bw.append(b)
    sp['bowls'] = bw
    if sp.get('tears'):
        for t in sp['tears']:
            if t['node'] == 'Body':     # the roof is torn open where the cab roof ends up after the crush
                t['center'] = (0.25, t['center'][1], 1.55)
                t['radii'] = (0.5, 0.4, 0.28)
    # the soot lies over the cab and bed, not at the coupe's positions
    for sc in sp.get('scorch', []):
        x, y, z = sc['center']
        if abs(z - 0.5) < 1e-6:
            sc['center'] = (x, y, 0.8)
    return sp


PROFILES = {
    'pickup': dict(hood_x=PK_HOOD_X, hood_len=PK_HOOD_LEN, trunk_x=None, adapt=pickup_adapt),
}
