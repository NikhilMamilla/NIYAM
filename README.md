# NIYAM

NIYAM turns sentences from Indian building bye-laws (currently the MoHUA Model Building Bye-Laws 2016) into
machine checks: buildingSMART [IDS 1.0](https://github.com/buildingSMART/IDS) files for declared data and small
sandboxed Python checks for values computed from geometry. Every candidate rule, whether written by a person or
an LLM, must pass a verifier gate on test models before it can be used. It then audits IFC building models, shows
the results beside the model in 3D, and exports HTML reports and BCF issues.

**Status: research prototype.** Every rule is a draft that no domain expert has reviewed yet, and all test
buildings are synthetic.

## Pipeline

```
 MBBL 2016 PDF ──> corpus (445 clauses) ──> rule units (verbatim sentences)
                                                │
                    hand-written spec ──────────┤──── or LLM compiler (gated / ungated)
                                                ▼
                     candidate IDS / Python check
                                                │
       verifier gate on dev fixtures: schema, sandbox, pass model must pass, fail model must fail
                                                │ accepted
                                                ▼
          draft rulepack ──> human review sheet ──> reviewed rulepack (none reviewed yet)
                                                │
   IFC model ──> audit engine ──> JSON, HTML report, BCF, web app with 3D viewer

   evaluation: compile per model x mode, score on held-out fixtures the gate never sees
```

## Status

| Area | State |
|---|---|
| Corpus: MBBL 2016, 445 clauses, search and curation CLI | works |
| Rule units: 25 verbatim units (6 hand-written pilots, 19 from rule specs; 3 tagged as duplicates) | works; **drafts, not human-reviewed**; each is a single-element threshold, conditions in the clause are not encoded |
| IDS gate and sandboxed geometric gate | works (the sandbox is defence in depth, not a hard security boundary) |
| LLM compiler, both tiers, with gated repair loop | works with scripted test providers; **no real LLM results yet** |
| Rulepack v0: 6 rules (3 door IDS, 3 room/stair Python) | works; **drafts, not reviewed** |
| Audit engine, HTML and BCF export, upload API, web app with 3D viewer | works on synthetic IFC4 models |
| Evaluation harness: held-out scoring, Wilson intervals, dry run, live-run preflight | works; dry-run numbers are synthetic and must never be quoted |
| Review sheet for domain experts | exported; **no decisions returned yet** |
| Real buildings, other states' bye-laws (e.g. Telangana), more rule templates | not built |

## Quickstart

Requirements: Python 3.11, Node.js 20+, git.

**Windows (PowerShell)**

```powershell
cd backend; python -m venv .venv; .venv\Scripts\Activate.ps1; pip install -e ".[dev]"; pytest -q; cd ..
cd frontend; npm ci; npm test; cd ..
.\scripts\demo.ps1          # starts API + web app, opens http://localhost:5173, Ctrl+C stops both
```

**Linux / macOS**

```bash
cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]" && pytest -q && cd ..
cd frontend && npm ci && npm test && cd ..
./scripts/demo.sh           # starts API + web app, opens http://localhost:5173, Ctrl+C stops both
```

No API key is needed for anything except the LLM compiler and a real evaluation run.

### Audit demo without any API key

```bash
cd backend && source .venv/bin/activate      # Windows: .venv\Scripts\Activate.ps1
python -m app.audit.cli run ../fixtures/samples/sample_a_mm.ifc --out ../eval/runs/audit-demo
```

It prints a per-rule table and writes `report.json`, `report.html` and `issues.bcf`. In the web app, click
"Try sample A" (doors) or "Try sample D" (rooms and stairs).

### Reproduce the dry run (synthetic answers, no key)

```bash
cd backend                                    # with the venv active
python -m app.eval.cli --config ../eval/config.dryrun.yaml plan
python -m app.eval.cli --config ../eval/config.dryrun.yaml run --yes --dry-run
```

The report in `eval/results/dryrun-*/summary.md` starts with **"DRY RUN: synthetic responses, not model results"**.
Its numbers only show that the pipeline works; never quote them. For a real run see `docs/evaluation.md`
(preflight, plan with token estimate, then run).

## Limitations

- **Synthetic fixtures.** Dev, held-out and sample models are small generated boxes, not real buildings or
  authoring-tool exports.
- **Drafts.** Every rule encodes one reading of a clause and none is human-reviewed yet
  (`docs/review/REVIEWER_GUIDE.md`).
- **Coverage.** The 25 units are every MBBL 2016 sentence found so far that fits a single-element template cleanly; the Stage 1 target of 40 to 60 clauses is not met (see `docs/spec-backlog.md` for why the rest do not fit).
- **Single-element thresholds.** The templates check one value of one element (a door width, a room's area or
  height). Ratios, counts, distances and relations between elements are not encoded (`docs/spec-backlog.md`).
- **Ignored conditions.** Building-type exceptions (e.g. 2 m doorways in assembly buildings), room-use conditions
  and second thresholds in the same sentence are dropped and only noted for the reviewer.
- **Thresholds are checked against the text, not its meaning** (`docs/specgen.md`).
- **Small n.** With 25 units (22 distinct) every evaluation interval is wide (`docs/evaluation.md`).

## More

- `docs/evaluation.md`: metrics, held-out fixtures, the first real run.
- `docs/specgen.md` and `docs/spec-backlog.md`: rule specs and what they cannot express.
- `docs/geometric-gate.md`: the Python sandbox and what it does not enforce.
- `docs/modelling-profile.md`: what an IFC model must contain to be checkable.
- `docs/review/`: the review sheet and the reviewer guide.
- `python scripts/check_public_ready.py`: scans the tree and history for secrets and personal paths.

## License

MIT (see `LICENSE`). Clause text is quoted from the publicly available MoHUA Model Building Bye-Laws 2016 for
research purposes; the source PDF is not redistributed (`rules/source/` is ignored).
