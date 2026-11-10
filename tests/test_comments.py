"""US-20 à US-22 : commentaires d'un cadeau."""

from datetime import timedelta

import pytest
from sqlalchemy import select

from app.models import Comment, utcnow

HTMX = {"HX-Request": "true"}


@pytest.fixture
def gift(make_gift, bob):
    return make_gift(bob, bob, "Vélo")


def _comments(db):
    db.expire_all()
    return db.scalars(select(Comment).order_by(Comment.id)).all()


def test_us20_fil_chronologique_avec_placeholder(login, db, alice, chloe, gift):
    gift.comments.append(Comment(author_id=chloe.id, content="Deuxième", created_at=utcnow()))
    gift.comments.append(
        Comment(author_id=alice.id, content="Premier", created_at=utcnow() - timedelta(hours=1))
    )
    db.commit()
    html = login(alice).get(f"/cadeaux/{gift.id}/commentaires").text
    assert html.index("Premier") < html.index("Deuxième")
    assert "chat__msg--mine" in html and "avatar--c" in html
    assert 'hx-trigger="every 20s"' in html


def test_us20_contenu_echappe(login, db, alice, gift):
    login(alice).post(
        f"/cadeaux/{gift.id}/commentaires", data={"content": "<script>alert(1)</script>"}
    )
    html = login(alice).get(f"/cadeaux/{gift.id}/commentaires/fil").text
    assert "<script>alert(1)" not in html and "&lt;script&gt;" in html


def test_us21_message_ajoute_et_badge(login, db, alice, chloe, gift):
    response = login(alice).post(
        f"/cadeaux/{gift.id}/commentaires", data={"content": "Je le prends 🎁"}, headers=HTMX
    )
    assert response.status_code == 200 and "Je le prends 🎁" in response.text
    (comment,) = _comments(db)
    assert comment.author_id == alice.id and comment.content == "Je le prends 🎁"
    assert (
        '<span class="badge">1</span>' in login(chloe).get(f"/personnes/{gift.recipient_id}").text
    )


@pytest.mark.parametrize("content", ["", "   \n  ", "x" * 1001])
def test_us21_message_vide_ou_trop_long_refuse(login, db, alice, gift, content):
    client = login(alice)
    assert (
        client.post(f"/cadeaux/{gift.id}/commentaires", data={"content": content}).status_code
        == 422
    )
    response = client.post(
        f"/cadeaux/{gift.id}/commentaires", data={"content": content}, headers=HTMX
    )
    assert response.status_code == 422 and "alert--error" in response.text
    assert _comments(db) == []


def test_us21_mille_caracteres_acceptes(login, db, alice, gift):
    login(alice).post(f"/cadeaux/{gift.id}/commentaires", data={"content": "x" * 1000})
    assert len(_comments(db)) == 1


def test_us22_modifier_mon_message(login, db, alice, chloe, gift):
    client = login(alice)
    client.post(f"/cadeaux/{gift.id}/commentaires", data={"content": "Avant"})
    (comment,) = _comments(db)
    html = client.get(f"/cadeaux/{gift.id}/commentaires").text
    assert f"/commentaires/{comment.id}/modifier" in html
    # Les actions ne sont pas proposées aux autres
    assert (
        f"/commentaires/{comment.id}/modifier"
        not in login(chloe).get(f"/cadeaux/{gift.id}/commentaires").text
    )
    assert (
        client.post(f"/commentaires/{comment.id}/modifier", data={"content": " "}).status_code
        == 422
    )
    client.post(f"/commentaires/{comment.id}/modifier", data={"content": "Après"})
    html = client.get(f"/cadeaux/{gift.id}/commentaires/fil").text
    assert "Après" in html and "(modifié)" in html and "Avant" not in html


def test_us22_message_d_un_autre_interdit(login, db, alice, chloe, gift):
    login(alice).post(f"/cadeaux/{gift.id}/commentaires", data={"content": "À Alice"})
    (comment,) = _comments(db)
    client = login(chloe)
    assert client.get(f"/commentaires/{comment.id}/modifier").status_code == 403
    assert (
        client.post(f"/commentaires/{comment.id}/modifier", data={"content": "x"}).status_code
        == 403
    )
    assert client.post(f"/commentaires/{comment.id}/supprimer").status_code == 403
    assert _comments(db)[0].content == "À Alice"


def test_us22_supprimer_mon_message(login, db, alice, gift):
    client = login(alice)
    client.post(f"/cadeaux/{gift.id}/commentaires", data={"content": "Oups"})
    (comment,) = _comments(db)
    response = client.post(f"/commentaires/{comment.id}/supprimer", headers=HTMX)
    assert response.status_code == 200 and "Oups" not in response.text
    assert _comments(db) == []
    assert "badge" not in client.get(f"/personnes/{gift.recipient_id}").text
