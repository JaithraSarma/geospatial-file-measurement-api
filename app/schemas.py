from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FileInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    file_type: str
    feature_count: int
    status: str
    crs: str | None = None
    projected_crs: str | None = None
    error: str | None = None
    created_at: datetime


class FeatureMeasurement(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    feature_index: int
    geometry_type: str
    measurement_type: str
    measurement_value: float | None = None
    measurement_unit: str | None = None
    note: str | None = None
    properties: dict = {}


class MeasurementsResponse(BaseModel):
    file_id: str
    features: list[FeatureMeasurement]
