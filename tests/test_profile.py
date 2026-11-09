from app.models import Comment


def test_us23_ecran_profil_affiche_placeholder_sans_photo(client, alice, login_as):
    login_as(client, alice)

    response = client.get("/profil")

    assert response.status_code == 200
    assert "photo-placeholder" in response.text


def test_us23_ecran_profil_affiche_la_photo_actuelle(
    client, alice, login_as, extract_csrf_token, make_image_bytes
):
    login_as(client, alice)
    token = extract_csrf_token(client.get("/profil").text)
    client.post(
        "/profil/photo",
        data={"csrf_token": token},
        files={"photo": ("photo.png", make_image_bytes("PNG"), "image/png")},
    )

    response = client.get("/profil")

    assert "<img" in response.text


def test_us23_nouvelle_photo_utilisee_a_la_connexion(
    client, alice, login_as, extract_csrf_token, make_image_bytes
):
    login_as(client, alice)
    token = extract_csrf_token(client.get("/profil").text)
    client.post(
        "/profil/photo",
        data={"csrf_token": token},
        files={"photo": ("photo.png", make_image_bytes("PNG"), "image/png")},
    )

    response = client.get("/login/photo", params={"first_name": "Alice"})

    assert "<img" in response.text


def test_us23_nouvelle_photo_utilisee_dans_la_liste_des_personnes(
    client, alice, login_as, extract_csrf_token, make_image_bytes
):
    login_as(client, alice)
    token = extract_csrf_token(client.get("/profil").text)
    client.post(
        "/profil/photo",
        data={"csrf_token": token},
        files={"photo": ("photo.png", make_image_bytes("PNG"), "image/png")},
    )

    response = client.get("/")

    assert "<img" in response.text


def test_us23_nouvelle_photo_utilisee_dans_les_commentaires(
    client, alice, bob, create_gift, login_as, extract_csrf_token, make_image_bytes, db_session
):
    login_as(client, alice)
    token = extract_csrf_token(client.get("/profil").text)
    client.post(
        "/profil/photo",
        data={"csrf_token": token},
        files={"photo": ("photo.png", make_image_bytes("PNG"), "image/png")},
    )

    gift = create_gift(bob, name="Vélo")
    db_session.add(Comment(gift_id=gift.id, author_id=alice.id, content="Salut"))
    db_session.commit()

    response = client.get(f"/cadeaux/{gift.id}/commentaires")

    assert "<img" in response.text


def test_us23_remplacer_la_photo_supprime_lancienne_du_disque(
    client, alice, login_as, extract_csrf_token, make_image_bytes, db_session
):
    login_as(client, alice)
    token = extract_csrf_token(client.get("/profil").text)
    client.post(
        "/profil/photo",
        data={"csrf_token": token},
        files={"photo": ("photo.png", make_image_bytes("PNG"), "image/png")},
    )
    db_session.refresh(alice)
    ancien_chemin = alice.photo_path

    client.post(
        "/profil/photo",
        data={"csrf_token": token},
        files={"photo": ("photo2.png", make_image_bytes("PNG"), "image/png")},
    )

    assert client.get(f"/media/{ancien_chemin}").status_code == 404


def test_us23_supprimer_la_photo_affiche_le_placeholder(
    client, alice, login_as, extract_csrf_token, make_image_bytes
):
    login_as(client, alice)
    token = extract_csrf_token(client.get("/profil").text)
    client.post(
        "/profil/photo",
        data={"csrf_token": token},
        files={"photo": ("photo.png", make_image_bytes("PNG"), "image/png")},
    )

    response = client.post(
        "/profil/photo", data={"csrf_token": token, "remove_photo": "oui"}, follow_redirects=True
    )

    assert "photo-placeholder" in response.text


def test_us23_fichier_invalide_refuse(client, alice, login_as, extract_csrf_token):
    login_as(client, alice)
    token = extract_csrf_token(client.get("/profil").text)

    response = client.post(
        "/profil/photo",
        data={"csrf_token": token},
        files={"photo": ("photo.png", b"pas une image", "image/png")},
    )

    assert response.status_code == 400
