import { useId, useRef, useState, type DragEvent } from "react";
import type { AuditResult, Counts, RuleResult, Sample, Status, Verdict } from "./api";
import { STATUS_ICON, VERDICT_ICON } from "./icons";
import { IconUpload } from "./icons";
import {
  STATUS_EXPLANATION,
  STATUS_LABEL,
  VERDICT_LABEL,
  formatBytes,
  issuesOf,
  type ElementSummary,
} from "./results";

export function StatusBadge({ status }: { status: Status }) {
  const Icon = STATUS_ICON[status];
  return (
    <span className={`badge status-${status}`}>
      <Icon />
      {STATUS_LABEL[status]}
    </span>
  );
}

export function VerdictBadge({ verdict }: { verdict: Verdict }) {
  const Icon = VERDICT_ICON[verdict];
  return (
    <span className={`badge verdict-${verdict}`}>
      <Icon />
      {VERDICT_LABEL[verdict]}
    </span>
  );
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
            <dd>{counts[key]}</dd>
          </div>
        );
      })}
    </dl>
  );
}

export function StartPanel(props: {
  samples: Sample[];
  busy: boolean;
  onFile: (file: File) => void;
  onSample: (name: string) => void;
}) {
  const inputId = useId();
  const input = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && !props.busy) props.onFile(file);
  };
  const sampleButtons = [
    { name: "sample_a_mm", label: "Try sample A (mm)" },
    { name: "sample_b_m", label: "Try sample B (m)" },
    { name: "sample_c_no_fireexit_mm", label: "Try sample C (no exit data)" },
  ].filter((b) => props.samples.some((s) => s.name === b.name));

  return (
    <section className="panel start" aria-labelledby={`${inputId}-h`}>
      <h2 id={`${inputId}-h`}>Audit a model</h2>
      <div
        className={dragging ? "dropzone dragging" : "dropzone"}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <IconUpload className="dropzone-icon" />
        <p>Drop an IFC4 file here, or</p>
        <label htmlFor={inputId} className="button primary">Choose .ifc file</label>
        <input
          ref={input}
          id={inputId}
          className="visually-hidden"
          type="file"
          accept=".ifc"
          disabled={props.busy}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) props.onFile(file);
            e.target.value = "";
          }}
        />
        <p className="hint">The file is audited on the NIYAM server and shown in 3D in your browser.</p>
      </div>
      {sampleButtons.length > 0 && (
        <div className="samples">
          <p className="samples-label">Or try a synthetic sample building:</p>
          <div className="button-row">
            {sampleButtons.map((b) => {
              const sample = props.samples.find((s) => s.name === b.name)!;
              return (
                <button key={b.name} type="button" className="button" disabled={props.busy}
                        title={sample.description} onClick={() => props.onSample(b.name)}>
                  {b.label}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </section>
  );
}

export function SummaryCard({ audit, fileName, fileSize }: { audit: AuditResult; fileName: string; fileSize: number }) {
  return (
    <section className="panel summary" aria-labelledby="summary-h">
      <h2 id="summary-h" className="visually-hidden">Audit summary</h2>
      <p className="file-line" title={fileName}>{fileName} <span>· {formatBytes(fileSize)}</span></p>
      <div className="overall" data-testid="overall-status">
        <StatusBadge status={audit.status} />
      </div>
      <p className="explanation">{STATUS_EXPLANATION[audit.status]}</p>
      <CountList counts={audit.summary} />
    </section>
  );
}

function ElementButton(props: {
  rule: RuleResult;
  elementIndex: number;
  selected: boolean;
  onSelect: () => void;
}) {
  const element = props.rule.elements[props.elementIndex]!;
  return (
    <li>
      <button type="button" className={props.selected ? "element selected" : "element"} aria-pressed={props.selected}
              onClick={props.onSelect}>
        <span className="element-head">
          <VerdictBadge verdict={element.verdict} />
          <span className="element-name">{element.name ?? "Unnamed element"}</span>
          <span className="element-class">{element.ifc_class}</span>
        </span>
        <span className="element-reason">{element.reason_plain}</span>
      </button>
    </li>
  );
}

export function RuleList(props: {
  audit: AuditResult;
  summaries: Map<number, ElementSummary>;
  selectedExpressId: number | null;
  onSelect: (expressId: number) => void;
}) {
  return (
    <section className="panel rules" aria-labelledby="rules-h">
      <h2 id="rules-h">Rules</h2>
      <ul className="rule-list">
        {props.audit.rules.map((rule) => {
          const { failed, unchecked } = issuesOf(rule);
          return (
            <li key={rule.unit_id} className="rule" data-testid={`rule-${rule.clause_id}`}>
              <details>
                <summary>
                  <span className="rule-top">
                    <span className="rule-id">{rule.clause_id}</span>
                    <span className="rule-page">p. {rule.page}</span>
                    <StatusBadge status={rule.status} />
                  </span>
                  <span className="rule-text">{rule.rule_text}</span>
                  <CountList counts={rule.counts} compact />
                </summary>
                <div className="rule-body">
                  <h3>Clause text</h3>
                  <blockquote className="clause">{rule.clause_text}</blockquote>
                  {[["Failed", failed], ["Unchecked", unchecked]].map(([label, list]) => {
                    const items = list as typeof failed;
                    return (
                      <div key={label as string}>
                        <h3>{label as string} elements ({items.length})</h3>
                        {items.length === 0 ? <p className="none">None.</p> : (
                          <ul className="element-list">
                            {items.map((e) => (
                              <ElementButton key={e.global_id} rule={rule}
                                             elementIndex={rule.elements.indexOf(e)}
                                             selected={props.selectedExpressId === e.express_id}
                                             onSelect={() => props.onSelect(e.express_id)} />
                            ))}
                          </ul>
                        )}
                      </div>
                    );
                  })}
                </div>
              </details>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

export function DetailPanel(props: {
  summary: ElementSummary | null;
  pickedWithoutRules: { localId: number; globalId: string | null } | null;
  onClose: () => void;
}) {
  if (!props.summary && !props.pickedWithoutRules) {
    return (
      <aside className="panel detail empty" aria-labelledby="detail-h">
        <h2 id="detail-h">Element detail</h2>
        <p>Select an element in the rule list or click it in the 3D view to see why it passed, failed or could not
          be checked.</p>
      </aside>
    );
  }
  if (!props.summary) {
    return (
      <aside className="panel detail" aria-labelledby="detail-h" data-testid="detail-panel">
        <div className="detail-head">
          <h2 id="detail-h">Element detail</h2>
          <button type="button" className="button small" onClick={props.onClose}>Close</button>
        </div>
        <p className="detail-meta"><code>{props.pickedWithoutRules!.globalId ?? `#${props.pickedWithoutRules!.localId}`}</code></p>
        <p>No rules applied to this element.</p>
      </aside>
    );
  }
  const s = props.summary;
  return (
    <aside className="panel detail" aria-labelledby="detail-h" data-testid="detail-panel">
      <div className="detail-head">
        <h2 id="detail-h">{s.name ?? "Unnamed element"}</h2>
        <button type="button" className="button small" onClick={props.onClose}>Close</button>
      </div>
      <p className="detail-meta">{s.ifcClass} · <code>{s.globalId}</code></p>
      <ul className="finding-list">
        {s.findings.map(({ rule, element }) => (
          <li key={rule.unit_id} className="finding">
            <div className="finding-head">
              <span className="rule-id">{rule.clause_id}</span>
              <VerdictBadge verdict={element.verdict} />
            </div>
            <p className="finding-rule">{rule.rule_text}</p>
            {element.reason_plain && <p className="finding-reason">{element.reason_plain}</p>}
            {element.reason_raw && (
              <details className="raw">
                <summary>Technical detail</summary>
                <p>{element.reason_raw}</p>
              </details>
            )}
            <details className="raw">
              <summary>Clause text ({rule.source_doc}, p. {rule.page})</summary>
              <blockquote className="clause">{rule.clause_text}</blockquote>
            </details>
          </li>
        ))}
      </ul>
    </aside>
  );
}

export function Legend() {
  return (
    <ul className="legend" aria-label="3D colour legend">
      {(["failed", "unchecked", "passed", "out_of_scope"] as Verdict[]).map((v) => {
        const Icon = VERDICT_ICON[v];
        return (
          <li key={v}><span className={`swatch swatch-${v}`} aria-hidden="true" /><Icon />{VERDICT_LABEL[v]}</li>
        );
      })}
    </ul>
  );
}
