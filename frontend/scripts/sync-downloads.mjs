// The documents themselves are PDFs built by build-pdfs.mjs (npm run docs:pdf, committed). This copies the data files.
// Copy the documents the footer links to into public/downloads/, so every link is a real, downloadable file
// served by the app itself (no external host). Source of truth stays in the repository's docs/.
import { copyFileSync, mkdirSync } from "node:fs";
import { basename } from "node:path";

const FILES = [
  "../LICENSE",
  "../docs/readiness/niyam-data-readiness.ids",
  "../docs/review/review-sheet.csv",
  "../docs/examples/gate-rejection.json",
];

mkdirSync("public/downloads", { recursive: true });
for (const f of FILES) copyFileSync(f, `public/downloads/${basename(f)}`);
console.log(`copied ${FILES.length} files to public/downloads/`);
