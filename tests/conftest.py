"""Fixtures : base SQLite en mémoire, membres Alice / Bob / Chloé et un admin."""

import os
import re
import tempfile

os.environ["NOEL_TESTING"] = "1"
os.environ["NOEL_SECRET_KEY"] = "cle-de-test"
os.environ["NOEL_DATABASE_URL"] = "sqlite://"
os.environ["NOEL_MEDIA_DIR"] = tempfile.mkdtemp(prefix="noel-media-")
os.environ["NOEL_PRIVATE_MEDIA_DIR"] = tempfile.mkdtemp(prefix="noel-prive-")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import ROLE_ADMIN, ROLE_MEMBER, Gift, User  # noqa: E402
from app.security import hash_password  # noqa: E402

PASSWORD = "motdepasse1"
_HASH = hash_password(PASSWORD)  # haché une seule fois : Argon2 est volontairement lent
_CSRF_RE = re.compile(r'name="csrf-token" content="([^"]+)"')


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = factory()

    def override():
        request_session = factory()
        try:
            yield request_session
        finally:
            request_session.close()

    app.dependency_overrides[get_db] = override
    yield session
    session.close()
    app.dependency_overrides.clear()
    engine.dispose()


def _user(db, name: str, role: str = ROLE_MEMBER) -> User:
    user = User(first_name=name, password_hash=_HASH, role=role)
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def alice(db):
    return _user(db, "Alice")


@pytest.fixture
def bob(db):
    return _user(db, "Bob")


@pytest.fixture
def chloe(db):
    return _user(db, "Chloé")


@pytest.fixture
def admin(db):
    return _user(db, "admin", ROLE_ADMIN)


def csrf_of(client: TestClient, path: str = "/login") -> str:
    match = _CSRF_RE.search(client.get(path).text)
    assert match, f"jeton CSRF introuvable sur {path}"
    return match.group(1)


def use_csrf(client: TestClient, path: str = "/login") -> None:
    client.headers["X-CSRF-Token"] = csrf_of(client, path)


@pytest.fixture
def anonymous(db):
    """Client sans session, avec un jeton CSRF valide."""
    client = TestClient(app, follow_redirects=False)
    use_csrf(client)
    return client


@pytest.fixture
def login(db):
    """Fabrique de clients connectés : login(alice) ou login(admin)."""

    def _login(user: User, password: str = PASSWORD) -> TestClient:
        client = TestClient(app, follow_redirects=False)
        if user.role == ROLE_ADMIN:
            use_csrf(client, "/admin/login")
            response = client.post(
                "/admin/login", data={"name": user.first_name, "password": password}
            )
            assert response.status_code == 303, response.text
            use_csrf(client, "/admin")
        else:
            use_csrf(client)
            response = client.post("/login", data={"user_id": user.id, "password": password})
            assert response.status_code == 303, response.text
            use_csrf(client, "/")
        return client

    return _login


@pytest.fixture
def make_gift(db):
    """Crée un cadeau directement en base : make_gift(author, recipient, "Vélo", price=...)."""

    def _make(author: User, recipient: User | None = None, name: str = "Cadeau", **fields) -> Gift:
        gift = Gift(name=name, author_id=author.id, recipient_id=(recipient or author).id, **fields)
        db.add(gift)
        db.commit()
        return gift

    return _make


def png_bytes(size: tuple[int, int] = (20, 20)) -> bytes:
    from io import BytesIO

    from PIL import Image

    buffer = BytesIO()
    Image.new("RGB", size, (30, 77, 58)).save(buffer, "PNG")
    return buffer.getvalue()
