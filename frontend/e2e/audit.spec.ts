import { expect, test, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";
import { colourStats, hueStats } from "./pixels";
import { expectedFromTruth } from "./truth";

const SHOTS = "test-results/shots"; // debug screenshots only (gitignored); the published set comes from shots.spec.ts
const RULE_IDS = ["MBBL2016-5.4.2", "MBBL2016-5.4.1", "MBBL2016-5.4.1", "MBBL2016-4.5.2", "MBBL2016-4.3.1.1",
  "MBBL2016-4.17.2"];

/** Records every request to a host other than the local app/API. Shared by the real check and its self-test. */
function watchExternalRequests(page: Page): string[] {
  const external: string[] = [];
  page.context().on("request", (r) => {
    const url = new URL(r.url());
    if (!["localhost", "127.0.0.1"].includes(url.hostname) && !["data:", "blob:"].includes(url.protocol)) external.push(r.url());
  });
  return external;
}

function watchConsoleErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text().slice(0, 300)); });
  page.on("pageerror", (e) => errors.push(e.message));
  return errors;
}

const IFC2X3 = "../fixtures/invalid/ifc2x3_minimal.ifc";

test.beforeEach(async ({ page }) => {
  // the first-use tour is tested on its own below
  await page.addInitScript(() => { try { window.localStorage.setItem("niyam.tour.done", "1"); } catch { /* ignore */ } });
});

async function loadSample(page: Page, label: RegExp, name: string) {
  await page.goto("/app");
  const response = page.waitForResponse((r) => r.url().endsWith(`/api/samples/${name}/audit`) && r.request().method() === "POST");
  await page.getByRole("button", { name: label }).first().click();
  const audit = await (await response).json();
  await expect(page.locator(".viewport")).toHaveAttribute("data-view-state", "ready", { timeout: 90_000 });
  await page.waitForTimeout(1500); // fly-in and the last frame with highlights
  return audit;
}

const viewportShot = (page: Page) => page.locator(".viewport").screenshot();

async function expectSummaryMatchesTruth(page: Page, audit: { summary: { checks: Record<string, number>; elements: unknown } }, name: string) {
  const truth = expectedFromTruth(name);
  for (const [key, value] of Object.entries(truth.checks)) {
    expect(audit.summary.checks[key]).toBe(value);
    await expect(page.locator(".summary").getByTestId(`count-${key}`).locator("dd")).toHaveText(String(value));
  }
  const clean = truth.total - truth.withFailed - truth.withUnchecked;
  expect(audit.summary.elements).toEqual({
    total_in_model_of_scoped_classes: truth.total, with_failed: truth.withFailed, with_unchecked: truth.withUnchecked, clean,
  });
  await expect(page.getByTestId("elements-affected")).toHaveText(
    `Distinct elements: ${truth.withFailed} with violations, ${truth.withUnchecked} could not be fully checked, ${clean} clean (of ${truth.total} the rules apply to)`, { useInnerText: true });
}

test("sample A: status, counts, rules, exports and 3D colours; no external requests or console errors", async ({ page, request }) => {
  const external = watchExternalRequests(page);
  const errors = watchConsoleErrors(page);
  const audit = await loadSample(page, /Sample A/, "sample_a_mm");
  await expect(page.getByTestId("overall-status")).toHaveText("Breaks a rule");
  await expectSummaryMatchesTruth(page, audit, "sample_a_mm");
  const truth = expectedFromTruth("sample_a_mm");
  await expect(page.getByTestId("plain-summary")).toHaveText(
    `${truth.withFailed} doors break a rule. ${truth.withUnchecked} doors could not be checked because the model lacks data.`);
  await expect(page.locator("li.rule .rule-id")).toHaveText(RULE_IDS);
  await expect(page.getByTestId("rule-MBBL2016-4.5.2")).toContainText("Nothing checked");
  await expect(page.getByTestId("viewport-summary")).toContainText("doors break a rule");
  await expect(page.locator(".viewport")).toHaveAttribute("data-id-mapping", "express_id");

  const downloadPromise = page.waitForEvent("download");
  await page.getByTestId("download-bcf").click();
  const bcf = readFileSync((await (await downloadPromise).path())!);
  expect(bcf.subarray(0, 2).toString()).toBe("PK"); // zip
  const jsonDownload = page.waitForEvent("download");
  await page.getByTestId("download-json").click();
  const json = JSON.parse(readFileSync((await (await jsonDownload).path())!, "utf-8"));
  expect(json.summary.checks).toEqual(audit.summary.checks);
  const report = await request.get((await page.getByTestId("open-report").getAttribute("href"))!);
  expect(report.status()).toBe(200);
  expect(await report.text()).toContain("NIYAM audit report");

  const hues = await hueStats(page, await viewportShot(page));
  expect(hues.red).toBeGreaterThan(500);
  expect(hues.amber).toBeGreaterThan(500);
  expect(external, "no runtime requests to CDNs or other hosts").toEqual([]);
  expect(errors, "no console errors").toEqual([]);
});

test("the external-request guard flags a request to another host (it can fail)", async ({ page }) => {
  const external = watchExternalRequests(page);
  await page.goto("/");
  expect(external).toEqual([]);
  await page.evaluate(() => fetch("http://example.invalid/").catch(() => "blocked or unresolvable, as expected"));
  await expect.poll(() => external).toEqual(["http://example.invalid/"]);
});

test("landing page: no external requests, no 3D engine loaded, no console errors; Open the app and back/forward work", async ({ page }) => {
  const external = watchExternalRequests(page);
  const errors = watchConsoleErrors(page);
  const engineRequests: string[] = [];
  page.on("request", (r) => { if (/web-ifc|\.wasm/.test(r.url())) engineRequests.push(r.url()); });
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("as checks a computer can run");
  // the button light and navigation use small canvases; the 3D engine (web-ifc wasm) must not load on the landing page
  expect(engineRequests).toEqual([]);
  await page.getByRole("link", { name: "Open the app" }).first().click();
  await expect(page).toHaveURL(/\/app$/);
  await expect(page.getByTestId("empty-state")).toBeVisible();
  await page.goBack();
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await page.goForward();
  await expect(page.getByTestId("empty-state")).toBeVisible();
  expect(external).toEqual([]);
  expect(errors).toEqual([]);
});

test("deep link /app?sample= opens that sample", async ({ page }) => {
  await page.goto("/app?sample=sample_c_no_fireexit_mm");
  await expect(page.getByTestId("overall-status")).toHaveText("Not fully checked", { timeout: 60_000 });
});

test("Back returns from a loaded sample to the start screen", async ({ page }) => {
  await loadSample(page, /Sample A/, "sample_a_mm");
  await page.getByRole("button", { name: "Back" }).click();
  await expect(page.getByTestId("empty-state")).toBeVisible();
  await expect(page.getByRole("button", { name: "Back" })).toHaveCount(0);
  await page.getByRole("button", { name: /Sample C/ }).first().click();
  await expect(page.getByTestId("overall-status")).toBeVisible({ timeout: 60_000 });
});

test("clicking a door in 3D and an element in the list both open the detail panel", async ({ page }) => {
  await loadSample(page, /Sample A/, "sample_a_mm");
  const before = await colourStats(page, await viewportShot(page));
  const box = (await page.locator(".viewport").boundingBox())!; // after the shot: it scrolls the viewport into view
  await page.mouse.click(box.x + before.redCentre!.x, box.y + before.redCentre!.y);
  const panel = page.getByTestId("detail-panel");
  await expect(panel).toBeVisible();
  await expect(panel.locator(".badge").first()).toBeVisible();
  await panel.getByRole("button", { name: "Back to rules" }).click();

  await page.locator("li.rule > details > summary").nth(1).click();
  await page.getByRole("button", { name: /A-G-03 narrow exit/ }).click();
  await expect(panel.locator("h2")).toHaveText("A-G-03 narrow exit");
  await expect(panel).toContainText("Declared width is 0.9 m; this rule requires at least 1 m.");
  const failing = panel.locator("li.finding", { hasText: "MBBL2016-5.4.1" }).filter({ hasText: "Failed" });
  await expect(failing.getByText("Details for experts")).toBeVisible();
  await expect(failing.getByText(/Clause text \(MBBL-2016, page 100\)/)).toBeVisible();
  await page.waitForTimeout(1500); // camera flies to the selected door
  expect((await hueStats(page, await viewportShot(page))).blue).toBeGreaterThan(300);
  await page.screenshot({ path: `${SHOTS}/02-element-selected.png` });
});

test("show only issues hides passing and out-of-scope elements", async ({ page }) => {
  await loadSample(page, /Sample A/, "sample_a_mm");
  const before = await colourStats(page, await viewportShot(page));
  await page.getByRole("button", { name: "Only issues" }).click();
  await expect(page.getByRole("button", { name: "Only issues" })).toHaveAttribute("aria-pressed", "true");
  await page.waitForTimeout(1000);
  const after = await colourStats(page, await viewportShot(page));
  const hues = await hueStats(page, await viewportShot(page));
  expect(hues.red).toBeGreaterThan(500);
  expect(hues.amber).toBeGreaterThan(500);
  expect(after.grey).toBeLessThan(before.grey);
  await page.screenshot({ path: `${SHOTS}/03-only-issues.png` });
});

test("sample C without exit data is not fully checked, never 'no issues'", async ({ page }) => {
  const audit = await loadSample(page, /Sample C/, "sample_c_no_fireexit_mm");
  expect(audit.status).toBe("incomplete");
  await expect(page.getByTestId("overall-status")).toHaveText("Not fully checked");
  await expect(page.locator(".summary .explanation")).toContainText("could not be checked because required data is missing");
  const hues = await hueStats(page, await viewportShot(page));
  expect(hues.amber).toBeGreaterThan(500);
  expect(hues.red).toBeLessThan(50);
});

test("keyboard only: open a sample, expand a rule and select an element", async ({ page }) => {
  await page.goto("/app");
  await expect(page.getByTestId("empty-state")).toBeVisible();
  const sample = page.getByRole("button", { name: /Sample A/ }).first();
  for (let i = 0; i < 20 && !(await sample.evaluate((el) => el === document.activeElement)); i++) await page.keyboard.press("Tab");
  await expect(sample).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("overall-status")).toHaveText("Breaks a rule");
  await expect(page.locator(".viewport")).toHaveAttribute("data-view-state", "ready", { timeout: 90_000 });
  const summary = page.locator("li.rule > details > summary").nth(1);
  await summary.focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("li.rule > details").nth(1)).toHaveAttribute("open", "");
  const element = page.getByRole("button", { name: /A-1-02 narrow sliding exit/ });
  await element.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("detail-panel").locator("h2")).toHaveText("A-1-02 narrow sliding exit");
  await expect(page.getByTestId("detail-panel").locator("h2")).toBeFocused(); // focus moves to the detail
  const back = page.getByRole("button", { name: "Back to rules" });
  await back.focus();
  expect(await back.evaluate((el) => getComputedStyle(el).boxShadow)).not.toBe("none"); // visible focus ring
});

test("garbage .ifc shows the 422 message", async ({ page }) => {
  await page.goto("/app");
  await page.locator('input[type="file"]').setInputFiles({
    name: "garbage.ifc", mimeType: "application/octet-stream", buffer: Buffer.from("this is not an IFC file"),
  });
  await expect(page.getByRole("alert")).toContainText("HTTP 422");
  await expect(page.getByTestId("error-message")).toHaveText("could not read IFC file: Unable to parse IFC SPF header");
  await expect(page.locator(".summary")).toHaveCount(0);
});

test("IFC2X3 file is refused with an explanation", async ({ page }) => {
  await page.goto("/app");
  await page.locator('input[type="file"]').setInputFiles(IFC2X3);
  await expect(page.getByTestId("error-message")).toHaveText("unsupported IFC schema IFC2X3: NIYAM v0.1 audits IFC4 models");
  await expect(page.getByRole("alert")).toContainText("Export your model as IFC4");
});

test("geometric sample D (mm): rooms and stairs are checked, listed and coloured", async ({ page }) => {
  const audit = await loadSample(page, /Sample D/, "sample_d_rooms_stairs_mm");
  await expect(page.getByTestId("overall-status")).toHaveText("Breaks a rule");
  await expectSummaryMatchesTruth(page, audit, "sample_d_rooms_stairs_mm");
  expect(audit.summary.rules_with_errors).toBe(0);
  await expect(page.locator("li.rule .rule-id")).toHaveText(RULE_IDS);
  const hues = await hueStats(page, await viewportShot(page));
  expect(hues.red).toBeGreaterThan(300);
  expect(hues.amber).toBeGreaterThan(300);
});

test("a failed room shows computed versus required area; it is also selectable from the list", async ({ page }) => {
  await loadSample(page, /Sample D/, "sample_d_rooms_stairs_mm");
  await page.locator("li.rule > details > summary").nth(3).click(); // MBBL2016-4.5.2
  await page.getByRole("button", { name: /D-B-02 small bathroom/ }).click();
  const panel = page.getByTestId("detail-panel");
  await expect(panel.locator("h2")).toHaveText("D-B-02 small bathroom 1.5 m2");
  await expect(panel).toContainText("Computed floor area is 1.50 m2; this rule requires at least 1.8 m2.");
  await expect(panel.locator("li.finding", { hasText: "MBBL2016-4.5.2" })).toContainText("Failed");
  await expect(panel.locator("li.finding", { hasText: "MBBL2016-4.3.1.1" })).toContainText("Out of scope");
});

test("an unchecked room explains what is missing and offers the readiness file", async ({ page }) => {
  await loadSample(page, /Sample D/, "sample_d_rooms_stairs_mm");
  await page.getByRole("button", { name: "Not checked", exact: false }).first().click();
  await page.locator("li.rule > details > summary").first().click();
  await page.getByRole("button", { name: /D-X-01 space without category/ }).first().click();
  const panel = page.getByTestId("detail-panel");
  await expect(panel).toContainText("What is missing:");
  await expect(panel).toContainText("Pset_SpaceCommon.Category");
  const download = page.waitForEvent("download");
  await panel.getByRole("button", { name: /Readiness/ }).first().click();
  expect((await download).suggestedFilename()).toBe("niyam-data-readiness.ids");
});

test("geometric sample E (m): counts equal the truth file and a narrow stair flight is explained", async ({ page }) => {
  const audit = await loadSample(page, /Sample E/, "sample_e_rooms_stairs_m");
  await expectSummaryMatchesTruth(page, audit, "sample_e_rooms_stairs_m");
  await page.locator("li.rule > details > summary").nth(5).click(); // MBBL2016-4.17.2
  await page.getByRole("button", { name: /E-ST-02 residential flight 0.85 m/ }).click();
  await expect(page.getByTestId("detail-panel")).toContainText("Computed stair width is 0.85 m; this rule requires at least 1 m.");
  await page.waitForTimeout(1500);
  expect((await hueStats(page, await viewportShot(page))).blue).toBeGreaterThan(300);
});

test("reduced motion: the landing page shows every sheet fully printed, without waiting", async ({ browser }) => {
  const context = await browser.newContext({ reducedMotion: "reduce" });
  const page = await context.newPage();
  await page.goto("/");
  expect(await page.locator("[data-waiting]").count()).toBe(0);
  const clip = await page.locator(".chart-svg").first().evaluate((el) => getComputedStyle(el).clipPath);
  expect(["none", "inset(0px)", "inset(0px 0px 0px 0px)"]).toContain(clip);
  await context.close();
});
