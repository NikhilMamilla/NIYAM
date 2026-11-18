# NIYAM evaluation 20261118T133025Z-4c4519

Date 2026-11-18T13:30:25.904374+00:00 · commit `ee865c2a3f971496d4109f623d36ce7a0a3952be` · rulepack `ac3af42db49e` · temperature 0.0 · max repairs 3 · repeats 1 · providers {'nemotron-3-ultra-550b-a55b (NVIDIA)': 'OpenAICompatProvider', 'nemotron-3.5-lightning-30b-a3b (NVIDIA)': 'OpenAICompatProvider'} · dry_run=false

**Skipped model:** glm-4.7-flash (Z.ai): optional model did not pass the preflight at 2026-11-18T13:26:23.548808+00:00

Each cell has n ≤ 25 (n < 30): the 95% intervals are wide; differences between rows are not evidence of a real difference.

Rates are k/n = rate [Wilson 95% interval]. wrong_shipped is over shipped rules: how often a rule that is wrong on the held-out fixtures reaches the rulepack.

## All units

| model | mode | n | valid | dev_correct | heldout_correct | shipped | wrong_shipped | needs_human | mean repairs | mean tokens | mean wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | 25 | 25/25 = 100% [87%, 100%] | 22/25 = 88% [70%, 96%] | 21/25 = 84% [65%, 94%] | 22/25 = 88% [70%, 96%] | 1/22 = 5% [1%, 22%] | 3/25 = 12% [4%, 30%] | 0.44 | 4981.60 | 11.19 |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | 25 | 24/25 = 96% [80%, 99%] | 20/25 = 80% [61%, 91%] | 19/25 = 76% [57%, 89%] | 25/25 = 100% [87%, 100%] | 6/25 = 24% [11%, 43%] | - | - | 2935.24 | 6.38 |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | 25 | 23/25 = 92% [75%, 98%] | 15/25 = 60% [41%, 77%] | 15/25 = 60% [41%, 77%] | 15/25 = 60% [41%, 77%] | 0/15 = 0% [0%, 20%] | 10/25 = 40% [23%, 59%] | 1.28 | 9015.48 | 8.67 |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | 25 | 22/25 = 88% [70%, 96%] | 15/25 = 60% [41%, 77%] | 14/25 = 56% [37%, 73%] | 25/25 = 100% [87%, 100%] | 11/25 = 44% [27%, 63%] | - | - | 2943.20 | 3.59 |

### Paired: gated vs ungated on the same unit and repeat (shipped and held-out correct)

| model | both correct | gated only | ungated only | neither |
|---|---|---|---|---|
| nemotron-3-ultra-550b-a55b (NVIDIA) | 19 | 2 | 0 | 4 |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | 12 | 3 | 2 | 8 |

### Breakdown by tier

| model | mode | tier | n | heldout_correct | shipped | wrong_shipped |
|---|---|---|---|---|---|---|
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | geometric | 18 | 16/18 = 89% [67%, 97%] | 16/18 = 89% [67%, 97%] | 0/16 = 0% [0%, 19%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | ids | 7 | 5/7 = 71% [36%, 92%] | 6/7 = 86% [49%, 97%] | 1/6 = 17% [3%, 56%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | geometric | 18 | 16/18 = 89% [67%, 97%] | 18/18 = 100% [82%, 100%] | 2/18 = 11% [3%, 33%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | ids | 7 | 3/7 = 43% [16%, 75%] | 7/7 = 100% [65%, 100%] | 4/7 = 57% [25%, 84%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | geometric | 18 | 12/18 = 67% [44%, 84%] | 12/18 = 67% [44%, 84%] | 0/12 = 0% [0%, 24%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | ids | 7 | 3/7 = 43% [16%, 75%] | 3/7 = 43% [16%, 75%] | 0/3 = 0% [0%, 56%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | geometric | 18 | 14/18 = 78% [55%, 91%] | 18/18 = 100% [82%, 100%] | 4/18 = 22% [9%, 45%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | ids | 7 | 0/7 = 0% [0%, 35%] | 7/7 = 100% [65%, 100%] | 7/7 = 100% [65%, 100%] |

### Breakdown by template

| model | mode | template | n | heldout_correct | shipped | wrong_shipped |
|---|---|---|---|---|---|---|
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | door_height_min | 1 | 0/1 = 0% [0%, 79%] | 0/1 = 0% [0%, 79%] | 0/0 (n/a) |
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | door_operation_forbidden | 2 | 2/2 = 100% [34%, 100%] | 2/2 = 100% [34%, 100%] | 0/2 = 0% [0%, 66%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | door_width_min | 1 | 1/1 = 100% [21%, 100%] | 1/1 = 100% [21%, 100%] | 0/1 = 0% [0%, 79%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | hand-written | 6 | 5/6 = 83% [44%, 97%] | 6/6 = 100% [61%, 100%] | 1/6 = 17% [3%, 56%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | space_area_min | 6 | 5/6 = 83% [44%, 97%] | 5/6 = 83% [44%, 97%] | 0/5 = 0% [0%, 43%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | space_height_min | 9 | 8/9 = 89% [57%, 98%] | 8/9 = 89% [57%, 98%] | 0/8 = 0% [0%, 32%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | door_height_min | 1 | 0/1 = 0% [0%, 79%] | 1/1 = 100% [21%, 100%] | 1/1 = 100% [21%, 100%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | door_operation_forbidden | 2 | 1/2 = 50% [9%, 91%] | 2/2 = 100% [34%, 100%] | 1/2 = 50% [9%, 91%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | door_width_min | 1 | 1/1 = 100% [21%, 100%] | 1/1 = 100% [21%, 100%] | 0/1 = 0% [0%, 79%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | hand-written | 6 | 4/6 = 67% [30%, 90%] | 6/6 = 100% [61%, 100%] | 2/6 = 33% [10%, 70%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | space_area_min | 6 | 5/6 = 83% [44%, 97%] | 6/6 = 100% [61%, 100%] | 1/6 = 17% [3%, 56%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | space_height_min | 9 | 8/9 = 89% [57%, 98%] | 9/9 = 100% [70%, 100%] | 1/9 = 11% [2%, 43%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | door_height_min | 1 | 1/1 = 100% [21%, 100%] | 1/1 = 100% [21%, 100%] | 0/1 = 0% [0%, 79%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | door_operation_forbidden | 2 | 0/2 = 0% [0%, 66%] | 0/2 = 0% [0%, 66%] | 0/0 (n/a) |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | door_width_min | 1 | 1/1 = 100% [21%, 100%] | 1/1 = 100% [21%, 100%] | 0/1 = 0% [0%, 79%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | hand-written | 6 | 3/6 = 50% [19%, 81%] | 3/6 = 50% [19%, 81%] | 0/3 = 0% [0%, 56%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | space_area_min | 6 | 3/6 = 50% [19%, 81%] | 3/6 = 50% [19%, 81%] | 0/3 = 0% [0%, 56%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | space_height_min | 9 | 7/9 = 78% [45%, 94%] | 7/9 = 78% [45%, 94%] | 0/7 = 0% [0%, 35%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | door_height_min | 1 | 0/1 = 0% [0%, 79%] | 1/1 = 100% [21%, 100%] | 1/1 = 100% [21%, 100%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | door_operation_forbidden | 2 | 0/2 = 0% [0%, 66%] | 2/2 = 100% [34%, 100%] | 2/2 = 100% [34%, 100%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | door_width_min | 1 | 0/1 = 0% [0%, 79%] | 1/1 = 100% [21%, 100%] | 1/1 = 100% [21%, 100%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | hand-written | 6 | 3/6 = 50% [19%, 81%] | 6/6 = 100% [61%, 100%] | 3/6 = 50% [19%, 81%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | space_area_min | 6 | 4/6 = 67% [30%, 90%] | 6/6 = 100% [61%, 100%] | 2/6 = 33% [10%, 70%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | space_height_min | 9 | 7/9 = 78% [45%, 94%] | 9/9 = 100% [70%, 100%] | 2/9 = 22% [6%, 55%] |

## Distinct rules only

Excluded from the distinct view: MBBL2016-4.24.7.2#b (duplicate of MBBL2016-5.4.1#b), MBBL2016-4.24.7.2#c (duplicate of MBBL2016-5.4.1#c), MBBL2016-4.24.7.2#f (duplicate of MBBL2016-5.4.2#1). They encode the same requirement as another unit, so counting both would weight it twice.

| model | mode | n | valid | dev_correct | heldout_correct | shipped | wrong_shipped | needs_human | mean repairs | mean tokens | mean wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | 22 | 22/22 = 100% [85%, 100%] | 19/22 = 86% [67%, 95%] | 18/22 = 82% [61%, 93%] | 19/22 = 86% [67%, 95%] | 1/19 = 5% [1%, 25%] | 3/22 = 14% [5%, 33%] | 0.50 | 5202.05 | 11.56 |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | 22 | 22/22 = 100% [85%, 100%] | 18/22 = 82% [61%, 93%] | 17/22 = 77% [57%, 90%] | 22/22 = 100% [85%, 100%] | 5/22 = 23% [10%, 43%] | - | - | 2877.18 | 6.53 |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | 22 | 21/22 = 95% [78%, 99%] | 14/22 = 64% [43%, 80%] | 14/22 = 64% [43%, 80%] | 14/22 = 64% [43%, 80%] | 0/14 = 0% [0%, 22%] | 8/22 = 36% [20%, 57%] | 1.14 | 8204.14 | 8.13 |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | 22 | 20/22 = 91% [72%, 97%] | 15/22 = 68% [47%, 84%] | 14/22 = 64% [43%, 80%] | 22/22 = 100% [85%, 100%] | 8/22 = 36% [20%, 57%] | - | - | 2889.82 | 3.68 |

### Paired: gated vs ungated on the same unit and repeat (shipped and held-out correct)

| model | both correct | gated only | ungated only | neither |
|---|---|---|---|---|
| nemotron-3-ultra-550b-a55b (NVIDIA) | 17 | 1 | 0 | 4 |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | 12 | 2 | 2 | 6 |

### Breakdown by tier

| model | mode | tier | n | heldout_correct | shipped | wrong_shipped |
|---|---|---|---|---|---|---|
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | geometric | 18 | 16/18 = 89% [67%, 97%] | 16/18 = 89% [67%, 97%] | 0/16 = 0% [0%, 19%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | ids | 4 | 2/4 = 50% [15%, 85%] | 3/4 = 75% [30%, 95%] | 1/3 = 33% [6%, 79%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | geometric | 18 | 16/18 = 89% [67%, 97%] | 18/18 = 100% [82%, 100%] | 2/18 = 11% [3%, 33%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | ids | 4 | 1/4 = 25% [5%, 70%] | 4/4 = 100% [51%, 100%] | 3/4 = 75% [30%, 95%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | geometric | 18 | 12/18 = 67% [44%, 84%] | 12/18 = 67% [44%, 84%] | 0/12 = 0% [0%, 24%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | ids | 4 | 2/4 = 50% [15%, 85%] | 2/4 = 50% [15%, 85%] | 0/2 = 0% [0%, 66%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | geometric | 18 | 14/18 = 78% [55%, 91%] | 18/18 = 100% [82%, 100%] | 4/18 = 22% [9%, 45%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | ids | 4 | 0/4 = 0% [0%, 49%] | 4/4 = 100% [51%, 100%] | 4/4 = 100% [51%, 100%] |

### Breakdown by template

| model | mode | template | n | heldout_correct | shipped | wrong_shipped |
|---|---|---|---|---|---|---|
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | door_height_min | 1 | 0/1 = 0% [0%, 79%] | 0/1 = 0% [0%, 79%] | 0/0 (n/a) |
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | hand-written | 6 | 5/6 = 83% [44%, 97%] | 6/6 = 100% [61%, 100%] | 1/6 = 17% [3%, 56%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | space_area_min | 6 | 5/6 = 83% [44%, 97%] | 5/6 = 83% [44%, 97%] | 0/5 = 0% [0%, 43%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | space_height_min | 9 | 8/9 = 89% [57%, 98%] | 8/9 = 89% [57%, 98%] | 0/8 = 0% [0%, 32%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | door_height_min | 1 | 0/1 = 0% [0%, 79%] | 1/1 = 100% [21%, 100%] | 1/1 = 100% [21%, 100%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | hand-written | 6 | 4/6 = 67% [30%, 90%] | 6/6 = 100% [61%, 100%] | 2/6 = 33% [10%, 70%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | space_area_min | 6 | 5/6 = 83% [44%, 97%] | 6/6 = 100% [61%, 100%] | 1/6 = 17% [3%, 56%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | space_height_min | 9 | 8/9 = 89% [57%, 98%] | 9/9 = 100% [70%, 100%] | 1/9 = 11% [2%, 43%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | door_height_min | 1 | 1/1 = 100% [21%, 100%] | 1/1 = 100% [21%, 100%] | 0/1 = 0% [0%, 79%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | hand-written | 6 | 3/6 = 50% [19%, 81%] | 3/6 = 50% [19%, 81%] | 0/3 = 0% [0%, 56%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | space_area_min | 6 | 3/6 = 50% [19%, 81%] | 3/6 = 50% [19%, 81%] | 0/3 = 0% [0%, 56%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | space_height_min | 9 | 7/9 = 78% [45%, 94%] | 7/9 = 78% [45%, 94%] | 0/7 = 0% [0%, 35%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | door_height_min | 1 | 0/1 = 0% [0%, 79%] | 1/1 = 100% [21%, 100%] | 1/1 = 100% [21%, 100%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | hand-written | 6 | 3/6 = 50% [19%, 81%] | 6/6 = 100% [61%, 100%] | 3/6 = 50% [19%, 81%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | space_area_min | 6 | 4/6 = 67% [30%, 90%] | 6/6 = 100% [61%, 100%] | 2/6 = 33% [10%, 70%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | space_height_min | 9 | 7/9 = 78% [45%, 94%] | 9/9 = 100% [70%, 100%] | 2/9 = 22% [6%, 55%] |

## Human review

No reviewer decisions recorded yet (docs/review/review-sheet.csv).
