"""Listes de courses partagées (RG-59 à RG-61)."""

import pytest
from sqlalchemy import select

from app.models import ShoppingItem, ShoppingList

HTMX = {"HX-Request": "true"}


def _create_list(client, name: str = "Repas du 24") -> int:
    response = client.post("/courses", data={"name": name})
    assert response.status_code == 303, response.text
    return int(response.headers["location"].rsplit("/", 1)[1])


def _add(client, list_id: int, name: str, quantity: str = "", headers=None):
    return client.post(
        f"/courses/{list_id}/articles",
        data={"name": name, "quantity": quantity},
        headers=headers or {},
    )


def _items(db) -> list[ShoppingItem]:
    db.expire_all()
    return db.scalars(select(ShoppingItem).order_by(ShoppingItem.id)).all()


# --- Menu et accès (RG-58, RG-59) ---------------------------------------------


def test_rg58_la_tuile_courses_est_dans_le_menu(login, alice):
    assert 'class="app-tile" href="/courses"' in login(alice).get("/").text


def test_rg59_reserve_aux_membres(anonymous, login, admin, alice):
    list_id = _create_list(login(alice))
    for path in ("/courses", f"/courses/{list_id}"):
        assert anonymous.get(path).headers["location"] == "/login"
        assert login(admin).get(path).status_code == 403
    response = login(admin).post(f"/courses/{list_id}/articles", data={"name": "Lait"})
    assert response.status_code == 403


# --- Listes (RG-59) -------------------------------------------------------------


def test_rg59_creer_une_liste_visible_par_tous(login, db, alice, bob):
    list_id = _create_list(login(alice), "  Repas   du 24 ")
    db.expire_all()
    shopping_list = db.get(ShoppingList, list_id)
    assert shopping_list.name == "Repas du 24" and shopping_list.creator_id == alice.id
    html = login(bob).get("/courses").text
    assert "Repas du 24" in html and f'href="/courses/{list_id}"' in html
    assert "Créée par Alice" in login(bob).get(f"/courses/{list_id}").text


@pytest.mark.parametrize("name", ["", "   ", "x" * 61])
def test_rg59_nom_de_liste_obligatoire_et_limite(login, db, alice, name):
    response = login(alice).post("/courses", data={"name": name})
    assert response.status_code == 422 and "field__error" in response.text
    assert db.scalars(select(ShoppingList)).all() == []


def test_rg59_liste_vide_et_aucune_liste(login, alice):
    client = login(alice)
    assert "Aucune liste pour l" in client.get("/courses").text
    list_id = _create_list(client)
    assert "La liste est vide" in client.get(f"/courses/{list_id}").text


def test_rg59_tout_membre_peut_renommer_et_supprimer(login, db, alice, bob):
    list_id = _create_list(login(alice))
    _add(login(alice), list_id, "Lait")
    client = login(bob)
    assert client.post(f"/courses/{list_id}/renommer", data={"name": " "}).status_code == 422
    client.post(f"/courses/{list_id}/renommer", data={"name": "Courses semaine"})
    assert "Courses semaine" in client.get(f"/courses/{list_id}").text
    response = client.post(f"/courses/{list_id}/supprimer")
    assert response.headers["location"] == "/courses"
    db.expire_all()
    assert db.scalars(select(ShoppingList)).all() == [] and _items(db) == []


def test_rg59_liste_inconnue_404(login, alice):
    client = login(alice)
    assert client.get("/courses/999").status_code == 404
    assert client.post("/courses/999/articles", data={"name": "Lait"}).status_code == 404


def test_rg59_ordre_des_listes_derniere_modifiee_d_abord(login, alice):
    client = login(alice)
    first = _create_list(client, "Première")
    _create_list(client, "Seconde")
    _add(client, first, "Pain")  # la première redevient la plus récente
    html = client.get("/courses").text
    assert html.index("Première") < html.index("Seconde")


# --- Articles (RG-60) -----------------------------------------------------------


def test_rg60_ajouter_un_article_avec_quantite(login, db, alice, bob):
    list_id = _create_list(login(alice))
    response = _add(login(bob), list_id, "  Pommes ", " 2 kg ")
    assert response.headers["location"] == f"/courses/{list_id}"
    (item,) = _items(db)
    assert (item.name, item.quantity, item.author_id) == ("Pommes", "2 kg", bob.id)
    html = login(alice).get(f"/courses/{list_id}").text
    assert "Pommes" in html and "2 kg" in html and "Ajouté par Bob" in html


def test_rg60_quantite_facultative(login, db, alice):
    list_id = _create_list(login(alice))
    _add(login(alice), list_id, "Lait")
    assert _items(db)[0].quantity is None


@pytest.mark.parametrize(
    ("name", "quantity"), [("", ""), ("   ", "2"), ("x" * 101, ""), ("Lait", "x" * 31)]
)
def test_rg60_article_invalide_refuse(login, db, alice, name, quantity):
    client = login(alice)
    list_id = _create_list(client)
    response = _add(client, list_id, name, quantity)
    assert response.status_code == 422 and "field__error" in response.text
    response = _add(client, list_id, name, quantity, headers=HTMX)
    assert response.status_code == 422 and 'id="shop"' in response.text
    assert "<html" not in response.text  # fragment seul
    assert _items(db) == []


def test_rg60_cocher_decocher_et_qui_a_pris(login, db, alice, bob):
    list_id = _create_list(login(alice))
    _add(login(alice), list_id, "Lait")
    item_id = _items(db)[0].id
    client = login(bob)
    client.post(f"/courses/{list_id}/articles/{item_id}/cocher")
    item = _items(db)[0]
    assert item.is_checked and item.checked_by_id == bob.id
    html = client.get(f"/courses/{list_id}").text
    assert "Dans le panier" in html and "Pris par Bob" in html
    assert "Tout est dans le panier" in html

    client.post(f"/courses/{list_id}/articles/{item_id}/cocher")
    item = _items(db)[0]
    assert not item.is_checked and item.checked_by_id is None


def test_rg60_compteur_des_articles_restants(login, db, alice):
    client = login(alice)
    list_id = _create_list(client)
    for name in ("Lait", "Pain", "Oeufs"):
        _add(client, list_id, name)
    client.post(f"/courses/{list_id}/articles/{_items(db)[0].id}/cocher")
    assert 'title="Articles à acheter">2<' in client.get("/courses").text


def test_rg60_supprimer_un_article(login, db, alice, bob):
    list_id = _create_list(login(alice))
    _add(login(alice), list_id, "Lait")
    login(bob).post(f"/courses/{list_id}/articles/{_items(db)[0].id}/supprimer")
    assert _items(db) == []


def test_rg60_retirer_les_articles_coches(login, db, alice):
    client = login(alice)
    list_id = _create_list(client)
    for name in ("Lait", "Pain", "Oeufs"):
        _add(client, list_id, name)
    lait, pain, _oeufs = _items(db)
    for item in (lait, pain):
        client.post(f"/courses/{list_id}/articles/{item.id}/cocher")
    client.post(f"/courses/{list_id}/vider")
    assert [i.name for i in _items(db)] == ["Oeufs"]


def test_rg60_article_d_une_autre_liste_404(login, db, alice):
    client = login(alice)
    first = _create_list(client, "Une")
    other = _create_list(client, "Deux")
    _add(client, first, "Lait")
    item_id = _items(db)[0].id
    assert client.post(f"/courses/{other}/articles/{item_id}/cocher").status_code == 404
    assert client.post(f"/courses/{other}/articles/{item_id}/supprimer").status_code == 404
    assert not _items(db)[0].is_checked


def test_rg60_actions_htmx_renvoient_le_fragment(login, db, alice):
    client = login(alice)
    list_id = _create_list(client)
    response = _add(client, list_id, "Lait", headers=HTMX)
    assert response.status_code == 200 and 'id="shop"' in response.text
    assert "Lait" in response.text and "<html" not in response.text
    item_id = _items(db)[0].id
    response = client.post(f"/courses/{list_id}/articles/{item_id}/cocher", headers=HTMX)
    assert "Dans le panier" in response.text
    response = client.post(f"/courses/{list_id}/vider", headers=HTMX)
    assert "La liste est vide" in response.text


def test_rg60_csrf_obligatoire(login, db, alice):
    client = login(alice)
    list_id = _create_list(client)
    del client.headers["X-CSRF-Token"]
    assert _add(client, list_id, "Lait").status_code in (400, 403)
    assert _items(db) == []


def test_rg60_contenu_echappe(login, alice):
    client = login(alice)
    list_id = _create_list(client, "<b>liste</b>")
    _add(client, list_id, "<script>x</script>")
    html = client.get(f"/courses/{list_id}").text
    assert "<script>x</script>" not in html and "&lt;script&gt;" in html
    assert "<b>liste</b>" not in client.get("/courses").text


# --- Suppression d'un compte (RG-61) ------------------------------------------


def test_rg61_les_listes_d_un_compte_supprime_restent(login, db, admin, alice, bob):
    list_id = _create_list(login(alice))
    _add(login(alice), list_id, "Lait")
    _add(login(bob), list_id, "Pain")
    lait = _items(db)[0]
    login(alice).post(f"/courses/{list_id}/articles/{lait.id}/cocher")

    response = login(admin).post(f"/admin/membres/{alice.id}/supprimer", data={"confirm": "1"})
    assert response.status_code == 303
    db.expire_all()
    shopping_list = db.get(ShoppingList, list_id)
    assert shopping_list is not None and shopping_list.creator_id is None
    lait, pain = _items(db)
    assert lait.author_id is None and lait.checked_by_id is None and lait.is_checked
    assert pain.author_id == bob.id
    assert "un ancien membre" in login(bob).get(f"/courses/{list_id}").text
