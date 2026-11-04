import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, NETWORK_ERROR, auditSample, errorMessage } from "./api";

describe("API error mapping", () => {
  it("shows the server's own detail verbatim", () => {
    expect(errorMessage(422, { detail: "unsupported IFC schema IFC2X3: NIYAM v0.1 audits IFC4 models" }))
      .toBe("unsupported IFC schema IFC2X3: NIYAM v0.1 audits IFC4 models");
    expect(errorMessage(413, { detail: "file exceeds the 100 MB upload limit" })).toBe("file exceeds the 100 MB upload limit");
    expect(errorMessage(415, { detail: "only .ifc files are accepted" })).toBe("only .ifc files are accepted");
    expect(errorMessage(500, { detail: "internal error while auditing the model" }))
      .toBe("internal error while auditing the model");
  });

  it("falls back to a readable sentence when there is no string detail", () => {
    expect(errorMessage(422, { detail: [{ msg: "Field required" }] })).toBe("The server could not process this request.");
    expect(errorMessage(502, null)).toBe("The server failed while handling the request.");
    expect(errorMessage(404, null)).toBe("Request failed (HTTP 404).");
  });
});

describe("request failures", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("turns a network failure into status 0 with a recovery hint", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    await expect(auditSample("sample_a_mm")).rejects.toEqual(new ApiError(0, NETWORK_ERROR));
  });

  it("carries the HTTP status and detail of an error response", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "sample not found" }), { status: 404 })));
    const error = await auditSample("nope").catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).status).toBe(404);
    expect((error as ApiError).message).toBe("sample not found");
  });
});
