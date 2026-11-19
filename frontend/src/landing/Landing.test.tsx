import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { CONTEXT } from "../content/site";
import siteJson from "../data/site-data.json";
import type { SiteData } from "../data/buildSiteData";
import { frac, pct, thousands } from "./format";
import Landing from "./Landing";

const site = siteJson as unknown as SiteData;
const html = renderToStaticMarkup(<Landing />);
const text = html.replace(/<pre[\s\S]*?<\/pre>/g, " ").replace(/<[^>]+>/g, " ").replace(/&[a-z#0-9]+;/g, " ").replace(/\s+/g, " ");

describe("landing page numbers", () => {
  it("shows the headline run's wrong-shipped figures exactly as in site-data.json", () => {
    for (const c of site.headline.all) expect(text).toContain(`${frac(c.wrongShipped)} · ${pct(c.wrongShipped.rate)}`);
    expect(text).toContain(site.headline.provenance.runId);
    expect(text).toContain(`${thousands(site.headline.provenance.calls)} model calls`);
    expect(text).toContain(`${thousands(site.headline.provenance.tokens)} tokens`);
    for (const p of site.headline.paired) expect(text).toContain(`in ${p.gatedOnly} pairs only the gated attempt`);
  });

  it("shows Telangana as counts only, with no rates", () => {
    const section = text.slice(text.indexOf("A second jurisdiction"), text.indexOf("Reality check"));
    expect(section).toContain("too few for rates");
    for (const c of site.telangana.caseStudy) expect(section).toContain(`${c.shippedCorrect} of ${c.repeats}`);
    expect(section).not.toMatch(/\d+%/);
  });

  it("keeps the honest status: the draft badge, and never 'compliant', 'approved', 'accurate' or 'proven'", () => {
    expect(text).toContain("Draft rules, not human-reviewed");
    expect(text).not.toMatch(/\b(compliant|approved|accurate|proven)\b/i);
  });

  it("contains no hand-typed number: every number traces to site-data.json, the content file or a standard's name", () => {
    const allowed = new Set<string>(["0", "25", "50", "75", "100", "95", "2", "3", "1.0", "2.1", "4", "16739"]); // axis, 95% CI, 2D/3D, IDS 1.0, BCF 2.1, IFC4, ISO 16739
    for (let i = 1; i <= 11; i++) allowed.add(String(i).padStart(2, "0")); // sheet numbers A-01..A-11
    const addTokens = (s: string) => (s.match(/\d[\d,.]*\d|\d/g) ?? []).forEach((t) => allowed.add(t));
    const walk = (v: unknown): void => {
      if (typeof v === "number") {
        for (const s of [String(v), thousands(v), thousands(Math.round(v)), String(Math.round(v * 100)), v.toFixed(1), v.toFixed(2), String(Math.round(v))]) allowed.add(s);
      } else if (typeof v === "string") addTokens(v);
      else if (Array.isArray(v)) v.forEach(walk);
      else if (v && typeof v === "object") Object.values(v).forEach(walk);
    };
    walk(site);
    Object.values(CONTEXT).forEach(addTokens);
    const tokens = (text.match(/\d[\d,.]*\d|\d/g) ?? []).map((t) => t.replace(/[.,]$/, ""));
    const stray = [...new Set(tokens.filter((t) => !allowed.has(t)))];
    expect(stray, `numbers on the page with no source: ${stray.join(", ")}`).toEqual([]);
  });
});
