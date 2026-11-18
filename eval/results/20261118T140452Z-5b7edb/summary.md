# NIYAM evaluation 20261118T140452Z-5b7edb

Date 2026-11-18T14:04:52.332733+00:00 · commit `7713d77fdfa690dedbdb70a73bd558d11fdf2c29` · rulepack `ac3af42db49e` · temperature 0.0 · max repairs 3 · repeats 3 · providers {'nemotron-3-ultra-550b-a55b (NVIDIA)': 'OpenAICompatProvider', 'nemotron-3.5-lightning-30b-a3b (NVIDIA)': 'OpenAICompatProvider'} · dry_run=false

**Skipped model:** glm-4.7-flash (Z.ai): excluded by the operator: failed preflight with HTTP 429 (overloaded) on 2026-11-18; kept out of run 2

Rates are k/n = rate [Wilson 95% interval]. wrong_shipped is over shipped rules: how often a rule that is wrong on the held-out fixtures reaches the rulepack.

## All units

### Items, correlated across repeats

Each row of this table is one compilation; repeats of the same unit are correlated, so these intervals overstate precision when repeats > 1. The unit-level tables below count units.

| model | mode | n | valid | dev_correct | heldout_correct | shipped | wrong_shipped | needs_human | mean repairs | mean tokens | mean wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | 75 | 75/75 = 100% [95%, 100%] | 68/75 = 91% [82%, 95%] | 66/75 = 88% [79%, 94%] | 68/75 = 91% [82%, 95%] | 2/68 = 3% [1%, 10%] | 7/75 = 9% [5%, 18%] | 0.43 | 4915.59 | 10.86 |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | 75 | 66/75 = 88% [79%, 94%] | 55/75 = 73% [62%, 82%] | 55/75 = 73% [62%, 82%] | 75/75 = 100% [95%, 100%] | 20/75 = 27% [18%, 38%] | - | - | 2930.51 | 7.71 |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | 75 | 70/75 = 93% [85%, 97%] | 50/75 = 67% [55%, 76%] | 50/75 = 67% [55%, 76%] | 50/75 = 67% [55%, 76%] | 0/50 = 0% [0%, 7%] | 25/75 = 33% [24%, 45%] | 1.11 | 8177.07 | 9.09 |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | 75 | 60/75 = 80% [70%, 87%] | 44/75 = 59% [47%, 69%] | 44/75 = 59% [47%, 69%] | 75/75 = 100% [95%, 100%] | 31/75 = 41% [31%, 53%] | - | - | 2952.57 | 4.44 |

### Paired: gated vs ungated on the same unit and repeat (shipped and held-out correct)

| model | both correct | gated only | ungated only | neither |
|---|---|---|---|---|
| nemotron-3-ultra-550b-a55b (NVIDIA) | 53 | 13 | 2 | 7 |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | 41 | 9 | 3 | 22 |

### Breakdown by tier

| model | mode | tier | n | heldout_correct | shipped | wrong_shipped |
|---|---|---|---|---|---|---|
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | geometric | 54 | 50/54 = 93% [82%, 97%] | 50/54 = 93% [82%, 97%] | 0/50 = 0% [0%, 7%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | ids | 21 | 16/21 = 76% [55%, 89%] | 18/21 = 86% [65%, 95%] | 2/18 = 11% [3%, 33%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | geometric | 54 | 47/54 = 87% [76%, 94%] | 54/54 = 100% [93%, 100%] | 7/54 = 13% [6%, 24%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | ids | 21 | 8/21 = 38% [21%, 59%] | 21/21 = 100% [85%, 100%] | 13/21 = 62% [41%, 79%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | geometric | 54 | 41/54 = 76% [63%, 85%] | 41/54 = 76% [63%, 85%] | 0/41 = 0% [0%, 9%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | ids | 21 | 9/21 = 43% [24%, 63%] | 9/21 = 43% [24%, 63%] | 0/9 = 0% [0%, 30%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | geometric | 54 | 40/54 = 74% [61%, 84%] | 54/54 = 100% [93%, 100%] | 14/54 = 26% [16%, 39%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | ids | 21 | 4/21 = 19% [8%, 40%] | 21/21 = 100% [85%, 100%] | 17/21 = 81% [60%, 92%] |

### Breakdown by template

| model | mode | template | n | heldout_correct | shipped | wrong_shipped |
|---|---|---|---|---|---|---|
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | door_height_min | 3 | 0/3 = 0% [0%, 56%] | 0/3 = 0% [0%, 56%] | 0/0 (n/a) |
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | door_operation_forbidden | 6 | 6/6 = 100% [61%, 100%] | 6/6 = 100% [61%, 100%] | 0/6 = 0% [0%, 39%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | door_width_min | 3 | 3/3 = 100% [44%, 100%] | 3/3 = 100% [44%, 100%] | 0/3 = 0% [0%, 56%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | hand-written | 18 | 16/18 = 89% [67%, 97%] | 18/18 = 100% [82%, 100%] | 2/18 = 11% [3%, 33%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | space_area_min | 18 | 15/18 = 83% [61%, 94%] | 15/18 = 83% [61%, 94%] | 0/15 = 0% [0%, 20%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | space_height_min | 27 | 26/27 = 96% [82%, 99%] | 26/27 = 96% [82%, 99%] | 0/26 = 0% [0%, 13%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | door_height_min | 3 | 0/3 = 0% [0%, 56%] | 3/3 = 100% [44%, 100%] | 3/3 = 100% [44%, 100%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | door_operation_forbidden | 6 | 1/6 = 17% [3%, 56%] | 6/6 = 100% [61%, 100%] | 5/6 = 83% [44%, 97%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | door_width_min | 3 | 3/3 = 100% [44%, 100%] | 3/3 = 100% [44%, 100%] | 0/3 = 0% [0%, 56%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | hand-written | 18 | 13/18 = 72% [49%, 88%] | 18/18 = 100% [82%, 100%] | 5/18 = 28% [12%, 51%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | space_area_min | 18 | 15/18 = 83% [61%, 94%] | 18/18 = 100% [82%, 100%] | 3/18 = 17% [6%, 39%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | space_height_min | 27 | 23/27 = 85% [68%, 94%] | 27/27 = 100% [88%, 100%] | 4/27 = 15% [6%, 32%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | door_height_min | 3 | 3/3 = 100% [44%, 100%] | 3/3 = 100% [44%, 100%] | 0/3 = 0% [0%, 56%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | door_operation_forbidden | 6 | 0/6 = 0% [0%, 39%] | 0/6 = 0% [0%, 39%] | 0/0 (n/a) |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | door_width_min | 3 | 3/3 = 100% [44%, 100%] | 3/3 = 100% [44%, 100%] | 0/3 = 0% [0%, 56%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | hand-written | 18 | 12/18 = 67% [44%, 84%] | 12/18 = 67% [44%, 84%] | 0/12 = 0% [0%, 24%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | space_area_min | 18 | 11/18 = 61% [39%, 80%] | 11/18 = 61% [39%, 80%] | 0/11 = 0% [0%, 26%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | space_height_min | 27 | 21/27 = 78% [59%, 89%] | 21/27 = 78% [59%, 89%] | 0/21 = 0% [0%, 15%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | door_height_min | 3 | 1/3 = 33% [6%, 79%] | 3/3 = 100% [44%, 100%] | 2/3 = 67% [21%, 94%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | door_operation_forbidden | 6 | 1/6 = 17% [3%, 56%] | 6/6 = 100% [61%, 100%] | 5/6 = 83% [44%, 97%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | door_width_min | 3 | 2/3 = 67% [21%, 94%] | 3/3 = 100% [44%, 100%] | 1/3 = 33% [6%, 79%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | hand-written | 18 | 9/18 = 50% [29%, 71%] | 18/18 = 100% [82%, 100%] | 9/18 = 50% [29%, 71%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | space_area_min | 18 | 11/18 = 61% [39%, 80%] | 18/18 = 100% [82%, 100%] | 7/18 = 39% [20%, 61%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | space_height_min | 27 | 20/27 = 74% [55%, 87%] | 27/27 = 100% [88%, 100%] | 7/27 = 26% [13%, 45%] |

### Unit level: wrong_shipped per unit

A unit counts as wrong if any repeat shipped a rule that is wrong on the held-out fixtures; n = units that shipped in at least one repeat. k/n = rate [Wilson 95% interval].

| model | mode | units | wrong_shipped per unit |
|---|---|---|---|
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | 25 | 1/23 = 4% [1%, 21%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | 25 | 8/25 = 32% [17%, 52%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | 25 | 0/17 = 0% [0%, 18%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | 25 | 14/25 = 56% [37%, 73%] |

### Stability across repeats

Outcome = (shipped, held-out correct) of each repeat.

| model | mode | units | identical in every repeat | varied |
|---|---|---|---|---|
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | 25 | 23 | 2 |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | 25 | 21 | 4 |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | 25 | 24 | 1 |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | 25 | 18 | 7 |

### Unit level: held-out-correct share per unit

Repeats that shipped a held-out-correct rule / repeats.

| unit | nemotron-3-ultra-550b-a55b (NVIDIA) gated | nemotron-3-ultra-550b-a55b (NVIDIA) ungated | nemotron-3.5-lightning-30b-a3b (NVIDIA) gated | nemotron-3.5-lightning-30b-a3b (NVIDIA) ungated |
|---|---|---|---|---|
| MBBL2016-3.16.1#a | 3/3 | 3/3 | 3/3 | 3/3 |
| MBBL2016-4.10.4#a | 3/3 | 3/3 | 3/3 | 3/3 |
| MBBL2016-4.13#1 | 3/3 | 3/3 | 3/3 | 3/3 |
| MBBL2016-4.17.2#A | 3/3 | 3/3 | 3/3 | 3/3 |
| MBBL2016-4.22#1 | 3/3 | 3/3 | 2/3 | 3/3 |
| MBBL2016-4.24.7.2#b | 3/3 | 3/3 | 3/3 | 2/3 |
| MBBL2016-4.24.7.2#c | 3/3 | 0/3 | 0/3 | 0/3 |
| MBBL2016-4.24.7.2#f | 3/3 | 1/3 | 0/3 | 1/3 |
| MBBL2016-4.3.1.1#1 | 3/3 | 3/3 | 3/3 | 3/3 |
| MBBL2016-4.4.1#1 | 3/3 | 3/3 | 3/3 | 3/3 |
| MBBL2016-4.5.1#1 | 3/3 | 3/3 | 3/3 | 2/3 |
| MBBL2016-4.5.2#1 | 3/3 | 3/3 | 3/3 | 3/3 |
| MBBL2016-4.5.2#2 | 3/3 | 3/3 | 0/3 | 1/3 |
| MBBL2016-4.5.2#3 | 3/3 | 3/3 | 3/3 | 2/3 |
| MBBL2016-4.7.1#1 | 3/3 | 1/3 | 0/3 | 0/3 |
| MBBL2016-4.7.2#1 | 3/3 | 3/3 | 3/3 | 2/3 |
| MBBL2016-4.8.1#1 | 3/3 | 3/3 | 3/3 | 3/3 |
| MBBL2016-4.8.2#1 | 0/3 | 0/3 | 0/3 | 0/3 |
| MBBL2016-4.9.1#1 | 3/3 | 3/3 | 3/3 | 3/3 |
| MBBL2016-5.4.1#b | 3/3 | 3/3 | 3/3 | 0/3 |
| MBBL2016-5.4.1#b2 | 0/3 | 0/3 | 3/3 | 1/3 |
| MBBL2016-5.4.1#c | 3/3 | 0/3 | 0/3 | 0/3 |
| MBBL2016-5.4.2#1 | 1/3 | 1/3 | 0/3 | 0/3 |
| MBBL2016-7.1#1 | 3/3 | 3/3 | 0/3 | 0/3 |
| MBBL2016-7.2#1 | 2/3 | 1/3 | 3/3 | 3/3 |

## Distinct rules only

Excluded from the distinct view: MBBL2016-4.24.7.2#b (duplicate of MBBL2016-5.4.1#b), MBBL2016-4.24.7.2#c (duplicate of MBBL2016-5.4.1#c), MBBL2016-4.24.7.2#f (duplicate of MBBL2016-5.4.2#1). They encode the same requirement as another unit, so counting both would weight it twice.

### Items, correlated across repeats

Each row of this table is one compilation; repeats of the same unit are correlated, so these intervals overstate precision when repeats > 1. The unit-level tables below count units.

| model | mode | n | valid | dev_correct | heldout_correct | shipped | wrong_shipped | needs_human | mean repairs | mean tokens | mean wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | 66 | 66/66 = 100% [94%, 100%] | 59/66 = 89% [80%, 95%] | 57/66 = 86% [76%, 93%] | 59/66 = 89% [80%, 95%] | 2/59 = 3% [1%, 12%] | 7/66 = 11% [5%, 20%] | 0.39 | 4725.02 | 10.57 |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | 66 | 62/66 = 94% [85%, 98%] | 51/66 = 77% [66%, 86%] | 51/66 = 77% [66%, 86%] | 66/66 = 100% [94%, 100%] | 15/66 = 23% [14%, 34%] | - | - | 2871.61 | 7.65 |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | 66 | 62/66 = 94% [85%, 98%] | 47/66 = 71% [59%, 81%] | 47/66 = 71% [59%, 81%] | 47/66 = 71% [59%, 81%] | 0/47 = 0% [0%, 8%] | 19/66 = 29% [19%, 41%] | 0.97 | 7365.12 | 8.42 |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | 66 | 57/66 = 86% [76%, 93%] | 41/66 = 62% [50%, 73%] | 41/66 = 62% [50%, 73%] | 66/66 = 100% [94%, 100%] | 25/66 = 38% [27%, 50%] | - | - | 2896.27 | 4.69 |

### Paired: gated vs ungated on the same unit and repeat (shipped and held-out correct)

| model | both correct | gated only | ungated only | neither |
|---|---|---|---|---|
| nemotron-3-ultra-550b-a55b (NVIDIA) | 49 | 8 | 2 | 7 |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | 39 | 8 | 2 | 17 |

### Breakdown by tier

| model | mode | tier | n | heldout_correct | shipped | wrong_shipped |
|---|---|---|---|---|---|---|
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | geometric | 54 | 50/54 = 93% [82%, 97%] | 50/54 = 93% [82%, 97%] | 0/50 = 0% [0%, 7%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | ids | 12 | 7/12 = 58% [32%, 81%] | 9/12 = 75% [47%, 91%] | 2/9 = 22% [6%, 55%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | geometric | 54 | 47/54 = 87% [76%, 94%] | 54/54 = 100% [93%, 100%] | 7/54 = 13% [6%, 24%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | ids | 12 | 4/12 = 33% [14%, 61%] | 12/12 = 100% [76%, 100%] | 8/12 = 67% [39%, 86%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | geometric | 54 | 41/54 = 76% [63%, 85%] | 41/54 = 76% [63%, 85%] | 0/41 = 0% [0%, 9%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | ids | 12 | 6/12 = 50% [25%, 75%] | 6/12 = 50% [25%, 75%] | 0/6 = 0% [0%, 39%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | geometric | 54 | 40/54 = 74% [61%, 84%] | 54/54 = 100% [93%, 100%] | 14/54 = 26% [16%, 39%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | ids | 12 | 1/12 = 8% [1%, 35%] | 12/12 = 100% [76%, 100%] | 11/12 = 92% [65%, 99%] |

### Breakdown by template

| model | mode | template | n | heldout_correct | shipped | wrong_shipped |
|---|---|---|---|---|---|---|
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | door_height_min | 3 | 0/3 = 0% [0%, 56%] | 0/3 = 0% [0%, 56%] | 0/0 (n/a) |
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | hand-written | 18 | 16/18 = 89% [67%, 97%] | 18/18 = 100% [82%, 100%] | 2/18 = 11% [3%, 33%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | space_area_min | 18 | 15/18 = 83% [61%, 94%] | 15/18 = 83% [61%, 94%] | 0/15 = 0% [0%, 20%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | space_height_min | 27 | 26/27 = 96% [82%, 99%] | 26/27 = 96% [82%, 99%] | 0/26 = 0% [0%, 13%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | door_height_min | 3 | 0/3 = 0% [0%, 56%] | 3/3 = 100% [44%, 100%] | 3/3 = 100% [44%, 100%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | hand-written | 18 | 13/18 = 72% [49%, 88%] | 18/18 = 100% [82%, 100%] | 5/18 = 28% [12%, 51%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | space_area_min | 18 | 15/18 = 83% [61%, 94%] | 18/18 = 100% [82%, 100%] | 3/18 = 17% [6%, 39%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | space_height_min | 27 | 23/27 = 85% [68%, 94%] | 27/27 = 100% [88%, 100%] | 4/27 = 15% [6%, 32%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | door_height_min | 3 | 3/3 = 100% [44%, 100%] | 3/3 = 100% [44%, 100%] | 0/3 = 0% [0%, 56%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | hand-written | 18 | 12/18 = 67% [44%, 84%] | 12/18 = 67% [44%, 84%] | 0/12 = 0% [0%, 24%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | space_area_min | 18 | 11/18 = 61% [39%, 80%] | 11/18 = 61% [39%, 80%] | 0/11 = 0% [0%, 26%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | space_height_min | 27 | 21/27 = 78% [59%, 89%] | 21/27 = 78% [59%, 89%] | 0/21 = 0% [0%, 15%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | door_height_min | 3 | 1/3 = 33% [6%, 79%] | 3/3 = 100% [44%, 100%] | 2/3 = 67% [21%, 94%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | hand-written | 18 | 9/18 = 50% [29%, 71%] | 18/18 = 100% [82%, 100%] | 9/18 = 50% [29%, 71%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | space_area_min | 18 | 11/18 = 61% [39%, 80%] | 18/18 = 100% [82%, 100%] | 7/18 = 39% [20%, 61%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | space_height_min | 27 | 20/27 = 74% [55%, 87%] | 27/27 = 100% [88%, 100%] | 7/27 = 26% [13%, 45%] |

### Unit level: wrong_shipped per unit

A unit counts as wrong if any repeat shipped a rule that is wrong on the held-out fixtures; n = units that shipped in at least one repeat. k/n = rate [Wilson 95% interval].

| model | mode | units | wrong_shipped per unit |
|---|---|---|---|
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | 22 | 1/20 = 5% [1%, 24%] |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | 22 | 6/22 = 27% [13%, 48%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | 22 | 0/16 = 0% [0%, 19%] |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | 22 | 11/22 = 50% [31%, 69%] |

### Stability across repeats

Outcome = (shipped, held-out correct) of each repeat.

| model | mode | units | identical in every repeat | varied |
|---|---|---|---|---|
| nemotron-3-ultra-550b-a55b (NVIDIA) | gated | 22 | 20 | 2 |
| nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | 22 | 19 | 3 |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | 22 | 21 | 1 |
| nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | 22 | 17 | 5 |

### Unit level: held-out-correct share per unit

Repeats that shipped a held-out-correct rule / repeats.

| unit | nemotron-3-ultra-550b-a55b (NVIDIA) gated | nemotron-3-ultra-550b-a55b (NVIDIA) ungated | nemotron-3.5-lightning-30b-a3b (NVIDIA) gated | nemotron-3.5-lightning-30b-a3b (NVIDIA) ungated |
|---|---|---|---|---|
| MBBL2016-3.16.1#a | 3/3 | 3/3 | 3/3 | 3/3 |
| MBBL2016-4.10.4#a | 3/3 | 3/3 | 3/3 | 3/3 |
| MBBL2016-4.13#1 | 3/3 | 3/3 | 3/3 | 3/3 |
| MBBL2016-4.17.2#A | 3/3 | 3/3 | 3/3 | 3/3 |
| MBBL2016-4.22#1 | 3/3 | 3/3 | 2/3 | 3/3 |
| MBBL2016-4.3.1.1#1 | 3/3 | 3/3 | 3/3 | 3/3 |
| MBBL2016-4.4.1#1 | 3/3 | 3/3 | 3/3 | 3/3 |
| MBBL2016-4.5.1#1 | 3/3 | 3/3 | 3/3 | 2/3 |
| MBBL2016-4.5.2#1 | 3/3 | 3/3 | 3/3 | 3/3 |
| MBBL2016-4.5.2#2 | 3/3 | 3/3 | 0/3 | 1/3 |
| MBBL2016-4.5.2#3 | 3/3 | 3/3 | 3/3 | 2/3 |
| MBBL2016-4.7.1#1 | 3/3 | 1/3 | 0/3 | 0/3 |
| MBBL2016-4.7.2#1 | 3/3 | 3/3 | 3/3 | 2/3 |
| MBBL2016-4.8.1#1 | 3/3 | 3/3 | 3/3 | 3/3 |
| MBBL2016-4.8.2#1 | 0/3 | 0/3 | 0/3 | 0/3 |
| MBBL2016-4.9.1#1 | 3/3 | 3/3 | 3/3 | 3/3 |
| MBBL2016-5.4.1#b | 3/3 | 3/3 | 3/3 | 0/3 |
| MBBL2016-5.4.1#b2 | 0/3 | 0/3 | 3/3 | 1/3 |
| MBBL2016-5.4.1#c | 3/3 | 0/3 | 0/3 | 0/3 |
| MBBL2016-5.4.2#1 | 1/3 | 1/3 | 0/3 | 0/3 |
| MBBL2016-7.1#1 | 3/3 | 3/3 | 0/3 | 0/3 |
| MBBL2016-7.2#1 | 2/3 | 1/3 | 3/3 | 3/3 |

## Human review

No reviewer decisions recorded yet (docs/review/review-sheet.csv).
