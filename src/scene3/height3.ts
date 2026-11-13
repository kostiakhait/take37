// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
// The Zeppelin sample's `height` module in this scene's local frame (x east of the airfield's centre, z south): the farmland and the forest of the zone, and the ground the landscape of this scene builds.
import * as Z from '@zeppelin/height';
import { SITE, FIELD } from './config';
import { groundOf } from './ground3';

export const hash2 = Z.hash2, noise2 = Z.noise2, fbm = Z.fbm;
const fieldDist = (x: number, z: number) => { const [ax, az] = FIELD.from, [bx, bz] = FIELD.to, dz = bz - az, t = Math.min(1, Math.max(0, (z - az) / dz)); return Math.hypot(x - ax - (bx - ax) * t, z - az - dz * t); };
const keep = (d: number, a: number, b: number) => Math.min(1, Math.max(0, (d - a) / (b - a)));
export const groundHeight = (x: number, z: number) => groundOf()(x, z);
/** how much of the ground is farmland / wood (the zone's rules), with the airfield and its surround kept clear of both */
export const farmAmount = (x: number, z: number) => Z.farmAmount(x + SITE.x, z + SITE.z) * keep(fieldDist(x, z), FIELD.inner + 40, FIELD.inner + 140);
export const forestAmount = (x: number, z: number) => Z.forestAmount(x + SITE.x, z + SITE.z) * keep(fieldDist(x, z), FIELD.inner + 60, FIELD.inner + 400);
/** the zone's water as local discs: centre, nominal radius, level */
export const lakesLocal = () => Z.LAKES.map(l => ({ x: l.x - SITE.x, z: l.z - SITE.z, r: l.r, level: l.level }));
/** the shapes the zone's own forest module asks of its height module (it is built against this file): the airfield of this scene (the forest keeps 1.1 km clear of it), its lakes, the hash */
export const AIRFIELD = { x: 40, z: 0, elevation: Z.AIRFIELD.elevation, heading: Z.AIRFIELD.heading };
export const LAKES = lakesLocal();
