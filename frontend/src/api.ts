// The only module that talks to the NIYAM API. All calls go to /api (proxied to the backend in dev), or to
// VITE_API_URL when set. A static build (VITE_STATIC_DEMO=1, GitHub Pages) uses the API only if its /health
// answers within 2 s; otherwise it serves the engine's saved results for the 5 samples from /demo/
// (scripts/build_demo_data.py, kept in step with the engine by backend/tests/test_demo_data.py).

export type Verdict = "passed" | "failed" | "unchecked" | "out_of_scope";
export type Status = "compliant" | "noncompliant" | "incomplete" | "nothing_checked";
/** A rule is "error" when its geometric check timed out or crashed: nothing was checked, and it is not a pass. */
export type RuleStatus = Status | "error";

export interface Counts {
  passed: number;
  failed: number;
  unchecked: number;
  out_of_scope: number;
}

export interface ElementResult {
  global_id: string;
  express_id: number;
  name: string | null;
  ifc_class: string;
  verdict: Verdict;
  reason_plain: string | null;
  reason_raw: string | null;
}

export interface RuleResult {
  unit_id: string;
  clause_id: string;
  clause_text: string;
  rule_text: string;
  source_doc: string;
  page: number;
  severity: string;
  human_reviewed: boolean;
  status: RuleStatus;
  counts: Counts;
  elements: ElementResult[];
  error?: string | null;
}

export interface ElementCounts {
  total_in_model_of_scoped_classes: number;
  with_failed: number;
  with_unchecked: number;
  clean: number;
}

export interface AuditResult {
  audit_id: string;
  status: Status;
  /** checks: one per rule x element; elements: distinct elements, failed outranks unchecked */
  summary: { checks: Counts; elements: ElementCounts; rules_with_errors: number };
  rules: RuleResult[];
}

export interface Sample {
  name: string;
  description: string;
  size_bytes: number;
}

export interface RulepackRule {
  unit_id: string;
  clause_id: string;
  clause_text: string;
  rule_text: string;
  human_reviewed: boolean;
}

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

export const NETWORK_ERROR = "Could not reach the NIYAM server. Check that the backend is running and try again.";

/** Turn an error response into the message shown to the user: the API's own detail text, verbatim. */
export function errorMessage(status: number, body: unknown): string {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string" && detail) return detail;
  if (status === 413) return "The file is larger than the server's upload limit.";
  if (status === 422) return "The server could not process this request.";
  if (status >= 500) return "The server failed while handling the request.";
  return `Request failed (HTTP ${status}).`;
}

export const DEMO_MESSAGE =
  "Demo mode: results for the 5 sample buildings were produced by the real NIYAM engine. To audit your own IFC file, run NIYAM locally (see How to run).";

const API = (import.meta.env.VITE_API_URL ?? "").replace(/\/+$/, "");
const DEMO = `${import.meta.env.BASE_URL}demo`;
export type Mode = "api" | "static";
let mode: Promise<Mode> | null = null;

/** Decided once per page load. Only a static build can fall back to the saved demo results. */
export function apiMode(): Promise<Mode> {
  return (mode ??= (async (): Promise<Mode> => {
    if (import.meta.env.VITE_STATIC_DEMO !== "1") return "api";
    if (!API) return "static";
    try {
      return (await fetch(`${API}/health`, { signal: AbortSignal.timeout(2000) })).ok ? "api" : "static";
    } catch {
      return "static";
    }
  })());
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, init);
  } catch {
    throw new ApiError(0, NETWORK_ERROR);
  }
  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);
    throw new ApiError(response.status, errorMessage(response.status, body));
  }
  return (await response.json()) as T;
}

/** The API path, or the saved demo file when the page runs in static demo mode. */
async function source(apiPath: string, demoPath: string): Promise<string> {
  return (await apiMode()) === "static" ? `${DEMO}/${demoPath}` : `${API}${apiPath}`;
}

// audit_id -> sample name, for the downloads of audits that came from the demo files
const demoAudits = new Map<string, string>();

export async function auditUpload(file: File): Promise<AuditResult> {
  if ((await apiMode()) === "static") throw new ApiError(0, DEMO_MESSAGE);
  const form = new FormData();
  form.append("file", file);
  return request<AuditResult>(`${API}/api/audit`, { method: "POST", body: form });
}

export async function auditSample(name: string): Promise<AuditResult> {
  const n = encodeURIComponent(name);
  if ((await apiMode()) === "static") {
    const result = await request<AuditResult>(`${DEMO}/${n}/audit.json`);
    demoAudits.set(result.audit_id, n);
    return result;
  }
  return request<AuditResult>(`${API}/api/samples/${n}/audit`, { method: "POST" });
}

export async function fetchSampleBytes(name: string): Promise<Uint8Array> {
  const n = encodeURIComponent(name);
  let response: Response;
  try {
    response = await fetch(await source(`/api/samples/${n}`, `${n}/${n}.ifc`));
  } catch {
    throw new ApiError(0, NETWORK_ERROR);
  }
  if (!response.ok) throw new ApiError(response.status, errorMessage(response.status, null));
  return new Uint8Array(await response.arrayBuffer());
}

export const listSamples = async () => request<Sample[]>(await source("/api/samples", "samples.json"));
export const getRulepack = async () =>
  request<{ version: string; rules: RulepackRule[] }>(await source("/api/rulepack", "rulepack.json"));

function auditFile(auditId: string, file: string): string {
  const sample = demoAudits.get(auditId);
  return sample ? `${DEMO}/${sample}/${file}` : `${API}/api/audit/${encodeURIComponent(auditId)}/${file}`;
}
export const reportUrl = (auditId: string) => auditFile(auditId, "report.html");
export const bcfUrl = (auditId: string) => auditFile(auditId, "issues.bcf");
