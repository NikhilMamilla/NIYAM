// The landing page at "/": the whiteprint sheet set. Every number is read from site-data.json; nothing is typed by hand.
import { useEffect, useRef, useState } from "react";
import type { SiteData } from "../data/buildSiteData";
import type { Cell, Rate } from "../data/siteData";
import siteJson from "../data/site-data.json";
import { CONTEXT, REPO_DOCS, TEAM } from "../content/site";
import { Term } from "../glossary";
import { IconFailed, IconOutOfScope, IconPassed, IconUnchecked } from "../icons";
import { Link } from "../router";
import { ForestChart, NumbersTable, PairedChart, StabilityChart, type ForestRow } from "./charts";
import { apart, date, frac, harness, modelLabel, rateWithInterval, thousands } from "./format";
import { HeroDrawing } from "./Hero";

const site = siteJson as unknown as SiteData;
const h = site.headline;
const SAMPLE_LINK = "/app?sample=sample_a_mm";

const cell = (list: Cell[], model: "ultra" | "lightning", mode: "gated" | "ungated") =>
  list.find((c) => c.model.includes(model) && c.mode === mode)!;
const unitCell = (model: "ultra" | "lightning", mode: "gated" | "ungated", list = h.unitsAll) =>
  list.find((u) => u.model.includes(model) && u.mode === mode)!;
const MODELS = ["ultra", "lightning"] as const;

/** Each sheet's line work develops as it scrolls into view (once); content is visible by default. */
function useDevelop() {
  useEffect(() => {
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches || !("IntersectionObserver" in window)) return;
    const sheets = [...document.querySelectorAll<HTMLElement>("[data-sheet]")];
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) {
        if (e.isIntersecting) {
          e.target.setAttribute("data-developed", "");
          io.unobserve(e.target);
        }
      }
    }, { rootMargin: "0px 0px -15% 0px" });
    for (const s of sheets) {
      if (s.getBoundingClientRect().top > window.innerHeight * 0.85) {
        s.setAttribute("data-waiting", "");
        io.observe(s);
      } else s.setAttribute("data-developed", "");
    }
    return () => io.disconnect();
  }, []);
}

function Stamp({ children }: { children: React.ReactNode }) {
  return <p className="stamp mono">{children}</p>;
}

function RunStamp() {
  const p = h.provenance;
  return (
    <Stamp>
      Run {p.runId} · commit {p.commit.slice(0, 7)} · {date(p.date)} · {p.models.length} models · {p.repeats} repeats ·
      {" "}{thousands(p.calls)} model calls · {thousands(p.tokens)} tokens · reasoning off · temperature {p.temperature}
    </Stamp>
  );
}

function Sheet({ id, sheet, title, children, className = "" }: { id: string; sheet: string; title: string; children: React.ReactNode; className?: string }) {
  return (
    <section id={id} className={`sheet ${className}`} data-sheet aria-labelledby={`${id}-h`}>
      <div className="sheet-inner">
        <h2 id={`${id}-h`}>{title}</h2>
        {children}
      </div>
      <p className="sheet-number mono" aria-hidden="true">Sheet {sheet}</p>
    </section>
  );
}

function Takeaway({ say, caveat }: { say: React.ReactNode; caveat: React.ReactNode }) {
  return (
    <div className="takeaway">
      <p className="say">{say}</p>
      <p className="caveat"><span className="caveat-label">Caveat</span> {caveat}</p>
    </div>
  );
}

const VERDICT_ICON = { failed: IconFailed, unchecked: IconUnchecked, passed: IconPassed, out_of_scope: IconOutOfScope } as const;
const VERDICT_WORD = { failed: "Fails", unchecked: "Could not be checked", passed: "Passes", out_of_scope: "Not in scope" } as const;

function Verdict({ v }: { v: keyof typeof VERDICT_ICON }) {
  const Icon = VERDICT_ICON[v];
  return <span className={`badge verdict-${v}`}><Icon />{VERDICT_WORD[v]}</span>;
}

/* ---------- 1. hero ---------- */
function HeroSheet() {
  return (
    <header className="hero sheet" data-sheet data-developed="">
      <div className="hero-copy">
        <p className="draft-badge"><IconUnchecked />Draft rules, not human-reviewed</p>
        <h1>Building bye‑laws, as checks a computer can run.</h1>
        <p className="lead">
          NIYAM reads sentences from Indian building bye-laws, drafts a machine check for each with an AI model, keeps a
          draft only if it behaves correctly on test buildings, and then audits your <Term k="IFC">IFC</Term> building model
          in 3D. It is a research prototype: {site.units.total} draft rules, synthetic test buildings, no expert review yet.
        </p>
        <div className="btn-row hero-actions">
          <Link to="/app" className="btn primary">Open the app</Link>
          <Link to={SAMPLE_LINK} className="btn">Try a sample building</Link>
        </div>
        <dl className="title-block">
          <div><dt>Sources</dt><dd>MBBL 2016 · Telangana 2012</dd></div>
          <div><dt>Clauses read</dt><dd className="num">{thousands(site.corpus.MBBL2016 + site.corpus.TGBR2012)}</dd></div>
          <div><dt>Rules drafted</dt><dd className="num">{site.units.total}</dd></div>
          <div><dt>Status</dt><dd>Research prototype</dd></div>
        </dl>
      </div>
      <HeroDrawing />
    </header>
  );
}

/* ---------- 2. problem ---------- */
function ProblemSheet() {
  return (
    <Sheet id="problem" sheet="A-02" title="Plans are still checked by reading">
      <div className="two-col">
        <div className="prose">
          <p>
            In most Indian cities, a building plan gets its permission after an officer reads 2D drawings against rules written
            as prose: setbacks, room sizes, exit widths. The digital tools that exist keep the rules inside closed
            software, so nobody outside can see how a clause was turned into a check.
          </p>
          <p>
            There is no open, machine-readable version of India's bye-laws. NIYAM is an attempt to build one honestly:
            every check points back to the sentence it came from, and every number about its accuracy says how it was measured.
          </p>
        </div>
        <ul className="context-list">
          <li>{CONTEXT.nbc}</li>
          <li>{CONTEXT.singapore}</li>
          <li>{CONTEXT.ids}</li>
        </ul>
      </div>
    </Sheet>
  );
}

/* ---------- 3. what NIYAM is: the pipeline, stage by stage, with one real unit ---------- */
const STAGES = [
  { key: "clause", name: "Clause", line: "A sentence from the bye-law, quoted word for word." },
  { key: "draft", name: "Draft", line: "An AI model writes a check for that sentence." },
  { key: "gate", name: "Gate", line: "The draft must behave correctly on two test buildings." },
  { key: "pack", name: "Rulepack", line: "Accepted drafts are stored, still marked as drafts." },
  { key: "audit", name: "Audit", line: "The checks run on an uploaded IFC4 model." },
  { key: "view", name: "3D view", line: "Every element is coloured by its verdict." },
  { key: "bcf", name: "BCF", line: "Issues export to the tools designers already use." },
] as const;

function PipelineSheet() {
  const [stage, setStage] = useState(0);
  const ex = site.workedExample;
  const failing = ex.sampleA.filter((d) => d.verdict === "failed");
  const unchecked = ex.sampleA.filter((d) => d.verdict === "unchecked");
  const detail: Record<(typeof STAGES)[number]["key"], React.ReactNode> = {
    clause: <><p className="quote">“{ex.text}”</p><p className="meta">MBBL 2016, clause {ex.clauseId.split("-")[1]}, page {ex.page}</p></>,
    draft: (
      <>
        <p>The check is an <Term k="IDS">IDS</Term> file: it applies to <code>{ex.ids.appliesTo}</code> and requires <code>{ex.ids.requires}</code>.</p>
        <p className="meta">Shown: the stored rule <code>{ex.ids.file}</code> (a pilot written by hand in the same format the AI produces).</p>
      </>
    ),
    gate: <p>Before it is kept, the check must pass a test building that follows the rule and fail one that breaks it. The next sheet shows a real draft that the <Term k="gate">gate</Term> turned back.</p>,
    pack: <p>The accepted check joins the rulepack with <code>human_reviewed: false</code>. It stays a draft until a domain expert signs it off on the review sheet.</p>,
    audit: (
      <>
        <p>On synthetic sample A, the expected results for this rule are:</p>
        <ul className="verdict-list">
          {ex.sampleA.filter((d) => d.verdict).map((d) => (
            <li key={d.name}><Verdict v={d.verdict as keyof typeof VERDICT_ICON} /><span>{d.name}</span>
              <span className="meta num">{d.widthM === null ? "no width in the model" : `${d.widthM} m`}{d.fireExit === null ? ", exit status missing" : d.fireExit ? "" : ", not an exit"}</span></li>
          ))}
        </ul>
      </>
    ),
    view: <p>In the app, {failing.map((d) => d.name).join(" and ")} {failing.length === 1 ? "turns" : "turn"} red, {unchecked.length} door{unchecked.length === 1 ? "" : "s"} with missing data {unchecked.length === 1 ? "turns" : "turn"} amber, and selecting one explains why, with the clause beside it.</p>,
    bcf: <p>Each failed or unchecked element becomes an issue in a <Term k="BCF">BCF</Term> file, with the element and a viewpoint, so a designer can open it in their own tool.</p>,
  };
  return (
    <Sheet id="what" sheet="A-03" title="One sentence, followed all the way through">
      <p className="lede">NIYAM is a pipeline. Step through it with one real rule from the repository.</p>
      <div className="pipeline">
        <ol className="stage-list" role="tablist" aria-label="Pipeline stages">
          {STAGES.map((s, i) => (
            <li key={s.key} role="presentation">
              <button type="button" role="tab" id={`stage-${s.key}`} aria-selected={stage === i} aria-controls="stage-panel"
                      className={`stage ${stage === i ? "on" : ""} ${i < stage ? "done" : ""}`} onClick={() => setStage(i)}
                      onKeyDown={(e) => {
                        if (e.key === "ArrowRight" || e.key === "ArrowDown") { e.preventDefault(); setStage((stage + 1) % STAGES.length); }
                        if (e.key === "ArrowLeft" || e.key === "ArrowUp") { e.preventDefault(); setStage((stage + STAGES.length - 1) % STAGES.length); }
                      }}>
                <span className="stage-dot" aria-hidden="true" />
                <span className="stage-name">{s.name}</span>
                <span className="stage-line">{s.line}</span>
              </button>
            </li>
          ))}
        </ol>
        <div className="stage-panel" id="stage-panel" role="tabpanel" aria-labelledby={`stage-${STAGES[stage]!.key}`}>
          <h3>{STAGES[stage]!.name}</h3>
          {detail[STAGES[stage]!.key]}
          <div className="btn-row">
            <button type="button" className="btn small" disabled={stage === 0} onClick={() => setStage(stage - 1)}>Previous</button>
            <button type="button" className="btn small" disabled={stage === STAGES.length - 1} onClick={() => setStage(stage + 1)}>Next stage</button>
          </div>
        </div>
      </div>
    </Sheet>
  );
}

/* ---------- 4. the gate ---------- */
const STAGE_PLAIN: Record<string, string> = {
  xml_wellformed: "Is it well-formed XML?",
  xsd_valid: "Is it a valid IDS 1.0 file?",
  unit_safe_bounds: "Are its numbers safe across units (mm and m)?",
  loads_in_ifctester: "Does the reference IDS checker load it?",
  applicable_on_fixtures: "Does it apply to the elements it is about?",
  verdict_pass_fixture: "Does the test building that follows the rule pass?",
  verdict_fail_fixture: "Does the test building that breaks the rule fail?",
};

function GateSheet() {
  const g = site.gateExample;
  return (
    <Sheet id="gate" sheet="A-04" title="Why an AI draft is never trusted on its own">
      <div className="two-col">
        <div className="prose">
          <p>
            A language model can write a check that looks right and is wrong: it may test the wrong door, use the wrong
            unit, or apply a rule to every element when the clause meant only some. So every draft goes through the{" "}
            <Term k="gate">gate</Term>, a fixed series of stations. A draft that fails a station is sent back with the
            reason, for up to {h.provenance.maxRepairs} repairs. If it never passes, a person has to look at it.
          </p>
          <p>
            The gate uses two small test buildings per rule. Separate held-out buildings, which the gate never sees, are
            used only to measure how often a passed draft is still wrong.
          </p>
        </div>
        {g && (
          <figure className="test-strip">
            <figcaption>
              <strong>A real rejection.</strong> {modelLabel(g.model)} drafted a check for {g.unit_id}
              {" "}(“{site.units.list.find((u) => u.id === g.unit_id)?.text}”). It applied the rule to every door, but the
              clause is about exits, so the test building that follows the rule, which has a lower door that is not an exit, failed.
            </figcaption>
            <ol className="stations">
              {g.stages.map((s: { stage: string; passed: boolean }) => (
                <li key={s.stage} className={s.passed ? "ok" : "stop"}>
                  {s.passed ? <IconPassed /> : <IconFailed />}<span>{STAGE_PLAIN[s.stage] ?? s.stage}</span>
                  <span className="visually-hidden">{s.passed ? "passed" : "failed here"}</span>
                </li>
              ))}
            </ol>
            <p className="strip-label">Sent back to the model, verbatim (test-building names masked):</p>
            <pre className="repair mono">{g.repair_message_head}</pre>
            <Stamp>Run {g.run_id} · attempt {g.attempt} · outcome after {g.repair_rounds} repairs: {g.outcome === "needs_human" ? "still rejected, needs a person" : g.outcome}</Stamp>
          </figure>
        )}
      </div>
    </Sheet>
  );
}

/* ---------- 5. two kinds of rules ---------- */
function KindsSheet() {
  const ids = site.units.byTier["MBBL2016/ids"] ?? 0;
  const geo = (site.units.byTier["MBBL2016/geometric"] ?? 0) + (site.units.byTier["TGBR2012/geometric"] ?? 0);
  return (
    <Sheet id="kinds" sheet="A-05" title="Two kinds of rules">
      <div className="kinds">
        <article className="kind">
          <h3>Declared data: <Term k="IDS">IDS</Term></h3>
          <p>When the rule is about something the model states, such as whether a door is an exit and how wide it is, the
            check is an IDS 1.0 file. Any IDS-aware tool can run it, not just NIYAM.</p>
          <p className="kind-count"><span className="num">{ids}</span> rules</p>
        </article>
        <article className="kind">
          <h3>Measured from shape: sandboxed Python</h3>
          <p>IDS cannot measure geometry. A room's floor area or height has to be computed from its shape, so these checks
            are short Python functions that run in a sandbox with a fixed set of helpers and a time limit.</p>
          <p className="kind-count"><span className="num">{geo}</span> rules</p>
        </article>
      </div>
    </Sheet>
  );
}

/* ---------- 6. evaluation ---------- */
function EvaluationSheet() {
  const [counted, setCounted] = useState<"items" | "units">("items");
  const forest = (pick: (m: "ultra" | "lightning", mode: "gated" | "ungated") => Rate): ForestRow[] =>
    MODELS.flatMap((m) => (["gated", "ungated"] as const).map((mode) => ({
      key: `${m}-${mode}`, group: modelLabel(cell(h.all, m, mode).model), label: mode === "gated" ? "With the gate" : "Without the gate",
      rate: pick(m, mode), tone: mode,
    })));
  const wrongRows = counted === "items" ? forest((m, mode) => cell(h.all, m, mode).wrongShipped) : forest((m, mode) => unitCell(m, mode).wrongShippedUnits);
  const tierRows: ForestRow[] = MODELS.flatMap((m) => (["ids", "geometric"] as const).flatMap((tier) => (["gated", "ungated"] as const).map((mode) => {
    const t = h.tiers.find((x) => x.model.includes(m) && x.mode === mode && x.tier === tier)!;
    return { key: `${m}-${tier}-${mode}`, group: `${modelLabel(t.model).split(" (")[0]} · ${tier === "ids" ? "IDS rules" : "shape rules"}`,
      label: mode === "gated" ? "With the gate" : "Without the gate", rate: t.wrongShipped, tone: mode };
  })));
  const ug = cell(h.all, "ultra", "gated"), uu = cell(h.all, "ultra", "ungated"), lg = cell(h.all, "lightning", "gated"), lu = cell(h.all, "lightning", "ungated");
  const uug = unitCell("ultra", "gated"), uuu = unitCell("ultra", "ungated");
  const p = h.provenance;
  return (
    <Sheet id="evaluation" sheet="A-06" title="How often a wrong rule gets through">
      <div className="prose">
        <p>
          The question is simple: when a rule is accepted, is it right on buildings it has never seen? Each of
          {" "}{h.unitsInRun} rules was drafted by {p.models.length} open models ({p.models.map((m) => modelLabel(m.name)).join(" and ")}),
          {" "}{p.repeats} times each, with and without the gate, and every result was scored on held-out test buildings
          that include the boundary case (exactly at the limit). Hidden reasoning was switched off and the temperature was {p.temperature}.
        </p>
      </div>
      <RunStamp />

      <div className="figure-block">
        <div className="figure-head">
          <h3>Wrong rules shipped</h3>
          <div className="segmented" role="radiogroup" aria-label="Count over">
            <button type="button" role="radio" aria-checked={counted === "items"} className="btn small" aria-pressed={counted === "items"} onClick={() => setCounted("items")}>Every attempt</button>
            <button type="button" role="radio" aria-checked={counted === "units"} className="btn small" aria-pressed={counted === "units"} onClick={() => setCounted("units")}>Per rule</button>
          </div>
        </div>
        <p className="figure-note">
          {counted === "items"
            ? "Shipped rules that are wrong on the held-out buildings, out of all shipped rules. Each attempt counts once; the three repeats of a rule are not independent."
            : "A rule counts as wrong if any of its repeats shipped a wrong check, out of rules that shipped at least once. This is the more cautious count."}
        </p>
        <ForestChart rows={wrongRows} title={`Wrong rules shipped, ${counted === "items" ? "per attempt" : "per rule"}: dot is the rate, bar the 95% interval`} unit={counted === "items" ? "shipped rules" : "rules"} />
        <Takeaway
          say={<>With the gate, {frac(ug.wrongShipped)} rules shipped by {modelLabel(ug.model)} were wrong ({rateWithInterval(ug.wrongShipped)}); without it, {frac(uu.wrongShipped)} ({rateWithInterval(uu.wrongShipped)}).
            For {modelLabel(lg.model)}: {frac(lg.wrongShipped)} with the gate, {frac(lu.wrongShipped)} without.
            {apart(ug.wrongShipped, uu.wrongShipped) && apart(lg.wrongShipped, lu.wrongShipped) ? " For both models the intervals do not overlap." : " Some intervals overlap."}</>}
          caveat={<>The gate also ships fewer rules ({frac(ug.shipped)} and {frac(lg.shipped)} attempts, against all {uu.n} without it); the rest go to a person. Counted per rule, the gap is {harness(uug.wrongShippedUnits)} against {harness(uuu.wrongShippedUnits)} for {modelLabel(ug.model)}. No difference between the two models may be claimed from {h.unitsInRun} rules.</>}
        />
      </div>

      <div className="figure-block">
        <h3>Where it goes wrong: declared-data rules against shape rules</h3>
        <ForestChart rows={tierRows} title="Wrong rules shipped by kind of rule, per attempt" unit="shipped rules" />
        <Takeaway
          say={<>{(["ungated", "gated"] as const).map((mode) => {
            const wrong = (tier: string) => h.tiers.filter((x) => x.mode === mode && x.tier === tier).reduce((s, x) => s + x.wrongShipped.k, 0);
            return `${mode === "gated" ? "With" : "Without"} the gate, ${wrong("ids")} wrong shipped attempts were declared-data (IDS) rules and ${wrong("geometric")} were shape rules. `;
          })}</>}
          caveat={<>Only {site.units.byTier["MBBL2016/ids"]} of the {h.unitsInRun} rules are IDS rules, so their intervals are very wide.</>}
        />
      </div>

      <div className="figure-block">
        <h3>Same rule, with and without the gate</h3>
        <PairedChart title="Paired outcomes on the same rule and repeat: did each condition ship a correct rule?"
                     rows={h.paired.map((r) => ({ key: r.model, label: modelLabel(r.model), ...r }))} />
        <Takeaway
          say={<>{h.paired.map((r) => `${modelLabel(r.model)}: in ${r.gatedOnly} pairs only the gated attempt shipped a correct rule, in ${r.ungatedOnly} only the ungated one did. `)}</>}
          caveat={<>These are paired counts, not a significance test. A rule the gate holds back counts as “not correct shipped” even if a person could fix it in a minute.</>}
        />
      </div>

      <div className="figure-block">
        <h3>Did the same rule come out the same way every time?</h3>
        <StabilityChart title="Rules whose outcome was identical in all repeats"
                        rows={h.unitsAll.map((u) => ({ key: `${u.model}-${u.mode}`, label: `${modelLabel(u.model).split(" (")[0]}, ${u.mode === "gated" ? "gated" : "ungated"}`, stable: u.stable, varied: u.varied }))} />
        <Takeaway
          say={<>Even at temperature {p.temperature}, some rules came out differently across the {p.repeats} repeats.</>}
          caveat={<>Three repeats are enough to see variation, not to measure it.</>}
        />
      </div>

      <div className="figure-block">
        <h3>What it cost</h3>
        <NumbersTableOpen p={p} />
      </div>

      <details className="disclosure posthoc">
        <summary>Post-hoc check: without the two rules whose reading is disputed</summary>
        <p className="figure-note">
          Excluded after seeing the results, because the spec's reading and the clause's literal text disagree
          ({h.posthoc.excluded.join(", ")}). Not a pre-registered analysis.
        </p>
        <NumbersTable caption="Post-hoc sensitivity" head={["Model", "Mode", "Attempts", "Correct on held-out", "Wrong shipped"]}
                      rows={h.posthoc.all.map((c) => [modelLabel(c.model), c.mode, String(c.n), harness(c.heldoutCorrect), harness(c.wrongShipped)])} />
      </details>
      <p className="handoff">All of this is on synthetic test buildings. The next sheet asks whether the approach carries to a second jurisdiction.</p>
    </Sheet>
  );
}

function NumbersTableOpen({ p }: { p: SiteData["headline"]["provenance"] }) {
  return (
    <div className="table-wrap">
      <table className="data-table">
        <caption className="visually-hidden">Cost of the headline run</caption>
        <thead><tr><th scope="col">Model and mode</th><th scope="col">Attempts</th><th scope="col">Mean repair rounds</th><th scope="col">Mean tokens per rule</th><th scope="col">Mean seconds</th></tr></thead>
        <tbody>
          {h.all.map((c) => (
            <tr key={`${c.model}-${c.mode}`}>
              <th scope="row">{modelLabel(c.model)}, {c.mode}</th>
              <td className="num">{c.n}</td>
              <td className="num">{c.meanRepairs === null ? "none (one call)" : c.meanRepairs.toFixed(2)}</td>
              <td className="num">{thousands(Math.round(c.meanTokens ?? 0))}</td>
              <td className="num">{(c.meanWallS ?? 0).toFixed(1)}</td>
            </tr>
          ))}
        </tbody>
        <tfoot><tr><th scope="row">Whole run</th><td className="num" colSpan={4}>{thousands(p.calls)} model calls, {thousands(p.tokens)} tokens</td></tr></tfoot>
      </table>
    </div>
  );
}

/* ---------- 7. Telangana ---------- */
function TelanganaSheet() {
  const t = site.telangana;
  return (
    <Sheet id="telangana" sheet="A-07" title="A second jurisdiction: Telangana">
      <div className="two-col">
        <div className="prose">
          <p>
            The {site.sources.TGBR2012} were read with the same pipeline: {site.corpus.TGBR2012} clauses, split by a
            new reader of {site.telanganaSegmenterLines} lines of code. Only {t.unitsInRun} sentences fit a single-value
            check once the condition in the rule's heading (it covers only buildings that are not high-rise) is set aside and noted for the reviewer:
          </p>
          <ul className="quotes">
            {site.units.list.filter((u) => u.source === "TGBR2012").map((u) => <li key={u.id}>“{u.text}” <span className="meta mono">{u.id}</span></li>)}
          </ul>
          <p>
            Few rules fit because most of the document governs plots and sites (setbacks, road widths), and it leaves room
            sizes and heights to the National Building Code, which is not in the corpus.
          </p>
        </div>
        <div>
          <p className="case-label">Case study: {t.unitsInRun} rules, too few for rates. Counts only.</p>
          <div className="table-wrap">
            <table className="data-table">
              <caption className="visually-hidden">Telangana case study counts</caption>
              <thead><tr><th scope="col">Rule</th><th scope="col">Model</th><th scope="col">Mode</th><th scope="col">Shipped</th><th scope="col">Shipped and right</th></tr></thead>
              <tbody>
                {t.caseStudy.map((c) => (
                  <tr key={`${c.unit}-${c.model}-${c.mode}`}>
                    <th scope="row" className="mono">{c.unit}</th><td>{modelLabel(c.model).split(" (")[0]}</td><td>{c.mode}</td>
                    <td className="num">{c.shipped} of {c.repeats}</td><td className="num">{c.shippedCorrect} of {c.repeats}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Stamp>Run {t.provenance.runId} · {date(t.provenance.date)} · {thousands(t.provenance.calls)} calls</Stamp>
        </div>
      </div>
    </Sheet>
  );
}

/* ---------- 8. reality check ---------- */
function RealitySheet() {
  const [, ...files] = site.realModels.files;
  const [auditHead, ...audit] = site.realModels.audit;
  return (
    <Sheet id="reality" sheet="A-08" title="Reality check: two real models could not be checked">
      <div className="prose">
        <p>
          We ran the audit on two real exports from an authoring tool (a buildingSMART sample scene, exported from
          SketchUp). Nothing passed and nothing failed. The rooms did not say what kind of room they are, and there were no
          doors or stairs, so every rule either found nothing to check or marked the rooms “could not be checked”. That is
          the honest finding: the bottleneck is the data in the model, not the rules.
        </p>
      </div>
      <div className="table-wrap">
        <table className="data-table">
          <caption className="visually-hidden">Audit of the real models</caption>
          <thead><tr>{(auditHead ?? []).map((c) => <th key={c} scope="col">{c}</th>)}</tr></thead>
          <tbody>{audit.map((r) => <tr key={r.join("|")}>{r.map((c, i) => (i === 0 ? <th key={i} scope="row">{c}</th> : <td key={i} className="num">{c}</td>))}</tr>)}</tbody>
        </table>
      </div>
      <p className="meta">Files: {files.map((f) => `${f[0]} (${f[3]}, ${f[2]})`).join("; ")}.</p>
      <h3 className="sub">What to add to a model before submitting</h3>
      <p>NIYAM writes one <Term k="IDS">IDS</Term> file listing the data its rules need. Run it in any IDS checker first:</p>
      <ul className="readiness">
        {site.readiness.map((r) => (
          <li key={r.name}><strong>{r.name}</strong><span className="meta">enables {r.enables.length} rule{r.enables.length === 1 ? "" : "s"}</span></li>
        ))}
      </ul>
      <p className="meta">The room names (Category values) are NIYAM's own assumed profile, not a standard.</p>
    </Sheet>
  );
}

/* ---------- 9. demo ---------- */
const DEMO = [
  { src: "/screens/demo-1-load.png", step: "Choose sample A. The server audits it and the model appears on the light table." },
  { src: "/screens/demo-2-select.png", step: "Select a red door. The panel says which rule it breaks, why, and quotes the clause." },
  { src: "/screens/demo-3-issues.png", step: "Show only issues to hide everything that passed, then export the HTML report or BCF." },
];

function DemoSheet() {
  return (
    <Sheet id="demo" sheet="A-09" title="What the app looks like">
      <ol className="demo">
        {DEMO.map((d) => (
          <li key={d.src}>
            <img src={d.src} alt={`Dashboard screenshot: ${d.step}`} loading="lazy" width={1280} height={800} />
            <p>{d.step}</p>
          </li>
        ))}
      </ol>
      <div className="btn-row center">
        <Link to="/app" className="btn primary">Open the app</Link>
        <Link to={SAMPLE_LINK} className="btn">Try sample A now</Link>
      </div>
    </Sheet>
  );
}

/* ---------- 10. standards ---------- */
function StandardsSheet() {
  return (
    <Sheet id="standards" sheet="A-10" title="Open standards, open code">
      <dl className="standards">
        <div><dt><Term k="IFC">IFC4</Term></dt><dd>the building model NIYAM reads (IFC2X3 files are refused with an explanation)</dd></div>
        <div><dt><Term k="IDS">IDS 1.0</Term></dt><dd>declared-data rules and the readiness file, runnable in other tools</dd></div>
        <div><dt><Term k="BCF">BCF 2.1</Term></dt><dd>issues exported for design tools</dd></div>
        <div><dt>MIT licence</dt><dd>for NIYAM's code. Clause text is quoted for research; the source PDFs are not redistributed. The two real models are CC BY 4.0 (buildingSMART).</dd></div>
      </dl>
    </Sheet>
  );
}

/* ---------- 11. limits ---------- */
function LimitsSheet() {
  return (
    <Sheet id="limits" sheet="A-11" title="What this does not show, yet">
      <div className="two-col">
        <ul className="limits">
          <li><strong>No rule is reviewed.</strong> All {site.units.total} rules are drafts until a domain expert signs them off.</li>
          <li><strong>Synthetic buildings.</strong> Every accuracy number comes from small generated test buildings.</li>
          <li><strong>Small numbers.</strong> {h.unitsInRun} rules ({site.units.distinct} distinct in all), {h.provenance.repeats} repeats, {h.provenance.models.length} models; every interval is wide.</li>
          <li><strong>One value per rule.</strong> Each check tests one value of one element; ratios, distances and setbacks are not encoded.</li>
          <li><strong>Conditions dropped.</strong> Building-type and use conditions in a clause are left out and noted for the reviewer.</li>
          <li><strong>Disputed readings.</strong> {site.units.readingDependent.length} rules depend on how a clause is read; they are listed first for review.</li>
          <li><strong>No real building checked.</strong> The real exports we tried lacked the data.</li>
        </ul>
        <div>
          <h3 className="sub">Next</h3>
          <ol className="next">
            <li>Expert review of every rule, starting with the disputed ones.</li>
            <li>Site geometry, so setbacks and plot rules can be checked.</li>
            <li>The National Building Code in the corpus, for room sizes and heights.</li>
            <li>Tests on real exports from Revit, ArchiCAD and other tools.</li>
          </ol>
        </div>
      </div>
    </Sheet>
  );
}

/* ---------- 12. team and footer ---------- */
function Footer() {
  const missing = <span className="placeholder">to be added</span>;
  return (
    <footer className="site-footer">
      <dl className="title-block footer-block">
        <div><dt>Team</dt><dd>{TEAM.TEAM_NAME || missing}</dd></div>
        <div><dt>Members</dt><dd>{TEAM.MEMBERS.length ? TEAM.MEMBERS.join(", ") : missing}</dd></div>
        <div><dt>College</dt><dd>{TEAM.COLLEGE || missing}</dd></div>
        <div><dt>Mentor</dt><dd>{TEAM.MENTOR || missing}</dd></div>
      </dl>
      <nav aria-label="Project documents">
        <ul className="doc-links">{REPO_DOCS.map((d) => <li key={d.path}><span>{d.label}</span> <code>{d.path}</code></li>)}</ul>
      </nav>
      <p className="meta">NIYAM · research prototype · MIT licence · draft rules, not human-reviewed</p>
    </footer>
  );
}

export default function Landing() {
  useDevelop();
  const main = useRef<HTMLElement>(null);
  useEffect(() => {
    document.title = "NIYAM: building bye-laws as machine checks";
  }, []);
  return (
    <div className="landing">
      <a href="#main" className="skip-link">Skip to content</a>
      <nav className="topbar" aria-label="Main">
        <Link to="/" className="brand" aria-label="NIYAM home"><span translate="no">NIYAM</span></Link>
        <ul className="nav-links">
          <li><a href="#what">How it works</a></li>
          <li><a href="#evaluation">Results</a></li>
          <li><a href="#limits">Limits</a></li>
        </ul>
        <Link to="/app" className="btn small primary">Open the app</Link>
      </nav>
      <main id="main" ref={main} tabIndex={-1}>
        <HeroSheet />
        <ProblemSheet />
        <PipelineSheet />
        <GateSheet />
        <KindsSheet />
        <EvaluationSheet />
        <TelanganaSheet />
        <RealitySheet />
        <DemoSheet />
        <StandardsSheet />
        <LimitsSheet />
      </main>
      <Footer />
    </div>
  );
}
