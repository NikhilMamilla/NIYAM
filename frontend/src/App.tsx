// The dashboard at /app: load a building, read the verdicts, ask why. Fixed regions; their contents swap.
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import readinessIds from "../../docs/readiness/niyam-data-readiness.ids?raw";
import {
  ApiError, auditSample, auditUpload, bcfUrl, fetchSampleBytes, getRulepack, listSamples, reportUrl,
  type AuditResult, type Sample,
} from "./api";
import { DetailPanel, EmptyState, Legend, RuleList, SAMPLES, StartPanel, SummaryStrip, VerdictBadge } from "./components";
import Button from "./Button";
import { IconReset, IconUnchecked } from "./icons";
import {
  LARGE_MODEL_BYTES, elementsByExpressId, errorRules, formatBytes, paintByLocalId, plainNoun, plainSummary, translucentLocalIds,
} from "./results";
import { Link } from "./router";
import type { Atmosphere, Quality } from "./stage";
import { Viewer, type ViewPreset } from "./viewer";
import "./styles/app.css";

type Phase = "idle" | "working" | "done";
type ViewState = "empty" | "loading" | "ready" | "failed";

interface LoadedFile { name: string; size: number; sample: string | null }

function downloadReadiness() {
  const url = URL.createObjectURL(new Blob([readinessIds], { type: "application/xml" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = "niyam-data-readiness.ids";
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export default function App({ initialSample = null }: { initialSample?: string | null }) {
  const [samples, setSamples] = useState<Sample[]>([]);
  const [draftRules, setDraftRules] = useState(true);
  const [phase, setPhase] = useState<Phase>("idle");
  const [error, setError] = useState<ApiError | null>(null);
  const [audit, setAudit] = useState<AuditResult | null>(null);
  const [file, setFile] = useState<LoadedFile | null>(null);
  const [view, setView] = useState<ViewState>("empty");
  const [idMapping, setIdMapping] = useState<"express_id" | "global_id" | "">("");
  const [selected, setSelected] = useState<number | null>(null);
  const [picked, setPicked] = useState<{ localId: number; globalId: string | null } | null>(null);
  const [onlyIssues, setOnlyIssues] = useState(false);
  const [implausible, setImplausible] = useState(0);
  const [orbit, setOrbit] = useState(false);
  const [camera, setCamera] = useState<ViewPreset>("iso");
  const [atmosphere, setAtmosphere] = useState<Atmosphere>("golden");
  const [quality, setQuality] = useState<Quality>("low");
  const [hover, setHover] = useState<{ x: number; y: number; name: string; detail: string } | null>(null);
  const viewportRef = useRef<HTMLDivElement>(null);
  const stageRef = useRef<HTMLElement>(null);
  const viewerRef = useRef<Viewer | null>(null);
  const maps = useRef({ localByExpress: new Map<number, number>(), expressByLocal: new Map<number, number>() });
  const runToken = useRef(0);
  const autoStarted = useRef(false);

  const summaries = useMemo(() => (audit ? elementsByExpressId(audit) : new Map()), [audit]);

  useEffect(() => {
    document.title = "NIYAM app: check a building model";
    listSamples().then(setSamples).catch(() => setSamples([]));
    getRulepack().then((p) => setDraftRules(p.rules.some((r) => !r.human_reviewed))).catch(() => setDraftRules(true));
  }, []);

  useEffect(() => {
    const viewer = new Viewer(viewportRef.current!);
    viewerRef.current = viewer;
    setQuality(viewer.quality);
    if (import.meta.env.DEV) (window as unknown as { __niyamViewer?: Viewer }).__niyamViewer = viewer; // e2e diagnostics
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
    setCamera("iso");
    setFile(label);
    setView("loading");
    setIdMapping("");
    setImplausible(0);
    setHover(null);
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
    const info = await viewer.paint(mapped.paints, translucentLocalIds(byExpress, mapped.localByExpress));
    if (stale()) return;
    setImplausible(info.implausible);
    setView("ready");
  }, []);

  // Back to the start screen: forget the model and its audit; a request still in flight is ignored.
  const backToStart = () => {
    runToken.current++;
    setPhase("idle");
    setError(null);
    setAudit(null);
    setFile(null);
    setSelected(null);
    setPicked(null);
    setOnlyIssues(false);
    setCamera("iso");
    setView("empty");
    setIdMapping("");
    setImplausible(0);
    setHover(null);
    void viewerRef.current?.clearModel();
    window.scrollTo({ top: 0 });
  };

  const onFile = (f: File) =>
    void run({ name: f.name, size: f.size, sample: null }, f.arrayBuffer().then((b) => new Uint8Array(b)), auditUpload(f));

  const onSample = useCallback((name: string) => {
    const size = samples.find((s) => s.name === name)?.size_bytes ?? 0;
    void run({ name: `${name}.ifc`, size, sample: name }, fetchSampleBytes(name), auditSample(name));
  }, [samples, run]);

  // On a phone the load panel fills the first screen: choosing a model brings the light table into view.
  // Instant, not smooth: the page is still growing while the audit runs, which would interrupt an animation,
  // so it scrolls again once the result lands.
  useEffect(() => {
    if (phase === "idle" || !window.matchMedia("(max-width: 760px)").matches) return;
    const stage = stageRef.current;
    if (stage) window.scrollTo({ top: stage.getBoundingClientRect().top + window.scrollY - 76, behavior: "instant" }); // 76 = the sticky bar and a gap
  }, [phase]);

  // deep link: /app?sample=sample_a_mm opens that sample once the sample list is known
  useEffect(() => {
    if (autoStarted.current || !initialSample || !samples.some((s) => s.name === initialSample)) return;
    autoStarted.current = true;
    onSample(initialSample);
  }, [initialSample, samples, onSample]);

  const selectExpress = useCallback(async (expressId: number | null) => {
    setSelected(expressId);
    setPicked(null);
    const local = expressId === null ? null : maps.current.localByExpress.get(expressId) ?? null;
    await viewerRef.current?.select(local);
  }, []);

  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || view !== "ready") return;
    const offPick = viewer.onPick(async (localId) => {
      if (localId === null) return void selectExpress(null);
      const expressId = maps.current.expressByLocal.get(localId);
      if (expressId !== undefined) return void selectExpress(expressId);
      setSelected(null);
      const [globalId] = await viewer.guidsByLocalId([localId]);
      setPicked({ localId, globalId: globalId ?? null });
      await viewer.select(localId, false);
    });
    const offHover = viewer.onHover((localId, x, y) => {
      const expressId = localId === null ? undefined : maps.current.expressByLocal.get(localId);
      const s = expressId === undefined ? undefined : summaries.get(expressId);
      const rect = viewportRef.current?.getBoundingClientRect();
      if (!s || !rect) return setHover(null);
      setHover({ x: x - rect.left, y: y - rect.top, name: s.name ?? "Unnamed element", detail: `${plainNoun(s.ifcClass, 1)} · ${s.worst.replace(/_/g, " ")}` });
    });
    return () => { offPick(); offHover(); };
  }, [view, selectExpress, summaries]);

  const toggleOnlyIssues = async () => {
    const next = !onlyIssues;
    setOnlyIssues(next);
    await viewerRef.current?.setOnlyIssues(next);
  };
  const resetView = async () => {
    setOnlyIssues(false);
    setCamera("iso");
    await selectExpress(null);
    await viewerRef.current?.setOnlyIssues(false);
    await viewerRef.current?.frame();
  };
  const preset = (p: ViewPreset) => { setCamera(p); void viewerRef.current?.preset(p); };

  const plain = audit ? plainSummary(audit) : null;
  const issueCount = audit ? audit.summary.elements.with_failed + audit.summary.elements.with_unchecked : 0;
  const textAlternative = audit && plain
    ? `3D view of ${file?.name}. ${plain.sentence} Red: breaks a rule; amber: could not be checked; grey: passed; faded: out of scope.`
    : "3D view: no model loaded.";
  const sampleMeta = file?.sample ? SAMPLES.find((s) => s.name === file.sample) : null;
  const ready = view === "ready";

  const status = (
    <>
      <div aria-live="polite" className="live">
            {phase === "working" && <p className="progress"><span className="spinner" aria-hidden="true" />Auditing the model on the server…</p>}
          </div>
          {error && (
            <div className="banner error" role="alert">
              <p className="banner-title">{error.status === 400 && /schema/i.test(error.message) ? "This file was not checked" : error.status ? `The model could not be audited (HTTP ${error.status})` : "Connection problem"}</p>
              <p className="banner-message" data-testid="error-message">{error.message}</p>
              {/schema/i.test(error.message) && <p className="banner-help">NIYAM reads IFC4 files. Export your model as IFC4 (not IFC2X3) and try again.</p>}
            </div>
          )}
          {file && file.size > LARGE_MODEL_BYTES && <p className="note">This model is {formatBytes(file.size)}: the 3D view may be slow. The audit itself runs on the server.</p>}
    </>
  );
  const detailOpen = !!(audit && file && (selected !== null || picked));

  return (
    <div className="dash">
      <a href="#verdicts" className="skip-link">Skip to the verdicts</a>
      <header className="dash-top">
        <div className="dash-top-start">
          {view !== "empty" && (
            <Button size="sm" radius={12} className="dash-back" onClick={backToStart}>
              <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M10 3 5 8l5 5" /></svg>
              Back
            </Button>
          )}
          <Link to="/" className="brand" translate="no">NIYAM</Link>
          <h1 className="dash-title">Check a building model</h1>
        </div>
        <div className="dash-top-end">
          {file && <span className="file-chip" title={file.name}><span className="file-chip-dot" aria-hidden="true" />{file.name}</span>}
          {draftRules && (
            <span className="draft-badge" title="The rule encodings have not been reviewed by a person yet.">
              <IconUnchecked />
              <span className="draft-long">Draft rules, not human-reviewed</span>
              <span className="draft-short">Draft rules</span>
            </span>
          )}
          <Button as={Link} to="/" size="sm" radius={12}>About <span className="about-niyam">NIYAM</span></Button>
        </div>
      </header>
      <main className={`dash-main${view === "empty" ? " dash-main--start" : ""}`} id="main">
        {view !== "empty" && <div className="dash-status">{status}</div>}
        {audit && file && (
          <section className="dash-headline" id="verdicts" aria-label="Verdicts" tabIndex={-1}>
            <SummaryStrip audit={audit} fileName={file.name} fileSize={file.size} reportUrl={reportUrl(audit.audit_id)} bcfUrl={bcfUrl(audit.audit_id)} />
            {errorRules(audit).length > 0 && (
              <p className="note" role="status" data-testid="rules-with-errors">
                {errorRules(audit).length} rule(s) could not be run ({errorRules(audit).map((r) => r.clause_id).join(", ")}), so the result is never better than Not fully checked.
              </p>
            )}
          </section>
        )}

      <section ref={stageRef} className="dash-stage" aria-labelledby="stage-h">
        <h2 id="stage-h" className="visually-hidden">3D model</h2>
        <p className="visually-hidden" id="viewport-summary" data-testid="viewport-summary">{textAlternative}</p>
        <div className="stage-tools" role="toolbar" aria-label="3D view controls">
          <div className="tool-group" role="group" aria-label="Camera">
            <span className="tool-label" aria-hidden="true">View</span>
            {(["iso", "plan", "front"] as ViewPreset[]).map((p) => (
              <Button key={p} size="sm" tone="light" radius={10} primary={camera === p} aria-pressed={camera === p} disabled={!ready} onClick={() => preset(p)}>
                {p === "iso" ? "3D" : p === "plan" ? "Plan" : "Front"}
              </Button>
            ))}
            <Button size="sm" tone="light" radius={10} disabled={!ready} onClick={() => void resetView()}><IconReset />Reset</Button>
          </div>
          <div className="tool-group" role="group" aria-label="What to show">
            <span className="tool-label" aria-hidden="true">Show</span>
            <Button size="sm" tone="light" radius={10} primary={onlyIssues} aria-pressed={onlyIssues} disabled={!ready || issueCount === 0} onClick={() => void toggleOnlyIssues()}>Only issues</Button>
            <Button size="sm" tone="light" radius={10} primary={orbit} aria-pressed={orbit} disabled={!ready} title="Keep the model turning"
                    onClick={() => { setOrbit(!orbit); viewerRef.current?.setAutoOrbit(!orbit); }}>Orbit</Button>
          </div>
          <div className="tool-group" role="group" aria-label="Look">
            <span className="tool-label" aria-hidden="true">Look</span>
            <Button size="sm" tone="light" radius={10} primary={atmosphere === "neutral"} aria-pressed={atmosphere === "neutral"}
                    onClick={() => { const a = atmosphere === "golden" ? "neutral" : "golden"; setAtmosphere(a); viewerRef.current?.setAtmosphere(a); }}>
              {atmosphere === "golden" ? "Neutral light" : "Golden hour"}
            </Button>
            <Button size="sm" tone="light" radius={10} aria-label={`Quality: ${quality === "low" ? "Low" : "High"}. Switch to ${quality === "low" ? "High" : "Low"}.`}
                    onClick={() => { const q = quality === "low" ? "high" : "low"; setQuality(q); viewerRef.current?.setQuality(q); }}>
              Quality: {quality === "low" ? "Low" : "High"}
            </Button>
          </div>
        </div>
        <div className="viewport-wrap">
          <div ref={viewportRef} className="viewport" role="img" aria-label="3D model view" aria-describedby="viewport-summary"
               data-view-state={view} data-id-mapping={idMapping} />
          {view === "loading" && <p className="viewport-message"><span className="spinner" aria-hidden="true" />Preparing the 3D view…</p>}
          {view === "failed" && <p className="viewport-message">The 3D view could not be shown for this file. The audit results are still valid.</p>}
          {ready && hover && (
            <div className="hover-tip" style={{ left: hover.x + 14, top: hover.y + 14 }} aria-hidden="true">
              <strong>{hover.name}</strong><span>{hover.detail}</span>
            </div>
          )}
          {ready && implausible > 0 && (
            <p className="viewport-warning" role="status" data-testid="implausible-geometry">
              {implausible} element{implausible === 1 ? " is" : "s are"} drawn more than 200 m across. The file
              probably stores their shape in the wrong unit; NIYAM draws the file as it is.
            </p>
          )}
        </div>
        <div className="stage-foot">
          <Legend />
          {ready && <p className="stage-hint">Drag to orbit · scroll to zoom · click an element</p>}
          <p className="stage-caption">
            {sampleMeta ? "Synthetic test building: only the modelled elements are drawn." : "Only the modelled elements are drawn."}
            {" "}Sky and ground are scenery. 3D by That Open Engine.
          </p>
        </div>
      </section>

        {audit && file && (
          <section className="dash-rules" aria-label="Rules">
            <RuleList audit={audit} selectedExpressId={selected} onSelect={(id) => void selectExpress(id)} />
            {plain && plain.withFailed + plain.withUnchecked > 0 && (
              <p className="right-foot">Select an element in the list or the 3D view to see why. <VerdictBadge verdict="unchecked" /> means data is missing, not that the element passed.</p>
            )}
          </section>
        )}

        {view === "empty" && (
          <div className="start-screen">
            <div className="start-screen-inner">
              {status}
              <EmptyState onSample={onSample} />
              <StartPanel wide samples={samples} busy={phase === "working"} current={file?.sample ?? null} onFile={onFile} onSample={onSample} />
            </div>
          </div>
        )}
      </main>

      <aside className={`detail-drawer${detailOpen ? " open" : ""}`} aria-label="Element detail" inert={!detailOpen}>
        {detailOpen && audit && file && (
          <DetailPanel summary={selected === null ? null : summaries.get(selected) ?? null} pickedWithoutRules={picked}
                       onClose={() => { void selectExpress(null); setPicked(null); }} onDownloadReadiness={downloadReadiness} />
        )}
      </aside>
    </div>
  );
}
