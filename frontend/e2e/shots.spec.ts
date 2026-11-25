// Screenshots for review and docs: landing (desktop, phone), dashboard states, and the landing page's demo images.
import { expect, test, type Page } from "@playwright/test";

const SHOTS = process.env.SHOTS_DIR ?? "../docs/screenshots";
const DEMO = "public/screens";

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

test.describe("screenshots", () => {
  test.setTimeout(900_000); // one page loads every sample; D and E take about a minute each here
  test.use({ reducedMotion: "reduce" });

  test("landing desktop and phone", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/");
    await settle(page);
    await page.screenshot({ path: `${SHOTS}/landing-desktop.png`, fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/");
    await settle(page);
    await page.screenshot({ path: `${SHOTS}/landing-mobile.png`, fullPage: true });
  });

  test("dashboard states", async ({ page }) => {
    await page.addInitScript(() => { try { window.localStorage.setItem("niyam.tour.done", "1"); } catch { /* ignore */ } });
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/app");
    await expect(page.getByTestId("empty-state")).toBeVisible();
    await settle(page);
    await page.screenshot({ path: `${SHOTS}/app-empty.png` });
    for (const [label, name] of [[/Sample A/, "a"], [/Sample B/, "b"], [/Sample C/, "c"], [/Sample D/, "d"], [/Sample E/, "e"]] as const) {
      await openSample(page, label);
      await page.screenshot({ path: `${SHOTS}/app-sample-${name}.png` });
    }
  });

  test("demo images for the landing page (sample A)", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/app");
    await expect(page.getByTestId("empty-state")).toBeVisible();
    await page.waitForTimeout(600);
    await page.screenshot({ path: `${DEMO}/demo-1-load.png` });
    await openSample(page, /Sample A/);
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(400);
    await page.screenshot({ path: `${DEMO}/demo-2-verdict.png` });
    await page.locator("li.rule > details > summary").nth(1).click();
    await page.getByRole("button", { name: /A-G-03 narrow exit/ }).click();
    await page.locator(".dash-stage").scrollIntoViewIfNeeded();
    await page.evaluate(() => document.querySelector(".dash-stage")!.scrollIntoView({ block: "start" }));
    await page.waitForTimeout(1800);
    await page.screenshot({ path: `${DEMO}/demo-3-select.png` });
    await page.screenshot({ path: `${SHOTS}/app-selected.png` });
  });
});
