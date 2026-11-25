"""Every image a reader can see is referenced, exists, and says one thing.

- every image path referenced by the landing page sources (frontend/src), the README, docs/ and submission/ exists;
- every image in the published folders (docs/screenshots, frontend/public/screens, frontend/public/journey,
  submission/screens) is referenced somewhere (submission/screens/README.md counts as a reference);
- no image is referenced with two different captions or alt texts.

Usage (repository root): python scripts/check_images.py. Exit 1 on any problem."""

import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = ["docs/screenshots", "frontend/public/screens", "frontend/public/journey", "submission/screens"]
IMG = r"[\w./-]+\.(?:png|svg|jpg|webp)"
MD_IMAGE = re.compile(rf"!\[([^\]]*)\]\(({IMG})\)")       # ![alt](path)
CODE_REF = re.compile(rf"`({IMG})`")                        # `path` in prose
SRC_REF = re.compile(rf"[\"'](/{IMG})[\"']")               # "/screens/x.png" in the web app's sources
ALT_AFTER = re.compile(r"alt:\s*\"([^\"]+)\"")


def main() -> int:
    refs: dict[Path, list[tuple[str, str]]] = defaultdict(list)  # file -> [(where, caption)]
    problems = []
    md_files = [ROOT / "README.md", *sorted((ROOT / "docs").rglob("*.md")), *sorted((ROOT / "submission").rglob("*.md"))]
    for md in md_files:
        text = md.read_text(encoding="utf-8")
        rel = md.relative_to(ROOT).as_posix()
        for alt, path in MD_IMAGE.findall(text):
            refs[(md.parent / path).resolve()].append((rel, alt.strip()))
        for path in CODE_REF.findall(text):
            target = (ROOT / path) if (ROOT / path).exists() else (md.parent / path)
            refs[target.resolve()].append((rel, ""))
    for src in sorted((ROOT / "frontend/src").rglob("*.ts*")):
        text = src.read_text(encoding="utf-8")
        rel = src.relative_to(ROOT).as_posix()
        for m in SRC_REF.finditer(text):
            alt = ALT_AFTER.search(text, m.end(), m.end() + 600)
            refs[(ROOT / "frontend/public" / m.group(1).lstrip("/")).resolve()].append((rel, alt.group(1) if alt else ""))

    for path, where in refs.items():
        if not path.exists():
            problems.append(f"missing: {path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path} (referenced in {where[0][0]})")
        captions = {c for _, c in where if c}
        if len(captions) > 1:
            problems.append(f"{path.relative_to(ROOT).as_posix()} has {len(captions)} different captions: {sorted(captions)}")
    published = [p for f in FOLDERS if (ROOT / f).exists() for p in (ROOT / f).rglob("*") if p.suffix in {".png", ".svg", ".jpg", ".webp"}]
    for p in published:
        if p.resolve() not in refs:
            problems.append(f"unreferenced: {p.relative_to(ROOT).as_posix()}")
    for p in problems:
        print("PROBLEM", p)
    print(f"check_images: {len(refs)} referenced images, {len(published)} published files, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
