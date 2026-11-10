"""Réservations et achat (RG-26 à RG-29).

Les fonctions reçoivent un cadeau déjà contrôlé par visibility.get_gift_with_secrets :
le destinataire n'arrive donc jamais jusqu'ici.
"""

from sqlalchemy.orm import Session

from app.errors import Forbidden, Invalid
from app.models import Gift, Reservation, User, utcnow

MSG_LOCKED = "Ce cadeau n'est plus modifiable."


def _require_not_recipient(user: User, gift: Gift) -> None:
    if user.id == gift.recipient_id or not user.is_member:
        raise Forbidden()


def _require_open(gift: Gift) -> None:
    """Ni acheté, ni retiré, ni archivé."""
    if gift.is_bought or gift.is_removed or gift.is_archived:
        raise Invalid(MSG_LOCKED)


def _find(gift: Gift, user: User) -> Reservation | None:
    return next((r for r in gift.reservations if r.user_id == user.id), None)


def reserve(db: Session, user: User, gift: Gift) -> None:
    _require_not_recipient(user, gift)
    _require_open(gift)
    if _find(gift, user) is not None:
        raise Invalid("Tu t'occupes déjà de ce cadeau.")
    gift.reservations.append(Reservation(user_id=user.id))
    db.commit()


def cancel(db: Session, user: User, gift: Gift) -> None:
    _require_not_recipient(user, gift)
    _require_open(gift)
    reservation = _find(gift, user)
    if reservation is None:
        raise Invalid("Tu n'as pas réservé ce cadeau.")
    gift.reservations.remove(reservation)
    db.commit()


def mark_bought(db: Session, user: User, gift: Gift) -> None:
    _require_not_recipient(user, gift)
    _require_open(gift)
    if _find(gift, user) is None:
        raise Forbidden()  # seul un réservant peut marquer acheté
    gift.purchased_by_id = user.id
    gift.purchased_at = utcnow()
    db.commit()


def cancel_bought(db: Session, user: User, gift: Gift) -> None:
    _require_not_recipient(user, gift)
    if gift.is_removed or gift.is_archived or not gift.is_bought:
        raise Invalid(MSG_LOCKED)
    if gift.purchased_by_id != user.id:
        raise Forbidden()  # seul l'acheteur peut annuler l'achat
    gift.purchased_by_id = None
    gift.purchased_at = None
    db.commit()
