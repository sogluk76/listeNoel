"""US-18 et US-19 : réservation « je m'en occupe » et statut acheté."""

import pytest

from app.models import Reservation, utcnow


@pytest.fixture
def gift(make_gift, bob):
    return make_gift(bob, bob, "Vélo")


def _state(db, gift):
    db.expire_all()
    db.refresh(gift)
    return sorted(r.user_id for r in gift.reservations), gift.purchased_by_id


def test_us18_plusieurs_membres_reservent_le_meme_cadeau(login, db, alice, chloe, gift):
    assert login(alice).post(f"/cadeaux/{gift.id}/reserver").status_code == 303
    login(chloe).post(f"/cadeaux/{gift.id}/reserver")
    assert _state(db, gift) == (sorted([alice.id, chloe.id]), None)
    html = login(chloe).get(f"/cadeaux/{gift.id}").text
    assert "Alice" in html and "Réservé" in html


def test_us18_pas_de_double_reservation(login, db, alice, gift):
    client = login(alice)
    client.post(f"/cadeaux/{gift.id}/reserver")
    client.post(f"/cadeaux/{gift.id}/reserver")
    assert _state(db, gift) == ([alice.id], None)


def test_us18_j_annule_seulement_ma_reservation(login, db, alice, chloe, gift):
    login(alice).post(f"/cadeaux/{gift.id}/reserver")
    login(chloe).post(f"/cadeaux/{gift.id}/annuler-reservation")  # Chloé n'a rien réservé
    assert _state(db, gift) == ([alice.id], None)
    login(alice).post(f"/cadeaux/{gift.id}/annuler-reservation")
    assert _state(db, gift) == ([], None)


def test_us19_seul_un_reservant_marque_achete(login, db, alice, chloe, gift):
    login(alice).post(f"/cadeaux/{gift.id}/reserver")
    assert login(chloe).post(f"/cadeaux/{gift.id}/acheter").status_code == 403
    assert login(alice).post(f"/cadeaux/{gift.id}/acheter").status_code == 303
    assert _state(db, gift) == ([alice.id], alice.id)
    assert "Acheté par Alice" in login(chloe).get(f"/cadeaux/{gift.id}").text


def test_us19_cadeau_achete_bloque_les_reservations(login, db, alice, chloe, gift):
    alice_client = login(alice)
    alice_client.post(f"/cadeaux/{gift.id}/reserver")
    alice_client.post(f"/cadeaux/{gift.id}/acheter")
    login(chloe).post(f"/cadeaux/{gift.id}/reserver")
    alice_client.post(f"/cadeaux/{gift.id}/annuler-reservation")
    assert _state(db, gift) == ([alice.id], alice.id)


def test_us19_commentaires_possibles_sur_un_cadeau_achete(login, db, alice, chloe, gift):
    client = login(alice)
    client.post(f"/cadeaux/{gift.id}/reserver")
    client.post(f"/cadeaux/{gift.id}/acheter")
    response = login(chloe).post(f"/cadeaux/{gift.id}/commentaires", data={"content": "Super"})
    assert response.status_code == 303


def test_us19_seul_l_acheteur_annule_l_achat(login, db, alice, chloe, gift):
    login(alice).post(f"/cadeaux/{gift.id}/reserver")
    login(chloe).post(f"/cadeaux/{gift.id}/reserver")
    login(alice).post(f"/cadeaux/{gift.id}/acheter")
    assert login(chloe).post(f"/cadeaux/{gift.id}/annuler-achat").status_code == 403
    login(alice).post(f"/cadeaux/{gift.id}/annuler-achat")
    # Le cadeau repasse en « réservé », avec ses réservants
    assert _state(db, gift) == (sorted([alice.id, chloe.id]), None)


@pytest.mark.parametrize("state", ["retire", "archive"])
def test_us18_impossible_sur_cadeau_retire_ou_archive(login, db, alice, gift, state):
    gift.reservations.append(Reservation(user_id=alice.id))
    if state == "retire":
        gift.removed_at = utcnow()
    else:
        gift.archived_year = 2026
    db.commit()
    client = login(alice)
    for action in ("annuler-reservation", "acheter"):
        response = client.post(f"/cadeaux/{gift.id}/{action}")
        assert response.status_code == (303 if state == "retire" else 404)
    assert _state(db, gift) == ([alice.id], None)


def test_us25_mes_reservations_groupees_avec_total(login, db, alice, bob, chloe, make_gift):
    from decimal import Decimal

    velo = make_gift(bob, bob, "Vélo", price=Decimal("100"))
    livre = make_gift(bob, bob, "Livre", price=Decimal("20.50"))
    jeu = make_gift(chloe, chloe, "Jeu")
    autre = make_gift(chloe, chloe, "Pas à moi")
    client = login(alice)
    for g in (velo, livre, jeu):
        client.post(f"/cadeaux/{g.id}/reserver")
    client.post(f"/cadeaux/{velo.id}/acheter")
    html = client.get("/profil").text
    assert "Pour Bob" in html and "Pour Chloé" in html
    assert "120,50" in html and "Acheté" in html
    assert autre.name not in html
