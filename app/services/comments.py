from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models import Comment, User
from app.services.visibility import get_commentable_gift

MAX_CONTENT_LENGTH = 1000


class CommentNotFoundError(Exception):
    pass


class NotCommentAuthorError(Exception):
    pass


def _now() -> datetime:
    """Naïf, UTC : même convention que `created_at`/`updated_at` (horodatage SQLite)."""
    return datetime.now(UTC).replace(tzinfo=None)


def _clean_content(content: str) -> str:
    cleaned = content.strip()
    if not cleaned or len(cleaned) > MAX_CONTENT_LENGTH:
        raise ValueError("Le message doit faire entre 1 et 1 000 caractères.")
    return cleaned


def create_comment(db: Session, author: User, gift_id: int, content: str) -> Comment:
    """RG-33 : écrit un message sur le fil d'un cadeau. Réutilise `get_commentable_gift`
    (RG-30/RG-31) : même contrôle d'accès que pour lire le fil, le destinataire n'y écrit
    jamais, même via requête forgée (403).
    """
    gift = get_commentable_gift(db, author, gift_id)
    cleaned_content = _clean_content(content)

    comment = Comment(gift_id=gift.id, author_id=author.id, content=cleaned_content)
    db.add(comment)
    db.commit()
    return comment


def get_own_comment(db: Session, author: User, comment_id: int) -> Comment:
    """RG-35 : le commentaire `comment_id`, si `author` en est bien l'auteur. Un cadeau
    retiré reste commentable (PO-04), mais un cadeau archivé ne l'est plus nulle part
    (RG-40) : `CommentNotFoundError` dans les deux cas d'inexistence/archivage, avant
    `NotCommentAuthorError` si `author` n'en est pas l'auteur.
    """
    comment = db.get(Comment, comment_id)
    if comment is None or comment.gift.archived_year is not None:
        raise CommentNotFoundError
    if comment.author_id != author.id:
        raise NotCommentAuthorError
    return comment


def update_comment(db: Session, author: User, comment_id: int, content: str) -> Comment:
    """RG-35 : modifie son propre message, mêmes validations qu'à l'écriture (RG-33).
    Affiche ensuite « (modifié) » (`updated_at` renseigné).
    """
    comment = get_own_comment(db, author, comment_id)
    comment.content = _clean_content(content)
    comment.updated_at = _now()
    db.commit()
    db.refresh(comment)
    return comment


def delete_comment(db: Session, author: User, comment_id: int) -> None:
    """RG-35 : supprime son propre message."""
    comment = get_own_comment(db, author, comment_id)
    db.delete(comment)
    db.commit()
