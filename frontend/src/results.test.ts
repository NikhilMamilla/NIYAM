import { describe, expect, it } from "vitest";
import type { AuditResult, ElementResult, RuleResult, Verdict } from "./api";
import { STATUS_LABEL, elementsByExpressId, issuesOf, paintByLocalId, worstVerdict } from "./results";

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
  audit_id: "a", status: "noncompliant", summary: { passed: 0, failed: 0, unchecked: 0, out_of_scope: 0 }, rules,
});

describe("status labels", () => {
  it("names every status in words, never only by colour", () => {
    expect(STATUS_LABEL).toEqual({
      noncompliant: "Non-compliant", incomplete: "Incomplete", compliant: "Compliant", nothing_checked: "Nothing checked",
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
