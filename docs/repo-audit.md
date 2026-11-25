# Repository audit (repo-cleanup branch, 25 November 2026)

Inventory: `git ls-files` on `main` before this branch's changes gave **689 tracked files, 16,405,156 bytes
(~16.4 MB)** total. Only one tracked file exceeds 1 MB: `submission/video/niyam-demo-silent.webm` (3.79 MB); no
tracked file exceeds 5 MB. No caches (`__pycache__`, `.pytest_cache`, `node_modules`, `dist`, `build`,
`*.egg-info`, `test-results`, `playwright-report`, `.vite`), editor/OS junk (`.vscode`, `.idea`, `.DS_Store`,
`Thumbs.db`, `desktop.ini`), logs, scratch/backup files (`*.orig`, `*.bak`, `*~`), `eval/runs/`, `.env` (only
`.env.example`, which holds no values), or absolute local Windows user/desktop paths were found tracked.

This file records every decision that is not a plain "keep as committed source": the 9 exceptions below, and the
bulk categories everything else falls into. Writing one row per file for all 689 would not be more informative
than this grouping; every path not named below was checked against the KEEP rules and kept unchanged.

## Exceptions (every path whose status changes)

| Path | Decision | Reason |
|---|---|---|
| `submission/video/niyam-demo-silent.webm` | untrack (gitignore `submission/video/*.webm` and video extensions) | Per the task's explicit rule: the team records its own demo video; a 3.6 MB binary in git history for a file the team will re-record is not something a juror or contributor needs committed. Kept on disk; `frontend/e2e/demo-video.spec.ts` regenerates it. No reference breaks: `CHECKLIST.md`, `narration.md` and the spec file describe where the file lives on disk, not a git-tracked link. |
| `.impeccable/surfaces/frontend-src-app-tsx.md` | untrack (gitignore `.impeccable/`, alongside the already-ignored `.agents/`, `.claude/`, `.codex/`) | Agent-tooling scratch note from a design-review pass, not referenced by any source, test, script or doc (`grep -rl impeccable` outside the ignored tool directories finds nothing). Not needed by a juror or contributor. |
| `docs/.gitkeep` | delete | `docs/` holds 22 real files; the placeholder has had no purpose since the folder stopped being empty. Not referenced anywhere. |
| `eval/.gitkeep` | delete | `eval/` holds config files and `eval/results/`; same reasoning. |
| `fixtures/ids/.gitkeep` | delete | `fixtures/ids/` holds 7 `.ids` files; same reasoning. |
| `fixtures/ifc/.gitkeep` | delete | `fixtures/ifc/` holds 100+ dev fixtures; same reasoning. |
| `rules/.gitkeep` | delete | `rules/` holds `corpus/`, `specs/`, `rulepack/`, `source/`; same reasoning. |
| `PRODUCT.md` | move to `docs/product-brief.md` | Root is reserved for `README.md`, `LICENSE`, `THIRD_PARTY_NOTICES.md`, `CITATION.cff`, `STATUS.md`, `.gitignore` and the folders. This is a design-brief document (brand commitments, product principles) with no incoming references to its old path, so moving it is zero-risk. |

No secret, key or personal path was found, so no history rewrite is needed or attempted.

## Duplicate content (same sha256 at two tracked paths) — all intentional, kept as is

A full-repository hash pass (689 files) found 47 sha256 values shared by more than one tracked path. Every group
is one of these four intentional patterns, not an accident to clean up:

| Pattern | Example | Why both copies are kept |
|---|---|---|
| Dry-run provider's canonical answer vs. the fixture it was copied from | `backend/app/eval/dryrun/MBBL2016-4_9_1_1/correct.py` and `fixtures/checks/MBBL2016-4_9_1_1.py` | The dry-run harness needs its own copy under `backend/app/`; the fixture is the source of truth used by other tests. Both are source, not generated cache. |
| Rulepack build output vs. the fixture it was built from | `fixtures/ids/MBBL2016-5_4_1_b.ids` and `rules/rulepack/v0/ids/MBBL2016-5_4_1_b.ids` | `rules/rulepack/v0/` is the shipped rulepack the backend loads at runtime; it is committed deliberately (not regenerated on every run), per the existing KEEP rule for `rules/`. |
| Packaged submission copy vs. the backend fixture it mirrors | `fixtures/samples/sample_a_mm.ifc` and `submission/samples/sample_a_mm/sample_a_mm.ifc` | `submission/samples/` must be self-contained for a juror who never clones `fixtures/`; `fixtures/samples/` is what the backend and tests read. Both are explicitly in the KEEP list. |
| Landing page asset vs. the submission deck's matching screen | `frontend/public/screens/demo-2-verdict.png` and `submission/screens/1440x900/03-verdict-sample-a.png` | Same screenshot, two consumers: the live site serves one, the submission package (for a juror with no running app) ships the other. Different lifecycles, so duplication here is intentional, not waste. |
| `frontend/public/downloads/*` vs. its `docs/` source | `docs/review/review-sheet.csv` and `frontend/public/downloads/review-sheet.csv`; also `LICENSE`, `docs/examples/gate-rejection.json`, `docs/readiness/niyam-data-readiness.ids` | `scripts/sync-downloads.mjs` copies these into `public/downloads/` so the landing page's download links (`Landing.tsx`) serve a real file; its own comment says the copies are committed on purpose, and `predev`/`prebuild` keep them in sync. |
| Empty `__init__.py` files | 17 files, all hashing to the empty-file hash | Ordinary empty Python package markers, not a duplication issue. |

The PDFs in `frontend/public/downloads/` (`README.pdf`, `STATUS.pdf`, etc.) are also generated, by
`scripts/build-pdfs.mjs` from the matching `docs/*.md` — not byte-identical to their source, so they did not show
up as hash duplicates, but the same reasoning applies: committed on purpose so the landing page's download links
work without a build step.

## Bulk categories kept unchanged

| Folder / pattern | Files | Why kept |
|---|---|---|
| `backend/app/**`, `backend/tests/**`, `backend/pyproject.toml` etc. | 235 | Backend source and its test suite (pytest). |
| `fixtures/ifc/`, `fixtures/heldout/`, `fixtures/samples/`, `fixtures/checks/`, `fixtures/ids/`, `fixtures/invalid/`, `fixtures/real/` | 186 (184 after the two `.gitkeep` deletions) | Read by pytest and the geometric/IDS gate; `fixtures/invalid/` and `fixtures/real/` carry their own licence notes and are explicitly in the KEEP list. |
| `frontend/src/**`, `frontend/e2e/**`, `frontend/public/**`, `frontend/*.json`/`*.ts` config | 107 | Frontend source, Playwright/vitest tests, and the landing page's served assets (screenshots, downloads, fonts, web-ifc wasm copy point). |
| `submission/**` (deck PDF+PPTX, screens, samples, `deck-facts.md`, `demo-script.md`, `narration.md`, `email.md`, `how-to-run.md`, `CHECKLIST.md`) | 56 (57 minus the untracked video) | Explicitly in the KEEP list; this is the reviewer-facing package. |
| `rules/**` | 33 (32 after the `.gitkeep` deletion) | The corpus, rule specs and the shipped `rulepack/v0/`. |
| `docs/**` (including `docs/review/` both review sheets, the AI review CSV and summary, and `docs/product-brief.md` moved in from root) | 24 (23 after the `.gitkeep` deletion, 24 again once `product-brief.md` moves in) | Explicitly in the KEEP list; linked from README and the landing page's documentation sheet. |
| `eval/**` (`eval/results/`, `rescore-after-mm-fix/`, example configs) | 22 (21 after the `.gitkeep` deletion) | Explicitly in the KEEP list; every number in `deck-facts.md` traces to one of these files via `check_numbers.py`. |
| `scripts/**` | 16 | `check_numbers.py`, `check_images.py`, `check_public_ready.py`, the fixture/sample/figure builders, `demo.ps1`/`demo.sh`, the dev-server scripts, the re-score and BCF-validation scripts: all are run by tests, CI-equivalent checks, or `how-to-run.md`. |
| Root: `README.md`, `LICENSE`, `THIRD_PARTY_NOTICES.md`, `CITATION.cff`, `STATUS.md`, `.gitignore`, `.env.example` | 7 | The allowed root set, plus `.env.example` (no values, referenced by `backend/app/eval/preflight.py`, `backend/tests/test_public_ready.py` and `docs/evaluation.md`). |

## Summary

- Untrack (kept on disk, gitignored): **2** paths (one video, one agent-tool note).
- Delete (no purpose, nothing lost): **5** `.gitkeep` placeholders.
- Move: **1** path (`PRODUCT.md` → `docs/product-brief.md`).
- Keep unchanged: **681** paths (689 total minus the 7 untracked/deleted minus the 1 moved).
- No secret, key or personal path found; no history rewrite needed.
