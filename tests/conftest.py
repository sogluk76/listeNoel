import io
import json
import re
from base64 import b64encode
from datetime import UTC, datetime

import itsdangerous
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.orm import Session

from app.config import settings
from app.db import create_db_engine, get_db
from app.main import app
from app.models import Base, Gift, User
from app.security import hash_password

FIXTURE_PASSWORD = "password123"


@pytest.fixture(autouse=True)
def _media_dir_isole(tmp_path, monkeypatch):
    """Aucun test ne doit écrire dans le vrai dossier media/ du projet."""
    monkeypatch.setattr(settings, "media_dir", tmp_path)


@pytest.fixture
def db_session():
    engine = create_db_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def login_as():
    """Pose directement un cookie de session valide, sans passer par un formulaire de login."""

    def _login_as(test_client: TestClient, user: User) -> None:
        signer = itsdangerous.TimestampSigner(settings.secret_key)
        payload = b64encode(json.dumps({"user_id": user.id}).encode("utf-8"))
        test_client.cookies.set(
            "session", signer.sign(payload).decode("utf-8"), domain="testserver.local"
        )

    return _login_as


@pytest.fixture
def extract_csrf_token():
    """Lit le jeton CSRF posé par `base.html` dans `hx-headers`, pour soumettre un formulaire."""

    def _extract(html: str) -> str:
        match = re.search(r'X-CSRF-Token":\s*"([^"]+)"', html)
        assert match, "jeton CSRF introuvable dans la page"
        return match.group(1)

    return _extract


@pytest.fixture
def make_image_bytes():
    def _make(fmt: str = "PNG", size: tuple[int, int] = (100, 100)) -> bytes:
        buffer = io.BytesIO()
        Image.new("RGB", size, color="red").save(buffer, format=fmt)
        return buffer.getvalue()

    return _make


def _create_member(session, first_name):
    user = User(first_name=first_name, password_hash=hash_password(FIXTURE_PASSWORD))
    session.add(user)
    session.commit()
    return user


@pytest.fixture
def alice(db_session):
    return _create_member(db_session, "Alice")


@pytest.fixture
def bob(db_session):
    return _create_member(db_session, "Bob")


@pytest.fixture
def chloe(db_session):
    return _create_member(db_session, "Chloé")


@pytest.fixture
def admin(db_session):
    user = User(first_name="Admin", password_hash=hash_password(FIXTURE_PASSWORD), role="admin")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def create_gift(db_session):
    """Factory de cadeau pour les tests : `create_gift(auteur)` (perso) ou
    `create_gift(auteur, recipient=quelquun)` (suggestion)."""

    def _create(
        author,
        recipient=None,
        *,
        name="Cadeau",
        removed=False,
        archived_year=None,
        purchased_by=None,
    ):
        gift = Gift(
            name=name,
            recipient_id=(recipient or author).id,
            author_id=author.id,
            removed_at=datetime.now(UTC).replace(tzinfo=None) if removed else None,
            archived_year=archived_year,
            purchased_by_id=purchased_by.id if purchased_by else None,
        )
        db_session.add(gift)
        db_session.commit()
        return gift

    return _create
