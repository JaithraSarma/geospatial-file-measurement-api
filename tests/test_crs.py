from pyproj import CRS
from shapely.geometry import LineString, Point, Polygon

from app.crs import pick_projected_crs, transform_geom, utm_epsg_for


def test_utm_epsg_bangalore():
    assert utm_epsg_for(77.6, 12.9) == 32643


def test_utm_epsg_nyc():
    assert utm_epsg_for(-74.0, 40.7) == 32618


def test_utm_epsg_sydney():
    assert utm_epsg_for(151.2, -33.9) == 32756


def test_pick_projected_crs_from_geographic():
    poly = Polygon([(77.5, 12.9), (77.6, 12.9), (77.6, 13.0), (77.5, 13.0)])
    crs = pick_projected_crs([poly], "EPSG:4326")
    assert crs.to_epsg() == 32643


def test_pick_projected_crs_returns_source_when_already_projected():
    poly = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    source = CRS.from_epsg(32643)
    crs = pick_projected_crs([poly], source)
    assert crs.to_epsg() == 32643


def test_transform_point():
    p = Point(77.6, 12.9)
    out = transform_geom(p, "EPSG:4326", "EPSG:32643")
    assert out.geom_type == "Point"
    # UTM coords are in meters, well away from 0-ish degree values
    assert out.x > 100000 and out.y > 100000


def test_transform_polygon_with_hole():
    exterior = [(77.5, 12.9), (77.6, 12.9), (77.6, 13.0), (77.5, 13.0)]
    hole = [(77.52, 12.92), (77.54, 12.92), (77.54, 12.94), (77.52, 12.94)]
    poly = Polygon(exterior, [hole])
    out = transform_geom(poly, "EPSG:4326", "EPSG:32643")
    assert out.geom_type == "Polygon"
    assert len(out.interiors) == 1
    # projected coords should be much bigger than degree-scale ones
    assert out.exterior.coords[0][0] > 1000


def test_transform_linestring():
    line = LineString([(-74.0, 40.7), (-73.9, 40.8)])
    out = transform_geom(line, "EPSG:4326", "EPSG:32618")
    assert out.geom_type == "LineString"
    assert out.length > 1000
