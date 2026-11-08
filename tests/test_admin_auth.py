def test_connexion_admin_correcte_redirige_vers_admin_et_ouvre_la_session(
    client, admin, extract_csrf_token
):
    page = client.get("/admin/login")
    token = extract_csrf_token(page.text)

    response = client.post(
        "/admin/login",
        data={"first_name": "Admin", "password": "password123", "csrf_token": token},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/admin"

    tableau_de_bord = client.get("/admin")
    assert tableau_de_bord.status_code == 200


def test_connexion_admin_mauvais_mot_de_passe_message_generique_sans_redirection(
    client, admin, extract_csrf_token
):
    page = client.get("/admin/login")
    token = extract_csrf_token(page.text)

    response = client.post(
        "/admin/login",
        data={"first_name": "Admin", "password": "mauvais-mot-de-passe", "csrf_token": token},
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert "Mot de passe incorrect" in response.text
    assert "location" not in response.headers


def test_membre_ne_peut_pas_se_connecter_via_admin_login(client, alice, extract_csrf_token):
    page = client.get("/admin/login")
    token = extract_csrf_token(page.text)

    response = client.post(
        "/admin/login",
        data={"first_name": "Alice", "password": "password123", "csrf_token": token},
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert "Mot de passe incorrect" in response.text
    assert "location" not in response.headers


def test_admin_sans_session_redirige_vers_admin_login(client):
    response = client.get("/admin", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/login"


def test_admin_avec_session_membre_refuse(client, alice, login_as):
    login_as(client, alice)

    response = client.get("/admin")

    assert response.status_code == 403


def test_admin_avec_session_admin_accepte(client, admin, login_as):
    login_as(client, admin)

    response = client.get("/admin")

    assert response.status_code == 200
