from app.models import Gift


def test_us11_formulaire_affiche_pour_membre_connecte(client, alice, login_as):
    login_as(client, alice)

    response = client.get("/cadeaux/nouveau")

    assert response.status_code == 200
    assert "Ajouter un cadeau" in response.text


def test_us11_sans_session_redirige_vers_login(client):
    response = client.get("/cadeaux/nouveau", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_us11_creation_minimale_redirige(client, alice, login_as, extract_csrf_token, db_session):
    login_as(client, alice)
    page = client.get("/cadeaux/nouveau")
    token = extract_csrf_token(page.text)

    response = client.post(
        "/cadeaux/nouveau",
        data={"name": "Vélo", "csrf_token": token},
        follow_redirects=False,
    )

    assert response.status_code == 303
    cadeau = db_session.query(Gift).filter_by(name="Vélo").one()
    assert cadeau.author_id == alice.id
    assert cadeau.recipient_id == alice.id


def test_us11_nom_vide_affiche_erreur(client, alice, login_as, extract_csrf_token):
    login_as(client, alice)
    page = client.get("/cadeaux/nouveau")
    token = extract_csrf_token(page.text)

    response = client.post("/cadeaux/nouveau", data={"name": "   ", "csrf_token": token})

    assert response.status_code == 400


def test_us11_destinataire_forge_est_ignore(
    client, alice, bob, login_as, extract_csrf_token, db_session
):
    login_as(client, alice)
    page = client.get("/cadeaux/nouveau")
    token = extract_csrf_token(page.text)

    client.post(
        "/cadeaux/nouveau",
        data={"name": "Jeu", "recipient_id": str(bob.id), "csrf_token": token},
    )

    cadeau = db_session.query(Gift).filter_by(name="Jeu").one()
    assert cadeau.recipient_id == alice.id
