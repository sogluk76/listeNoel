import pytest
from sqlalchemy.orm import Session

from app.cli import create_admin, main
from app.db import create_db_engine
from app.models import Base, User
from app.security import verify_password


def test_create_admin_cree_un_compte_role_admin(db_session):
    admin = create_admin("Admin", "motdepasse123", session=db_session)

    assert admin.role == "admin"
    assert admin.first_name == "Admin"
    assert verify_password("motdepasse123", admin.password_hash)


def test_mot_de_passe_stocke_hache(db_session):
    admin = create_admin("Admin", "motdepasse123", session=db_session)

    assert admin.password_hash != "motdepasse123"
    stocke = db_session.query(User).filter_by(first_name="Admin").one()
    assert stocke.password_hash == admin.password_hash


def test_create_admin_refuse_prenom_deja_pris_meme_casse_differente(db_session, alice):
    with pytest.raises(ValueError):
        create_admin("alice", "motdepasse123", session=db_session)


def test_create_admin_refuse_doublon_entre_deux_admins(db_session):
    create_admin("Admin", "motdepasse123", session=db_session)

    with pytest.raises(ValueError):
        create_admin("Admin", "autremotdepasse", session=db_session)


def test_create_admin_refuse_mot_de_passe_trop_court(db_session):
    with pytest.raises(ValueError):
        create_admin("Admin", "court1", session=db_session)


def test_create_admin_refuse_prenom_vide(db_session):
    with pytest.raises(ValueError):
        create_admin("   ", "motdepasse123", session=db_session)


def test_cli_create_admin_flux_interactif(monkeypatch, capsys):
    engine = create_db_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    monkeypatch.setattr("app.cli.SessionLocal", lambda: Session(engine))
    monkeypatch.setattr("builtins.input", lambda _: "Admin")
    monkeypatch.setattr("app.cli.getpass", lambda _: "motdepasse123")

    main(["create-admin"])

    assert "créé" in capsys.readouterr().out
    with Session(engine) as verif:
        admin = verif.query(User).filter_by(first_name="Admin").one()
        assert admin.role == "admin"
