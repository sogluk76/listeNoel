"""US-11 à US-17 : ajout, suggestion, recherche, tri, détail, modification, suppression."""

from decimal import Decimal

import pytest
from sqlalchemy import select

from app.config import settings
from app.models import Comment, Gift, Reservation
from app.services.gifts import parse_price
from tests.conftest import png_bytes


def _gifts(db):
    db.expire_all()
    return db.scalars(select(Gift)).all()


def test_us11_cadeau_avec_seulement_un_nom(login, db, alice):
    response = login(alice).post("/cadeaux", data={"name": "  Vélo  "})
    assert response.status_code == 303 and response.headers["location"] == f"/personnes/{alice.id}"
    (gift,) = _gifts(db)
    assert gift.name == "Vélo" and gift.author_id == gift.recipient_id == alice.id
    assert gift.price is None and gift.url is None and gift.image_path is None


@pytest.mark.parametrize("name", ["", "   "])
def test_us11_nom_vide_refuse(login, db, alice, name):
    response = login(alice).post("/cadeaux", data={"name": name})
    assert response.status_code == 422 and "obligatoire" in response.text
    assert _gifts(db) == []


@pytest.mark.parametrize("price", ["-5", "12,345", "abc", "1e3x"])
def test_us11_prix_invalide_refuse(login, db, alice, price):
    response = login(alice).post("/cadeaux", data={"name": "Vélo", "price": price})
    assert response.status_code == 422
    assert _gifts(db) == []


@pytest.mark.parametrize(
    "raw, expected", [("39,99", "39.99"), ("39.9", "39.90"), ("40", "40.00"), ("39,99 €", "39.99")]
)
def test_us11_prix_virgule_ou_point(raw, expected):
    assert parse_price(raw) == Decimal(expected)


@pytest.mark.parametrize("url", ["exemple.com", "ftp://exemple.com", "javascript:alert(1)"])
def test_us11_lien_sans_http_refuse(login, db, alice, url):
    response = login(alice).post("/cadeaux", data={"name": "Vélo", "url": url})
    assert response.status_code == 422 and "http" in response.text
    assert _gifts(db) == []


def test_us11_destinataire_forge_ignore_sans_suggestion(login, db, alice, bob):
    login(alice).post("/cadeaux", data={"name": "Vélo", "recipient_id": bob.id})
    (gift,) = _gifts(db)
    assert gift.recipient_id == alice.id


def test_us11_image_enregistree_et_fichier_invalide_refuse(login, db, alice):
    client = login(alice)
    response = client.post(
        "/cadeaux", data={"name": "Vélo"}, files={"image": ("v.png", png_bytes(), "image/png")}
    )
    assert response.status_code == 303
    (gift,) = _gifts(db)
    assert gift.image_path and (settings.media_dir / gift.image_path).is_file()

    response = client.post(
        "/cadeaux", data={"name": "Faux"}, files={"image": ("x.png", b"pas une image", "image/png")}
    )
    assert response.status_code == 422 and "image valide" in response.text
    assert len(_gifts(db)) == 1


def test_us12_formulaire_pour_qui_sans_moi_ni_admin_ni_desactive(
    login, db, alice, bob, chloe, admin
):
    chloe.is_active = False
    db.commit()
    html = login(alice).get("/cadeaux/nouveau").text
    select_html = html.split('id="recipient_id"')[1].split("</select>")[0]
    assert "Bob" in select_html
    assert "Alice" not in select_html and "Chloé" not in select_html and "admin" not in select_html
    assert "Idée de" in html


def test_us12_suggestion_enregistree_et_affichee_aux_autres(login, db, alice, bob, chloe):
    response = login(alice).post(
        "/cadeaux", data={"name": "Trottinette", "suggest": "1", "recipient_id": bob.id}
    )
    assert response.headers["location"] == f"/personnes/{bob.id}"
    (gift,) = _gifts(db)
    assert gift.author_id == alice.id and gift.recipient_id == bob.id
    assert "Suggéré par Alice" in login(chloe).get(f"/personnes/{bob.id}").text
    assert "Trottinette" not in login(bob).get(f"/personnes/{bob.id}").text


@pytest.mark.parametrize("target", ["moi", "admin", "vide", "inconnu"])
def test_us12_destinataire_invalide_refuse(login, db, alice, admin, target):
    recipient = {"moi": alice.id, "admin": admin.id, "vide": "", "inconnu": 999}[target]
    response = login(alice).post(
        "/cadeaux", data={"name": "X", "suggest": "1", "recipient_id": recipient}
    )
    assert response.status_code == 422
    assert _gifts(db) == []


def test_us13_personne_inexistante_404(login, alice, admin):
    client = login(alice)
    assert client.get("/personnes/999").status_code == 404
    assert client.get(f"/personnes/{admin.id}").status_code == 404


def test_us14_recherche_sans_accents_ni_casse(login, alice, bob, make_gift):
    make_gift(bob, bob, "Vélo électrique")
    make_gift(bob, bob, "Livre")
    html = login(alice).get(f"/personnes/{bob.id}?q=velo").text
    assert "Vélo électrique" in html and "Livre" not in html


def test_us14_tri_par_prix_sans_prix_a_la_fin(login, alice, bob, make_gift):
    make_gift(bob, bob, "Sans prix")
    make_gift(bob, bob, "Cher", price=Decimal("90"))
    make_gift(bob, bob, "Pas cher", price=Decimal("5"))
    client = login(alice)
    asc = client.get(f"/personnes/{bob.id}?tri=prix").text
    assert asc.index("Pas cher") < asc.index(">Cher<") < asc.index("Sans prix")
    desc = client.get(f"/personnes/{bob.id}?tri=prix&sens=desc").text
    assert desc.index(">Cher<") < desc.index("Pas cher") < desc.index("Sans prix")


def test_us14_tri_par_statut_absent_de_ma_liste(login, db, alice, bob, make_gift):
    libre = make_gift(bob, bob, "Aaa libre")
    pris = make_gift(bob, bob, "Zzz pris")
    pris.reservations.append(Reservation(user_id=alice.id))
    db.commit()
    assert libre.id
    other = login(alice).get(f"/personnes/{bob.id}?tri=statut&sens=desc").text
    assert 'value="statut"' in other and other.index("Zzz pris") < other.index("Aaa libre")
    mine = login(bob).get(f"/personnes/{bob.id}?tri=statut&sens=desc").text
    assert 'value="statut"' not in mine
    assert mine.index("Zzz pris") < mine.index("Aaa libre")  # retombe sur le tri par nom


def test_us15_detail_lien_et_boutons_auteur(login, alice, bob, make_gift):
    gift = make_gift(bob, bob, "Vélo", url="https://exemple.com/velo", price=Decimal("39.99"))
    as_author = login(bob).get(f"/cadeaux/{gift.id}").text
    assert 'target="_blank" rel="noopener noreferrer"' in as_author
    assert "39,99" in as_author and "Modifier" in as_author and "Supprimer" in as_author
    as_other = login(alice).get(f"/cadeaux/{gift.id}").text
    assert "Modifier" not in as_other and "Je m'en occupe" in as_other


def test_us16_seul_l_auteur_modifie(login, db, alice, bob, make_gift):
    gift = make_gift(bob, bob, "Vélo")
    other = login(alice)
    assert other.get(f"/cadeaux/{gift.id}/modifier").status_code == 403
    assert other.post(f"/cadeaux/{gift.id}/modifier", data={"name": "Piraté"}).status_code == 403
    response = login(bob).post(
        f"/cadeaux/{gift.id}/modifier", data={"name": "Vélo rouge", "price": "120"}
    )
    assert response.status_code == 303
    db.refresh(gift)
    assert gift.name == "Vélo rouge" and gift.price == Decimal("120.00")
    assert gift.recipient_id == bob.id


def test_us16_validations_et_remplacement_d_image(login, db, bob, make_gift):
    client = login(bob)
    client.post(
        "/cadeaux", data={"name": "Vélo"}, files={"image": ("v.png", png_bytes(), "image/png")}
    )
    (gift,) = _gifts(db)
    old_file = settings.media_dir / gift.image_path
    assert client.post(f"/cadeaux/{gift.id}/modifier", data={"name": ""}).status_code == 422
    client.post(
        f"/cadeaux/{gift.id}/modifier",
        data={"name": "Vélo"},
        files={"image": ("n.png", png_bytes((30, 30)), "image/png")},
    )
    db.refresh(gift)
    assert not old_file.exists() and (settings.media_dir / gift.image_path).is_file()


def test_us17_suppression_definitive_sans_activite(login, db, alice, bob, make_gift):
    gift = make_gift(bob, bob, "Vélo")
    assert login(alice).post(f"/cadeaux/{gift.id}/supprimer").status_code == 403
    response = login(bob).post(f"/cadeaux/{gift.id}/supprimer")
    assert response.status_code == 303
    assert _gifts(db) == []


@pytest.mark.parametrize("activity", ["reservation", "achat", "commentaire"])
def test_us17_suppression_douce_avec_activite(login, db, alice, bob, make_gift, activity):
    gift = make_gift(bob, bob, "Vélo")
    if activity == "commentaire":
        gift.comments.append(Comment(author_id=alice.id, content="ok"))
    else:
        gift.reservations.append(Reservation(user_id=alice.id))
        if activity == "achat":
            gift.purchased_by_id = alice.id
    db.commit()
    client = login(bob)
    hard = make_gift(bob, bob, "Autre")
    soft_response = client.post(f"/cadeaux/{gift.id}/supprimer")
    soft_page = client.get(soft_response.headers["location"]).text
    hard_response = client.post(f"/cadeaux/{hard.id}/supprimer")
    hard_page = client.get(hard_response.headers["location"]).text
    # Même écran et même message dans les deux cas : rien n'est révélé à l'auteur
    assert soft_response.headers["location"] == hard_response.headers["location"]
    assert "Cadeau supprimé." in soft_page and "Cadeau supprimé." in hard_page
    assert "Vélo" not in soft_page
    (remaining,) = _gifts(db)
    assert remaining.id == gift.id and remaining.removed_at is not None
    # Un cadeau retiré n'est plus réservable
    other = login(alice)
    other.post(f"/cadeaux/{gift.id}/reserver")
    assert "plus modifiable" in other.get(f"/cadeaux/{gift.id}").text
