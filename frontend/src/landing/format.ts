// Formatting for numbers read from site-data.json. Nothing here invents a value: it only renders one.
import type { Rate } from "../data/siteData";

export const pct = (x: number | null) => (x === null ? "n/a" : `${Math.round(x * 100)}%`);

/** "2/68" */
export const frac = (r: Rate) => `${r.k}/${r.n}`;

/** "3% (95% interval 1% to 10%)" */
export const rateWithInterval = (r: Rate) =>
  r.n ? `${pct(r.rate)}, 95% interval ${pct(r.lo)} to ${pct(r.hi)}` : "no shipped rules";

/** "2/68 = 3% [1%, 10%]": the harness's own notation */
export const harness = (r: Rate) => (r.n ? `${r.k}/${r.n} = ${pct(r.rate)} [${pct(r.lo)}, ${pct(r.hi)}]` : `${r.k}/0`);

export const thousands = (n: number) => n.toLocaleString("en-GB");

/** Short model label from "nemotron-3-ultra-550b-a55b (NVIDIA)". */
export function modelLabel(name: string): string {
  if (name.includes("ultra")) return "Nemotron 3 Ultra (550B)";
  if (name.includes("lightning")) return "Nemotron 3.5 Lightning (30B)";
  return name;
}

/** Whether two intervals are clearly apart (one's upper bound below the other's lower bound). */
export const apart = (a: Rate, b: Rate) =>
  a.lo !== null && a.hi !== null && b.lo !== null && b.hi !== null && (a.hi < b.lo || b.hi < a.lo);

export const date = (iso: string) =>
  new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
