"""Commentaires d'un cadeau (RG-31 à RG-35).

Les fonctions reçoivent un cadeau déjà contrôlé par visibility.get_gift_with_secrets.
"""

from sqlalchemy.orm import Session

from app.errors import Forbidden, Invalid, NotFound
from app.models import Comment, Gift, User, utcnow
from app.services import visibility

CONTENT_MAX = 1000


def clean_content(content: str) -> str:
    text = (content or "").replace("\r\n", "\n").strip()
    if not text:
        raise Invalid("Le message ne peut pas être vide.")
    if len(text) > CONTENT_MAX:
        raise Invalid(f"Le message ne doit pas dépasser {CONTENT_MAX} caractères.")
    return text


def thread(gift: Gift) -> list[Comment]:
    return sorted(gift.comments, key=lambda c: (c.created_at, c.id))


def add(db: Session, user: User, gift: Gift, content: str) -> Comment:
    comment = Comment(author_id=user.id, content=clean_content(content))
    gift.comments.append(comment)
    db.commit()
    return comment


def get_own(db: Session, user: User, comment_id: int) -> Comment:
    """Commentaire du viewer. 404 s'il n'existe pas, 403 s'il n'est pas à lui."""
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise NotFound()
    visibility.get_gift_with_secrets(db, user, comment.gift_id)
    if comment.author_id != user.id:
        raise Forbidden()
    return comment


def edit(db: Session, comment: Comment, content: str) -> None:
    comment.content = clean_content(content)
    comment.updated_at = utcnow()
    db.commit()


def delete(db: Session, comment: Comment) -> None:
    db.delete(comment)
    db.commit()
