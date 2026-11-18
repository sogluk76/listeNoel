"""Matrice de confidentialité RG-30 : le destinataire ne reçoit jamais rien de caché,
ni dans les pages, ni dans les fragments HTMX, ni par URL forgée."""

import pytest
from sqlalchemy import select

from app.models import Comment, Notification, Reservation, utcnow

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
    html_alice = login(alice).get("/noel").text
    html_bob = login(bob).get("/noel").text
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
    assert _count(login(chloe).get("/noel").text, "Alice") == 0


def test_rg40_cadeau_archive_invisible_partout(login, db, scene, alice, bob):
    scene["perso"].archived_year = 2026
    db.commit()
    client = login(bob)
    assert "Livre de cuisine" not in client.get(f"/personnes/{alice.id}").text
    assert client.get(f"/cadeaux/{scene['perso'].id}").status_code == 404
    assert "Livre de cuisine" not in client.get("/profil").text
    assert _count(client.get("/noel").text, "Alice") == 1  # il reste la suggestion


def test_rg11_compte_desactive_masque(login, db, scene, alice, bob):
    alice.is_active = False
    db.commit()
    client = login(bob)
    assert ">Alice" not in client.get("/noel").text
    assert client.get(f"/personnes/{alice.id}").status_code == 404
    assert client.get(f"/cadeaux/{scene['perso'].id}").status_code == 404


def test_rg11_session_d_un_compte_desactive_refusee(login, db, alice):
    client = login(alice)
    alice.is_active = False
    db.commit()
    assert client.get("/").headers["location"] == "/login"


# --- Notifications de mention (RG-43, RG-45) ----------------------------------


def _bell_count(html: str) -> bool:
    return "app-header__bell-count" in html


def test_us27_mentionner_le_destinataire_ne_le_notifie_jamais(login, db, alice, bob, make_gift):
    """La surprise d'abord : Alice ne doit pas apprendre qu'on parle de son cadeau."""
    gift = make_gift(alice, alice, "Vélo")
    alice_client = login(alice)
    response = login(bob).post(
        f"/cadeaux/{gift.id}/commentaires", data={"content": "SECRET @Alice va adorer"}
    )
    assert response.status_code == 303  # le commentaire est accepté
    db.expire_all()
    assert db.scalars(select(Notification)).all() == []

    for path in ("/", "/notifications", f"/personnes/{alice.id}", f"/cadeaux/{gift.id}"):
        html = alice_client.get(path).text
        assert not _bell_count(html), path
        assert "SECRET" not in html, path
    assert "Aucune notification" in alice_client.get("/notifications").text
    # Pour les autres, le prénom du destinataire reste du texte simple.
    thread = login(bob).get(f"/cadeaux/{gift.id}/commentaires/fil").text
    assert "SECRET @Alice va adorer" in thread and 'class="mention"' not in thread


def test_us28_notification_forgee_en_base_invisible_pour_le_destinataire(
    login, db, alice, bob, make_gift
):
    """Défense en profondeur : même si une ligne existait, le destinataire ne voit rien."""
    gift = make_gift(alice, alice, "Vélo")
    comment = Comment(author_id=bob.id, content="SECRET-FORGE @Alice")
    gift.comments.append(comment)
    comment.notifications.append(Notification(user_id=alice.id))
    db.commit()
    client = login(alice)
    html = client.get("/notifications").text
    assert "SECRET-FORGE" not in html and "Aucune notification" in html
    assert not _bell_count(client.get("/").text)
    db.expire_all()
    assert db.scalar(select(Notification)).read_at is None  # pas même marquée lue


def test_us28_notification_masquee_si_le_cadeau_n_est_plus_visible(
    login, db, alice, bob, chloe, make_gift
):
    gift = make_gift(chloe, chloe, "Vélo")
    login(alice).post(f"/cadeaux/{gift.id}/commentaires", data={"content": "ARCHIVE-TEST @Bob"})
    client = login(bob)
    assert _bell_count(client.get("/").text)

    gift.archived_year = 2026  # RG-40
    db.commit()
    assert not _bell_count(client.get("/").text)
    assert "ARCHIVE-TEST" not in client.get("/notifications").text

    gift.archived_year = None
    chloe.is_active = False  # RG-11 : la liste d'un compte désactivé est masquée
    db.commit()
    assert not _bell_count(client.get("/").text)
    assert "ARCHIVE-TEST" not in client.get("/notifications").text


def test_rg57_suggestion_ne_notifie_jamais_le_destinataire(login, db, alice, bob, chloe):
    """La surprise d'abord : une suggestion pour Alice ne lui crée aucune notification."""
    response = login(bob).post(
        "/cadeaux", data={"name": "SECRET-SURPRISE", "suggest": "1", "recipient_id": alice.id}
    )
    assert response.status_code == 303
    db.expire_all()
    assert alice.id not in db.scalars(select(Notification.user_id)).all()
    alice_client = login(alice)
    for path in ("/", "/notifications", f"/personnes/{alice.id}"):
        html = alice_client.get(path).text
        assert not _bell_count(html), path
        assert "SECRET" not in html, path


def test_rg57_notification_cadeau_forgee_invisible_pour_le_destinataire(
    login, db, alice, bob, make_gift
):
    """Défense en profondeur : même une ligne forgée en base ne révèle pas la suggestion."""
    gift = make_gift(bob, alice, "SECRET-FORGE")
    gift.notifications.append(Notification(user_id=alice.id))
    db.commit()
    client = login(alice)
    html = client.get("/notifications").text
    assert "SECRET-FORGE" not in html and "Aucune notification" in html
    assert not _bell_count(client.get("/").text)
    db.expire_all()
    assert db.scalar(select(Notification)).read_at is None


def test_rg57_notification_cadeau_masquee_si_archive(login, db, alice, bob, make_gift):
    gift = make_gift(alice, alice, "ARCHIVE-TEST")
    gift.notifications.append(Notification(user_id=bob.id))
    db.commit()
    client = login(bob)
    assert _bell_count(client.get("/").text)
    gift.archived_year = 2026  # RG-40
    db.commit()
    assert not _bell_count(client.get("/").text)
    assert "ARCHIVE-TEST" not in client.get("/notifications").text
