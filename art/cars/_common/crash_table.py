# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""The damage table: (impact type, degree) -> parameters of crashkit.crash. Data only; the car's own sizes (nose, belt line, hinge...) are measured from the car by crashkit.Car.

Degrees: 1 = lightly dented metal BUT the fragile parts already broken (lamps on the hit side smashed, glass cracked, bumper sagging, grille broken, mirrors/handles/strips loose);
         2 = badly crashed (lamps gone or hanging, bumper hanging, grille torn out, glass mostly out, panels buckled);   3 = wrecked (everything fragile gone, metal mangled).
Types (written for the LEFT side; build(..., side=-1) mirrors):  front, front_corner, rear, rear_corner, side, roll.
Each spec = METAL (crush field, roof, hinge folds, doors, wheels, dents, soot) + EXTRAS (beaten sides, scrapes, far end) + FRAGILE (part-level states, see LADDER/ZONES).
Part states: lamp ok/cracked/broken/hanging/missing; grille ok/cracked/broken/missing; bumper sag/hang/missing (+ end it comes off from); mirror bent/hanging/missing;
handle, trim hanging/missing; plate ok/tilted/hanging; glass ok/cracked/shattered/gone.
Units: metres and degrees, car frame +X forward, +Y left, +Z up. The numbers are the coupe's proportions; other cars keep the schema and change numbers only where the picture asks."""
import copy

PI = 3.14159
HOOD_HINGE = 0.835
TRUNK_HINGE = -1.439


def ridge(theta, c, lam, amp, t=0.0, span=1.2):
    return dict(theta=theta, c=c, lam=lam, amp=amp, t=t, span=span)


def hood_pop(a):
    return dict(op='hinge', x=HOOD_HINGE, alpha=0.0, angle=-a, r=0.01, z=0.98)


def hood_crease(x, a, alpha=0.0, r=0.05):
    return dict(op='hinge', x=x, alpha=alpha, angle=a, r=r, z=0.9)


def trunk_pop(a, x=TRUNK_HINGE):
    return dict(op='hinge', x=x, alpha=PI, angle=-a, r=0.01, z=0.96)


def trunk_crease(x, a, r=0.05):
    return dict(op='hinge', x=x, alpha=PI, angle=-a, r=r, z=0.93)


def scorch(c, r, s, scale=(1, 1, 1)):
    return dict(center=c, r=r, strength=s, scale=scale)


def bowl(c, r, depth, d=(0, 0, -1.0)):
    return dict(center=c, r=r, depth=depth, dir=d)


def door(open_, sag=0, roll=0):
    return dict(op='door', open=open_, sag=sag, roll=roll)


def _pick(a, d):
    return a[d - 1]


# ---- METAL -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def end_row(end, corner, d):
    front = end == 'front'
    amp, lam = _pick([0.06, 0.10, 0.14], d), _pick([0.10, 0.12, 0.14], d)
    if corner:
        t0, w, base, gam = 0.62, 0.45, 0.12, -0.3 - 0.05 * d
    else:
        t0, w, base, gam = 0.15, _pick([0.6, 0.7, 0.85], d), _pick([0.3, 0.4, 0.55], d), 0.1
    rt = 0.6 if corner else 0.3
    rd = [ridge(0.5, 0.55, lam, -amp, rt), ridge(0.5, 0.95, lam, 0.7 * amp, rt), ridge(-0.5 if not corner else -0.45, 0.78, lam, -0.8 * amp, 0.1 if corner else -0.4)]
    if d == 3:
        rd.append(ridge(0.5, 1.4, lam, -0.6 * amp, rt - 0.1))
    crush = dict(end=end, depth=_pick([0.5, 0.95, 1.35], d), length=_pick([1.3, 1.7, 2.0], d), t0=t0, width=w, base=base, zc=0.62, zh=0.5, zbase=0.5, gamma=gam,
                 bend=_pick([0.06, 0.2, 0.35], d), sag=_pick([0.03, 0.07, 0.12], d), rise=_pick([0.04, 0.1, 0.18], d), pinch=_pick([0.05, 0.09, 0.12], d), ridges=rd)
    al = 0.5 if corner else 0.12
    if front:
        lid = {'Hood': [hood_pop(_pick([4, 8, 12], d)), hood_crease(_pick([1.7, 1.55, 1.3], d), _pick([20, 45, 70], d), al, 0.05)] + ([hood_crease(1.75, -62, al - 0.2, 0.06)] if d == 3 else [])}
    else:
        lid = {'Trunk': [trunk_pop(_pick([3, 6, 9], d)), trunk_crease(_pick([-1.95, -1.95, -1.9], d), _pick([20, 45, 70], d), 0.05)] + ([trunk_crease(-2.15, -60, 0.06)] if d == 3 else [])}
    xs = 1 if front else -1
    near, far = ('F', 'R') if front else ('R', 'F')
    wheels = {'%sL' % near: [dict(dx=-xs * 0.03, toe=8, camber=-5, wobble=3), dict(dx=-xs * 0.12, camber=-16, toe=20, wobble=8), 'remove'][d - 1]}
    if d == 3:
        wheels['%sR' % near] = dict(dx=-xs * 0.08, camber=14, toe=-14, wobble=9)
    wheels['%sL' % far] = [dict(toe=2), dict(camber=-4, wobble=2), dict(camber=-9, toe=6, wobble=5)][d - 1]
    row = dict(crush=crush, parts=dict(lid, Door_FL=[door(_pick([3, 10, 30], d), _pick([0.5, 2, 6], d))]), wheels=wheels,
               scorch=[scorch((2.2 * xs, 0.5 if corner else 0.15, 0.7), _pick([0.8, 1.0, 1.3], d), _pick([0.5, 0.65, 0.85], d)), scorch((1.3 * xs, 0.2, 0.9), 0.8, _pick([0.2, 0.45, 0.6], d))])
    if not front and d == 3 and not corner:
        row['roof'] = dict(c=0.10, dish=0.03, push=0.12, ridges=[(-0.9, 0.25, -0.05)])
    return row


def side_row(d):
    amp = _pick([0.05, 0.08, 0.11], d)
    return dict(
        crush=dict(end='left', depth=_pick([0.32, 0.55, 0.8], d), length=_pick([0.6, 0.8, 1.0], d), t0=0.1, width=_pick([0.7, 0.85, 1.0], d), base=0.15, zc=0.65, zh=0.45, zbase=0.35,
                   sag=_pick([0.02, 0.04, 0.06], d), ridges=[ridge(0.0, 0.12, 0.14, -amp, 0.1, 0.9), ridge(0.0, 0.3, 0.12, 0.8 * amp, 0.1, 0.9), ridge(0.0, 0.5, 0.12, -0.6 * amp, 0.1, 0.9)]),
        roof=dict(c=_pick([0.06, 0.14, 0.24], d), lean=_pick([-0.08, -0.15, -0.26], d), dish=_pick([0.03, 0.06, 0.1], d), lean_tw=0.2, pillars=[(1.1, 0.14, _pick([0.03, 0.06, 0.09], d))]),
        parts={'Door_FL': [door(_pick([4, 14, 40], d), _pick([1, 3, 8], d), _pick([0, 2, 6], d))], 'Hood': [hood_pop(_pick([3, 6, 9], d))], 'Trunk': [trunk_pop(_pick([3, 6, 9], d))]},
        wheels={'FL': [dict(dy=-0.03, camber=-4, wobble=2), dict(dy=-0.06, camber=-10, wobble=5), dict(dy=-0.1, camber=-18, toe=8, wobble=8)][d - 1],
                'RL': [dict(dy=-0.02, camber=-3), dict(dy=-0.05, camber=-8, wobble=3), 'remove'][d - 1]},
        scrape=[dict(side=1, z=0.55, h=_pick([0.14, 0.18, 0.22], d), x0=-2.0, x1=1.9, strength=_pick([0.5, 0.65, 0.8], d))],
        scorch=[scorch((0.2, 0.9, 0.7), _pick([0.7, 0.9, 1.1], d), _pick([0.3, 0.45, 0.6], d))],
        bowls=[bowl((0.1, 0.9, 0.7), 0.7, _pick([0.05, 0.1, 0.16], d), (0, -1, 0))])


def roll_row(d):
    r = dict(
        roof=dict(c=_pick([0.28, 0.45, 0.58], d), dish=_pick([0.12, 0.2, 0.26], d), lean=_pick([0.12, 0.2, 0.28], d), lean_tw=0.4, push=_pick([0.08, 0.12, 0.18], d), twist=_pick([0.05, 0.07, 0.1], d),
                  pillars=[(1.05, 0.14, _pick([0.08, 0.12, 0.16], d)), (1.2, 0.1, _pick([0.06, 0.09, 0.12], d)), (0.9, 0.12, _pick([0.04, 0.08, 0.12], d))],
                  ridges=[(-0.35, 0.3, -_pick([0.10, 0.15, 0.2], d)), (0.15, 0.3, _pick([0.08, 0.12, 0.17], d)), (-0.9, 0.3, -_pick([0.07, 0.11, 0.15], d)), (0.55, 0.25, -_pick([0.05, 0.09, 0.13], d))]),
        parts={'Hood': [hood_pop(_pick([6, 12, 16], d)), hood_crease(_pick([1.6, 1.5, 1.4], d), _pick([25, 50, 65], d), 0.1, 0.05)] + ([hood_crease(1.85, -55, -0.1, 0.06)] if d == 3 else []),
               'Trunk': [trunk_pop(_pick([6, 12, 18], d)), trunk_crease(-1.9, _pick([25, 45, 60], d), 0.05)] + ([trunk_crease(-2.15, -50, 0.06)] if d == 3 else []),
               'Door_FL': [door(_pick([8, 38, 0], d), _pick([3, 7, 0], d))], 'Door_FR': [door(_pick([4, 18, 70], d), _pick([1, 4, 10], d), _pick([0, 3, 8], d))]},
        wheels=[{'FL': dict(camber=-10, toe=10, wobble=4), 'RR': dict(camber=9, wobble=4)},
                {'FL': dict(camber=-24, toe=18, wobble=9), 'RR': dict(camber=22, wobble=8), 'FR': dict(camber=-12, wobble=4)},
                {'FL': 'remove', 'RR': dict(camber=30, toe=-20, wobble=12), 'FR': dict(camber=-22, wobble=10), 'RL': dict(camber=18, wobble=6)}][d - 1],
        scrape=[dict(side=1, z=0.5, h=0.2, x0=-2.2, x1=2.0, strength=_pick([0.6, 0.8, 0.95], d)), dict(side=-1, z=0.62, h=0.16, x0=-1.6, x1=1.7, strength=_pick([0.45, 0.65, 0.85], d))],
        bowls=[bowl((0.2, 0.9, 0.75), 0.6, _pick([0.08, 0.14, 0.2], d), (0, -1, 0)), bowl((-1.3, -0.9, 0.75), 0.45, _pick([0.06, 0.1, 0.16], d), (0, 1, 0)),
               bowl((0.0, 0.0, 1.3), 0.7, _pick([0.04, 0.1, 0.16], d), (0, 0, -1)), bowl((1.4, 0.3, 0.95), 0.5, _pick([0.05, 0.1, 0.15], d), (0, 0, -1))],
        scorch=[scorch((0.8, 0.0, 0.95), 1.3, _pick([0.3, 0.45, 0.6], d)), scorch((-1.5, 0.0, 0.9), 0.9, _pick([0.2, 0.35, 0.5], d)), scorch((1.8, 0.0, 0.7), 0.8, _pick([0.2, 0.4, 0.55], d))])
    if d == 3:
        r['remove'] = ['Door_FL']
        r['tears'] = [dict(node='Body', center=(-0.35, 0.0, 1.15), radii=(0.65, 0.42, 0.3), frac=0.5, cells=18)]
    if d == 2:
        r['tears'] = [dict(node='Body', center=(0.0, -0.25, 1.2), radii=(0.4, 0.28, 0.3), frac=0.4, cells=12)]
    return r


# ---- EXTRAS every variant carries: beaten sides, scrapes, soot, far end, so damage reads from every one of the nine views -------------------------------------------------------------------------
BEAT = [((1.0, 0.92, 0.7), (0, -1, 0)), ((-0.3, 0.92, 0.65), (0, -1, 0)), ((-1.8, 0.9, 0.75), (0, -1, 0)), ((1.9, 0.8, 0.7), (0, -1, 0)),
        ((1.0, -0.92, 0.7), (0, 1, 0)), ((-0.4, -0.92, 0.7), (0, 1, 0)), ((-1.8, -0.9, 0.75), (0, 1, 0)), ((1.9, -0.8, 0.7), (0, 1, 0)),
        ((1.5, -0.3, 0.95), (0, 0, -1)), ((1.8, 0.4, 0.95), (0, 0, -1)), ((-2.0, 0.3, 0.95), (0, 0, -1)), ((-1.7, -0.4, 0.95), (0, 0, -1)),
        ((-0.2, 0.2, 1.35), (0, 0, -1)), ((0.2, -0.3, 1.35), (0, 0, -1)), ((-2.55, 0.5, 0.7), (1, 0, 0)), ((2.45, -0.5, 0.7), (-1, 0, 0)),
        ((0.6, 0.3, 0.25), (0, 0, 1)), ((-0.8, -0.3, 0.25), (0, 0, 1)), ((-1.9, 0.2, 0.25), (0, 0, 1)), ((1.6, -0.2, 0.25), (0, 0, 1))]


def extras(kind, d):
    k = 1.7 if kind == 'roll' else 1.0
    ex = dict(bowls=[bowl(c, 0.4, _pick([0.06, 0.1, 0.15], d) * k, dr) for c, dr in BEAT],
              scrape=[dict(side=1, z=0.45, h=0.14, x0=-2.2, x1=2.0, strength=_pick([0.4, 0.55, 0.7], d)), dict(side=-1, z=0.45, h=0.14, x0=-2.2, x1=2.0, strength=_pick([0.4, 0.55, 0.7], d))],
              scorch=[scorch((-1.3, 0.0, 0.5), 1.4, _pick([0.1, 0.16, 0.24], d), (1, 1, 1.6)), scorch((1.3, 0.0, 0.5), 1.4, _pick([0.1, 0.16, 0.24], d), (1, 1, 1.6))],
              parts={})
    if kind in ('front', 'front_corner'):
        ex['parts']['Trunk'] = [trunk_pop(_pick([2, 4, 6], d))]
    if kind in ('rear', 'rear_corner'):
        ex['parts']['Hood'] = [hood_pop(_pick([2, 4, 6], d))]
    return ex


def merge(a, b):
    out = copy.deepcopy(a)
    for k, v in b.items():
        if k == 'parts':
            for n, ops in v.items():
                out.setdefault('parts', {}).setdefault(n, []).extend(copy.deepcopy(ops))
        elif k in ('bowls', 'scrape', 'scorch', 'tears', 'remove', 'hangs'):
            out.setdefault(k, []).extend(copy.deepcopy(v))
        else:
            out.setdefault(k, copy.deepcopy(v))
    return out


# ---- FRAGILE: part-level states per type x degree (written for the left side) --------------------------------------------------------------------------------------------------------------------
LADDER = {
    'lamp': dict(hit=['broken', 'missing', 'missing'], mid=['broken', 'hanging', 'missing'], far=['cracked', 'broken', 'hanging']),
    'grille': dict(hit=['broken', 'missing', 'missing'], mid=['broken', 'broken', 'missing'], far=['cracked', 'broken', 'broken']),
    'bumper': dict(hit=['sag', 'hang', 'missing'], mid=['sag', 'hang', 'hang'], far=['sag', 'sag', 'hang']),
    'mirror': dict(hit=['bent', 'hanging', 'missing'], mid=['bent', 'bent', 'hanging'], far=['bent', 'bent', 'hanging']),
    'handle': dict(hit=['hanging', 'missing', 'missing'], mid=['hanging', 'hanging', 'missing'], far=['hanging', 'hanging', 'missing']),
    'trim': dict(hit=['hanging', 'missing', 'missing'], mid=['hanging', 'hanging', 'missing'], far=['hanging', 'hanging', 'missing']),
    'plate': dict(hit=['tilted', 'hanging', 'hanging'], mid=['tilted', 'tilted', 'hanging'], far=['ok', 'tilted', 'tilted']),
    'glass': dict(hit=['cracked', 'shattered', 'gone'], mid=['cracked', 'shattered', 'gone'], far=['cracked', 'cracked', 'shattered']),
}
ZONES = {
    'front': dict(lamps=dict(front_L='hit', front_R='hit', rear_L='far', rear_R='far'), grille='hit', bumper=dict(F=('hit', -1), R=('far', 1)), mirrors=dict(L='mid', R='mid'),
                  handles=dict(L='mid', R='mid'), trim=dict(L='mid', R='mid'), plate=dict(front='hit', rear='far'), glass=dict(wind='hit', Glass_FL='mid', Glass_FR='mid', opera='mid', rear='far')),
    'front_corner': dict(lamps=dict(front_L='hit', front_R='mid', rear_L='far', rear_R='far'), grille='hit', bumper=dict(F=('hit', -1), R=('far', 1)), mirrors=dict(L='hit', R='mid'),
                         handles=dict(L='hit', R='far'), trim=dict(L='hit', R='far'), plate=dict(front='hit', rear='far'), glass=dict(wind='hit', Glass_FL='hit', Glass_FR='mid', opera='mid', rear='far')),
    'rear': dict(lamps=dict(rear_L='hit', rear_R='hit', front_L='far', front_R='far'), grille='far', bumper=dict(R=('hit', -1), F=('far', 1)), mirrors=dict(L='mid', R='mid'),
                 handles=dict(L='mid', R='mid'), trim=dict(L='mid', R='mid'), plate=dict(rear='hit', front='far'), glass=dict(rear='hit', Glass_FL='mid', Glass_FR='mid', opera='mid', wind='far')),
    'rear_corner': dict(lamps=dict(rear_L='hit', rear_R='mid', front_L='far', front_R='far'), grille='far', bumper=dict(R=('hit', -1), F=('far', 1)), mirrors=dict(L='mid', R='far'),
                        handles=dict(L='hit', R='far'), trim=dict(L='hit', R='far'), plate=dict(rear='hit', front='far'), glass=dict(rear='hit', Glass_FL='mid', Glass_FR='far', opera='hit', wind='far')),
    'side': dict(lamps=dict(front_L='mid', rear_L='mid', front_R='far', rear_R='far'), grille='far', bumper=dict(F=('far', -1), R=('far', 1)), mirrors=dict(L='hit', R='far'),
                 handles=dict(L='hit', R='far'), trim=dict(L='hit', R='far'), plate=dict(front='far', rear='far'), glass=dict(Glass_FL='hit', opera='hit', wind='mid', rear='mid', Glass_FR='far')),
    'roll': dict(lamps=dict(front_L='hit', front_R='hit', rear_L='hit', rear_R='hit'), grille='hit', bumper=dict(F=('hit', -1), R=('hit', 1)), mirrors=dict(L='hit', R='hit'),
                 handles=dict(L='hit', R='hit'), trim=dict(L='hit', R='hit'), plate=dict(front='hit', rear='hit'), glass=dict(wind='hit', rear='hit', opera='hit', Glass_FL='hit', Glass_FR='hit')),
}


def fragile(kind, d):
    z = ZONES[kind]
    L = lambda part, zone: LADDER[part][zone][d - 1]   # noqa: E731
    return dict(lamps={k: L('lamp', v) for k, v in z['lamps'].items()}, grille=L('grille', z['grille']),
                bumper={k: (L('bumper', v[0]), v[1]) for k, v in z['bumper'].items()},
                mirrors={k: L('mirror', v) for k, v in z['mirrors'].items()}, handles={k: L('handle', v) for k, v in z['handles'].items()},
                trim={k: L('trim', v) for k, v in z['trim'].items()}, plate={k: L('plate', v) for k, v in z['plate'].items()},
                glass={k: L('glass', v) for k, v in z['glass'].items()})


def metal(kind, d):
    if kind == 'front':
        return end_row('front', False, d)
    if kind == 'front_corner':
        return end_row('front', True, d)
    if kind == 'rear':
        return end_row('rear', False, d)
    if kind == 'rear_corner':
        return end_row('rear', True, d)
    if kind == 'side':
        return side_row(d)
    return roll_row(d)


KINDS = ('front', 'front_corner', 'rear', 'rear_corner', 'side', 'roll')
TABLE = {(k, d): None for k in KINDS for d in (1, 2, 3)}      # keys only: the rows are generated by build()

_SWAP = {'FL': 'FR', 'FR': 'FL', 'RL': 'RR', 'RR': 'RL', 'Glass_FL': 'Glass_FR', 'Glass_FR': 'Glass_FL', 'Door_FL': 'Door_FR', 'Door_FR': 'Door_FL',
         'Glass_RL': 'Glass_RR', 'Glass_RR': 'Glass_RL', 'Door_RL': 'Door_RR', 'Door_RR': 'Door_RL', 'L': 'R', 'R': 'L', 'front_L': 'front_R', 'front_R': 'front_L', 'rear_L': 'rear_R', 'rear_R': 'rear_L'}


def _mk(k):
    return _SWAP.get(k, k)


def _mop(o):
    o = dict(o)
    if 'from' in o:
        o['from'] = -o['from']
    if o.get('op') == 'hinge':
        o['alpha'] = -o.get('alpha', 0.0)
    for k in ('yaw', 'fold_t'):
        if k in o:
            o[k] = -o[k]
    return o


def mirror(spec):
    """left <-> right: lateral positions, slants and rolls change sign, left/right names swap"""
    sp = copy.deepcopy(spec)
    for ck in ('crush', 'crush2'):
        c = sp.get(ck)
        if not c:
            continue
        if c['end'] in ('front', 'rear'):
            for k in ('t0', 'gamma', 'bend'):
                if k in c:
                    c[k] = -c[k]
            for r in c.get('ridges', []):
                r['theta'], r['t'] = -r['theta'], -r['t']
        else:
            c['end'] = 'right' if c['end'] == 'left' else 'left'
    if sp.get('roof'):
        for k in ('lean', 'twist'):
            if k in sp['roof']:
                sp['roof'][k] = -sp['roof'][k]
    for h in sp.get('hangs', []):
        x, y, z = h['center']
        h['center'] = (x, -y, z)
        for k in ('roll', 'yaw'):
            if k in h:
                h[k] = -h[k]
        if 'move' in h:
            h['move'] = (h['move'][0], -h['move'][1], h['move'][2])
    sp['parts'] = {_mk(k): [_mop(o) for o in v] for k, v in sp.get('parts', {}).items()}
    sp['wheels'] = {_mk(k): (dict(v, toe=-v.get('toe', 0.0), camber=-v.get('camber', 0.0), dy=-v.get('dy', 0.0)) if isinstance(v, dict) else v) for k, v in sp.get('wheels', {}).items()}
    sp['glass'] = {_mk(k): v for k, v in sp.get('glass', {}).items()}
    sp['remove'] = [_mk(k) for k in sp.get('remove', [])]
    for sc in sp.get('scorch', []):
        x, y, z = sc['center']
        sc['center'] = (x, -y, z)
    for sc in sp.get('scrape', []):
        sc['side'] = -sc['side']
    for b in sp.get('bowls', []):
        x, y, z = b['center']
        b['center'] = (x, -y, z)
        dx, dy, dz = b.get('dir', (0, 0, -1))
        b['dir'] = (dx, -dy, dz)
    for t in sp.get('tears', []):
        x, y, z = t['center']
        t['center'] = (x, -y, z)
    fr = sp.get('fragile')
    if fr:
        fr['lamps'] = {_mk(k): v for k, v in fr['lamps'].items()}
        for k in ('mirrors', 'handles', 'trim'):
            fr[k] = {_mk(a): b for a, b in fr[k].items()}
        fr['bumper'] = {k: (v[0], -v[1]) for k, v in fr['bumper'].items()}
        fr['glass'] = {_mk(k): v for k, v in fr['glass'].items()}
    return sp


def build(kind, degree, side=1):
    """the spec of crashkit.crash for a type and a degree: metal + extras + fragile states (side -1 = the mirror image of the left-hand row)"""
    spec = merge(metal(kind, degree), extras(kind, degree))
    spec['fragile'] = fragile(kind, degree)
    spec['seed'] = 7 + degree * 3
    return mirror(spec) if side < 0 else spec
