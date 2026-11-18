// Site data: every number the landing page and dashboard show, computed from committed result files.
// A port of backend/app/eval/metrics.py; src/data/siteData.test.ts checks it against the CSVs the Python harness wrote.

export const Z95 = 1.959963984540054;

export interface Rate {
  k: number;
  n: number;
  rate: number | null;
  lo: number | null;
  hi: number | null;
}

const round12 = (x: number) => Math.round(x * 1e12) / 1e12;

/** Wilson score interval, rounded like the Python harness; null when n is 0. */
export function wilson(k: number, n: number, z = Z95): [number, number] | null {
  if (n === 0) return null;
  const p = k / n;
  const denom = 1 + (z * z) / n;
  const centre = (p + (z * z) / (2 * n)) / denom;
  const half = (z * Math.sqrt((p * (1 - p)) / n + (z * z) / (4 * n * n))) / denom;
  return [round12(Math.max(0, centre - half)), round12(Math.min(1, centre + half))];
}

export function rate(k: number, n: number): Rate {
  const w = wilson(k, n);
  return { k, n, rate: n ? k / n : null, lo: w ? w[0] : null, hi: w ? w[1] : null };
}

export interface Item {
  model: string;
  mode: "gated" | "ungated";
  unit_id: string;
  tier: string;
  template?: string;
  repeat: number;
  outcome: string;
  shipped: boolean;
  repair_rounds: number;
  total_tokens: number;
  wall_time_s: number;
  score: { valid: boolean; dev_correct: boolean; heldout_correct: boolean };
}

export interface Cell {
  model: string;
  mode: string;
  n: number;
  valid: Rate;
  devCorrect: Rate;
  heldoutCorrect: Rate;
  shipped: Rate;
  wrongShipped: Rate;
  needsHuman: Rate | null;
  meanRepairs: number | null;
  meanTokens: number | null;
  meanWallS: number | null;
}

const mean = (xs: number[]) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null);

export function cellMetrics(model: string, mode: string, items: Item[]): Cell {
  const shipped = items.filter((i) => i.shipped);
  const gated = mode === "gated";
  return {
    model, mode, n: items.length,
    valid: rate(items.filter((i) => i.score.valid).length, items.length),
    devCorrect: rate(items.filter((i) => i.score.dev_correct).length, items.length),
    heldoutCorrect: rate(items.filter((i) => i.score.heldout_correct).length, items.length),
    shipped: rate(shipped.length, items.length),
    wrongShipped: rate(shipped.filter((i) => !i.score.heldout_correct).length, shipped.length),
    needsHuman: gated ? rate(items.filter((i) => i.outcome === "needs_human").length, items.length) : null,
    meanRepairs: gated ? mean(items.map((i) => i.repair_rounds)) : null,
    meanTokens: mean(items.map((i) => i.total_tokens)),
    meanWallS: mean(items.map((i) => i.wall_time_s)),
  };
}

export function groupBy<T>(items: T[], key: (t: T) => string): Map<string, T[]> {
  const out = new Map<string, T[]>();
  for (const i of items) {
    const k = key(i);
    out.set(k, [...(out.get(k) ?? []), i]);
  }
  return new Map([...out].sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0)));
}

const correctShipped = (i: Item) => i.shipped && i.score.heldout_correct;

export interface UnitView {
  model: string;
  mode: string;
  units: number;
  stable: number;
  varied: number;
  wrongShippedUnits: Rate;
  /** unit -> [repeats that shipped a held-out-correct rule, repeats] */
  shares: Record<string, [number, number]>;
}

export function unitView(model: string, mode: string, items: Item[]): UnitView {
  const units = groupBy(items, (i) => i.unit_id);
  let stable = 0;
  let wrong = 0;
  let shippedUnits = 0;
  const shares: Record<string, [number, number]> = {};
  for (const [unit, group] of units) {
    if (new Set(group.map((i) => `${i.shipped}/${i.score.heldout_correct}`)).size === 1) stable += 1;
    if (group.some((i) => i.shipped)) {
      shippedUnits += 1;
      if (group.some((i) => i.shipped && !i.score.heldout_correct)) wrong += 1;
    }
    shares[unit] = [group.filter(correctShipped).length, group.length];
  }
  return { model, mode, units: units.size, stable, varied: units.size - stable, wrongShippedUnits: rate(wrong, shippedUnits), shares };
}

export interface PairedRow { model: string; bothCorrect: number; gatedOnly: number; ungatedOnly: number; neither: number }

export function paired(items: Item[]): PairedRow[] {
  const rows = new Map<string, PairedRow>();
  for (const [, pair] of groupBy(items, (i) => `${i.model}\u0000${i.unit_id}\u0000${i.repeat}`)) {
    const g = pair.find((i) => i.mode === "gated");
    const u = pair.find((i) => i.mode === "ungated");
    if (!g || !u) continue;
    const row = rows.get(g.model) ?? { model: g.model, bothCorrect: 0, gatedOnly: 0, ungatedOnly: 0, neither: 0 };
    const [a, b] = [correctShipped(g), correctShipped(u)];
    if (a && b) row.bothCorrect += 1;
    else if (a) row.gatedOnly += 1;
    else if (b) row.ungatedOnly += 1;
    else row.neither += 1;
    rows.set(g.model, row);
  }
  return [...rows.values()].sort((x, y) => (x.model < y.model ? -1 : 1));
}

export interface RunMeta {
  run_id: string;
  date: string;
  dry_run: boolean;
  git_commit: string;
  rulepack_hash: string;
  models: { name: string; role: string; model?: string | null }[];
  request_extras?: Record<string, Record<string, unknown>>;
  temperature: number;
  max_repairs: number;
  repeats: number;
  used: { calls: number; tokens: number };
  stopped_early: string | null;
  skipped_models?: Record<string, string>;
}

export interface Results { meta: RunMeta; items: Item[] }

export const POSTHOC_EXCLUDED = ["MBBL2016-4.8.2#1", "MBBL2016-5.4.1#b2"];

/** Everything one run contributes: cells (all units and distinct rules), unit views, tiers, pairs, post-hoc. */
export function runView(results: Results, duplicates: Set<string>) {
  const { meta, items } = results;
  const distinct = items.filter((i) => !duplicates.has(i.unit_id));
  const cells = (xs: Item[]) => [...groupBy(xs, (i) => `${i.model}\u0000${i.mode}`)].map(([k, g]) => {
    const [model, mode] = k.split("\u0000") as [string, string];
    return cellMetrics(model, mode, g);
  });
  const units = (xs: Item[]) => [...groupBy(xs, (i) => `${i.model}\u0000${i.mode}`)].map(([k, g]) => {
    const [model, mode] = k.split("\u0000") as [string, string];
    return unitView(model, mode, g);
  });
  const tiers = [...groupBy(items, (i) => `${i.model}\u0000${i.mode}\u0000${i.tier}`)].map(([k, g]) => {
    const [model, mode, tier] = k.split("\u0000") as [string, string, string];
    return { tier, ...cellMetrics(model, mode, g) };
  });
  const kept = items.filter((i) => !POSTHOC_EXCLUDED.includes(i.unit_id));
  return {
    provenance: {
      runId: meta.run_id, date: meta.date, commit: meta.git_commit, dryRun: meta.dry_run, rulepackHash: meta.rulepack_hash,
      models: meta.models.map((m) => ({ name: m.name, id: m.model ?? null, role: m.role })),
      requestExtras: meta.request_extras ?? {}, temperature: meta.temperature, maxRepairs: meta.max_repairs,
      repeats: meta.repeats, calls: meta.used.calls, tokens: meta.used.tokens, stoppedEarly: meta.stopped_early,
      skippedModels: meta.skipped_models ?? {},
    },
    unitsInRun: new Set(items.map((i) => i.unit_id)).size,
    items: items.length,
    all: cells(items),
    distinct: cells(distinct),
    unitsAll: units(items),
    unitsDistinct: units(distinct),
    tiers,
    paired: paired(items),
    posthoc: { excluded: POSTHOC_EXCLUDED, all: cells(kept), units: units(kept) },
  };
}

/** Case study: counts per unit, model and mode, no rates (fewer than 5 units). */
export function caseStudy(results: Results) {
  return [...groupBy(results.items, (i) => `${i.unit_id}\u0000${i.model}\u0000${i.mode}`)].map(([k, g]) => {
    const [unit, model, mode] = k.split("\u0000") as [string, string, string];
    const outcomes: Record<string, number> = {};
    for (const i of g) outcomes[i.outcome] = (outcomes[i.outcome] ?? 0) + 1;
    return { unit, model, mode, repeats: g.length, shipped: g.filter((i) => i.shipped).length,
      shippedCorrect: g.filter(correctShipped).length, outcomes };
  });
}

/** RFC 4180 CSV (quoted fields may contain commas, quotes and newlines). */
export function parseCsv(text: string): Record<string, string>[] {
  const rows: string[][] = [];
  let row: string[] = [];
  let field = "";
  let quoted = false;
  const src = text.replace(/^﻿/, "");
  for (let i = 0; i < src.length; i++) {
    const c = src[i]!;
    if (quoted) {
      if (c === '"' && src[i + 1] === '"') { field += '"'; i++; } else if (c === '"') quoted = false; else field += c;
    } else if (c === '"') quoted = true;
    else if (c === ",") { row.push(field); field = ""; }
    else if (c === "\n" || c === "\r") {
      if (c === "\r" && src[i + 1] === "\n") i++;
      row.push(field); rows.push(row); row = []; field = "";
    } else field += c;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  const [header, ...body] = rows.filter((r) => r.length > 1 || r[0]);
  return body.map((r) => Object.fromEntries(header!.map((h, i) => [h, r[i] ?? ""])));
}

/** Rows of the first markdown table that follows `heading` in a document. */
export function markdownTable(md: string, heading: string): string[][] {
  const start = md.indexOf(heading);
  if (start < 0) return [];
  const lines = md.slice(start).split(/\r?\n/);
  const first = lines.findIndex((l) => l.trim().startsWith("|"));
  const out: string[][] = [];
  for (const line of lines.slice(first)) {
    if (!line.trim().startsWith("|")) break;
    const cells = line.trim().slice(1, -1).split("|").map((c) => c.trim());
    if (cells.every((c) => /^-+$/.test(c))) continue;
    out.push(cells);
  }
  return out;
}

const decodeXml = (s: string) => s.replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&");

/** Specification names and instructions of an IDS file (enough to list the readiness requirements). */
export function idsSpecifications(xml: string): { name: string; instructions: string; enables: string[] }[] {
  return [...xml.matchAll(/<(?:ids:)?specification\b([^>]*)>/g)].map(([, attrs]) => {
    const attr = (n: string) => decodeXml(attrs!.match(new RegExp(`\\b${n}="([^"]*)"`))?.[1] ?? "");
    const instructions = attr("instructions");
    return { name: attr("name"), instructions, enables: instructions.match(/(?:MBBL2016|TGBR2012)-[\w.]+#\w+/g) ?? [] };
  });
}
