from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import Gift, User


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
