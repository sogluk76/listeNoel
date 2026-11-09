from app.models import Reservation


def test_us18_bouton_absent_pour_le_destinataire(client, alice, create_gift, login_as):
    gift = create_gift(alice, name="Vélo")
    login_as(client, alice)

    response = client.get(f"/cadeaux/{gift.id}")

    assert "Je m'en occupe" not in response.text
    assert "reservation" not in response.text


def test_us18_destinataire_requete_forgee_refusee_sans_rien_reveler(
    client, alice, bob, create_gift, login_as, extract_csrf_token
):
    gift = create_gift(alice, name="Vélo")
    login_as(client, bob)
    token = extract_csrf_token(client.get(f"/cadeaux/{gift.id}").text)
    login_as(client, alice)

    response = client.post(f"/cadeaux/{gift.id}/reserver", data={"csrf_token": token})

    assert response.status_code == 403
    assert "Vélo" not in response.text


def test_us18_reserver_retourne_le_fragment_avec_le_bouton_annuler(
    client, alice, bob, create_gift, login_as, extract_csrf_token
):
    gift = create_gift(alice, name="Vélo")
    login_as(client, bob)
    page = client.get(f"/cadeaux/{gift.id}")
    token = extract_csrf_token(page.text)

    response = client.post(f"/cadeaux/{gift.id}/reserver", data={"csrf_token": token})

    assert response.status_code == 200
    assert "Annuler ma réservation" in response.text
    assert "Je m'en occupe" not in response.text


def test_us18_deux_membres_reservent_le_meme_cadeau(
    client, alice, bob, chloe, create_gift, login_as, extract_csrf_token, db_session
):
    gift = create_gift(alice, name="Vélo")
    login_as(client, bob)
    token_bob = extract_csrf_token(client.get(f"/cadeaux/{gift.id}").text)
    client.post(f"/cadeaux/{gift.id}/reserver", data={"csrf_token": token_bob})

    login_as(client, chloe)
    token_chloe = extract_csrf_token(client.get(f"/cadeaux/{gift.id}").text)
    client.post(f"/cadeaux/{gift.id}/reserver", data={"csrf_token": token_chloe})

    assert db_session.query(Reservation).filter_by(gift_id=gift.id).count() == 2


def test_us18_annuler_retire_sa_reservation(
    client, alice, bob, create_gift, login_as, extract_csrf_token, db_session
):
    gift = create_gift(alice, name="Vélo")
    login_as(client, bob)
    token = extract_csrf_token(client.get(f"/cadeaux/{gift.id}").text)
    client.post(f"/cadeaux/{gift.id}/reserver", data={"csrf_token": token})

    response = client.post(f"/cadeaux/{gift.id}/annuler-reservation", data={"csrf_token": token})

    assert response.status_code == 200
    assert "Je m'en occupe" in response.text
    assert db_session.query(Reservation).filter_by(gift_id=gift.id).count() == 0


def test_us18_annuler_une_reservation_quon_na_pas_faite_refuse(
    client, alice, bob, chloe, create_gift, login_as, extract_csrf_token, db_session
):
    gift = create_gift(alice, name="Vélo")
    login_as(client, bob)
    token_bob = extract_csrf_token(client.get(f"/cadeaux/{gift.id}").text)
    client.post(f"/cadeaux/{gift.id}/reserver", data={"csrf_token": token_bob})

    login_as(client, chloe)
    token_chloe = extract_csrf_token(client.get(f"/cadeaux/{gift.id}").text)
    response = client.post(
        f"/cadeaux/{gift.id}/annuler-reservation", data={"csrf_token": token_chloe}
    )

    assert response.status_code == 400
    assert db_session.query(Reservation).filter_by(gift_id=gift.id).count() == 1


def test_us18_reserver_cadeau_achete_recoit_400(
    client, alice, bob, create_gift, login_as, extract_csrf_token
):
    gift = create_gift(alice, name="Vélo", purchased_by=bob)
    login_as(client, bob)
    token = extract_csrf_token(client.get(f"/cadeaux/{gift.id}").text)

    response = client.post(f"/cadeaux/{gift.id}/reserver", data={"csrf_token": token})

    assert response.status_code == 400


def test_us18_reserver_cadeau_retire_recoit_400(
    client, alice, bob, create_gift, login_as, extract_csrf_token
):
    gift = create_gift(alice, name="Vélo", removed=True)
    login_as(client, bob)
    token = extract_csrf_token(client.get("/cadeaux/nouveau").text)

    response = client.post(f"/cadeaux/{gift.id}/reserver", data={"csrf_token": token})

    assert response.status_code == 400


def test_us18_reserver_cadeau_archive_recoit_404(
    client, alice, bob, create_gift, login_as, extract_csrf_token
):
    gift = create_gift(alice, name="Vélo", archived_year=2025)
    login_as(client, bob)
    token = extract_csrf_token(client.get("/cadeaux/nouveau").text)

    response = client.post(f"/cadeaux/{gift.id}/reserver", data={"csrf_token": token})

    assert response.status_code == 404
