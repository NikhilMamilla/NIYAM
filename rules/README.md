# rules

`corpus/` is the ingested clause corpus (MBBL 2016, Telangana 2012). `specs/` are the hand-written rule specs
the compiler and generator read. `rulepack/v0/` is the shipped rulepack (6 rules) the backend loads at runtime;
it is committed, not regenerated on every run. `source/` is gitignored on purpose: the bye-law PDFs are never
committed (see `source/README.md`).

Used by: `backend/app/corpus`, `backend/app/specgen`, `backend/app/rulepack`, and `scripts/check_numbers.py`
(every "N rules"/"N units" claim in the docs is checked against these files).
