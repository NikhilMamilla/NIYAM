// Silent screen recording of submission/demo-script.md, shot by shot, with Playwright video on.
// Each shot is held open at least as long as its Time column so narration (submission/video/narration.md)
// fits; the clicks reuse demo-script.spec.ts's approach. Saves to submission/video/niyam-demo-silent.webm.
// Run on its own: npx playwright test demo-video
import { expect, test } from "@playwright/test";
import { copyFileSync, mkdirSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { colourStats } from "./pixels";

const here = dirname(fileURLToPath(import.meta.url));

test.use({ viewport: { width: 1920, height: 1080 }, video: "on" });

// Cumulative end time (seconds from page load) of each shot in the demo script's Time column.
const SHOT_END_S = [10, 20, 35, 50, 65, 75, 85] as const;

test("demo video: silent recording of the demo script, one shot per narration line", async ({ page }) => {
  test.setTimeout(180_000);
  const t0 = Date.now();
  const padTo = async (targetS: number) => {
    const remain = targetS * 1000 - (Date.now() - t0);
    if (remain > 0) await page.waitForTimeout(remain);
  };

  // 1. Start screen
  await page.goto("/app");
  await expect(page.getByTestId("empty-state")).toBeVisible();
  await expect(page.getByText("Check a building model in three steps")).toBeVisible();
  await padTo(SHOT_END_S[0]);

  // 2. Load sample A
  await page.getByRole("button", { name: "Open sample A" }).click();
  await expect(page.locator("#verdicts")).toBeVisible({ timeout: 60_000 });
  await padTo(SHOT_END_S[1]);

  // 3. Verdict and 3D view ready
  await expect(page.locator(".viewport")).toHaveAttribute("data-view-state", "ready", { timeout: 120_000 });
  await padTo(SHOT_END_S[2]);

  // 4. Select a red (failing) door in 3D
  const shot = await page.locator(".viewport").screenshot();
  const red = (await colourStats(page, shot)).redCentre!;
  const box = (await page.locator(".viewport").boundingBox())!;
  await page.mouse.click(box.x + red.x, box.y + red.y);
  const panel = page.getByTestId("detail-panel");
  await expect(panel).toBeVisible();
  await padTo(SHOT_END_S[3]);

  // 5. Clause card
  const failing = panel.locator("li.finding").filter({ hasText: "Failed" }).first();
  await failing.getByText(/Clause text \(MBBL-2016, page \d+\)/).click();
  await expect(failing.locator("details[open]").first()).toBeVisible();
  await padTo(SHOT_END_S[4]);

  // 6. Export BCF
  await panel.getByRole("button", { name: "Back to rules" }).click();
  await page.locator("#verdicts").scrollIntoViewIfNeeded();
  const download = page.waitForEvent("download");
  await page.getByTestId("download-bcf").click();
  await download;
  await padTo(SHOT_END_S[5]);

  // 7. The honest limitation, on screen
  const badge = page.getByText("Draft rules, not human-reviewed");
  await badge.scrollIntoViewIfNeeded();
  await badge.hover();
  await padTo(SHOT_END_S[6]);

  // Close the context to finalise the video file, then copy it to submission/video/.
  const context = page.context();
  await context.close();
  const recorded = await page.video()!.path();
  const destDir = join(here, "..", "..", "submission", "video");
  mkdirSync(destDir, { recursive: true });
  const dest = join(destDir, "niyam-demo-silent.webm");
  copyFileSync(recorded, dest);
  const { size } = statSync(dest);
  console.log(JSON.stringify({ dest, size_bytes: size, duration_s: (Date.now() - t0) / 1000 }));
});
