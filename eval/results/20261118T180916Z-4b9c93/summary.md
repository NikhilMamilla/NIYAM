# NIYAM evaluation 20261118T180916Z-4b9c93

Date 2026-11-18T18:09:16.867761+00:00 · commit `757877ec997d639178e3bca502dd98cc5642c60e` · rulepack `ac3af42db49e` · temperature 0.0 · max repairs 3 · repeats 3 · providers {'nemotron-3-ultra-550b-a55b (NVIDIA)': 'OpenAICompatProvider', 'nemotron-3.5-lightning-30b-a3b (NVIDIA)': 'OpenAICompatProvider'} · dry_run=false

**Skipped model:** glm-4.7-flash (Z.ai): excluded by the operator: failed preflight with HTTP 429 (overloaded) on 2026-11-18

Each cell has n ≤ 6 (n < 30): the 95% intervals are wide; differences between rows are not evidence of a real difference.

Rates are k/n = rate [Wilson 95% interval]. wrong_shipped is over shipped rules: how often a rule that is wrong on the held-out fixtures reaches the rulepack.

# Source: TGBR2012 (Telangana Building Rules 2012 (G.O.Ms.No.168, original text, amendments not applied))

**case study, n too small for rates** (2 unit(s); rates need at least 5). Counts per unit, model and mode:

| unit | model | mode | repeats | shipped | shipped and held-out correct | outcomes |
|---|---|---|---|---|---|---|
| TGBR2012-5#c | nemotron-3-ultra-550b-a55b (NVIDIA) | gated | 3 | 3 | 3 | accepted x3 |
| TGBR2012-5#c | nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | 3 | 3 | 3 | baseline_scored x3 |
| TGBR2012-5#c | nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | 3 | 2 | 2 | accepted x2, needs_human x1 |
| TGBR2012-5#c | nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | 3 | 3 | 2 | baseline_scored x3 |
| TGBR2012-5#fxi | nemotron-3-ultra-550b-a55b (NVIDIA) | gated | 3 | 3 | 3 | accepted x3 |
| TGBR2012-5#fxi | nemotron-3-ultra-550b-a55b (NVIDIA) | ungated | 3 | 3 | 1 | baseline_scored x3 |
| TGBR2012-5#fxi | nemotron-3.5-lightning-30b-a3b (NVIDIA) | gated | 3 | 2 | 2 | accepted x2, needs_human x1 |
| TGBR2012-5#fxi | nemotron-3.5-lightning-30b-a3b (NVIDIA) | ungated | 3 | 3 | 0 | baseline_scored x3 |

## Human review

No reviewer decisions recorded yet (docs/review/review-sheet.csv).
