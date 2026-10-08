from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class File(Base):
    __tablename__ = "files"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    file_type: Mapped[str] = mapped_column(String, nullable=False)
    source_crs: Mapped[str | None] = mapped_column(String, nullable=True)
    projected_crs: Mapped[str | None] = mapped_column(String, nullable=True)
    feature_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, nullable=False)
    error: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    features: Mapped[list["Feature"]] = relationship(
        back_populates="file", cascade="all, delete-orphan"
    )


class Feature(Base):
    __tablename__ = "features"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_id: Mapped[str] = mapped_column(ForeignKey("files.id"), nullable=False)
    feature_index: Mapped[int] = mapped_column(Integer, nullable=False)
    geometry_type: Mapped[str] = mapped_column(String, nullable=False)
    source_crs: Mapped[str | None] = mapped_column(String, nullable=True)
    properties: Mapped[dict] = mapped_column(JSON, default=dict)
    geometry_geojson: Mapped[dict] = mapped_column(JSON, default=dict)
    measurement_type: Mapped[str] = mapped_column(String, nullable=False, default="none")
    measurement_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    measurement_unit: Mapped[str | None] = mapped_column(String, nullable=True)
    note: Mapped[str | None] = mapped_column(String, nullable=True)

    file: Mapped["File"] = relationship(back_populates="features")
