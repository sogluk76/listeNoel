"""US-01 à US-04 : connexion, déconnexion, blocage, séparation membre / admin."""

from datetime import timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.models import utcnow
from tests.conftest import PASSWORD, csrf_of


def test_us01_liste_deroulante_membres_actifs_tries_sans_admin(anonymous, db, bob, alice, admin):
    chloe_inactive = bob.__class__(first_name="Zoé", password_hash="x", is_active=False)
    db.add(chloe_inactive)
    db.commit()
    html = anonymous.get("/login").text
    assert html.index(">Alice<") < html.index(">Bob<")
    assert "admin" not in html.split("<select")[1].split("</select>")[0]
    assert "Zoé" not in html


def test_us01_avatar_placeholder_avec_initiales(anonymous, alice):
    html = anonymous.get(f"/login/avatar?user_id={alice.id}").text
    assert "avatar--xl" in html and ">A<" in html


def test_us01_connexion_correcte_redirige_et_ouvre_session_30_jours(anonymous, alice):
    response = anonymous.post("/login", data={"user_id": alice.id, "password": PASSWORD})
    assert response.status_code == 303 and response.headers["location"] == "/"
    assert "Max-Age=2592000" in response.headers["set-cookie"]
    assert anonymous.get("/").status_code == 200


def test_us01_mauvais_mot_de_passe_message_generique(anonymous, alice):
    response = anonymous.post("/login", data={"user_id": alice.id, "password": "faux"})
    assert response.status_code == 401
    assert "Mot de passe incorrect" in response.text


def test_us01_compte_inexistant_meme_message(anonymous, alice):
    response = anonymous.post("/login", data={"user_id": 9999, "password": PASSWORD})
    assert response.status_code == 401
    assert "Mot de passe incorrect" in response.text


def test_us01_compte_desactive_ne_peut_pas_se_connecter(anonymous, db, alice):
    alice.is_active = False
    db.commit()
    response = anonymous.post("/login", data={"user_id": alice.id, "password": PASSWORD})
    assert response.status_code == 401


def test_us01_page_membre_sans_session_redirige_vers_login(anonymous):
    for path in ("/", "/profil", "/personnes/1", "/cadeaux/1", "/cadeaux/nouveau"):
        response = anonymous.get(path)
        assert response.status_code == 303 and response.headers["location"] == "/login"


def test_us01_membre_deja_connecte_redirige_vers_accueil(login, alice):
    response = login(alice).get("/login")
    assert response.status_code == 303 and response.headers["location"] == "/"


def test_csrf_post_sans_jeton_refuse(db, alice):
    client = TestClient(app, follow_redirects=False)
    client.get("/login")
    response = client.post("/login", data={"user_id": alice.id, "password": PASSWORD})
    assert response.status_code == 403


def test_csrf_jeton_en_champ_cache_accepte(db, alice):
    client = TestClient(app, follow_redirects=False)
    token = csrf_of(client)
    response = client.post(
        "/login", data={"user_id": alice.id, "password": PASSWORD, "csrf_token": token}
    )
    assert response.status_code == 303


def test_us02_deconnexion(login, alice):
    client = login(alice)
    assert client.get("/logout").status_code == 405  # un GET ne déconnecte pas
    assert client.get("/").status_code == 200
    response = client.post("/logout")
    assert response.status_code == 303 and response.headers["location"] == "/login"
    assert client.get("/").headers["location"] == "/login"


def test_us03_quatre_echecs_puis_succes(anonymous, db, alice):
    for _ in range(4):
        anonymous.post("/login", data={"user_id": alice.id, "password": "faux"})
    response = anonymous.post("/login", data={"user_id": alice.id, "password": PASSWORD})
    assert response.status_code == 303
    db.refresh(alice)
    assert alice.failed_login_count == 0


def test_us03_cinq_echecs_bloquent_meme_le_bon_mot_de_passe(anonymous, db, alice, bob):
    for _ in range(5):
        response = anonymous.post("/login", data={"user_id": alice.id, "password": "faux"})
    assert "temporairement bloqué" in response.text
    response = anonymous.post("/login", data={"user_id": alice.id, "password": PASSWORD})
    assert response.status_code == 401 and "temporairement bloqué" in response.text
    # Le blocage d'un compte n'affecte pas les autres
    assert (
        anonymous.post("/login", data={"user_id": bob.id, "password": PASSWORD}).status_code == 303
    )


def test_us03_apres_expiration_du_blocage(anonymous, db, alice):
    alice.failed_login_count = 5
    alice.locked_until = utcnow() - timedelta(minutes=1)
    db.commit()
    response = anonymous.post("/login", data={"user_id": alice.id, "password": PASSWORD})
    assert response.status_code == 303


def test_us03_duree_du_blocage_15_minutes(anonymous, db, alice):
    for _ in range(5):
        anonymous.post("/login", data={"user_id": alice.id, "password": "faux"})
    db.refresh(alice)
    remaining = alice.locked_until - utcnow()
    assert timedelta(minutes=14) < remaining <= timedelta(minutes=15)


def test_us04_connexion_admin(login, admin):
    client = login(admin)
    assert client.get("/admin").status_code == 200


def test_us04_membre_ne_peut_pas_se_connecter_par_admin_login(anonymous, alice):
    response = anonymous.post("/admin/login", data={"name": "Alice", "password": PASSWORD})
    assert response.status_code == 401


def test_us04_admin_ne_peut_pas_se_connecter_par_login_membre(anonymous, admin):
    response = anonymous.post("/login", data={"user_id": admin.id, "password": PASSWORD})
    assert response.status_code == 401


def test_us04_admin_refuse_sur_les_ecrans_membres(login, admin, alice):
    client = login(admin)
    for path in ("/", f"/personnes/{alice.id}", "/profil", "/cadeaux/nouveau"):
        assert client.get(path).status_code == 403


def test_us04_membre_refuse_sur_le_panel_admin(login, alice):
    client = login(alice)
    for path in ("/admin", "/admin/cadeaux", "/admin/cloture", "/admin/membres/nouveau"):
        assert client.get(path).status_code == 403


def test_us04_admin_sans_session_redirige_vers_admin_login(anonymous):
    response = anonymous.get("/admin")
    assert response.status_code == 303 and response.headers["location"] == "/admin/login"
