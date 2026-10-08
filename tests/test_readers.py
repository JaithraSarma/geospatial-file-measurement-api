import io
import zipfile

import shapefile
from shapely.geometry import Polygon

from app.readers import kml_reader, shapefile_reader
from tests.factories import (
    make_kml_bytes,
    make_kml_with_hole_bytes,
    make_polygon_shapefile_zip,
    make_shapefile_zip,
)


def test_shapefile_reader_reads_polygon_and_props():
    data = make_polygon_shapefile_zip()
    source_crs, features = shapefile_reader.read(data)

    assert source_crs == "EPSG:4326"
    assert len(features) == 1
    feat = features[0]
    assert feat["index"] == 0
    assert feat["geometry_type"] == "Polygon"
    assert feat["geometry"].area == 4
    assert feat["properties"] == {"name": "plot1", "val": 5}


def test_shapefile_reader_reads_lines():
    coords = [(0, 0), (3, 4)]
    data = make_shapefile_zip(shape_type=shapefile.POLYLINE, records=[(coords, ["path1", 1])])
    source_crs, features = shapefile_reader.read(data)

    assert source_crs == "EPSG:4326"
    assert len(features) == 1
    assert features[0]["geometry_type"] == "LineString"
    assert features[0]["geometry"].length == 5


def test_shapefile_reader_without_prj_returns_none_crs():
    coords = [(0, 0), (0, 2), (2, 2), (2, 0), (0, 0)]
    data = make_shapefile_zip(records=[(coords, ["plot1", 5])], prj_wkt=None)
    source_crs, features = shapefile_reader.read(data)

    assert source_crs is None
    assert len(features) == 1


def test_shapefile_reader_missing_shp_raises():
    import io
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("readme.txt", "no shapefile here")

    try:
        shapefile_reader.read(buf.getvalue())
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_kml_reader_reads_all_geometry_types():
    data = make_kml_bytes()
    source_crs, features = kml_reader.read(data)

    assert source_crs == "EPSG:4326"
    # the no-geom placemark should be skipped
    assert len(features) == 3

    by_name = {f["properties"]["name"]: f for f in features}

    poly = by_name["field-a"]
    assert poly["geometry_type"] == "Polygon"
    assert poly["properties"]["crop"] == "wheat"
    assert poly["geometry"].exterior.coords[0] == (77.0, 12.0)

    line = by_name["road-a"]
    assert line["geometry_type"] == "LineString"
    assert line["properties"]["surface"] == "gravel"

    point = by_name["point-a"]
    assert point["geometry_type"] == "Point"
    assert point["geometry"].x == 77.0
    assert point["geometry"].y == 12.0


def test_kml_reader_accepts_str_input():
    data = make_kml_bytes().decode("utf-8")
    source_crs, features = kml_reader.read(data)
    assert source_crs == "EPSG:4326"
    assert len(features) == 3


def test_kml_reader_polygon_with_hole():
    data = make_kml_with_hole_bytes()
    _, features = kml_reader.read(data)

    assert len(features) == 1
    poly = features[0]["geometry"]
    assert poly.geom_type == "Polygon"
    assert len(poly.interiors) == 1

    outer_area = Polygon(poly.exterior).area
    assert poly.area < outer_area


def test_shapefile_reader_finds_members_in_subfolder_mixed_case():
    coords = [(0, 0), (0, 2), (2, 2), (2, 0), (0, 0)]
    data = make_shapefile_zip(
        records=[(coords, ["plot1", 5])],
        folder="shp_data/",
        basename="survey",
        exts=(".Shp", ".SHX", ".dbf", ".PRJ"),
    )
    source_crs, features = shapefile_reader.read(data)

    assert source_crs == "EPSG:4326"
    assert len(features) == 1
    assert features[0]["geometry_type"] == "Polygon"


def test_shapefile_reader_ignores_macosx_junk_members():
    coords = [(0, 0), (0, 2), (2, 2), (2, 0), (0, 0)]
    data = make_shapefile_zip(
        records=[(coords, ["plot1", 5])],
        basename="survey",
        extra_members={
            "__MACOSX/._survey.shp": b"not a real shapefile",
            "__MACOSX/survey/._survey.dbf": b"not a real dbf",
        },
    )
    source_crs, features = shapefile_reader.read(data)

    assert source_crs == "EPSG:4326"
    assert len(features) == 1
    assert features[0]["properties"] == {"name": "plot1", "val": 5}
