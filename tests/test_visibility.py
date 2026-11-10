"""Matrice de confidentialité RG-30 : le destinataire ne reçoit jamais rien de caché,
ni dans les pages, ni dans les fragments HTMX, ni par URL forgée."""

import pytest

from app.models import Comment, Reservation, utcnow

HTMX = {"HX-Request": "true"}


@pytest.fixture
def scene(db, alice, bob, chloe, make_gift):
    """Alice a un cadeau personnel (réservé et commenté par Bob) et une suggestion de Bob."""
    perso = make_gift(alice, alice, "Livre de cuisine")
    perso.reservations.append(Reservation(user_id=bob.id))
    perso.comments.append(Comment(author_id=bob.id, content="SECRET-COMMENTAIRE je le prends"))
    surprise = make_gift(bob, alice, "SECRET-SURPRISE trottinette")
    surprise.comments.append(Comment(author_id=chloe.id, content="SECRET-COMMENTAIRE bonne idée"))
    db.commit()
    return {"perso": perso, "surprise": surprise}


def test_us10_compteur_sans_les_suggestions_sur_ma_ligne(login, scene, alice, bob):
    html_alice = login(alice).get("/").text
    html_bob = login(bob).get("/").text
    assert _count(html_alice, "Alice") == 1  # son cadeau personnel seulement
    assert _count(html_bob, "Alice") == 2  # personnel + suggestion


def _count(html: str, name: str) -> int:
    row = html.split(f">{name}")[1]
    return int(row.split('class="count"')[1].split(">")[1].split("<")[0])


def test_us13_ma_liste_ne_contient_aucune_donnee_cachee(login, scene, alice):
    html = login(alice).get(f"/personnes/{alice.id}").text
    assert "Livre de cuisine" in html
    for hidden in ("SECRET", "Suggéré par", "pill", "badge", "commentaires", "Réservé"):
        assert hidden not in html, hidden


def test_us13_fragment_htmx_de_ma_liste_sans_donnee_cachee(login, scene, alice):
    html = login(alice).get(f"/personnes/{alice.id}?q=&tri=statut", headers=HTMX).text
    assert "Livre de cuisine" in html
    for hidden in ("SECRET", "pill", "badge", "commentaires"):
        assert hidden not in html, hidden


def test_us14_recherche_ne_revele_pas_de_suggestion(login, scene, alice):
    html = login(alice).get(f"/personnes/{alice.id}?q=trottinette").text
    assert "SECRET" not in html


def test_us13_les_autres_voient_tout(login, scene, alice, chloe):
    html = login(chloe).get(f"/personnes/{alice.id}").text
    assert "SECRET-SURPRISE trottinette" in html
    assert "Suggéré par Bob" in html
    assert "Réservé" in html and "badge" in html


def test_us15_detail_de_mon_cadeau_sans_statut_ni_reservants(login, scene, alice):
    html = login(alice).get(f"/cadeaux/{scene['perso'].id}").text
    assert "Livre de cuisine" in html
    for hidden in ("Qui s'en occupe", "Bob", "commentaires", "pill", "Je m'en occupe"):
        assert hidden not in html, hidden


def test_us12_suggestion_introuvable_pour_le_destinataire(login, scene, alice):
    client = login(alice)
    gift_id = scene["surprise"].id
    assert client.get(f"/cadeaux/{gift_id}").status_code == 404
    assert client.get(f"/cadeaux/{gift_id}/modifier").status_code == 404
    assert client.get(f"/cadeaux/{gift_id}/commentaires").status_code == 404
    assert client.post(f"/cadeaux/{gift_id}/supprimer").status_code == 404
    assert client.post(f"/cadeaux/{gift_id}/reserver").status_code == 404


def test_us20_commentaires_interdits_au_destinataire(login, scene, alice):
    client = login(alice)
    gift_id = scene["perso"].id
    for path in (f"/cadeaux/{gift_id}/commentaires", f"/cadeaux/{gift_id}/commentaires/fil"):
        response = client.get(path)
        assert response.status_code == 403
        assert "SECRET" not in response.text
    response = client.get(f"/cadeaux/{gift_id}/commentaires/fil", headers=HTMX)
    assert response.status_code == 403 and "SECRET" not in response.text
    assert (
        client.post(f"/cadeaux/{gift_id}/commentaires", data={"content": "coucou"}).status_code
        == 403
    )


def test_us22_destinataire_ne_peut_pas_toucher_un_commentaire(login, db, scene, alice):
    comment = scene["perso"].comments[0]
    client = login(alice)
    assert client.get(f"/commentaires/{comment.id}/modifier").status_code == 403
    assert client.post(f"/commentaires/{comment.id}/supprimer").status_code == 403


def test_us18_reservation_interdite_au_destinataire(login, db, scene, alice):
    client = login(alice)
    gift_id = scene["perso"].id
    for action in ("reserver", "annuler-reservation", "acheter", "annuler-achat"):
        assert client.post(f"/cadeaux/{gift_id}/{action}").status_code == 403


def test_us25_mes_reservations_ne_montrent_pas_mes_propres_cadeaux(login, scene, alice, bob):
    assert "Livre de cuisine" not in login(alice).get("/profil").text
    assert "Livre de cuisine" in login(bob).get("/profil").text


def test_rg22_cadeau_retire_visible_des_autres_pas_de_son_auteur(
    login, db, scene, alice, bob, chloe
):
    scene["perso"].removed_at = utcnow()
    scene["surprise"].removed_at = utcnow()
    db.commit()
    # Alice (auteure de son cadeau personnel) ne le voit plus
    assert "Livre de cuisine" not in login(alice).get(f"/personnes/{alice.id}").text
    # Bob (auteur de la suggestion) ne voit plus sa suggestion, mais voit le cadeau d'Alice retiré
    html_bob = login(bob).get(f"/personnes/{alice.id}").text
    assert "SECRET-SURPRISE" not in html_bob and "Retiré" in html_bob
    # Chloé voit les deux, marqués « Retiré »
    html_chloe = login(chloe).get(f"/personnes/{alice.id}").text
    assert "SECRET-SURPRISE" in html_chloe and html_chloe.count("pill--removed") == 2
    # ... et ils ne comptent plus
    assert _count(login(chloe).get("/").text, "Alice") == 0


def test_rg40_cadeau_archive_invisible_partout(login, db, scene, alice, bob):
    scene["perso"].archived_year = 2026
    db.commit()
    client = login(bob)
    assert "Livre de cuisine" not in client.get(f"/personnes/{alice.id}").text
    assert client.get(f"/cadeaux/{scene['perso'].id}").status_code == 404
    assert "Livre de cuisine" not in client.get("/profil").text
    assert _count(client.get("/").text, "Alice") == 1  # il reste la suggestion


def test_rg11_compte_desactive_masque(login, db, scene, alice, bob):
    alice.is_active = False
    db.commit()
    client = login(bob)
    assert ">Alice" not in client.get("/").text
    assert client.get(f"/personnes/{alice.id}").status_code == 404
    assert client.get(f"/cadeaux/{scene['perso'].id}").status_code == 404


def test_rg11_session_d_un_compte_desactive_refusee(login, db, alice):
    client = login(alice)
    alice.is_active = False
    db.commit()
    assert client.get("/").headers["location"] == "/login"
