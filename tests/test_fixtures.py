from app.models import User


def test_fixtures_membres_et_admin(db_session, alice, bob, chloe, admin):
    assert alice.first_name == "Alice"
    assert alice.role == "member"
    assert bob.first_name == "Bob"
    assert chloe.first_name == "Chloé"
    assert admin.first_name == "Admin"
    assert admin.role == "admin"

    utilisateurs = db_session.query(User).all()
    assert {u.first_name for u in utilisateurs} == {"Alice", "Bob", "Chloé", "Admin"}


def test_fixtures_isolees_entre_tests(db_session):
    # Si Alice créée dans le test précédent persistait, la base ne serait pas vide ici.
    assert db_session.query(User).all() == []
