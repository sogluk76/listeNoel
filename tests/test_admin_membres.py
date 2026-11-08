from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.models import User
from app.security import verify_password
from app.services.users import MAX_FAILED_ATTEMPTS, AuthenticationError, authenticate


def _creer_membre(client, extract_csrf_token, photo=None, **champs):
    page = client.get("/admin/membres/nouveau")
    token = extract_csrf_token(page.text)
    data = {
        "first_name": "Denise",
        "password": "motdepasse123",
        "password_confirmation": "motdepasse123",
        "csrf_token": token,
        **champs,
    }
    files = {"photo": photo} if photo is not None else None
    return client.post("/admin/membres/nouveau", data=data, files=files)


def _modifier_membre(
    client,
    extract_csrf_token,
    member_id,
    first_name,
    active=True,
    remove_photo=False,
    photo=None,
    follow_redirects=True,
):
    page = client.get(f"/admin/membres/{member_id}/modifier")
    token = extract_csrf_token(page.text)
    data = {"first_name": first_name, "csrf_token": token}
    if active:
        data["active"] = "true"
    if remove_photo:
        data["remove_photo"] = "true"
    files = {"photo": photo} if photo is not None else None
    return client.post(
        f"/admin/membres/{member_id}/modifier",
        data=data,
        files=files,
        follow_redirects=follow_redirects,
    )


def _reinitialiser_mot_de_passe(
    client, extract_csrf_token, member_id, password, confirmation=None, follow_redirects=False
):
    page = client.get(f"/admin/membres/{member_id}/modifier")
    token = extract_csrf_token(page.text)
    data = {
        "password": password,
        "password_confirmation": confirmation if confirmation is not None else password,
        "csrf_token": token,
    }
    return client.post(
        f"/admin/membres/{member_id}/mot-de-passe", data=data, follow_redirects=follow_redirects
    )


def _debloquer(client, extract_csrf_token, member_id, follow_redirects=False):
    page = client.get(f"/admin/membres/{member_id}/modifier")
    token = extract_csrf_token(page.text)
    return client.post(
        f"/admin/membres/{member_id}/debloquer",
        data={"csrf_token": token},
        follow_redirects=follow_redirects,
    )


def test_formulaire_reserve_a_admin(client):
    response = client.get("/admin/membres/nouveau", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/login"


def test_formulaire_refuse_un_membre(client, alice, login_as):
    login_as(client, alice)

    response = client.get("/admin/membres/nouveau")

    assert response.status_code == 403


def test_creation_reussie_cree_un_membre_actif(
    client, admin, login_as, db_session, extract_csrf_token
):
    login_as(client, admin)

    response = _creer_membre(client, extract_csrf_token)

    assert response.status_code == 200
    assert "créé" in response.text
    membre = db_session.query(User).filter_by(first_name="Denise").one()
    assert membre.role == "member"
    assert membre.is_active is True


def test_mot_de_passe_stocke_hache(client, admin, login_as, db_session, extract_csrf_token):
    login_as(client, admin)

    _creer_membre(client, extract_csrf_token)

    membre = db_session.query(User).filter_by(first_name="Denise").one()
    assert membre.password_hash != "motdepasse123"
    assert verify_password("motdepasse123", membre.password_hash)


def test_prenom_deja_pris_meme_casse_differente_refuse(
    client, admin, alice, login_as, extract_csrf_token
):
    login_as(client, admin)

    response = _creer_membre(client, extract_csrf_token, first_name="alice")

    assert response.status_code == 400
    assert "déjà utilisé" in response.text


def test_confirmation_differente_refusee(client, admin, login_as, extract_csrf_token):
    login_as(client, admin)

    response = _creer_membre(client, extract_csrf_token, password_confirmation="autre-mdp")

    assert response.status_code == 400
    assert "ne correspondent pas" in response.text


def test_mot_de_passe_trop_court_refuse(client, admin, login_as, extract_csrf_token):
    login_as(client, admin)

    response = _creer_membre(
        client, extract_csrf_token, password="court1", password_confirmation="court1"
    )

    assert response.status_code == 400
    assert "8 caractères" in response.text


def test_photo_valide_enregistree(
    client, admin, login_as, db_session, extract_csrf_token, make_image_bytes
):
    login_as(client, admin)

    response = _creer_membre(
        client, extract_csrf_token, photo=("photo.png", make_image_bytes("PNG"), "image/png")
    )

    assert response.status_code == 200
    membre = db_session.query(User).filter_by(first_name="Denise").one()
    assert membre.photo_path is not None
    assert (settings.media_dir / membre.photo_path).exists()


def test_fichier_non_image_refuse_a_la_creation(client, admin, login_as, extract_csrf_token):
    login_as(client, admin)

    response = _creer_membre(
        client, extract_csrf_token, photo=("photo.jpg", b"pas une image", "image/jpeg")
    )

    assert response.status_code == 400
    assert "pas une image valide" in response.text


def test_sans_photo_photo_path_reste_none(client, admin, login_as, db_session, extract_csrf_token):
    login_as(client, admin)

    _creer_membre(client, extract_csrf_token)

    membre = db_session.query(User).filter_by(first_name="Denise").one()
    assert membre.photo_path is None


def test_liste_reservee_a_admin(client):
    response = client.get("/admin/membres", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/login"


def test_liste_refuse_un_membre(client, alice, login_as):
    login_as(client, alice)

    response = client.get("/admin/membres")

    assert response.status_code == 403


def test_liste_affiche_les_membres_actifs_et_inactifs(client, admin, alice, bob, login_as):
    bob.is_active = False
    login_as(client, admin)

    response = client.get("/admin/membres")

    assert "Alice" in response.text
    assert "Bob" in response.text


def test_liste_exclut_admin(client, admin, alice, login_as):
    login_as(client, admin)

    response = client.get("/admin/membres")

    assert "Admin" not in response.text


def test_formulaire_modifier_reserve_a_admin(client, alice, login_as):
    login_as(client, alice)

    response = client.get(f"/admin/membres/{alice.id}/modifier")

    assert response.status_code == 403


def test_formulaire_modifier_id_inconnu_renvoie_404(client, admin, login_as):
    login_as(client, admin)

    response = client.get("/admin/membres/9999/modifier")

    assert response.status_code == 404


def test_formulaire_modifier_id_admin_renvoie_404(client, admin, login_as):
    login_as(client, admin)

    response = client.get(f"/admin/membres/{admin.id}/modifier")

    assert response.status_code == 404


def test_modifier_change_le_prenom(client, admin, alice, login_as, db_session, extract_csrf_token):
    login_as(client, admin)

    response = _modifier_membre(
        client, extract_csrf_token, alice.id, "Alicia", follow_redirects=False
    )

    assert response.status_code == 303
    membre = db_session.get(User, alice.id)
    assert membre.first_name == "Alicia"


def test_modifier_prenom_deja_pris_refuse(client, admin, alice, bob, login_as, extract_csrf_token):
    login_as(client, admin)

    response = _modifier_membre(client, extract_csrf_token, bob.id, "alice")

    assert response.status_code == 400
    assert "déjà utilisé" in response.text


def test_modifier_id_admin_refuse_via_post(client, admin, login_as, extract_csrf_token):
    login_as(client, admin)
    # Le GET sur cet id renvoie déjà 404 : on récupère le jeton CSRF ailleurs pour vérifier
    # que le POST refuse aussi, indépendamment du garde-fou du formulaire.
    token = extract_csrf_token(client.get("/admin/membres").text)

    response = client.post(
        f"/admin/membres/{admin.id}/modifier",
        data={"first_name": "Admin", "csrf_token": token, "active": "true"},
    )

    assert response.status_code == 404


def test_session_active_refusee_apres_desactivation(
    client, admin, alice, login_as, extract_csrf_token
):
    client_alice = TestClient(app)
    login_as(client_alice, alice)
    assert client_alice.get("/").status_code == 200

    login_as(client, admin)
    _modifier_membre(client, extract_csrf_token, alice.id, "Alice", active=False)

    response = client_alice.get("/", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_reactivation_retrouve_lacces(client, admin, alice, login_as, extract_csrf_token):
    alice.is_active = False
    login_as(client, admin)

    _modifier_membre(client, extract_csrf_token, alice.id, "Alice", active=True)

    client_alice = TestClient(app)
    login_as(client_alice, alice)
    assert client_alice.get("/").status_code == 200


def test_modifier_remplace_la_photo_et_supprime_lancienne(
    client, admin, alice, login_as, db_session, extract_csrf_token, make_image_bytes
):
    login_as(client, admin)
    _modifier_membre(
        client,
        extract_csrf_token,
        alice.id,
        "Alice",
        photo=("photo.png", make_image_bytes("PNG"), "image/png"),
    )
    membre = db_session.get(User, alice.id)
    ancien_chemin = settings.media_dir / membre.photo_path

    _modifier_membre(
        client,
        extract_csrf_token,
        alice.id,
        "Alice",
        photo=("photo2.png", make_image_bytes("PNG"), "image/png"),
    )

    db_session.refresh(membre)
    assert not ancien_chemin.exists()
    assert (settings.media_dir / membre.photo_path).exists()


def test_modifier_supprime_la_photo_via_case_a_cocher(
    client, admin, alice, login_as, db_session, extract_csrf_token, make_image_bytes
):
    login_as(client, admin)
    _modifier_membre(
        client,
        extract_csrf_token,
        alice.id,
        "Alice",
        photo=("photo.png", make_image_bytes("PNG"), "image/png"),
    )

    _modifier_membre(client, extract_csrf_token, alice.id, "Alice", remove_photo=True)

    membre = db_session.get(User, alice.id)
    db_session.refresh(membre)
    assert membre.photo_path is None


def test_reinitialiser_mot_de_passe_change_le_mot_de_passe(
    client, admin, alice, login_as, db_session, extract_csrf_token
):
    login_as(client, admin)

    response = _reinitialiser_mot_de_passe(client, extract_csrf_token, alice.id, "nouveaumdp123")

    assert response.status_code == 303
    with pytest.raises(AuthenticationError):
        authenticate(db_session, "Alice", "password123", role="member")
    user = authenticate(db_session, "Alice", "nouveaumdp123", role="member")
    assert user.id == alice.id


def test_reinitialiser_mot_de_passe_refuse_confirmation_differente(
    client, admin, alice, login_as, extract_csrf_token
):
    login_as(client, admin)

    response = _reinitialiser_mot_de_passe(
        client, extract_csrf_token, alice.id, "nouveaumdp123", confirmation="autre-mdp"
    )

    assert response.status_code == 400
    assert "ne correspondent pas" in response.text


def test_reinitialiser_mot_de_passe_refuse_trop_court(
    client, admin, alice, login_as, extract_csrf_token
):
    login_as(client, admin)

    response = _reinitialiser_mot_de_passe(client, extract_csrf_token, alice.id, "court1")

    assert response.status_code == 400
    assert "8 caractères" in response.text


def test_reinitialiser_mot_de_passe_leve_le_blocage(
    client, admin, alice, login_as, db_session, extract_csrf_token
):
    alice.failed_login_count = MAX_FAILED_ATTEMPTS
    alice.locked_until = datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=15)
    db_session.commit()
    login_as(client, admin)

    _reinitialiser_mot_de_passe(client, extract_csrf_token, alice.id, "nouveaumdp123")

    user = authenticate(db_session, "Alice", "nouveaumdp123", role="member")
    assert user.id == alice.id


def test_reinitialiser_mot_de_passe_refuse_sur_id_admin(
    client, admin, login_as, extract_csrf_token
):
    login_as(client, admin)
    token = extract_csrf_token(client.get("/admin/membres").text)

    response = client.post(
        f"/admin/membres/{admin.id}/mot-de-passe",
        data={
            "password": "nouveaumdp123",
            "password_confirmation": "nouveaumdp123",
            "csrf_token": token,
        },
    )

    assert response.status_code == 404


def test_bouton_debloquer_absent_si_compte_non_bloque(client, admin, alice, login_as):
    login_as(client, admin)

    response = client.get(f"/admin/membres/{alice.id}/modifier")

    assert "Débloquer" not in response.text


def test_bouton_debloquer_visible_si_compte_bloque(client, admin, alice, login_as, db_session):
    alice.failed_login_count = MAX_FAILED_ATTEMPTS
    alice.locked_until = datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=15)
    db_session.commit()
    login_as(client, admin)

    response = client.get(f"/admin/membres/{alice.id}/modifier")

    assert "Débloquer" in response.text


def test_debloquer_remet_le_compteur_et_permet_une_connexion_immediate(
    client, admin, alice, login_as, db_session, extract_csrf_token
):
    alice.failed_login_count = MAX_FAILED_ATTEMPTS
    alice.locked_until = datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=15)
    db_session.commit()
    login_as(client, admin)

    response = _debloquer(client, extract_csrf_token, alice.id)

    assert response.status_code == 303
    user = authenticate(db_session, "Alice", "password123", role="member")
    assert user.id == alice.id


def test_debloquer_refuse_sur_id_admin(client, admin, login_as, extract_csrf_token):
    login_as(client, admin)
    token = extract_csrf_token(client.get("/admin/membres").text)

    response = client.post(f"/admin/membres/{admin.id}/debloquer", data={"csrf_token": token})

    assert response.status_code == 404
