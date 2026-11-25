# Re-scored after the unit fix (a re-score, not a re-run)

Offline: the final candidate of each geometric item, read from the local attempt logs, scored again with
`app.eval.scoring.score_candidate`. **before** = the code and fixtures at the start of branch fix-mm-units
(reproduces the committed scores); **after** = helpers without the extra scale and regenerated
millimetre fixtures. The committed results under eval/results/<run>/ are unchanged.

This does not replay the generate-verify-repair loop. The gate's pass and fail models changed, so a live
run could repair differently and ship different code: these numbers are "re-scored after the unit fix",
not a corrected headline run.

## 20261118T140452Z-5b7edb

- geometric items: 216
- before-fix re-score equals the committed score: 216 of 216
- items whose score changes after the fix: 0

- `valid`: 0 false -> true, 0 true -> false
- `dev_correct`: 0 false -> true, 0 true -> false
- `heldout_correct`: 0 false -> true, 0 true -> false
- `vacuous`: 0 false -> true, 0 true -> false

- shipped and held-out wrong: 21 before, 21 after (of 199 shipped geometric items)

## 20261118T180916Z-4b9c93

- geometric items: 24
- before-fix re-score equals the committed score: 24 of 24
- items whose score changes after the fix: 0

- `valid`: 0 false -> true, 0 true -> false
- `dev_correct`: 0 false -> true, 0 true -> false
- `heldout_correct`: 0 false -> true, 0 true -> false
- `vacuous`: 0 false -> true, 0 true -> false

- shipped and held-out wrong: 6 before, 6 after (of 22 shipped geometric items)

