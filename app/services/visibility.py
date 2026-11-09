from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import Gift, User


class GiftNotFoundError(Exception):
    pass


class IsRecipientError(Exception):
    """Le destinataire d'un cadeau n'agit jamais sur son propre cadeau (réservation,
    achat) : levée même via une requête forgée (RG-26, RG-28), toujours traduite en 403.
    """

    pass


@dataclass
class GiftView:
    """Un cadeau annoté des informations calculées nécessaires à l'affichage (RG-30).

    Jamais construit à la main dans un router ou un template : c'est ici, et nulle part
    ailleurs, que se décide ce qu'un viewer peut savoir d'un cadeau.
    """

    gift: Gift
    is_suggestion: bool
    suggested_by: User | None
    is_removed: bool
    removed_by: User | None
    status: str | None
    reservants: list[User]
    comment_count: int


def visible_gift_count(db: Session, viewer: User, person: User) -> int:
    """RG-13/RG-30 : nombre de cadeaux de `person` visibles par `viewer` sur sa liste.

    Les cadeaux personnels comptent toujours ; les suggestions pour `person` ne comptent
    que si `viewer` n'est pas `person` (un destinataire ne voit jamais ce qu'on lui
    suggère). Retirés et archivés ne comptent jamais. Un cadeau acheté compte toujours
    (PO-06).
    """
    query = db.query(Gift).filter(
        Gift.recipient_id == person.id,
        Gift.removed_at.is_(None),
        Gift.archived_year.is_(None),
    )
    if viewer.id == person.id:
        query = query.filter(Gift.author_id == Gift.recipient_id)
    return query.count()


def visible_gifts_for(db: Session, viewer: User, person: User) -> list[GiftView]:
    """RG-30 : cadeaux de `person` visibles par `viewer`, triés par nom, avec les
    métadonnées d'affichage (statut, suggestion, réservants, commentaires) déjà calculées
    selon le rôle du viewer — jamais à construire dans le router ou le template.
    """
    is_own_list = viewer.id == person.id

    query = db.query(Gift).filter(Gift.recipient_id == person.id, Gift.archived_year.is_(None))
    if is_own_list:
        # Sur sa propre liste (RG-30) : ni suggestion, ni cadeau que j'ai moi-même retiré.
        query = query.filter(Gift.author_id == Gift.recipient_id, Gift.removed_at.is_(None))

    gifts = query.order_by(Gift.name).all()
    return [_to_gift_view(gift, is_own_list=is_own_list) for gift in gifts]


def get_visible_gift(db: Session, viewer: User, gift_id: int) -> GiftView:
    """RG-30/RG-40 (US-15) : détail d'un cadeau, filtré par les mêmes règles que sa liste.

    Un cadeau inexistant, archivé, ou qui n'apparaîtrait pas dans la liste de son
    destinataire pour ce `viewer` lève `GiftNotFoundError` — même 404 dans tous les cas,
    pour ne jamais révéler qu'un cadeau cache une suggestion ou un retrait.
    """
    gift = db.get(Gift, gift_id)
    if gift is None or gift.archived_year is not None:
        raise GiftNotFoundError

    vue = next(
        (v for v in visible_gifts_for(db, viewer, gift.recipient) if v.gift.id == gift.id), None
    )
    if vue is None:
        raise GiftNotFoundError
    return vue


def get_commentable_gift(db: Session, viewer: User, gift_id: int) -> Gift:
    """RG-30/RG-31 (US-20) : le cadeau `gift_id`, si `viewer` peut accéder à son fil de
    commentaires. Le destinataire n'y accède **jamais**, cadeau personnel ou suggestion
    (`IsRecipientError`, toujours 403, même via requête forgée). Un cadeau retiré reste
    commentable (RG-22/PO-04) ; archivé ou inexistant lève `GiftNotFoundError` (404).
    """
    gift = db.get(Gift, gift_id)
    if gift is None or gift.archived_year is not None:
        raise GiftNotFoundError
    if gift.recipient_id == viewer.id:
        raise IsRecipientError
    return gift


def _to_gift_view(gift: Gift, *, is_own_list: bool) -> GiftView:
    if is_own_list:
        return GiftView(
            gift=gift,
            is_suggestion=False,
            suggested_by=None,
            is_removed=False,
            removed_by=None,
            status=None,
            reservants=[],
            comment_count=0,
        )

    is_suggestion = gift.author_id != gift.recipient_id
    is_removed = gift.removed_at is not None

    if is_removed:
        status = "retiré"
    elif gift.purchased_by_id is not None:
        status = "acheté"
    elif gift.reservations:
        status = "réservé"
    else:
        status = "disponible"

    return GiftView(
        gift=gift,
        is_suggestion=is_suggestion,
        suggested_by=gift.author if is_suggestion else None,
        is_removed=is_removed,
        removed_by=gift.author if is_removed else None,
        status=status,
        reservants=[reservation.user for reservation in gift.reservations],
        comment_count=len(gift.comments),
    )
