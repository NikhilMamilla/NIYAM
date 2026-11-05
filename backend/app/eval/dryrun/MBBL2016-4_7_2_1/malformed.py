import os


def check(model, helpers):
    """MBBL2016-4.7.2#1: floor area of Mezzanine at least 9.5 m2. DRAFT generated from a rule spec, not human-reviewed."""
    required = 9.5
    categories = ('Mezzanine',)
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
        value = helpers.space_floor_area_m2(model, space)
        if value is None:
            findings.append(helpers.finding(
                space, "unchecked", "This space has no geometry, so its floor area could not be computed."))
            continue
        verdict = "pass" if value >= required - 1e-9 else "fail"
        findings.append(helpers.finding(
            space, verdict,
            f"Computed floor area is {value:.2f} m2; this rule requires at least {required:g} m2.",
            measured=value, required=required))
    return findings
