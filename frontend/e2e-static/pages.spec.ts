// The public GitHub Pages site with no backend at all: the landing page and every asset under the base path,
// /app opened directly, all 5 samples from the engine's saved results (counts equal the hand-written truth files,
// not the saved files themselves), a door selected in 3D, its clause card, and a valid BCF 2.1 download.
// Local: npx playwright test -c playwright.static.config.ts      Live: LIVE_URL=<site>/ npx playwright test -c ...
import { expect, test, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";
import { colourStats } from "../e2e/pixels";
import { expectedFromTruth } from "../e2e/truth";
import { readZip } from "./zip";

const SAMPLES = {
  sample_a_mm: "Breaks a rule",
  sample_b_m: "Breaks a rule",
  sample_c_no_fireexit_mm: "Not fully checked",
  sample_d_rooms_stairs_mm: "Breaks a rule",
  sample_e_rooms_stairs_m: "Breaks a rule",
} as const;

/** Any request that would need a backend: there must be none. */
function watchApi(page: Page): string[] {
  const calls: string[] = [];
  page.context().on("request", (r) => { if (/\/api\/|:8000\b|\/health\b/.test(r.url())) calls.push(r.url()); });
  return calls;
}

/** Assets that failed to load. The deep-link document itself is served from 404.html with status 404, as on Pages. */
function watchFailures(page: Page): string[] {
  const failed: string[] = [];
  page.on("response", (r) => { if (r.status() >= 400 && r.request().resourceType() !== "document") failed.push(`${r.status()} ${r.url()}`); });
  page.on("requestfailed", (r) => failed.push(`failed ${r.url()}`));
  return failed;
}

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => { try { window.localStorage.setItem("niyam.tour.done", "1"); } catch { /* ignore */ } });
});

test("landing page: loads under the base path with every image, font and download", async ({ page, request }) => {
  const failed = watchFailures(page);
  const api = watchApi(page);
  await page.goto("./");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("as checks a computer can run");
  await page.evaluate(async () => {
    for (let y = 0; y < document.body.scrollHeight; y += 500) { window.scrollTo(0, y); await new Promise((r) => setTimeout(r, 40)); }
  });
  await page.waitForLoadState("networkidle");
  const broken = await page.$$eval("img", (imgs) => imgs.filter((i) => i.complete && i.naturalWidth === 0).map((i) => i.src));
  expect(broken, "images that did not load").toEqual([]);
  expect(await page.evaluate(() => document.fonts.check("16px 'Plex Sans'"))).toBe(true);
  for (const link of await page.locator('a[href*="/downloads/"]').all()) {
    const href = (await link.getAttribute("href"))!;
    expect((await request.get(new URL(href, page.url()).href)).status(), href).toBe(200);
  }
  expect(failed).toEqual([]);
  expect(api).toEqual([]);
  await expect(page.locator('meta[property="og:image"]')).toHaveAttribute("content", /og-image\.png$/);
});

test("/app opens directly and is honest about demo mode", async ({ page }) => {
  const failed = watchFailures(page);
  await page.goto("app");
  await expect(page.getByTestId("demo-banner")).toContainText(
    "Demo mode: results for the 5 sample buildings were produced by the real NIYAM engine. To audit your own IFC file, run NIYAM locally (see How to run).");
  await expect(page.getByText("Draft rules, not human-reviewed")).toBeVisible();
  await expect(page.getByTestId("dropzone").locator('input[type="file"]')).toBeDisabled();
  await expect(page.getByTestId("dropzone")).toContainText("Uploads are off in this demo");
  await page.getByRole("link", { name: "NIYAM" }).first().click();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("as checks a computer can run");
  expect(failed).toEqual([]);
});

for (const [name, status] of Object.entries(SAMPLES)) {
  test(`${name}: the verdict and counts equal the truth file, and the 3D view draws`, async ({ page }) => {
    const api = watchApi(page);
    const failed = watchFailures(page);
    await page.goto(`app?sample=${name}`);
    await expect(page.getByTestId("overall-status")).toHaveText(status);
    const truth = expectedFromTruth(name);
    for (const [key, value] of Object.entries(truth.checks)) {
      await expect(page.locator(".summary").getByTestId(`count-${key}`).locator("dd")).toHaveText(String(value));
    }
    const clean = truth.total - truth.withFailed - truth.withUnchecked;
    await expect(page.getByTestId("elements-affected")).toHaveText(
      `Distinct elements: ${truth.withFailed} with violations, ${truth.withUnchecked} could not be fully checked, ${clean} clean (of ${truth.total} the rules apply to)`,
      { useInnerText: true });
    await expect(page.locator(".viewport")).toHaveAttribute("data-view-state", "ready", { timeout: 120_000 });
    expect(api, "no request needs a backend").toEqual([]);
    expect(failed).toEqual([]);
  });
}

test("sample A: select a door in 3D, open its clause card, download the report and a valid BCF 2.1 file", async ({ page, request }) => {
  await page.goto("app?sample=sample_a_mm");
  await expect(page.locator(".viewport")).toHaveAttribute("data-view-state", "ready", { timeout: 120_000 });
  await page.waitForTimeout(1500); // fly-in
  const shot = await page.locator(".viewport").screenshot();
  const red = (await colourStats(page, shot)).redCentre!;
  const box = (await page.locator(".viewport").boundingBox())!;
  await page.mouse.click(box.x + red.x, box.y + red.y);
  const panel = page.getByTestId("detail-panel");
  await expect(panel).toBeVisible();
  const failing = panel.locator("li.finding").filter({ hasText: "Failed" }).first();
  await failing.getByText(/Clause text \(MBBL-2016, page \d+\)/).click();
  await expect(failing.locator("details[open]").first()).toBeVisible();
  await panel.getByRole("button", { name: "Back to rules" }).click();

  const report = await request.get(new URL((await page.getByTestId("open-report").getAttribute("href"))!, page.url()).href);
  expect(report.status()).toBe(200);
  expect(await report.text()).toContain("NIYAM audit report");

  const download = page.waitForEvent("download");
  await page.getByTestId("download-bcf").click();
  const zip = readZip(readFileSync((await (await download).path())!));
  expect(zip.get("bcf.version")?.toString("utf-8")).toMatch(/VersionId="2\.1"/);
  const topics = [...new Set([...zip.keys()].filter((n) => n.includes("/")).map((n) => n.split("/")[0]))];
  for (const t of topics) expect(zip.has(`${t}/markup.bcf`), `${t}/markup.bcf`).toBe(true);
  const truth = expectedFromTruth("sample_a_mm");
  expect(topics.length, "one topic per failed or unchecked check").toBe(truth.checks.failed! + truth.checks.unchecked!);
});
