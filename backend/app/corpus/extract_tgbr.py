"""Segmenter for the Telangana Building Rules 2012 (G.O.Ms.No.168, original text, amendments not applied).

Clauses are the 29 numbered rules (TGBR2012-<n>) and the annexures and appendices (TGBR2012-AnnexureV, ...).
Sub-rules ((a), (i), ...) stay inside their rule's text. Pages come from app.corpus.extract_mbbl.extract_pages."""

import re

from app.corpus.models import Clause

SOURCE_DOC = "TGBR-2012"
ID_PREFIX = "TGBR2012"

# "5. PERMISSIBLE SETBACKS & HEIGHT ..." / "2. DEFINITIONS: In these rules,": an upper-case title after the number.
RULE = re.compile(r"^(\d{1,2})\.\s+([A-Z][A-Z0-9 ,&/()'\-]{3,}.*)$")
# "ANNEXURE-I", "ANNEXURE � V" (the dash is lost in extraction), "APPENDIX - IV", alone on a line.
PART = re.compile(r"^(ANNEXURE|APPENDIX)\s*[-–—�]?\s*([IVXL]+)$")


def _strip_page_number(lines: list[str], page_no: int) -> list[str]:
    """Every page starts with its printed number, alone ("31") or glued to the first line ("10 (c) Stilt ...")."""
    if lines and lines[0] == str(page_no):
        return lines[1:]
    if lines and lines[0].startswith(f"{page_no} "):
        return [lines[0][len(str(page_no)) + 1:].strip(), *lines[1:]]
    return lines


def segment(pages: list[str]) -> list[Clause]:
    """Split page texts into rule, annexure and appendix clauses. Pages are 1-based PDF page numbers."""
    clauses: dict[str, dict] = {}  # insertion-ordered; a repeated annexure heading continues the same clause
    current: dict | None = None
    last_rule, in_parts = 0, False

    for page_no, page_text in enumerate(pages, start=1):
        lines = _strip_page_number([ln.strip() for ln in page_text.splitlines() if ln.strip()], page_no)
        first_part = next((i for i, ln in enumerate(lines) if PART.match(ln)), None)
        above = lines[:first_part] if first_part is not None else []  # e.g. the town name above "ANNEXURE-I"
        for line in lines[len(above):]:
            if m := PART.match(line):
                in_parts = True
                kind, numeral = m.group(1).capitalize(), m.group(2)
                path = ["Appendices"] if kind == "Appendix" else ["Annexures"]
                current = clauses.setdefault(f"{ID_PREFIX}-{kind}{numeral}", {
                    "number": f"{kind} {numeral}", "title": None, "lines": [], "page": page_no, "path": path})
                current["lines"] += [*above, line]
                above = []
                continue
            m = RULE.match(line)
            if m and not in_parts and int(m.group(1)) == last_rule + 1:  # rules run 1..29 in order
                last_rule = int(m.group(1))
                current = clauses.setdefault(f"{ID_PREFIX}-{last_rule}", {
                    "number": str(last_rule), "title": m.group(2).split(":")[0].strip(), "lines": [],
                    "page": page_no, "path": ["Rules"]})
            if current is not None:  # None only for the G.O. text before rule 1
                current["lines"].append(line)

    return [Clause(id=cid, source_doc=SOURCE_DOC, clause_number=c["number"], title=c["title"],
                   text="\n".join(c["lines"]).strip(), page=c["page"], section_path=c["path"])
            for cid, c in clauses.items()]
