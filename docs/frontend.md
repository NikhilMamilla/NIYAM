# Web app (frontend/)

## Stack (exact pins in `frontend/package.json`, lockfile committed)

| Package | Version | Role |
|---|---|---|
| react, react-dom | 19.3.1 | UI |
| @thatopen/components | 3.6.0 | world, camera, renderer, IfcLoader |
| @thatopen/fragments | 3.6.0 | fragments model: colouring, visibility, boxes, picking; worker |
| three | 0.187.0 | rendering |
| camera-controls | 3.1.2 | peer of @thatopen/components |
| web-ifc | **0.0.77** | IFC parsing in the browser (wasm) |
| vite / @vitejs/plugin-react | 8.3.5 / 6.2.1 | dev server and build |
| typescript | 7.0.2 | strict type checking (`tsc -p tsconfig.json`) |
| vitest | 5.1.0 | unit tests for pure logic |
| @playwright/test | 1.64.1 | end-to-end tests (same version as the root, reusing its Chromium) |
| @types/react, @types/react-dom, @types/three, @types/node | 19.3.0, 19.3.0, 0.187.0, 22.20.5 | types |

`@thatopen/components-front` is not used: the fragments model API covers highlighting and picking,
and it would add `potree-core`. There is no linter: the app was scaffolded by hand rather than from
the Vite template, so no ESLint dependencies were added.

**web-ifc is pinned to 0.0.77.** With 0.0.78 the browser build fails while converting any model
(`BindingError: function StreamMeshes called with 4 arguments, expected 3`): its browser wasm does
not match its JavaScript. 0.0.78's Node build works, and That Open 3.6 accepts `>=0.0.77`.

## Offline: no CDN at runtime

- The web-ifc wasm is copied from `node_modules` to `public/web-ifc/` by `npm install`
  (`scripts/copy-wasm.mjs`) and loaded with `autoSetWasm: false`. That Open's default fetches it from
  unpkg.
- The fragments worker is bundled by Vite from `@thatopen/fragments/worker`, instead of
  `FragmentsManager.getWorker()`, which also fetches from unpkg.
- The e2e test asserts that loading and auditing sample A makes no request to any other host.

## How results reach the 3D view

The browser converts the IFC to fragments only after the server has accepted the audit: web-ifc runs
on the main thread and can spin on unreadable bytes, which would freeze the page before the error
banner could appear. Audit records are mapped to viewer ids by GlobalId
(`model.getLocalIdsByGuids`); the viewport's `data-id-mapping` attribute records whether those ids
equal the API's `express_id` (they do for the samples). An element's colour is its most serious
verdict across rules: failed (red) > unchecked (amber) > passed (grey) > out of scope (faded).

## Rooms, stairs and rules that could not run

Geometric findings reach the viewer the same way as door findings (the audit's `express_id`s are mapped to
viewer ids by GlobalId). An element's colour is still its most serious verdict. `IfcSpace` elements are rooms
(volumes) and are drawn translucent (opacity 0.5 for failed/unchecked, 0.3 passed, 0.12 out of scope) so doors and
walls inside them stay visible; stair flights are opaque like doors. Selecting a room or flight shows the
check's sentence ("Computed floor area is 1.50 m2; this rule requires at least 1.8 m2.").

A geometric rule whose check timed out or crashed has status `error` ("Could not run"): the rule list shows
the reason, a note above it counts such rules, and the overall status is never better than Incomplete.

The summary card shows two different numbers: **Checks run** (one per rule × element) and **Doors/Elements
affected** (distinct elements: with violations, could not be fully checked).

## Check manually in a real browser

The e2e suite runs Chromium with SwiftShader (software WebGL). Please confirm in your own browser:

1. The 3D view renders with your GPU in Chrome/Edge and in Firefox (only Chromium was tested).
2. Orbit, pan and zoom feel right with mouse and trackpad; clicking a door selects it, and a click
   that ends a drag does not.
3. "Reset view" and selecting an element animate the camera; with the OS "reduce motion" setting on,
   they jump without animation.
4. Drag-and-drop of an `.ifc` file onto the drop zone (the tests use the file picker).
5. A large real-world IFC4 model: time to view, and that the "may be slow" note appears above 30 MB.
6. Screen-reader output (NVDA or VoiceOver) for the summary, rule list and detail panel.

## Why sample D looked like one red wall (fixed in Phase 13)

Reproduced headless (`docs/screenshots/sample-d-before.png`) and diagnosed with per-element boxes from the
fragments model, not by guessing. Two separate causes:

1. **Viewer: the camera could not frame anything larger than about 150 m.** That Open's camera controls fix
   `maxDistance = 300` and the camera's far plane at 1000. Sample D's model box is 4 km across, so the fit was
   clamped 300 units from the target, inside the volumes. Fix: `src/framing.ts` computes an exact fit (every corner
   of the box inside both field-of-view angles) plus near/far planes and zoom limits from the model's size;
   `viewer.ts` applies them on load and on "Reset view". Unit tests cover a 0.1 m element, sample A, sample E and a
   4 km box; `e2e/viewer-framing.spec.ts` checks every sample is framed with the camera outside the model.
2. **Data: sample D's file stores its room and stair shapes 1000x too large** (a 2.0 m room has a 2,000,000 mm
   profile), while their placements are correct. The viewer draws what the file contains, so these elements are
   kilometres across and overlap. This was a backend unit-conversion bug that the fixtures compensated for; it is
   fixed on branch fix-mm-units (`STATUS.md`), and sample D now draws at its real size. The viewer now shows a notice when audited elements are more
   than 200 m across ("NIYAM draws the file as it is").

A third bug surfaced while checking the fix against sample E's truth file: room edge lines were matched to rooms by
array position, but rooms without geometry return no meshes, so later rooms got their neighbour's verdict colour.
Edges now use each mesh's own id; the e2e check asserts every edge set lies inside its own room's box (it fails with
the old mapping).

After the fix: `docs/screenshots/viewer-sample_*.png`.

## Routes, design system and data

**Routes.** A tiny History API router (`src/router.tsx`, no dependency): `/` is the landing page, `/app` the dashboard,
`/app?sample=<name>` opens a sample. Back/forward and deep links work in `vite` and `vite preview`. The dashboard
(three.js, web-ifc) is a lazy chunk, so the landing page loads no WebGL code.

**Design world: a diazo whiteprint.** Warm print paper, deep ink, one accent in diazo blue-violet, and a dark light-table
for the 3D stage. Tokens live in `src/styles/tokens.css` (colour, type scale, spacing, radius, elevation, motion).
Every text colour pair was checked numerically for WCAG AA. Fonts: Instrument Serif for headings and IBM Plex Sans and Mono (OFL), latin subsets
self-hosted in `public/fonts/`, so nothing is fetched at runtime. Verdicts are always colour, icon and word.
State grammar: pressed = inverted ink, disabled = half-tone, focus = a diazo ring. Plain words first ("Room", "Door");
IFC terms sit behind "Details for experts". Glossary tooltips: IFC, IDS, BCF, gate, unchecked.

**One source of truth for numbers.** `npm run site-data` (Node type stripping, no dependency) reads the committed
results (`eval/results/*/results.json`), the review sheet, the specs, `docs/real-models.md`, the readiness IDS and one real
gate rejection (`docs/examples/gate-rejection.json`, extracted by `scripts/extract_gate_example.py`) and writes
`src/data/site-data.json`. Tests check it is current, that its Wilson intervals and counts equal the Python harness's
CSVs and summaries, and that every number rendered on the landing page traces to it (a hand-typed statistic fails
`src/landing/Landing.test.tsx`). The README's "What NIYAM is, and is not" statements are read into the same file and shown verbatim (hero and sheet
A-11). Context facts in "The problem" (NBC/NBCS, CORENET X, IDS 1.0) live in `src/content/site.ts` and each is checked,
with its source and access date, in `docs/sources.md`.

**Dashboard: one page, top to bottom.** `/app` opens on a start screen: "Check a building model in three steps"
with arrows between the steps, a drop zone ("Choose a file" or drop an `.ifc`) and one card per sample (A to E). Loading a
model replaces it with one column: the headline verdict first, in plain words ("2 doors break a rule..."), with the
status, the distinct-element counts, the per-rule checks behind a disclosure and the exports (HTML report, BCF, JSON);
then the wide 3D stage; then the rules grid with filters and search. Selecting an element in the list or in 3D opens a
detail slide-over that says which rule it breaks or what data is missing, quotes the clause and offers the readiness
IDS. A "Back" button returns to the start screen. There is no tour and no menu. The UI never says "Compliant": the
statuses read "Breaks a rule", "Not fully checked", "No issues found", "Nothing checked". The backend's HTML report
keeps the engine's status names (`docs/audit.md`).

**3D stage (`src/stage.ts`, `src/viewer.ts`).** Procedural sky dome, low warm sun with soft shadows (High quality only),
a paving grid and fog sized to each model, ACES tone mapping, sRGB output; a "Neutral light" toggle. Verdict outlines are
built from each element's real mesh (failed outlines pulse unless reduced motion is set). Camera: eased fly-in, presets
(3D, plan, front), fly-to on selection with the rest dimmed, reset, optional auto-orbit, a hover tooltip. Quality
defaults to Low on devices with 4 or fewer cores, 4 GB or less memory, or narrow screens. Not built: a storey filter
and a section slider. The That Open logo overlay is hidden; That Open Engine is credited in the stage caption.

## Landing page: navigation, buttons, footer documents and weaker devices

**Navigation.** A floating bar holds the NIYAM wordmark and the section pills (a gooey, animated pill follows the active
section). Below 1100 px wide it becomes a frosted strip with the wordmark and a hamburger that opens a full-screen menu
of plain section names. The bar stays visible while the hero is in view; further down it hides after 3 seconds without
activity or when scrolling down, and returns on scroll up, when the cursor nears the top edge, or on a key press. It
stays put while it has pointer or keyboard focus and while the mobile menu is open.

**One button for the whole project.** `src/Button.tsx` wraps `src/SpecularButton.jsx` (React Bits, with an `as` prop so a
router link, anchor or label can be a button). Every action button on the landing page and the dashboard uses it, in the
heading ink colour; `primary` fills it, `tone="light"` is for dark surfaces. All buttons draw their edge light through a
single shared WebGL context into their own 2D canvas, so any number can be on screen (separate contexts per button
exceeded the browser limit and showed broken white boxes). Toggles, chips, list rows and the viewer toolbar are not
action buttons and keep their own styling. Two buttons side by side always share one width and height.

**Documents (sheet A-12).** The documents are offered as PDFs (`public/downloads/*.pdf`), built from the
repository's Markdown by `npm run docs:pdf` (`scripts/build-pdfs.mjs`: Markdown to styled HTML to A4 PDF through the
Chromium that Playwright already installs). The PDFs are committed, so a normal build needs no Chromium. The three data
files (readiness IDS, review sheet CSV, gate rejection JSON) are copied unchanged by `scripts/sync-downloads.mjs`.

**Weaker devices.** `src/perf.ts` marks a device as low-end (4 or fewer cores, 4 GB or less memory, data saver, or reduced
motion) and adds an `lite` class to the page. There the buttons are plain CSS, blur filters and the large glow shapes are
switched off, the navigation uses fewer particles, and the 3D view defaults to Low quality.
