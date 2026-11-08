import pytest

from app.models import User
from app.security import verify_password
from app.services.users import AuthenticationError, authenticate, create_admin, create_member


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


def test_create_admin_cree_un_compte_role_admin(db_session):
    admin = create_admin(db_session, "Admin", "motdepasse123")

    assert admin.role == "admin"
    assert admin.is_active is True
    assert verify_password("motdepasse123", admin.password_hash)


def test_create_admin_refuse_prenom_deja_pris_meme_casse_differente(db_session, alice):
    with pytest.raises(ValueError):
        create_admin(db_session, "alice", "motdepasse123")


def test_create_admin_refuse_mot_de_passe_trop_court(db_session):
    with pytest.raises(ValueError):
        create_admin(db_session, "Admin", "court1")


def test_create_admin_refuse_prenom_vide(db_session):
    with pytest.raises(ValueError):
        create_admin(db_session, "   ", "motdepasse123")


def test_create_member_cree_un_compte_actif_role_member(db_session):
    membre = create_member(db_session, "Denise", "motdepasse123", "motdepasse123")

    assert membre.role == "member"
    assert membre.is_active is True
    assert verify_password("motdepasse123", membre.password_hash)


def test_create_member_mot_de_passe_stocke_hache(db_session):
    membre = create_member(db_session, "Denise", "motdepasse123", "motdepasse123")

    assert membre.password_hash != "motdepasse123"
    stocke = db_session.query(User).filter_by(first_name="Denise").one()
    assert stocke.password_hash == membre.password_hash


def test_create_member_refuse_prenom_deja_pris_meme_casse_differente(db_session, alice):
    with pytest.raises(ValueError):
        create_member(db_session, "alice", "motdepasse123", "motdepasse123")


def test_create_member_refuse_prenom_deja_pris_par_un_admin(db_session, admin):
    with pytest.raises(ValueError):
        create_member(db_session, "Admin", "motdepasse123", "motdepasse123")


def test_create_member_refuse_confirmation_differente(db_session):
    with pytest.raises(ValueError):
        create_member(db_session, "Denise", "motdepasse123", "autre-mot-de-passe")


def test_create_member_refuse_mot_de_passe_trop_court(db_session):
    with pytest.raises(ValueError):
        create_member(db_session, "Denise", "court1", "court1")


def test_create_member_refuse_prenom_vide(db_session):
    with pytest.raises(ValueError):
        create_member(db_session, "   ", "motdepasse123", "motdepasse123")
