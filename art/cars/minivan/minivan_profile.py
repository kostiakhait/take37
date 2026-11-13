# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""The minivan's profile of the damage table (registered into crash_table.PROFILES by minivan_crash_run.py; the table itself is written in the coupe's metres).
The minivan differs from the coupe: a short hood (hinge at the cowl x 1.07, nose 2.25), a tall cab (belt 1.03, roof 1.64), a liftgate hinged at the roof edge (x -1.75, z 1.58) instead of a
trunk lid, a sliding right door (Door_SR) and no left rear door, a windscreen raked from the cowl back to x 0.05, side windows in the body glass (quarters and the left sliding-door window),
the liftgate window as its own node. adapt() maps every absolute coordinate of the coupe row onto this car and renames the parts."""
import copy

# the coupe's measures (crashkit.Car of coupe_final.blend)
C = dict(nose=2.5028, tail=-2.6127, hw=0.9111, belt=0.9159, zroof=1.3744, hood_x=0.835, hood_end=2.38, cab0=-1.4856, cab1=0.8176)
# the minivan's measures (crashkit.Car of minivan_final.blend)
M = dict(nose=2.2477, tail=-2.2488, hw=0.8819, belt=1.0333, zroof=1.6358, hood_x=1.0728, hood_end=1.98, cab0=-1.8629, cab1=1.0502)
GATE_X, GATE_Z = -1.75, 1.58        # liftgate hinge (top edge)
GATE_X_FOOT = -2.17                 # the liftgate's foot at z 0.62
HOOD_X, HOOD_LEN = M['hood_x'], M['hood_end'] - M['hood_x']
GATE_LEN = GATE_X - GATE_X_FOOT
SX = (M['nose'] - M['tail']) / (C['nose'] - C['tail'])           # 0.88
SZ = (M['zroof'] - M['belt']) / (C['zroof'] - C['belt'])         # 1.31


def tx(x):
    return M['tail'] + (x - C['tail']) * SX


def ty(y):
    return y * M['hw'] / C['hw']


def tz(z):
    if z <= C['belt']:
        return z * M['belt'] / C['belt']
    return M['belt'] + (z - C['belt']) * SZ


def tp(p):
    return (tx(p[0]), ty(p[1]), tz(p[2]))


def gate_z(x):
    """height of the liftgate's slanted skin at x"""
    return 0.62 + (x - GATE_X_FOOT) / (GATE_LEN / (GATE_Z - 0.62))


def adapt(spec, kind, d):
    sp = spec
    # ---- crush fields: lengths along the car shrink with the car, heights follow the belt line
    for ck in ('crush', 'crush2'):
        c = sp.get(ck)
        if not c:
            continue
        c['depth'] *= 0.92
        if c['end'] in ('front', 'rear'):
            c['length'] *= SX
        c['width'] *= 0.97
        if 't0' in c:
            c['t0'] *= 0.97
        c['zc'], c['zh'] = tz(c['zc']), c['zh'] * 1.13
        for r in c.get('ridges', []):
            r['c'] *= SX
            r['lam'] *= 1.1
    # ---- the roof of the cab
    r = sp.get('roof')
    if r:
        xm0, xm1 = 0.5 * (C['cab0'] + C['cab1']), 0.5 * (M['cab0'] + M['cab1'])
        k = (M['cab1'] - M['cab0']) / (C['cab1'] - C['cab0'])
        r['pillars'] = [(tz(z), lam * 1.3, amp * 1.15) for (z, lam, amp) in r.get('pillars', [])]
        r['ridges'] = [(xm1 + (x - xm0) * k, lam * 1.25, amp * 1.15) for (x, lam, amp) in r.get('ridges', [])]
    # ---- scattered marks: positions, sizes
    for b in sp.get('bowls', []):
        b['center'] = tp(b['center'])
        b['r'] *= 0.95
    for s in sp.get('scorch', []):
        s['center'] = tp(s['center'])
        s['r'] *= 0.92
    for s in sp.get('scrape', []):
        s['z'], s['h'] = tz(s['z']), s['h'] * 1.1
        s['x0'], s['x1'] = tx(s['x0']), tx(s['x1'])
    for t in sp.get('tears', []):
        t['center'] = tp(t['center'])
        t['radii'] = (t['radii'][0] * SX * 1.1, t['radii'][1], t['radii'][2] * SZ)
    for h in sp.get('hangs', []):
        h['center'] = tp(h['center'])
    # ---- hood: hinge and creases scaled onto the hood's own length
    parts = sp.setdefault('parts', {})
    for o in parts.get('Hood', []):
        if o['op'] == 'hinge':
            o['x'] = HOOD_X if abs(o['x'] - C['hood_x']) < 1e-6 else HOOD_X + (o['x'] - C['hood_x']) / (C['hood_end'] - C['hood_x']) * HOOD_LEN
            o['z'] = 1.0
    # ---- the trunk lid becomes the liftgate: it hinges at its top edge, its creases lie on its slanted skin
    tr = parts.pop('Trunk', [])
    lg = []
    for o in tr:
        o = copy.deepcopy(o)
        if o['op'] == 'hinge':
            if o.get('r') == 0.01:        # popped: swings out about the top hinge
                o['x'], o['z'] = GATE_X, GATE_Z
                o['angle'] *= 1.6
            else:                          # crease across the skin: the foot folds in
                f = (-1.439 - o['x']) / 1.03
                o['x'] = GATE_X - f * GATE_LEN
                o['z'] = gate_z(o['x'])
                o['angle'] = -abs(o['angle']) * 0.6
        elif o['op'] == 'crumple':
            o['x'], o['len'], o['z'] = GATE_X, GATE_LEN, GATE_Z - 0.1
            o['curl'] *= 0.6
        lg.append(o)
    if lg:
        parts['Liftgate'] = lg
    # ---- the sliding right door gets what the front door gets (named Door_RL / Door_RR here so that the mirror image swaps them; finish() renames Door_RR to Door_SR)
    for src, dst in (('Door_FL', 'Door_RL'), ('Door_FR', 'Door_RR')):
        if parts.get(src):
            parts[dst] = [dict(o, open=o.get('open', 0) * 0.6, sag=o.get('sag', 0) * 0.8) for o in copy.deepcopy(parts[src])]
    # ---- glass panes by place (|y| range): the windscreen, side windows in the body glass; the liftgate window and the sliding door's own nodes
    sp['regions'] = dict(wind=(0.0, 1.1, 0.0, 0.68), opera=(-1.95, 0.0, 0.7, 1.0), rear=(9.0, 9.0, 9.0, 9.0))
    fr = sp.get('fragile')
    if fr:
        g = fr['glass']
        g['Glass_Liftgate'] = g.pop('rear')
        g['Glass_RL'], g['Glass_RR'] = g.get('Glass_FL', 'ok'), g.get('Glass_FR', 'ok')
    return sp


PROFILE = dict(hood_x=HOOD_X, hood_len=HOOD_LEN, trunk_x=GATE_X, trunk_len=GATE_LEN, adapt=adapt)


def finish(spec):
    """after the mirror image: the sliding door's slot Door_RR / Glass_RR become Door_SR / Glass_SR; the van has no left rear door"""
    p = spec.setdefault('parts', {})
    p.pop('Door_RL', None)
    if 'Door_RR' in p:
        p['Door_SR'] = p.pop('Door_RR')
    g = spec.get('fragile', {}).get('glass', {})
    g.pop('Glass_RL', None)
    if 'Glass_RR' in g:
        g['Glass_SR'] = g.pop('Glass_RR')
    return spec
