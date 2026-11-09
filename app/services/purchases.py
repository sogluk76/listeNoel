from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models import Gift, User
from app.services.visibility import GiftNotFoundError, IsRecipientError


class NotReservantError(Exception):
    pass


class NotPurchaserError(Exception):
    pass


def _now() -> datetime:
    """Naïf, UTC : même convention que `created_at`/`updated_at` (horodatage SQLite)."""
    return datetime.now(UTC).replace(tzinfo=None)


def _get_purchasable_gift(db: Session, member: User, gift_id: int) -> Gift:
    """Lève `GiftNotFoundError` si inexistant ou archivé, `IsRecipientError` si `member`
    en est le destinataire (toujours 403, même via requête forgée, RG-28/RG-29), `ValueError`
    si le cadeau a été retiré par son auteur (plus d'activité possible).
    """
    gift = db.get(Gift, gift_id)
    if gift is None or gift.archived_year is not None:
        raise GiftNotFoundError
    if gift.recipient_id == member.id:
        raise IsRecipientError
    if gift.removed_at is not None:
        raise ValueError("Ce cadeau n'est plus disponible.")
    return gift


def mark_purchased(db: Session, member: User, gift_id: int) -> Gift:
    """RG-28 : un réservant marque le cadeau comme acheté. Bloque alors toute nouvelle
    réservation ou annulation (déjà assuré par `reservations._get_reservable_gift`, qui
    vérifie `purchased_by_id`), mais pas les commentaires.
    """
    gift = _get_purchasable_gift(db, member, gift_id)
    if gift.purchased_by_id is not None:
        raise ValueError("Ce cadeau est déjà marqué comme acheté.")
    if not any(r.user_id == member.id for r in gift.reservations):
        raise NotReservantError

    gift.purchased_by_id = member.id
    gift.purchased_at = _now()
    db.commit()
    db.refresh(gift)
    return gift


def cancel_purchase(db: Session, member: User, gift_id: int) -> Gift:
    """RG-29 : seul l'acheteur annule l'achat. Le cadeau repasse en réservé avec ses
    réservants, jamais touchés pendant qu'il était acheté.
    """
    gift = _get_purchasable_gift(db, member, gift_id)
    if gift.purchased_by_id is None:
        raise ValueError("Ce cadeau n'est pas acheté.")
    if gift.purchased_by_id != member.id:
        raise NotPurchaserError

    gift.purchased_by_id = None
    gift.purchased_at = None
    db.commit()
    db.refresh(gift)
    return gift
