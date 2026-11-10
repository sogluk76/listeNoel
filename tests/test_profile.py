"""US-23 et US-24 : photo de profil et mot de passe."""

from app.config import settings
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
