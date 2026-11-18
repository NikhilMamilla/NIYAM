# NIYAM slide data: run 20261118T180916Z-4b9c93

- Date: 2026-11-18T18:09:16.867761+00:00
- Commit: `757877ec997d639178e3bca502dd98cc5642c60e`
- Rulepack hash: `ac3af42db49e15a0f5bc65773e6ab9d5a7af01d563439f05af2f8af98cb163d5`
- Models: nemotron-3-ultra-550b-a55b (NVIDIA) (open); nemotron-3.5-lightning-30b-a3b (NVIDIA) (open)
- Provider classes: {'nemotron-3-ultra-550b-a55b (NVIDIA)': 'OpenAICompatProvider', 'nemotron-3.5-lightning-30b-a3b (NVIDIA)': 'OpenAICompatProvider'}; request extras: {'nemotron-3-ultra-550b-a55b (NVIDIA)': {'reasoning_effort': 'none'}, 'nemotron-3.5-lightning-30b-a3b (NVIDIA)': {'reasoning_effort': 'none'}}
- Temperature 0.0, max repairs 3, repeats 3, dry_run=false
- Calls used: 31, tokens used: 196879
- Stopped early: no
- Skipped models: glm-4.7-flash (Z.ai) (excluded by the operator: failed preflight with HTTP 429 (overloaded) on 2026-11-18)
- Fallback items: 0 (only on_limit=wait is implemented; each item was answered by its model)

**Caution: n is small (25 draft units, 3 repeats per unit; repeats of a unit are correlated), so every interval is wide; no model difference may be claimed, and no mode difference beyond what the intervals show.**

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

Caution: n is small (25 draft units, 3 repeats per unit; repeats of a unit are correlated), so every interval is wide; no model difference may be claimed, and no mode difference beyond what the intervals show.
