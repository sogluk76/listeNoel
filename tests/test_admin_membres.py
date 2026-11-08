from app.models import User
from app.security import verify_password


def _creer_membre(client, extract_csrf_token, **champs):
    page = client.get("/admin/membres/nouveau")
    token = extract_csrf_token(page.text)
    data = {
        "first_name": "Denise",
        "password": "motdepasse123",
        "password_confirmation": "motdepasse123",
        "csrf_token": token,
        **champs,
    }
    return client.post("/admin/membres/nouveau", data=data)


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
