import io

import pytest

from tests.factories import (
    make_kml_bytes,
    make_polygon_shapefile_zip,
    make_projected_polygon_shapefile_zip,
)


def test_upload_shapefile_returns_completed(client):
    zip_bytes = make_polygon_shapefile_zip()
    resp = client.post(
        "/api/files/",
        files={"file": ("plot.zip", io.BytesIO(zip_bytes), "application/zip")},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "COMPLETED"
    assert body["feature_count"] == 1
    assert body["crs"] == "EPSG:4326"
    assert body["projected_crs"] is not None
    assert body["file_type"] == "shapefile"


def test_get_file_info(client):
    zip_bytes = make_polygon_shapefile_zip()
    upload = client.post(
        "/api/files/",
        files={"file": ("plot.zip", io.BytesIO(zip_bytes), "application/zip")},
    )
    file_id = upload.json()["id"]

    resp = client.get(f"/api/files/{file_id}/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == file_id
    assert body["filename"] == "plot.zip"
    assert body["status"] == "COMPLETED"


def test_shapefile_measurements_reports_projected_area(client):
    zip_bytes = make_polygon_shapefile_zip()
    upload = client.post(
        "/api/files/",
        files={"file": ("plot.zip", io.BytesIO(zip_bytes), "application/zip")},
    )
    file_id = upload.json()["id"]

    resp = client.get(f"/api/files/{file_id}/measurements/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["file_id"] == file_id
    assert len(body["features"]) == 1
    feature = body["features"][0]
    assert feature["measurement_type"] == "area"
    # a 2x2 degree box reprojected to UTM meters is way more than 1000 m2
    assert feature["measurement_value"] > 1000
    assert feature["geometry"] is not None
    assert feature["geometry"]["type"] == "Polygon"
    assert feature["source_crs"] == "EPSG:4326"


def test_upload_already_projected_shapefile_skips_reprojection(client):
    zip_bytes = make_projected_polygon_shapefile_zip()
    upload = client.post(
        "/api/files/",
        files={"file": ("plot_utm.zip", io.BytesIO(zip_bytes), "application/zip")},
    )
    assert upload.status_code == 201
    body = upload.json()
    assert body["status"] == "COMPLETED"
    assert body["crs"] == "EPSG:32643"
    assert body["projected_crs"] == "EPSG:32643"
    file_id = body["id"]

    resp = client.get(f"/api/files/{file_id}/measurements/")
    assert resp.status_code == 200
    feature = resp.json()["features"][0]
    assert feature["measurement_type"] == "area"
    # 200m x 200m square -> 40000 m2, already in meters with no reprojection
    assert feature["measurement_value"] == pytest.approx(40000, rel=1e-3)
    assert feature["source_crs"] == "EPSG:32643"


def test_upload_kml_has_area_length_and_none(client):
    kml_bytes = make_kml_bytes()
    upload = client.post(
        "/api/files/",
        files={"file": ("fields.kml", io.BytesIO(kml_bytes), "application/vnd.google-earth.kml+xml")},
    )
    assert upload.status_code == 201
    body = upload.json()
    assert body["status"] == "COMPLETED"
    assert body["feature_count"] == 3
    assert body["crs"] == "EPSG:4326"
    file_id = body["id"]

    resp = client.get(f"/api/files/{file_id}/measurements/")
    features = {f["geometry_type"]: f for f in resp.json()["features"]}

    assert features["Polygon"]["measurement_type"] == "area"
    assert features["Polygon"]["measurement_value"] > 1000

    assert features["LineString"]["measurement_type"] == "length"
    assert features["LineString"]["measurement_value"] > 1000

    assert features["Point"]["measurement_type"] == "none"
    assert features["Point"]["measurement_value"] is None


def test_upload_rejects_unsupported_extension(client):
    resp = client.post(
        "/api/files/",
        files={"file": ("notes.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert resp.status_code == 400


def test_upload_rejects_missing_file(client):
    resp = client.post("/api/files/")
    assert resp.status_code == 400


def test_get_unknown_file_returns_404(client):
    resp = client.get("/api/files/doesnotexist/")
    assert resp.status_code == 404


def test_get_unknown_measurements_returns_404(client):
    resp = client.get("/api/files/doesnotexist/measurements/")
    assert resp.status_code == 404


def test_upload_corrupt_zip_is_failed_not_500(client):
    resp = client.post(
        "/api/files/",
        files={"file": ("broken.zip", io.BytesIO(b"this is not a real zip file"), "application/zip")},
    )
    assert resp.status_code in (200, 201)
    body = resp.json()
    assert body["status"] == "FAILED"
    assert body["error"]
    assert body["feature_count"] == 0
