"""Turns an uploaded file into a persisted File row with measured Features."""
import uuid

from shapely.geometry import mapping

from app.crs import pick_projected_crs, transform_geom
from app.measurement import measure
from app.models import Feature, File
from app.readers import kml_reader, shapefile_reader


def _detect_file_type(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".zip"):
        return "shapefile"
    if lower.endswith(".kml"):
        return "kml"
    raise ValueError(f"unsupported file extension: {filename}")


def process_upload(filename: str, raw_bytes: bytes, db) -> File:
    """Read, measure and persist an upload. Returns the File row either way.

    A malformed geo file does not raise - it's recorded as a FAILED file so
    the caller can return it to the client instead of a 500.
    """
    file_type = _detect_file_type(filename)
    file_row = File(
        id=uuid.uuid4().hex[:12],
        filename=filename,
        file_type=file_type,
        feature_count=0,
        status="FAILED",
    )

    try:
        reader = shapefile_reader if file_type == "shapefile" else kml_reader
        source_crs, raw_features = reader.read(raw_bytes)
        file_row.source_crs = source_crs

        if not raw_features:
            file_row.status = "COMPLETED"
            file_row.feature_count = 0
            db.add(file_row)
            db.commit()
            db.refresh(file_row)
            return file_row

        geoms = [f["geometry"] for f in raw_features]
        projected_crs = pick_projected_crs(geoms, source_crs)
        epsg = projected_crs.to_epsg()
        projected_crs_str = f"EPSG:{epsg}" if epsg else projected_crs.to_wkt()
        src_crs = source_crs or "EPSG:4326"

        feature_rows = []
        for f in raw_features:
            projected_geom = transform_geom(f["geometry"], src_crs, projected_crs)
            m_type, m_value, m_unit, note = measure(projected_geom)
            feature_rows.append(
                Feature(
                    feature_index=f["index"],
                    geometry_type=f["geometry_type"],
                    source_crs=source_crs,
                    properties=f["properties"],
                    geometry_geojson=mapping(f["geometry"]),
                    measurement_type=m_type,
                    measurement_value=m_value,
                    measurement_unit=m_unit,
                    note=note,
                )
            )

        file_row.features = feature_rows
        file_row.projected_crs = projected_crs_str
        file_row.feature_count = len(feature_rows)
        file_row.status = "COMPLETED"
        db.add(file_row)
        db.commit()
        db.refresh(file_row)
        return file_row

    except Exception as exc:
        db.rollback()
        file_row.features = []
        file_row.status = "FAILED"
        file_row.error = str(exc)
        file_row.feature_count = 0
        db.add(file_row)
        db.commit()
        db.refresh(file_row)
        return file_row
