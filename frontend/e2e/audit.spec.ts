import { expect, test, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";
import { colourStats } from "./pixels";

const SHOTS = "../docs/screenshots";
const SAMPLES = "../fixtures/samples";

/** Records every request to a host other than the local app/API. Shared by the real check and its self-test. */
function watchExternalRequests(page: Page): string[] {
  const external: string[] = [];
  page.context().on("request", (r) => {
    const url = new URL(r.url());
    if (!["localhost", "127.0.0.1"].includes(url.hostname) && !["data:", "blob:"].includes(url.protocol)) external.push(r.url());
  });
  return external;
}

type Truth = { doors: { expected: Record<string, string> }[] };

/** Expected summary computed from the hand-written truth file, independently of the audit engine. */
function expectedFromTruth(name: string) {
  const truth = JSON.parse(readFileSync(`${SAMPLES}/${name}.truth.json`, "utf-8")) as Truth;
  const checks: Record<string, number> = { passed: 0, failed: 0, unchecked: 0, out_of_scope: 0 };
  let withFailed = 0;
  let withUnchecked = 0;
  for (const door of truth.doors) {
    const verdicts = Object.values(door.expected);
    for (const v of verdicts) checks[v] = (checks[v] ?? 0) + 1;
    if (verdicts.includes("failed")) withFailed += 1;
    else if (verdicts.includes("unchecked")) withUnchecked += 1;
  }
  return { checks, withFailed, withUnchecked, total: truth.doors.length };
}
const IFC2X3 = "../fixtures/invalid/ifc2x3_minimal.ifc";

async function loadSample(page: Page, label: string, name: string) {
  await page.goto("/");
  const response = page.waitForResponse((r) => r.url().endsWith(`/api/samples/${name}/audit`) && r.request().method() === "POST");
  await page.getByRole("button", { name: label }).click();
  const audit = await (await response).json();
  await expect(page.locator(".viewport")).toHaveAttribute("data-view-state", "ready", { timeout: 90_000 });
  await page.waitForTimeout(800); // let the last frame with highlights render
  return audit;
}

async function viewportShot(page: Page) {
  return page.locator(".viewport").screenshot();
}

test("sample A: status, counts, rules, downloads and 3D highlighting", async ({ page, request }) => {
  const external = watchExternalRequests(page);
  const audit = await loadSample(page, "Try sample A (mm)", "sample_a_mm");
  const truth = expectedFromTruth("sample_a_mm");

  await expect(page.getByTestId("overall-status")).toHaveText("Non-compliant");
  const summary = page.locator(".summary");
  for (const [key, value] of Object.entries(truth.checks)) {
    expect(audit.summary.checks[key]).toBe(value);
    await expect(summary.getByTestId(`count-${key}`).locator("dd")).toHaveText(String(value));
  }
  expect(audit.summary.elements).toEqual({
    total_in_model_of_scoped_classes: truth.total, with_failed: truth.withFailed, with_unchecked: truth.withUnchecked,
    clean: truth.total - truth.withFailed - truth.withUnchecked,
  });
  await expect(summary.locator(".counts-heading")).toContainText("Checks run");
  await expect(page.getByTestId("elements-affected")).toHaveText(
    `Doors affected: ${truth.withFailed} with violations, ${truth.withUnchecked} could not be fully checked`);
  await expect(page.locator("li.rule .rule-id")).toHaveText(["MBBL2016-5.4.2", "MBBL2016-5.4.1", "MBBL2016-5.4.1"]);
  await expect(page.getByTestId("viewport-summary")).toContainText(
    `Doors affected: ${truth.withFailed} with violations, ${truth.withUnchecked} could not be fully checked`);
  await expect(page.locator(".viewport")).toHaveAttribute("data-id-mapping", "express_id");

  const downloadPromise = page.waitForEvent("download");
  await page.getByTestId("download-bcf").click();
  const download = await downloadPromise;
  const bcf = readFileSync((await download.path())!);
  expect(bcf.length).toBeGreaterThan(1000);
  expect(bcf.subarray(0, 2).toString()).toBe("PK"); // zip
  expect(download.suggestedFilename()).toMatch(/\.bcf$/);

  const href = await page.getByTestId("open-report").getAttribute("href");
  const report = await request.get(href!);
  expect(report.status()).toBe(200);
  expect(await report.text()).toContain("NIYAM audit report");

  const stats = await colourStats(page, await viewportShot(page));
  console.log("sample A viewport colours", JSON.stringify(stats));
  expect(stats.red).toBeGreaterThan(500);
  expect(stats.amber).toBeGreaterThan(500);
  expect(stats.grey).toBeGreaterThan(500);
  expect(external, "no runtime requests to CDNs or other hosts").toEqual([]);
  await page.screenshot({ path: `${SHOTS}/01-sample-a-audit.png` });
});

test("clicking a door in 3D and an element in the list both open the detail panel", async ({ page }) => {
  await loadSample(page, "Try sample A (mm)", "sample_a_mm");

  // 3D -> detail: click the centre of the red pixels (a failed door)
  const box = (await page.locator(".viewport").boundingBox())!;
  const before = await colourStats(page, await viewportShot(page));
  await page.mouse.click(box.x + before.redCentre!.x, box.y + before.redCentre!.y);
  const panel = page.getByTestId("detail-panel");
  await expect(panel).toBeVisible();
  await expect(panel.locator(".badge").first()).toBeVisible();

  // list -> 3D: open rule 5.4.1#b and select the narrow exit door
  await page.locator("li.rule summary").nth(1).click();
  await page.getByRole("button", { name: /A-G-03 narrow exit/ }).click();
  await expect(panel.locator("h2")).toHaveText("A-G-03 narrow exit");
  await expect(panel).toContainText("Declared width is 0.9 m; this rule requires at least 1 m.");
  const failing = panel.locator("li.finding", { hasText: "MBBL2016-5.4.1" }).filter({ hasText: "Failed" });
  await expect(failing.getByText("Technical detail")).toBeVisible();
  await expect(failing.getByText(/Clause text \(MBBL-2016, p\. 100\)/)).toBeVisible();
  await page.waitForTimeout(1200); // camera transition to the selected door
  const selected = await colourStats(page, await viewportShot(page));
  console.log("selected viewport colours", JSON.stringify(selected));
  expect(selected.blue).toBeGreaterThan(300);
  await page.screenshot({ path: `${SHOTS}/02-element-selected.png` });
});

test("show only issues hides passing and out-of-scope elements", async ({ page }) => {
  await loadSample(page, "Try sample A (mm)", "sample_a_mm");
  const before = await colourStats(page, await viewportShot(page));
  await page.getByRole("button", { name: "Show only issues" }).click();
  await expect(page.getByRole("button", { name: "Show only issues" })).toHaveAttribute("aria-pressed", "true");
  await page.waitForTimeout(1000);
  const after = await colourStats(page, await viewportShot(page));
  console.log("only-issues colours before", JSON.stringify(before), "after", JSON.stringify(after));
  expect(after.red).toBeGreaterThan(500);
  expect(after.amber).toBeGreaterThan(500);
  expect(after.grey).toBeLessThan(before.grey * 0.2);
  await page.screenshot({ path: `${SHOTS}/03-only-issues.png` });
});

test("sample C without FireExit data is incomplete, never compliant", async ({ page }) => {
  const audit = await loadSample(page, "Try sample C (no exit data)", "sample_c_no_fireexit_mm");
  expect(audit.status).toBe("incomplete");
  await expect(page.getByTestId("overall-status")).toHaveText("Incomplete");
  await expect(page.locator(".summary .explanation")).toContainText("could not be checked because required data is missing");
  const stats = await colourStats(page, await viewportShot(page));
  console.log("sample C viewport colours", JSON.stringify(stats));
  expect(stats.amber).toBeGreaterThan(500);
  expect(stats.red).toBe(0);
  await page.screenshot({ path: `${SHOTS}/04-incomplete.png` });
});

test("keyboard only: start a sample audit, expand a rule and select an element", async ({ page }) => {
  await page.goto("/");
  const sample = page.getByRole("button", { name: "Try sample A (mm)" });
  for (let i = 0; i < 12 && !(await sample.evaluate((el) => el === document.activeElement)); i++) {
    await page.keyboard.press("Tab");
  }
  await expect(sample).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("overall-status")).toHaveText("Non-compliant");
  await expect(page.locator(".viewport")).toHaveAttribute("data-view-state", "ready", { timeout: 90_000 });

  const summary = page.locator("li.rule summary").nth(1);
  await summary.focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("li.rule details").nth(1)).toHaveAttribute("open", "");
  const element = page.getByRole("button", { name: /A-1-02 narrow sliding exit/ });
  await element.focus();
  await page.keyboard.press("Enter");
  await expect(element).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByTestId("detail-panel").locator("h2")).toHaveText("A-1-02 narrow sliding exit");
  // a visible focus ring: the focused button carries the focus box-shadow
  expect(await element.evaluate((el) => getComputedStyle(el).boxShadow)).not.toBe("none");
});

test("garbage .ifc shows the 422 message", async ({ page }) => {
  await page.goto("/");
  await page.locator('input[type="file"]').setInputFiles({
    name: "garbage.ifc", mimeType: "application/octet-stream", buffer: Buffer.from("this is not an IFC file"),
  });
  await expect(page.getByRole("alert")).toContainText("HTTP 422");
  await expect(page.getByTestId("error-message")).toHaveText("could not read IFC file: Unable to parse IFC SPF header");
  await expect(page.locator(".summary")).toHaveCount(0);
});

test("IFC2X3 file shows the unsupported-schema message", async ({ page }) => {
  await page.goto("/");
  await page.locator('input[type="file"]').setInputFiles(IFC2X3);
  await expect(page.getByTestId("error-message"))
    .toHaveText("unsupported IFC schema IFC2X3: NIYAM v0.1 audits IFC4 models");
});
