# eval

The evaluation harness's configs (`config.example.yaml`, `config.dryrun.yaml`, `config.tgbr.yaml`; the real
`config.yaml` with local model choices is gitignored) and `results/`, the committed output of every run this
project reports: the pilot, the headline run 2, the Telangana case study, and the millimetre-fix re-score.

Produced by `backend/app/eval` (`python -m app.eval ...`); `eval/runs/`, its raw per-attempt logs, is gitignored.

Used by: `scripts/check_numbers.py`, `submission/deck-facts.md`, and every rate quoted in README/STATUS.
