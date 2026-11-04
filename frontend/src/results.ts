// Pure logic over the audit JSON: labels, grouping, and mapping results onto model element ids.
import type { AuditResult, ElementResult, RuleResult, RuleStatus, Status, Verdict } from "./api";

export type Paint = Verdict;

export const STATUS_LABEL: Record<RuleStatus, string> = {
  error: "Could not run",
  noncompliant: "Non-compliant",
  incomplete: "Incomplete",
  compliant: "Compliant",
  nothing_checked: "Nothing checked",
};

export const STATUS_EXPLANATION: Record<Status, string> = {
  noncompliant: "At least one element breaks a rule.",
  incomplete: "No element breaks a rule, but some elements could not be checked because required data is missing.",
  compliant: "Every element in scope was checked and none breaks a rule.",
  nothing_checked: "No element in the model is in scope of any rule, so nothing was checked.",
};

export const VERDICT_LABEL: Record<Verdict, string> = {
  failed: "Failed",
  unchecked: "Unchecked",
  passed: "Passed",
  out_of_scope: "Out of scope",
};

// When one element has different verdicts under different rules, the most serious one colours it.
const SEVERITY: Verdict[] = ["failed", "unchecked", "passed", "out_of_scope"];

export function worstVerdict(verdicts: Verdict[]): Verdict | null {
  return SEVERITY.find((v) => verdicts.includes(v)) ?? null;
}

export function issuesOf(rule: RuleResult): { failed: ElementResult[]; unchecked: ElementResult[] } {
  return {
    failed: rule.elements.filter((e) => e.verdict === "failed"),
    unchecked: rule.elements.filter((e) => e.verdict === "unchecked"),
  };
}

export interface ElementFinding {
  rule: RuleResult;
  element: ElementResult;
}

export interface ElementSummary {
  expressId: number;
  globalId: string;
  name: string | null;
  ifcClass: string;
  worst: Verdict;
  findings: ElementFinding[];
}

/** One entry per element that any rule looked at, keyed by its express id in the audited file. */
export function elementsByExpressId(audit: AuditResult): Map<number, ElementSummary> {
  const byId = new Map<number, ElementSummary>();
  for (const rule of audit.rules) {
    for (const element of rule.elements) {
      const entry = byId.get(element.express_id) ?? {
        expressId: element.express_id,
        globalId: element.global_id,
        name: element.name,
        ifcClass: element.ifc_class,
        worst: element.verdict,
        findings: [],
      };
      entry.findings.push({ rule, element });
      entry.worst = worstVerdict(entry.findings.map((f) => f.element.verdict)) ?? element.verdict;
      byId.set(element.express_id, entry);
    }
  }
  return byId;
}

/**
 * Map audit results onto the viewer's local ids. The audit reports express ids; the viewer's local ids are
 * looked up by GlobalId, so the mapping is correct even if a loader numbers items differently.
 * Returns the paint per local id plus whether local ids equal express ids (reported for diagnostics).
 */
export function paintByLocalId(
  summaries: Map<number, ElementSummary>,
  localIds: (number | null)[],
): { paints: Map<number, Paint>; localByExpress: Map<number, number>; idsMatch: boolean; missing: number } {
  const entries = [...summaries.values()];
  const paints = new Map<number, Paint>();
  const localByExpress = new Map<number, number>();
  let idsMatch = true;
  let missing = 0;
  entries.forEach((entry, i) => {
    const local = localIds[i];
    if (local === null || local === undefined) {
      missing += 1;
      return;
    }
    paints.set(local, entry.worst);
    localByExpress.set(entry.expressId, local);
    if (local !== entry.expressId) idsMatch = false;
  });
  return { paints, localByExpress, idsMatch, missing };
}

export function checksLine(audit: AuditResult): string {
  const c = audit.summary.checks;
  return `Checks run: passed ${c.passed}, failed ${c.failed}, unchecked ${c.unchecked}`;
}

export function affectedLine(audit: AuditResult): string {
  const classes = new Set(audit.rules.flatMap((r) => r.elements.map((e) => e.ifc_class)));
  const noun = classes.size === 1 && classes.has("IfcDoor") ? "Doors" : "Elements";
  const e = audit.summary.elements;
  return `${noun} affected: ${e.with_failed} with violations, ${e.with_unchecked} could not be fully checked`;
}

/** Viewer local ids of IfcSpace elements: rooms are volumes, so they are drawn translucent to keep doors visible. */
export function translucentLocalIds(
  summaries: Map<number, ElementSummary>,
  localByExpress: Map<number, number>,
): Set<number> {
  const ids = new Set<number>();
  for (const s of summaries.values()) {
    const local = localByExpress.get(s.expressId);
    if (s.ifcClass === "IfcSpace" && local !== undefined) ids.add(local);
  }
  return ids;
}

export function errorRules(audit: AuditResult): RuleResult[] {
  return audit.rules.filter((r) => r.status === "error");
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export const LARGE_MODEL_BYTES = 30 * 1024 * 1024;
