import math


def check(model, helpers):
    """MBBL2016-4.5.2#1: the area of a bathroom shall not be less than 1.8 m2. DRAFT, not human-reviewed."""
    required = 1.8
    findings = []
    for space in helpers.elements(model, "IfcSpace"):
        category = helpers.pset_value(model, space, "Pset_SpaceCommon", "Category")
        if category is None:
            findings.append(helpers.finding(
                space, "unchecked",
                "This space does not declare its category (Pset_SpaceCommon.Category), so it is unknown "
                "whether the rule applies."))
            continue
        if category != "Bathroom":
            continue
        area = helpers.space_floor_area_m2(model, space)
        if area is None:
            findings.append(helpers.finding(
                space, "unchecked",
                "This bathroom has no geometry, so its floor area could not be computed."))
        elif area > required + 1e-9:
            findings.append(helpers.finding(
                space, "fail",
                f"Computed floor area is {area:.2f} m2; this rule requires at least {required:g} m2.",
                measured=area, required=required))
        else:
            findings.append(helpers.finding(
                space, "pass",
                f"Computed floor area is {area:.2f} m2; this rule requires at least {required:g} m2.",
                measured=area, required=required))
    return findings
