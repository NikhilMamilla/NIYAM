import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ApiError,
  auditSample,
  auditUpload,
  bcfUrl,
  fetchSampleBytes,
  getRulepack,
  listSamples,
  reportUrl,
  type AuditResult,
  type Sample,
} from "./api";
import { DetailPanel, Legend, RuleList, StartPanel, SummaryCard } from "./components";
import { IconDownload, IconExternal, IconReset } from "./icons";
import { LARGE_MODEL_BYTES, affectedLine, checksLine, elementsByExpressId, formatBytes, paintByLocalId } from "./results";
import { Viewer } from "./viewer";

type Phase = "idle" | "working" | "done";
type ViewState = "empty" | "loading" | "ready" | "failed";

interface LoadedFile {
  name: string;
  size: number;
}

export default function App() {
  const [samples, setSamples] = useState<Sample[]>([]);
  const [draftRules, setDraftRules] = useState(false);
  const [phase, setPhase] = useState<Phase>("idle");
  const [error, setError] = useState<ApiError | null>(null);
  const [audit, setAudit] = useState<AuditResult | null>(null);
  const [file, setFile] = useState<LoadedFile | null>(null);
  const [view, setView] = useState<ViewState>("empty");
  const [idMapping, setIdMapping] = useState<"express_id" | "global_id" | "">("");
  const [selected, setSelected] = useState<number | null>(null);
  const [picked, setPicked] = useState<{ localId: number; globalId: string | null } | null>(null);
  const [onlyIssues, setOnlyIssues] = useState(false);
  const viewportRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<Viewer | null>(null);
  const maps = useRef({ localByExpress: new Map<number, number>(), expressByLocal: new Map<number, number>() });
  const runToken = useRef(0);

  const summaries = useMemo(() => (audit ? elementsByExpressId(audit) : new Map()), [audit]);

  useEffect(() => {
    listSamples().then(setSamples).catch(() => setSamples([]));
    getRulepack().then((p) => setDraftRules(p.rules.some((r) => !r.human_reviewed))).catch(() => setDraftRules(false));
  }, []);

  useEffect(() => {
    const viewer = new Viewer(viewportRef.current!);
    viewerRef.current = viewer;
    return () => {
      viewerRef.current = null;
      void viewer.dispose();
    };
  }, []);

  const run = useCallback(async (label: LoadedFile, bytes: Promise<Uint8Array>, request: Promise<AuditResult>) => {
    setPhase("working");
    setError(null);
    setAudit(null);
    setSelected(null);
    setPicked(null);
    setOnlyIssues(false);
    setFile(label);
    setView("loading");
    setIdMapping("");
    const token = ++runToken.current;
    const stale = () => token !== runToken.current;
    const viewer = viewerRef.current!;
    await viewer.clearModel();
    let result: AuditResult;
    try {
      result = await request;
    } catch (reason) {
      if (stale()) return;
      setError(reason instanceof ApiError ? reason : new ApiError(0, "Unexpected error while auditing the model."));
      setPhase("idle");
      setFile(null);
      setView("empty");
      return;
    }
    if (stale()) return;
    setAudit(result);
    setPhase("done");
    // Convert to 3D only once the server has accepted the file: web-ifc runs on the main thread and can spin
    // on unreadable bytes, which would freeze the page before the audit error could be shown.
    const [viewOutcome] = await Promise.allSettled([bytes.then((b) => viewer.load(b))]);
    if (stale()) return;
    if (viewOutcome.status === "rejected") {
      console.error("3D view failed:", viewOutcome.reason);
      setView("failed");
      return;
    }
    const byExpress = elementsByExpressId(result);
    const localIds = await viewer.localIdsByGuid([...byExpress.values()].map((s) => s.globalId));
    const mapped = paintByLocalId(byExpress, localIds);
    maps.current.localByExpress = mapped.localByExpress;
    maps.current.expressByLocal = new Map([...mapped.localByExpress].map(([e, l]) => [l, e]));
    setIdMapping(mapped.idsMatch ? "express_id" : "global_id");
    await viewer.paint(mapped.paints);
    setView("ready");
  }, []);

  const onFile = (f: File) =>
    void run({ name: f.name, size: f.size }, f.arrayBuffer().then((b) => new Uint8Array(b)), auditUpload(f));

  const onSample = (name: string) => {
    const size = samples.find((s) => s.name === name)?.size_bytes ?? 0;
    void run({ name: `${name}.ifc`, size }, fetchSampleBytes(name), auditSample(name));
  };

  const selectExpress = useCallback(async (expressId: number | null) => {
    setSelected(expressId);
    setPicked(null);
    const local = expressId === null ? null : maps.current.localByExpress.get(expressId) ?? null;
    await viewerRef.current?.select(local);
  }, []);

  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || view !== "ready") return;
    return viewer.onPick(async (localId) => {
      if (localId === null) return void selectExpress(null);
      const expressId = maps.current.expressByLocal.get(localId);
      if (expressId !== undefined) return void selectExpress(expressId);
      setSelected(null);
      const [globalId] = await viewer.guidsByLocalId([localId]);
      setPicked({ localId, globalId: globalId ?? null });
      await viewer.select(localId, false);
    });
  }, [view, selectExpress]);

  const toggleOnlyIssues = async () => {
    const next = !onlyIssues;
    setOnlyIssues(next);
    await viewerRef.current?.setOnlyIssues(next);
  };

  const resetView = async () => {
    setOnlyIssues(false);
    await selectExpress(null);
    await viewerRef.current?.setOnlyIssues(false);
    await viewerRef.current?.frame();
  };

  const issueCount = audit ? audit.summary.elements.with_failed + audit.summary.elements.with_unchecked : 0;
  const textAlternative = audit
    ? `3D view of ${file?.name}. ${affectedLine(audit)} (red: violations, amber: could not be fully checked; ` +
      `other elements grey if passed, faded if out of scope). ${checksLine(audit)}.`
    : "3D view: no model loaded.";

  return (
    <div className="app">
      <a href="#results" className="skip-link">Skip to results</a>
      <header className="header">
        <div className="brand">
          <h1 translate="no">NIYAM</h1>
          <p>Checks IFC building models against Indian building bye-laws.</p>
        </div>
        {draftRules && (
          <span className="draft-badge" title="The rule encodings have not been reviewed by a person yet.">
            Draft rules, not human-reviewed
          </span>
        )}
      </header>

      <main className="layout">
        <div className="column controls" id="results">
          <div aria-live="polite" className="live">
            {phase === "working" && <p className="progress"><span className="spinner" aria-hidden="true" />Auditing the model on the server…</p>}
          </div>
          {error && (
            <div className="banner error" role="alert">
              <p className="banner-title">{error.status ? `The model could not be audited (HTTP ${error.status})` : "Connection problem"}</p>
              <p className="banner-message" data-testid="error-message">{error.message}</p>
            </div>
          )}
          {file && file.size > LARGE_MODEL_BYTES && (
            <p className="note">This model is {formatBytes(file.size)}: the 3D view may be slow. The audit itself runs on the server.</p>
          )}
          <StartPanel samples={samples} busy={phase === "working"} onFile={onFile} onSample={onSample} />
          {audit && file && (
            <>
              <SummaryCard audit={audit} fileName={file.name} fileSize={file.size} />
              <div className="button-row downloads">
                <a className="button" href={bcfUrl(audit.audit_id)} download data-testid="download-bcf">
                  <IconDownload />Download BCF
                </a>
                <a className="button" href={reportUrl(audit.audit_id)} target="_blank" rel="noopener noreferrer"
                   data-testid="open-report">
                  <IconExternal />Open HTML report
                </a>
              </div>
              <RuleList audit={audit} summaries={summaries} selectedExpressId={selected}
                        onSelect={(id) => void selectExpress(id)} />
            </>
          )}
        </div>

        <section className="column stage" aria-labelledby="viewport-h">
          <h2 id="viewport-h" className="visually-hidden">3D model</h2>
          <p className="text-alternative" id="viewport-summary" data-testid="viewport-summary">{textAlternative}</p>
          <div className="toolbar">
            <Legend />
            <div className="button-row">
              <button type="button" className="button small" aria-pressed={onlyIssues} disabled={view !== "ready" || issueCount === 0}
                      onClick={() => void toggleOnlyIssues()}>
                Show only issues
              </button>
              <button type="button" className="button small" disabled={view !== "ready"} onClick={() => void resetView()}>
                <IconReset />Reset view
              </button>
            </div>
          </div>
          <div className="viewport-wrap">
            <div ref={viewportRef} className="viewport" role="img" aria-label="3D model view"
                 aria-describedby="viewport-summary" data-view-state={view} data-id-mapping={idMapping} />
            {view === "empty" && <p className="viewport-message">Load a model to see it here.</p>}
            {view === "loading" && <p className="viewport-message"><span className="spinner" aria-hidden="true" />Preparing the 3D view…</p>}
            {view === "failed" && <p className="viewport-message">The 3D view could not be shown for this file. The audit results are still valid.</p>}
          </div>
        </section>

        <div className="column side">
          <DetailPanel summary={selected === null ? null : summaries.get(selected) ?? null} pickedWithoutRules={picked}
                       onClose={() => void selectExpress(null)} />
        </div>
      </main>
    </div>
  );
}
