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
- **Free-tier limits.** Each model slot keeps a minimum interval between calls (`OPEN_MODEL_MIN_INTERVAL_S`, default
  1.6 s for NVIDIA's ~40 requests per minute; `HOSTED_LLM_MIN_INTERVAL_S`, default 0). Calls are always one at a time:
  the runner is sequential. On HTTP 429 or 5xx the provider waits for `Retry-After` when the server sends one (up to
  600 s), otherwise backs off exponentially up to 60 s; 429 gets `LLM_RATE_LIMIT_RETRIES` (default 8) attempts, other
  errors `LLM_MAX_RETRIES`. The run pauses and resumes with the same model. If retries run out, the run **stops**:
  the items so far are written, `stopped_early` names the model, mode and unit, and no unit is skipped.
- **Only `wait` is implemented, not `on_limit: switch`.** Switching models mid-run would mix two models' answers in
  one gated repair loop and need a separate fallback path through scoring and reports; every item is answered by the
  model it names, so the fallback count is always 0.
- **Several models per provider, optional models.** A config model may set `model:` (a model id on its role's
  endpoint, with the same key and limits) and `optional: true`. An optional model that fails the preflight is skipped
  by `run` and recorded in `results.json` as `skipped_models` (and in summary.md and slides-data.md); a required one
  blocks the run, and so does having no model left.
- **Sources.** `units.source: [MBBL2016]` or `[TGBR2012]` selects units by source; summary.md, slides-data.md and both CSVs show each source in its own section (CSV column `source`) and never merge them. A plan that selects no unit is refused.
- **Case studies.** A source with fewer than 5 units in a run is reported as "case study, n too small for rates": counts and per-unit outcomes only, and its CSV rows keep counts with the rate and interval cells empty.
- **Excluding a model.** `skip: "<reason>"` on a config model keeps it out of plan, preflight and run; the reason is
  recorded in `skipped_models`.
- **Repeats are correlated.** The item-level tables are labelled "items, correlated across repeats": with
  repeats > 1 their Wilson intervals overstate precision. summary.md and slides-data.md therefore add a unit-level
  view per model x mode: wrong_shipped per unit (a unit is wrong if any repeat shipped a held-out-wrong rule; n =
  units that shipped at least once), a stability table (units whose (shipped, held-out correct) outcome is identical in
  every repeat vs varied), and each unit's share of repeats that shipped a held-out-correct rule.
- **Hidden reasoning.** `HOSTED_LLM_EXTRA_BODY` / `OPEN_MODEL_EXTRA_BODY` (JSON) are merged into every request, e.g.
  to turn off thinking; they are recorded in `results.json` as `request_extras`.

## The first real run, step by step

1. `cp eval/config.example.yaml eval/config.yaml` (gitignored). Name the models, keep `repeats: 1` and low budget
   caps for the first run, and optionally add `price_per_million_input` / `price_per_million_output` from the
   provider's current price list. Keys stay in `.env` (see `.env.example`), never in the config.
2. `python -m app.eval.cli preflight` makes **one** tiny call per configured model ("Reply with the single word OK.")
   and never compiles. It lists which variable NAMES are set or missing (never their values), the provider class,
   the base URL host and the model name, then the call's latency and token counts. Errors are shown as an HTTP status
   class and a fixed sentence, never the server's text or headers. Exit code 0 only if at least one model is
   configured and every configured model answered. Unconfigured models are listed as `skipped: not configured`.
   The result is stamped in `eval/runs/.preflight.json` (model labels, time, success; no keys).
3. `python -m app.eval.cli plan` prints the worst-case LLM calls and a **rough token estimate (characters / 4)**
   built from the actual system and user prompts of every unit, assuming every answer uses `max_tokens` and every
   gated unit needs all repairs with the history resent each time. With prices configured it shows a worst-case
   cost; otherwise "no price configured". It compares the total with `max_total_tokens`.
4. `python -m app.eval.cli run --yes` refuses to start unless every selected model passed a preflight on this machine
   in the last 24 hours (`--skip-preflight` overrides it with a printed warning). Dry runs need no preflight.
5. `python -m app.eval.cli report ../eval/runs/<id>/results.json` writes `eval/results/<id>/summary.md`.

**Before quoting any number** from a real run, the results table must show: the run id, date and git commit
(not `-dirty`), the rulepack hash, the model labels and provider classes, temperature, max repairs, repeats, `n` for
every cell with its Wilson interval, both the all-units and the distinct-rules views, and `dry_run=false`.
Quote rates only with their n and interval; with n this small, do not claim a difference between models or modes.

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
