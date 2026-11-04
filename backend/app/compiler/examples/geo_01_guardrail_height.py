import math


def check(model, helpers):
    """EXAMPLE (synthetic): a guard rail shall be at least 1.1 m high."""
    required = 1.1
    findings = []
    for rail in helpers.elements(model, "IfcRailing"):
        kind = helpers.pset_value(model, rail, "Pset_RailingCommon", "PredefinedUse")
        if kind is None:
            findings.append(helpers.finding(
                rail, "unchecked",
                "This railing does not declare its use (Pset_RailingCommon.PredefinedUse), so it is unknown "
                "whether the example rule applies."))
            continue
        if kind != "GUARDRAIL":
            continue
        height = helpers.element_height_m(model, rail)
        if height is None:
            findings.append(helpers.finding(
                rail, "unchecked", "This guard rail has no geometry, so its height could not be computed."))
            continue
        verdict = "fail" if height < required - 1e-9 else "pass"
        findings.append(helpers.finding(
            rail, verdict, f"Computed height is {height:.2f} m; the example rule requires at least {required:g} m.",
            measured=height, required=required))
    return findings
