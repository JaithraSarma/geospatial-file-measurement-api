from fastapi.testclient import TestClient

from app.main import app
from app.models import File, Feature


def test_health_endpoint():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_file_and_feature_roundtrip(db_session):
    f = File(
        id="abc123",
        filename="parcels.zip",
        file_type="shapefile",
        source_crs="EPSG:4326",
        projected_crs="EPSG:32643",
        feature_count=1,
        status="COMPLETED",
    )
    db_session.add(f)
    db_session.flush()

    feat = Feature(
        file_id=f.id,
        feature_index=0,
        geometry_type="Polygon",
        source_crs="EPSG:4326",
        properties={"name": "lot 1"},
        geometry_geojson={"type": "Polygon", "coordinates": []},
        measurement_type="area",
        measurement_value=123.4567,
        measurement_unit="m2",
    )
    db_session.add(feat)
    db_session.commit()

    loaded = db_session.query(File).filter_by(id="abc123").one()
    assert loaded.filename == "parcels.zip"
    assert loaded.feature_count == 1
    assert len(loaded.features) == 1
    assert loaded.features[0].measurement_value == 123.4567
    assert loaded.features[0].properties == {"name": "lot 1"}
