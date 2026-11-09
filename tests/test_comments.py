from app.models import Comment


def _poster_commentaire(client, gift_id, content, token):
    client.post(f"/cadeaux/{gift_id}/commentaires", data={"content": content, "csrf_token": token})


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


def test_us22_bouton_modifier_et_supprimer_visibles_seulement_sur_mon_message(
    client, alice, bob, chloe, create_gift, login_as, extract_csrf_token, db_session
):
    gift = create_gift(alice, name="Vélo")
    login_as(client, bob)
    token = extract_csrf_token(client.get(f"/cadeaux/{gift.id}/commentaires").text)
    _poster_commentaire(client, gift.id, "Message de Bob", token)
    comment = db_session.query(Comment).filter_by(gift_id=gift.id).one()

    login_as(client, chloe)
    page_chloe = client.get(f"/cadeaux/{gift.id}/commentaires")

    login_as(client, bob)
    page_bob = client.get(f"/cadeaux/{gift.id}/commentaires")

    assert f"/commentaires/{comment.id}/modifier" not in page_chloe.text
    assert f"/commentaires/{comment.id}/modifier" in page_bob.text


def test_us22_modifier_message_dun_autre_recoit_403(
    client, alice, bob, chloe, create_gift, login_as, extract_csrf_token, db_session
):
    gift = create_gift(alice, name="Vélo")
    login_as(client, bob)
    token_bob = extract_csrf_token(client.get(f"/cadeaux/{gift.id}/commentaires").text)
    _poster_commentaire(client, gift.id, "Message de Bob", token_bob)
    comment = db_session.query(Comment).filter_by(gift_id=gift.id).one()

    login_as(client, chloe)
    token_chloe = extract_csrf_token(client.get(f"/cadeaux/{gift.id}/commentaires").text)

    response = client.post(
        f"/commentaires/{comment.id}/modifier",
        data={"content": "Piraté", "csrf_token": token_chloe},
    )
    get_response = client.get(f"/commentaires/{comment.id}/modifier")

    assert response.status_code == 403
    assert get_response.status_code == 403


def test_us22_supprimer_message_dun_autre_recoit_403(
    client, alice, bob, chloe, create_gift, login_as, extract_csrf_token, db_session
):
    gift = create_gift(alice, name="Vélo")
    login_as(client, bob)
    token_bob = extract_csrf_token(client.get(f"/cadeaux/{gift.id}/commentaires").text)
    _poster_commentaire(client, gift.id, "Message de Bob", token_bob)
    comment = db_session.query(Comment).filter_by(gift_id=gift.id).one()

    login_as(client, chloe)
    token_chloe = extract_csrf_token(client.get(f"/cadeaux/{gift.id}/commentaires").text)

    response = client.post(
        f"/commentaires/{comment.id}/supprimer", data={"csrf_token": token_chloe}
    )

    assert response.status_code == 403
    assert db_session.get(Comment, comment.id) is not None


def test_us22_modifier_affiche_modifie(
    client, alice, bob, create_gift, login_as, extract_csrf_token, db_session
):
    gift = create_gift(alice, name="Vélo")
    login_as(client, bob)
    token = extract_csrf_token(client.get(f"/cadeaux/{gift.id}/commentaires").text)
    _poster_commentaire(client, gift.id, "Premier texte", token)
    comment = db_session.query(Comment).filter_by(gift_id=gift.id).one()

    response = client.post(
        f"/commentaires/{comment.id}/modifier",
        data={"content": "Texte corrigé", "csrf_token": token},
    )

    assert response.status_code == 200
    assert "Texte corrigé" in response.text
    assert "(modifié)" in response.text


def test_us22_supprimer_fait_disparaitre_le_message_et_le_badge(
    client, alice, bob, create_gift, login_as, extract_csrf_token, db_session
):
    gift = create_gift(alice, name="Vélo")
    login_as(client, bob)
    token = extract_csrf_token(client.get(f"/cadeaux/{gift.id}/commentaires").text)
    _poster_commentaire(client, gift.id, "À supprimer", token)
    comment = db_session.query(Comment).filter_by(gift_id=gift.id).one()

    response = client.post(f"/commentaires/{comment.id}/supprimer", data={"csrf_token": token})
    fil = client.get(f"/cadeaux/{gift.id}/commentaires")
    liste = client.get(f"/personnes/{alice.id}")

    assert response.status_code == 200
    assert "À supprimer" not in fil.text
    assert "💬 0" in liste.text
