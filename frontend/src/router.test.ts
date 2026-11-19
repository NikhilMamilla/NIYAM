import { describe, expect, it } from "vitest";
import { routeOf } from "./router";

describe("routeOf", () => {
  it("maps / to the landing page and /app to the dashboard", () => {
    expect(routeOf("/")).toEqual({ page: "landing" });
    expect(routeOf("")).toEqual({ page: "landing" });
    expect(routeOf("/app")).toEqual({ page: "app", sample: null });
    expect(routeOf("/app/")).toEqual({ page: "app", sample: null });
  });

  it("reads a sample deep link and rejects anything that is not a plain sample name", () => {
    expect(routeOf("/app", "?sample=sample_d_rooms_stairs_mm")).toEqual({ page: "app", sample: "sample_d_rooms_stairs_mm" });
    expect(routeOf("/app", "?sample=../../etc")).toEqual({ page: "app", sample: null });
  });

  it("reports unknown paths", () => {
    expect(routeOf("/nope")).toEqual({ page: "not-found", path: "/nope" });
  });
});
