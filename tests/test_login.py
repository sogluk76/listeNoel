from app.services.users import update_member


def test_page_sans_session_affiche_le_formulaire(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert "Choisis ton prénom" in response.text


def test_dropdown_ne_contient_que_les_membres_actifs_sans_admin(
    client, alice, bob, admin, db_session
):
    bob.is_active = False
    db_session.commit()

    response = client.get("/login")

    assert "Alice" in response.text
    assert "Bob" not in response.text
    assert "Admin" not in response.text


def test_dropdown_triee_par_ordre_alphabetique(client, chloe, alice, bob):
    response = client.get("/login")

    position_alice = response.text.index("Alice")
    position_bob = response.text.index("Bob")
    position_chloe = response.text.index("Chloé")
    assert position_alice < position_bob < position_chloe


def test_membre_deja_connecte_redirige_vers_accueil(client, alice, login_as):
    login_as(client, alice)

    response = client.get("/login", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/"


def test_connexion_correcte_redirige_et_ouvre_la_session(client, alice, extract_csrf_token):
    page = client.get("/login")
    token = extract_csrf_token(page.text)

    response = client.post(
        "/login",
        data={"first_name": "Alice", "password": "password123", "csrf_token": token},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/"

    accueil = client.get("/")
    assert accueil.status_code == 200


def test_mot_de_passe_faux_message_generique(client, alice, extract_csrf_token):
    page = client.get("/login")
    token = extract_csrf_token(page.text)

    response = client.post(
        "/login",
        data={"first_name": "Alice", "password": "mauvais-mot-de-passe", "csrf_token": token},
    )

    assert response.status_code == 400
    assert "Mot de passe incorrect" in response.text


def test_compte_desactive_ne_peut_pas_se_connecter(
    client, alice, login_as, db_session, extract_csrf_token
):
    alice.is_active = False
    db_session.commit()
    page = client.get("/login")
    token = extract_csrf_token(page.text)

    response = client.post(
        "/login",
        data={"first_name": "Alice", "password": "password123", "csrf_token": token},
    )

    assert response.status_code == 400
    assert "Mot de passe incorrect" in response.text


def test_succes_remet_le_compteur_dechecs_a_zero(client, alice, db_session, extract_csrf_token):
    alice.failed_login_count = 3
    db_session.commit()
    page = client.get("/login")
    token = extract_csrf_token(page.text)

    client.post(
        "/login",
        data={"first_name": "Alice", "password": "password123", "csrf_token": token},
    )

    db_session.refresh(alice)
    assert alice.failed_login_count == 0


def test_page_membre_sans_session_redirige_vers_login(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_photo_fragment_affiche_la_photo_du_membre(client, alice, db_session, make_image_bytes):
    membre = update_member(
        db_session, alice.id, "Alice", is_active=True, photo=make_image_bytes("PNG")
    )

    response = client.get("/login/photo", params={"first_name": "Alice"})

    assert response.status_code == 200
    assert f"/media/{membre.photo_path}" in response.text


def test_photo_fragment_affiche_les_initiales_sans_photo(client, alice):
    response = client.get("/login/photo", params={"first_name": "Alice"})

    assert response.status_code == 200
    assert "A" in response.text
    assert "img" not in response.text


def test_photo_fragment_prenom_inconnu_et_inactif_renvoient_le_meme_placeholder_vide(
    client, alice, db_session
):
    alice.is_active = False
    db_session.commit()

    reponse_inactive = client.get("/login/photo", params={"first_name": "Alice"})
    reponse_inconnue = client.get("/login/photo", params={"first_name": "Zorro"})

    assert reponse_inactive.status_code == 200
    assert reponse_inconnue.status_code == 200
    assert reponse_inactive.text == reponse_inconnue.text
    assert "A" not in reponse_inactive.text
    assert "img" not in reponse_inactive.text


def test_deconnexion_detruit_la_session_et_redirige(client, alice, login_as, extract_csrf_token):
    login_as(client, alice)
    page = client.get("/")
    token = extract_csrf_token(page.text)

    response = client.post("/logout", data={"csrf_token": token}, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"

    accueil = client.get("/", follow_redirects=False)
    assert accueil.status_code == 303
    assert accueil.headers["location"] == "/login"


def test_deconnexion_vide_le_cookie_de_session(client, alice, login_as, extract_csrf_token):
    login_as(client, alice)
    page = client.get("/")
    token = extract_csrf_token(page.text)

    response = client.post("/logout", data={"csrf_token": token}, follow_redirects=False)

    assert "expires=Thu, 01 Jan 1970" in response.headers["set-cookie"]


def test_get_logout_ne_deconnecte_pas(client, alice, login_as):
    login_as(client, alice)

    response = client.get("/logout")

    assert response.status_code == 405
    assert client.get("/").status_code == 200


def test_deconnexion_sans_jeton_csrf_refusee(client, alice, login_as):
    login_as(client, alice)

    response = client.post("/logout")

    assert response.status_code == 403
    assert client.get("/").status_code == 200


def test_admin_ne_peut_pas_se_deconnecter_via_logout_membre(
    client, admin, login_as, extract_csrf_token
):
    login_as(client, admin)
    page = client.get("/admin")
    token = extract_csrf_token(page.text)

    response = client.post("/logout", data={"csrf_token": token})

    assert response.status_code == 403
