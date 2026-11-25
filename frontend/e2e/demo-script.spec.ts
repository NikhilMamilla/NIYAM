// Executes every click of submission/demo-script.md, in order, and records how long each shot takes.
// Timings are written to test-results/demo-timings.json and printed. Run on its own: npx playwright test demo-script
import { expect, test } from "@playwright/test";
import { mkdirSync, writeFileSync } from "node:fs";
import { colourStats } from "./pixels";

test("demo script: every shot works in order", async ({ page }) => {
  test.setTimeout(300_000);
  await page.setViewportSize({ width: 1920, height: 1080 });
  const t0 = Date.now();
  const marks: { shot: string; at_s: number }[] = [];
  const mark = (shot: string) => marks.push({ shot, at_s: Math.round((Date.now() - t0) / 100) / 10 });

  // 1. Start screen
  await page.goto("/app");
  await expect(page.getByTestId("empty-state")).toBeVisible();
  await expect(page.getByText("Check a building model in three steps")).toBeVisible();
  mark("1 start screen shown");

  // 2. Load sample A: click "Open sample A"
  await page.getByRole("button", { name: "Open sample A" }).click();
  await expect(page.locator("#verdicts")).toBeVisible({ timeout: 60_000 });
  mark("2 verdict shown");
  await expect(page.locator(".viewport")).toHaveAttribute("data-view-state", "ready", { timeout: 120_000 });
  await page.waitForTimeout(1500);
  mark("3 3D view ready");

  // 4. Select a red (failing) door in 3D
  const shot = await page.locator(".viewport").screenshot();
  const red = (await colourStats(page, shot)).redCentre!;
  const box = (await page.locator(".viewport").boundingBox())!;
  await page.mouse.click(box.x + red.x, box.y + red.y);
  const panel = page.getByTestId("detail-panel");
  await expect(panel).toBeVisible();
  mark("4 failing door selected in 3D");

  // 5. Clause card: open "Clause text (MBBL-2016, page ...)" on the failing finding
  const failing = panel.locator("li.finding").filter({ hasText: "Failed" }).first();
  await failing.getByText(/Clause text \(MBBL-2016, page \d+\)/).click();
  await expect(failing.locator("details[open]").first()).toBeVisible();
  mark("5 clause card open");

  // 6. Export BCF
  await panel.getByRole("button", { name: "Back to rules" }).click();
  await page.locator("#verdicts").scrollIntoViewIfNeeded();
  const download = page.waitForEvent("download");
  await page.getByTestId("download-bcf").click();
  expect((await download).suggestedFilename()).toMatch(/\.bcf$/);
  mark("6 BCF downloaded");

  // 7. The honest limitation, on screen
  await expect(page.getByText("Draft rules, not human-reviewed")).toBeVisible();
  mark("7 draft badge visible");

  mkdirSync("test-results", { recursive: true });
  writeFileSync("test-results/demo-timings.json", JSON.stringify(marks, null, 1));
  console.log(JSON.stringify(marks));
});
