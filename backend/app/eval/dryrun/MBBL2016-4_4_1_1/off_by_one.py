import math


def check(model, helpers):
    """MBBL2016-4.4.1#1: room height of Kitchen more than 2.75 m. DRAFT generated from a rule spec, not human-reviewed."""
    required = 2.75
    categories = ('Kitchen',)
    findings = []
    for space in helpers.elements(model, "IfcSpace"):
        category = helpers.pset_value(model, space, "Pset_SpaceCommon", "Category")
        if category is None:
            findings.append(helpers.finding(
                space, "unchecked",
                "This space does not declare its category (Pset_SpaceCommon.Category), so it is unknown "
                "whether the rule applies."))
            continue
        if category not in categories:
            continue
        value = helpers.element_height_m(model, space)
        if value is None:
            findings.append(helpers.finding(
                space, "unchecked", "This space has no geometry, so its room height could not be computed."))
            continue
        verdict = "pass" if value > required + 1e-9 else "fail"
        findings.append(helpers.finding(
            space, verdict,
            f"Computed room height is {value:.2f} m; this rule requires more than {required:g} m.",
            measured=value, required=required))
    return findings
