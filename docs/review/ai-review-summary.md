# AI second-opinion review of the rule units

Reviewer: ChatGPT, an AI doing a preliminary text review, not a building-law domain expert. It read each rule
unit's clause text against the rule's machine reading (`docs/review/ai-review-chatgpt-2026-11-25.csv`, 27 rows,
one per unit in `docs/review/review-sheet.csv`). This does not change any rule spec, truth file, fixture or
committed result; it is a second pair of eyes, recorded for whoever reviews the rules next.

## Decisions

7 accept, 18 modify, 2 reject (of 27 units).

- **Accept (7):** MBBL2016-3.16.1#a, MBBL2016-4.13#1, MBBL2016-4.5.2#1, MBBL2016-4.5.2#3, MBBL2016-4.8.1#1,
  MBBL2016-4.9.1#1, MBBL2016-5.4.2#1.
- **Reject (2):** MBBL2016-4.24.7.2#c (duplicate of MBBL2016-5.4.1#c) and MBBL2016-4.24.7.2#f (duplicate of
  MBBL2016-5.4.2#1). Both duplicates were already flagged in our own machine_reading and in the `duplicate_of`
  column of `docs/review/review-sheet.csv`; the reviewer's reject confirms them and adds nothing new.
- **Modify (18):** every reading or omission the reviewer raised is listed below, split into what our own
  machine_reading already disclosed and what is new.

## Modify findings our machine_reading already disclosed as NOT encoded or ambiguous

For 15 of the 18 modify units, the reviewer's "modify" comment restates a limitation the unit's `machine_reading`
field already states in the committed review sheet:

| Unit | Already-disclosed limitation |
|---|---|
| MBBL2016-4.8.2#1 | "NOT encoded: the condition 'where provided in a residential building'" |
| MBBL2016-5.4.1#b2 | "AMBIGUITY: ... read as exit doorways" (reading-dependent unit, see below) |
| MBBL2016-4.10.4#a | "AMBIGUITY: 'in every part' asks for the minimum height everywhere, but the helper measures the vertical extent" |
| MBBL2016-4.17.2#A | "other building types (1.5 m, 2.0 m) and the row-housing note (0.75 m) are not encoded" |
| MBBL2016-4.22#1 | "NOT encoded: 'with a minimum width of 2.1 m' and the clause heading's condition 'Non-residential buildings'" |
| MBBL2016-4.3.1.1#1 | "the beam (2.4 m), pitched-roof (average height) and air-conditioned (2.4 m) provisions ... are not encoded" |
| MBBL2016-4.4.1#1 | "NOT encoded: the exception 'except for the portion to accommodate floor trap of the upper floor'" |
| MBBL2016-4.5.2#2 | "AMBIGUITY: ... read as a minimum ... NOT encoded: 'with a minimum width of 0.9 m'" |
| MBBL2016-4.7.1#1 | "AMBIGUITY: whether the height is clear height above the mezzanine or below it is not stated" |
| MBBL2016-4.7.2#1 | "the condition 'if it is to be used as a living room' is ignored ... the one-third-of-plinth-area limit ... is not encoded" |
| MBBL2016-5.4.1#b | "Ambiguity: clear vs leaf vs overall width not specified" |
| MBBL2016-5.4.1#c | "'overhead' mapped to ROLLINGUP only" |
| MBBL2016-7.2#1 | "NOT encoded: the 3.0 m clear height under balconies or girders and the 2.75 m head room under beams" |
| TGBR2012-5#c | NOT encoded (1)-(4): Rule 5's non-high-rise heading, the stilt floor's parking use, the 4.5 m mechanical/lift exception, measuring to a clear height under beams |
| TGBR2012-5#fxi | NOT encoded (1)-(5): side-width, open-to-sky, the lighting/ventilation condition, duct/interior-open-space scope, Rule 5's non-high-rise heading |

## New findings

Three units' modify comments raise something our machine_reading had not written down:

- **MBBL2016-7.1#1** (factory workroom height, 4.5 m). The clause excludes "room intended for storage, godowns and
  the like purposes" from the 4.5 m rule, and lets the Authority allow as low as 3.66 m for a qualifying small
  factory (under 50 workers, flatted-factory/service-industry class). Our machine_reading only disclosed that the
  building type (industrial) is not checked; it did not mention the storage/godown exclusion or the 3.66 m
  allowance.
- **MBBL2016-4.24.7.2#b**. Our review sheet lists this as a duplicate of MBBL2016-5.4.1#b (same 1 m exit-doorway
  width). The reviewer disagrees that it is a *pure* duplicate: clause 4.24.7.2#b carries a 2 m width exception for
  assembly and institutional buildings that clause 5.4.1#b's wording does not have. Decision recorded as modify,
  not reject, pending a person's call on whether to keep it as a separate unit with the exception encoded, or fold
  the exception into the existing duplicate.
- **MBBL2016-4.5.1#1** (bathroom/water-closet height, 2.1 m). The clause measures "from the surface of the floor
  to the lowest point in the ceiling (bottom of slab)"; the reviewer reads this as requiring the minimum clearance
  at the lowest point, not the space's overall vertical extent (which can overstate height where a ceiling is
  sloped or has a lower portion). Our machine_reading disclosed a different ambiguity for this unit (whether a
  combined bath/WC room counts) but not this measurement-point distinction.

None of these three units' specs, fixtures or truth files changed; they are future work (`docs/spec-backlog.md`).

## Reading-dependent units

On both of the pipeline's own flagged reading-dependent units, the reviewer agrees with the models' reading, not
our spec:

- **MBBL2016-4.8.2#1**: the reviewer's corrected reading keeps the clause's "where provided in a residential
  building" condition — the spec's reading (every store room, any building type) is what all 12 final run-2
  candidates departed from by applying the residential condition anyway.
- **MBBL2016-5.4.1#b2**: the reviewer's corrected reading applies the 2 m doorway height to every doorway, not
  only exit doors — the opposite of the spec's FireExit-only reading, which is also the reading some final
  candidates departed from.

This does not change the spec or the committed results. The existing post-hoc sensitivity table
(`eval/results/20261118T140452Z-5b7edb/summary.md`, `docs/spec-backlog.md` "Reading-dependent units") already
reports the headline numbers with and without these two units; this review is one more reason a person should
resolve the reading before any future run treats them as settled.
