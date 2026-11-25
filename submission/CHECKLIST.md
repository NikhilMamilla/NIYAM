# Final submission checklist (DBI 2026 Stage 2, send by 29 Nov 2026)

| Item | Path | Status |
|---|---|---|
| Slide deck (PDF, 10 pages) | `submission/deck/NIYAM_TeamAbhyudaya_DBI2026_Stage2.pdf` | done |
| Slide deck (source, PPTX) | `submission/deck/NIYAM_DBI2026_Stage2.pptx` | done |
| Demo video (silent) | `submission/video/niyam-demo-silent.webm` | done |
| Demo video (MP4/H.264) | `submission/video/niyam-demo-silent.mp4` | needs the team: no `ffmpeg` on this machine; re-run `frontend/e2e/demo-video.spec.ts` on a machine with `ffmpeg` on PATH, or convert the `.webm` by hand |
| Narration script | `submission/video/narration.md` | done |
| Submission email | `submission/email.md` | needs the team: fill in `[REPO LINK]` and `[DEMO VIDEO LINK]`, confirm the samples zip should be attached (130 KB), then send to dbi@cdcpindia.org |
| Sample audits zip | `submission/NIYAM_samples.zip` | done (not committed, gitignored; regenerate with `python -c "import shutil; shutil.make_archive('submission/NIYAM_samples','zip','submission','samples')"`) |
| Repository push | `origin/main`, `origin/submission-v2` | needs the team: `gh repo view` reports the repo is PUBLIC, so this run did not push (see report below); push yourself when ready, or ask to make the repo private first if that was unintended |
| Deck facts (sources for every number) | `submission/deck-facts.md` | done, pre-existing |
| Demo script (shot list) | `submission/demo-script.md` | done, pre-existing |
| Run guide | `submission/how-to-run.md` | done, pre-existing |
| Sample outputs (IFC, BCF, HTML/JSON, truth) | `submission/samples/` | done, pre-existing |
| Slide screens | `submission/screens/` | done, pre-existing |
| This checklist | `submission/CHECKLIST.md` | done |

## Open items for the team

1. Fill `[REPO LINK]` and `[DEMO VIDEO LINK]` in `submission/email.md` once you decide how the video and repo are
   shared (the video is not pushed anywhere by this run; host it or attach it directly).
2. Decide whether to push `main` and the `submission-v2` tag: the GitHub repository is public, so this run left
   it unpushed per instruction. If the organisers need the repo link, push it yourself (`git push origin main
   --tags`) or make the repository private first if that was not intended.
3. Optional: produce the MP4 if a reviewer's system cannot play WebM.
