"""Configuration de l'application (variables d'environnement préfixées NOEL_)."""

import secrets
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="NOEL_", extra="ignore")

    secret_key: str = ""
    database_url: str = f"sqlite:///{(BASE_DIR / 'data' / 'app.db').as_posix()}"
    media_dir: Path = BASE_DIR / "media"
    secure_cookies: bool = False
    testing: bool = False

    session_days: int = 30
    max_login_failures: int = 5
    lock_minutes: int = 15
    max_upload_bytes: int = 5 * 1024 * 1024
    comments_poll_seconds: int = 20
    password_min_length: int = 8

    def resolved_secret_key(self) -> str:
        """Clé de signature des sessions.

        En production, définir NOEL_SECRET_KEY. Sinon une clé est générée une fois
        et conservée dans data/secret_key pour que les sessions survivent aux redémarrages.
        """
        if self.secret_key:
            return self.secret_key
        key_file = BASE_DIR / "data" / "secret_key"
        if key_file.exists():
            return key_file.read_text(encoding="utf-8").strip()
        key_file.parent.mkdir(parents=True, exist_ok=True)
        key = secrets.token_urlsafe(48)
        key_file.write_text(key, encoding="utf-8")
        return key


settings = Settings()
