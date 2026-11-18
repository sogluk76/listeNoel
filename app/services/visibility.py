"""Matrice de confidentialité (RG-30).

C'est le SEUL endroit qui décide de ce qu'un membre peut voir. Toute lecture de
cadeaux, de réservations ou de commentaires côté membre passe par ce module :
les données cachées ne sont jamais chargées dans la vue du destinataire.
"""

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import Forbidden, NotFound
from app.models import (
    STATUS_AVAILABLE,
    STATUS_BOUGHT,
    STATUS_REMOVED,
    STATUS_RESERVED,
    Gift,
    Notification,
    Reservation,
    User,
)
from app.services import users as users_service
from app.services.text import fold

SORT_NAME = "nom"
SORT_PRICE = "prix"
SORT_STATUS = "statut"
_STATUS_ORDER = {STATUS_AVAILABLE: 0, STATUS_RESERVED: 1, STATUS_BOUGHT: 2, STATUS_REMOVED: 3}


@dataclass
class GiftView:
    """Ce que le viewer a le droit de voir d'un cadeau. Les templates n'utilisent que ça."""

    gift: Gift
    is_mine: bool  # le viewer est le destinataire
    can_edit: bool  # le viewer est l'auteur (RG-21)
    show_secrets: bool  # statut, réservations, commentaires
    status: str | None = None
    reservers: list[User] = field(default_factory=list)
    buyer: User | None = None
    comment_count: int | None = None
    suggested_by: User | None = None
    removed_by: User | None = None
    i_reserved: bool = False
    i_bought: bool = False


def can_see_secrets(viewer: User, gift: Gift) -> bool:
    return viewer.id != gift.recipient_id


def is_visible(viewer: User, gift: Gift) -> bool:
    """Un cadeau est-il visible par ce membre ? (RG-11, RG-22, RG-30, RG-40)"""
    if gift.is_archived:
        return False
    if not gift.recipient.is_active or not gift.recipient.is_member:
        return False
    if gift.is_removed and gift.author_id == viewer.id:
        return False  # retiré : disparaît de la vue de son auteur
    if viewer.id == gift.recipient_id and gift.is_suggestion:
        return False  # jamais de suggestion sur ma propre liste
    return True


def build_view(viewer: User, gift: Gift) -> GiftView:
    is_mine = viewer.id == gift.recipient_id
    can_edit = gift.author_id == viewer.id and not gift.is_removed and not gift.is_archived
    view = GiftView(gift=gift, is_mine=is_mine, can_edit=can_edit, show_secrets=not is_mine)
    if is_mine:
        return view  # aucune donnée cachée n'est copiée dans la vue
    view.status = gift.status
    view.reservers = [r.user for r in gift.reservations]
    view.buyer = gift.purchased_by
    view.comment_count = len(gift.comments)
    view.suggested_by = gift.author if gift.is_suggestion else None
    view.removed_by = gift.author if gift.is_removed else None
    view.i_reserved = any(r.user_id == viewer.id for r in gift.reservations)
    view.i_bought = gift.purchased_by_id == viewer.id
    return view


def _visible_gifts(db: Session, viewer: User, recipient: User) -> list[Gift]:
    stmt = select(Gift).where(Gift.recipient_id == recipient.id, Gift.archived_year.is_(None))
    if viewer.id == recipient.id:
        # Filtrage dans la requête : les suggestions ne sortent jamais de la base.
        stmt = stmt.where(Gift.author_id == viewer.id, Gift.removed_at.is_(None))
    return [g for g in db.scalars(stmt).all() if is_visible(viewer, g)]


def get_person(db: Session, person_id: int) -> User:
    person = users_service.get_active_member(db, person_id)
    if person is None:
        raise NotFound()
    return person


def people_with_counts(db: Session, viewer: User) -> list[tuple[User, int]]:
    """Membres actifs et nombre de cadeaux visibles par le viewer (RG-12, RG-13)."""
    result = []
    for person in users_service.active_members(db):
        gifts = _visible_gifts(db, viewer, person)
        result.append((person, sum(1 for g in gifts if not g.is_removed)))
    return result


def list_gifts(
    db: Session,
    viewer: User,
    recipient: User,
    query: str = "",
    sort: str = SORT_NAME,
    descending: bool = False,
) -> list[GiftView]:
    """Liste de cadeaux d'une personne, filtrée, puis recherchée et triée (RG-24, RG-25)."""
    views = [build_view(viewer, g) for g in _visible_gifts(db, viewer, recipient)]

    needle = fold(query or "")
    if needle:
        views = [v for v in views if needle in fold(v.gift.name)]

    if sort == SORT_STATUS and viewer.id == recipient.id:
        sort = SORT_NAME  # pas de tri par statut sur ma propre liste

    views.sort(key=lambda v: fold(v.gift.name))
    if sort == SORT_PRICE:
        priced = sorted(
            (v for v in views if v.gift.price is not None),
            key=lambda v: v.gift.price,
            reverse=descending,
        )
        return priced + [v for v in views if v.gift.price is None]  # sans prix à la fin
    if sort == SORT_STATUS:
        views.sort(key=lambda v: _STATUS_ORDER[v.status], reverse=descending)
        return views
    if descending:
        views.reverse()
    return views


def get_gift(db: Session, viewer: User, gift_id: int) -> Gift:
    """Cadeau visible par le viewer, sinon 404 (y compris pour une URL forgée)."""
    gift = db.get(Gift, gift_id)
    if gift is None or not is_visible(viewer, gift):
        raise NotFound()
    return gift


def get_gift_with_secrets(db: Session, viewer: User, gift_id: int) -> Gift:
    """Cadeau dont le viewer peut voir réservations et commentaires, sinon 403/404."""
    gift = get_gift(db, viewer, gift_id)
    if not can_see_secrets(viewer, gift):
        raise Forbidden()
    return gift


def my_notifications(db: Session, viewer: User) -> list[Notification]:
    """Notifications du viewer, de la plus récente à la plus ancienne (RG-45, RG-57).

    Une mention n'est renvoyée que si le viewer a le droit de voir le fil du cadeau.
    Un nouveau cadeau ne l'est que si le viewer le voit, n'en est ni l'auteur ni le
    destinataire, et qu'il n'a pas été retiré. Le destinataire n'en reçoit donc jamais,
    même si une ligne existait en base par erreur.
    """
    stmt = (
        select(Notification)
        .where(Notification.user_id == viewer.id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
    )
    result = []
    for notification in db.scalars(stmt).all():
        gift = notification.target_gift
        if not (is_visible(viewer, gift) and can_see_secrets(viewer, gift)):
            continue
        if notification.is_new_gift and (gift.is_removed or gift.author_id == viewer.id):
            continue
        result.append(notification)
    return result


def unread_notification_count(db: Session, viewer: User) -> int:
    return sum(1 for n in my_notifications(db, viewer) if n.read_at is None)


def my_reservations(db: Session, viewer: User) -> list[tuple[User, list[GiftView], object]]:
    """Cadeaux réservés ou achetés par le viewer, groupés par destinataire (RG-38)."""
    stmt = (
        select(Gift)
        .outerjoin(Reservation, Reservation.gift_id == Gift.id)
        .where(
            Gift.archived_year.is_(None),
            (Reservation.user_id == viewer.id) | (Gift.purchased_by_id == viewer.id),
        )
        .distinct()
    )
    groups: dict[int, list[GiftView]] = {}
    recipients: dict[int, User] = {}
    for gift in db.scalars(stmt).all():
        if not is_visible(viewer, gift) or not can_see_secrets(viewer, gift):
            continue
        groups.setdefault(gift.recipient_id, []).append(build_view(viewer, gift))
        recipients[gift.recipient_id] = gift.recipient
    result = []
    for rid in sorted(groups, key=lambda i: fold(recipients[i].first_name)):
        views = sorted(groups[rid], key=lambda v: fold(v.gift.name))
        total = sum(
            (v.gift.price for v in views if v.gift.price is not None and not v.gift.is_removed),
            start=0,
        )
        result.append((recipients[rid], views, total))
    return result
