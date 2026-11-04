import { describe, expect, it } from "vitest";
import type { AuditResult, ElementResult, RuleResult, Verdict } from "./api";
import {
  STATUS_LABEL, affectedLine, checksLine, elementsByExpressId, errorRules, issuesOf, paintByLocalId, translucentLocalIds,
  worstVerdict,
} from "./results";

const el = (express_id: number, verdict: Verdict, name = `d${express_id}`): ElementResult => ({
  global_id: `G${express_id}`, express_id, name, ifc_class: "IfcDoor", verdict,
  reason_plain: verdict === "failed" || verdict === "unchecked" ? "why" : null,
  reason_raw: verdict === "failed" || verdict === "unchecked" ? "raw" : null,
});

const rule = (unit_id: string, elements: ElementResult[]): RuleResult => ({
  unit_id, clause_id: unit_id.split("#")[0]!, clause_text: "c", rule_text: "r", source_doc: "MBBL-2016", page: 100,
  severity: "error", human_reviewed: false, status: "noncompliant",
  counts: { passed: 0, failed: 0, unchecked: 0, out_of_scope: 0 }, elements,
});

const audit = (rules: RuleResult[]): AuditResult => ({
  audit_id: "a", status: "noncompliant", rules,
  summary: {
    checks: { passed: 0, failed: 0, unchecked: 0, out_of_scope: 0 },
    elements: { total_in_model_of_scoped_classes: 0, with_failed: 0, with_unchecked: 0, clean: 0 },
    rules_with_errors: 0,
  },
});

describe("status labels", () => {
  it("names every status in words, never only by colour", () => {
    expect(STATUS_LABEL).toEqual({
      noncompliant: "Non-compliant", incomplete: "Incomplete", compliant: "Compliant", nothing_checked: "Nothing checked",
      error: "Could not run",
    });
  });
});

describe("grouping by verdict", () => {
  it("splits a rule's issues into failed and unchecked, in order", () => {
    const r = rule("X#1", [el(1, "passed"), el(2, "failed"), el(3, "unchecked"), el(4, "failed"), el(5, "out_of_scope")]);
    const { failed, unchecked } = issuesOf(r);
    expect(failed.map((e) => e.express_id)).toEqual([2, 4]);
    expect(unchecked.map((e) => e.express_id)).toEqual([3]);
  });

  it("colours an element by its most serious verdict across rules", () => {
    expect(worstVerdict(["passed", "unchecked"])).toBe("unchecked");
    expect(worstVerdict(["out_of_scope", "failed", "unchecked"])).toBe("failed");
    expect(worstVerdict(["out_of_scope", "passed"])).toBe("passed");
    expect(worstVerdict([])).toBeNull();
  });
});

describe("express id mapping", () => {
  const result = audit([
    rule("A#1", [el(10, "passed"), el(11, "out_of_scope"), el(12, "unchecked")]),
    rule("A#2", [el(10, "failed"), el(11, "out_of_scope"), el(12, "passed")]),
  ]);

  it("merges every rule's record for an element under its express id", () => {
    const byId = elementsByExpressId(result);
    expect([...byId.keys()]).toEqual([10, 11, 12]);
    expect(byId.get(10)!.worst).toBe("failed");
    expect(byId.get(10)!.findings.map((f) => f.rule.unit_id)).toEqual(["A#1", "A#2"]);
    expect(byId.get(11)!.worst).toBe("out_of_scope");
    expect(byId.get(12)!.worst).toBe("unchecked");
  });

  it("maps paints onto viewer local ids and reports whether they equal express ids", () => {
    const byId = elementsByExpressId(result);
    const same = paintByLocalId(byId, [10, 11, 12]);
    expect(same.idsMatch).toBe(true);
    expect([...same.paints]).toEqual([[10, "failed"], [11, "out_of_scope"], [12, "unchecked"]]);

    const shifted = paintByLocalId(byId, [110, null, 112]);
    expect(shifted.idsMatch).toBe(false);
    expect(shifted.missing).toBe(1);
    expect(shifted.localByExpress.get(10)).toBe(110);
    expect(shifted.paints.get(112)).toBe("unchecked");
    expect(shifted.paints.has(11)).toBe(false);
  });
});

describe("summary card wording", () => {
  it("labels rule x element checks as checks, and distinct elements by their class", () => {
    const a = audit([rule("A#1", [el(1, "failed"), el(2, "unchecked")])]);
    a.summary = {
      checks: { passed: 17, failed: 6, unchecked: 7, out_of_scope: 6 },
      elements: { total_in_model_of_scoped_classes: 12, with_failed: 5, with_unchecked: 3, clean: 4 },
      rules_with_errors: 0,
    };
    expect(checksLine(a)).toBe("Checks run: passed 17, failed 6, unchecked 7");
    expect(affectedLine(a)).toBe("Doors affected: 5 with violations, 3 could not be fully checked");
    a.rules[0]!.elements.push({ ...el(3, "passed"), ifc_class: "IfcSpace" });
    expect(affectedLine(a)).toBe("Elements affected: 5 with violations, 3 could not be fully checked");
  });
});

describe("spaces and rule errors", () => {
  it("draws only IfcSpace elements translucent, by viewer local id", () => {
    const space = { ...el(5, "failed"), ifc_class: "IfcSpace" };
    const byId = elementsByExpressId(audit([rule("G#1", [space, el(6, "passed")])]));
    const mapped = paintByLocalId(byId, [105, 106]);
    expect([...translucentLocalIds(byId, mapped.localByExpress)]).toEqual([105]);
  });

  it("lists the rules that could not run, with their reason", () => {
    const broken = { ...rule("G#2", []), status: "error" as const, error: "the check timed out after 60 s" };
    const a = audit([rule("G#1", [el(1, "passed")]), broken]);
    expect(errorRules(a).map((r) => [r.unit_id, r.error])).toEqual([["G#2", "the check timed out after 60 s"]]);
  });
});
