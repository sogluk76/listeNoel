"""Opérations du panel admin sur les cadeaux (RG-23, RG-39, RG-40).

Ces fonctions ne renvoient jamais ni commentaires, ni réservations, ni statut d'achat.
"""

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Gift
from app.services.text import fold


def list_gifts(db: Session, recipient_id: int | None = None) -> list[Gift]:
    stmt = select(Gift).where(Gift.archived_year.is_(None))
    if recipient_id is not None:
        stmt = stmt.where(Gift.recipient_id == recipient_id)
    gifts = db.scalars(stmt).all()
    return sorted(gifts, key=lambda g: (fold(g.recipient.first_name), fold(g.name)))


def _to_archive():
    return select(Gift).where(
        Gift.archived_year.is_(None),
        or_(Gift.purchased_by_id.is_not(None), Gift.removed_at.is_not(None)),
    )


def count_to_archive(db: Session) -> int:
    return len(db.scalars(_to_archive()).all())


def close_year(db: Session, year: int) -> int:
    """Archive les cadeaux achetés ou retirés. Relançable sans effet (idempotent)."""
    gifts = db.scalars(_to_archive()).all()
    for gift in gifts:
        gift.archived_year = year
    db.commit()
    return len(gifts)
