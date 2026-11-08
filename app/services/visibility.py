from sqlalchemy.orm import Session

from app.models import Gift, User


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
