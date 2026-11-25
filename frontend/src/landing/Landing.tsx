// The landing page at "/": the whiteprint sheet set. Every number is read from site-data.json; nothing is typed by hand.
import { useEffect, useRef, useState } from "react";
import type { SiteData } from "../data/buildSiteData";
import type { Cell, Rate } from "../data/siteData";
import siteJson from "../data/site-data.json";
import { CONTEXT, DOC_GROUPS, TEAM } from "../content/site";
import { Term } from "../glossary";
import { IconFailed, IconOutOfScope, IconPassed, IconUnchecked } from "../icons";
import { Link } from "../router";
import { ForestChart, NumbersTable, PairedChart, StabilityChart, type ForestRow } from "./charts";
import { apart, date, frac, harness, modelLabel, rateWithInterval, thousands } from "./format";
import { HeroDrawing } from "./Hero";
import { ProblemIllustration } from "./ProblemIllustration";
import GooeyNav from "./GooeyNav";
import Button from "../Button";
import { isLowEnd } from "../perf";
import CardSwap, { type CardSwapHandle } from "./CardSwap";
import ArchitecturalJourney from "./ArchitecturalJourney";

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

function Sheet({ id, sheet, title, kicker, children, className = "", aside }: { id: string; sheet: string; title: string; kicker?: string; children: React.ReactNode; className?: string; aside?: React.ReactNode }) {
  return (
    <section id={id} className={`sheet ${className}`} data-sheet aria-labelledby={`${id}-h`}>
      <div className="sheet-inner">
        <p className="sheet-id" aria-hidden="true">Sheet {sheet}</p>
        {kicker && <p className="sheet-kicker">{kicker}</p>}
        <h2 id={`${id}-h`}>{title}</h2>
        {aside && <div className="sheet-aside">{aside}</div>}
        {children}
      </div>
      <p className="sheet-number mono" aria-hidden="true">{sheet}</p>
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

export function Verdict({ v }: { v: keyof typeof VERDICT_ICON }) {
  const Icon = VERDICT_ICON[v];
  return <span className={`badge verdict-${v}`}><Icon />{VERDICT_WORD[v]}</span>;
}

/* ---------- 1. hero ---------- */
function HeroSheet() {
  return (
    <header className="hero sheet" data-sheet data-developed="">
      <div className="hero-copy">
        <p className="draft-badge"><IconUnchecked />Draft rules, not human-reviewed</p>
        <h1>Building bye‑laws, as checks a <em>computer</em> can run.</h1>
        <p className="lead">
          NIYAM reads sentences from Indian building bye-laws, drafts a machine check for each with an AI model, keeps a
          draft only if it behaves correctly on test buildings, and then audits your <Term k="IFC">IFC</Term> building model
          in 3D. It is a research prototype: {site.units.total} draft rules, synthetic test buildings, no expert review yet.
        </p>
        <div className="btn-row hero-actions">
          <Button as={Link} to="/app" primary>Open the app</Button>
          <Button as={Link} to={SAMPLE_LINK}>Try a sample building</Button>
        </div>
      </div>
      <HeroDrawing />
      <dl className="title-block hero-title-block">
        <div><dt>Sources</dt><dd>MBBL 2016 · Telangana 2012</dd></div>
        <div><dt>Clauses read</dt><dd className="num">{thousands(site.corpus.MBBL2016 + site.corpus.TGBR2012)}</dd></div>
        <div><dt>Rules drafted</dt><dd className="num">{site.units.total}</dd></div>
        <div><dt>Status</dt><dd>Research prototype</dd></div>
      </dl>
    </header>
  );
}

/* ---------- 2. problem ---------- */
/* Flag emoji do not render on Windows, so the two flags are drawn as SVG. */
function FlagIndia() {
  return (
    <svg className="flag" viewBox="0 0 36 24" width="36" height="24" role="img" aria-label="India">
      <rect width="36" height="8" fill="#FF9933" /><rect y="8" width="36" height="8" fill="#fff" /><rect y="16" width="36" height="8" fill="#138808" />
      <circle cx="18" cy="12" r="3" fill="none" stroke="#000080" strokeWidth="0.8" /><circle cx="18" cy="12" r="0.7" fill="#000080" />
    </svg>
  );
}
function FlagSingapore() {
  const star = (cx = 0, cy = 0) => <circle key={`${cx}${cy}`} cx={cx} cy={cy} r="0.9" fill="#fff" />;
  return (
    <svg className="flag" viewBox="0 0 36 24" width="36" height="24" role="img" aria-label="Singapore">
      <rect width="36" height="12" fill="#ED2939" /><rect y="12" width="36" height="12" fill="#fff" />
      <circle cx="8" cy="6" r="3.6" fill="#fff" /><circle cx="9.4" cy="6" r="3.6" fill="#ED2939" />
      {[[14, 3.2], [11.6, 5.2], [16.4, 5.2], [12.6, 8.4], [15.4, 8.4]].map(([x, y]) => star(x, y))}
    </svg>
  );
}

function ProblemSheet() {
  const [expandedCard, setExpandedCard] = useState<number | null>(null);

  const toggleCard = (index: number) => {
    setExpandedCard(expandedCard === index ? null : index);
  };

  return (
    <Sheet id="problem" sheet="A-02" title="Plans are still checked by reading" className="sheet-dark sheet-fullheight">
      <div className="two-col">
        <div className="prose">
          <p>
            In most Indian cities, officers manually compare 2D building plans against written rules covering setbacks, room sizes and exit widths. Existing digital tools keep these rules locked in proprietary software, hiding how regulations become checks.
          </p>
          <p>
            India lacks an open, machine-readable version of its building bye-laws. NIYAM aims to change this through transparent, traceable checks, where every result links to its original clause and accuracy is measured openly.
          </p>
          <div className="info-accordion">
            <div 
              className={`accordion-item ${expandedCard === 0 ? 'expanded' : ''}`}
              onClick={() => toggleCard(0)}
            >
              <div className="accordion-header">
                <div className="info-card-icon"><FlagIndia /></div>
                <h4>India</h4>
                <span className="accordion-toggle">{expandedCard === 0 ? '−' : '+'}</span>
              </div>
              <div className="accordion-content">
                <p>{CONTEXT.nbc}</p>
              </div>
            </div>
            
            <div 
              className={`accordion-item ${expandedCard === 1 ? 'expanded' : ''}`}
              onClick={() => toggleCard(1)}
            >
              <div className="accordion-header">
                <div className="info-card-icon"><FlagSingapore /></div>
                <h4>Singapore</h4>
                <span className="accordion-toggle">{expandedCard === 1 ? '−' : '+'}</span>
              </div>
              <div className="accordion-content">
                <p>{CONTEXT.singapore}</p>
              </div>
            </div>
            
            <div 
              className={`accordion-item ${expandedCard === 2 ? 'expanded' : ''}`}
              onClick={() => toggleCard(2)}
            >
              <div className="accordion-header">
                <div className="info-card-icon"><img className="bsi-logo" src="/buildingsmart-logo.png" alt="" width="36" height="36" loading="lazy" /></div>
                <h4>buildingSMART</h4>
                <span className="accordion-toggle">{expandedCard === 2 ? '−' : '+'}</span>
              </div>
              <div className="accordion-content">
                <p>{CONTEXT.ids}</p>
              </div>
            </div>
          </div>
        </div>
        <ProblemIllustration />
      </div>
    </Sheet>
  );
}

/* ---------- 3. what NIYAM is: the pipeline, stage by stage, with one real unit ---------- */
function PipelineSheet() {
  return (
    <Sheet id="what" sheet="A-03" title="One sentence, followed all the way through" className="sheet-pipeline-journey">
      <ArchitecturalJourney />
    </Sheet>
  );
}

/* ---------- 4. the gate ---------- */
const STAGE_PLAIN: Record<string, string> = {
  xml_wellformed: "Well-formed XML",
  xsd_valid: "Valid IDS 1.0",
  unit_safe_bounds: "Safe across mm and m",
  loads_in_ifctester: "Loads in the checker",
  applicable_on_fixtures: "Applies to the right elements",
  verdict_pass_fixture: "Good building passes",
  verdict_fail_fixture: "Bad building fails",
};

function GateBox({ g }: { g: NonNullable<typeof site.gateExample> }) {
  return (
    <figure className="test-strip">
      <figcaption>
        <strong>A real rejection.</strong> The draft applied the rule to every door, so the building that follows the
        rule failed.
      </figcaption>
      <ol className="stations">
        {g.stages.map((s: { stage: string; passed: boolean }) => (
          <li key={s.stage} className={s.passed ? "ok" : "stop"}>
            {s.passed ? <IconPassed /> : <IconFailed />}<span>{STAGE_PLAIN[s.stage] ?? s.stage}</span>
            <span className="visually-hidden">{s.passed ? "passed" : "failed here"}</span>
          </li>
        ))}
      </ol>
      <p className="strip-label">Sent back, verbatim:</p>
      <pre className="repair mono">{g.repair_message_head}</pre>
      <Stamp>Run {g.run_id} · {modelLabel(g.model).split(" (")[0]} · {g.repair_rounds} repairs · {g.outcome === "needs_human" ? "needs a person" : g.outcome}</Stamp>
    </figure>
  );
}

function GateSheet() {
  const g = site.gateExample;
  return (
    <Sheet
      id="gate"
      sheet="A-04"
      title="Why an AI draft is never trusted on its own"
      className="sheet-gate sheet-dark"
      aside={g ? <GateBox g={g} /> : null}
    >
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
    </Sheet>
  );
}

/* ---------- 5. two kinds of rules ---------- */
const SPEC_IDS = `<specification name="exit-door-width">
  <entity name="IfcDoor" />
  <property name="Width" value="900" />
</specification>`;

const SPEC_PY = `def check(room):
    area = sum(face.area for face in room.faces)
    return area >= 7.5`;

function KindsSheet() {
  const ids = site.units.byTier["MBBL2016/ids"] ?? 0;
  const geo = (site.units.byTier["MBBL2016/geometric"] ?? 0) + (site.units.byTier["TGBR2012/geometric"] ?? 0);
  return (
    <Sheet id="kinds" sheet="A-05" title="Two kinds of rules" className="sheet-kinds">
      <p className="kinds-lede">What the check has to read decides what it is: a value the model states, or a shape it
        has to measure.</p>

      <div className="kinds">
        <article className="kind kind-declared">
          <p className="kind-index">01 · Declared</p>
          <div className="kind-top">
            <h3>Stated by the model: <Term k="IDS">IDS</Term></h3>
            <p className="kind-count"><span className="num">{ids}</span><span className="kind-count-label">rules</span></p>
          </div>
          <p className="kind-what">Whether a door is an exit, and how wide it is.</p>
          <div className="spec">
            <p className="spec-bar mono"><span>exit-door-width.ids</span><span>IDS 1.0</span></p>
            <pre>{SPEC_IDS}</pre>
          </div>
          <p className="kind-say">A file any IDS-aware tool can run, not only NIYAM.</p>
        </article>
        <article className="kind kind-measured">
          <p className="kind-index">02 · Measured</p>
          <div className="kind-top">
            <h3>Measured from shape: Python</h3>
            <p className="kind-count"><span className="num">{geo}</span><span className="kind-count-label">rules</span></p>
          </div>
          <p className="kind-what">A room's floor area, computed from its geometry.</p>
          <div className="spec">
            <p className="spec-bar mono"><span>space_area_min.py</span><span>Sandbox</span></p>
            <pre>{SPEC_PY}</pre>
          </div>
          <p className="kind-say">IDS cannot measure geometry, so this is a short function with fixed helpers and a time limit.</p>
        </article>
      </div>

      <div className="kind-axis">
        <div className="axis-bar" aria-hidden="true">
          <span className="axis-a" style={{ flexGrow: ids }} />
          <span className="axis-b" style={{ flexGrow: geo }} />
        </div>
        <p className="axis-key mono">
          <span><i className="axis-dot axis-dot-a" />{ids} declared</span>
          <span><i className="axis-dot axis-dot-b" />{geo} measured</span>
          <span className="axis-total">{site.units.total} draft rules</span>
        </p>
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
    <Sheet id="evaluation" sheet="A-06" title="How often a wrong rule gets through" className="sheet-eval">
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
            <Button role="radio" aria-checked={counted === "items"} size="sm" primary={counted === "items"} aria-pressed={counted === "items"} onClick={() => setCounted("items")}>Every attempt</Button>
            <Button role="radio" aria-checked={counted === "units"} size="sm" primary={counted === "units"} aria-pressed={counted === "units"} onClick={() => setCounted("units")}>Per rule</Button>
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
    <Sheet
      id="telangana"
      sheet="A-07"
      title="Telangana"
      kicker="A second jurisdiction"
      className="sheet-telangana sheet-dark"
      aside={
        <div className="case-panel">
          <div className="case-head">
            <p className="case-label">Case study</p>
            <p className="case-count mono"><b>{t.unitsInRun}</b> rules · too few for rates</p>
          </div>
          <div className="table-wrap">
            <table className="data-table">
              <caption className="visually-hidden">Telangana case study counts</caption>
              <thead><tr><th scope="col">Rule</th><th scope="col">Model</th><th scope="col">Mode</th><th scope="col">Shipped</th><th scope="col">Correct</th></tr></thead>
              <tbody>
                {t.caseStudy.map((c) => (
                  <tr key={`${c.unit}-${c.model}-${c.mode}`}>
                    <th scope="row" className="mono">{c.unit}</th>
                    <td className="cell-model" data-label="Model">{modelLabel(c.model).split(" (")[0]}</td>
                    <td className="cell-mode" data-label="Mode"><span className="mode-tag mono">{c.mode}</span></td>
                    <td className="num cell-count" data-label="Shipped">
                      <span className="pips" aria-hidden="true">
                        {Array.from({ length: c.repeats }, (_, i) => <i key={i} data-on={i < c.shipped ? "" : undefined} />)}
                      </span>
                      <span className="count-of">{c.shipped} of {c.repeats}</span>
                    </td>
                    <td className="num cell-count" data-label="Correct">
                      <span className="pips pips-correct" aria-hidden="true">
                        {Array.from({ length: c.repeats }, (_, i) => <i key={i} data-on={i < c.shippedCorrect ? "" : undefined} />)}
                      </span>
                      <span className="count-of">{c.shippedCorrect} of {c.repeats}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  <th scope="row">All rows</th><td /><td />
                  <td className="num">{t.caseStudy.reduce((s, c) => s + c.shipped, 0)} of {t.caseStudy.reduce((s, c) => s + c.repeats, 0)}</td>
                  <td className="num">{t.caseStudy.reduce((s, c) => s + c.shippedCorrect, 0)} of {t.caseStudy.reduce((s, c) => s + c.repeats, 0)}</td>
                </tr>
              </tfoot>
            </table>
          </div>
          <Stamp>Run {t.provenance.runId} · {date(t.provenance.date)} · {thousands(t.provenance.calls)} calls</Stamp>
        </div>
      }
    >
      <div className="prose">
        <p>
          The {site.sources.TGBR2012} went through the same pipeline: {site.corpus.TGBR2012} clauses, read by a new
          segmenter of {site.telanganaSegmenterLines} lines. Only {t.unitsInRun} sentences reduce to one value each,
          once the high-rise condition in the heading is set aside for the reviewer:
        </p>
        <ul className="quotes">
          {site.units.list.filter((u) => u.source === "TGBR2012").map((u) => <li key={u.id}>“{u.text}” <span className="meta mono">{u.id}</span></li>)}
        </ul>
        <p className="prose-foot">
          Most of the document rules on plots — setbacks, road widths — and leaves room sizes and heights to the National
          Building Code, which is not in the corpus.
        </p>
      </div>
    </Sheet>
  );
}

/* ---------- 8. reality check ---------- */
const AUDIT_HEAD: Record<string, string> = { File: "File", Rules: "Rules", passed: "Passed", failed: "Failed", unchecked: "Unchecked", out_of_scope: "Out of scope", "Rules that checked nothing": "Rules that checked nothing" };

function RealitySheet() {
  const [, ...files] = site.realModels.files;
  const [auditHead, ...audit] = site.realModels.audit;
  return (
    <Sheet id="reality" sheet="A-08" title="Reality check: two real models could not be checked" className="sheet-reality">
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
          <thead><tr>{(auditHead ?? []).map((c) => <th key={c} scope="col">{AUDIT_HEAD[c] ?? c}</th>)}</tr></thead>
          <tbody>{audit.map((r) => <tr key={r.join("|")}>{r.map((c, i) => (i === 0 ? <th key={i} scope="row">{c}</th> : <td key={i} className="num">{c}</td>))}</tr>)}</tbody>
        </table>
      </div>
      <h3 className="sub">The files behind the audit</h3>
      <div className="table-wrap">
        <table className="data-table file-table">
          <caption className="visually-hidden">The files, their schema and what they contain</caption>
          <thead><tr><th scope="col">File</th><th scope="col">Schema</th><th scope="col">Tool</th><th scope="col">Unit</th><th scope="col">Doors</th><th scope="col">Rooms</th><th scope="col">Stairs</th></tr></thead>
          <tbody>
            {files.map((f) => (
              <tr key={f[0]}>
                <th scope="row">{f[0]}</th><td>{f[3]}</td><td>{f[4]}</td><td>{f[5]}</td>
                <td className="num">{f[6]}</td><td className="num">{f[7]}</td><td className="num">{f[8]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="meta">Sources and licences: {files.map((f) => `${f[0]} (${f[2]})`).join("; ")}. All public.</p>
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
const icon = (d: string) => (
  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={d} /></svg>
);
const DEMO = [
  { src: "/screens/demo-1-load.png", title: "Load a building", icon: icon("M8 11V2.5M4.5 6 8 2.5 11.5 6M2.5 10.5v3h11v-3"),
    step: "Drop an IFC4 file, or choose sample A. The server audits it in a moment." },
  { src: "/screens/demo-2-verdict.png", title: "Read the verdict", icon: icon("M2 3h12L9.5 8.5V13l-3-1.5V8.5L2 3Z"),
    step: "The answer comes first, in plain words. Below it the 3D view colours every element by verdict." },
  { src: "/screens/demo-3-select.png", title: "Open a failing door", icon: icon("M3 2.5v11l3-3 2 3.5 1.5-.8-2-3.4H11L3 2.5Z"),
    step: "Select a red door. The panel says which rule it breaks, why, and quotes the clause." },
];

function DemoSheet() {
  const [front, setFront] = useState(0);
  const swap = useRef<CardSwapHandle>(null);
  const frontRef = useRef(0);
  frontRef.current = front;

  // A step brings its card to the front by sending the cards in front of it to the back, one by one.
  const show = (i: number) => {
    const turns = (i - frontRef.current + DEMO.length) % DEMO.length;
    for (let t = 0; t < turns; t++) window.setTimeout(() => swap.current?.next(), t * 130);
  };

  return (
    <Sheet id="demo" sheet="A-09" title="What the app looks like" className="sheet-demo">
      <div className="demo">
        <div className="demo-side">
          <ol className="demo-steps">
            {DEMO.map((d, i) => (
              <li key={d.src}>
                <button type="button" className="demo-step" aria-pressed={i === front} onClick={() => show(i)}>
                  <span className="demo-num mono">{String(i + 1).padStart(2, "0")}</span>
                  <span className="demo-text">
                    <span className="demo-title">{d.title}</span>
                    <span className="demo-say">{d.step}</span>
                  </span>
                </button>
              </li>
            ))}
          </ol>
          <div className="btn-row">
            <Button as={Link} to="/app" primary>Open the app</Button>
            <Button as={Link} to={SAMPLE_LINK}>Try sample A now</Button>
          </div>
        </div>

        <figure className="demo-stack">
          <div className="demo-swap">
            <CardSwap
              ref={swap}
              items={DEMO.map((d) => ({ title: d.title, image: d.src, icon: d.icon, alt: `App screenshot: ${d.step}` }))}
              width={680}
              height={470}
              cardDistance={44}
              verticalDistance={50}
              depth={80}
              skewAmount={4}
              visibleCards={3}
              delay={5000}
              theme="light"
              onChange={setFront}
            />
          </div>
          <figcaption className="demo-cap mono">Screenshots of the real app on synthetic sample building A. Drag, click or use the arrow keys.</figcaption>
        </figure>
      </div>
    </Sheet>
  );
}

/* ---------- 10. standards ---------- */
function StandardsSheet() {
  return (
    <Sheet id="standards" sheet="A-10" title="Open standards, open code" className="sheet-standards sheet-dark">
      <div className="std-grid">
        <div className="std-plate"><span className="std-index mono">01</span>
          <p className="std-code"><Term k="IFC">IFC4</Term></p><p className="std-role">The model</p>
          <p className="std-say">Read directly. IFC2X3 files are refused with an explanation instead of a wrong verdict.</p></div>
        <div className="std-plate"><span className="std-index mono">02</span>
          <p className="std-code"><Term k="IDS">IDS 1.0</Term></p><p className="std-role">The rules</p>
          <p className="std-say">Declared-data rules and the readiness file, runnable in other tools.</p></div>
        <div className="std-plate"><span className="std-index mono">03</span>
          <p className="std-code"><Term k="BCF">BCF 2.1</Term></p><p className="std-role">The issues</p>
          <p className="std-say">One issue per broken rule, exported into the design tool that drew the model.</p></div>
        <div className="std-plate"><span className="std-index mono">04</span>
          <p className="std-code">MIT</p><p className="std-role">The code</p>
          <p className="std-say">NIYAM's own source. Clause text is quoted for research; the source PDFs are not redistributed.</p></div>
      </div>
      <p className="std-note">The two real models are CC BY 4.0 (buildingSMART), and the audit table on the previous sheet names them.</p>
    </Sheet>
  );
}

/* ---------- 11. limits ----------
   The sheet is a plan drawing of what is not drawn: every limit is a void in
   the plan, hatched like an unfilled area, and the sheet carries its revision
   stamp. Nothing here is a list of excuses; it is the missing geometry. */
const LIMITS = [
  { title: "No rule is reviewed.", body: <>All {site.units.total} rules are drafts until a domain expert signs them off.</>, span: 6 },
  { title: "Synthetic buildings.", body: "Every accuracy number comes from small generated test buildings.", span: 6 },
  { title: "Small numbers.", body: <>{h.unitsInRun} rules ({site.units.distinct} distinct in all), {h.provenance.repeats} repeats, {h.provenance.models.length} models; every interval is wide.</>, span: 4 },
  { title: "One value per rule.", body: "Each check tests one value of one element; ratios, distances and setbacks are not encoded.", span: 4 },
  { title: "Conditions dropped.", body: "Building-type and use conditions in a clause are left out and noted for the reviewer.", span: 4 },
  { title: "Disputed readings.", body: <>{site.units.readingDependent.length} rules depend on how a clause is read; they are listed first for review.</>, span: 7 },
  { title: "No real building checked.", body: "The real exports we tried lacked the data.", span: 5 },
];

function LimitsSheet() {
  return (
    <Sheet id="limits" sheet="A-11" title="What this does not show, yet" className="sheet-limits">
      <div className="void-plan">
        <div className="plan-bar mono">
          <span>Plan of what is not drawn</span>
          <span>{LIMITS.length} open</span>
        </div>
        <div className="plan-grid">
          {LIMITS.map((l, i) => (
            <article key={l.title} className="void-cell" style={{ "--span": l.span } as React.CSSProperties}>
              <span className="void-id mono">L-{String(i + 1).padStart(2, "0")}</span>
              <h3>{l.title}</h3>
              <p>{l.body}</p>
              <span className="void-mark" aria-hidden="true" />
            </article>
          ))}
        </div>
        <div className="plan-notes">
          <div className="plan-notes-head mono">Open work · what comes next</div>
          <ol className="next">
            <li>Expert review of every rule, starting with the disputed ones.</li>
            <li>Site geometry, so setbacks and plot rules can be checked.</li>
            <li>The National Building Code in the corpus, for room sizes and heights.</li>
            <li>Tests on real exports from Revit, ArchiCAD and other tools.</li>
          </ol>
        </div>
        <div className="plan-foot mono">
          <span>Before expert review</span>
          <span className="void-stamp">Draft — not signed off</span>
        </div>
      </div>
    </Sheet>
  );
}

/* ---------- 12. team and footer ---------- */
type Viewing = { label: string; file: string; about?: string };

function FileRow({ label, file, about, onView }: Viewing & { onView: (v: Viewing) => void }) {
  const ext = file.split(".").pop()!.toUpperCase();
  return (
    <li className="file-row">
      <span className="file-ext mono" aria-hidden="true">{ext}</span>
      <span className="file-label" title={file}><b>{label}</b>{about && <small>{about}</small>}</span>
      <span className="file-actions">
        <Button size="sm" onClick={() => onView({ label, file })}>
          View<span className="visually-hidden"> {label}</span>
        </Button>
        <Button as="a" size="sm" primary href={`/downloads/${file}`} download={file} title={`Download ${file}`}>
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M8 2v8M4.5 7 8 10.5 11.5 7M3 13.5h10" /></svg>
          <span className="visually-hidden">Download {label}</span>
        </Button>
      </span>
    </li>
  );
}

/** A file shown on the page itself: PDFs in a frame, data files as plain text, both from the app's own /downloads folder. */
function FileViewer({ viewing, onClose }: { viewing: Viewing | null; onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [text, setText] = useState<string>("");
  const [state, setState] = useState<"loading" | "ready" | "failed">("loading");
  useEffect(() => {
    const d = dialog.current;
    if (!d) return;
    if (!viewing) { if (d.open) d.close(); return; }
    setState("loading");
    setText("");
    if (!d.open) d.showModal();
    if (viewing.file.endsWith(".pdf")) { setState("ready"); return; }
    let cancelled = false;
    fetch(`/downloads/${viewing.file}`)
      .then((r) => { if (!r.ok) throw new Error(String(r.status)); return r.text(); })
      .then((t) => {
        if (cancelled) return;
        let shown = t;
        if (viewing.file.endsWith(".json")) { try { shown = JSON.stringify(JSON.parse(t), null, 2); } catch { /* show as is */ } }
        setText(shown);
        setState("ready");
      })
      .catch(() => { if (!cancelled) setState("failed"); });
    return () => { cancelled = true; };
  }, [viewing]);
  return (
    <dialog ref={dialog} className="file-viewer" aria-labelledby="viewer-h" onClose={onClose}
            onClick={(e) => { if (e.target === dialog.current) onClose(); }}>
      <div className="viewer-head">
        <div>
          <h2 id="viewer-h">{viewing?.label}</h2>
          <p className="mono">{viewing?.file}</p>
        </div>
        <div className="viewer-actions">
          {viewing && <Button as="a" size="sm" primary href={`/downloads/${viewing.file}`} download={viewing.file}>Download</Button>}
          <Button size="sm" onClick={onClose}>Close</Button>
        </div>
      </div>
      {viewing?.file.endsWith(".pdf") ? (
        <iframe className="viewer-pdf" title={viewing.label} src={`/downloads/${viewing.file}#view=FitH`} />
      ) : (
        <pre className="viewer-body mono" tabIndex={0}>
          {state === "loading" ? "Loading…" : state === "failed" ? "This file could not be loaded. Use Download instead." : text}
        </pre>
      )}
    </dialog>
  );
}


const initials = (name: string) => name.split(/\s+/).slice(0, 2).map((w) => w[0]).join("").toUpperCase();

const EXPLORE: [string, string][] = [["The problem", "problem"], ["How it works", "what"], ["Results", "evaluation"], ["The app", "demo"], ["What it does not show", "limits"], ["Documentation", "docs"]];

function Footer() {
  return (
    <footer className="site-footer ft">
      <div className="ft-inner">
        <section className="ft-brand" aria-label="About NIYAM">
          <p className="ft-mark" translate="no">NIYAM</p>
          <p className="ft-tag">Building bye-laws as machine checks. A research prototype with draft rules.</p>
          <div className="ft-actions">
            <Button as={Link} to="/app" size="sm" primary>Open the app</Button>
            <Button as={Link} to={SAMPLE_LINK} size="sm">Try a sample</Button>
          </div>
        </section>

        <section className="ft-team" aria-labelledby="team-h">
          <p className="ft-label mono">Built by</p>
          <h2 id="team-h" className="ft-team-name">{TEAM.TEAM_NAME}</h2>
          <p className="ft-college">
            <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M1.5 6 8 2.5 14.5 6 8 9.5 1.5 6ZM4 7.6v3.2c0 .9 1.8 1.7 4 1.7s4-.8 4-1.7V7.6" /></svg>
            {TEAM.COLLEGE}
          </p>
          <ul className="ft-members" aria-label="Team members">
            {TEAM.MEMBERS.map((m, i) => (
              <li key={m} className="ft-member">
                <span className={`avatar avatar-${i % 5}`} aria-hidden="true">{initials(m)}</span>
                <span>{m}</span>
              </li>
            ))}
          </ul>
          <div className="ft-mentor">
            <span className="avatar avatar-mentor" aria-hidden="true">{initials(TEAM.MENTOR.replace(/^Dr\.?\s*/, ""))}</span>
            <span className="ft-mentor-text">
              <span className="mentor-badge mono">Mentor</span>
              <span className="ft-mentor-name">{TEAM.MENTOR}</span>
              <span className="ft-mentor-role">{TEAM.MENTOR_ROLE}</span>
            </span>
          </div>
        </section>

        <nav className="ft-explore" aria-label="Explore this page">
          <p className="ft-label mono">Explore</p>
          <ul>
            {EXPLORE.map(([label, id]) => (
              <li key={id}>
                <a href={`#${id}`} onClick={(e) => { e.preventDefault(); document.getElementById(id)?.scrollIntoView({ behavior: "smooth" }); }}>{label}</a>
              </li>
            ))}
          </ul>
        </nav>

        <p className="ft-legal">
          <span>A research prototype: the rules are drafts no expert has reviewed yet, so read every result as a lead to check, not as approval.</span>
          <span>Open source under the MIT licence, built on the IFC4, IDS 1.0 and BCF 2.1 standards.</span>
        </p>
      </div>
    </footer>
  );
}

/* ---------- 12. documentation ---------- */
function DocsSheet() {
  const [viewing, setViewing] = useState<Viewing | null>(null);
  return (
    <Sheet id="docs" sheet="A-12" title="Read the documents" kicker="Documentation" className="sheet-docs">
      <p className="docs-lede">
        Everything behind the numbers on this page: method, results, limits and the files the tools use. Read a PDF here
        or download it; the data files open as plain text.
      </p>
      <div className="docs-grid">
        {DOC_GROUPS.map((g) => (
          <section key={g.title} className={`docs-card${g === DOC_GROUPS[0] ? " docs-card--wide" : ""}`} aria-labelledby={`docs-${g.title.replace(/\W+/g, "-")}`}>
            <h3 id={`docs-${g.title.replace(/\W+/g, "-")}`}>{g.title}</h3>
            <p className="docs-blurb">{g.blurb}</p>
            <ul className="file-list">{g.docs.map((d) => <FileRow key={d.file} {...d} onView={setViewing} />)}</ul>
          </section>
        ))}
      </div>
      <FileViewer viewing={viewing} onClose={() => setViewing(null)} />
    </Sheet>
  );
}

// Home first, so the hero has its own pill. No href: items are buttons and the address bar stays at "/".
const NAV_SECTIONS: { label: string; id: string | null }[] = [
  { label: "Home", id: null },
  { label: "Problem", id: "problem" },
  { label: "How it works", id: "what" },
  { label: "The gate", id: "gate" },
  { label: "Two kinds", id: "kinds" },
  { label: "Results", id: "evaluation" },
  { label: "Telangana", id: "telangana" },
  { label: "Reality", id: "reality" },
  { label: "Demo", id: "demo" },
  { label: "Standards", id: "standards" },
  { label: "Limits", id: "limits" },
  { label: "Docs", id: "docs" },
];
const NAV_ITEMS = NAV_SECTIONS.map(({ label }) => ({ label }));

const sectionTop = (id: string | null) => (id ? document.getElementById(id)!.getBoundingClientRect().top + window.scrollY : 0);

export default function Landing() {
  useDevelop();
  const main = useRef<HTMLElement>(null);

  // Follow the scroll: the pill moves to the section at the top of the viewport. While a click is
  // scrolling the page, the clicked item stays active; afterwards the position is corrected once.
  const [activeNav, setActiveNav] = useState(0);
  const [menuOpen, setMenuOpen] = useState(false);
  const [dockHidden, setDockHidden] = useState(false);
  const dockHold = useRef(false); // pointer or focus is on the bar, or the menu is open
  const holdOpen = useRef(false);
  holdOpen.current = menuOpen;
  // Auto-hide bar (never while the hero at the top is in view): hides after 3 s without activity or when scrolling down; returns on scroll up or a cursor near the top.
  useEffect(() => {
    let timer = 0;
    let lastY = window.scrollY;
    const arm = () => {
      window.clearTimeout(timer);
      timer = window.setTimeout(() => { if (!dockHold.current && !holdOpen.current && window.scrollY > 80) setDockHidden(true); }, 3000);
    };
    const show = () => { setDockHidden(false); arm(); };
    const onScroll = () => {
      const y = window.scrollY;
      if (y < lastY - 2 || y <= 80) show();
      else if (y > lastY + 2 && y > 80 && !holdOpen.current) { window.clearTimeout(timer); setDockHidden(true); }
      lastY = y;
    };
    const onMove = (e: PointerEvent) => { if (e.clientY < 90) show(); else arm(); };
    const onKey = () => show();
    arm();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("pointermove", onMove, { passive: true });
    window.addEventListener("keydown", onKey);
    window.addEventListener("touchstart", arm, { passive: true });
    return () => {
      window.clearTimeout(timer);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("touchstart", arm);
    };
  }, []);
  useEffect(() => {
    document.body.style.overflow = menuOpen ? "hidden" : "";
    const esc = (e: KeyboardEvent) => e.key === "Escape" && setMenuOpen(false);
    window.addEventListener("keydown", esc);
    return () => { window.removeEventListener("keydown", esc); document.body.style.overflow = ""; };
  }, [menuOpen]);
  const pending = useRef<number | null>(null);
  useEffect(() => {
    let idle = 0;
    const onScroll = () => {
      window.clearTimeout(idle);
      if (pending.current !== null) {
        const wanted = pending.current;
        idle = window.setTimeout(() => {
          pending.current = null;
          const off = sectionTop(NAV_SECTIONS[wanted]?.id ?? null) - window.scrollY;
          if (Math.abs(off) > 2) window.scrollBy({ top: off, behavior: "instant" }); // layout moved while scrolling
        }, 140);
        return;
      }
      let found = 0;
      NAV_SECTIONS.forEach((sec, i) => { if (sec.id && sectionTop(sec.id) <= window.scrollY + window.innerHeight * 0.35) found = i; });
      setActiveNav(found);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => { window.removeEventListener("scroll", onScroll); window.clearTimeout(idle); };
  }, []);
  const goTo = (index: number) => {
    pending.current = index;
    setActiveNav(index);
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top: sectionTop(NAV_SECTIONS[index]?.id ?? null), behavior: reduce ? "instant" : "smooth" });
  };

  useEffect(() => {
    document.title = "NIYAM: building bye-laws as machine checks";
  }, []);

  return (
    <div className="landing">
      <a href="#main" className="skip-link">Skip to content</a>

      <div className={`gooey-dock${dockHidden && !menuOpen ? " gooey-dock--hidden" : ""}`}
           onPointerEnter={() => { dockHold.current = true; }} onPointerLeave={() => { dockHold.current = false; }}
           onFocus={() => { dockHold.current = true; }} onBlur={() => { dockHold.current = false; }}>
       <div className="dock-bar">
        <Link to="/" className="brand dock-brand" translate="no">NIYAM</Link>
        <button type="button" className={`burger${menuOpen ? " open" : ""}`} aria-expanded={menuOpen} aria-controls="mobile-menu"
                aria-label={menuOpen ? "Close menu" : "Open menu"} onClick={() => setMenuOpen((o) => !o)}>
          <span /><span /><span />
        </button>
        <GooeyNav
          items={NAV_ITEMS}
          activeIndex={activeNav}
          onChange={goTo}
          theme="light"
          size="md"
          frame={true}
          particleCount={isLowEnd() ? 5 : 15}
          spread={56}
          animationTime={600}
          timeVariance={300}
          gooeyness={0.5}
          wobble={0.5}
          hoverEffect={true}
        />
       </div>
      </div>

      <div id="mobile-menu" className={`mobile-menu${menuOpen ? " open" : ""}`} hidden={!menuOpen}>
        <nav className="mobile-menu-list" aria-label="Sections">
          {NAV_ITEMS.map((it, i) => (
            <button key={it.label} type="button" className={`mobile-menu-link${i === activeNav ? " current" : ""}`}
                    onClick={() => { setMenuOpen(false); goTo(i); }}>{it.label}</button>
          ))}
          <Link to="/app" className="mobile-menu-link" onClick={() => setMenuOpen(false)}>Open the app</Link>
        </nav>
      </div>

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
        <DocsSheet />
        <section className="sheet sheet-cta" data-sheet aria-labelledby="cta-h">
          <span className="cta-glow cta-glow-a" aria-hidden="true" />
          <span className="cta-glow cta-glow-b" aria-hidden="true" />
          <div className="sheet-inner cta-glass">
            <p className="cta-kicker mono">Your turn</p>
            <h2 id="cta-h">Try it on your building model.</h2>
            <p>Upload an IFC4 file or open a sample building. The audit runs in seconds and exports BCF issues for your design tool.</p>
            <div className="btn-row">
              <Button as={Link} tone="light" to="/app" primary>Open the app</Button>
              <Button as={Link} tone="light" to={SAMPLE_LINK}>Try a sample building</Button>
            </div>
            <ul className="cta-chips" aria-label="What you get">
              <li>IFC4 upload</li><li>HTML report</li><li>BCF issues</li><li>JSON export</li>
            </ul>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
