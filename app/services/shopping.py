"""Listes de courses partagées entre les membres (RG-59 à RG-61).

Toutes les listes sont visibles et modifiables par tous les membres actifs. L'admin n'y
a pas accès : c'est assuré par la dépendance current_member dans le router.
"""

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.errors import Invalid, NotFound
from app.models import ShoppingItem, ShoppingList, User, utcnow
from app.services.text import fold

LIST_NAME_MAX = 60
ITEM_NAME_MAX = 100
QUANTITY_MAX = 30


def _clean(raw: str | None) -> str:
    return " ".join((raw or "").split())


def clean_list_name(raw: str | None) -> str:
    name = _clean(raw)
    if not name:
        raise Invalid("Donne un nom à la liste.")
    if len(name) > LIST_NAME_MAX:
        raise Invalid(f"Le nom ne doit pas dépasser {LIST_NAME_MAX} caractères.")
    return name


def clean_item(name: str | None, quantity: str | None) -> tuple[str, str | None]:
    clean_name = _clean(name)
    if not clean_name:
        raise Invalid("Écris ce qu'il faut acheter.")
    if len(clean_name) > ITEM_NAME_MAX:
        raise Invalid(f"L'article ne doit pas dépasser {ITEM_NAME_MAX} caractères.")
    clean_quantity = _clean(quantity) or None
    if clean_quantity and len(clean_quantity) > QUANTITY_MAX:
        raise Invalid(f"La quantité ne doit pas dépasser {QUANTITY_MAX} caractères.")
    return clean_name, clean_quantity


# --- Listes ------------------------------------------------------------------


def all_lists(db: Session) -> list[tuple[ShoppingList, int]]:
    """Toutes les listes, la plus récemment modifiée d'abord, avec leurs articles restants."""
    lists = db.scalars(select(ShoppingList)).all()
    lists = sorted(lists, key=lambda s: fold(s.name))
    lists.sort(key=lambda s: s.updated_at, reverse=True)
    return [(s, sum(1 for i in s.items if not i.is_checked)) for s in lists]


def get_list(db: Session, list_id: int) -> ShoppingList:
    shopping_list = db.get(ShoppingList, list_id)
    if shopping_list is None:
        raise NotFound()
    return shopping_list


def create_list(db: Session, user: User, name: str) -> ShoppingList:
    shopping_list = ShoppingList(name=clean_list_name(name), creator_id=user.id)
    db.add(shopping_list)
    db.commit()
    return shopping_list


def rename_list(db: Session, shopping_list: ShoppingList, name: str) -> None:
    shopping_list.name = clean_list_name(name)
    db.commit()


def delete_list(db: Session, shopping_list: ShoppingList) -> None:
    db.delete(shopping_list)
    db.commit()


# --- Articles ----------------------------------------------------------------


def pending(shopping_list: ShoppingList) -> list[ShoppingItem]:
    """Articles à acheter, dans l'ordre où ils ont été ajoutés."""
    return [i for i in shopping_list.items if not i.is_checked]


def done(shopping_list: ShoppingList) -> list[ShoppingItem]:
    """Articles cochés (« dans le panier »), le dernier coché en premier."""
    items = [i for i in shopping_list.items if i.is_checked]
    return sorted(items, key=lambda i: (i.checked_at, i.id), reverse=True)


def _touch(shopping_list: ShoppingList) -> None:
    shopping_list.updated_at = utcnow()


def add_item(
    db: Session, user: User, shopping_list: ShoppingList, name: str, quantity: str
) -> ShoppingItem:
    clean_name, clean_quantity = clean_item(name, quantity)
    item = ShoppingItem(name=clean_name, quantity=clean_quantity, author_id=user.id)
    shopping_list.items.append(item)
    _touch(shopping_list)
    db.commit()
    return item


def get_item(db: Session, shopping_list: ShoppingList, item_id: int) -> ShoppingItem:
    """Article de cette liste, sinon 404 (y compris l'article d'une autre liste)."""
    item = db.get(ShoppingItem, item_id)
    if item is None or item.list_id != shopping_list.id:
        raise NotFound()
    return item


def toggle_item(db: Session, user: User, item: ShoppingItem) -> None:
    """Coche ou décoche l'article. On retient qui l'a coché (RG-60)."""
    if item.is_checked:
        item.checked_at = None
        item.checked_by_id = None
    else:
        item.checked_at = utcnow()
        item.checked_by_id = user.id
    _touch(item.shopping_list)
    db.commit()


def delete_item(db: Session, item: ShoppingItem) -> None:
    shopping_list = item.shopping_list
    shopping_list.items.remove(item)
    _touch(shopping_list)
    db.commit()


def clear_checked(db: Session, shopping_list: ShoppingList) -> int:
    """Retire tous les articles cochés de la liste. Renvoie le nombre retiré."""
    checked = done(shopping_list)
    for item in checked:
        shopping_list.items.remove(item)
    if checked:
        _touch(shopping_list)
    db.commit()
    return len(checked)


# --- Suppression d'un compte (RG-41) -------------------------------------------


def purge_member(db: Session, member: User) -> None:
    """Détache le membre de ses listes et articles, qui restent à la famille (RG-61).

    Ne fait pas de commit : appelée par admin.delete_member avant la suppression du compte.
    """
    db.execute(
        update(ShoppingList).where(ShoppingList.creator_id == member.id).values(creator_id=None)
    )
    db.execute(
        update(ShoppingItem).where(ShoppingItem.author_id == member.id).values(author_id=None)
    )
    db.execute(
        update(ShoppingItem)
        .where(ShoppingItem.checked_by_id == member.id)
        .values(checked_by_id=None)
    )
