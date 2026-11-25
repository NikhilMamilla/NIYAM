// Landing page at 375, 768, 1280 and 1440 px: no horizontal overflow, nothing wider than the viewport, every image
// with alt text (charts and tables scroll inside their own box on purpose), a working skip link, and keyboard focus
// that reaches the main actions with a visible ring. 1280 sits in the gap between the demo sheet's two-column
// breakpoint (960px) and its full-size card stack (around 920px natural width): the card stack must scale itself
// down to fit there, not just at the three sizes a page is usually checked at.
// Full-page screenshots go to test-results/responsive/ for a person to look at.
import { expect, test } from "@playwright/test";

test.use({ reducedMotion: "reduce" });

for (const width of [375, 768, 1280, 1440]) {
  test(`landing at ${width} px: no layout break`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/");
    await page.evaluate(() => document.fonts.ready);
    const overflow = await page.evaluate(() => {
      const vw = document.documentElement.clientWidth;
      const wide = [...document.querySelectorAll<HTMLElement>("main *, footer *")]
        .filter((el) => {
          const r = el.getBoundingClientRect();
          const style = getComputedStyle(el);
          return r.width > 0 && style.position !== "fixed" && (r.right > vw + 1 || r.left < -1)
            && !el.closest(".table-wrap, .chart, .demo-swap, [aria-hidden='true'], .hero-drawing, pre");
        })
        .slice(0, 5)
        .map((el) => `${el.tagName.toLowerCase()}.${el.className}`.slice(0, 80));
      return { scroll: document.documentElement.scrollWidth - vw, wide };
    });
    expect(overflow.scroll, "page scrolls sideways").toBeLessThanOrEqual(1);
    expect(overflow.wide, "elements outside the viewport").toEqual([]);
    const missingAlt = await page.locator("img:not([alt])").count();
    expect(missingAlt).toBe(0);
    await page.screenshot({ path: `test-results/responsive/landing-${width}.png`, fullPage: true });
  });
}

test("keyboard: skip link first, then the hero actions, with a visible focus ring", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/");
  await page.keyboard.press("Tab");
  await expect(page.locator(".skip-link")).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("#main")).toBeFocused();
  let reached = false;
  for (let i = 0; i < 40 && !reached; i++) {
    await page.keyboard.press("Tab");
    reached = await page.evaluate(() => document.activeElement?.textContent?.trim() === "Open the app");
  }
  expect(reached, "Tab reaches 'Open the app'").toBe(true);
  const ring = await page.evaluate(() => {
    const s = getComputedStyle(document.activeElement!);
    return s.outlineStyle !== "none" && parseFloat(s.outlineWidth) > 0 || s.boxShadow !== "none";
  });
  expect(ring, "focused button shows a focus ring").toBe(true);
});
