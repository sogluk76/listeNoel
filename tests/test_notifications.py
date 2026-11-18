"""US-27, US-28 : mentions « @Prénom » dans les commentaires et notifications (RG-42 à RG-45)."""

import re

import pytest
from sqlalchemy import select

from app.models import Comment, Notification
from app.services import notifications as notifications_service

_COUNT_RE = re.compile(r'app-header__bell-count">\s*([^<\s]+)\s*<')


@pytest.fixture
def gift(make_gift, chloe):
    """Cadeau de la liste de Chloé : Alice et Bob voient le fil, pas Chloé."""
    return make_gift(chloe, chloe, "Vélo")


def _bell(client, path: str = "/") -> str | None:
    """Nombre affiché sur la cloche, ou None s'il n'y a pas de pastille."""
    html = client.get(path).text
    assert "app-header__bell" in html
    match = _COUNT_RE.search(html)
    return match.group(1) if match else None


def _post(client, gift, content: str):
    return client.post(f"/cadeaux/{gift.id}/commentaires", data={"content": content})


def _notified(db) -> list[int]:
    db.expire_all()
    return sorted(db.scalars(select(Notification.user_id)).all())


# --- Détection des mentions (RG-42) -------------------------------------------


def test_us27_split_reconnait_les_prenoms(alice, bob, chloe):
    members = [alice, bob, chloe]

    def names(text):
        return [m.first_name for m in notifications_service.mentioned(text, members)]

    assert names("@Bob tu en penses quoi ?") == ["Bob"]
    assert names("coucou @bob, et @CHLOE aussi") == ["Bob", "Chloé"]  # casse et accents
    assert names("@Bob @bob @BOB") == ["Bob"]  # une seule fois
    assert names("(@Alice)") == ["Alice"]
    assert names("@Bobby et @Alicia") == []  # prénom plus long : ce n'est pas Bob
    assert names("ecris a truc@bob.fr") == []  # une adresse mail n'est pas une mention
    assert names("@ Bob, Bob, @Inconnu") == []
    parts = notifications_service.split("Hé @bob !", members)
    assert [(text, m.first_name if m else None) for text, m in parts] == [
        ("Hé ", None),
        ("@bob", "Bob"),
        (" !", None),
    ]


def test_us27_prenom_compose_le_plus_long_gagne(db, alice):
    from tests.conftest import _user

    jean = _user(db, "Jean")
    jean_pierre = _user(db, "Jean Pierre")
    found = notifications_service.mentioned("@jean pierre et @Jean", [alice, jean, jean_pierre])
    assert [m.first_name for m in found] == ["Jean Pierre", "Jean"]


# --- Création des notifications (RG-42, RG-44) --------------------------------


def test_us27_mention_cree_une_notification_et_la_cloche_compte(login, db, alice, bob, gift):
    bob_client = login(bob)
    assert _bell(bob_client) is None
    _post(login(alice), gift, "@Bob tu participes ?")
    _post(login(alice), gift, "et encore @bob")
    assert _notified(db) == [bob.id, bob.id]
    assert _bell(bob_client) == "2"
    assert _bell(bob_client, f"/personnes/{alice.id}") == "2"  # sur toutes les pages
    assert _bell(login(alice)) is None  # l'auteur n'est pas notifié


def test_us27_pas_de_notification_pour_soi_ni_en_double(login, db, alice, bob, gift):
    _post(login(alice), gift, "note pour moi @Alice, et @Bob @Bob @bob")
    assert _notified(db) == [bob.id]


def test_us27_mention_mise_en_valeur_et_contenu_toujours_echappe(login, db, alice, bob, gift):
    _post(login(alice), gift, "<b>@bob</b> regarde <script>x</script>")
    html = login(bob).get(f"/cadeaux/{gift.id}/commentaires/fil").text
    assert '<span class="mention">@Bob</span>' in html
    assert "<script>x" not in html and "&lt;b&gt;" in html


def test_us27_modifier_un_message_met_a_jour_les_notifications(login, db, alice, bob, gift):
    client = login(alice)
    _post(client, gift, "Bonjour")
    comment = db.scalar(select(Comment))
    assert _notified(db) == []

    client.post(f"/commentaires/{comment.id}/modifier", data={"content": "Bonjour @Bob"})
    assert _notified(db) == [bob.id]
    client.post(f"/commentaires/{comment.id}/modifier", data={"content": "Bonjour @Bob !!"})
    assert _notified(db) == [bob.id]  # pas de doublon
    client.post(f"/commentaires/{comment.id}/modifier", data={"content": "Bonjour"})
    assert _notified(db) == []  # mention retirée : notification retirée


def test_us27_supprimer_le_message_supprime_la_notification(login, db, alice, bob, gift):
    client = login(alice)
    _post(client, gift, "@Bob ?")
    comment = db.scalar(select(Comment))
    assert _bell(login(bob)) == "1"
    client.post(f"/commentaires/{comment.id}/supprimer")
    assert _notified(db) == []
    assert _bell(login(bob)) is None


def test_us27_membre_desactive_non_notifie(login, db, alice, bob, gift):
    bob.is_active = False
    db.commit()
    _post(login(alice), gift, "@Bob tu es là ?")
    assert _notified(db) == []


# --- Page des notifications (RG-45) -------------------------------------------


def test_us28_page_liste_puis_marque_comme_lu(login, db, alice, bob, chloe, gift):
    _post(login(alice), gift, "@Bob on se cotise pour le vélo ?")
    comment = db.scalar(select(Comment))
    client = login(bob)

    html = client.get("/notifications").text
    assert "Alice" in html and "t'a mentionné" in html and "Vélo" in html
    assert "on se cotise" in html and "Nouveau" in html
    assert f'href="/cadeaux/{gift.id}/commentaires#c{comment.id}"' in html
    assert _COUNT_RE.search(html) is None  # ouvrir la page remet le compteur à zéro

    assert _bell(client) is None
    again = client.get("/notifications").text
    assert "on se cotise" in again and "Nouveau" not in again  # reste listée, mais lue
    assert f'id="c{comment.id}"' in client.get(f"/cadeaux/{gift.id}/commentaires").text


def test_us28_page_vide(login, alice):
    html = login(alice).get("/notifications").text
    assert "Aucune notification" in html


def test_us28_chacun_ne_voit_que_les_siennes(login, db, alice, bob, make_gift, chloe, gift):
    _post(login(alice), gift, "SECRET-POUR-BOB @Bob")
    assert "SECRET-POUR-BOB" not in login(alice).get("/notifications").text
    assert "SECRET-POUR-BOB" in login(bob).get("/notifications").text


def test_us28_reserve_aux_membres(login, anonymous, admin):
    assert anonymous.get("/notifications").headers["location"] == "/login"
    admin_client = login(admin)
    assert admin_client.get("/notifications").status_code == 403
    assert "app-header__bell" not in admin_client.get("/admin").text


# --- Aide à la saisie : liste de prénoms et clic sur un auteur (US-27, incrément 2) ---

_NAMES_RE = re.compile(r"data-mentions='([^']*)'")


def _proposed(html: str) -> list[str]:
    import json

    return json.loads(_NAMES_RE.search(html).group(1))


def test_us27_saisie_propose_les_autres_membres_sauf_le_destinataire(
    login, db, alice, bob, chloe, gift
):
    from tests.conftest import _user

    _user(db, "Dorian").is_active = False
    db.commit()
    html = login(alice).get(f"/cadeaux/{gift.id}/commentaires").text
    assert '<script src="/static/js/mentions.js" defer></script>' in html
    # Ni moi (Alice), ni la destinataire (Chloé, RG-43), ni un compte désactivé.
    assert _proposed(html) == ["Bob"]


def test_us27_page_de_modification_propose_aussi_les_prenoms(login, db, alice, bob, gift):
    client = login(alice)
    _post(client, gift, "Bonjour")
    comment = db.scalar(select(Comment))
    html = client.get(f"/commentaires/{comment.id}/modifier").text
    assert "mentions.js" in html and _proposed(html) == ["Bob"]
    refused = client.post(f"/commentaires/{comment.id}/modifier", data={"content": "  "})
    assert refused.status_code == 422 and _proposed(refused.text) == ["Bob"]


def test_us27_prenom_d_un_auteur_cliquable_pour_le_mentionner(login, db, alice, bob, gift):
    _post(login(alice), gift, "Message d'Alice")
    _post(login(bob), gift, "Message de Bob")
    html = login(bob).get(f"/cadeaux/{gift.id}/commentaires/fil").text
    assert 'data-mention="Alice"' in html  # l'auteur d'un autre message
    assert 'data-mention="Bob"' not in html  # pas mon propre prénom
    assert "<strong>Bob</strong>" in html

    alice.is_active = False  # un compte désactivé ne peut plus être mentionné
    db.commit()
    html = login(bob).get(f"/cadeaux/{gift.id}/commentaires/fil").text
    assert "data-mention=" not in html and "<strong>Alice</strong>" in html


def test_us27_prenom_avec_apostrophe_ou_guillemet_reste_inoffensif(login, db, alice, gift):
    from tests.conftest import _user

    _user(db, """O'Neil "x" <b>""")
    html = login(alice).get(f"/cadeaux/{gift.id}/commentaires").text
    assert _proposed(html) == ["""O'Neil "x" <b>"""]
    assert "<b>" not in _NAMES_RE.search(html).group(1)


def test_us28_ouvrir_le_fil_marque_ses_mentions_comme_lues(
    login, db, alice, bob, chloe, make_gift, gift
):
    """RG-45 : la notification part aussi quand on ouvre le fil concerné, et seulement lui."""
    autre = make_gift(alice, alice, "Livre")
    _post(login(alice), gift, "PREMIER-FIL @Bob")
    _post(login(chloe), autre, "AUTRE-FIL @Bob")
    client = login(bob)
    assert _bell(client) == "2"

    page = client.get(f"/cadeaux/{gift.id}/commentaires").text
    assert _COUNT_RE.search(page).group(1) == "1"  # déjà décompté sur la page du fil
    assert _bell(client) == "1"

    html = client.get("/notifications").text
    assert "PREMIER-FIL" in html and "AUTRE-FIL" in html  # toujours listées
    assert html.count("Nouveau") == 1  # seule celle de l'autre fil était encore non lue


def test_us28_le_rafraichissement_du_fil_ne_marque_pas_comme_lu(login, db, alice, bob, gift):
    _post(login(alice), gift, "@Bob ?")
    client = login(bob)
    client.get(f"/cadeaux/{gift.id}/commentaires/fil")  # fragment rechargé toutes les 20 s
    client.get(f"/cadeaux/{gift.id}")  # page de détail du cadeau
    assert _bell(client) == "1"


# --- Nouveau cadeau (RG-57) ----------------------------------------------------


def _create(client, name: str, recipient=None):
    data = {"name": name}
    if recipient is not None:
        data.update(suggest="1", recipient_id=recipient.id)
    response = client.post("/cadeaux", data=data)
    assert response.status_code == 303, response.text


def _gift_notified(db) -> list[int]:
    db.expire_all()
    return sorted(
        db.scalars(select(Notification.user_id).where(Notification.gift_id.is_not(None))).all()
    )


def test_rg57_cadeau_sur_sa_liste_notifie_les_autres_membres(login, db, alice, bob, chloe):
    _create(login(alice), "Puzzle 1000 pièces")
    assert _gift_notified(db) == sorted([bob.id, chloe.id])  # pas l'auteur
    html = login(bob).get("/notifications").text
    assert "<strong>Alice</strong> a ajouté « Puzzle 1000 pièces » à sa liste" in html
    assert _bell(login(chloe)) == "1"
    assert _bell(login(alice)) is None


def test_rg57_suggestion_notifie_tout_le_monde_sauf_auteur_et_destinataire(
    login, db, alice, bob, chloe
):
    _create(login(alice), "Casque audio", recipient=chloe)
    assert _gift_notified(db) == [bob.id]
    assert "<strong>Alice</strong> a suggéré « Casque audio » pour Chloé" in (
        login(bob).get("/notifications").text
    )


def test_rg57_compte_desactive_et_admin_non_notifies(login, db, alice, bob, chloe, admin):
    chloe.is_active = False
    db.commit()
    _create(login(alice), "Vélo")
    assert _gift_notified(db) == [bob.id]


def test_rg57_la_ligne_mene_au_cadeau_et_l_ouvrir_la_marque_lue(login, db, alice, bob):
    _create(login(alice), "Vélo")
    _create(login(alice), "Livre")
    db.expire_all()
    velo = db.scalar(select(Notification).where(Notification.gift_id.is_not(None))).gift
    client = login(bob)
    assert _bell(client) == "2"
    client.get(f"/cadeaux/{velo.id}")  # la fiche marque seulement ce cadeau comme lu
    assert _bell(client) == "1"
    html = client.get("/notifications").text
    assert f'href="/cadeaux/{velo.id}"' in html
    assert _bell(client) is None  # la page marque tout comme lu


def test_rg57_modifier_le_cadeau_ne_notifie_pas(login, db, alice, bob):
    client = login(alice)
    _create(client, "Vélo")
    db.expire_all()
    gift = db.scalar(select(Notification)).gift
    client.post(f"/cadeaux/{gift.id}/modifier", data={"name": "Vélo rouge"})
    assert _gift_notified(db) == [bob.id]


def test_rg57_notification_supprimee_ou_masquee_avec_le_cadeau(login, db, alice, bob, chloe):
    client = login(alice)
    _create(client, "Vélo")
    _create(client, "Livre")
    db.expire_all()
    velo, livre = sorted(
        (n.gift for n in db.scalars(select(Notification).where(Notification.user_id == bob.id))),
        key=lambda g: g.name,
    )[::-1]
    # Sans activité : suppression définitive, la notification part avec le cadeau.
    client.post(f"/cadeaux/{velo.id}/supprimer")
    assert _gift_notified(db) == sorted([bob.id, chloe.id])
    # Avec activité : retrait doux, la notification n'est plus affichée ni comptée.
    login(bob).post(f"/cadeaux/{livre.id}/commentaires", data={"content": "je regarde"})
    client.post(f"/cadeaux/{livre.id}/supprimer")
    bob_client = login(bob)
    assert _bell(bob_client) is None
    assert "Livre" not in bob_client.get("/notifications").text
