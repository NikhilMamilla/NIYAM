# Third-party notices

NIYAM's own source is MIT (`LICENSE`), including the landing page's button, section nav and card-stack
components: `frontend/src/SpecularButton.tsx`, `frontend/src/landing/GooeyNav.tsx` and
`frontend/src/landing/CardSwap.tsx` were originally adapted from the React Bits components of the same name
(MIT + Commons Clause, which is not compatible with redistributing NIYAM's own source as MIT); they were
rewritten from scratch as plain CSS/TypeScript, with no copied code, so the repository is fully MIT. The
packages, fonts and data below keep their own licences. Versions are the ones pinned in
`frontend/package-lock.json` (checked 25 November 2026 against each package's `package.json`; licence pages
accessed the same day).

## Packages in the built frontend (`npm ls --omit=dev --all`)

| Package | Version | Licence | Source | Where used |
|---|---|---|---|---|
| react, react-dom, scheduler | 19.3.1, 19.3.1, 0.28.0 | MIT | https://github.com/facebook/react | the whole web app |
| three | 0.187.0 | MIT | https://github.com/mrdoob/three.js | 3D view (`frontend/src/viewer.ts`) |
| @thatopen/components | 3.6.0 | MIT | https://github.com/ThatOpen/engine_components | 3D view: IFC loading, camera, selection |
| @thatopen/fragments | 3.6.0 | MIT | https://github.com/ThatOpen/engine_fragment | 3D view: IFC to fragments |
| web-ifc (and its `.wasm`, copied to `frontend/public/web-ifc/` at install) | 0.0.77 | MPL-2.0 | https://github.com/ThatOpen/engine_web-ifc | IFC parsing in the browser; unmodified |
| camera-controls | 3.1.2 | MIT | https://github.com/yomotsu/camera-controls | 3D view camera |
| three-mesh-bvh | 0.9.9 | MIT | https://github.com/gkjohnson/three-mesh-bvh | 3D picking (via @thatopen/components) |
| earcut | 3.2.4 | ISC | https://github.com/mapbox/earcut | via @thatopen/fragments |
| flatbuffers | 25.2.10 | Apache-2.0 | https://github.com/google/flatbuffers | via @thatopen/fragments |
| lru-cache | 11.1.0 | ISC | https://github.com/isaacs/node-lru-cache | via @thatopen/fragments |
| pako | 1.0.11, 2.1.0 | MIT AND Zlib | https://github.com/nodeca/pako | via @thatopen packages, jszip |
| jszip | 3.10.1 | MIT OR GPL-3.0-or-later (used under MIT) | https://github.com/Stuk/jszip | via @thatopen/components |
| fast-xml-parser, fast-xml-builder, strnum, anynum, path-expression-matcher, xml-naming | 5.7.2, 1.3.1, 2.5.1, 1.0.1, 1.6.2, 0.3.0 | MIT | https://github.com/NaturalIntelligence | via @thatopen/components |
| @nodable/entities | 2.2.0 | MIT | https://github.com/nodable/val-parsers | via fast-xml-parser |
| xxhash-wasm | 1.1.0 | MIT | https://github.com/jungomi/xxhash-wasm | via @thatopen packages |
| lie, immediate, readable-stream, string_decoder, safe-buffer, core-util-is, isarray, process-nextick-args, util-deprecate, inherits, setimmediate | 3.3.0, 3.0.6, 2.3.8, 1.1.1, 5.1.2, 1.0.3, 1.0.0, 2.0.1, 1.0.2, 2.0.4, 1.0.5 | MIT (inherits: ISC) | npm registry pages of each package | via jszip |

Build and test tools (Vite, TypeScript, Vitest, Playwright, marked) are development dependencies and do not ship.
Backend Python dependencies (FastAPI, ifcopenshell and ifctester (IfcOpenShell project, LGPL-3.0-or-later), and others in `backend/pyproject.toml`) run
on the server and are not part of the built frontend.

## Fonts (`frontend/public/fonts/`)

| Font | Licence | Copyright | Licence file |
|---|---|---|---|
| IBM Plex Sans, Serif, Mono | SIL Open Font License 1.1 | Copyright 2019 IBM Corp. | `frontend/public/fonts/OFL-IBM-Plex.txt` |
| Instrument Serif | SIL Open Font License 1.1 | Copyright 2022 The Instrument Serif Project Authors (https://github.com/Instrument/instrument-serif) | `frontend/public/fonts/OFL-Instrument-Serif.txt` |

## Data and images

| Item | Licence | Where |
|---|---|---|
| `fixtures/real/buildingsmart/Building-Architecture.ifc`, `Building-Structural.ifc` | CC BY 4.0, (C) buildingSMART International Ltd.; unmodified copies, redistributed with attribution | `fixtures/real/README.md`, `docs/real-models.md` |
| buildingSMART logo (`frontend/public/buildingsmart-logo.png`) | trademark of buildingSMART International, shown only to identify the organisation next to its IDS standard (sheet A-02); no endorsement is implied | landing sheet A-02 |
| Official buildingSMART IDS test cases (CC BY-ND 4.0) | **not redistributed**: downloaded outside the repository; only findings are committed | `docs/notes-ids-official-testcases.md` |
| MoHUA Model Building Bye-Laws 2016, Telangana Building Rules 2012 (G.O.Ms.No.168) | public government documents; the PDFs are **not redistributed** (`rules/source/` is ignored); clause sentences are quoted for research | `rules/`, `docs/review/` |
