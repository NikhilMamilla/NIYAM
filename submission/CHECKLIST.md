# Final submission checklist (DBI 2026 Stage 2, send by 29 Nov 2026)

| Item | Path | Status |
|---|---|---|
| Slide deck (PDF, 10 pages) | `submission/deck/NIYAM_TeamAbhyudaya_DBI2026_Stage2.pdf` | done |
| Slide deck (source, PPTX) | `submission/deck/NIYAM_DBI2026_Stage2.pptx` | done |
| Demo video (silent) | `submission/video/niyam-demo-silent.webm` | done locally, not committed (gitignored per the repo cleanup; regenerate with `npx playwright test demo-video`, see `frontend/e2e/demo-video.spec.ts`) |
| Demo video (MP4/H.264) | `submission/video/niyam-demo-silent.mp4` | needs the team: no `ffmpeg` on this machine; re-run `frontend/e2e/demo-video.spec.ts` on a machine with `ffmpeg` on PATH, or convert the `.webm` by hand |
| Narration script | `submission/video/narration.md` | done |
| Submission email | `submission/email.md` | needs the team: fill in `[DEMO VIDEO LINK]`, confirm the samples zip should be attached (130 KB), then send to dbi@cdcpindia.org |
| Sample audits zip | `submission/NIYAM_samples.zip` | done (not committed, gitignored; regenerate with `python -c "import shutil; shutil.make_archive('submission/NIYAM_samples','zip','submission','samples')"`) |
| Repository push | `origin/main` and tags | done |
| Live demo (GitHub Pages) | https://nikhilmamilla.github.io/NIYAM/, built by `.github/workflows/deploy-pages.yml` | done: live, checked by `e2e-static` against the live URL (8 passed) |
| Upload API (Render) | `render.yaml`, `docs/deploy.md` | optional, prepared: five clicks in `docs/deploy.md` |
| Deck facts (sources for every number) | `submission/deck-facts.md` | done, pre-existing |
| Demo script (shot list) | `submission/demo-script.md` | done, pre-existing |
| Run guide | `submission/how-to-run.md` | done, pre-existing |
| Sample outputs (IFC, BCF, HTML/JSON, truth) | `submission/samples/` | done, pre-existing |
| Slide screens | `submission/screens/` | done, pre-existing |
| This checklist | `submission/CHECKLIST.md` | done |

## Open items for the team

1. Fill `[DEMO VIDEO LINK]` in `submission/email.md` once you record and host your own demo video: the repo
   cleanup removed the recorded `.webm` from git (it stays on this machine and is gitignored; the team records
   its own, per the cleanup task's instruction). Re-run `npx playwright test demo-video` to produce a fresh one,
   or record manually following `submission/demo-script.md`.
2. Live demo address: fixed on 26 November 2026 by removing the custom domain `nikhilmamilla.me` from the
   `NikhilMamilla.github.io` repository (it forwarded every github.io address to Vercel, where `/NIYAM/` is a
   404). `nikhilmamilla.me` itself is unaffected; plain `nikhilmamilla.github.io` no longer forwards to it.
3. Optional: produce the MP4 if a reviewer's system cannot play WebM.
