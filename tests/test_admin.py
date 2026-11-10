"""US-05 à US-09 : comptes, mots de passe, suppression de cadeaux, clôture de l'année."""

from datetime import timedelta

from sqlalchemy import select

from app.config import settings
from app.models import Comment, Gift, Notification, Reservation, User, utcnow
from app.services import users as users_service
from tests.conftest import PASSWORD, png_bytes, use_csrf

NEW = {"name": "Dorian", "password": "motdepasse2", "confirmation": "motdepasse2"}


def _member(db, name):
    db.expire_all()
    return db.scalar(select(User).where(User.first_name == name))


def test_create_admin_refuse_un_nom_deja_pris(db, alice):
    import pytest

    from app.errors import Invalid

    created = users_service.create_user(db, "chef", "motdepasse9", "motdepasse9", role="admin")
    assert created.is_admin
    with pytest.raises(Invalid):
        users_service.create_user(db, "ALICE", "motdepasse9", "motdepasse9", role="admin")


def test_us05_creer_un_compte(login, anonymous, db, admin):
    client = login(admin)
    response = client.post(
        "/admin/membres", data=NEW, files={"photo": ("d.png", png_bytes(), "image/png")}
    )
    assert response.status_code == 303
    member = _member(db, "Dorian")
    assert member.is_member and member.is_active
    assert member.password_hash.startswith("$argon2") and "motdepasse2" not in member.password_hash
    assert (settings.media_dir / member.photo_path).is_file()
    assert ">Dorian<" in anonymous.get("/login").text
    login_response = anonymous.post(
        "/login", data={"user_id": member.id, "password": "motdepasse2"}
    )
    assert login_response.status_code == 303


def test_us05_refus(login, db, admin, alice):
    client = login(admin)
    cases = [
        ({**NEW, "name": "aLiCe"}, "déjà utilisé"),
        ({**NEW, "name": "  "}, "obligatoire"),
        ({**NEW, "confirmation": "different"}, "confirmation"),
        ({**NEW, "password": "court", "confirmation": "court"}, "au moins 8"),
    ]
    for data, message in cases:
        response = client.post("/admin/membres", data=data)
        assert response.status_code == 422 and message in response.text
    response = client.post(
        "/admin/membres", data=NEW, files={"photo": ("x.png", b"pas une image", "image/png")}
    )
    assert response.status_code == 422
    assert _member(db, "Dorian") is None


def test_us06_modifier_et_desactiver(login, db, admin, alice, bob, make_gift):
    make_gift(alice, alice, "Vélo")
    client = login(admin)
    alice_client = login(alice)
    page = client.get("/admin").text
    assert "Alice" in page and "Gérer" in page and ">admin<" not in page

    dup = client.post(f"/admin/membres/{alice.id}", data={"name": "bob", "is_active": "1"})
    assert dup.status_code == 422

    client.post(f"/admin/membres/{alice.id}", data={"name": "Alicia", "is_active": "1"})
    assert "Alicia" in login(bob).get("/").text

    client.post(f"/admin/membres/{alice.id}", data={"name": "Alicia"})  # case décochée
    assert alice_client.get("/").headers["location"] == "/login"  # session invalidée
    assert "Alicia" not in login(bob).get("/").text

    client.post(f"/admin/membres/{alice.id}", data={"name": "Alicia", "is_active": "1"})
    assert "Vélo" in login(bob).get(f"/personnes/{alice.id}").text  # données retrouvées


def test_us06_admin_non_gerable_depuis_le_panel(login, admin):
    client = login(admin)
    assert client.get(f"/admin/membres/{admin.id}").status_code == 404
    assert client.post(f"/admin/membres/{admin.id}", data={"name": "x"}).status_code == 404


def test_us07_reinitialiser_et_debloquer(login, anonymous, db, admin, alice):
    alice.failed_login_count = 5
    alice.locked_until = utcnow() + timedelta(minutes=15)
    db.commit()
    client = login(admin)
    assert "Débloquer" in client.get(f"/admin/membres/{alice.id}").text

    client.post(f"/admin/membres/{alice.id}/debloquer")
    assert "Débloquer" not in client.get(f"/admin/membres/{alice.id}").text
    ok = anonymous.post("/login", data={"user_id": alice.id, "password": PASSWORD})
    assert ok.status_code == 303
    use_csrf(anonymous, "/")  # la connexion a renouvelé la session, donc le jeton

    alice.locked_until = utcnow() + timedelta(minutes=15)
    db.commit()
    client.post(
        f"/admin/membres/{alice.id}/mot-de-passe",
        data={"password": "tout-nouveau", "confirmation": "tout-nouveau"},
    )
    old = anonymous.post("/login", data={"user_id": alice.id, "password": PASSWORD})
    assert old.status_code == 401
    new = anonymous.post("/login", data={"user_id": alice.id, "password": "tout-nouveau"})
    assert new.status_code == 303  # la réinitialisation lève aussi le blocage


def _fichier_media(relative: str) -> str:
    target = settings.media_dir / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(png_bytes())
    return relative


def test_us26_supprimer_un_compte_et_toute_sa_trace(
    login, anonymous, db, admin, alice, bob, chloe, make_gift
):
    """RG-41 : le compte disparaît avec sa liste, ses suggestions, réservations et commentaires."""
    alice.photo_path = _fichier_media("avatars/alice-us26.webp")
    sa_liste = make_gift(alice, alice, "Vélo-d-Alice", image_path=_fichier_media("gifts/us26.webp"))
    sa_liste.reservations.append(Reservation(user_id=bob.id))
    sa_liste.comments.append(Comment(author_id=bob.id, content="Bob en parle"))
    suggestion_pour_alice = make_gift(bob, alice, "Idée-de-Bob-pour-Alice")
    suggestion_d_alice = make_gift(alice, bob, "Idée-d-Alice-pour-Bob")
    suggestion_d_alice.reservations.append(Reservation(user_id=chloe.id))
    archive = make_gift(alice, alice, "Archive-d-Alice", archived_year=2025)
    cadeau_de_bob = make_gift(bob, bob, "Livre-de-Bob")
    cadeau_de_bob.reservations.append(Reservation(user_id=alice.id))
    cadeau_de_bob.reservations.append(Reservation(user_id=chloe.id))
    cadeau_de_bob.comments.append(Comment(author_id=alice.id, content="Alice en parle"))
    cadeau_de_bob.comments.append(Comment(author_id=chloe.id, content="Chloé en parle"))
    cadeau_de_bob.purchased_by_id = alice.id
    cadeau_de_bob.purchased_at = utcnow()
    # Notifications : une reçue par Alice, une envoyée par Alice, une sur sa liste
    cadeau_de_bob.comments[1].notifications.append(Notification(user_id=alice.id))
    cadeau_de_bob.comments[0].notifications.append(Notification(user_id=chloe.id))
    sa_liste.comments[0].notifications.append(Notification(user_id=chloe.id))
    db.commit()
    alice_id, bob_gift_id = alice.id, cadeau_de_bob.id
    supprimes = [sa_liste.id, suggestion_pour_alice.id, suggestion_d_alice.id, archive.id]
    alice_client = login(alice)
    client = login(admin)

    page = client.get(f"/admin/membres/{alice_id}").text
    assert "Supprimer ce compte" in page
    assert "Bob en parle" not in page and "Réservé" not in page  # RG-23 : aucun secret côté admin

    response = client.post(f"/admin/membres/{alice_id}/supprimer", data={"confirm": "1"})
    assert response.status_code == 303 and response.headers["location"] == "/admin"
    db.expire_all()

    assert db.get(User, alice_id) is None
    for gift_id in supprimes:
        assert db.get(Gift, gift_id) is None, gift_id
    assert not (settings.media_dir / "avatars/alice-us26.webp").exists()
    assert not (settings.media_dir / "gifts/us26.webp").exists()

    # Ce que les autres ont fait ailleurs est intact, sans trace d'Alice
    reste = db.get(Gift, bob_gift_id)
    assert [r.user_id for r in reste.reservations] == [chloe.id]
    assert [c.content for c in reste.comments] == ["Chloé en parle"]
    assert reste.purchased_by_id is None and reste.purchased_at is None
    assert db.scalars(select(Reservation).where(Reservation.user_id == alice_id)).all() == []
    assert db.scalars(select(Comment).where(Comment.author_id == alice_id)).all() == []
    assert db.scalars(select(Notification)).all() == []
    assert db.get(User, bob.id) is not None and db.get(User, chloe.id) is not None

    # Alice ne peut plus rien faire : session refusée, absente des listes
    assert alice_client.get("/").headers["location"] == "/login"
    assert ">Alice<" not in anonymous.get("/login").text
    assert "Alice" not in client.get("/admin").text.replace("Alice supprimé", "")
    html = login(chloe).get(f"/personnes/{bob.id}").text
    assert "Livre-de-Bob" in html and "Idée-d-Alice-pour-Bob" not in html


def test_us26_sans_confirmation_rien_n_est_supprime(login, db, admin, alice, make_gift):
    gift = make_gift(alice, alice, "Vélo")
    client = login(admin)
    response = client.post(f"/admin/membres/{alice.id}/supprimer")
    assert response.headers["location"] == f"/admin/membres/{alice.id}"
    db.expire_all()
    assert db.get(User, alice.id) is not None and db.get(Gift, gift.id) is not None


def test_us26_reserve_a_l_admin_et_admin_non_supprimable(login, anonymous, db, admin, alice, bob):
    data = {"confirm": "1"}
    assert login(admin).post(f"/admin/membres/{admin.id}/supprimer", data=data).status_code == 404
    assert login(bob).post(f"/admin/membres/{alice.id}/supprimer", data=data).status_code == 403
    assert anonymous.post(f"/admin/membres/{alice.id}/supprimer", data=data).status_code != 200
    db.expire_all()
    assert db.get(User, admin.id) is not None and db.get(User, alice.id) is not None


def test_us08_liste_admin_sans_secrets_et_suppression(login, db, admin, alice, bob, make_gift):
    client = login(admin)
    client_png = login(bob)
    client_png.post(
        "/cadeaux", data={"name": "Vélo"}, files={"image": ("v.png", png_bytes(), "image/png")}
    )
    gift = db.scalar(select(Gift))
    image = settings.media_dir / gift.image_path
    gift.reservations.append(Reservation(user_id=alice.id))
    gift.comments.append(Comment(author_id=alice.id, content="SECRET-COMMENTAIRE"))
    gift.purchased_by_id = alice.id
    db.commit()

    html = client.get("/admin/cadeaux").text
    assert "Vélo" in html and "Bob" in html
    for hidden in ("SECRET", "Acheté", "Réservé", "pill"):
        assert hidden not in html, hidden

    client.post(f"/admin/cadeaux/{gift.id}/supprimer")  # sans confirmation
    assert db.scalar(select(Gift)) is not None

    client.post(f"/admin/cadeaux/{gift.id}/supprimer", data={"confirm": "1"})
    db.expire_all()
    assert db.scalar(select(Gift)) is None
    assert db.scalar(select(Comment)) is None and db.scalar(select(Reservation)) is None
    assert not image.exists()


def test_us09_cloture_de_l_annee(login, db, admin, alice, bob, make_gift):
    achete = make_gift(bob, bob, "Acheté-cadeau", purchased_by_id=alice.id)
    retire = make_gift(bob, bob, "Retiré-cadeau", removed_at=utcnow())
    reserve = make_gift(bob, bob, "Réservé-cadeau")
    reserve.reservations.append(Reservation(user_id=alice.id))
    libre = make_gift(bob, bob, "Libre-cadeau")
    db.commit()
    client = login(admin)

    page = client.get("/admin/cloture").text
    assert "<strong>2</strong>" in page
    assert "Acheté-cadeau" not in page  # un nombre seulement, aucun détail

    assert client.post("/admin/cloture", data={"year": "2026"}).status_code == 422
    db.expire_all()
    assert achete.archived_year is None

    assert client.post("/admin/cloture", data={"year": "2026", "confirm": "1"}).status_code == 303
    for g in (achete, retire, reserve, libre):
        db.refresh(g)
    assert achete.archived_year == 2026 and retire.archived_year == 2026
    assert reserve.archived_year is None and libre.archived_year is None
    assert [r.user_id for r in reserve.reservations] == [alice.id]  # réservations conservées

    html = login(alice).get(f"/personnes/{bob.id}").text
    assert "Réservé-cadeau" in html and "Libre-cadeau" in html
    assert "Acheté-cadeau" not in html and "Retiré-cadeau" not in html

    # Relançable sans erreur
    assert client.post("/admin/cloture", data={"year": "2027", "confirm": "1"}).status_code == 303
    db.refresh(achete)
    assert achete.archived_year == 2026
