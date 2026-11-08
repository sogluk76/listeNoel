from datetime import UTC, datetime, timedelta

import pytest

from app.config import settings
from app.models import User
from app.security import verify_password
from app.services.users import (
    GENERIC_AUTH_ERROR_MESSAGE,
    LOCKED_AUTH_ERROR_MESSAGE,
    MAX_FAILED_ATTEMPTS,
    AuthenticationError,
    MemberNotFoundError,
    authenticate,
    create_admin,
    create_member,
    list_members,
    reset_password,
    unlock_member,
    update_member,
)


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


def test_authenticate_bloque_apres_5_echecs_consecutifs(db_session, alice):
    for _ in range(MAX_FAILED_ATTEMPTS):
        with pytest.raises(AuthenticationError):
            authenticate(db_session, "Alice", "mauvais-mot-de-passe", role="member")

    with pytest.raises(AuthenticationError) as exc_info:
        authenticate(db_session, "Alice", "password123", role="member")
    assert str(exc_info.value) == LOCKED_AUTH_ERROR_MESSAGE


def test_authenticate_message_de_blocage_distinct_du_message_generique(db_session, alice):
    for _ in range(MAX_FAILED_ATTEMPTS):
        with pytest.raises(AuthenticationError):
            authenticate(db_session, "Alice", "mauvais-mot-de-passe", role="member")

    with pytest.raises(AuthenticationError) as exc_info:
        authenticate(db_session, "Alice", "mauvais-mot-de-passe", role="member")
    assert str(exc_info.value) != GENERIC_AUTH_ERROR_MESSAGE


def test_authenticate_4_echecs_puis_succes_remet_le_compteur_a_zero(db_session, alice):
    for _ in range(MAX_FAILED_ATTEMPTS - 1):
        with pytest.raises(AuthenticationError):
            authenticate(db_session, "Alice", "mauvais-mot-de-passe", role="member")

    user = authenticate(db_session, "Alice", "password123", role="member")

    assert user.failed_login_count == 0
    assert user.locked_until is None


def test_authenticate_accepte_apres_expiration_du_blocage(db_session, alice):
    alice.failed_login_count = MAX_FAILED_ATTEMPTS
    alice.locked_until = datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=1)
    db_session.commit()

    user = authenticate(db_session, "Alice", "password123", role="member")

    assert user.id == alice.id
    assert user.failed_login_count == 0
    assert user.locked_until is None


def test_authenticate_blocage_dun_compte_naffecte_pas_un_autre(db_session, alice, bob):
    for _ in range(MAX_FAILED_ATTEMPTS):
        with pytest.raises(AuthenticationError):
            authenticate(db_session, "Alice", "mauvais-mot-de-passe", role="member")

    user = authenticate(db_session, "Bob", "password123", role="member")

    assert user.id == bob.id


def test_deblocage_direct_permet_une_connexion_immediate(db_session, alice):
    """Ce que fera US-07 : remettre le compteur et `locked_until` à zéro débloque le compte."""
    alice.failed_login_count = MAX_FAILED_ATTEMPTS
    alice.locked_until = datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=15)
    db_session.commit()

    alice.failed_login_count = 0
    alice.locked_until = None
    db_session.commit()

    user = authenticate(db_session, "Alice", "password123", role="member")
    assert user.id == alice.id


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


def test_list_members_retourne_les_membres_actifs_et_inactifs(db_session, alice, bob):
    bob.is_active = False
    db_session.commit()

    membres = list_members(db_session)

    assert {m.id for m in membres} == {alice.id, bob.id}


def test_list_members_exclut_admin(db_session, alice, admin):
    membres = list_members(db_session)

    assert admin.id not in {m.id for m in membres}


def test_list_members_tries_par_prenom(db_session, chloe, alice, bob):
    membres = list_members(db_session)

    assert [m.first_name for m in membres] == ["Alice", "Bob", "Chloé"]


def test_update_member_modifie_le_prenom(db_session, alice):
    membre = update_member(db_session, alice.id, "Alicia", is_active=True)

    assert membre.first_name == "Alicia"


def test_update_member_refuse_prenom_deja_pris_par_un_autre_membre(db_session, alice, bob):
    with pytest.raises(ValueError):
        update_member(db_session, bob.id, "alice", is_active=True)


def test_update_member_autorise_a_garder_son_propre_prenom(db_session, alice):
    membre = update_member(db_session, alice.id, "alice", is_active=True)

    assert membre.first_name == "alice"


def test_update_member_refuse_prenom_vide(db_session, alice):
    with pytest.raises(ValueError):
        update_member(db_session, alice.id, "   ", is_active=True)


def test_update_member_desactive_le_compte(db_session, alice):
    membre = update_member(db_session, alice.id, "Alice", is_active=False)

    assert membre.is_active is False


def test_update_member_reactive_le_compte(db_session, alice):
    alice.is_active = False
    db_session.commit()

    membre = update_member(db_session, alice.id, "Alice", is_active=True)

    assert membre.is_active is True


def test_update_member_refuse_sur_id_admin(db_session, admin):
    with pytest.raises(MemberNotFoundError):
        update_member(db_session, admin.id, "Admin", is_active=False)


def test_update_member_refuse_sur_id_inconnu(db_session):
    with pytest.raises(MemberNotFoundError):
        update_member(db_session, 9999, "Quelqu'un", is_active=True)


def test_update_member_remplace_la_photo_et_supprime_lancienne(db_session, alice, make_image_bytes):
    membre = update_member(
        db_session, alice.id, "Alice", is_active=True, photo=make_image_bytes("PNG")
    )
    ancien_chemin = settings.media_dir / membre.photo_path

    membre = update_member(
        db_session, alice.id, "Alice", is_active=True, photo=make_image_bytes("PNG")
    )

    assert not ancien_chemin.exists()
    assert (settings.media_dir / membre.photo_path).exists()


def test_update_member_supprime_la_photo_sans_la_remplacer(db_session, alice, make_image_bytes):
    membre = update_member(
        db_session, alice.id, "Alice", is_active=True, photo=make_image_bytes("PNG")
    )
    ancien_chemin = settings.media_dir / membre.photo_path

    membre = update_member(db_session, alice.id, "Alice", is_active=True, remove_photo=True)

    assert membre.photo_path is None
    assert not ancien_chemin.exists()


def test_update_member_refuse_fichier_non_image(db_session, alice):
    with pytest.raises(ValueError):
        update_member(db_session, alice.id, "Alice", is_active=True, photo=b"pas une image")


def test_reset_password_remplace_lancien_mot_de_passe(db_session, alice):
    reset_password(db_session, alice.id, "nouveaumdp123", "nouveaumdp123")

    assert not verify_password("password123", alice.password_hash)
    assert verify_password("nouveaumdp123", alice.password_hash)


def test_reset_password_refuse_confirmation_differente(db_session, alice):
    with pytest.raises(ValueError):
        reset_password(db_session, alice.id, "nouveaumdp123", "autre-mdp")


def test_reset_password_refuse_mot_de_passe_trop_court(db_session, alice):
    with pytest.raises(ValueError):
        reset_password(db_session, alice.id, "court1", "court1")


def test_reset_password_leve_le_blocage(db_session, alice):
    alice.failed_login_count = MAX_FAILED_ATTEMPTS
    alice.locked_until = datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=15)
    db_session.commit()

    reset_password(db_session, alice.id, "nouveaumdp123", "nouveaumdp123")

    assert alice.failed_login_count == 0
    assert alice.locked_until is None
    user = authenticate(db_session, "Alice", "nouveaumdp123", role="member")
    assert user.id == alice.id


def test_reset_password_refuse_sur_id_admin(db_session, admin):
    with pytest.raises(MemberNotFoundError):
        reset_password(db_session, admin.id, "nouveaumdp123", "nouveaumdp123")


def test_reset_password_refuse_sur_id_inconnu(db_session):
    with pytest.raises(MemberNotFoundError):
        reset_password(db_session, 9999, "nouveaumdp123", "nouveaumdp123")


def test_unlock_member_remet_le_compteur_et_le_blocage_a_zero(db_session, alice):
    alice.failed_login_count = MAX_FAILED_ATTEMPTS
    alice.locked_until = datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=15)
    db_session.commit()

    unlock_member(db_session, alice.id)

    assert alice.failed_login_count == 0
    assert alice.locked_until is None


def test_unlock_member_permet_une_connexion_immediate(db_session, alice):
    alice.failed_login_count = MAX_FAILED_ATTEMPTS
    alice.locked_until = datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=15)
    db_session.commit()

    unlock_member(db_session, alice.id)

    user = authenticate(db_session, "Alice", "password123", role="member")
    assert user.id == alice.id


def test_unlock_member_sans_effet_si_compte_non_bloque(db_session, alice):
    membre = unlock_member(db_session, alice.id)

    assert membre.failed_login_count == 0
    assert membre.locked_until is None


def test_unlock_member_refuse_sur_id_admin(db_session, admin):
    with pytest.raises(MemberNotFoundError):
        unlock_member(db_session, admin.id)
