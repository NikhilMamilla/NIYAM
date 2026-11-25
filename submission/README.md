# submission

The DBI 2026 Stage 2 package for jurors: `deck/` (the slide PDF and PPTX), `samples/` (five audited IFC models
with their BCF/HTML/JSON reports and truth files), `screens/` (slide screenshots), `demo-script.md` and
`video/narration.md` (the shot-by-shot script), `deck-facts.md` (every number with its source), `how-to-run.md`,
`email.md` (the submission email draft) and `CHECKLIST.md` (what is sent and what is still open).

Mostly written by hand; `samples/` and `screens/` are built by `scripts/build_sample_buildings.py` and
`scripts/build_slide_figures.py`. `video/*.webm` is gitignored: the team records its own demo (`npx playwright
test demo-video`).

Used by: the DBI 2026 organisers and reviewers.
