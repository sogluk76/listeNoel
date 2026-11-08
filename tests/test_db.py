from app.db import create_db_engine


def test_pragma_foreign_keys_actif_sur_une_connexion():
    engine = create_db_engine("sqlite:///:memory:")

    with engine.connect() as conn:
        resultat = conn.exec_driver_sql("PRAGMA foreign_keys").scalar()

    assert resultat == 1
