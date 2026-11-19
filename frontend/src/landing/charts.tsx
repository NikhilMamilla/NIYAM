// Hand-built SVG charts. Every mark is reachable by keyboard and states its exact k/n and interval;
// every chart also has a plain table of the same numbers behind a disclosure.
import { useId, useState, type ReactNode } from "react";
import type { Rate } from "../data/siteData";
import { frac, harness, pct } from "./format";

export interface ForestRow {
  key: string;
  group: string;      // e.g. model
  label: string;      // e.g. "With the gate"
  rate: Rate;
  tone: "gated" | "ungated";
}

const TICKS = [0, 0.25, 0.5, 0.75, 1];

/** A forest plot: one row per estimate, a dot at the rate, a bar for the 95% Wilson interval, k/n at the right. */
export function ForestChart({ rows, title, unit }: { rows: ForestRow[]; title: string; unit: string }) {
  const titleId = useId();
  const [active, setActive] = useState<string | null>(null);
  const W = 640, left = 210, right = 92, rowH = 34, top = 26;
  const plotW = W - left - right;
  const groups = [...new Set(rows.map((r) => r.group))];
  let y = top;
  const placed: (ForestRow & { y: number })[] = [];
  const groupY: { g: string; y: number }[] = [];
  for (const g of groups) {
    groupY.push({ g, y: y + 4 });
    y += 22;
    for (const r of rows.filter((x) => x.group === g)) {
      placed.push({ ...r, y: y + rowH / 2 });
      y += rowH;
    }
    y += 10;
  }
  const H = y + 8;
  const x = (v: number) => left + v * plotW;
  return (
    <figure className="chart">
      <svg viewBox={`0 0 ${W} ${H}`} role="group" aria-labelledby={titleId} className="chart-svg">
        <title id={titleId}>{title}</title>
        {TICKS.map((t) => (
          <g key={t}>
            <line x1={x(t)} x2={x(t)} y1={top - 8} y2={H - 8} className="grid" />
            <text x={x(t)} y={top - 12} className="tick" textAnchor="middle">{pct(t)}</text>
          </g>
        ))}
        {groupY.map(({ g, y: gy }) => <text key={g} x={8} y={gy + 12} className="group-label">{g}</text>)}
        {placed.map((r) => {
          const has = r.rate.n > 0 && r.rate.lo !== null && r.rate.hi !== null && r.rate.rate !== null;
          const label = `${r.group}, ${r.label}: ${harness(r.rate)} ${unit}`;
          return (
            <g key={r.key} className={`row ${r.tone} ${active === r.key ? "active" : ""}`} tabIndex={0} role="img" aria-label={label}
               onMouseEnter={() => setActive(r.key)} onMouseLeave={() => setActive(null)}
               onFocus={() => setActive(r.key)} onBlur={() => setActive(null)}>
              <rect x={0} y={r.y - rowH / 2} width={W} height={rowH} className="row-hit" />
              <text x={24} y={r.y + 5} className="row-label">{r.label}</text>
              {has && (
                <>
                  <line x1={x(r.rate.lo!)} x2={x(r.rate.hi!)} y1={r.y} y2={r.y} className="interval" />
                  <line x1={x(r.rate.lo!)} x2={x(r.rate.lo!)} y1={r.y - 6} y2={r.y + 6} className="interval" />
                  <line x1={x(r.rate.hi!)} x2={x(r.rate.hi!)} y1={r.y - 6} y2={r.y + 6} className="interval" />
                  <circle cx={x(r.rate.rate!)} cy={r.y} r={6} className="point" />
                </>
              )}
              <text x={W - 6} y={r.y + 5} textAnchor="end" className="row-value">{has ? `${frac(r.rate)} · ${pct(r.rate.rate)}` : "none shipped"}</text>
              {active === r.key && has && (
                <text x={x(r.rate.hi!) + 10 > W - right - 60 ? x(r.rate.lo!) - 10 : x(r.rate.hi!) + 10} y={r.y - 9}
                      textAnchor={x(r.rate.hi!) + 10 > W - right - 60 ? "end" : "start"} className="row-tip">
                  {pct(r.rate.lo)} to {pct(r.rate.hi)}
                </text>
              )}
            </g>
          );
        })}
      </svg>
      <NumbersTable caption={title} head={["Model", "Condition", unit, "Rate", "95% interval"]}
                    rows={rows.map((r) => [r.group, r.label, frac(r.rate), pct(r.rate.rate), r.rate.n ? `${pct(r.rate.lo)} to ${pct(r.rate.hi)}` : "n/a"])} />
    </figure>
  );
}

/** Two-part bars: units whose outcome was identical in every repeat versus units that varied. */
export function StabilityChart({ rows, title }: { rows: { key: string; label: string; stable: number; varied: number }[]; title: string }) {
  const titleId = useId();
  const W = 640, left = 210, right = 70, rowH = 30, top = 8;
  const plotW = W - left - right;
  const H = top + rows.length * rowH + 30;
  return (
    <figure className="chart">
      <svg viewBox={`0 0 ${W} ${H}`} role="group" aria-labelledby={titleId} className="chart-svg">
        <title id={titleId}>{title}</title>
        {rows.map((r, i) => {
          const total = r.stable + r.varied;
          const y = top + i * rowH;
          const ws = (r.stable / total) * plotW;
          return (
            <g key={r.key} tabIndex={0} role="img" className="row" aria-label={`${r.label}: ${r.stable} of ${total} units identical in every repeat, ${r.varied} varied`}>
              <text x={8} y={y + 19} className="row-label">{r.label}</text>
              <rect x={left} y={y + 6} width={ws} height={18} className="bar-stable" />
              <rect x={left + ws} y={y + 6} width={plotW - ws} height={18} className="bar-varied" />
              <text x={W - 6} y={y + 19} textAnchor="end" className="row-value">{r.stable} / {total}</text>
            </g>
          );
        })}
        <g transform={`translate(${left}, ${H - 14})`} className="legend-svg">
          <rect width={12} height={12} y={-10} className="bar-stable" /><text x={18} y={0}>same outcome in every repeat</text>
          <rect x={250} width={12} height={12} y={-10} className="bar-varied" /><text x={268} y={0}>varied</text>
        </g>
      </svg>
      <NumbersTable caption={title} head={["Model and mode", "Identical", "Varied", "Units"]}
                    rows={rows.map((r) => [r.label, String(r.stable), String(r.varied), String(r.stable + r.varied)])} />
    </figure>
  );
}

/** Paired outcomes on the same unit and repeat: gated vs ungated, as four counted segments per model. */
export function PairedChart({ rows, title }: {
  rows: { key: string; label: string; bothCorrect: number; gatedOnly: number; ungatedOnly: number; neither: number }[]; title: string;
}) {
  const titleId = useId();
  const parts = [
    { key: "bothCorrect", label: "both right", cls: "seg-both" },
    { key: "gatedOnly", label: "only with the gate", cls: "seg-gated" },
    { key: "ungatedOnly", label: "only without the gate", cls: "seg-ungated" },
    { key: "neither", label: "neither", cls: "seg-neither" },
  ] as const;
  const W = 640, left = 210, right = 10, rowH = 34;
  const plotW = W - left - right;
  const H = rows.length * rowH + 44;
  return (
    <figure className="chart">
      <svg viewBox={`0 0 ${W} ${H}`} role="group" aria-labelledby={titleId} className="chart-svg">
        <title id={titleId}>{title}</title>
        {rows.map((r, i) => {
          const total = parts.reduce((s, p) => s + r[p.key], 0);
          let x = left;
          const y = 8 + i * rowH;
          return (
            <g key={r.key} tabIndex={0} role="img" className="row"
               aria-label={`${r.label}: ${parts.map((p) => `${r[p.key]} ${p.label}`).join(", ")}, of ${total}`}>
              <text x={8} y={y + 19} className="row-label">{r.label}</text>
              {parts.map((p) => {
                const w = (r[p.key] / total) * plotW;
                const el = (
                  <g key={p.key}>
                    <rect x={x} y={y + 4} width={w} height={22} className={p.cls} />
                    {w > 22 && <text x={x + w / 2} y={y + 19} textAnchor="middle" className={`seg-text ${p.cls}-text`}>{r[p.key]}</text>}
                  </g>
                );
                x += w;
                return el;
              })}
            </g>
          );
        })}
        <g transform={`translate(${left}, ${H - 12})`} className="legend-svg">
          {parts.map((p, i) => (
            <g key={p.key} transform={`translate(${[0, 84, 224, 370][i]}, 0)`}><rect width={12} height={12} y={-10} className={p.cls} /><text x={16} y={0}>{p.label}</text></g>
          ))}
        </g>
      </svg>
      <NumbersTable caption={title} head={["Model", ...parts.map((p) => p.label)]}
                    rows={rows.map((r) => [r.label, ...parts.map((p) => String(r[p.key]))])} />
    </figure>
  );
}

export function NumbersTable({ caption, head, rows }: { caption: string; head: string[]; rows: ReactNode[][] }) {
  return (
    <details className="disclosure numbers">
      <summary>Show the numbers</summary>
      <div className="table-wrap">
        <table className="data-table">
          <caption className="visually-hidden">{caption}</caption>
          <thead><tr>{head.map((h) => <th key={h} scope="col">{h}</th>)}</tr></thead>
          <tbody>{rows.map((r, i) => <tr key={i}>{r.map((c, j) => (j === 0 ? <th key={j} scope="row">{c}</th> : <td key={j} className="num">{c}</td>))}</tr>)}</tbody>
        </table>
      </div>
    </details>
  );
}
