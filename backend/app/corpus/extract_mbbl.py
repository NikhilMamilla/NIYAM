import re
from pathlib import Path

import pdfplumber

from app.corpus.models import Clause

SOURCE_DOC = "MBBL-2016"
ID_PREFIX = "MBBL2016"

# Running headers alternate between "Development Codes 3" and "3 Development Codes".
HEADER_TITLE_FIRST = re.compile(r"^([A-Z][A-Za-z ,/&()\-]+?)\s+(\d{1,2})$")
HEADER_NUMBER_FIRST = re.compile(r"^(\d{1,2})\s+([A-Z][A-Za-z ,/&()\-]+)$")
# Odd pages: "Model Building Bye-Law, 2016, TCPO Page 43"; even pages: "Page 56 Model Building Bye-Law, ..."
FOOTER = re.compile(r"^(?:Page\s+\d+\s+)?Model Building Bye-?Law", re.IGNORECASE)
TOC_LEADER = re.compile(r"\.{5,}")
# "4.25.1 Text", "4.25. Text", "2.14.1 a) Text"; the text must start with a capital, which
# rejects wrapped references such as "2.14 (b) of the property" and table values like "0.75m wide".
# The space after the number is optional: the source has "11.10.1Requirements".
HEADING = re.compile(r"^(\d{1,2}(?:\.\d{1,3}){1,3})\.?\s*((?:\(?[a-z]\)\s+)?[A-Z\"'][^\n]*)$")
UNIT_START = re.compile(r"^(m|mm|cm|sq|sqm|km|ha|x|%)\b", re.IGNORECASE)


def extract_pages(pdf_path: Path) -> list[str]:
    with pdfplumber.open(pdf_path) as pdf:
        return [page.extract_text() or "" for page in pdf.pages]


def _title(rest: str) -> str | None:
    # shortcut: a heading line is a title only if short and not a sentence, refine per source if needed
    return rest.strip() if len(rest) <= 100 and " shall " not in f" {rest.lower()} " else None


def _parse_header(line: str) -> tuple[int, str] | None:
    if m := HEADER_TITLE_FIRST.match(line):
        return int(m.group(2)), m.group(1).strip()
    if m := HEADER_NUMBER_FIRST.match(line):
        return int(m.group(1)), m.group(2).strip()
    return None


def _first_line(page_text: str) -> str:
    return next((ln.strip() for ln in page_text.splitlines() if ln.strip()), "")


def _number_key(number: str) -> tuple[int, ...]:
    return tuple(int(p) for p in number.split("."))


def segment(pages: list[str]) -> list[Clause]:
    """Split page texts into clauses at numbered headings. Pages are 1-based PDF page numbers."""
    # A running header recurs on many pages; a table row that merely looks like one does not.
    header_counts: dict[tuple[int, str], int] = {}
    for text in pages:
        if parsed := _parse_header(_first_line(text)):
            header_counts[parsed] = header_counts.get(parsed, 0) + 1
    headers = {h for h, n in header_counts.items() if n >= 2}

    clauses: list[Clause] = []
    seen: set[str] = set()
    last_key: tuple[int, ...] = ()
    chapter: tuple[int, str] | None = None
    current: dict | None = None

    def flush():
        if current:
            clauses.append(
                Clause(
                    id=f"{ID_PREFIX}-{current['number']}",
                    source_doc=SOURCE_DOC,
                    clause_number=current["number"],
                    title=current["title"],
                    text="\n".join(current["lines"]).strip(),
                    page=current["page"],
                    section_path=current["section_path"],
                )
            )

    for page_no, page_text in enumerate(pages, start=1):
        lines = [ln.rstrip() for ln in page_text.splitlines() if ln.strip()]
        if lines and (parsed := _parse_header(lines[0].strip())) in headers:
            chapter = parsed
            lines = lines[1:]
        elif lines and lines[0].strip().startswith("Annexure and Appendices"):
            chapter = None
            lines = lines[1:]
        if any(TOC_LEADER.search(ln) for ln in lines):
            continue  # Contents pages

        for line in lines:
            if FOOTER.match(line.strip()):
                continue
            m = HEADING.match(line.strip())
            if m and chapter and not UNIT_START.match(m.group(2)):
                number = m.group(1)
                key = _number_key(number)
                # Out-of-order numbers are wrapped cross-references ("...vide section 5.2 shall").
                if key[0] == chapter[0] and number not in seen and key > last_key:
                    flush()
                    seen.add(number)
                    last_key = key
                    current = {
                        "number": number,
                        "title": _title(m.group(2)),
                        "lines": [line.strip()],
                        "page": page_no,
                        "section_path": [f"Chapter {chapter[0]}", chapter[1]],
                    }
                    continue
            if current:
                current["lines"].append(line.strip())
        if chapter is None:
            flush()
            current = None
    flush()
    return clauses
