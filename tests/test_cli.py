from sqlalchemy.orm import Session

from app.cli import main
from app.db import create_db_engine
from app.models import Base, User


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


def test_cli_create_admin_refuse_confirmation_differente(monkeypatch, capsys, db_session):
    monkeypatch.setattr("app.cli.SessionLocal", lambda: db_session)
    monkeypatch.setattr("builtins.input", lambda _: "Admin")
    mots_de_passe = iter(["motdepasse123", "autre-mot-de-passe"])
    monkeypatch.setattr("app.cli.getpass", lambda _: next(mots_de_passe))

    try:
        main(["create-admin"])
    except SystemExit as exc:
        assert exc.code == 1
    else:
        raise AssertionError("SystemExit attendu")

    assert "ne correspondent pas" in capsys.readouterr().err
    assert db_session.query(User).count() == 0
