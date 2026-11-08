from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    secret_key: str = "dev-secret-key-change-me-in-production"
    database_path: Path = Path("data/app.db")
    media_dir: Path = Path("media")
    session_max_age_seconds: int = 60 * 60 * 24 * 30  # RG-07 : session de 30 jours
    session_https_only: bool = False  # à passer à True en production (cookie Secure)


settings = Settings()
