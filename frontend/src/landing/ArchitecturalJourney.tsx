// ArchitecturalJourney.tsx — Sheet A-03
// Layout: left column = stepper + stage text + dots
//         right column = large image, top-aligned with the lede, full height
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import siteJson from "../data/site-data.json";
import type { SiteData } from "../data/buildSiteData";
import { IconFailed, IconPassed, IconUnchecked } from "../icons";

const site = siteJson as unknown as SiteData;
const ex   = site.workedExample;

const STAGES = [
  { key: "clause",   num: "01", name: "Clause",   img: "/journey/stage-01-clause.webp",   alt: "Blueprint of exit doorway with ≥ 1.0 m width annotation" },
  { key: "draft",    num: "02", name: "Draft",    img: "/journey/stage-02-draft.png",    alt: "Blueprint doorway with open door and ≥ 1.0 m dimension" },
  { key: "gate",     num: "03", name: "Gate",     img: "/journey/stage-03-gate.png",     alt: "Two test buildings: one passing (1.2 m), one failing (0.8 m)" },
  { key: "rulepack", num: "04", name: "Rulepack", img: "/journey/stage-04-rulepack.png", alt: "Card file box with rule cards filed in a rulepack" },
  { key: "audit",    num: "05", name: "Audit",    img: "/journey/stage-05-audit.png",    alt: "Audited building: red door fails (0.8 m), green passes (1.2 m), amber unchecked (0.9 m)" },
  { key: "view",     num: "06", name: "3D View",  img: "/journey/stage-06-3d.png",       alt: "3D cutaway building with verdict-coloured elements" },
] as const;

// ─── Fade ─────────────────────────────────────────────────────────────────────
function Fade({ id, children }: { id: number; children: React.ReactNode }) {
  // The old content fades out first and is swapped while invisible, so a new stage never flashes in early.
  const [shown, setShown] = useState({ id, children });
  const [visible, setVisible] = useState(true);
  useEffect(() => {
    if (id === shown.id) { setShown({ id, children }); return; }
    setVisible(false);
    const t = setTimeout(() => { setShown({ id, children }); setVisible(true); }, 170);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);
  return <div className={`j-fade ${visible ? "j-fade-in" : "j-fade-out"}`}>{shown.children}</div>;
}

// ─── Stage left-column content only (no image) ───────────────────────────────
function StageClause() {
  return (
    <div className="j-stage-content">
      <p className="j-stage-num">01 / CLAUSE</p>
      <h3 className="j-stage-title">Clause</h3>
      <p className="j-stage-desc">A sentence from the bye-law, quoted word for word.</p>
      <figure className="j-quote-card">
        <blockquote className="j-quote-text">"{ex.text}"</blockquote>
        <figcaption className="j-quote-cite">
          <span className="j-cite-src">MBBL 2016</span>
          <span aria-hidden="true"> · </span>
          Clause {ex.clauseId.split("-")[1]}
          <span aria-hidden="true"> · </span>
          Page {ex.page}
        </figcaption>
      </figure>
      <p className="j-stage-note">Each rule keeps the clause number and page it came from, so a reader can check it against the source.</p>
    </div>
  );
}

function StageDraft() {
  return (
    <div className="j-stage-content">
      <p className="j-stage-num">02 / DRAFT</p>
      <h3 className="j-stage-title">Draft</h3>
      <p className="j-stage-desc">An AI model writes a machine check for that sentence.</p>
      <div className="j-code-card" role="figure" aria-label="Draft IDS file">
        <div className="j-code-header">
          <span className="j-dot" /><span className="j-dot" /><span className="j-dot" />
          <span className="j-code-filename">exit-doorway-width.ids</span><span className="j-eg">example</span>
        </div>
        <dl className="j-code-body">
          <div className="j-code-row"><dt>min_exit_width</dt><dd>1.0 m</dd></div>
          <div className="j-code-row"><dt>applies_to</dt><dd>IfcDoor[FireExit=true]</dd></div>
          <div className="j-code-row"><dt>source</dt><dd>MBBL 2016 §{ex.clauseId.split("-")[1]}</dd></div>
          <div className="j-code-row"><dt>status</dt><dd><span className="j-pill-draft">draft</span></dd></div>
        </dl>
      </div>
      <p className="j-stage-note">The check is written as an IDS file: an open standard that any compatible tool can open and run.</p>
    </div>
  );
}

function StageGate() {
  return (
    <div className="j-stage-content">
      <p className="j-stage-num">03 / GATE</p>
      <h3 className="j-stage-title">Gate</h3>
      <p className="j-stage-desc">The draft must behave correctly on two test buildings.</p>
      <div className="j-gate-list">
        <p className="j-gate-eg"><span className="j-eg">example</span> two made-up test buildings</p>
        <div className="j-gate-row j-gate-pass">
          <span className="j-gate-icon"><IconPassed /></span>
          <div className="j-gate-body">
            <strong>Test building A</strong>
            <span className="j-gate-dim">exit width 1.2 m — passes</span>
          </div>
        </div>
        <div className="j-gate-row j-gate-fail">
          <span className="j-gate-icon"><IconFailed /></span>
          <div className="j-gate-body">
            <strong>Test building B</strong>
            <span className="j-gate-dim">exit width 0.8 m — fails</span>
          </div>
        </div>
        <p className="j-gate-note">
          Failed drafts are sent back for repair — up to {site.headline.provenance.maxRepairs} attempts.
        </p>
      </div>
    </div>
  );
}

function StageRulepack() {
  return (
    <div className="j-stage-content">
      <p className="j-stage-num">04 / RULEPACK</p>
      <h3 className="j-stage-title">Rulepack</h3>
      <p className="j-stage-desc">Accepted drafts are stored — still marked draft until a domain expert reviews them.</p>
      <div className="j-code-card" role="figure" aria-label="Rulepack entry">
        <div className="j-code-header">
          <span className="j-dot" /><span className="j-dot" /><span className="j-dot" />
          <span className="j-code-filename">rulepack / v0 / {ex.clauseId}</span><span className="j-eg">example</span>
        </div>
        <dl className="j-code-body">
          <div className="j-code-row"><dt>rule</dt><dd>exit doorway width</dd></div>
          <div className="j-code-row"><dt>file</dt><dd>exit-doorway-width.ids</dd></div>
          <div className="j-code-row"><dt>gate</dt><dd>passed both test buildings</dd></div>
          <div className="j-code-row"><dt>review</dt><dd><span className="j-pill-draft">draft, not human-reviewed</span></dd></div>
        </dl>
      </div>
      <p className="j-stage-note">Nothing here is a reviewed legal rule yet. The rules are drafts, and the app says so on every page.</p>
    </div>
  );
}

function StageAudit() {
  return (
    <div className="j-stage-content">
      <p className="j-stage-num">05 / AUDIT</p>
      <h3 className="j-stage-title">Audit</h3>
      <p className="j-stage-desc">The checks run on an uploaded IFC4 model.</p>
      <div className="j-model-card">
        <div className="j-model-row j-model-title-row">
          <span className="j-model-icon" aria-hidden="true">
            <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M8 1L15 5v6l-7 4L1 11V5z"/><path d="M1 5l7 4 7-4M8 9v6"/></svg>
          </span>
          <strong>Model: Building_A.ifc</strong><span className="j-eg">example</span>
        </div>
        <div className="j-model-row"><span className="j-model-key">Format</span><span className="j-model-val">IFC4</span></div>
        <div className="j-model-row"><span className="j-model-key">Elements</span><span className="j-model-val">4,218</span></div>
        <div className="j-model-row"><span className="j-model-key">Checked</span><span className="j-model-val">12.4 s</span></div>
      </div>
      <div className="j-verdict-stack" aria-label="Verdict key">
        <div className="j-verdict-card j-verdict-pass">
          <span className="j-verdict-icon"><IconPassed /></span>
          <div><strong>Pass</strong><span>Meets the rule</span></div>
        </div>
        <div className="j-verdict-card j-verdict-fail">
          <span className="j-verdict-icon"><IconFailed /></span>
          <div><strong>Fail</strong><span>Smaller than 1.0 m</span></div>
        </div>
        <div className="j-verdict-card j-verdict-warn">
          <span className="j-verdict-icon"><IconUnchecked /></span>
          <div><strong>Unverified</strong><span>Not enough data</span></div>
        </div>
      </div>
      <p className="j-stage-note">Each element gets one verdict per rule: pass, fail, or unchecked when the model lacks the data.</p>
    </div>
  );
}

function Stage3DView() {
  const [filter, setFilter] = useState<"all"|"pass"|"fail"|"warn">("all");
  const opts = [
    { k: "all"  as const, label: "All",       icon: null             },
    { k: "pass" as const, label: "Passes",    icon: <IconPassed />   },
    { k: "fail" as const, label: "Fails",     icon: <IconFailed />   },
    { k: "warn" as const, label: "Unchecked", icon: <IconUnchecked /> },
  ];
  return (
    <div className="j-stage-content">
      <p className="j-stage-num">06 / 3D VIEW</p>
      <h3 className="j-stage-title">3D View</h3>
      <p className="j-stage-desc">Every element is coloured by its verdict.</p>
      <div className="j-model-card">
        <div className="j-model-row j-model-title-row">
          <span className="j-model-icon" aria-hidden="true">
            <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M8 1L15 5v6l-7 4L1 11V5z"/><path d="M1 5l7 4 7-4M8 9v6"/></svg>
          </span>
          <strong>Model: Building_A.ifc</strong><span className="j-eg">example</span>
        </div>
        <div className="j-model-row"><span className="j-model-key">Format</span><span className="j-model-val">IFC4</span></div>
        <div className="j-model-row"><span className="j-model-key">Checked</span><span className="j-model-val">12.4 s</span></div>
      </div>
      <div className="j-filter-group" role="group" aria-label="Filter by verdict">
        {opts.map(o => (
          <button key={o.k} type="button"
            className={`j-filter-btn j-filter-${o.k}${filter === o.k ? " j-filter-on" : ""}`}
            aria-pressed={filter === o.k}
            onClick={() => setFilter(o.k)}>
            {o.icon && <span aria-hidden="true" className="j-filter-icon">{o.icon}</span>}
            {o.label}
          </button>
        ))}
      </div>
      <p className="j-stage-note">Click an element to see which rule it broke, or which data the model was missing.</p>
    </div>
  );
}

// ─── Main ─────────────────────────────────────────────────────────────────────
export default function ArchitecturalJourney() {
  const [active, setActive] = useState(0);
  // Every stage card has the same fixed size, no scrollbar: the text is scaled up when there is little of it and down when there is a lot.
  const fitRef = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => {
    const el = fitRef.current;
    const body = el?.parentElement;
    if (!el || !body) return;
    const fit = () => {
      el.style.zoom = "1";
      if (window.matchMedia("(max-width: 960px)").matches) return; // stacked layout: natural height
      const cs = getComputedStyle(body);
      const avail = body.clientHeight - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom);
      let lo = 0.55;
      let hi = 1.4;
      for (let i = 0; i < 9; i++) {
        const mid = (lo + hi) / 2;
        el.style.zoom = String(mid);
        if (el.getBoundingClientRect().height <= avail) lo = mid; else hi = mid;
      }
      el.style.zoom = String(lo);
    };
    fit();
    void document.fonts?.ready.then(fit);
    window.addEventListener("resize", fit);
    // the stage content is swapped after a short fade, so refit whenever it changes
    const swapped = new MutationObserver(() => requestAnimationFrame(fit));
    swapped.observe(el, { childList: true, subtree: true });
    return () => { window.removeEventListener("resize", fit); swapped.disconnect(); };
  }, []);
  const go = (i: number) => setActive(Math.max(0, Math.min(STAGES.length - 1, i)));
  const stage = STAGES[active]!;

  // Arrow keys move between tabs and focus the new one (WAI-ARIA tabs pattern)
  const onKey = (e: React.KeyboardEvent) => {
    const next = e.key === "ArrowRight" || e.key === "ArrowDown" ? active + 1
      : e.key === "ArrowLeft" || e.key === "ArrowUp" ? active - 1
      : e.key === "Home" ? 0 : e.key === "End" ? STAGES.length - 1 : null;
    if (next === null) return;
    e.preventDefault();
    const i = Math.max(0, Math.min(STAGES.length - 1, next));
    go(i);
    requestAnimationFrame(() => document.getElementById(`j-tab-${i}`)?.focus());
  };

  return (
    <div className="j-wrap" data-stage={stage.key}>
      <p className="j-lede">NIYAM is a pipeline. Follow an architectural regulation from legal text to a 3D building audit.</p>

      {/* Six equal tabs: the whole pipeline is always visible, and the page never moves when you switch */}
      <div className="j-tabs" role="tablist" aria-label="Pipeline stages" onKeyDown={onKey}>
        {STAGES.map((s, i) => (
          <button key={s.key} type="button" role="tab" id={`j-tab-${i}`}
            aria-selected={i === active} aria-controls="j-panel" tabIndex={i === active ? 0 : -1}
            className={`j-tab${i === active ? " j-on" : ""}${i < active ? " j-past" : ""}`}
            onClick={() => go(i)}>
            <span className="j-tab-num">{s.num}</span>
            <span className="j-tab-name">{s.name}</span>
          </button>
        ))}
      </div>

      <div className="j-panel" id="j-panel" role="tabpanel" aria-labelledby={`j-tab-${active}`}>
        <div className="j-card">
          <div className="j-card-body">
           <div className="j-fit" ref={fitRef}>
            <Fade id={active}>
              {active === 0 && <StageClause />}
              {active === 1 && <StageDraft />}
              {active === 2 && <StageGate />}
              {active === 3 && <StageRulepack />}
              {active === 4 && <StageAudit />}
              {active === 5 && <Stage3DView />}
            </Fade>
           </div>
          </div>
          <div className="j-nav" role="group" aria-label="Stage navigation">
            <button type="button" className="j-nav-btn" onClick={() => go(active - 1)} disabled={active === 0}
              aria-label={active > 0 ? `Previous: ${STAGES[active - 1]?.name}` : "First stage"}>
              <svg width="16" height="12" viewBox="0 0 16 12" fill="none" aria-hidden="true" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M15 6H1M6 1L1 6l5 5" /></svg>
              Prev
            </button>
            <span className="j-nav-count" aria-live="polite" aria-atomic="true">
              {String(active + 1).padStart(2, "0")} / {String(STAGES.length).padStart(2, "0")}
            </span>
            <button type="button" className="j-nav-btn j-nav-next" onClick={() => go(active + 1)} disabled={active === STAGES.length - 1}
              aria-label={active < STAGES.length - 1 ? `Next: ${STAGES[active + 1]?.name}` : "Last stage"}>
              Next
              <svg width="16" height="12" viewBox="0 0 16 12" fill="none" aria-hidden="true" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M1 6h14M10 1l5 5-5 5" /></svg>
            </button>
          </div>
        </div>

        {/* The drawing always sits on the same blueprint plate, so every stage looks the same size */}
        <figure className="j-plate">
          <div className="j-plate-img" aria-hidden="true">
            <Fade id={active}>
              <img key={stage.key} src={stage.img} alt={stage.alt} className="j-img" loading="eager" />
            </Fade>
          </div>
          <figcaption className="j-img-cap">
            <span className="j-eg">illustration</span> Made for the interface. Example values, not a real building or a result.
          </figcaption>
        </figure>
      </div>
    </div>
  );
}
