// Static demo mode (GitHub Pages): which source each call uses. The mode is decided once per module load,
// so each case loads a fresh copy of the module with its own build variables.
import { afterEach, describe, expect, it, vi } from "vitest";

async function load(env: Record<string, string>, fetchImpl: (url: string) => Promise<Response>) {
  vi.resetModules();
  for (const [k, v] of Object.entries(env)) vi.stubEnv(k, v);
  const fetchMock = vi.fn((url: string) => fetchImpl(url));
  vi.stubGlobal("fetch", fetchMock);
  return { api: await import("./api"), fetchMock };
}
const json = (body: unknown) => Promise.resolve(new Response(JSON.stringify(body), { status: 200 }));

describe("static demo mode", () => {
  afterEach(() => { vi.unstubAllEnvs(); vi.unstubAllGlobals(); });

  it("a static build with no API URL serves the saved files and refuses uploads", async () => {
    const { api, fetchMock } = await load({ VITE_STATIC_DEMO: "1", VITE_API_URL: "" },
      () => json({ audit_id: "abc", status: "noncompliant", summary: {}, rules: [] }));
    expect(await api.apiMode()).toBe("static");
    const audit = await api.auditSample("sample_a_mm");
    expect(fetchMock.mock.lastCall?.[0]).toBe("/demo/sample_a_mm/audit.json");
    expect(api.bcfUrl(audit.audit_id)).toBe("/demo/sample_a_mm/issues.bcf");
    expect(api.reportUrl(audit.audit_id)).toBe("/demo/sample_a_mm/report.html");
    await expect(api.auditUpload(new File(["x"], "m.ifc"))).rejects.toEqual(new api.ApiError(0, api.DEMO_MESSAGE));
  });

  it("falls back to the saved files when the API does not answer its health check", async () => {
    const { api } = await load({ VITE_STATIC_DEMO: "1", VITE_API_URL: "https://api.example" },
      () => Promise.reject(new TypeError("Failed to fetch")));
    expect(await api.apiMode()).toBe("static");
  });

  it("uses the API, prefixed with its URL, when it is healthy", async () => {
    const { api, fetchMock } = await load({ VITE_STATIC_DEMO: "1", VITE_API_URL: "https://api.example/" },
      () => json({ status: "ok" }));
    expect(await api.apiMode()).toBe("api");
    await api.listSamples();
    expect(fetchMock.mock.lastCall?.[0]).toBe("https://api.example/api/samples");
    expect(api.bcfUrl("abc")).toBe("https://api.example/api/audit/abc/issues.bcf");
  });

  it("a normal build never checks health and keeps the relative /api paths", async () => {
    const { api, fetchMock } = await load({ VITE_STATIC_DEMO: "" }, () => json([]));
    expect(await api.apiMode()).toBe("api");
    await api.listSamples();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.lastCall?.[0]).toBe("/api/samples");
  });
});
