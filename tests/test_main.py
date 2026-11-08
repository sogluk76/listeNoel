def test_accueil_anonyme_redirige_vers_login(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_accueil_admin_connecte_refuse(client, admin, login_as):
    login_as(client, admin)

    response = client.get("/")

    assert response.status_code == 403


def test_accueil_membre_connecte_repond_200(client, alice, login_as):
    login_as(client, alice)

    response = client.get("/")

    assert response.status_code == 200


def test_page_accueil_charge_htmx(client, alice, login_as):
    login_as(client, alice)

    response = client.get("/")

    assert "static/js/htmx.min.js" in response.text


def test_page_accueil_porte_le_jeton_csrf_en_en_tete_htmx(client, alice, login_as):
    login_as(client, alice)

    response = client.get("/")

    assert "X-CSRF-Token" in response.text
