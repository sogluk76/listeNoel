"""US-29 à US-35 : messages privés entre membres (RG-46 à RG-55)."""

import re
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.config import settings
from app.errors import NotFound
from app.models import Conversation, ConversationMember, Message, User, utcnow
from app.services import messages as messages_service
from tests.conftest import _user, png_bytes

HX = {"HX-Request": "true"}
_BELL_RE = re.compile(r'app-header__bell-count">\s*([^<\s]+)\s*<')
_BUBBLE_RE = re.compile(r'msg-bubble__count">\s*([^<\s]+)\s*<')


def _open(client, other: User) -> int:
    """Ouvre la conversation à deux avec `other` et renvoie son identifiant."""
    response = client.post(f"/messages/avec/{other.id}")
    assert response.status_code == 303, response.text
    return int(response.headers["location"].rsplit("/", 1)[1])


def _send(client, conversation_id: int, content: str = "", **kwargs):
    return client.post(f"/messages/{conversation_id}", data={"content": content}, **kwargs)


def _group(client, name: str, *members: User) -> int:
    response = client.post(
        "/messages/groupes", data={"name": name, "members": [m.id for m in members]}
    )
    assert response.status_code == 303, response.text
    return int(response.headers["location"].rsplit("/", 1)[1])


def _bell(client, path: str = "/") -> str | None:
    match = _BELL_RE.search(client.get(path).text)
    return match.group(1) if match else None


def _bubble(client) -> str | None:
    match = _BUBBLE_RE.search(client.get("/").text)
    return match.group(1) if match else None


def _messages(db) -> list[Message]:
    db.expire_all()
    return list(db.scalars(select(Message).order_by(Message.id)).all())


# --- US-29 : conversation à deux (RG-46, RG-48) -------------------------------


def test_us29_une_seule_conversation_par_paire(login, db, alice, bob):
    first = _open(login(alice), bob)
    assert _open(login(bob), alice) == first  # RG-46 : la même, dans les deux sens
    assert _open(login(alice), bob) == first
    assert len(db.scalars(select(Conversation)).all()) == 1


def test_us29_on_n_ecrit_qu_a_un_autre_membre_actif(login, db, alice, bob, admin):
    client = login(alice)
    bob.is_active = False
    db.commit()
    for target in (alice, admin, bob):  # soi-même, l'admin, un compte désactivé
        assert client.post(f"/messages/avec/{target.id}").status_code == 404
    assert client.post("/messages/avec/9999").status_code == 404
    assert db.scalars(select(Conversation)).all() == []


def test_us29_envoyer_et_lire_un_message(login, db, alice, bob):
    alice_client, bob_client = login(alice), login(bob)
    cid = _open(alice_client, bob)
    assert _send(alice_client, cid, "  Coucou <b>Bob</b> 🎄  ").status_code == 303
    html = bob_client.get(f"/messages/{cid}").text
    assert "Coucou &lt;b&gt;Bob&lt;/b&gt; 🎄" in html  # échappé, emojis acceptés
    assert "<b>Bob</b>" not in html
    assert [m.content for m in _messages(db)] == ["Coucou <b>Bob</b> 🎄"]


def test_us29_message_vide_ou_trop_long_refuse(login, db, alice, bob):
    client = login(alice)
    cid = _open(client, bob)
    for content in ("", "   \n ", "x" * 1001):  # RG-48
        response = _send(client, cid, content, headers=HX)
        assert response.status_code == 422
        assert "alert--error" in response.text
    assert _send(client, cid, "x" * 1000).status_code == 303
    assert len(_messages(db)) == 1


def test_us29_liste_des_conversations(login, db, alice, bob, chloe):
    alice_client = login(alice)
    with_bob = _open(alice_client, bob)
    _open(alice_client, chloe)  # ouverte mais vide : pas listée
    _send(alice_client, with_bob, "On fait un cadeau commun ?")
    mine = alice_client.get("/messages").text
    assert "Bob" in mine and "Toi : On fait un cadeau commun ?" in mine
    assert f'href="/messages/{with_bob}"' in mine
    assert "Chloé" not in mine
    theirs = login(bob).get("/messages").text
    assert "Alice" in theirs and "On fait un cadeau commun ?" in theirs
    assert "Aucune conversation" in login(chloe).get("/messages").text


def test_us29_fragment_pour_la_popup_page_entiere_sinon(login, alice, bob):
    client = login(alice)
    cid = _open(client, bob)
    for path in ("/messages", "/messages/nouveau", f"/messages/{cid}"):
        page = client.get(path).text
        assert "<html" in page and 'id="messages-panel"' in page
        assert 'id="msg-dock"' not in page  # pas de bulle sur la messagerie en pleine page
        popup = client.get(path, headers=HX).text
        assert "<html" not in popup and "data-view-url" in popup


# --- RG-47 : seuls les participants lisent ------------------------------------


def test_rg47_un_tiers_ne_lit_ni_n_ecrit(login, db, alice, bob, chloe):
    alice_client = login(alice)
    cid = _open(alice_client, bob)
    _send(alice_client, cid, "Secret entre nous")
    message = _messages(db)[0]
    outsider = login(chloe)
    for path in (
        f"/messages/{cid}",
        f"/messages/{cid}/fil",
        f"/messages/{cid}/reglages",
        f"/messages/m/{message.id}/modifier",
        f"/messages/photos/{message.id}",
    ):
        response = outsider.get(path)
        assert response.status_code == 404, path
        assert "Secret" not in response.text
    assert _send(outsider, cid, "Je m'incruste").status_code == 404
    assert (
        outsider.post(f"/messages/m/{message.id}/modifier", data={"content": "x"}).status_code
        == 404
    )
    assert outsider.post(f"/messages/m/{message.id}/supprimer").status_code == 404
    assert "Secret" not in outsider.get("/messages").text
    assert "Secret" not in outsider.get("/notifications").text
    assert [m.content for m in _messages(db)] == ["Secret entre nous"]
    with pytest.raises(NotFound):
        messages_service.get_conversation(db, chloe, cid)


def test_rg46_admin_et_visiteur_n_ont_pas_acces(login, anonymous, db, alice, bob, admin):
    client = login(alice)
    cid = _open(client, bob)
    _send(client, cid, "Privé")
    admin_client = login(admin)
    for path in ("/messages", "/messages/bulle", "/messages/nouveau", f"/messages/{cid}"):
        assert admin_client.get(path).status_code == 403, path
        response = anonymous.get(path)
        assert response.status_code == 303 and response.headers["location"] == "/login"
    assert _send(admin_client, cid, "x").status_code == 403
    for path in ("/admin", "/admin/cadeaux"):  # ni bulle ni message dans le panel
        html = admin_client.get(path).text
        assert "msg-dock" not in html and "Privé" not in html
    with pytest.raises(NotFound):
        messages_service.get_conversation(db, admin, cid)


def test_rg47_envoi_protege_par_csrf(login, alice, bob):
    client = login(alice)
    cid = _open(client, bob)
    del client.headers["X-CSRF-Token"]
    assert _send(client, cid, "sans jeton").status_code == 403


# --- US-30 : non-lus, bulle et cloche (RG-50, RG-55) --------------------------


def test_us30_bulle_et_cloche_signalent_les_messages(login, alice, bob, chloe):
    alice_client, bob_client = login(alice), login(bob)
    assert 'id="msg-dock"' in bob_client.get("/").text  # la bulle est sur les pages membre
    assert _bubble(bob_client) is None and _bell(bob_client) is None
    cid = _open(alice_client, bob)
    _send(alice_client, cid, "Un")
    _send(alice_client, cid, "Deux")
    assert _bubble(bob_client) == "2"  # la bulle compte les messages
    assert _bell(bob_client) == "1"  # la cloche compte une ligne par conversation
    assert _bell(bob_client, f"/personnes/{alice.id}") == "1"
    assert _bubble(alice_client) is None and _bell(alice_client) is None  # pas ses propres messages
    _send(login(chloe), _open(login(chloe), bob), "Trois")
    assert _bubble(bob_client) == "3" and _bell(bob_client) == "2"


def test_us30_page_notifications_liste_sans_marquer_lu(login, alice, bob):
    alice_client, bob_client = login(alice), login(bob)
    cid = _open(alice_client, bob)
    _send(alice_client, cid, "Un")
    html = bob_client.get("/notifications").text
    assert "t'a envoyé un message" in html and f'href="/messages/{cid}"' in html
    _send(alice_client, cid, "Deux")
    assert "t'a envoyé 2 messages" in bob_client.get("/notifications").text
    assert _bell(bob_client) == "1"  # RG-50 : seule l'ouverture de la conversation marque lu
    assert "t'a envoyé" not in alice_client.get("/notifications").text


def test_us30_ouvrir_la_conversation_marque_lu(login, alice, bob, chloe):
    alice_client, bob_client, chloe_client = login(alice), login(bob), login(chloe)
    with_alice = _open(alice_client, bob)
    _send(alice_client, with_alice, "Un")
    _send(chloe_client, _open(chloe_client, bob), "Deux")
    bob_client.get(f"/messages/{with_alice}")
    assert _bubble(bob_client) == "1" and _bell(bob_client) == "1"  # reste celle de Chloé
    assert "t'a envoyé" in bob_client.get("/notifications").text
    _send(alice_client, with_alice, "Trois")
    assert _bubble(bob_client) == "2"
    bob_client.get(f"/messages/{with_alice}/fil", headers=HX)  # conversation restée ouverte
    assert _bubble(bob_client) == "1"


def test_us30_fragment_de_la_bulle_met_a_jour_la_cloche(login, alice, bob):
    alice_client, bob_client = login(alice), login(bob)
    _send(alice_client, _open(alice_client, bob), "Coucou")
    html = bob_client.get("/messages/bulle", headers=HX).text
    assert _BUBBLE_RE.search(html).group(1) == "1"
    assert 'id="bell-count" hx-swap-oob="true"' in html
    assert _BELL_RE.search(html).group(1) == "1"


def test_us30_fil_inchange_ne_renvoie_rien(login, alice, bob):
    alice_client, bob_client = login(alice), login(bob)
    cid = _open(alice_client, bob)
    _send(alice_client, cid, "Un")
    html = bob_client.get(f"/messages/{cid}/fil", headers=HX).text
    version = re.search(r"/fil\?v=(\w+)", html).group(1)
    assert bob_client.get(f"/messages/{cid}/fil?v={version}", headers=HX).status_code == 204
    _send(alice_client, cid, "Deux")
    response = bob_client.get(f"/messages/{cid}/fil?v={version}", headers=HX)
    assert response.status_code == 200 and "Deux" in response.text


# --- US-31 : modifier et supprimer ses messages (RG-49) -----------------------


def test_us31_modifier_son_message(login, db, alice, bob):
    alice_client, bob_client = login(alice), login(bob)
    cid = _open(alice_client, bob)
    _send(alice_client, cid, "Brouillon")
    message = _messages(db)[0]
    assert "(modifié)" not in bob_client.get(f"/messages/{cid}").text
    assert "Brouillon" in alice_client.get(f"/messages/m/{message.id}/modifier").text
    response = alice_client.post(f"/messages/m/{message.id}/modifier", data={"content": "Corrigé"})
    assert response.status_code == 303
    html = bob_client.get(f"/messages/{cid}").text
    assert "Corrigé" in html and "Brouillon" not in html and "(modifié)" in html
    empty = alice_client.post(f"/messages/m/{message.id}/modifier", data={"content": " "})
    assert empty.status_code == 422
    assert _messages(db)[0].content == "Corrigé"


def test_us31_seul_l_auteur_modifie_ou_supprime(login, db, alice, bob):
    alice_client, bob_client = login(alice), login(bob)
    cid = _open(alice_client, bob)
    _send(alice_client, cid, "À moi")
    message = _messages(db)[0]
    assert bob_client.get(f"/messages/m/{message.id}/modifier").status_code == 403
    assert (
        bob_client.post(f"/messages/m/{message.id}/modifier", data={"content": "x"}).status_code
        == 403
    )
    assert bob_client.post(f"/messages/m/{message.id}/supprimer").status_code == 403
    assert [m.content for m in _messages(db)] == ["À moi"]
    html = bob_client.get(f"/messages/{cid}").text
    assert (
        f"/messages/m/{message.id}/supprimer" not in html
    )  # pas d'action sur le message d'un autre


def test_us31_supprimer_ne_laisse_aucune_trace(login, db, alice, bob):
    alice_client, bob_client = login(alice), login(bob)
    cid = _open(alice_client, bob)
    _send(alice_client, cid, "Oups")
    message = _messages(db)[0]
    assert alice_client.post(f"/messages/m/{message.id}/supprimer").status_code == 303
    assert _messages(db) == []
    assert "Oups" not in bob_client.get(f"/messages/{cid}").text
    assert _bubble(bob_client) is None


def test_us31_non_lus_justes_apres_une_suppression(login, db, alice, bob):
    """Un identifiant de message n'est jamais réutilisé : le suivant reste non lu."""
    alice_client, bob_client = login(alice), login(bob)
    cid = _open(alice_client, bob)
    _send(alice_client, cid, "Un")
    bob_client.get(f"/messages/{cid}")
    alice_client.post(f"/messages/m/{_messages(db)[0].id}/supprimer")
    _send(alice_client, cid, "Deux")
    assert _bubble(bob_client) == "1"


# --- US-32 : « Vu » (RG-51) ---------------------------------------------------


def test_us32_vu_sous_mon_dernier_message(login, alice, bob):
    alice_client, bob_client = login(alice), login(bob)
    cid = _open(alice_client, bob)
    _send(alice_client, cid, "Tu as vu ?")
    assert "msg-seen" not in alice_client.get(f"/messages/{cid}").text
    assert (
        "msg-seen" not in bob_client.get(f"/messages/{cid}").text
    )  # Bob lit : pas de « Vu » chez lui
    assert "msg-seen" in alice_client.get(f"/messages/{cid}").text
    _send(bob_client, cid, "Oui !")
    assert (
        "msg-seen" not in alice_client.get(f"/messages/{cid}").text
    )  # le dernier n'est plus le sien


def test_us32_vu_par_dans_un_groupe(login, alice, bob, chloe):
    alice_client = login(alice)
    cid = _group(alice_client, "Cadeau Mamie", bob, chloe)
    _send(alice_client, cid, "Qui participe ?")
    login(bob).get(f"/messages/{cid}")
    html = alice_client.get(f"/messages/{cid}").text
    assert re.search(r'msg-seen">\s*Vu par Bob\s*<', html)


# --- US-33 : « En ligne » (RG-52) ---------------------------------------------


def test_us33_libelle_de_presence(db, alice):
    now = utcnow()
    assert messages_service.presence(alice, now) == ""  # jamais vue
    for delta, label in (
        (timedelta(seconds=30), "En ligne"),
        (timedelta(minutes=7), "En ligne il y a 7 min"),
        (timedelta(hours=3), "En ligne il y a 3 h"),
        (timedelta(days=2), "En ligne il y a 2 j"),
        (timedelta(days=15), "En ligne il y a 2 sem."),
    ):
        alice.last_seen_at = now - delta
        assert messages_service.presence(alice, now) == label
    alice.is_active = False
    assert messages_service.presence(alice, now) == "Compte désactivé"


def test_us33_naviguer_met_a_jour_la_presence(login, db, alice, bob):
    assert alice.last_seen_at is None
    alice_client = login(alice)
    alice_client.get("/")
    db.expire_all()
    assert db.get(User, alice.id).last_seen_at is not None
    cid = _open(login(bob), alice)
    assert re.search(r'id="msg-status">\s*En ligne\s*<', login(bob).get(f"/messages/{cid}").text)
    seen = db.get(User, alice.id)
    seen.last_seen_at = utcnow() - timedelta(minutes=7)
    db.commit()
    assert "En ligne il y a 7 min" in login(bob).get(f"/messages/{cid}").text


# --- US-34 : photos (RG-47, RG-48) --------------------------------------------


def _photo(name: str = "p.png", data: bytes | None = None) -> dict:
    return {"photo": (name, data or png_bytes(), "image/png")}


def test_us34_envoyer_une_photo_reservee_aux_participants(login, db, alice, bob, chloe):
    alice_client = login(alice)
    cid = _open(alice_client, bob)
    assert _send(alice_client, cid, "", files=_photo()).status_code == 303  # photo seule acceptée
    message = _messages(db)[0]
    assert message.content == "" and message.image_path.startswith("messages/")
    assert (settings.private_media_dir / message.image_path).is_file()
    assert not (settings.media_dir / message.image_path).exists()  # jamais dans le dossier public
    assert f'src="/messages/photos/{message.id}"' in login(bob).get(f"/messages/{cid}").text
    photo = login(bob).get(f"/messages/photos/{message.id}")
    assert photo.status_code == 200 and photo.headers["content-type"] == "image/webp"
    assert login(chloe).get(f"/messages/photos/{message.id}").status_code == 404
    assert alice_client.get(f"/media/{message.image_path}").status_code == 404
    assert "Photo" in login(bob).get("/messages").text  # aperçu dans la liste


def test_us34_fichier_refuse_et_photo_supprimee_avec_le_message(login, db, alice, bob):
    client = login(alice)
    cid = _open(client, bob)
    bad = _send(client, cid, "regarde", files=_photo("x.png", b"pas une image"), headers=HX)
    assert bad.status_code == 422 and _messages(db) == []
    _send(client, cid, "regarde", files=_photo())
    message = _messages(db)[0]
    path = settings.private_media_dir / message.image_path
    # un message avec photo peut perdre son texte
    assert (
        client.post(f"/messages/m/{message.id}/modifier", data={"content": ""}).status_code == 303
    )
    client.post(f"/messages/m/{message.id}/supprimer")
    assert not path.exists()


# --- US-35 : groupes (RG-53) --------------------------------------------------


def test_us35_creer_un_groupe(login, db, alice, bob, chloe, admin):
    client = login(alice)
    for data in (
        {"name": " ", "members": [bob.id]},
        {"name": "Vide", "members": []},
        {"name": "Seule", "members": [alice.id, admin.id, 9999]},  # ni soi, ni l'admin
        {"name": "x" * 61, "members": [bob.id]},
    ):
        assert client.post("/messages/groupes", data=data).status_code == 422
    assert db.scalars(select(Conversation)).all() == []
    cid = _group(client, "  Cadeau   Mamie ", bob, chloe)
    group = db.get(Conversation, cid)
    assert group.is_group and group.name == "Cadeau Mamie" and group.creator_id == alice.id
    assert {m.user_id for m in group.members} == {alice.id, bob.id, chloe.id}
    _send(client, cid, "Bienvenue")
    for member in (bob, chloe):
        member_client = login(member)
        assert "Cadeau Mamie" in member_client.get("/messages").text
        assert "1 nouveau message dans « Cadeau Mamie »" in member_client.get("/notifications").text
        assert "Bienvenue" in member_client.get(f"/messages/{cid}").text
    # un groupe à deux reste distinct de la conversation à deux
    assert _group(client, "Duo", bob) != _open(client, bob)


def test_us35_ajouter_retirer_quitter(login, db, alice, bob, chloe):
    dorian = _user(db, "Dorian")
    alice_client, bob_client = login(alice), login(bob)
    cid = _group(alice_client, "Cadeau Mamie", bob)
    _send(alice_client, cid, "Historique")
    base = f"/messages/{cid}"

    # Tout participant ajoute ; le nouveau voit l'historique, sans rien de non lu.
    assert bob_client.post(f"{base}/membres", data={"user_id": chloe.id}).status_code == 303
    assert (
        bob_client.post(f"{base}/membres", data={"user_id": chloe.id}).status_code == 422
    )  # déjà là
    chloe_client = login(chloe)
    assert "Historique" in chloe_client.get(base, headers=HX).text
    db.expire_all()
    member = db.get(ConversationMember, (cid, chloe.id))
    assert messages_service.unread_count(db.get(Conversation, cid), chloe) == 0
    assert member.last_read_message_id == _messages(db)[-1].id

    # Seul le créateur renomme ou retire.
    assert bob_client.post(f"{base}/nom", data={"name": "Pirate"}).status_code == 403
    assert bob_client.post(f"{base}/membres/{chloe.id}/retirer").status_code == 403
    assert alice_client.post(f"{base}/nom", data={"name": "Cadeau Papi"}).status_code == 303
    assert alice_client.post(f"{base}/nom", data={"name": ""}).status_code == 422
    assert alice_client.post(f"{base}/membres/{chloe.id}/retirer").status_code == 303
    assert chloe_client.get(base).status_code == 404  # retirée : plus aucun accès
    assert _send(chloe_client, cid, "encore là ?").status_code == 404
    assert login(dorian).get(base).status_code == 404

    # Le créateur qui part passe la main ; le dernier qui part supprime le groupe.
    assert alice_client.post(f"{base}/quitter").status_code == 303
    db.expire_all()
    group = db.get(Conversation, cid)
    assert group.name == "Cadeau Papi" and group.creator_id == bob.id
    assert alice_client.get(base).status_code == 404
    assert "Historique" in bob_client.get(base).text  # ses messages restent
    assert bob_client.post(f"{base}/quitter").status_code == 303
    db.expire_all()
    assert db.get(Conversation, cid) is None and _messages(db) == []


def test_us35_reglages_reserves_aux_groupes(login, alice, bob):
    client = login(alice)
    cid = _open(client, bob)
    assert client.get(f"/messages/{cid}/reglages").status_code == 404
    assert client.post(f"/messages/{cid}/quitter").status_code == 404
    assert client.post(f"/messages/{cid}/membres", data={"user_id": bob.id}).status_code == 404
    gid = _group(client, "Groupe", bob)
    html = client.get(f"/messages/{gid}/reglages").text
    assert "Renommer" in html and "Retirer" in html
    theirs = login(bob).get(f"/messages/{gid}/reglages").text
    assert "Renommer" not in theirs and "Retirer" not in theirs and "Quitter le groupe" in theirs


# --- RG-54 : compte désactivé -------------------------------------------------


def test_rg54_compte_desactive(login, db, alice, bob, chloe):
    alice_client = login(alice)
    cid = _open(alice_client, bob)
    gid = _group(alice_client, "Groupe", bob, chloe)
    _send(alice_client, cid, "Avant")
    bob.is_active = False
    db.commit()
    html = alice_client.get(f"/messages/{cid}").text
    assert "Avant" in html and "Compte désactivé" in html  # toujours lisible
    assert "data-msg-form" not in html
    refused = _send(alice_client, cid, "Après", headers=HX)
    assert refused.status_code == 422 and "désactivé" in refused.text
    assert [m.content for m in _messages(db)] == ["Avant"]
    assert f"/messages/avec/{bob.id}" not in alice_client.get("/messages/nouveau").text
    assert _send(alice_client, gid, "Le groupe continue").status_code == 303


# --- RG-41, RG-54 : suppression d'un compte -----------------------------------


def test_us26_supprimer_un_compte_emporte_ses_messages(login, db, admin, alice, bob, chloe):
    alice_client, bob_client = login(alice), login(bob)
    direct = _open(alice_client, bob)
    _send(alice_client, direct, "Alice à Bob", files=_photo())
    _send(bob_client, direct, "Bob à Alice", files=_photo())
    group = _group(alice_client, "Cadeau Mamie", bob, chloe)
    _send(alice_client, group, "Alice au groupe", files=_photo())
    _send(bob_client, group, "Bob au groupe")
    quitte = _group(bob_client, "Ancien groupe", alice)
    _send(alice_client, quitte, "Avant de partir")
    alice_client.post(f"/messages/{quitte}/quitter")
    seule = _group(alice_client, "Bientôt seule", bob)
    bob_client.post(f"/messages/{seule}/quitter")
    photos = [settings.private_media_dir / m.image_path for m in _messages(db) if m.image_path]
    assert len(photos) == 3 and all(p.is_file() for p in photos)
    alice_id = alice.id

    response = login(admin).post(f"/admin/membres/{alice_id}/supprimer", data={"confirm": "1"})
    assert response.status_code == 303
    db.expire_all()

    assert db.get(User, alice_id) is None
    assert db.get(Conversation, direct) is None  # la conversation à deux disparaît en entier
    assert db.get(Conversation, seule) is None  # groupe resté sans participant
    assert [m.content for m in _messages(db)] == ["Bob au groupe"]
    assert not any(p.exists() for p in photos)
    kept = db.get(Conversation, group)
    assert kept.creator_id == bob.id  # le groupe continue, Bob en devient le créateur
    assert {m.user_id for m in kept.members} == {bob.id, chloe.id}
    assert (
        db.scalars(select(ConversationMember).where(ConversationMember.user_id == alice_id)).all()
        == []
    )
    html = bob_client.get("/messages").text
    assert "Cadeau Mamie" in html and "Alice" not in html
