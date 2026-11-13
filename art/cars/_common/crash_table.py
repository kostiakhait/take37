# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""The damage table: (impact type, degree) -> parameters of crashkit.crash. Pure data; per-car sizes (nose, belt line, hinge...) are measured from the car by crashkit.Car.

Degrees: 1 = slightly dented (the existing *_damaged.glb of each car is degree 1 of the FRONT type), 2 = badly crashed (clearly folded, parts hanging),
         3 = completely wrecked (everything open, glass gone, parts missing, black with soot).
Types (rows; every row is written for the LEFT side, build(..., side=-1) gives the mirror image):
  front         head-on, a little left of the middle           front_corner  offset hit on the front corner (left; right = mirror)
  rear          from behind, a little left of the middle       rear_corner   offset hit on the rear corner (left; right = mirror)
  side          broadside into the door (left; right = mirror)  roll          rollover: crushed roof, scraped sides (the game lays the model on its roof or side)
Units: metres and degrees, car frame +X forward, +Y left, +Z up. Hinge ops: + angle = the part ahead of the crease turns nose down. The numbers are the coupe's proportions
(nose 2.50, tail -2.61, belt 0.92, roof 1.37, door hinge 0.84); for another car the shared schema is kept and only the numbers that the picture asks for change."""
import copy

HOOD_HINGE = 0.835
TRUNK_HINGE = -1.439
PI = 3.14159


def ridge(theta, c, lam, amp, t=0.0, span=1.2):
    return dict(theta=theta, c=c, lam=lam, amp=amp, t=t, span=span)


def hood_pop(a):
    return dict(op='hinge', x=HOOD_HINGE, alpha=0.0, angle=-a, r=0.01, z=0.98)


def hood_crease(x, a, alpha=0.0, r=0.05):
    return dict(op='hinge', x=x, alpha=alpha, angle=a, r=r, z=0.9)


def trunk_pop(a, x=TRUNK_HINGE):
    """the lid is hinged at its front edge and rises at the back: a crease whose far side is the rear (alpha pi); + a = the rear edge up"""
    return dict(op='hinge', x=x, alpha=PI, angle=-a, r=0.01, z=0.96)


def trunk_crease(x, a, r=0.05):
    return dict(op='hinge', x=x, alpha=PI, angle=-a, r=r, z=0.93)


def bumper(end, roll, yaw, fold, fold_t, fold_w=0.45, fold_z=0.05, bow=0.03, drop=0.0):
    return dict(op='hang_bumper', **{'from': end}, roll=roll, yaw=yaw, bow=bow, fold=fold, fold_t=fold_t, fold_w=fold_w, fold_z=fold_z, drop=drop)


def scorch(c, r, s, scale=(1, 1, 1)):
    return dict(center=c, r=r, strength=s, scale=scale)


F = 2.4      # x of the front lamps and plate, R: the rear ones
R = -2.5

TABLE = {
    # ---- FRONT -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    ('front', 2): dict(
        crush=dict(end='front', depth=0.8, length=1.6, t0=0.15, width=0.6, base=0.3, zc=0.62, zh=0.45, zbase=0.45, gamma=0.1, bend=0.10, sag=0.05, rise=0.05, pinch=0.08,
                   ridges=[ridge(0.5, 0.65, 0.10, -0.05, 0.3), ridge(0.5, 0.95, 0.10, 0.04, 0.3), ridge(-0.5, 0.75, 0.10, -0.04, -0.4)]),
        parts={'Hood': [hood_pop(10), hood_crease(1.55, 32, 0.15, 0.05)], 'Bumper_F': [bumper(-1, 9, 4, 0.22, 0.62, drop=-0.30)]},
        hangs=[dict(center=(F, 0.7, 0.72), r=0.3, roll=-18, move=(0.0, 0.0, -0.10))],
        wheels={'FL': dict(dx=-0.05, camber=-7, toe=14, wobble=4)}, glass={'wind': 0.4},
        scorch=[scorch((2.2, 0.3, 0.7), 0.9, 0.5)],
    ),
    ('front', 3): dict(
        crush=dict(end='front', depth=1.15, length=1.9, t0=0.1, width=0.85, base=0.55, zc=0.62, zh=0.55, zbase=0.55, gamma=0.1, bend=0.30, sag=0.12, rise=0.18, pinch=0.12,
                   ridges=[ridge(0.5, 0.55, 0.14, -0.08, 0.3), ridge(0.5, 0.95, 0.14, 0.07, 0.3), ridge(-0.5, 0.75, 0.14, -0.07, -0.4), ridge(0.5, 1.35, 0.14, -0.06, 0.2)]),
        parts={'Hood': [hood_pop(26), hood_crease(1.3, 70, 0.12, 0.06), hood_crease(1.75, -62, -0.1, 0.06)], 'Bumper_F': [bumper(-1, 38, 10, 0.4, 0.1, 0.5, 0.08, 0.06)],
               'Door_FL': [dict(op='door', open=26, sag=5)]},
        hangs=[dict(center=(F, 0.7, 0.72), r=0.3, roll=-35, move=(0.12, 0.0, -0.22)), dict(center=(F, -0.7, 0.72), r=0.3, roll=22, move=(0.0, 0.0, -0.12))],
        wheels={'FL': 'remove', 'FR': dict(dx=-0.1, camber=10, toe=-18, wobble=8)}, glass={'wind': 1.0, 'Glass_FL': 0.7},
        scorch=[scorch((2.1, 0.0, 0.75), 1.1, 0.75), scorch((1.3, 0.0, 0.9), 0.8, 0.6)],
    ),
    # ---- FRONT CORNER (left): the nose slants away, the left fender peels, the left wheel is shoved back -----------------------------------------------------------------------------
    ('front_corner', 1): dict(
        crush=dict(end='front', depth=0.30, length=1.2, t0=0.62, width=0.42, base=0.10, zc=0.62, zh=0.4, zbase=0.45, gamma=-0.3, bend=0.06, sag=0.02, rise=0.03, pinch=0.04,
                   ridges=[ridge(0.5, 0.5, 0.10, -0.04, 0.6)]),
        parts={'Hood': [hood_pop(4), hood_crease(1.7, 14, 0.5, 0.05)], 'Bumper_F': [bumper(-1, 4, 3, 0.0, 0.0, bow=0.01)]},
        wheels={'FL': dict(dx=-0.03, toe=6)}, glass={'wind': 0.2}, scorch=[scorch((2.2, 0.7, 0.7), 0.5, 0.35)],
    ),
    ('front_corner', 2): dict(
        crush=dict(end='front', depth=0.75, length=1.5, t0=0.62, width=0.45, base=0.12, zc=0.62, zh=0.45, zbase=0.45, gamma=-0.35, bend=0.18, sag=0.06, rise=0.08, pinch=0.06,
                   ridges=[ridge(0.5, 0.55, 0.12, -0.06, 0.6), ridge(0.5, 1.0, 0.12, 0.05, 0.6), ridge(-0.45, 0.8, 0.12, -0.05, 0.2)]),
        parts={'Hood': [hood_pop(12), hood_crease(1.5, 36, 0.5, 0.05)], 'Bumper_F': [bumper(-1, 12, 8, 0.2, 0.5, 0.4)], 'Door_FL': [dict(op='door', open=7, sag=1)]},
        hangs=[dict(center=(F, 0.7, 0.72), r=0.3, roll=-25, move=(0.1, 0.0, -0.16))],
        wheels={'FL': dict(dx=-0.18, dy=-0.04, camber=-12, toe=22, wobble=6)}, glass={'wind': 0.5, 'Glass_FL': 0.3}, scorch=[scorch((2.0, 0.65, 0.7), 0.8, 0.6)],
    ),
    ('front_corner', 3): dict(
        crush=dict(end='front', depth=1.2, length=1.9, t0=0.6, width=0.55, base=0.2, zc=0.62, zh=0.55, zbase=0.5, gamma=-0.4, bend=0.35, sag=0.12, rise=0.16, pinch=0.1,
                   ridges=[ridge(0.5, 0.55, 0.14, -0.08, 0.6), ridge(0.5, 1.05, 0.14, 0.07, 0.6), ridge(-0.5, 0.8, 0.14, -0.07, 0.2), ridge(0.5, 1.5, 0.14, -0.06, 0.5)]),
        parts={'Hood': [hood_pop(30), hood_crease(1.35, 62, 0.5, 0.06), hood_crease(1.8, -58, 0.45, 0.06)], 'Bumper_F': [bumper(-1, 34, 14, 0.35, 0.5, 0.5, 0.08, 0.06)],
               'Door_FL': [dict(op='door', open=34, sag=6)]},
        hangs=[dict(center=(F, 0.7, 0.72), r=0.3, roll=-40, move=(0.2, 0.0, -0.3)), dict(center=(F, -0.7, 0.72), r=0.3, roll=15, move=(0.0, 0.0, -0.06))],
        wheels={'FL': 'remove', 'FR': dict(dx=-0.06, camber=6, toe=-10, wobble=5)}, glass={'wind': 1.0, 'Glass_FL': 0.8},
        scorch=[scorch((2.0, 0.6, 0.75), 1.0, 0.8), scorch((1.3, 0.3, 0.9), 0.8, 0.55)],
    ),
    # ---- REAR --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    ('rear', 1): dict(
        crush=dict(end='rear', depth=0.30, length=1.2, t0=0.15, width=0.6, base=0.3, zc=0.62, zh=0.4, zbase=0.45, gamma=0.05, bend=0.04, sag=0.03, rise=0.04, pinch=0.04,
                   ridges=[ridge(0.4, 0.5, 0.10, -0.04, 0.3)]),
        parts={'Trunk': [trunk_pop(6)], 'Bumper_R': [bumper(-1, 4, 3, 0.0, 0.0, bow=0.01)]},
        glass={'rear': 0.2}, scorch=[scorch((-2.3, 0.2, 0.7), 0.6, 0.3)],
    ),
    ('rear', 2): dict(
        crush=dict(end='rear', depth=0.75, length=1.5, t0=0.15, width=0.65, base=0.3, zc=0.65, zh=0.45, zbase=0.45, gamma=0.1, bend=0.10, sag=0.06, rise=0.12, pinch=0.08,
                   ridges=[ridge(0.5, 0.55, 0.11, -0.06, 0.3), ridge(0.5, 0.95, 0.11, 0.05, 0.3), ridge(-0.5, 0.75, 0.11, -0.05, -0.4)]),
        parts={'Trunk': [trunk_pop(18), trunk_crease(-1.95, 40, 0.05)], 'Bumper_R': [bumper(-1, 10, 4, 0.2, 0.25)]},
        hangs=[dict(center=(R, 0.7, 0.8), r=0.3, roll=-20, move=(-0.1, 0.0, -0.12))],
        wheels={'RL': dict(dx=0.05, camber=-7, toe=10, wobble=4)}, glass={'rear': 0.5}, scorch=[scorch((-2.2, 0.2, 0.7), 0.9, 0.5)],
    ),
    ('rear', 3): dict(
        crush=dict(end='rear', depth=1.2, length=1.9, t0=0.1, width=0.85, base=0.5, zc=0.65, zh=0.55, zbase=0.55, gamma=0.1, bend=0.28, sag=0.12, rise=0.2, pinch=0.12,
                   ridges=[ridge(0.5, 0.55, 0.14, -0.08, 0.3), ridge(0.5, 0.95, 0.14, 0.07, 0.3), ridge(-0.5, 0.75, 0.14, -0.07, -0.4), ridge(0.5, 1.35, 0.14, -0.06, 0.2)]),
        parts={'Trunk': [trunk_pop(34), trunk_crease(-1.9, 70, 0.06), trunk_crease(-2.15, -60, 0.06)], 'Bumper_R': [bumper(-1, 38, 10, 0.4, 0.1, 0.5, 0.08, 0.06)]},
        hangs=[dict(center=(R, 0.7, 0.8), r=0.3, roll=-35, move=(-0.12, 0.0, -0.22)), dict(center=(R, -0.7, 0.8), r=0.3, roll=20, move=(0.0, 0.0, -0.1))],
        wheels={'RL': 'remove', 'RR': dict(dx=0.1, camber=10, toe=-14, wobble=8)}, glass={'rear': 1.0, 'opera': 0.6},
        roof=dict(c=0.10, dish=0.03, push=0.12, ridges=[(-0.9, 0.25, -0.05)]), scorch=[scorch((-2.1, 0.0, 0.8), 1.2, 0.75)],
    ),
    # ---- REAR CORNER (left) -------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    ('rear_corner', 1): dict(
        crush=dict(end='rear', depth=0.30, length=1.2, t0=0.62, width=0.42, base=0.10, zc=0.62, zh=0.4, zbase=0.45, gamma=-0.3, bend=0.06, sag=0.02, rise=0.03, pinch=0.04,
                   ridges=[ridge(0.5, 0.5, 0.10, -0.04, 0.6)]),
        parts={'Trunk': [trunk_pop(4)], 'Bumper_R': [bumper(-1, 4, 3, 0.0, 0.0, bow=0.01)]}, wheels={'RL': dict(toe=4)}, scorch=[scorch((-2.3, 0.7, 0.7), 0.5, 0.3)],
    ),
    ('rear_corner', 2): dict(
        crush=dict(end='rear', depth=0.75, length=1.5, t0=0.62, width=0.45, base=0.12, zc=0.62, zh=0.45, zbase=0.45, gamma=-0.35, bend=0.18, sag=0.06, rise=0.08, pinch=0.06,
                   ridges=[ridge(0.5, 0.55, 0.12, -0.06, 0.6), ridge(0.5, 1.0, 0.12, 0.05, 0.6), ridge(-0.45, 0.8, 0.12, -0.05, 0.2)]),
        parts={'Trunk': [trunk_pop(14), trunk_crease(-1.9, 34, 0.05)], 'Bumper_R': [bumper(-1, 12, 8, 0.2, 0.5, 0.4)]},
        hangs=[dict(center=(R, 0.7, 0.8), r=0.3, roll=-25, move=(-0.1, 0.0, -0.16))],
        wheels={'RL': dict(dx=0.15, camber=-12, toe=18, wobble=6)}, glass={'rear': 0.4}, scorch=[scorch((-2.1, 0.65, 0.7), 0.8, 0.55)],
    ),
    ('rear_corner', 3): dict(
        crush=dict(end='rear', depth=1.2, length=1.9, t0=0.6, width=0.55, base=0.2, zc=0.62, zh=0.55, zbase=0.5, gamma=-0.4, bend=0.35, sag=0.12, rise=0.16, pinch=0.1,
                   ridges=[ridge(0.5, 0.55, 0.14, -0.08, 0.6), ridge(0.5, 1.05, 0.14, 0.07, 0.6), ridge(-0.5, 0.8, 0.14, -0.07, 0.2), ridge(0.5, 1.5, 0.14, -0.06, 0.5)]),
        parts={'Trunk': [trunk_pop(32), trunk_crease(-1.85, 60, 0.06), trunk_crease(-2.15, -55, 0.06)], 'Bumper_R': [bumper(-1, 34, 14, 0.35, 0.5, 0.5, 0.08, 0.06)],
               'Door_FL': [dict(op='door', open=18, sag=3)]},
        hangs=[dict(center=(R, 0.7, 0.8), r=0.3, roll=-40, move=(-0.2, 0.0, -0.3)), dict(center=(R, -0.7, 0.8), r=0.3, roll=15, move=(0.0, 0.0, -0.06))],
        wheels={'RL': 'remove', 'RR': dict(dx=0.05, camber=6, toe=-10, wobble=5)}, glass={'rear': 1.0, 'opera': 1.0}, scorch=[scorch((-2.0, 0.6, 0.75), 1.0, 0.8)],
    ),
    # ---- SIDE (left): a broadside into the door; the door and the wing are pushed in, the roof leans over ----------------------------------------------------------------------------------
    ('side', 1): dict(
        crush=dict(end='left', depth=0.26, length=0.6, t0=0.15, width=0.6, base=0.1, zc=0.65, zh=0.38, zbase=0.3, ridges=[ridge(0.0, 0.1, 0.12, -0.03, 0.15, 0.7)]),
        parts={'Door_FL': [dict(op='door', open=2.5, sag=0.5)]}, glass={'Glass_FL': 0.3}, scrape=[dict(side=1, z=0.55, h=0.12, x0=-0.7, x1=1.0, strength=0.4)],
    ),
    ('side', 2): dict(
        crush=dict(end='left', depth=0.40, length=0.7, t0=0.15, width=0.75, base=0.15, zc=0.65, zh=0.4, zbase=0.3, sag=0.03,
                   ridges=[ridge(0.0, 0.12, 0.14, -0.05, 0.15, 0.8), ridge(0.0, 0.28, 0.12, 0.04, 0.15, 0.8)]),
        roof=dict(c=0.05, lean=-0.10, dish=0.03), parts={'Door_FL': [dict(op='door', open=9, sag=2)]}, glass={'Glass_FL': 1.0, 'opera': 0.7},
        wheels={'FL': dict(dy=-0.05, camber=-8, wobble=4), 'RL': dict(dy=-0.05, camber=-5)},
        scrape=[dict(side=1, z=0.55, h=0.16, x0=-1.2, x1=1.4, strength=0.55)], scorch=[scorch((0.2, 0.9, 0.7), 0.7, 0.3)],
    ),
    ('side', 3): dict(
        crush=dict(end='left', depth=0.62, length=0.85, t0=0.1, width=0.95, base=0.2, zc=0.7, zh=0.5, zbase=0.35, sag=0.06,
                   ridges=[ridge(0.0, 0.12, 0.16, -0.07, 0.1, 0.9), ridge(0.0, 0.3, 0.14, 0.06, 0.1, 0.9)]),
        roof=dict(c=0.12, lean=-0.22, dish=0.05, lean_tw=0.2, pillars=[(1.1, 0.14, 0.06)]),
        parts={'Door_FL': [dict(op='door', open=36, sag=8, roll=4)]}, glass={'Glass_FL': 1.0, 'opera': 1.0, 'wind': 0.7},
        wheels={'FL': dict(dy=-0.1, camber=-14, toe=6, wobble=7), 'RL': 'remove'},
        scrape=[dict(side=1, z=0.55, h=0.2, x0=-2.0, x1=1.9, strength=0.7)], scorch=[scorch((0.2, 0.9, 0.7), 1.0, 0.6)],
        bowls=[dict(center=(0.1, 0.9, 0.7), r=0.7, depth=0.14, dir=(0, -1, 0))],
    ),
    # ---- ROLLOVER: the car in its own frame with the roof crushed; the game lays it on its roof or side ------------------------------------------------------------------------------------------
    ('roll', 1): dict(
        roof=dict(c=0.12, dish=0.05, lean=0.05, lean_tw=0.3, pillars=[(1.1, 0.12, 0.03)], ridges=[(-0.2, 0.3, -0.03)]),
        parts={'Hood': [hood_pop(4)]}, glass={'wind': 0.35},
        scrape=[dict(side=1, z=0.55, h=0.12, x0=-1.8, x1=1.6, strength=0.55)],
        bowls=[dict(center=(0.3, 0.9, 0.75), r=0.45, depth=0.05, dir=(0, -1, 0))],
    ),
    ('roll', 2): dict(
        roof=dict(c=0.30, dish=0.12, lean=0.16, lean_tw=0.4, push=0.08, twist=0.04, pillars=[(1.05, 0.14, 0.06), (1.2, 0.1, 0.05)], ridges=[(-0.35, 0.3, -0.06), (0.15, 0.3, 0.05)]),
        parts={'Hood': [hood_pop(14), hood_crease(1.6, 25, 0.1, 0.05)], 'Trunk': [trunk_pop(14)], 'Door_FL': [dict(op='door', open=16, sag=3)]},
        wheels={'FL': dict(camber=-9, toe=8, wobble=5), 'RR': dict(camber=8, wobble=4)},
        glass={'wind': 1.0, 'rear': 0.7, 'opera': 1.0, 'Glass_FL': 1.0, 'Glass_FR': 0.5},
        scrape=[dict(side=1, z=0.5, h=0.18, x0=-2.0, x1=1.9, strength=0.7), dict(side=-1, z=0.65, h=0.12, x0=-1.0, x1=1.2, strength=0.5)],
        bowls=[dict(center=(0.2, 0.9, 0.75), r=0.6, depth=0.10, dir=(0, -1, 0)), dict(center=(-1.3, -0.9, 0.75), r=0.4, depth=0.07, dir=(0, 1, 0))],
        scorch=[scorch((0.2, 0.0, 1.0), 0.8, 0.25)],
    ),
    ('roll', 3): dict(
        roof=dict(c=0.34, dish=0.0, lean=0.26, lean_tw=0.5, push=0.15, twist=0.08, pillars=[(1.0, 0.14, 0.10), (1.15, 0.12, 0.08), (1.25, 0.1, 0.06)],
                  ridges=[(-0.5, 0.3, -0.09), (-0.1, 0.3, 0.07), (0.35, 0.3, -0.07)]),
        parts={'Hood': [hood_pop(16), hood_crease(1.45, 40, 0.12, 0.06)], 'Trunk': [trunk_pop(30)], 'Door_FR': [dict(op='door', open=62, sag=8, roll=6)]},
        remove=['Door_FL'],
        wheels={'FL': 'remove', 'RR': dict(camber=14, toe=-10, wobble=9), 'FR': dict(camber=-12, wobble=6)},
        glass={'wind': 1.0, 'rear': 1.0, 'opera': 1.0, 'Glass_FR': 1.0},
        scrape=[dict(side=1, z=0.45, h=0.22, x0=-2.2, x1=2.0, strength=0.85), dict(side=-1, z=0.6, h=0.16, x0=-1.5, x1=1.6, strength=0.65)],
        bowls=[dict(center=(0.1, 0.9, 0.7), r=0.8, depth=0.16, dir=(0, -1, 0)), dict(center=(-1.2, -0.9, 0.75), r=0.5, depth=0.10, dir=(0, 1, 0))],
        scorch=[scorch((0.8, 0.0, 0.95), 1.3, 0.55), scorch((-1.5, 0.0, 0.9), 0.9, 0.35)],
    ),
}

_SWAP = {'FL': 'FR', 'FR': 'FL', 'RL': 'RR', 'RR': 'RL', 'Glass_FL': 'Glass_FR', 'Glass_FR': 'Glass_FL', 'Door_FL': 'Door_FR', 'Door_FR': 'Door_FL',
         'Glass_RL': 'Glass_RR', 'Glass_RR': 'Glass_RL', 'Door_RL': 'Door_RR', 'Door_RR': 'Door_RL'}


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
    return sp


def build(kind, degree, side=1):
    """the spec of crashkit.crash for a type and a degree (a deep copy; side -1 = the mirror image of the table row, which is written for the left side)"""
    spec = copy.deepcopy(TABLE[(kind, degree)])
    spec['seed'] = 7 + degree * 3
    return mirror(spec) if side < 0 else spec
