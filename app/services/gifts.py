"""Cadeaux : validation, création, modification, suppression (RG-14 à RG-23)."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.errors import Forbidden
from app.models import Gift, User, utcnow
from app.services import images, notifications
from app.services import users as users_service

NAME_MAX = 150
PRICE_MAX = Decimal("99999999.99")


@dataclass
class GiftData:
    name: str
    price: Decimal | None
    url: str | None


def parse_price(raw: str) -> Decimal | None:
    """Montant en euros, virgule ou point, 2 décimales maximum (RG-15)."""
    text = (raw or "").replace("€", "").replace(" ", "").replace("\xa0", "").replace(" ", "")
    if not text:
        return None
    try:
        value = Decimal(text.replace(",", "."))
    except InvalidOperation as exc:
        raise ValueError("Le prix doit être un nombre, par exemple 39,99.") from exc
    if not value.is_finite():
        raise ValueError("Le prix doit être un nombre, par exemple 39,99.")
    if value < 0:
        raise ValueError("Le prix ne peut pas être négatif.")
    if value.as_tuple().exponent < -2:
        raise ValueError("Le prix ne peut pas avoir plus de 2 décimales.")
    if value > PRICE_MAX:
        raise ValueError("Ce prix est trop élevé.")
    return value.quantize(Decimal("0.01"))


def parse_url(raw: str) -> str | None:
    """Lien http(s) uniquement (RG-16)."""
    text = (raw or "").strip()
    if not text:
        return None
    parsed = urlparse(text)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("Le lien doit commencer par http:// ou https://.")
    if len(text) > 2000:
        raise ValueError("Ce lien est trop long.")
    return text


def validate(name: str, price: str, url: str) -> tuple[GiftData | None, dict[str, str]]:
    """Valide les champs du formulaire. Renvoie (données, erreurs par champ)."""
    errors: dict[str, str] = {}
    clean_name = " ".join((name or "").split())
    if not clean_name:
        errors["name"] = "Le nom du cadeau est obligatoire."
    elif len(clean_name) > NAME_MAX:
        errors["name"] = f"Le nom ne doit pas dépasser {NAME_MAX} caractères."
    clean_price = None
    try:
        clean_price = parse_price(price)
    except ValueError as exc:
        errors["price"] = str(exc)
    clean_url = None
    try:
        clean_url = parse_url(url)
    except ValueError as exc:
        errors["url"] = str(exc)
    if errors:
        return None, errors
    return GiftData(name=clean_name, price=clean_price, url=clean_url), errors


def resolve_recipient(
    db: Session, author: User, suggest: bool, recipient_id: int | None
) -> User | None:
    """Destinataire du cadeau (RG-18, RG-19). None si le choix est invalide."""
    if not suggest:
        return author  # tout destinataire forgé est ignoré
    recipient = users_service.get_active_member(db, recipient_id)
    if recipient is None or recipient.id == author.id:
        return None
    return recipient


def create(
    db: Session, author: User, recipient: User, data: GiftData, image_path: str | None
) -> Gift:
    gift = Gift(
        name=data.name,
        price=data.price,
        url=data.url,
        image_path=image_path,
        author_id=author.id,
        recipient_id=recipient.id,
    )
    db.add(gift)
    notifications.notify_new_gift(db, gift)
    db.commit()
    return gift


def require_author(user: User, gift: Gift) -> None:
    """Seul l'auteur modifie ou supprime un cadeau (RG-21)."""
    if gift.author_id != user.id or gift.is_removed or gift.is_archived:
        raise Forbidden()


def update(
    db: Session,
    user: User,
    gift: Gift,
    data: GiftData,
    new_image_path: str | None = None,
    remove_image: bool = False,
) -> None:
    require_author(user, gift)
    gift.name = data.name
    gift.price = data.price
    gift.url = data.url
    old_image = None
    if new_image_path:
        old_image, gift.image_path = gift.image_path, new_image_path
    elif remove_image:
        old_image, gift.image_path = gift.image_path, None
    gift.updated_at = utcnow()
    db.commit()
    images.delete_image(old_image)


def has_activity(gift: Gift) -> bool:
    return bool(gift.reservations) or gift.is_bought or bool(gift.comments)


def delete_by_author(db: Session, user: User, gift: Gift) -> None:
    """Suppression définitive, ou douce s'il y a eu de l'activité (RG-22)."""
    require_author(user, gift)
    if has_activity(gift):
        gift.removed_at = utcnow()
        db.commit()
        return
    hard_delete(db, gift)


def hard_delete(db: Session, gift: Gift) -> None:
    """Supprime le cadeau, ses réservations, ses commentaires et son image (RG-23)."""
    image_path = gift.image_path
    db.delete(gift)
    db.commit()
    images.delete_image(image_path)
