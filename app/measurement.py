AREA_TYPES = {"Polygon", "MultiPolygon"}
LENGTH_TYPES = {"LineString", "MultiLineString"}
NONE_TYPES = {"Point", "MultiPoint"}


def measure(geom):
    """Measure an already-projected geometry.

    Returns (measurement_type, value, unit, note).
    """
    if geom is None or geom.is_empty:
        return "none", None, None, "empty geometry"

    if not geom.is_valid:
        return "none", None, None, "invalid geometry"

    geom_type = geom.geom_type

    if geom_type in AREA_TYPES:
        return "area", round(geom.area, 4), "m2", None

    if geom_type in LENGTH_TYPES:
        return "length", round(geom.length, 4), "m", None

    if geom_type in NONE_TYPES:
        return "none", None, None, None

    return "none", None, None, f"unsupported geometry type: {geom_type}"
