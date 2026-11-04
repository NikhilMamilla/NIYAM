# rules/source

Original regulation documents (PDFs) go here. Everything in this folder except this README is
gitignored: source documents are never committed.

Expected files:

- `mbbl-2016.pdf` — MoHUA / TCPO *Model Building Bye-Laws, 2016*, downloaded from
  https://www.mohua.gov.in/static/uploads/2026/07/0e33558a9326c8a89f945cae00cc3647.pdf
  (270 pages, `%PDF-1.6`).

Ingest with `python -m app.corpus.cli ingest` from `backend/`.
