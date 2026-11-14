"""Opérations du panel admin sur les cadeaux et les comptes (RG-23, RG-39 à RG-41).

Ces fonctions ne renvoient jamais ni commentaires, ni réservations, ni statut d'achat.
"""

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Comment, Gift, Notification, Reservation, User
from app.services import images
from app.services import messages as messages_service
from app.services.text import fold


def list_gifts(db: Session, recipient_id: int | None = None) -> list[Gift]:
    stmt = select(Gift).where(Gift.archived_year.is_(None))
    if recipient_id is not None:
        stmt = stmt.where(Gift.recipient_id == recipient_id)
    gifts = db.scalars(stmt).all()
    return sorted(gifts, key=lambda g: (fold(g.recipient.first_name), fold(g.name)))


def delete_member(db: Session, member: User) -> None:
    """Supprime définitivement un membre et toute sa trace (RG-41).

    Disparaissent : sa liste (cadeaux dont il est destinataire), les cadeaux qu'il a créés
    pour d'autres, ses réservations et ses commentaires. Un cadeau qu'il avait marqué
    « acheté » redevient réservé ou disponible. Les cadeaux archivés sont concernés aussi.
    Ses messages privés et ses conversations à deux disparaissent également (RG-54).
    """
    private_photos = messages_service.purge_member(db, member)
    for notification in db.scalars(select(Notification).where(Notification.user_id == member.id)):
        db.delete(notification)
    for reservation in db.scalars(select(Reservation).where(Reservation.user_id == member.id)):
        db.delete(reservation)
    for comment in db.scalars(select(Comment).where(Comment.author_id == member.id)):
        db.delete(comment)
    db.flush()

    image_paths = [member.photo_path]
    own_gifts = db.scalars(
        select(Gift).where(or_(Gift.recipient_id == member.id, Gift.author_id == member.id))
    ).all()
    for gift in own_gifts:
        image_paths.append(gift.image_path)
        db.delete(gift)
    db.flush()

    for gift in db.scalars(select(Gift).where(Gift.purchased_by_id == member.id)):
        gift.purchased_by_id = None
        gift.purchased_at = None

    db.delete(member)
    db.commit()
    for path in image_paths:
        images.delete_image(path)
    messages_service.delete_photos(private_photos)


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
