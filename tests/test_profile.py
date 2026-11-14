"""US-23, US-24 et US-36 : photo de profil, mot de passe et thème."""

from app.config import settings
from app.services import users as users_service
from tests.conftest import PASSWORD, png_bytes


def test_us23_changer_puis_supprimer_ma_photo(login, db, alice):
    client = login(alice)
    response = client.post("/profil/photo", files={"photo": ("moi.png", png_bytes(), "image/png")})
    assert response.status_code == 303
    db.refresh(alice)
    first = settings.media_dir / alice.photo_path
    assert first.is_file()
    # La photo apparaît dans la liste des personnes et à la connexion
    assert alice.photo_path in client.get("/").text
    assert alice.photo_path in client.get(f"/login/avatar?user_id={alice.id}").text

    client.post("/profil/photo", files={"photo": ("moi2.png", png_bytes((40, 40)), "image/png")})
    db.refresh(alice)
    assert not first.exists()  # l'ancienne image est supprimée du disque

    second = settings.media_dir / alice.photo_path
    client.post("/profil/photo/supprimer")
    db.refresh(alice)
    assert alice.photo_path is None and not second.exists()
    assert "avatar--c" in client.get("/profil").text  # placeholder


def test_us23_fichier_invalide_refuse(login, db, alice):
    client = login(alice)
    client.post("/profil/photo", files={"photo": ("x.png", b"pas une image", "image/png")})
    db.refresh(alice)
    assert alice.photo_path is None
    assert "image valide" in client.get("/profil").text


def test_us24_changer_mon_mot_de_passe(login, anonymous, db, alice):
    client = login(alice)
    data = {
        "current_password": PASSWORD,
        "new_password": "nouveau-mdp",
        "confirmation": "nouveau-mdp",
    }

    wrong = client.post("/profil/mot-de-passe", data={**data, "current_password": "faux"})
    assert wrong.status_code == 422 and "actuel est incorrect" in wrong.text
    short = client.post(
        "/profil/mot-de-passe", data={**data, "new_password": "court", "confirmation": "court"}
    )
    assert short.status_code == 422 and "au moins 8" in short.text
    mismatch = client.post("/profil/mot-de-passe", data={**data, "confirmation": "autre-chose"})
    assert mismatch.status_code == 422 and "confirmation" in mismatch.text

    assert client.post("/profil/mot-de-passe", data=data).status_code == 303
    assert client.get("/profil").status_code == 200  # la session reste ouverte
    old = anonymous.post("/login", data={"user_id": alice.id, "password": PASSWORD})
    assert old.status_code == 401
    new = anonymous.post("/login", data={"user_id": alice.id, "password": "nouveau-mdp"})
    assert new.status_code == 303


# --- US-36 : thème d'affichage (RG-56) ----------------------------------------


def _theme(client, path: str = "/") -> str | None:
    """Thème posé sur la balise <html>, ou None pour le thème automatique."""
    import re

    match = re.search(r'<html lang="fr"(?: data-theme="([^"]+)")?>', client.get(path).text)
    assert match, "balise <html> introuvable"
    return match.group(1)


def test_us36_theme_automatique_par_defaut(login, alice):
    client = login(alice)
    assert alice.theme == "auto"
    assert _theme(client) is None  # sans attribut : clair ou sombre selon l'appareil
    html = client.get("/profil").text
    for key in users_service.THEMES:
        assert f'name="theme" value="{key}"' in html
    assert 'name="theme" value="auto" checked' in html


def test_us36_changer_de_theme_s_applique_partout(login, db, alice, bob):
    client = login(alice)
    response = client.post("/profil/theme", data={"theme": "minuit"})
    assert response.status_code == 303 and response.headers["location"] == "/profil#apparence"
    db.refresh(alice)
    assert alice.theme == "minuit"
    for path in ("/", "/profil", "/notifications", "/messages", f"/personnes/{bob.id}"):
        assert _theme(client, path) == "minuit", path
    assert 'name="theme" value="minuit" checked' in client.get("/profil").text
    assert _theme(login(alice)) == "minuit"  # le thème suit le compte, pas l'appareil
    assert _theme(login(bob)) is None  # chacun le sien
    client.post("/profil/theme", data={"theme": "auto"})
    assert _theme(client) is None


def test_us36_tous_les_themes_existent_dans_les_tokens(login, alice):
    from pathlib import Path

    css = Path("app/static/css/tokens.css").read_text(encoding="utf-8")
    client = login(alice)
    for key in users_service.THEMES:
        assert client.post("/profil/theme", data={"theme": key}).status_code == 303
        if key != "auto":
            assert f'[data-theme="{key}"]' in css, key


def test_us36_theme_inconnu_refuse(login, db, alice):
    client = login(alice)
    client.post("/profil/theme", data={"theme": "sombre"})
    for bad in ("", "rose-fluo", '"><script>'):
        assert client.post("/profil/theme", data={"theme": bad}).status_code == 303
        db.refresh(alice)
        assert alice.theme == "sombre"
    assert "Ce thème n" in client.get("/profil").text  # message d'erreur affiché


def test_us36_reponse_htmx_et_acces(login, anonymous, db, admin, alice):
    response = login(alice).post(
        "/profil/theme", data={"theme": "neige"}, headers={"HX-Request": "true"}
    )
    assert response.status_code == 200 and response.headers["HX-Refresh"] == "true"
    admin_client = login(admin)
    assert admin_client.post("/profil/theme", data={"theme": "neige"}).status_code == 403
    assert "data-theme" not in admin_client.get("/admin").text  # le panel reste sobre
    assert anonymous.post("/profil/theme", data={"theme": "neige"}).headers["location"] == "/login"
    assert "data-theme" not in anonymous.get("/login").text
