# Demo script (60 to 90 seconds)

Before the demo: run `.\scripts\demo.ps1` (see `how-to-run.md`), wait for the browser, and open
`http://localhost:5173/app` in a 1920x1080 window. Everything shown is on NIYAM's synthetic sample building A.

Every click below is executed in order by `frontend/e2e/demo-script.spec.ts` (`npx playwright test demo-script`),
which also writes the machine timings to `frontend/test-results/demo-timings.json`. Measured on 25 November 2026,
headless Chromium with software WebGL: the clicks themselves take 31.7 s from opening the page to the BCF download.
The speaking time below fills the rest.

| # | Time | Shot | Click exactly | Say |
|---|---|---|---|---|
| 1 | 0:00 to 0:10 | Start screen | (nothing: the page is open on `/app`) | "NIYAM checks an IFC building model against rules drafted from Indian bye-laws. You load a model in three steps." |
| 2 | 0:10 to 0:20 | Load sample | **Open sample A** (the button in step 1) | "This is a synthetic test building with twelve doors. The server audits it against six draft rules." |
| 3 | 0:20 to 0:35 | Verdict | (wait for the verdict at the top, about 1 s; the 3D view is ready about 5 s later) | "The answer comes first, in plain words: which doors break a rule and which could not be checked. Missing data is never counted as a pass." |
| 4 | 0:35 to 0:50 | 3D selection | click a **red door** in the 3D view | "Red is a failed check. Selecting a door opens its detail panel." |
| 5 | 0:50 to 1:05 | Clause card | in the panel, on the failed finding, click **Clause text (MBBL-2016, page 100)** | "Each result names its rule and quotes the clause it comes from, here MBBL 2016, page 100." |
| 6 | 1:05 to 1:15 | BCF export | **Back to rules**, then **BCF issues** at the top | "The issues export as BCF 2.1, one topic per problem, for the design tool that drew the model." |
| 7 | 1:15 to 1:25 | Honest limitation | point at the **Draft rules, not human-reviewed** badge | "These rules are drafts that no expert has reviewed yet, and on the two real models we tried most rules could not check anything, because the data was missing. NIYAM is a decision aid, not an approval." |

Measured machine time per shot (seconds from opening `/app`, from `demo-timings.json`):

| Shot | Reached at |
|---|---|
| 1 start screen shown | 5.9 s |
| 2 verdict shown | 7.0 s |
| 3 3D view ready | 11.6 s |
| 4 failing door selected in 3D | 27.7 s (includes a test-only screenshot to find a red pixel) |
| 5 clause card open | 28.9 s |
| 6 BCF downloaded | 31.7 s |
| 7 draft badge visible | 31.7 s |

If the 3D view is slow on the demo machine, do shot 4 from the list instead: open the second rule and click
**A-G-03 narrow exit**; the same panel opens.
