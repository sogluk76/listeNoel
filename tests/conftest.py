import pytest
from sqlalchemy.orm import Session

from app.db import create_db_engine
from app.models import Base, User


@pytest.fixture
def db_session():
    engine = create_db_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _create_member(session, first_name):
    user = User(first_name=first_name, password_hash=f"hash-{first_name.lower()}")
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
    user = User(first_name="Admin", password_hash="hash-admin", role="admin")
    db_session.add(user)
    db_session.commit()
    return user
