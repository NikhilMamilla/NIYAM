# Product

Inferred from the Phase 13 brief and the repository on 2026-11-19, while the owner was away (no interview round was
possible: "I will be asleep; work unattended"). Every line marked (inferred) awaits the owner's confirmation.

## Platform

web

## Stack

React 19 + TypeScript, Vite, That Open Engine / three.js for the 3D view; FastAPI backend audits IFC4 files. Offline at
runtime: no CDN, no external fonts or requests.

## Users

- A civil engineer, architect or plan-scrutiny officer in an Indian urban local body who wants to know whether a
  building model can be checked against bye-law clauses automatically. (inferred)
- A juror or reviewer of the research project, judging whether the claims are honest and the method is sound. (brief)
- A modeller preparing an IFC4 file who needs to know what data to add before submitting. (repo: readiness IDS)

## Product Purpose

NIYAM turns sentences from Indian building bye-laws (MBBL 2016; Telangana Building Rules 2012, G.O.Ms.No.168, original
text) into machine checks (buildingSMART IDS for declared data, small sandboxed Python checks for geometry), gates every
LLM-drafted rule against test models, and audits IFC4 models with results shown in 3D and exported as HTML and BCF.

## Positioning

A research prototype that is honest about its limits: draft rules, not human-reviewed; synthetic test buildings; small
n. Openness (IFC4, IDS 1.0, BCF 2.1, MIT licence) is the point. Never "compliant", "approved", "accurate" or "proven"
about any real building. (brief)

## Operating Context

Read on a laptop or projector during a review, and on a phone when the link is shared (inferred). The dashboard is used
at a desk with a mouse, sometimes keyboard-only.

## Capabilities and Constraints

- Every number shown comes from committed data (`frontend/src/data/site-data.json`, generated and tested).
- The 3D view draws only what the IFC contains; the environment around it may be added.
- Verdicts: failed, unchecked (could not be checked), passed, out of scope. Colour is never the only signal.

## Brand Commitments

Calm, architectural, precise: a high-end technical journal meets a modern BIM tool. Light theme, warm paper ground,
deep ink, one confident accent, a dark neutral 3D stage. Badge "Draft rules, not human-reviewed" stays. (brief)

## Evidence on Hand

Real evaluation runs (headline run 2, pilot run 1, Telangana case study), one real gate rejection, the readiness IDS,
two real IFC4 exports and five synthetic samples with screenshots. No photographs of buildings; no logos beyond text.

## Product Principles

1. Prove, don't claim: show the gate rejecting a real draft, show intervals and n.
2. Plain words first ("Room", "Door"); IFC/IDS terms behind "Details for experts".
3. The caveat travels with the number.

## Accessibility & Inclusion

WCAG AA contrast, visible focus, full keyboard path, screen-reader text for the 3D view, prefers-reduced-motion
respected everywhere, verdicts paired with icon and text.
