from shapely.geometry import (
    GeometryCollection,
    LineString,
    MultiLineString,
    MultiPolygon,
    Point,
    Polygon,
)

from app.crs import transform_geom
from app.measurement import measure


def test_measure_polygon_area_projected():
    # roughly 0.01 deg square near bangalore, projected to UTM first
    poly = Polygon([(77.5, 12.9), (77.6, 12.9), (77.6, 13.0), (77.5, 13.0)])
    projected = transform_geom(poly, "EPSG:4326", "EPSG:32643")
    kind, value, unit, note = measure(projected)
    assert kind == "area"
    assert unit == "m2"
    # raw degree area would be ~0.01, projected area should be in the
    # square-kilometer range (not confused with the degree figure)
    assert value > 100000
    assert note is None


def test_measure_multipolygon():
    a = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    b = Polygon([(20, 20), (30, 20), (30, 30), (20, 30)])
    mp = MultiPolygon([a, b])
    kind, value, unit, note = measure(mp)
    assert kind == "area"
    assert value == 200.0
    assert unit == "m2"


def test_measure_linestring_length():
    line = LineString([(0, 0), (0, 100)])
    kind, value, unit, note = measure(line)
    assert kind == "length"
    assert value == 100.0
    assert unit == "m"


def test_measure_multilinestring():
    ml = MultiLineString([[(0, 0), (0, 10)], [(0, 0), (0, 5)]])
    kind, value, unit, note = measure(ml)
    assert kind == "length"
    assert value == 15.0
    assert unit == "m"


def test_measure_point_returns_none():
    kind, value, unit, note = measure(Point(5, 5))
    assert kind == "none"
    assert value is None


def test_measure_empty_geometry_returns_note():
    empty = Polygon()
    kind, value, unit, note = measure(empty)
    assert kind == "none"
    assert value is None
    assert note


def test_measure_invalid_geometry_returns_note():
    # self-intersecting bowtie polygon, invalid
    bowtie = Polygon([(0, 0), (10, 10), (10, 0), (0, 10)])
    kind, value, unit, note = measure(bowtie)
    assert kind == "none"
    assert value is None
    assert note


def test_measure_unsupported_geometry_type():
    gc = GeometryCollection([Point(0, 0), LineString([(0, 0), (1, 1)])])
    kind, value, unit, note = measure(gc)
    assert kind == "none"
    assert value is None
    assert note
