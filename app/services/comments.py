from sqlalchemy.orm import Session

from app.models import Comment, User
from app.services.visibility import get_commentable_gift

MAX_CONTENT_LENGTH = 1000


def create_comment(db: Session, author: User, gift_id: int, content: str) -> Comment:
    """RG-33 : écrit un message sur le fil d'un cadeau. Réutilise `get_commentable_gift`
    (RG-30/RG-31) : même contrôle d'accès que pour lire le fil, le destinataire n'y écrit
    jamais, même via requête forgée (403).
    """
    gift = get_commentable_gift(db, author, gift_id)

    cleaned_content = content.strip()
    if not cleaned_content or len(cleaned_content) > MAX_CONTENT_LENGTH:
        raise ValueError("Le message doit faire entre 1 et 1 000 caractères.")

    comment = Comment(gift_id=gift.id, author_id=author.id, content=cleaned_content)
    db.add(comment)
    db.commit()
    return comment
