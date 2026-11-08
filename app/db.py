from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings


def database_url(database_path: Path) -> str:
    if str(database_path) == ":memory:":
        return "sqlite:///:memory:"
    database_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{database_path}"


def create_db_engine(database_url: str) -> Engine:
    # SQLite :memory: perd son état à chaque nouvelle connexion : avec FastAPI, les
    # dépendances synchrones s'exécutent dans un thread à part, donc sans StaticPool
    # (une seule connexion partagée) chaque requête verrait une base vide.
    extra_kwargs = {"poolclass": StaticPool} if database_url == "sqlite:///:memory:" else {}
    engine = create_engine(database_url, connect_args={"check_same_thread": False}, **extra_kwargs)

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()

    return engine


engine = create_db_engine(database_url(settings.database_path))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
