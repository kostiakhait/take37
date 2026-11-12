// Copyright (C) Konstantin Khait, Squirrel Wisdom Academy, 2026
/**
 * The film set in the game's world: the street of `art/street/street_level.glb`, with the street along +x and the centre line at z = 0 (the model's own y is the world's z).
 * The platform is the flat ground the set stands on: a stadium (a rectangle with round ends) round the street, at one level. The landscape is flat there and rises outside it.
 */
export const PLATFORM = {
  /** the centre line of the stadium: two points on the street axis (x, z) */
  from: [-10, 0] as [number, number],
  to: [610, 0] as [number, number],
  /** the stadium's half width, metres: the ground is flat within this distance of the line */
  halfWidth: 66,
  /** the level of the ground (m): 30 cm under the road, so no vertex of the land reaches the road, and the coplanar depth of the two never fights */
  level: -0.3,
  /** metres over which the land rises from the platform's edge to what the hills say (the edge itself is tangent, no step) */
  rampWidth: 90,
};

/** the street: the extent of the model, metres (street length along x, half width of the buildings and the side streets along z) */
export const STREET = { x0: -40, x1: 640, halfWidth: 50.4, roadLevel: 0 };

/** distance from the platform line (x, z) to the platform's edge: negative inside */
export function platformEdgeDistance(x: number, z: number): number {
  const [ax, az] = PLATFORM.from, [bx, bz] = PLATFORM.to, dx = bx - ax, dz = bz - az, l2 = dx * dx + dz * dz;
  const u = Math.min(1, Math.max(0, ((x - ax) * dx + (z - az) * dz) / l2));
  return Math.hypot(x - (ax + dx * u), z - (az + dz * u)) - PLATFORM.halfWidth;
}
