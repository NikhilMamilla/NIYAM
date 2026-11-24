import { useCallback, useEffect, useId, useMemo, useRef, useState, type DragEvent } from "react";
import type { AuditResult, Counts, RuleResult, RuleStatus, Sample, Verdict } from "./api";
import { Term } from "./glossary";
import Button from "./Button";
import { IconDownload, IconUpload, STATUS_ICON, VERDICT_ICON } from "./icons";
import {
  STATUS_EXPLANATION, STATUS_LABEL, VERDICT_LABEL, formatBytes, issuesOf, plainNoun, plainSummary, type ElementSummary,
} from "./results";

export function StatusBadge({ status, big = false }: { status: RuleStatus; big?: boolean }) {
  const Icon = STATUS_ICON[status];
  return <span className={`badge status-${status}${big ? " big" : ""}`}><Icon />{STATUS_LABEL[status]}</span>;
}

export function VerdictBadge({ verdict }: { verdict: Verdict }) {
  const Icon = VERDICT_ICON[verdict];
  return <span className={`badge verdict-${verdict}`}><Icon />{VERDICT_LABEL[verdict]}</span>;
}

const COUNT_ORDER: (keyof Counts)[] = ["failed", "unchecked", "passed", "out_of_scope"];

export function CountList({ counts, compact = false }: { counts: Counts; compact?: boolean }) {
  return (
    <dl className={compact ? "counts compact" : "counts"}>
      {COUNT_ORDER.map((key) => {
        const Icon = VERDICT_ICON[key];
        return (
          <div key={key} className={`count verdict-${key}`} data-testid={`count-${key}`}>
            <dt><Icon />{VERDICT_LABEL[key]}</dt>
            <dd className="num">{counts[key]}</dd>
          </div>
        );
      })}
    </dl>
  );
}

/** Samples with a one-line plain description each (the files are synthetic test buildings). */
export const SAMPLES: { name: string; label: string; line: string }[] = [
  { name: "sample_a_mm", label: "Sample A", line: "Doors on two floors, in millimetres: some exits too narrow, some revolving." },
  { name: "sample_b_m", label: "Sample B", line: "The same kind of doors, modelled in metres." },
  { name: "sample_c_no_fireexit_mm", label: "Sample C", line: "Doors that do not say whether they are exits: nothing can be decided." },
  { name: "sample_d_rooms_stairs_mm", label: "Sample D", line: "Rooms and stair flights, in millimetres; some lack shape or room type." },
  { name: "sample_e_rooms_stairs_m", label: "Sample E", line: "Rooms and stair flights, in metres." },
];

export function StartPanel(props: { samples: Sample[]; busy: boolean; current: string | null; onFile: (f: File) => void; onSample: (n: string) => void }) {
  const inputId = useId();
  const [dragging, setDragging] = useState(false);
  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && !props.busy) props.onFile(file);
  };
  const available = SAMPLES.filter((s) => props.samples.some((x) => x.name === s.name));
  return (
    <section className="panel start" aria-labelledby={`${inputId}-h`} data-tour="start">
      <h2 id={`${inputId}-h`} className="panel-title">Load a building</h2>
      <div className={dragging ? "dropzone dragging" : "dropzone"}
           onDragOver={(e) => { e.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={onDrop}>
        <IconUpload className="dropzone-icon" />
        <p>Drop an <Term k="IFC">IFC4</Term> file here, or</p>
        <Button as="label" htmlFor={inputId} size="sm" primary>Choose a file</Button>
        <input id={inputId} className="visually-hidden" type="file" accept=".ifc" disabled={props.busy}
               onChange={(e) => { const f = e.target.files?.[0]; if (f) props.onFile(f); e.target.value = ""; }} />
        <p className="hint">Audited on the NIYAM server, drawn in 3D in your browser.</p>
      </div>
      {available.length > 0 && (
        <div className="samples">
          <h3 className="samples-label">Or open a synthetic sample building</h3>
          <ul className="sample-list">
            {available.map((s) => (
              <li key={s.name}>
                <button type="button" className={`sample ${props.current === s.name ? "current" : ""}`} disabled={props.busy}
                        aria-pressed={props.current === s.name} onClick={() => props.onSample(s.name)}>
                  <span className="sample-name">{s.label}</span>
                  <span className="sample-line">{s.line}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

function downloadText(name: string, text: string, type: string) {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function SummaryStrip(props: { audit: AuditResult; fileName: string; fileSize: number; reportUrl: string; bcfUrl: string }) {
  const { audit } = props;
  const s = plainSummary(audit);
  const e = audit.summary.elements;
  return (
    <section className="panel summary" aria-labelledby="summary-h" data-tour="summary">
      <h2 id="summary-h" className="visually-hidden">Audit summary</h2>
      <p className="file-line" title={props.fileName}>{props.fileName} <span>· {formatBytes(props.fileSize)}</span></p>
      <p className="story" data-testid="plain-summary">{s.sentence}</p>
      <div className="overall" data-testid="overall-status" aria-live="polite"><StatusBadge status={audit.status} big /></div>
      <p className="explanation">{STATUS_EXPLANATION[audit.status]}</p>
      <p className="affected" data-testid="elements-affected">
        Distinct elements: <span className="num">{e.with_failed}</span> with violations, <span className="num">{e.with_unchecked}</span> <Term k="unchecked">could not be fully checked</Term>, <span className="num">{e.clean}</span> clean
        {" "}(of <span className="num">{e.total_in_model_of_scoped_classes}</span> the rules apply to)
      </p>
      <details className="disclosure checks">
        <summary>Checks run: one per rule and element</summary>
        <CountList counts={audit.summary.checks} />
      </details>
      <div className="exports" aria-label="Exports">
        <Button as="a" size="sm" href={props.reportUrl} target="_blank" rel="noopener noreferrer" data-testid="open-report"><IconDownload />HTML report</Button>
        <Button as="a" size="sm" href={props.bcfUrl} download data-testid="download-bcf"><IconDownload /><span><Term k="BCF">BCF</Term> issues</span></Button>
        <Button size="sm" data-testid="download-json"
                onClick={() => downloadText(`${props.fileName.replace(/\.ifc$/i, "")}-audit.json`, JSON.stringify(audit, null, 2), "application/json")}>
          <IconDownload />JSON
        </Button>
      </div>
    </section>
  );
}

type Filter = "all" | "issues" | "failed" | "unchecked" | "nothing";
const FILTERS: { key: Filter; label: string; test: (r: RuleResult) => boolean }[] = [
  { key: "all", label: "All", test: () => true },
  { key: "issues", label: "With issues", test: (r) => r.counts.failed + r.counts.unchecked > 0 || r.status === "error" },
  { key: "failed", label: "Broken", test: (r) => r.counts.failed > 0 },
  { key: "unchecked", label: "Not checked", test: (r) => r.counts.unchecked > 0 },
  { key: "nothing", label: "Nothing to check", test: (r) => r.status === "nothing_checked" },
];

export function RuleList(props: { audit: AuditResult; selectedExpressId: number | null; onSelect: (id: number) => void }) {
  const [filter, setFilter] = useState<Filter>("all");
  const [query, setQuery] = useState("");
  const searchId = useId();
  const rules = useMemo(() => {
    const q = query.trim().toLowerCase();
    const f = FILTERS.find((x) => x.key === filter)!;
    return props.audit.rules.filter((r) => f.test(r) && (!q || `${r.clause_id} ${r.rule_text} ${r.clause_text}`.toLowerCase().includes(q)));
  }, [props.audit, filter, query]);
  return (
    <section className="panel rules" aria-labelledby="rules-h" data-tour="rules">
      <div className="rules-head">
        <h2 id="rules-h" className="panel-title">Rules <span className="num">({props.audit.rules.length})</span></h2>
        <label htmlFor={searchId} className="visually-hidden">Search rules</label>
        <input id={searchId} type="search" className="search" placeholder="Search rules" value={query} onChange={(e) => setQuery(e.target.value)} />
      </div>
      <div className="chips" role="group" aria-label="Filter rules">
        {FILTERS.map((f) => (
          <button key={f.key} type="button" className="chip" aria-pressed={filter === f.key} onClick={() => setFilter(f.key)}>
            {f.label} <span className="num">{props.audit.rules.filter(f.test).length}</span>
          </button>
        ))}
      </div>
      {rules.length === 0 && <p className="none">No rule matches this filter.</p>}
      <ul className="rule-list">
        {rules.map((rule) => {
          const { failed, unchecked } = issuesOf(rule);
          return (
            <li key={rule.unit_id} className="rule" data-testid={`rule-${rule.clause_id}`}>
              <details>
                <summary>
                  <span className="rule-top"><span className="rule-id mono">{rule.clause_id}</span><StatusBadge status={rule.status} /></span>
                  <span className="rule-text">{rule.rule_text}</span>
                  <span className="rule-counts">
                    {failed.length > 0 && <span className="mini fail num">{failed.length} broken</span>}
                    {unchecked.length > 0 && <span className="mini warn num">{unchecked.length} not checked</span>}
                    {failed.length + unchecked.length === 0 && <span className="mini">{rule.status === "nothing_checked" ? "nothing in this model to check" : "no issues"}</span>}
                  </span>
                </summary>
                <div className="rule-body">
                  {rule.error && <p className="note" role="alert" data-testid="rule-error">This rule could not be run: {rule.error}. Its elements were not checked; this is not a pass.</p>}
                  {[["Broken", failed], ["Could not be checked", unchecked]].map(([label, list]) => {
                    const items = list as typeof failed;
                    if (!items.length) return null;
                    return (
                      <div key={label as string}>
                        <h3>{label as string} ({items.length})</h3>
                        <ul className="element-list">
                          {items.map((e) => (
                            <li key={e.global_id}>
                              <button type="button" className={props.selectedExpressId === e.express_id ? "element selected" : "element"}
                                      aria-pressed={props.selectedExpressId === e.express_id} onClick={() => props.onSelect(e.express_id)}>
                                <span className="element-head"><VerdictBadge verdict={e.verdict} /><span className="element-name">{e.name ?? "Unnamed element"}</span>
                                  <span className="element-class">{plainNoun(e.ifc_class, 1)}</span></span>
                                <span className="element-reason">{e.reason_plain}</span>
                              </button>
                            </li>
                          ))}
                        </ul>
                      </div>
                    );
                  })}
                  <details className="disclosure clause-x">
                    <summary>Clause text ({rule.source_doc}, page {rule.page})</summary>
                    <blockquote className="clause">{rule.clause_text}</blockquote>
                  </details>
                </div>
              </details>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

/** How to add missing data, from the words of the reason; the readiness IDS lists all of it. */
function missingHint(reason: string | null): string | null {
  if (!reason) return null;
  if (/Category/i.test(reason)) return "Give the room a Pset_SpaceCommon.Category with one of NIYAM's room names (for example Bathroom or Habitable).";
  if (/FireExit/i.test(reason)) return "Set Pset_DoorCommon.FireExit on the door (TRUE for an exit door).";
  if (/width/i.test(reason) && /quantit|Qto/i.test(reason)) return "Add Qto_DoorBaseQuantities.Width to the door.";
  if (/height/i.test(reason) && /quantit|Qto/i.test(reason)) return "Add Qto_DoorBaseQuantities.Height to the door.";
  if (/OccupancyType|occupancy/i.test(reason)) return "Set Pset_BuildingCommon.OccupancyType on the building.";
  if (/geometry|shape/i.test(reason)) return "Export the element with its 3D body geometry.";
  return null;
}

export function DetailPanel(props: {
  summary: ElementSummary | null;
  pickedWithoutRules: { localId: number; globalId: string | null } | null;
  onClose: () => void;
  onDownloadReadiness: () => void;
}) {
  const head = useRef<HTMLHeadingElement>(null);
  useEffect(() => head.current?.focus(), [props.summary, props.pickedWithoutRules]);
  if (!props.summary && !props.pickedWithoutRules) return null;
  if (!props.summary) {
    return (
      <section className="panel detail" aria-labelledby="detail-h" data-testid="detail-panel">
        <div className="detail-head"><h2 id="detail-h" ref={head} tabIndex={-1}>An element no rule looks at</h2>
          <Button size="sm" onClick={props.onClose}>Back to rules</Button></div>
        <p>None of the draft rules applies to this element, so it has no verdict.</p>
        <details className="expert"><summary>Details for experts</summary><p className="mono small">{props.pickedWithoutRules!.globalId ?? `#${props.pickedWithoutRules!.localId}`}</p></details>
      </section>
    );
  }
  const s = props.summary;
  return (
    <section className="panel detail" aria-labelledby="detail-h" data-testid="detail-panel">
      <div className="detail-head">
        <h2 id="detail-h" ref={head} tabIndex={-1}>{s.name ?? "Unnamed element"}</h2>
        <Button size="sm" onClick={props.onClose}>Back to rules</Button>
      </div>
      <p className="detail-meta">{plainNoun(s.ifcClass, 1).replace(/^./, (c) => c.toUpperCase())} · worst result: <VerdictBadge verdict={s.worst} /></p>
      <ul className="finding-list">
        {s.findings.map(({ rule, element }) => {
          const hint = element.verdict === "unchecked" ? missingHint(element.reason_plain) : null;
          return (
            <li key={rule.unit_id} className={`finding v-${element.verdict}`}>
              <div className="finding-head"><span className="rule-id mono">{rule.clause_id}</span><VerdictBadge verdict={element.verdict} /></div>
              <p className="finding-rule">{rule.rule_text}</p>
              {element.reason_plain && <p className="finding-reason">{element.reason_plain}</p>}
              {element.verdict === "unchecked" && (
                <div className="fix">
                  <p><strong>What is missing:</strong> {hint ?? "data this rule needs to decide."} The readiness file lists every item NIYAM's rules need.</p>
                  <Button size="sm" onClick={props.onDownloadReadiness}><IconDownload />Readiness <Term k="IDS">IDS</Term> file</Button>
                </div>
              )}
              <details className="disclosure">
                <summary>Clause text ({rule.source_doc}, page {rule.page})</summary>
                <blockquote className="clause">{rule.clause_text}</blockquote>
              </details>
              {element.reason_raw && (
                <details className="expert"><summary>Details for experts</summary>
                  <p className="small">{element.reason_raw}</p>
                  <p className="small mono">{s.ifcClass} · {s.globalId}</p>
                </details>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}

export function Legend() {
  return (
    <ul className="legend" aria-label="Colour legend for the 3D view">
      {(["failed", "unchecked", "passed", "out_of_scope"] as Verdict[]).map((v) => {
        const Icon = VERDICT_ICON[v];
        return <li key={v}><span className={`swatch swatch-${v}`} aria-hidden="true" /><Icon />{VERDICT_LABEL[v]}</li>;
      })}
    </ul>
  );
}

export function EmptyState({ onSample }: { onSample: (name: string) => void }) {
  return (
    <div className="empty-state" data-testid="empty-state">
      <h2>Check a building model in three steps</h2>
      <ol>
        <li><strong>Load a model.</strong> Upload an IFC4 file, or open one of the synthetic samples on the left.</li>
        <li><strong>Read the verdicts.</strong> Red breaks a rule, amber could not be checked, grey passed. Every verdict has a word and an icon too.</li>
        <li><strong>Ask why.</strong> Select an element to see the rule, the reason and the clause it came from.</li>
      </ol>
      <Button primary onClick={() => onSample("sample_a_mm")}>Open sample A</Button>
    </div>
  );
}

const TOUR = [
  { target: "start", title: "Load a building", text: "Upload your own IFC4 file or open a synthetic sample." },
  { target: "stage", title: "The light table", text: "Your model in 3D, coloured by verdict. Drag to orbit, scroll to zoom, click an element to select it." },
  { target: "summary", title: "The verdict in words", text: "A plain summary first, then the counts and the exports." },
  { target: "rules", title: "Rules", text: "Every draft rule, with its broken and unchecked elements. Filter or search them." },
];
const TOUR_KEY = "niyam.tour.done";

export function Tour({ ready }: { ready: boolean }) {
  const [step, setStep] = useState<number | null>(null);
  useEffect(() => {
    if (!ready) return;
    let done = false;
    try { done = window.localStorage.getItem(TOUR_KEY) === "1"; } catch { done = false; }
    if (!done) setStep(0);
  }, [ready]);
  const finish = useCallback(() => {
    setStep(null);
    try { window.localStorage.setItem(TOUR_KEY, "1"); } catch { /* storage unavailable: the tour shows again next time */ }
  }, []);
  useEffect(() => {
    document.querySelectorAll("[data-tour-active]").forEach((el) => el.removeAttribute("data-tour-active"));
    if (step !== null) document.querySelector(`[data-tour="${TOUR[step]!.target}"]`)?.setAttribute("data-tour-active", "");
  }, [step]);
  useEffect(() => {
    if (step === null) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") finish(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [step, finish]);
  if (step === null) return null;
  const t = TOUR[step]!;
  return (
    <div className="tour" role="dialog" aria-modal="false" aria-labelledby="tour-h" data-testid="tour">
      <p className="tour-step num">{step + 1} of {TOUR.length}</p>
      <div className="tour-copy">
        <h2 id="tour-h">{t.title}</h2>
        <p className="tour-text">{t.text}</p>
      </div>
      <div className="tour-actions">
        <Button size="sm" tone="light" onClick={finish}>Skip the tour</Button>
        <Button size="sm" tone="light" primary onClick={() => (step + 1 < TOUR.length ? setStep(step + 1) : finish())}>
          {step + 1 < TOUR.length ? "Next" : "Done"}
        </Button>
        <button type="button" className="tour-close" aria-label="Close the tour" onClick={finish}>×</button>
      </div>
    </div>
  );
}
