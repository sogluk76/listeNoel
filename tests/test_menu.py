"""Menu des applications : page d'arrivée après la connexion (RG-58)."""

from tests.conftest import PASSWORD


def test_rg58_connexion_arrive_sur_le_menu(anonymous, alice):
    response = anonymous.post("/login", data={"user_id": alice.id, "password": PASSWORD})
    assert response.headers["location"] == "/"
    html = anonymous.get("/").text
    assert "Bonjour Alice" in html
    assert 'class="app-tile" href="/noel"' in html


def test_rg58_la_liste_de_noel_est_sur_noel(login, alice, bob):
    html = login(alice).get("/noel").text
    assert "Liste de Noël" in html and f'href="/personnes/{bob.id}"' in html
    assert 'href="/">' in html  # retour au menu


def test_rg58_en_tete_commun_sur_le_menu(login, alice):
    html = login(alice).get("/").text
    assert "app-header__bell" in html and 'id="msg-dock"' in html
    assert "La Famille" in html


def test_rg58_retour_de_la_liste_d_une_personne_vers_noel(login, alice):
    html = login(alice).get(f"/personnes/{alice.id}").text
    assert 'class="back-link" href="/noel"' in html


def test_rg58_menu_et_noel_reserves_aux_membres(anonymous, login, admin):
    for path in ("/", "/noel"):
        assert anonymous.get(path).headers["location"] == "/login"
        assert login(admin).get(path).status_code == 403
