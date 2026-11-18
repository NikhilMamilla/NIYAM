// Camera framing maths, independent of three.js so it can be unit-tested. World units are metres.

export type Vec3 = [number, number, number];

export interface Box {
  min: Vec3;
  max: Vec3;
}

export interface Framing {
  target: Vec3;
  position: Vec3;
  distance: number;
  radius: number;
  near: number;
  far: number;
  minDistance: number;
  maxDistance: number;
}

/** Front-left, from above: rows of elements do not hide each other. */
export const ISO_DIRECTION: Vec3 = [-0.42, 0.52, 0.74];
export const PLAN_DIRECTION: Vec3 = [0, 1, 0.0001];
export const FRONT_DIRECTION: Vec3 = [0, 0.12, 1];

const sub = (a: Vec3, b: Vec3): Vec3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const dot = (a: Vec3, b: Vec3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a: Vec3, b: Vec3): Vec3 => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const unit = (a: Vec3): Vec3 => {
  const l = Math.hypot(...a) || 1;
  return [a[0] / l, a[1] / l, a[2] / l];
};

/**
 * Where to put a perspective camera (y up) so the whole box is visible, and depth limits that suit the box's size.
 * Exact fit: the distance is the smallest that keeps each of the 8 corners inside both field-of-view angles.
 */
export function frameBox(box: Box, opts: { fovDeg: number; aspect: number; direction: Vec3; padding?: number }): Framing {
  const target: Vec3 = [0, 1, 2].map((i) => (box.min[i]! + box.max[i]!) / 2) as Vec3;
  const radius = Math.max(0.25, Math.hypot(...sub(box.max, box.min)) / 2);
  const tanV = Math.tan((opts.fovDeg * Math.PI) / 360);
  const tanH = tanV * opts.aspect;
  const pad = opts.padding ?? 1.08;
  const back = unit(opts.direction); // from the target towards the camera
  const side = cross([0, 1, 0], back);
  const right = unit(Math.hypot(...side) > 1e-9 ? side : [1, 0, 0]); // looking straight down: any horizontal axis
  const up = cross(back, right);
  const corners: Vec3[] = [];
  for (const x of [box.min[0], box.max[0]]) for (const y of [box.min[1], box.max[1]]) for (const z of [box.min[2], box.max[2]]) {
    corners.push(sub([x, y, z], target));
  }
  let distance = radius * 0.5;
  for (const c of corners) {
    const along = dot(c, back); // towards the camera
    distance = Math.max(distance, along + (Math.abs(dot(c, right)) * pad) / tanH, along + (Math.abs(dot(c, up)) * pad) / tanV);
  }
  const position = target.map((t, i) => t + back[i]! * distance) as Vec3;
  const nearest = Math.min(...corners.map((c) => distance - dot(c, back))); // depth of the closest corner
  return {
    target,
    position,
    distance,
    radius,
    // generous depth range for orbiting and zooming, but never a near plane so small that depth precision collapses
    near: Math.max(radius / 2000, Math.min(nearest * 0.5, radius / 50)),
    far: distance + radius * 40,
    minDistance: Math.max(0.05, radius / 50),
    maxDistance: distance * 6,
  };
}

/** Ids of elements whose largest dimension exceeds `limitM` metres (geometry stored in the wrong unit). */
export function implausiblySized(sizes: Map<number, Vec3>, limitM: number): number[] {
  return [...sizes].filter(([, s]) => Math.max(...s) > limitM).map(([id]) => id);
}
