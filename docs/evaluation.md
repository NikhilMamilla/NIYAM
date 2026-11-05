# Evaluation harness

The headline question: **how often does a wrong rule reach the rulepack, with and without the verifier gate, per
model?** `backend/app/eval/` answers it by compiling every pilot unit with each configured model in two modes,
then scoring the shipped rule on fixtures the gate never saw.

## Why held-out fixtures

The gate accepts a rule when it is right on the unit's dev pass/fail pair (`fixtures/ifc/`). Scoring on that same
pair would be circular: every gated rule would look correct by construction. `fixtures/heldout/` holds a second
pair per unit, built by `scripts/build_heldout.py`, that:

- uses different values and element names, and a different project length unit (metres; the dev pairs are mm);
- contains a **boundary pair** for each quantitative unit: exactly the threshold must pass (the clauses say "not
  less than"), and just under it (0.99 m, 1.79 m², 2.74 m) must fail, so `>` instead of `>=` is caught;
- carries hand-written expected verdicts per element (`<unit>.truth.json`), written from the clause text.

Held-out files are never used by the gate and never appear in a prompt (`tests/test_heldout_leaks.py` checks file
names, element names, GlobalIds and entity lines in every initial and repair prompt of both tiers). The proof that
they add information is `tests/test_heldout.py`: a rule whose threshold is tuned to the dev values (0.95 m for a
1.0 m rule; 1.7 m² for a 1.8 m² rule) passes the dev gate and fails held-out.

## What each metric means

Each (model, mode, unit, repeat) is one item. Its **final candidate** is scored by `score_candidate`
(report-only: nothing is fed back to the model):

| Field | Meaning |
|---|---|
| valid | passes every static stage: IDS `xml_wellformed`, `xsd_valid`, `unit_safe_bounds`; geometric `python_syntax`, `ast_allowlist`, `sandbox_load`, `returns_findings` |
| dev_correct | accepted by the full gate on the dev pair, which is all the gate can see |
| heldout_correct | every element of both held-out models gets its hand-written verdict, boundary elements included |
| vacuous | the rule applies to nothing in any dev or held-out model |
| error | scoring raised or the sandbox failed (recorded; never stops a run) |

**Shipped:** gated mode ships the candidate only when the gate accepted it (`needs_human` ships nothing); ungated
mode ships its single candidate regardless.

Per model × mode, `summary.md` reports counts **and** rates `k/n = rate [Wilson 95% interval]`, with n always shown:

- **valid rate**, **dev_correct rate**, **heldout_correct rate**: over all items.
- **shipped rate**: shipped / items.
- **wrong_shipped rate (the headline)**: shipped rules that are not heldout_correct / shipped rules, i.e. how
  often a wrong rule reaches the rulepack.
- **needs_human rate**, **mean repair rounds** (gated only); **mean tokens**, **mean wall seconds** per unit.
- **Paired table**: on the same unit and repeat, how often gated and ungated both ship a held-out-correct rule,
  only gated does, only ungated does, or neither does.
- **Human edits**: when review decisions exist, the share of reviewed rules whose decision was modify or reject.

The Wilson interval is implemented in `metrics.py` in plain Python (z = 1.95996). Worked example, 7/10:
p = 0.7, z² = 3.8415, denominator 1 + z²/n = 1.38415, centre (0.7 + 0.19207)/1.38415 = 0.6445, half-width
1.95996 · √(0.021 + 0.0096037)/1.38415 = 0.2477, interval **[0.397, 0.892]** (tested).

## Running a real evaluation

```bash
cp eval/config.example.yaml eval/config.yaml      # gitignored: choose models, modes, repeats, budget
cd backend && source .venv/Scripts/activate
python -m app.eval.cli plan                        # units x modes x models x repeats, worst-case LLM calls
python -m app.eval.cli run --yes                   # needs configured providers in .env; writes eval/runs/<id>/
python -m app.eval.cli report ../eval/runs/<id>/results.json   # eval/results/<id>/summary.md and summary.csv
```

- **Budget caps.** `plan` counts the worst case (gated: 1 + `max_repairs` calls per unit; ungated: 1) and refuses
  when it exceeds `budget.max_total_calls`. `run` also stops at `max_total_tokens`, recorded as `stopped_early`.
- **Metadata** in `results.json`: run id, date, git commit (marked `-dirty` for uncommitted changes), rulepack hash,
  model labels and provider classes, temperature, max repairs, system-prompt hashes, budget and usage, `dry_run`.
  API keys are never written.
- An unconfigured provider stops the run before any call, with the missing setting named.

## Dry runs: never quote them

`run --yes --dry-run` replaces every model with `DryRunProvider`, which replays synthetic answers from
`backend/app/eval/dryrun/` (correct, wrong property, inverted logic, off-by-one, overfit threshold, malformed). It
exists only to test the pipeline end to end. Dry runs get `dry_run: true` and a `dryrun-` run id; every report file
starts with **"DRY RUN: synthetic responses, not model results"**; the report generator refuses to write a dry-run
report anywhere under `docs/`; `eval/results/dryrun-*/` is gitignored. **Dry-run numbers are not results and must
never be quoted.**

## Units in an evaluation

Every rule unit with status `pilot` (or `selected`, as configured) is evaluated: the six hand-written pilots and
every unit generated from a rule spec (`docs/specgen.md`). Reports break results down by tier and by template
(`hand-written`, `door_width_min`, `door_operation_forbidden`, `space_area_min`, `space_height_min`).

After `python -m app.corpus.cli review-import <sheet>`, the corpus DB is **not** updated: run
`python -m app.corpus.cli unit-import` to load the updated `rules/corpus/rule-units.yaml`.

## Limitations

- **Tiny n.** Six pilot units (three IDS, three geometric). With n = 6 per cell a 6/6 rate has a 95% interval of
  [61%, 100%]; no comparison at this size is evidence of a real difference. Repeats do not create new units.
- **Synthetic fixtures.** Dev and held-out models are small generated files, not real buildings; a rule correct on
  them can still fail on real authoring-tool output.
- **Threshold encodings** are checked on synthetic IFCs only, against the reading of the clause in the gold
  artifacts, which is itself **not yet human-reviewed** (see `docs/review/review-sheet.csv`).
- **Temperature 0 is not deterministic** across providers or even across calls of one provider; repeats are needed
  before trusting any single run.
- The held-out truth for a unit encodes one reading of the clause; a model that reads the clause differently but
  defensibly is scored as wrong until a reviewer decides.

## Results table (template: fill only from real, non-dry runs)

| model | mode | n | valid | dev_correct | heldout_correct | shipped | wrong_shipped | needs_human | mean repairs | mean tokens |
|---|---|---|---|---|---|---|---|---|---|---|
| | gated | | | | | | | | | |
| | ungated | | | | | | | — | — | |
