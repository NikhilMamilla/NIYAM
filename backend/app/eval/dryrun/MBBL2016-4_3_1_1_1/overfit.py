import math


def check(model, helpers):
    """MBBL2016-4.3.1.1#1: a room for human habitation shall be at least 2.75 m high. DRAFT, not human-reviewed."""
    required = 2.7
    findings = []
    for space in helpers.elements(model, "IfcSpace"):
        category = helpers.pset_value(model, space, "Pset_SpaceCommon", "Category")
        if category is None:
            findings.append(helpers.finding(
                space, "unchecked",
                "This space does not declare its category (Pset_SpaceCommon.Category), so it is unknown "
                "whether the rule applies."))
            continue
        if category != "Habitable":
            continue
        height = helpers.element_height_m(model, space)
        if height is None:
            findings.append(helpers.finding(
                space, "unchecked",
                "This habitable room has no geometry, so its height could not be computed."))
        elif height < required - 1e-9:
            findings.append(helpers.finding(
                space, "fail",
                f"Computed room height is {height:.2f} m; this rule requires at least {required:g} m.",
                measured=height, required=required))
        else:
            findings.append(helpers.finding(
                space, "pass",
                f"Computed room height is {height:.2f} m; this rule requires at least {required:g} m.",
                measured=height, required=required))
    return findings
