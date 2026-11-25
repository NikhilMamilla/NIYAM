// Every image on the landing page loads and has alt text; the demo cards (sheet A-09) are the current dashboard
// screenshots (byte-identical to submission/screens/1440x900/, written by shots.spec.ts), each with the caption and
// alt text the page declares, and none is reused for two steps.
import { expect, test } from "@playwright/test";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";

const SAME_AS: Record<string, string> = {
  "/screens/demo-1-start.png": "02-start-screen.png",
  "/screens/demo-2-verdict.png": "03-verdict-sample-a.png",
  "/screens/demo-3-sample-d.png": "04-sample-d-3d.png",
  "/screens/demo-4-clause.png": "05-selected-door-clause.png",
  "/screens/demo-5-report.png": "06-html-report.png",
};
const sha = (path: string) => createHash("sha256").update(readFileSync(path)).digest("hex");

test("landing images load, have alt text, and the demo cards are the current dashboard screenshots", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/");
  await page.locator("#demo").scrollIntoViewIfNeeded();
  await page.waitForTimeout(800);
  const images = await page.locator("img").evaluateAll((els) => els.map((e) => {
    const img = e as HTMLImageElement;
    return { src: new URL(img.src).pathname, alt: img.getAttribute("alt"), loaded: img.complete && img.naturalWidth > 0, decorative: img.closest("[aria-hidden='true']") !== null };
  }));
  const demo = images.filter((i) => i.src.startsWith("/screens/demo-"));
  expect(demo.map((d) => d.src).sort()).toEqual(Object.keys(SAME_AS).sort());
  expect(new Set(demo.map((d) => d.alt)).size).toBe(demo.length); // one claim per image
  for (const img of images) {
    if (!img.loaded) await page.evaluate((s) => fetch(s).then((r) => r.ok), img.src).then((ok) => expect(ok, `${img.src} loads`).toBe(true));
    if (!img.decorative && !img.src.includes("buildingsmart-logo")) expect(img.alt, `${img.src} has alt text`).toBeTruthy();
  }
  for (const [src, shot] of Object.entries(SAME_AS)) {
    expect(sha(`public${src}`), `${src} is the current ${shot}`).toBe(sha(`../submission/screens/1440x900/${shot}`));
  }
  // each step's caption names what its image shows
  const steps = await page.locator(".demo-step").allInnerTexts();
  expect(steps.length).toBe(Object.keys(SAME_AS).length);
  for (const [i, word] of ["Load a building", "Read the verdict", "Rooms and stairs", "failing door", "Export the report"].entries()) {
    expect(steps[i]).toContain(word);
  }
  // the old three-column dashboard had a left load panel next to the 3D view; the start screen now has none
  await page.goto("/app");
  await expect(page.getByTestId("empty-state")).toBeVisible();
  await expect(page.locator(".dash-main--start")).toBeVisible();
});
