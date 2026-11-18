import { describe, expect, it } from "vitest";
import { ISO_DIRECTION, frameBox, implausiblySized, type Vec3 } from "./framing";

/** Project a world point with a perspective camera at `position` looking at `target` (y up); NDC x/y. */
function project(p: Vec3, position: Vec3, target: Vec3, fovDeg: number, aspect: number) {
  const sub = (a: Vec3, b: Vec3): Vec3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
  const cross = (a: Vec3, b: Vec3): Vec3 => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  const dot = (a: Vec3, b: Vec3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const norm = (a: Vec3): Vec3 => { const l = Math.hypot(...a); return [a[0] / l, a[1] / l, a[2] / l]; };
  const forward = norm(sub(target, position));
  const right = norm(cross(forward, [0, 1, 0]));
  const up = cross(right, forward);
  const d = sub(p, position);
  const z = dot(d, forward);
  const t = Math.tan((fovDeg * Math.PI) / 360);
  return { x: dot(d, right) / (z * t * aspect), y: dot(d, up) / (z * t), z };
}

function corners(min: Vec3, max: Vec3): Vec3[] {
  const out: Vec3[] = [];
  for (const x of [min[0], max[0]]) for (const y of [min[1], max[1]]) for (const z of [min[2], max[2]]) out.push([x, y, z]);
  return out;
}

describe("frameBox", () => {
  const cases: [string, Vec3, Vec3, number][] = [
    ["sample A row of doors (13 x 6 x 3 m), wide stage", [-1, -2.3, -1.5], [12, 3.5, 1.5], 16 / 9],
    ["sample E row of rooms (35 m long), narrow stage", [0, -2.4, -3.5], [35.4, 0.35, 0], 0.7],
    ["sample D as stored in its file (4 km)", [0, -2750, -3000], [4008.75, 250, 0], 1.3],
    ["a single 0.1 m element", [0, 0, 0], [0.1, 0.1, 0.1], 1],
  ];
  for (const [label, min, max, aspect] of cases) {
    it(`keeps every corner of ${label} inside the view, in front of the near plane and before the far plane`, () => {
      const f = frameBox({ min, max }, { fovDeg: 60, aspect, direction: ISO_DIRECTION });
      for (const c of corners(min, max)) {
        const p = project(c, f.position, f.target, 60, aspect);
        expect(Math.abs(p.x)).toBeLessThanOrEqual(1);
        expect(Math.abs(p.y)).toBeLessThanOrEqual(1);
        expect(p.z).toBeGreaterThan(f.near);
        expect(p.z).toBeLessThan(f.far);
      }
      expect(f.maxDistance).toBeGreaterThanOrEqual(f.distance * 2); // the user can zoom out further
      expect(f.minDistance).toBeLessThan(f.distance);
    });
  }

  it("never uses That Open's fixed limits (max distance 300, far plane 1000) for a 4 km model", () => {
    const f = frameBox({ min: [0, 0, 0], max: [4000, 3000, 3000] }, { fovDeg: 60, aspect: 1, direction: ISO_DIRECTION });
    expect(f.distance).toBeGreaterThan(300);
    expect(f.maxDistance).toBeGreaterThan(300);
    expect(f.far).toBeGreaterThan(1000);
  });

  it("targets the centre of the box and looks from the given direction", () => {
    const f = frameBox({ min: [0, 0, 0], max: [10, 4, 2] }, { fovDeg: 60, aspect: 1, direction: [0, 0, 1] });
    expect(f.target).toEqual([5, 2, 1]);
    expect(f.position[0]).toBeCloseTo(5);
    expect(f.position[1]).toBeCloseTo(2);
    expect(f.position[2]).toBeGreaterThan(2);
  });
});

describe("implausiblySized", () => {
  it("flags elements larger than the limit and keeps ordinary rooms", () => {
    const sizes = new Map<number, Vec3>([[1, [2, 2.75, 1.2]], [2, [2000, 2750, 1200]], [3, [3000, 1500, 1200]]]);
    expect(implausiblySized(sizes, 200)).toEqual([2, 3]);
  });
});
