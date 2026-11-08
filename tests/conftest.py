import json
from base64 import b64encode

import itsdangerous
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import settings
from app.db import create_db_engine, get_db
from app.main import app
from app.models import Base, User
from app.security import hash_password

FIXTURE_PASSWORD = "password123"


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
        test_client.cookies.set("session", signer.sign(payload).decode("utf-8"))

    return _login_as


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
