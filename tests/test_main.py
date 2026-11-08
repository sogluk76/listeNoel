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


def test_media_sert_un_fichier_existant(client, make_image_bytes):
    from app.services.images import save_profile_photo

    chemin = save_profile_photo(make_image_bytes("PNG"))

    response = client.get(f"/media/{chemin}")

    assert response.status_code == 200


def test_media_404_si_fichier_absent(client):
    response = client.get("/media/inexistant.png")

    assert response.status_code == 404


def test_media_refuse_le_path_traversal(client):
    response = client.get("/media/..%2F..%2Fpyproject.toml")

    assert response.status_code == 404
