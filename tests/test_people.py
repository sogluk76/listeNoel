def test_us10_liste_affiche_les_membres_actifs_sans_admin(
    client, alice, bob, admin, login_as, db_session
):
    bob.is_active = False
    db_session.commit()
    login_as(client, alice)

    response = client.get("/")

    assert "Alice" in response.text
    assert "Bob" not in response.text
    assert "Admin" not in response.text


def test_us10_liste_triee_par_ordre_alphabetique(client, alice, bob, chloe, login_as):
    login_as(client, alice)

    response = client.get("/")

    position_alice = response.text.index("Alice")
    position_bob = response.text.index("Bob")
    position_chloe = response.text.index("Chloé")
    assert position_alice < position_bob < position_chloe


def test_us10_compteur_sur_sa_propre_ligne_exclut_les_suggestions(
    client, alice, bob, create_gift, login_as
):
    create_gift(alice)
    create_gift(bob, recipient=alice)
    login_as(client, alice)

    response = client.get("/")

    assert "Alice (1)" in response.text


def test_us10_compteur_sur_la_ligne_dun_autre_inclut_les_suggestions(
    client, alice, bob, create_gift, login_as
):
    create_gift(alice, recipient=bob)
    login_as(client, alice)

    response = client.get("/")

    assert "Bob (1)" in response.text


def test_us10_bouton_ajouter_et_lien_vers_une_personne(client, alice, login_as):
    login_as(client, alice)

    response = client.get("/")

    assert "/cadeaux/nouveau" in response.text
    assert f"/personnes/{alice.id}" in response.text
