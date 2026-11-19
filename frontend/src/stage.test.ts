import { describe, expect, it } from "vitest";
import { defaultQuality } from "./stage";

describe("defaultQuality", () => {
  it("is high on a capable desktop, or when the browser reports nothing", () => {
    expect(defaultQuality({ hardwareConcurrency: 8, deviceMemory: 8 }, 1440)).toBe("high");
    expect(defaultQuality({}, 1440)).toBe("high");
  });
  it("is low on few cores, little memory or a narrow screen", () => {
    expect(defaultQuality({ hardwareConcurrency: 4 }, 1440)).toBe("low");
    expect(defaultQuality({ deviceMemory: 2 }, 1440)).toBe("low");
    expect(defaultQuality({}, 390)).toBe("low");
  });
});
