def test_us19_non_reservant_recoit_403(
    client, alice, bob, create_gift, login_as, extract_csrf_token
):
    gift = create_gift(alice, name="Vélo")
    login_as(client, bob)
    token = extract_csrf_token(client.get(f"/cadeaux/{gift.id}").text)

    response = client.post(f"/cadeaux/{gift.id}/acheter", data={"csrf_token": token})

    assert response.status_code == 403


def test_us19_reservant_marque_achete_le_fragment_affiche_achete_par(
    client, alice, bob, create_gift, login_as, extract_csrf_token
):
    gift = create_gift(alice, name="Vélo")
    login_as(client, bob)
    token = extract_csrf_token(client.get(f"/cadeaux/{gift.id}").text)
    client.post(f"/cadeaux/{gift.id}/reserver", data={"csrf_token": token})

    response = client.post(f"/cadeaux/{gift.id}/acheter", data={"csrf_token": token})

    assert response.status_code == 200
    assert "Acheté par Bob" in response.text
    assert "Annuler l'achat" in response.text


def test_us19_apres_achat_plus_de_reservation_possible(
    client, alice, bob, chloe, create_gift, login_as, extract_csrf_token
):
    gift = create_gift(alice, name="Vélo")
    login_as(client, bob)
    token_bob = extract_csrf_token(client.get(f"/cadeaux/{gift.id}").text)
    client.post(f"/cadeaux/{gift.id}/reserver", data={"csrf_token": token_bob})
    client.post(f"/cadeaux/{gift.id}/acheter", data={"csrf_token": token_bob})

    login_as(client, chloe)
    token_chloe = extract_csrf_token(client.get(f"/cadeaux/{gift.id}").text)
    reserver = client.post(f"/cadeaux/{gift.id}/reserver", data={"csrf_token": token_chloe})

    login_as(client, bob)
    token_bob = extract_csrf_token(client.get(f"/cadeaux/{gift.id}").text)
    annuler = client.post(f"/cadeaux/{gift.id}/annuler-reservation", data={"csrf_token": token_bob})

    assert reserver.status_code == 400
    assert annuler.status_code == 400


def test_us19_commentaire_toujours_possible_sur_cadeau_achete(
    client, alice, bob, create_gift, login_as, extract_csrf_token
):
    gift = create_gift(alice, name="Vélo")
    login_as(client, bob)
    token = extract_csrf_token(client.get(f"/cadeaux/{gift.id}").text)
    client.post(f"/cadeaux/{gift.id}/reserver", data={"csrf_token": token})
    client.post(f"/cadeaux/{gift.id}/acheter", data={"csrf_token": token})

    page = client.get(f"/cadeaux/{gift.id}")

    assert f"/cadeaux/{gift.id}/commentaires" in page.text


def test_us19_seul_lacheteur_voit_annuler_lachat(
    client, alice, bob, chloe, create_gift, login_as, extract_csrf_token
):
    gift = create_gift(alice, name="Vélo")
    login_as(client, bob)
    token_bob = extract_csrf_token(client.get(f"/cadeaux/{gift.id}").text)
    client.post(f"/cadeaux/{gift.id}/reserver", data={"csrf_token": token_bob})
    client.post(f"/cadeaux/{gift.id}/acheter", data={"csrf_token": token_bob})

    login_as(client, chloe)
    page_chloe = client.get(f"/cadeaux/{gift.id}")
    token_chloe = extract_csrf_token(page_chloe.text)
    annuler_par_chloe = client.post(
        f"/cadeaux/{gift.id}/annuler-achat", data={"csrf_token": token_chloe}
    )

    assert "Annuler l'achat" not in page_chloe.text
    assert annuler_par_chloe.status_code == 403


def test_us19_acheteur_annule_lachat_repasse_en_reserve(
    client, alice, bob, create_gift, login_as, extract_csrf_token
):
    gift = create_gift(alice, name="Vélo")
    login_as(client, bob)
    token = extract_csrf_token(client.get(f"/cadeaux/{gift.id}").text)
    client.post(f"/cadeaux/{gift.id}/reserver", data={"csrf_token": token})
    client.post(f"/cadeaux/{gift.id}/acheter", data={"csrf_token": token})

    response = client.post(f"/cadeaux/{gift.id}/annuler-achat", data={"csrf_token": token})

    assert response.status_code == 200
    assert "Statut : réservé" in response.text
    assert "Réservé par Bob" in response.text


def test_us19_destinataire_ne_voit_aucune_trace_de_lachat(
    client, alice, bob, create_gift, login_as, db_session
):
    from app.services.purchases import mark_purchased
    from app.services.reservations import reserve_gift

    gift = create_gift(alice, name="Vélo")
    reserve_gift(db_session, bob, gift.id)
    mark_purchased(db_session, bob, gift.id)

    login_as(client, alice)
    response = client.get(f"/cadeaux/{gift.id}")

    assert "Bob" not in response.text
    assert "Acheté" not in response.text
