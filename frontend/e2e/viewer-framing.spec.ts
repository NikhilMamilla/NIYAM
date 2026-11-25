// Regression for the 3D view (Phase 13): every sample is framed on load, the camera is outside the model, and the
// verdict colours the side panel reports are visible. No sample shows the "drawn more than 200 m across" notice since
// the millimetre fix (branch fix-mm-units); a deliberately mis-scaled upload still does (last test).
import { expect, test, type Page } from "@playwright/test";
import { hueStats } from "./pixels";

const SHOTS = "../docs/screenshots";
const SAMPLES: { label: RegExp; name: string; implausible: boolean }[] = [
  { label: /Sample A/, name: "sample_a_mm", implausible: false },
  { label: /Sample B/, name: "sample_b_m", implausible: false },
  { label: /Sample C/, name: "sample_c_no_fireexit_mm", implausible: false },
  { label: /Sample D/, name: "sample_d_rooms_stairs_mm", implausible: false },
  { label: /Sample E/, name: "sample_e_rooms_stairs_m", implausible: false },
];

type DebugState = { allCornersInView: boolean; cameraOutsideModel: boolean; near: number; far: number; maxDistance: number };
const state = (page: Page) => page.evaluate(() => (window as unknown as { __niyamViewer: { debugState(): DebugState } }).__niyamViewer.debugState());

test("every sample is framed on load and shows the verdict colours of its summary", async ({ page }) => {
  test.setTimeout(900_000); // five models in one page; D and E take about a minute each here
  await page.goto("/app");
  for (const sample of SAMPLES) {
    if (await page.getByRole("button", { name: "Back" }).count()) await page.getByRole("button", { name: "Back" }).click();
    const response = page.waitForResponse((r) => r.url().endsWith(`/api/samples/${sample.name}/audit`) && r.request().method() === "POST");
    await page.getByRole("button", { name: sample.label }).first().click();
    const audit = await (await response).json();
    const viewport = page.locator(".viewport");
    await expect(viewport).toHaveAttribute("data-view-state", "ready", { timeout: 170_000 });
    await page.waitForTimeout(1200);
    const s = await state(page);
    expect(s.allCornersInView, `${sample.name}: whole model in view`).toBe(true);
    expect(s.cameraOutsideModel, `${sample.name}: camera outside the model`).toBe(true);
    expect(s.far).toBeGreaterThan(s.near * 10);
    expect(await page.evaluate(() => (window as unknown as { __niyamViewer: { debugMisplacedEdges(): Promise<number> } }).__niyamViewer.debugMisplacedEdges()),
      `${sample.name}: room edges belong to their own room`).toBe(0);
    await expect(page.getByTestId("implausible-geometry")).toHaveCount(sample.implausible ? 1 : 0);
    const hues = await hueStats(page, await viewport.screenshot());
    console.log(sample.name, JSON.stringify(hues));
    if (audit.summary.elements.with_failed > 0) expect(hues.red, `${sample.name}: failed elements red`).toBeGreaterThan(200);
    else expect(hues.red, `${sample.name}: nothing red without failures`).toBeLessThan(50);
    if (audit.summary.elements.with_unchecked > 0) expect(hues.amber, `${sample.name}: unchecked elements amber`).toBeGreaterThan(200);
    await viewport.screenshot({ path: `${SHOTS}/viewer-${sample.name}.png` });
  }
});

test("a file whose shapes are stored 1000x too large shows the wrong-unit notice", async ({ page }) => {
  test.setTimeout(300_000);
  await page.goto("/app");
  // the pre-fix sample D: a millimetre project whose rooms and stairs were written in micrometres by mistake
  await page.locator("input[type=file]").setInputFiles("../fixtures/invalid/misscaled_rooms_mm.ifc");
  await expect(page.locator(".viewport")).toHaveAttribute("data-view-state", "ready", { timeout: 170_000 });
  await expect(page.getByTestId("implausible-geometry")).toHaveCount(1);
  await expect(page.getByTestId("implausible-geometry")).toContainText("more than 200 m across");
  const s = await state(page);
  expect(s.allCornersInView).toBe(true);
  await page.waitForTimeout(1200);
  await page.screenshot({ path: `${SHOTS}/viewer-misscaled-upload.png` });
});
