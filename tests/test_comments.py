from app.models import Comment


def test_us20_destinataire_dun_cadeau_personnel_recoit_403(client, alice, create_gift, login_as):
    gift = create_gift(alice, name="Vélo")
    login_as(client, alice)

    response = client.get(f"/cadeaux/{gift.id}/commentaires")

    assert response.status_code == 403


def test_us20_destinataire_recoit_403_aussi_sur_le_fragment_de_rafraichissement(
    client, alice, create_gift, login_as
):
    gift = create_gift(alice, name="Vélo")
    login_as(client, alice)

    response = client.get(f"/cadeaux/{gift.id}/commentaires/fil")

    assert response.status_code == 403


def test_us20_destinataire_dune_suggestion_recoit_403(client, alice, bob, create_gift, login_as):
    gift = create_gift(bob, recipient=alice, name="Cadeau secret")
    login_as(client, alice)

    response = client.get(f"/cadeaux/{gift.id}/commentaires")

    assert response.status_code == 403


def test_us20_autre_membre_voit_le_fil(client, alice, bob, create_gift, login_as, db_session):
    gift = create_gift(alice, name="Vélo")
    db_session.add(Comment(gift_id=gift.id, author_id=bob.id, content="Chouette idée"))
    db_session.commit()
    login_as(client, bob)

    response = client.get(f"/cadeaux/{gift.id}/commentaires")

    assert response.status_code == 200
    assert "Chouette idée" in response.text


def test_us20_messages_tries_du_plus_ancien_au_plus_recent(
    client, alice, bob, chloe, create_gift, login_as, db_session
):
    gift = create_gift(alice, name="Vélo")
    db_session.add(Comment(gift_id=gift.id, author_id=bob.id, content="Premier message"))
    db_session.commit()
    db_session.add(Comment(gift_id=gift.id, author_id=chloe.id, content="Second message"))
    db_session.commit()
    login_as(client, bob)

    response = client.get(f"/cadeaux/{gift.id}/commentaires")

    assert response.text.index("Premier message") < response.text.index("Second message")


def test_us20_auteur_sans_photo_affiche_placeholder(
    client, alice, bob, create_gift, login_as, db_session
):
    gift = create_gift(alice, name="Vélo")
    db_session.add(Comment(gift_id=gift.id, author_id=bob.id, content="Salut"))
    db_session.commit()
    login_as(client, bob)

    response = client.get(f"/cadeaux/{gift.id}/commentaires")

    assert "photo-placeholder" in response.text
    assert ">B<" in response.text


def test_us20_contenu_echappe_pas_dinjection_html(
    client, alice, bob, create_gift, login_as, db_session
):
    gift = create_gift(alice, name="Vélo")
    db_session.add(Comment(gift_id=gift.id, author_id=bob.id, content="<script>alert(1)</script>"))
    db_session.commit()
    login_as(client, bob)

    response = client.get(f"/cadeaux/{gift.id}/commentaires")

    assert "<script>" not in response.text
    assert "&lt;script&gt;" in response.text


def test_us20_cadeau_retire_reste_commentable(
    client, alice, bob, create_gift, login_as, db_session
):
    gift = create_gift(alice, name="Vélo")
    db_session.add(Comment(gift_id=gift.id, author_id=bob.id, content="Toujours là"))
    db_session.commit()
    gift.removed_at = gift.created_at
    db_session.commit()
    login_as(client, bob)

    response = client.get(f"/cadeaux/{gift.id}/commentaires")

    assert response.status_code == 200
    assert "Toujours là" in response.text


def test_us20_cadeau_archive_recoit_404(client, alice, bob, create_gift, login_as):
    gift = create_gift(alice, name="Vélo", archived_year=2025)
    login_as(client, bob)

    response = client.get(f"/cadeaux/{gift.id}/commentaires")

    assert response.status_code == 404


def test_us20_cadeau_inexistant_recoit_404(client, bob, login_as):
    login_as(client, bob)

    response = client.get("/cadeaux/9999/commentaires")

    assert response.status_code == 404


def test_us21_message_apparait_immediatement_dans_le_fil(
    client, alice, bob, create_gift, login_as, extract_csrf_token
):
    gift = create_gift(alice, name="Vélo")
    login_as(client, bob)
    token = extract_csrf_token(client.get(f"/cadeaux/{gift.id}/commentaires").text)

    response = client.post(
        f"/cadeaux/{gift.id}/commentaires",
        data={"content": "Super idée !", "csrf_token": token},
    )

    assert response.status_code == 200
    assert "Super idée !" in response.text


def test_us21_message_vide_refuse(client, alice, bob, create_gift, login_as, extract_csrf_token):
    gift = create_gift(alice, name="Vélo")
    login_as(client, bob)
    token = extract_csrf_token(client.get(f"/cadeaux/{gift.id}/commentaires").text)

    response = client.post(
        f"/cadeaux/{gift.id}/commentaires", data={"content": "   ", "csrf_token": token}
    )

    assert response.status_code == 400


def test_us21_message_trop_long_refuse(
    client, alice, bob, create_gift, login_as, extract_csrf_token
):
    gift = create_gift(alice, name="Vélo")
    login_as(client, bob)
    token = extract_csrf_token(client.get(f"/cadeaux/{gift.id}/commentaires").text)

    response = client.post(
        f"/cadeaux/{gift.id}/commentaires", data={"content": "a" * 1001, "csrf_token": token}
    )

    assert response.status_code == 400


def test_us21_emojis_affiches_correctement(
    client, alice, bob, create_gift, login_as, extract_csrf_token
):
    gift = create_gift(alice, name="Vélo")
    login_as(client, bob)
    token = extract_csrf_token(client.get(f"/cadeaux/{gift.id}/commentaires").text)

    response = client.post(
        f"/cadeaux/{gift.id}/commentaires",
        data={"content": "Trop bien 🎉🎄", "csrf_token": token},
    )

    assert "Trop bien 🎉🎄" in response.text


def test_us21_destinataire_ne_peut_pas_ecrire_sur_son_propre_cadeau(
    client, alice, create_gift, login_as, extract_csrf_token
):
    gift = create_gift(alice, name="Vélo")
    login_as(client, alice)
    token = extract_csrf_token(client.get(f"/cadeaux/{gift.id}").text)

    response = client.post(
        f"/cadeaux/{gift.id}/commentaires",
        data={"content": "Je commente mon cadeau", "csrf_token": token},
    )

    assert response.status_code == 403


def test_us21_badge_incremente_sur_la_liste(
    client, alice, bob, create_gift, login_as, extract_csrf_token
):
    gift = create_gift(alice, name="Vélo")
    login_as(client, bob)
    token = extract_csrf_token(client.get(f"/cadeaux/{gift.id}/commentaires").text)
    client.post(
        f"/cadeaux/{gift.id}/commentaires",
        data={"content": "Super idée !", "csrf_token": token},
    )

    liste = client.get(f"/personnes/{alice.id}")

    assert "💬 1" in liste.text
