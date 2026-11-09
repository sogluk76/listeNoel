from decimal import Decimal

from app.models import Comment, Gift, Reservation


def test_us11_formulaire_affiche_pour_membre_connecte(client, alice, login_as):
    login_as(client, alice)

    response = client.get("/cadeaux/nouveau")

    assert response.status_code == 200
    assert "Ajouter un cadeau" in response.text


def test_us11_sans_session_redirige_vers_login(client):
    response = client.get("/cadeaux/nouveau", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_us11_creation_minimale_redirige(client, alice, login_as, extract_csrf_token, db_session):
    login_as(client, alice)
    page = client.get("/cadeaux/nouveau")
    token = extract_csrf_token(page.text)

    response = client.post(
        "/cadeaux/nouveau",
        data={"name": "Vélo", "csrf_token": token},
        follow_redirects=False,
    )

    assert response.status_code == 303
    cadeau = db_session.query(Gift).filter_by(name="Vélo").one()
    assert cadeau.author_id == alice.id
    assert cadeau.recipient_id == alice.id


def test_us11_nom_vide_affiche_erreur(client, alice, login_as, extract_csrf_token):
    login_as(client, alice)
    page = client.get("/cadeaux/nouveau")
    token = extract_csrf_token(page.text)

    response = client.post("/cadeaux/nouveau", data={"name": "   ", "csrf_token": token})

    assert response.status_code == 400


def test_us11_destinataire_forge_est_ignore(
    client, alice, bob, login_as, extract_csrf_token, db_session
):
    login_as(client, alice)
    page = client.get("/cadeaux/nouveau")
    token = extract_csrf_token(page.text)

    client.post(
        "/cadeaux/nouveau",
        data={"name": "Jeu", "recipient_id": str(bob.id), "csrf_token": token},
    )

    cadeau = db_session.query(Gift).filter_by(name="Jeu").one()
    assert cadeau.recipient_id == alice.id


def test_us13_personne_inexistante_404(client, alice, login_as):
    login_as(client, alice)

    response = client.get("/personnes/9999")

    assert response.status_code == 404


def test_us13_personne_desactivee_404(client, alice, bob, login_as, db_session):
    bob.is_active = False
    db_session.commit()
    login_as(client, alice)

    response = client.get(f"/personnes/{bob.id}")

    assert response.status_code == 404


def test_us13_admin_comme_personne_404(client, alice, admin, login_as):
    login_as(client, alice)

    response = client.get(f"/personnes/{admin.id}")

    assert response.status_code == 404


def test_us13_propre_liste_ne_revele_rien_sur_une_suggestion_cachee(
    client, alice, bob, create_gift, login_as, db_session
):
    gift = create_gift(bob, recipient=alice, name="Cadeau secret")
    db_session.add(Comment(gift_id=gift.id, author_id=bob.id, content="commentaire secret"))
    db_session.add(Reservation(gift_id=gift.id, user_id=bob.id))
    db_session.commit()
    login_as(client, alice)

    response = client.get(f"/personnes/{alice.id}")

    assert "Cadeau secret" not in response.text
    assert "commentaire secret" not in response.text
    assert "Suggéré" not in response.text


def test_us13_liste_dun_autre_affiche_statut_et_reservants(
    client, alice, bob, create_gift, login_as, db_session
):
    gift = create_gift(bob, name="Cadeau de Bob")
    db_session.add(Reservation(gift_id=gift.id, user_id=alice.id))
    db_session.commit()
    login_as(client, alice)

    response = client.get(f"/personnes/{bob.id}")

    assert "réservé" in response.text
    assert "Alice" in response.text


def test_us12_destinataire_par_defaut_affiche_mon_prenom_sans_liste(client, alice, login_as):
    login_as(client, alice)

    response = client.get("/cadeaux/nouveau/destinataire", params={"is_suggestion": "non"})

    assert "Alice" in response.text
    assert "<select" not in response.text


def test_us12_destinataire_suggestion_exclut_moi_admin_et_inactifs(
    client, alice, bob, chloe, admin, login_as, db_session
):
    chloe.is_active = False
    db_session.commit()
    login_as(client, alice)

    response = client.get("/cadeaux/nouveau/destinataire", params={"is_suggestion": "oui"})

    assert ">Bob</option>" in response.text
    assert ">Alice</option>" not in response.text
    assert ">Chloé</option>" not in response.text
    assert ">Admin</option>" not in response.text
    assert "Idée de : Alice" in response.text


def test_us12_creation_suggestion_enregistre_bon_auteur_et_destinataire(
    client, alice, bob, login_as, extract_csrf_token, db_session
):
    login_as(client, alice)
    page = client.get("/cadeaux/nouveau")
    token = extract_csrf_token(page.text)

    client.post(
        "/cadeaux/nouveau",
        data={
            "name": "Jeu de société",
            "is_suggestion": "oui",
            "recipient_id": str(bob.id),
            "csrf_token": token,
        },
    )

    cadeau = db_session.query(Gift).filter_by(name="Jeu de société").one()
    assert cadeau.author_id == alice.id
    assert cadeau.recipient_id == bob.id


def test_us12_destinataire_ne_voit_jamais_sa_suggestion_sur_sa_liste_ni_son_compteur(
    client, alice, bob, login_as, extract_csrf_token
):
    login_as(client, alice)
    page = client.get("/cadeaux/nouveau")
    token = extract_csrf_token(page.text)
    client.post(
        "/cadeaux/nouveau",
        data={
            "name": "Jeu secret",
            "is_suggestion": "oui",
            "recipient_id": str(bob.id),
            "csrf_token": token,
        },
    )

    login_as(client, bob)
    liste = client.get(f"/personnes/{bob.id}")
    accueil = client.get("/")

    assert "Jeu secret" not in liste.text
    assert "Bob (0)" in accueil.text


def test_us12_les_autres_voient_suggere_par(
    client, alice, bob, chloe, login_as, extract_csrf_token
):
    login_as(client, alice)
    page = client.get("/cadeaux/nouveau")
    token = extract_csrf_token(page.text)
    client.post(
        "/cadeaux/nouveau",
        data={
            "name": "Jeu visible",
            "is_suggestion": "oui",
            "recipient_id": str(bob.id),
            "csrf_token": token,
        },
    )

    login_as(client, chloe)
    liste = client.get(f"/personnes/{bob.id}")

    assert "Jeu visible" in liste.text
    assert "Suggéré par Alice" in liste.text


def test_us15_lien_souvre_dans_un_nouvel_onglet_avec_rel_securise(
    client, alice, login_as, create_gift
):
    gift = create_gift(alice, name="Vélo", url="https://example.com")
    login_as(client, alice)

    response = client.get(f"/cadeaux/{gift.id}")

    assert 'target="_blank"' in response.text
    assert 'rel="noopener noreferrer"' in response.text


def test_us15_modifier_et_supprimer_visibles_seulement_pour_lauteur(
    client, bob, chloe, login_as, create_gift
):
    gift = create_gift(bob)

    login_as(client, bob)
    response_auteur = client.get(f"/cadeaux/{gift.id}")

    login_as(client, chloe)
    response_autre = client.get(f"/cadeaux/{gift.id}")

    assert f"/cadeaux/{gift.id}/modifier" in response_auteur.text
    assert f"/cadeaux/{gift.id}/modifier" not in response_autre.text
    assert f"/cadeaux/{gift.id}/supprimer" in response_auteur.text
    assert f"/cadeaux/{gift.id}/supprimer" not in response_autre.text


def test_us15_destinataire_de_son_cadeau_ne_voit_ni_statut_ni_reservants_ni_acces_commentaires(
    client, alice, bob, login_as, create_gift, db_session
):
    gift = create_gift(alice)
    db_session.add(Reservation(gift_id=gift.id, user_id=bob.id))
    db_session.commit()
    login_as(client, alice)

    response = client.get(f"/cadeaux/{gift.id}")

    assert "Bob" not in response.text
    assert f"/cadeaux/{gift.id}/commentaires" not in response.text


def test_us15_autre_viewer_voit_statut_reservants_et_acces_commentaires(
    client, alice, bob, chloe, login_as, create_gift, db_session
):
    gift = create_gift(alice)
    db_session.add(Reservation(gift_id=gift.id, user_id=bob.id))
    db_session.commit()
    login_as(client, chloe)

    response = client.get(f"/cadeaux/{gift.id}")

    assert "Bob" in response.text
    assert f"/cadeaux/{gift.id}/commentaires" in response.text


def test_us15_destinataire_dune_suggestion_recoit_404(client, alice, bob, login_as, create_gift):
    gift = create_gift(bob, recipient=alice)
    login_as(client, alice)

    response = client.get(f"/cadeaux/{gift.id}")

    assert response.status_code == 404


def test_us14_recherche_filtre_la_liste(client, alice, create_gift, login_as):
    create_gift(alice, name="Vélo électrique")
    create_gift(alice, name="Casque audio")
    login_as(client, alice)

    response = client.get(f"/personnes/{alice.id}", params={"q": "velo"})

    assert "Vélo électrique" in response.text
    assert "Casque audio" not in response.text


def test_us14_tri_prix_croissant_cadeaux_sans_prix_en_fin(client, alice, create_gift, login_as):
    create_gift(alice, name="Cher", price=Decimal("50"))
    create_gift(alice, name="Pas cher", price=Decimal("5"))
    create_gift(alice, name="Sans prix")
    login_as(client, alice)

    response = client.get(f"/personnes/{alice.id}", params={"tri": "prix"})

    positions = [response.text.index(nom) for nom in ["Pas cher", "Cher", "Sans prix"]]
    assert positions == sorted(positions)


def test_us14_tri_statut_absent_de_sa_propre_liste(client, alice, login_as):
    login_as(client, alice)

    response = client.get(f"/personnes/{alice.id}")

    assert 'value="statut"' not in response.text


def test_us14_tri_statut_force_retombe_sur_le_tri_par_nom_sur_sa_propre_liste(
    client, alice, create_gift, login_as
):
    create_gift(alice, name="Zebre en peluche")
    create_gift(alice, name="Abricots séchés")
    login_as(client, alice)

    response = client.get(f"/personnes/{alice.id}", params={"tri": "statut"})

    assert response.text.index("Abricots") < response.text.index("Zebre")


def test_us14_tri_statut_disponible_sur_la_liste_dun_autre(client, alice, bob, login_as):
    login_as(client, bob)

    response = client.get(f"/personnes/{alice.id}")

    assert 'value="statut"' in response.text


def test_us16_formulaire_prerempli_pour_lauteur(client, alice, create_gift, login_as):
    gift = create_gift(alice, name="Vélo", price=Decimal("50"))
    login_as(client, alice)

    response = client.get(f"/cadeaux/{gift.id}/modifier")

    assert response.status_code == 200
    assert 'value="Vélo"' in response.text


def test_us16_autre_membre_recoit_403_sur_formulaire_et_soumission(
    client, alice, bob, create_gift, login_as, extract_csrf_token
):
    gift = create_gift(alice, name="Vélo")
    login_as(client, alice)
    token = extract_csrf_token(client.get(f"/cadeaux/{gift.id}/modifier").text)
    login_as(client, bob)

    get_response = client.get(f"/cadeaux/{gift.id}/modifier")
    post_response = client.post(
        f"/cadeaux/{gift.id}/modifier",
        data={"name": "Piraté", "csrf_token": token},
    )

    assert get_response.status_code == 403
    assert post_response.status_code == 403


def test_us16_modification_redirige_vers_le_detail(
    client, alice, create_gift, login_as, extract_csrf_token, db_session
):
    gift = create_gift(alice, name="Vélo")
    login_as(client, alice)
    page = client.get(f"/cadeaux/{gift.id}/modifier")
    token = extract_csrf_token(page.text)

    response = client.post(
        f"/cadeaux/{gift.id}/modifier",
        data={"name": "Trottinette", "csrf_token": token},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == f"/cadeaux/{gift.id}"
    db_session.refresh(gift)
    assert gift.name == "Trottinette"


def test_us16_destinataire_non_modifiable_meme_force(
    client, alice, bob, create_gift, login_as, extract_csrf_token, db_session
):
    gift = create_gift(alice, name="Vélo")
    login_as(client, alice)
    page = client.get(f"/cadeaux/{gift.id}/modifier")
    token = extract_csrf_token(page.text)

    client.post(
        f"/cadeaux/{gift.id}/modifier",
        data={"name": "Vélo", "recipient_id": str(bob.id), "csrf_token": token},
    )

    db_session.refresh(gift)
    assert gift.recipient_id == alice.id


def test_us16_cadeau_retire_404_meme_pour_lauteur(client, alice, create_gift, login_as):
    gift = create_gift(alice, name="Vélo", removed=True)
    login_as(client, alice)

    response = client.get(f"/cadeaux/{gift.id}/modifier")

    assert response.status_code == 404


def test_us16_cadeau_archive_404_meme_pour_lauteur(client, alice, create_gift, login_as):
    gift = create_gift(alice, name="Vélo", archived_year=2025)
    login_as(client, alice)

    response = client.get(f"/cadeaux/{gift.id}/modifier")

    assert response.status_code == 404


def test_us17_autre_membre_recoit_403(
    client, alice, bob, create_gift, login_as, extract_csrf_token
):
    gift = create_gift(alice, name="Vélo")
    login_as(client, alice)
    token = extract_csrf_token(client.get(f"/cadeaux/{gift.id}").text)
    login_as(client, bob)

    response = client.post(f"/cadeaux/{gift.id}/supprimer", data={"csrf_token": token})

    assert response.status_code == 403


def test_us17_sans_activite_supprime_definitivement(
    client, alice, create_gift, login_as, extract_csrf_token, db_session
):
    gift = create_gift(alice, name="Vélo")
    gift_id = gift.id
    login_as(client, alice)
    page = client.get(f"/cadeaux/{gift_id}")
    token = extract_csrf_token(page.text)

    response = client.post(f"/cadeaux/{gift_id}/supprimer", data={"csrf_token": token})

    assert response.status_code == 200
    assert "Cadeau supprimé" in response.text
    assert db_session.get(Gift, gift_id) is None


def test_us17_avec_reservation_supprime_en_douceur_meme_message(
    client, alice, bob, create_gift, login_as, extract_csrf_token, db_session
):
    gift = create_gift(alice, name="Vélo")
    db_session.add(Reservation(gift_id=gift.id, user_id=bob.id))
    db_session.commit()
    login_as(client, alice)
    page = client.get(f"/cadeaux/{gift.id}")
    token = extract_csrf_token(page.text)

    response = client.post(f"/cadeaux/{gift.id}/supprimer", data={"csrf_token": token})

    assert response.status_code == 200
    assert "Cadeau supprimé" in response.text
    db_session.refresh(gift)
    assert gift.removed_at is not None


def test_us17_cadeau_deja_retire_recoit_404(
    client, alice, create_gift, login_as, extract_csrf_token
):
    gift = create_gift(alice, name="Vélo", removed=True)
    login_as(client, alice)
    page = client.get("/cadeaux/nouveau")
    token = extract_csrf_token(page.text)

    response = client.post(f"/cadeaux/{gift.id}/supprimer", data={"csrf_token": token})

    assert response.status_code == 404


def test_us17_destinataire_ne_voit_jamais_le_cadeau_retire_sur_sa_liste(
    client, alice, bob, create_gift, login_as, extract_csrf_token, db_session
):
    gift = create_gift(alice, name="Vélo")
    db_session.add(Comment(gift_id=gift.id, author_id=bob.id, content="Chouette"))
    db_session.commit()
    login_as(client, alice)
    page = client.get(f"/cadeaux/{gift.id}")
    token = extract_csrf_token(page.text)
    client.post(f"/cadeaux/{gift.id}/supprimer", data={"csrf_token": token})

    liste = client.get(f"/personnes/{alice.id}")

    assert "Vélo" not in liste.text
