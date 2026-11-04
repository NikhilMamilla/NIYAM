// The only module that talks to the NIYAM API. All calls go to /api (proxied to the backend in dev).

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

export function auditUpload(file: File): Promise<AuditResult> {
  const form = new FormData();
  form.append("file", file);
  return request<AuditResult>("/api/audit", { method: "POST", body: form });
}

export function auditSample(name: string): Promise<AuditResult> {
  return request<AuditResult>(`/api/samples/${encodeURIComponent(name)}/audit`, { method: "POST" });
}

export async function fetchSampleBytes(name: string): Promise<Uint8Array> {
  let response: Response;
  try {
    response = await fetch(`/api/samples/${encodeURIComponent(name)}`);
  } catch {
    throw new ApiError(0, NETWORK_ERROR);
  }
  if (!response.ok) throw new ApiError(response.status, errorMessage(response.status, null));
  return new Uint8Array(await response.arrayBuffer());
}

export const listSamples = () => request<Sample[]>("/api/samples");
export const getRulepack = () => request<{ version: string; rules: RulepackRule[] }>("/api/rulepack");
export const reportUrl = (auditId: string) => `/api/audit/${encodeURIComponent(auditId)}/report.html`;
export const bcfUrl = (auditId: string) => `/api/audit/${encodeURIComponent(auditId)}/issues.bcf`;
