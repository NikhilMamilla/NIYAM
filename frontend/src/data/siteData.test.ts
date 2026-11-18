import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { RUNS, buildSiteData } from "./buildSiteData.ts";
import { parseCsv, wilson, type Rate } from "./siteData.ts";
import committed from "./site-data.json";

const ROOT = join(__dirname, "..", "..", "..");
const data = buildSiteData(ROOT);
const csv = (run: string, file: string) => parseCsv(readFileSync(join(ROOT, "eval", "results", run, file), "utf-8"));
const close = (a: number | null, b: string) => (b === "" ? a === null : Math.abs((a ?? NaN) - Number(b)) < 1e-9);

function expectRate(r: Rate | null, row: Record<string, string>, prefix: string) {
  expect(r, prefix).not.toBeNull();
  expect(String(r!.k)).toBe(row[`${prefix}_k`]);
  expect(String(r!.n)).toBe(row[`${prefix}_n`]);
  expect(close(r!.lo, row[`${prefix}_lo`]!), `${prefix} lo`).toBe(true);
  expect(close(r!.hi, row[`${prefix}_hi`]!), `${prefix} hi`).toBe(true);
}

describe("site data", () => {
  it("is current: the committed site-data.json equals a fresh build from the committed result files", () => {
    expect(JSON.parse(JSON.stringify(data))).toEqual(committed);
  });

  it("Wilson intervals equal the Python harness's (k=2, n=68 from run 2)", () => {
    expect(wilson(2, 68)).toEqual([0.008103179543, 0.101046313652]);
    expect(wilson(0, 0)).toBeNull();
  });

  for (const [label, run, view] of [["headline", RUNS.headline, data.headline], ["pilot", RUNS.pilot, data.pilot]] as const) {
    it(`${label} run: every item-level cell equals summary.csv (all units and distinct rules)`, () => {
      const rows = csv(run, "summary.csv");
      for (const [viewName, cells] of [["all_units", view.all], ["distinct_rules", view.distinct]] as const) {
        for (const cell of cells) {
          const row = rows.find((r) => r.view === viewName && r.model === cell.model && r.mode === cell.mode)!;
          expect(row, `${viewName} ${cell.model} ${cell.mode}`).toBeDefined();
          expect(String(cell.n)).toBe(row.n);
          expectRate(cell.valid, row, "valid");
          expectRate(cell.heldoutCorrect, row, "heldout_correct");
          expectRate(cell.shipped, row, "shipped");
          expectRate(cell.wrongShipped, row, "wrong_shipped");
          if (cell.needsHuman) expectRate(cell.needsHuman, row, "needs_human");
        }
      }
    });
  }

  it("headline run: unit-level wrong_shipped and stability equal slides-data.csv", () => {
    const rows = csv(RUNS.headline, "slides-data.csv");
    for (const [viewName, list] of [["all_units", data.headline.unitsAll], ["distinct_rules", data.headline.unitsDistinct]] as const) {
      for (const u of list) {
        const w = rows.find((r) => r.view === viewName && r.model === u.model && r.mode === u.mode && r.group === "unit_wrong_shipped")!;
        expect([String(u.wrongShippedUnits.k), String(u.wrongShippedUnits.n)]).toEqual([w.k, w.n]);
        expect(close(u.wrongShippedUnits.lo, w.wilson_lo!) && close(u.wrongShippedUnits.hi, w.wilson_hi!)).toBe(true);
        const s = rows.find((r) => r.view === viewName && r.model === u.model && r.mode === u.mode && r.group === "stability")!;
        expect([String(u.stable), String(u.units)]).toEqual([s.k, s.n]);
      }
    }
  });

  it("headline run: the paired table and post-hoc rows equal summary.md", () => {
    const md = readFileSync(join(ROOT, "eval", "results", RUNS.headline, "summary.md"), "utf-8");
    for (const p of data.headline.paired) {
      expect(md).toContain(`| ${p.model} | ${p.bothCorrect} | ${p.gatedOnly} | ${p.ungatedOnly} | ${p.neither} |`);
    }
    const ultraGated = data.headline.posthoc.all.find((c) => c.model.startsWith("nemotron-3-ultra") && c.mode === "gated")!;
    expect(md).toContain(`| all units | ${ultraGated.model} | gated | ${ultraGated.n} | ${ultraGated.heldoutCorrect.k}/${ultraGated.heldoutCorrect.n} =`);
  });

  it("Telangana is a counts-only case study of 2 units", () => {
    expect(data.telangana.unitsInRun).toBe(2);
    const md = readFileSync(join(ROOT, "eval", "results", RUNS.telangana, "summary.md"), "utf-8");
    for (const c of data.telangana.caseStudy) {
      expect(md).toContain(`| ${c.unit} | ${c.model} | ${c.mode} | ${c.repeats} | ${c.shipped} | ${c.shippedCorrect} |`);
    }
  });

  it("unit inventory matches the review sheet: 27 units, 3 duplicates, both sources", () => {
    expect(data.units.total).toBe(27);
    expect(data.units.duplicates).toEqual(["MBBL2016-4.24.7.2#b", "MBBL2016-4.24.7.2#c", "MBBL2016-4.24.7.2#f"]);
    expect(data.units.bySource).toEqual({ MBBL2016: 25, TGBR2012: 2 });
    expect(data.corpus).toEqual({ MBBL2016: 445, TGBR2012: 55 });
    expect(data.readiness.map((r) => r.name)).toContain("Spaces declare a profile Category");
  });
});
