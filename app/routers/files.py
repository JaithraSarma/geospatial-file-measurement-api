from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi import File as FormFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import File as FileModel
from app.processing import process_upload
from app.schemas import FeatureMeasurement, FileInfo, MeasurementsResponse

router = APIRouter(prefix="/api/files", tags=["files"])

SUPPORTED_EXTENSIONS = (".zip", ".kml")


def _to_file_info(row: FileModel) -> FileInfo:
    # FileInfo.crs maps to the ORM's source_crs, not a field of the same name
    return FileInfo(
        id=row.id,
        filename=row.filename,
        file_type=row.file_type,
        feature_count=row.feature_count,
        status=row.status,
        crs=row.source_crs,
        projected_crs=row.projected_crs,
        error=row.error,
        created_at=row.created_at,
    )


@router.post("/", response_model=FileInfo, status_code=201)
async def upload_file(file: UploadFile | None = FormFile(None), db: Session = Depends(get_db)):
    if file is None or not file.filename:
        raise HTTPException(status_code=400, detail="no file provided")
    if not file.filename.lower().endswith(SUPPORTED_EXTENSIONS):
        raise HTTPException(status_code=400, detail="unsupported file extension")

    raw_bytes = await file.read()
    try:
        row = process_upload(file.filename, raw_bytes, db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_file_info(row)


@router.get("/", response_model=list[FileInfo])
def list_files(db: Session = Depends(get_db)):
    rows = db.query(FileModel).order_by(FileModel.created_at.desc()).all()
    return [_to_file_info(r) for r in rows]


@router.get("/{file_id}/", response_model=FileInfo)
def get_file(file_id: str, db: Session = Depends(get_db)):
    row = db.get(FileModel, file_id)
    if row is None:
        raise HTTPException(status_code=404, detail="file not found")
    return _to_file_info(row)


@router.get("/{file_id}/measurements/", response_model=MeasurementsResponse)
def get_measurements(file_id: str, db: Session = Depends(get_db)):
    row = db.get(FileModel, file_id)
    if row is None:
        raise HTTPException(status_code=404, detail="file not found")

    features = [
        FeatureMeasurement(
            feature_index=f.feature_index,
            geometry_type=f.geometry_type,
            geometry=f.geometry_geojson,
            source_crs=f.source_crs,
            measurement_type=f.measurement_type,
            measurement_value=f.measurement_value,
            measurement_unit=f.measurement_unit,
            note=f.note,
            properties=f.properties,
        )
        for f in sorted(row.features, key=lambda f: f.feature_index)
    ]
    return MeasurementsResponse(file_id=row.id, features=features)
