import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const SAMPLES = fileURLToPath(new URL("../../fixtures/samples", import.meta.url));

type TruthElement = { expected: Record<string, string> };
type Truth = { doors?: TruthElement[]; spaces?: TruthElement[]; stairs?: TruthElement[] };

/** Expected summary computed from the hand-written truth file, independently of the audit engine. */
export function expectedFromTruth(name: string) {
  const truth = JSON.parse(readFileSync(`${SAMPLES}/${name}.truth.json`, "utf-8")) as Truth;
  const elements = [...(truth.doors ?? []), ...(truth.spaces ?? []), ...(truth.stairs ?? [])];
  const checks: Record<string, number> = { passed: 0, failed: 0, unchecked: 0, out_of_scope: 0 };
  let withFailed = 0;
  let withUnchecked = 0;
  for (const element of elements) {
    const verdicts = Object.values(element.expected);
    for (const v of verdicts) checks[v] = (checks[v] ?? 0) + 1;
    if (verdicts.includes("failed")) withFailed += 1;
    else if (verdicts.includes("unchecked")) withUnchecked += 1;
  }
  return { checks, withFailed, withUnchecked, total: elements.length };
}
