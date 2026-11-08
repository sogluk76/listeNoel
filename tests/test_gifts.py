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
