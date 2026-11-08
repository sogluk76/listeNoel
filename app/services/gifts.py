from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session

from app.models import Gift, User
from app.services.images import InvalidImageError, save_profile_photo

MAX_NAME_LENGTH = 150


def _parse_price(raw: str | None) -> Decimal | None:
    if raw is None or raw.strip() == "":
        return None
    try:
        value = Decimal(raw.strip().replace(",", "."))
    except InvalidOperation as exc:
        raise ValueError("Le prix doit être un nombre.") from exc
    if value < 0:
        raise ValueError("Le prix ne peut pas être négatif.")
    if value.as_tuple().exponent < -2:
        raise ValueError("Le prix accepte au maximum 2 décimales.")
    return value


def _clean_url(raw: str | None) -> str | None:
    if raw is None or raw.strip() == "":
        return None
    cleaned = raw.strip()
    if not cleaned.startswith(("http://", "https://")):
        raise ValueError("Le lien doit commencer par http:// ou https://.")
    return cleaned


def create_gift(
    db: Session,
    author: User,
    name: str,
    *,
    price: str | None = None,
    url: str | None = None,
    image: bytes | None = None,
) -> Gift:
    """RG-14 à RG-18 : création d'un cadeau personnel (auteur = destinataire = `author`).

    Le destinataire n'est jamais pris en paramètre : tant que « Suggérer » n'existe pas
    encore (US-12), un cadeau créé ici est toujours pour son auteur, quoi que contienne
    une requête forgée.
    """
    cleaned_name = name.strip()
    if not cleaned_name or len(cleaned_name) > MAX_NAME_LENGTH:
        raise ValueError("Le nom du cadeau doit faire entre 1 et 150 caractères.")

    parsed_price = _parse_price(price)
    cleaned_url = _clean_url(url)

    image_path = None
    if image:
        try:
            image_path = save_profile_photo(image)
        except InvalidImageError as exc:
            raise ValueError(str(exc)) from exc

    gift = Gift(
        name=cleaned_name,
        price=parsed_price,
        url=cleaned_url,
        image_path=image_path,
        recipient_id=author.id,
        author_id=author.id,
    )
    db.add(gift)
    db.commit()
    return gift
