# frontend

The React + TypeScript app: the landing page (`src/landing/`) and the audit app with its Three.js 3D view
(`src/`), served by Vite. `public/` holds the images, downloadable PDFs and the web-ifc wasm copy it serves.

Produced by `npm run dev`/`npm run build`; `npm run site-data` regenerates `src/data/site-data.json` from the
root README and `docs/sources.md` so the landing page's text stays in sync with the documents.

Used by: a person opening the app, and by `e2e/` (Playwright) and `src/**/*.test.tsx` (vitest).
