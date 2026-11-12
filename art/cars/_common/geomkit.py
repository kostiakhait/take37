# Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
"""The shape of a car read off a side-view drawing (pure python; imported inside Blender by cargen.py).

A car's geometry module builds Geom(**spec). The drawing gives the shape; the listed sizes give the scale (see each car's SOURCES.md):
  X: the axle columns (ax_r, ax_f) are put at the listed wheelbase, the overhangs (px_rbump -> ax_r, ax_f -> px_fbump) scaled together to the listed overall length;
  Z: ground row and roof row are put at the listed height;
  Y: the listed width; the body's half width at the shoulder is W.
"""
import math


def interp(pts, x):
    if x <= pts[0][0]:
        return pts[0][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x <= x1:
            t = (x - x0) / (x1 - x0) if x1 > x0 else 0.0
            return y0 + (y1 - y0) * t
    return pts[-1][1]


def smooth(pts, x, h=0.05):
    n = 6
    return sum(interp(pts, x + h * (2 * k / n - 1)) for k in range(n + 1)) / (n + 1)


class Geom:
    def __init__(self, **s):
        self.__dict__.update(s)
        d = self.__dict__
        self.HWB = self.WHEELBASE / 2
        self.K_WB = (self.ax_f - self.ax_r) / self.WHEELBASE
        self.K_OH = ((self.ax_r - self.px_rbump) + (self.px_fbump - self.ax_f)) / (self.LENGTH - self.WHEELBASE)
        self.K_Z = (self.row_ground - self.row_roof) / self.HEIGHT
        self.W = self.WIDTH / 2
        self.ZC = self.R_TYRE
        d.setdefault('X_HUMP', (1.0, 0.0))
        d.setdefault('CAB_Y', self.W - 0.15)
        d.setdefault('HUMP_Y', self.W - 0.38)
        d.setdefault('CAB_FLOOR', 0.36)
        d.setdefault('ROUND_TAIL', 0.07)
        d.setdefault('ROUND_NOSE', 0.11)
        d.setdefault('SHELL', 0.035)
        self.TOP = [(self.X(a), self.Z(b)) for a, b in self.top_px]
        self.BOTTOM = [(self.X(a), self.Z(b)) for a, b in self.bottom_px]
        self.X_TAIL, self.X_NOSE = self.X(self.px_tail), self.X(self.px_nose)
        self.X_RBUMP, self.X_FBUMP = self.X(self.px_rbump), self.X(self.px_fbump)
        self.X_BACKLIGHT_BASE, self.X_C_PILLAR = self.X(self.col_backlight_base), self.X(self.col_c_pillar)
        self.X_COWL = self.X(self.col_cowl)
        self.Z_ROOF = self.Z(self.row_roof)
        self.Z_BELT = self.Z(self.row_belt)
        self.Z_CREASE_REAR, self.Z_CREASE_FRONT = self.Z(self.row_crease_rear), self.Z(self.row_crease_front)
        self.GH_Z_ROOF_EDGE = self.Z(self.row_roof_edge)
        self.GH_Y_BELT = self.W - self.tumble_in
        self.GH_Y_ROOF = self.gh_y_roof
        self.Y_EDGE = self.GH_Y_BELT + 0.004
        d.setdefault('X_GH0', self.X_BACKLIGHT_BASE - 0.03)
        d.setdefault('CABIN_X0', self.X_BACKLIGHT_BASE + 0.10)
        d.setdefault('CABIN_X1', self.X_COWL - 0.03)
        d.setdefault('WINDOW_SIDES', {})
        d.setdefault('WINDOW_OWNER', {})
        d.setdefault('ARCH_Y', self.W - 0.32)
        d.setdefault('ARCH_GAP', 0.045)
        d.setdefault('WINDOW_TRIM', 'black')
        d.setdefault('REVEAL', 'black')
        d.setdefault('HANDLE_KIND', 'black')
        d.setdefault('ENGINE_X', self.X_NOSE - 0.6)
        d.setdefault('DRIVE', 'fwd')
        d.setdefault('LUGS', 5)
        d.setdefault('PCD', 0.0572)
        d.setdefault('WHEEL_STYLE', 'cover')
        d.setdefault('SHIFTER', 'console')
        d.setdefault('CARGO', None)
        d.setdefault('CAVITIES', [])
        d.setdefault('PANELS', [])
        d.setdefault('SIDE_STRIPS', [])
        d.setdefault('TRIM_X0', self.X_TAIL + 0.5)
        d.setdefault('TRIM_X1', self.X_COWL)

    def X(self, px):
        if px < self.ax_r:
            return -self.HWB - (self.ax_r - px) / self.K_OH
        if px > self.ax_f:
            return self.HWB + (px - self.ax_f) / self.K_OH
        return (px - (self.ax_r + self.ax_f) / 2) / self.K_WB

    def Z(self, py):
        return (self.row_ground - py) / self.K_Z

    def gh_side_y(self, z):
        t = (z - self.Z_BELT) / (self.GH_Z_ROOF_EDGE - self.Z_BELT)
        return self.GH_Y_BELT + (self.GH_Y_ROOF - self.GH_Y_BELT) * t

    def top_z(self, x):
        if self.X_C_PILLAR <= x < self.X_COWL:
            return self.Z_BELT
        if self.X_BACKLIGHT_BASE < x < self.X_C_PILLAR:
            zd = smooth(self.TOP, self.X_BACKLIGHT_BASE, 0.03)
            t = (x - self.X_BACKLIGHT_BASE) / (self.X_C_PILLAR - self.X_BACKLIGHT_BASE)
            t = t * t * (3 - 2 * t)
            return zd + (self.Z_BELT - zd) * t
        return smooth(self.TOP, x, 0.03)

    def roof_z(self, x):
        return smooth(self.TOP, x, 0.025)

    def crease_z(self, x):
        if x <= self.X_COWL:
            return self.Z_CREASE_REAR
        t = (x - self.X_COWL) / (self.X_NOSE - self.X_COWL)
        return self.Z_CREASE_REAR + (self.Z_CREASE_FRONT - self.Z_CREASE_REAR) * t

    def bottom_z(self, x):
        return smooth(self.BOTTOM, x, 0.08)

    def plan_half_width(self, x, w=None):
        w = self.W if w is None else w
        for xe, r, s in ((self.X_TAIL, self.ROUND_TAIL, 1), (self.X_NOSE, self.ROUND_NOSE, -1)):
            d = (x - xe) * s
            if d < r:
                d = max(d, 0.0)
                return w - r + math.sqrt(max(r * r - (r - d) ** 2, 0.0))
        return w
