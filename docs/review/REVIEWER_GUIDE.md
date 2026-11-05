# Reviewer guide

Thank you for reviewing. You do not need to run any software: you only read a spreadsheet and fill in a few columns.

## What NIYAM is

NIYAM is a research tool that reads Indian building bye-laws (here the MoHUA Model Building Bye-Laws 2016) and turns
single sentences into automatic checks that a computer can run on a digital building model, for example "is every
exit door at least 1 m wide?". A computer, sometimes with the help of an AI model, wrote each check as a **draft**.
It has been tested only on small artificial models. Your judgement decides whether a draft says what the bye-law
means.

## What a "rule unit" is

A **rule unit** is one sentence, or part of a sentence, copied word for word from a bye-law **clause** (a numbered
section such as 4.8.2). One clause often holds several requirements; each becomes its own unit, for example
MBBL2016-4.5.2#1 (bathroom area) and MBBL2016-4.5.2#2 (water-closet area).

## The review sheet, column by column

Open `review-sheet.csv` in Excel. `review-sheet.md` shows the same content as readable text.

| Column | What it means |
|---|---|
| unit_id | the rule unit's name: clause number plus a suffix |
| clause_id, page | the clause and its page in the PDF |
| tier | `ids` = checks data typed into the model (e.g. a door's width); `geometric` = measures the 3D shape (e.g. a room's floor area) |
| unit_text | the exact words being checked |
| clause_text | the whole clause, for context |
| machine_reading | in plain English, what the computer checks and which parts of the sentence it ignores |
| threshold | the number it compares against, e.g. "at least 2.2 m" |
| scope | which elements it applies to, e.g. "rooms marked Store" or "doors marked as fire exits" |
| duplicate_of | if filled, we believe another unit already checks the same thing |
| **decision** | **you fill:** `accept`, `modify` or `reject` |
| **corrected_reading, corrected_threshold** | **you fill** for `modify`: what it should check instead |
| **comments** | **you fill:** anything else, including whether you agree with duplicate_of |
| **reviewer_name, reviewed_on** | **you fill:** your name and the date as YYYY-MM-DD |

## What accept, modify and reject mean

- **accept**: the machine reading and threshold say what the bye-law requires, for the elements in scope.
- **modify**: the idea is right but something is missing or wrong; describe the correction. The rule is set aside
  until it is rewritten, and nothing changes automatically.
- **reject**: the unit should not be checked this way, for example because it is a duplicate, not a real
  requirement, or not checkable from a model.

**Example 1, accept.** MBBL2016-4.8.1#1, "The height of a store room shall be not less than 2.2 m." The reading is
"rooms marked Store must be at least 2.2 m high" and the threshold is "at least 2.2 m". If you agree, write `accept`.

**Example 2, modify.** MBBL2016-4.8.2#1, "The size of a store room, where provided in a residential building, shall
be not less than 3 m2." The machine checks every store room, but the clause applies only in **residential**
buildings. Write `modify` with the comment "only in residential buildings", or write `accept` if you think the
condition does not matter in practice.

**Example 3, reject or merge.** MBBL2016-4.24.7.2#f, "Revolving doors shall not to be provided as means of fire
exit.", is marked `duplicate_of: MBBL2016-5.4.2#1`, which says the same thing in chapter 5. If you agree, write
`reject` with the comment "duplicate of 5.4.2#1". If the two clauses differ in a way that matters, say so and keep it.

## Known concerns we would like you to look at

- **MBBL2016-4.24.7.2#b** (exit doors at least 1 m): the exception "assembly and institutional buildings where
  Doorway shall not be less than 2 m" is ignored, so a 1.5 m exit in a cinema would pass.
- **MBBL2016-4.8.2#1** (store room at least 3 m2): the "residential building" condition is ignored.
- **MBBL2016-4.10.4#a** (basement at least 2.4 m "in every part"): the machine measures the full height of the
  space from its lowest to its highest point, not the lowest height under a beam or a sloping ceiling.
- **MBBL2016-4.5.2#2** (water-closet "shall be 1.1 m2"): we read "shall be" as "at least 1.1 m2". Is it a minimum or
  an exact size?
- **Duplicates:** MBBL2016-4.24.7.2#b of 5.4.1#b, 4.24.7.2#c of 5.4.1#c, 4.24.7.2#f of 5.4.2#1.

## What the machine does not understand

- **Building-type conditions** ("in residential buildings", "except assembly buildings"): usually ignored.
- **Exceptions and provisos** ("except for the portion to accommodate floor trap"): ignored.
- **Several thresholds in one sentence** (an area *and* a minimum width): only one is checked; the other is listed
  in machine_reading as not encoded.
- **Room use** that the model does not record ("if it is to be used as a living room").
- **Relations** between elements, such as distances, ratios or which door belongs to which room.

## How to return the sheet

1. Fill in only the **decision**, **corrected_reading**, **corrected_threshold**, **comments**, **reviewer_name**
   and **reviewed_on** columns. Do not change other columns, column names or the order of rows.
2. Leave decision empty for any unit you did not review.
3. In Excel choose **File > Save As > CSV UTF-8 (Comma delimited) (*.csv)**, keep the file name, and send it back.

## Glossary

- **IFC**: the open file format for digital building models, exported by tools such as Revit and ArchiCAD.
- **IDS**: Information Delivery Specification, an open standard that states which information a model must contain
  and what values are allowed, for example "exit doors must be at least 1 m wide".
- **BCF**: BIM Collaboration Format, an open format for issues about specific elements, which design tools can open.
- **Rule unit**: one checkable sentence copied word for word from a bye-law clause.
- **Clause**: a numbered section of the bye-law, e.g. 4.8.2 "Size".
- **Threshold**: the number a value is compared with, e.g. 2.2 m.
- **Draft**: written by the computer or a developer and not yet confirmed by a domain expert.
