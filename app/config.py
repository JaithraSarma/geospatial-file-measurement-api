from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App-wide settings, overridable via env vars (prefix GEO_)."""

    model_config = SettingsConfigDict(env_prefix="GEO_")

    app_title: str = "Geospatial File Measurement API"
    db_url: str = "sqlite:///./geo.db"


settings = Settings()
