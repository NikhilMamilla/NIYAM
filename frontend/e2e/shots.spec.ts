// The final screenshots, in one sequential run: submission/screens/ at 1920x1080 (the slide set, also used by the
// README), submission/screens/1440x900/, and the landing page's demo images (copied from the 1440x900 set), plus the
// two slide figures rendered from their SVGs (python scripts/build_slide_figures.py writes the SVGs first).
import { expect, test, type Page } from "@playwright/test";
import { copyFileSync, existsSync, mkdirSync } from "node:fs";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

const SCREENS = resolve("../submission/screens");
// landing sheet A-09: file in submission/screens/1440x900 -> file in public/screens
const LANDING_DEMO: [string, string][] = [
  ["02-start-screen.png", "demo-1-start.png"],
  ["03-verdict-sample-a.png", "demo-2-verdict.png"],
  ["04-sample-d-3d.png", "demo-3-sample-d.png"],
  ["05-selected-door-clause.png", "demo-4-clause.png"],
  ["06-html-report.png", "demo-5-report.png"],
];

async function settle(page: Page) {
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(400);
}

async function openSample(page: Page, label: RegExp) {
  // samples are on the start screen only (one-page dashboard): go back to it when a model is already loaded
  if (await page.getByRole("button", { name: "Back" }).count()) await page.getByRole("button", { name: "Back" }).click();
  await page.getByRole("button", { name: label }).first().click();
  await expect(page.locator(".viewport")).toHaveAttribute("data-view-state", "ready", { timeout: 170_000 });
  await page.waitForTimeout(2200); // fly-in and highlights
}

const stageToTop = (page: Page) => page.evaluate(() => document.querySelector(".dash-stage")!.scrollIntoView({ block: "start" }));

test.describe("screenshots", () => {
  test.setTimeout(900_000); // sample D takes about a minute per load here
  test.use({ reducedMotion: "reduce" });

  for (const [w, h, dir] of [[1920, 1080, SCREENS], [1440, 900, `${SCREENS}/1440x900`]] as const) {
    test(`submission screens ${w}x${h}`, async ({ page }) => {
      mkdirSync(dir, { recursive: true });
      await page.setViewportSize({ width: w, height: h });

      await page.goto("/");
      await settle(page);
      await page.screenshot({ path: `${dir}/01-landing-hero.png` });

      await page.goto("/app");
      await expect(page.getByTestId("empty-state")).toBeVisible();
      await settle(page);
      await page.screenshot({ path: `${dir}/02-start-screen.png` });

      await page.getByRole("button", { name: "Open sample A" }).click();
      await expect(page.locator(".viewport")).toHaveAttribute("data-view-state", "ready", { timeout: 170_000 });
      await page.waitForTimeout(2200);
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.waitForTimeout(400);
      await page.screenshot({ path: `${dir}/03-verdict-sample-a.png` });

      await page.locator("li.rule > details > summary").nth(1).click();
      await page.getByRole("button", { name: /A-G-03 narrow exit/ }).click();
      const panel = page.getByTestId("detail-panel");
      const failing = panel.locator("li.finding", { hasText: "MBBL2016-5.4.1" }).filter({ hasText: "Failed" });
      await failing.getByText(/Clause text \(MBBL-2016, page 100\)/).click(); // the clause card
      await failing.getByText("Details for experts").click();
      await stageToTop(page);
      await page.waitForTimeout(1800); // camera flies to the selected door
      await page.screenshot({ path: `${dir}/05-selected-door-clause.png` });
      await panel.getByRole("button", { name: "Back to rules" }).click();

      await page.evaluate(() => window.scrollTo(0, 0));
      const popup = page.waitForEvent("popup");
      await page.getByTestId("open-report").click();
      const report = await popup;
      await report.setViewportSize({ width: w, height: h });
      await report.waitForLoadState("load");
      await report.screenshot({ path: `${dir}/06-html-report.png` });
      await report.close();

      await openSample(page, /Sample D/);
      await expect(page.getByTestId("implausible-geometry")).toHaveCount(0); // drawn at its real size
      await stageToTop(page);
      await page.waitForTimeout(800);
      await page.screenshot({ path: `${dir}/04-sample-d-3d.png` });

      if (w === 1440) for (const [from, to] of LANDING_DEMO) copyFileSync(`${dir}/${from}`, `public/screens/${to}`);
    });
  }

  test("slide figures rendered from their SVGs at 1920x1080", async ({ browser }) => {
    const context = await browser.newContext({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1.2 });
    const page = await context.newPage();
    for (const name of ["07-results-chart", "08-pipeline"]) {
      const svg = `${SCREENS}/${name}.svg`;
      expect(existsSync(svg), `${svg}: run python scripts/build_slide_figures.py first`).toBe(true);
      await page.goto(pathToFileURL(svg).href);
      await page.screenshot({ path: `${SCREENS}/${name}.png` });
    }
    await context.close();
  });
});
