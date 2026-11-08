import pytest

from app.services.users import AuthenticationError, authenticate


def test_authenticate_membre_reussit(db_session, alice):
    user = authenticate(db_session, "Alice", "password123", role="member")

    assert user.id == alice.id


def test_authenticate_admin_reussit(db_session, admin):
    user = authenticate(db_session, "Admin", "password123", role="admin")

    assert user.id == admin.id


def test_authenticate_insensible_a_la_casse_du_prenom(db_session, alice):
    user = authenticate(db_session, "alice", "password123", role="member")

    assert user.id == alice.id


def test_authenticate_refuse_mauvais_mot_de_passe(db_session, alice):
    with pytest.raises(AuthenticationError):
        authenticate(db_session, "Alice", "mauvais-mot-de-passe", role="member")


def test_authenticate_refuse_mauvais_role(db_session, alice):
    # Alice est membre : même avec le bon mot de passe, pas d'authentification côté admin.
    with pytest.raises(AuthenticationError):
        authenticate(db_session, "Alice", "password123", role="admin")


def test_authenticate_refuse_prenom_inconnu(db_session):
    with pytest.raises(AuthenticationError):
        authenticate(db_session, "Inconnu", "password123", role="member")


def test_authenticate_refuse_compte_inactif(db_session, alice):
    alice.is_active = False
    db_session.commit()

    with pytest.raises(AuthenticationError):
        authenticate(db_session, "Alice", "password123", role="member")


def test_authenticate_message_generique_identique_dans_tous_les_cas(db_session, alice):
    messages = set()

    for prenom, mdp, role in [
        ("Alice", "mauvais", "member"),
        ("Inconnu", "password123", "member"),
        ("Alice", "password123", "admin"),
    ]:
        try:
            authenticate(db_session, prenom, mdp, role=role)
        except AuthenticationError as exc:
            messages.add(str(exc))

    assert len(messages) == 1
