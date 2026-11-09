from sqlalchemy.orm import Session

from app.models import Gift, Reservation, User
from app.services.visibility import GiftNotFoundError, IsRecipientError


def _get_reservable_gift(db: Session, member: User, gift_id: int) -> Gift:
    """RG-26 à RG-28 : le cadeau `gift_id`, à condition que `member` puisse y réserver ou
    annuler. Lève `GiftNotFoundError` si inexistant ou archivé, `IsRecipientError` si
    `member` en est le destinataire (toujours 403, même via requête forgée), `ValueError`
    s'il est acheté ou retiré (AC US-18 : réserver et annuler y sont impossibles).
    """
    gift = db.get(Gift, gift_id)
    if gift is None or gift.archived_year is not None:
        raise GiftNotFoundError
    if gift.recipient_id == member.id:
        raise IsRecipientError
    if gift.purchased_by_id is not None or gift.removed_at is not None:
        raise ValueError("Ce cadeau n'est plus réservable.")
    return gift


def reserve_gift(db: Session, member: User, gift_id: int) -> Gift:
    """RG-26 : réserve `gift_id` pour `member`. Plusieurs membres peuvent réserver le même
    cadeau, mais pas deux fois le même (`ValueError` sinon).
    """
    gift = _get_reservable_gift(db, member, gift_id)
    if any(r.user_id == member.id for r in gift.reservations):
        raise ValueError("Vous avez déjà réservé ce cadeau.")

    db.add(Reservation(gift_id=gift.id, user_id=member.id))
    db.commit()
    db.refresh(gift)
    return gift


def cancel_reservation(db: Session, member: User, gift_id: int) -> Gift:
    """RG-27 : annule la réservation de `member` sur `gift_id`. Il n'y a pas de paramètre
    désignant un autre réservant : on ne peut jamais annuler que la sienne, par construction.
    `ValueError` si `member` n'avait pas réservé ce cadeau.
    """
    gift = _get_reservable_gift(db, member, gift_id)
    reservation = next((r for r in gift.reservations if r.user_id == member.id), None)
    if reservation is None:
        raise ValueError("Vous n'avez pas réservé ce cadeau.")

    db.delete(reservation)
    db.commit()
    db.refresh(gift)
    return gift
