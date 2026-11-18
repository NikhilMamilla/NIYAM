"""Review sheet for the domain reviewer: export every rule unit with its machine reading to CSV/Markdown, and import
the reviewer's decisions back into rules/corpus/rule-units.yaml and the rulepack manifest.

accept -> human_reviewed true (unit and manifest rule) with reviewer and date
modify -> unit status needs_rework, correction appended to notes; no rule is changed automatically
reject -> unit status rejected
A unit that already has a decision is only changed with force=True; repeating the same decision is a no-op."""

import csv
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml

from app.corpus.models import SOURCES, RuleUnit, source_of
from app.rulepack.loader import read_manifest, write_manifest
from app.rulepack.models import Rule

INFO_COLUMNS = ["unit_id", "source", "clause_id", "page", "tier", "unit_text", "clause_text", "machine_reading", "threshold",
                "scope", "duplicate_of", "reading_dependent"]
# Units whose spec reading departs from the literal clause text (found in evaluation run 20261118T140452Z-5b7edb).
# They are listed first so a reviewer settles the reading before anything is scored against it.
READING_DEPENDENT = {
    "MBBL2016-4.8.2#1": "The clause says 'where provided in a residential building'; the spec drops that condition and "
                        "checks store rooms in every building. Both models' candidates kept the residential "
                        "condition, which never applies to the test buildings (they declare no OccupancyType). "
                        "Decide which reading is intended.",
    "MBBL2016-5.4.1#b2": "The sentence says 'Doorways' (all doors); the spec reads it as exit doors only "
                         "(Pset_DoorCommon.FireExit = TRUE) because clause 5.4.1 is about exits. Candidates that "
                         "applied the 2 m height to every door failed the test buildings, which contain a lower "
                         "non-exit door. Decide which reading is intended.",
}
REVIEW_COLUMNS = ["decision", "corrected_reading", "corrected_threshold", "comments", "reviewer_name", "reviewed_on"]
COLUMNS = INFO_COLUMNS + REVIEW_COLUMNS
DECISIONS = ("accept", "modify", "reject")
BOUND_WORDS = {"minInclusive": "at least", "minExclusive": "more than", "maxInclusive": "at most",
               "maxExclusive": "less than"}


class ReviewImportError(Exception):
    def __init__(self, errors: list[str]):
        super().__init__("\n".join(errors))
        self.errors = errors


def load_units_yaml(path: Path) -> list[RuleUnit]:
    return [RuleUnit(**u) for u in yaml.safe_load(path.read_text(encoding="utf-8")) or []]


def save_units_yaml(path: Path, units: list[RuleUnit]) -> None:
    with open(path, "w", encoding="utf-8") as fh:  # same layout as repository.export_units
        yaml.safe_dump([u.model_dump() for u in units], fh, allow_unicode=True, sort_keys=False, width=100)


def _threshold(rule: Rule | None, pack: Path) -> str:
    if rule is None:
        return "none"
    text = (pack / (rule.ids_file or rule.check_file)).read_text(encoding="utf-8")
    if rule.ids_file:
        bounds = re.findall(r"xs:(minInclusive|minExclusive|maxInclusive|maxExclusive) value=\"([^\"]+)\"", text)
        return "; ".join(f"{BOUND_WORDS[k]} {v} m" for k, v in bounds) or "none"
    m = re.search(r"^\s*required = ([0-9.]+)", text, re.MULTILINE)
    if not m:
        return "none"
    unit = "m2" if "space_floor_area_m2" in (rule.scope.measures or []) else "m"
    return f"at least {m.group(1)} {unit} (computed: {', '.join(rule.scope.measures or [])})"


def _scope(rule: Rule | None) -> str:
    if rule is None:
        return "not in the rulepack"
    s = rule.scope
    if s.selector is not None:
        value = str(s.selector.value).upper() if isinstance(s.selector.value, bool) else s.selector.value
        where = f"{s.ifc_class} where {s.selector.pset}.{s.selector.property} is {value}"
    else:
        where = f"{s.ifc_class}, selected inside the check"
    needs = ", ".join(d.key.split(":", 1)[1] for d in s.required_data)
    return f"{where}; needs {needs}" if needs else where


def sheet_rows(units: list[RuleUnit], pack: Path) -> list[dict[str, str]]:
    manifest = read_manifest(pack)
    rules = {r.unit_id: r for r in (manifest.rules if manifest else [])}
    rows = []
    for u in units:
        rule = rules.get(u.id)
        spec = None if rule else _spec(u.id)
        if spec is not None:  # a spec-generated unit: not in any rulepack until it is reviewed
            from app.specgen.models import parent_clause

            clause = parent_clause(spec.clause_id)
            page, clause_text, threshold, scope = str(clause.page), clause.text, _spec_threshold(spec), _spec_scope(spec)
        else:
            page, clause_text = (str(rule.page), rule.clause_text) if rule else ("", "")
            threshold, scope = _threshold(rule, pack), _scope(rule)
        rows.append({
            "unit_id": u.id, "source": SOURCES.get(source_of(u.id), source_of(u.id)), "clause_id": u.clause_id, "page": page, "tier": u.tier,
            "unit_text": " ".join(u.text.split()), "clause_text": clause_text,
            "machine_reading": " ".join((u.notes or "none").split()), "threshold": threshold,
            "scope": scope, "duplicate_of": u.duplicate_of or "", "reading_dependent": READING_DEPENDENT.get(u.id, ""),
            **{c: "" for c in REVIEW_COLUMNS},
        })
    order = list(READING_DEPENDENT)
    return sorted(rows, key=lambda r: order.index(r["unit_id"]) if r["unit_id"] in order else len(order))


def _spec(unit_id: str):
    from app.fixtures.builders import REPO_ROOT, safe_name
    from app.specgen.models import Spec

    path = REPO_ROOT / "rules" / "specs" / f"{safe_name(unit_id)}.yaml"
    return Spec(**yaml.safe_load(path.read_text(encoding="utf-8"))) if path.exists() else None


def _spec_threshold(spec) -> str:
    if spec.threshold is None:
        return "none (forbidden operations: " + ", ".join(spec.params.forbidden_operations) + ")"
    t = spec.threshold
    measure = {"space_area_min": " (computed: space_floor_area_m2)", "space_height_min": " (computed: element_height_m)"}
    return f"{'at least' if t.inclusive else 'more than'} {t.text} {t.unit}{measure.get(spec.template, '')}"


def _spec_scope(spec) -> str:
    if spec.template.startswith("door"):
        s = spec.params.selector
        value = str(s.value).upper() if isinstance(s.value, bool) else s.value
        needs = {"door_width_min": "Qto_DoorBaseQuantities.Width",
                 "door_height_min": "Qto_DoorBaseQuantities.Height"}.get(spec.template, "OperationType")
        return f"IfcDoor where {s.pset}.{s.property} is {value}; needs {s.pset}.{s.property}, {needs}; not in a rulepack"
    return (f"IfcSpace where Pset_SpaceCommon.Category is {' or '.join(spec.params.categories)}; needs "
            "Pset_SpaceCommon.Category and body geometry; not in a rulepack")


def export_sheet(units_yaml: Path, pack: Path, out_csv: Path, out_md: Path | None = None) -> int:
    rows = sheet_rows(load_units_yaml(units_yaml), pack)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8-sig") as fh:  # the BOM makes Excel read UTF-8
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    if out_md is not None:
        out_md.write_text(_markdown(rows), encoding="utf-8")
    return len(rows)


def _markdown(rows: list[dict[str, str]]) -> str:
    parts = ["# NIYAM rule review sheet\n",
             "Fill in the empty columns of `review-sheet.csv` (it opens in Excel): **decision** is `accept`, `modify` "
             "or `reject`; give your name and the date. For `modify`, write the corrected reading and/or "
             "threshold. Every rule below is a draft machine encoding of the quoted clause.\n"]
    for r in rows:
        parts += [f"## {r['unit_id']} ({r['tier']}, page {r['page'] or '?'})\n", f"**Source:** {r['source']}\n",
                  f"**Rule text:** {r['unit_text']}\n", f"**Machine reading:** {r['machine_reading']}\n",
                  f"**Threshold:** {r['threshold']}\n", f"**Applies to:** {r['scope']}\n",
                  *([f"**Claimed duplicate of:** {r['duplicate_of']} (confirm or reject in comments)\n"]
                    if r["duplicate_of"] else []),
                  *([f"**Reading-dependent:** {r['reading_dependent']}\n"] if r["reading_dependent"] else []),
                  "<details><summary>Full clause text</summary>\n\n```\n" + r["clause_text"] + "\n```\n</details>\n"]
    return "\n".join(parts)


def _existing_decision(u: RuleUnit) -> str | None:
    return {"needs_rework": "modify", "rejected": "reject"}.get(u.status) or ("accept" if u.human_reviewed else None)


@dataclass
class ImportResult:
    changed: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)


def import_sheet(sheet: Path, units_yaml: Path, pack: Path, *, force: bool = False,
                 today: str | None = None) -> ImportResult:
    units = load_units_yaml(units_yaml)
    by_id = {u.id: u for u in units}
    errors, decisions = [], []
    with open(sheet, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in ("unit_id", *REVIEW_COLUMNS) if c not in (reader.fieldnames or [])]
        if missing:
            raise ReviewImportError([f"row 1: missing columns {missing}"])
        for spreadsheet_row, row in enumerate(reader, start=2):
            line = f"{spreadsheet_row} (file line {reader.line_num})"  # clause cells span lines
            uid = (row.get("unit_id") or "").strip()
            decision = (row.get("decision") or "").strip().lower()
            name = (row.get("reviewer_name") or "").strip()
            on = (row.get("reviewed_on") or "").strip() or today or date.today().isoformat()
            if uid not in by_id:
                errors.append(f"row {line}: unknown unit_id {uid!r}")
                continue
            if not decision:
                continue
            if decision not in DECISIONS:
                errors.append(f"row {line}: decision {decision!r} for {uid} must be one of {', '.join(DECISIONS)}")
                continue
            if not name:
                errors.append(f"row {line}: decision {decision!r} for {uid} has no reviewer_name")
                continue
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", on):
                errors.append(f"row {line}: reviewed_on {on!r} for {uid} must be YYYY-MM-DD")
                continue
            existing = _existing_decision(by_id[uid])
            same = existing == decision and by_id[uid].reviewer == name
            if existing and not same and not force:
                errors.append(f"row {line}: {uid} already has decision {existing!r} by {by_id[uid].reviewer!r}; "
                              "use --force to replace it")
                continue
            decisions.append((uid, decision, name, on, row, same))
    if errors:
        raise ReviewImportError(errors)

    result = ImportResult()
    accepted = {}
    for uid, decision, name, on, row, same in decisions:
        if same:
            result.unchanged.append(uid)
            continue
        u = by_id[uid]
        update = {"reviewer": name, "reviewed_on": on, "human_reviewed": decision == "accept"}
        if decision == "accept":
            update["status"] = "pilot" if u.status in ("needs_rework", "rejected") else u.status
            accepted[uid] = (name, on)
        else:
            update["status"] = "needs_rework" if decision == "modify" else "rejected"
            fields = [f"{k}={row.get(k, '').strip()}" for k in ("corrected_reading", "corrected_threshold", "comments")
                      if (row.get(k) or "").strip()]
            note = f"REVIEW {decision} ({name}, {on}): " + ("; ".join(fields) or "no comment")
            update["notes"] = f"{u.notes}\n{note}" if u.notes else note
        by_id[uid] = u.model_copy(update=update)
        result.changed.append(uid)
    save_units_yaml(units_yaml, [by_id[u.id] for u in units])

    manifest = read_manifest(pack)
    if manifest is not None:
        for rule in manifest.rules:
            u = by_id.get(rule.unit_id)
            if rule.unit_id in result.changed and u is not None:
                rule.human_reviewed = u.human_reviewed
                rule.reviewer, rule.reviewed_on = (accepted[rule.unit_id] if rule.unit_id in accepted else (None, None))
        write_manifest(pack, manifest)
    return result
