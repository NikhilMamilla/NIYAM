"""Validate .bcf files as BCF 2.1 zips: structure (bcf.version at the root, one folder per topic GUID holding
markup.bcf and the viewpoint files it names) and, when the official schemas are given, every XML file against them.

Usage: python scripts/validate_bcf.py <file.bcf>... [--xsd <dir with markup.xsd, visinfo.xsd, version.xsd>]
The schemas are buildingSMART's (https://github.com/buildingSMART/BCF-XML/tree/release_2_1/Schemas); they are not
committed. Exit 1 if any file has a problem."""

import re
import sys
import zipfile
from pathlib import Path

GUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def validate(path: Path, schemas: dict | None) -> tuple[list[str], dict]:
    from lxml import etree
    problems, stats = [], {"topics": 0, "viewpoints": 0}
    try:
        z = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        return [f"{path.name}: not a zip"], stats
    names = set(z.namelist())
    if "bcf.version" not in names:
        problems.append("no bcf.version at the root")
    else:
        root = etree.fromstring(z.read("bcf.version"))
        if root.get("VersionId") != "2.1":
            problems.append(f"bcf.version VersionId is {root.get('VersionId')!r}, not '2.1'")
        if schemas and not schemas["version"].validate(root):
            problems.append(f"bcf.version: {schemas['version'].error_log.last_error}")
    topics = sorted({n.split("/")[0] for n in names if "/" in n})
    for t in topics:
        if not GUID.match(t):
            problems.append(f"folder {t!r} is not a GUID")
            continue
        if f"{t}/markup.bcf" not in names:
            problems.append(f"{t}: no markup.bcf")
            continue
        stats["topics"] += 1
        markup = etree.fromstring(z.read(f"{t}/markup.bcf"))
        if schemas and not schemas["markup"].validate(markup):
            problems.append(f"{t}/markup.bcf: {schemas['markup'].error_log.last_error}")
        if markup.find("Topic") is None or markup.find("Topic").get("Guid") != t:
            problems.append(f"{t}/markup.bcf: Topic Guid does not match its folder")
        for vp in markup.iter("Viewpoints"):
            file = vp.findtext("Viewpoint")
            if not file or f"{t}/{file}" not in names:
                problems.append(f"{t}: viewpoint file {file!r} named in markup.bcf is missing")
                continue
            stats["viewpoints"] += 1
            visinfo = etree.fromstring(z.read(f"{t}/{file}"))
            if schemas and not schemas["visinfo"].validate(visinfo):
                problems.append(f"{t}/{file}: {schemas['visinfo'].error_log.last_error}")
            snap = vp.findtext("Snapshot")
            if snap and f"{t}/{snap}" not in names:
                problems.append(f"{t}: snapshot {snap!r} is missing")
    return problems, stats


def main(argv: list[str]) -> int:
    from lxml import etree
    schemas = None
    if "--xsd" in argv:
        d = Path(argv[argv.index("--xsd") + 1])
        argv = argv[: argv.index("--xsd")] + argv[argv.index("--xsd") + 2:]
        schemas = {k: etree.XMLSchema(etree.parse(str(d / f"{k}.xsd"))) for k in ("markup", "visinfo", "version")}
    bad = 0
    for f in map(Path, argv):
        problems, stats = validate(f, schemas)
        bad += bool(problems)
        what = "structure and XSD" if schemas else "structure only"
        print(f"{'OK  ' if not problems else 'FAIL'} {f}: {stats['topics']} topics, {stats['viewpoints']} viewpoints ({what})")
        for p in problems[:10]:
            print("     ", p)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
