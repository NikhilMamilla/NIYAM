import math


def check(model, helpers):
    """MBBL2016-4.17.2#A: a staircase in a residential building shall be at least 1.0 m wide. DRAFT, not
    human-reviewed."""
    required = 1.0
    findings = []
    for flight in helpers.elements(model, "IfcStairFlight"):
        occupancy = helpers.build