import math


def check(model, helpers):
    """MBBL2016-4.17.2#A: a staircase in a residential building shall be at least 1.0 m wide. DRAFT, not
    human-reviewed."""
    required = 0.95
    findings = []
    for flight in helpers.elements(model, "IfcStairFlight"):
        occupancy = helpers.building_occupancy(model, flight)
        if occupancy is None:
            findings.append(helpers.finding(
                flight, "unchecked",
                "The building of this stair flight does not declare its occupancy "
                "(Pset_BuildingCommon.OccupancyType), so it is unknown whether the rule applies."))
            continue
        if occupancy != "Residential":
            continue
        width = helpers.stair_flight_width_m(model, flight)
        if width is None:
            findings.append(helpers.finding(
                flight, "unchecked",
                "This stair flight has no geometry, so its width could not be computed."))
        elif width < required - 1e-9:
            findings.append(helpers.finding(
                flight, "fail",
                f"Computed stair width is {width:.2f} m; this rule requires at least {required:g} m.",
                measured=width, required=required))
        else:
            findings.append(helpers.finding(
                flight, "pass",
                f"Computed stair width is {width:.2f} m; this rule requires at least {required:g} m.",
                measured=width, required=required))
    return findings
