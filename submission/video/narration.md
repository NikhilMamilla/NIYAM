# Narration for niyam-demo-silent.webm

The recording is silent; read these lines aloud over it, or record them separately and mux the audio in. Start
times are from `frontend/e2e/demo-video.spec.ts`'s shot boundaries, matching `submission/demo-script.md`.

| Start | Shot | Say |
|---|---|---|
| 0:00 | Start screen | "NIYAM checks an IFC building model against rules drafted from Indian bye-laws. You load a model in three steps." |
| 0:10 | Load sample | "This is a synthetic test building with twelve doors. The server audits it against six draft rules." |
| 0:20 | Verdict | "The answer comes first, in plain words: which doors break a rule and which could not be checked. Missing data is never counted as a pass." |
| 0:35 | 3D selection | "Red is a failed check. Selecting a door opens its detail panel." |
| 0:50 | Clause card | "Each result names its rule and quotes the clause it comes from, here MBBL 2016, page 100." |
| 1:05 | BCF export | "The issues export as BCF 2.1, one topic per problem, for the design tool that drew the model." |
| 1:15 | Honest limitation | "These rules are drafts that no expert has reviewed yet, and on the two real models we tried most rules could not check anything, because the data was missing. NIYAM is a decision aid, not an approval." |

Total: about 85 s of narration against an 89.5 s recording; the recording holds the last shot open slightly past
1:25 before the context closes. Lines are taken verbatim from `submission/demo-script.md`.
