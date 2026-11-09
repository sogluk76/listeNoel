import unicodedata
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session

from app.models import Gift, User
from app.services.images import InvalidImageError, delete_profile_photo, save_profile_photo
from app.services.users import MemberNotFoundError, get_active_member
from app.services.visibility import GiftNotFoundError, GiftView

MAX_NAME_LENGTH = 150
STATUS_ORDER = {"disponible": 0, "réservé": 1, "acheté": 2, "retiré": 3}


class NotGiftAuthorError(Exception):
    pass


def _now() -> datetime:
    """Naïf, UTC : même convention que `created_at`/`updated_at` (horodatage SQLite)."""
    return datetime.now(UTC).replace(tzinfo=None)


def _clean_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned or len(cleaned) > MAX_NAME_LENGTH:
        raise ValueError("Le nom du cadeau doit faire entre 1 et 150 caractères.")
    return cleaned


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


def _get_suggestable_recipient(db: Session, recipient_id: int | None, author: User) -> User:
    if recipient_id is None:
        raise ValueError("Choisis à qui est destiné ce cadeau.")
    try:
        recipient = get_active_member(db, recipient_id)
    except MemberNotFoundError as exc:
        raise ValueError("Destinataire invalide.") from exc
    if recipient.id == author.id:
        raise ValueError("Destinataire invalide.")
    return recipient


def create_gift(
    db: Session,
    author: User,
    name: str,
    *,
    price: str | None = None,
    url: str | None = None,
    image: bytes | None = None,
    is_suggestion: bool = False,
    recipient_id: int | None = None,
) -> Gift:
    """RG-14 à RG-19 : création d'un cadeau personnel, ou d'une suggestion pour un autre
    membre actif (`is_suggestion=True`). Tant que `is_suggestion` est faux, le destinataire
    est toujours `author`, quoi que contienne une requête forgée : `recipient_id` n'est
    jamais lu dans ce cas.
    """
    cleaned_name = _clean_name(name)
    parsed_price = _parse_price(price)
    cleaned_url = _clean_url(url)

    recipient = _get_suggestable_recipient(db, recipient_id, author) if is_suggestion else author

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
        recipient_id=recipient.id,
        author_id=author.id,
    )
    db.add(gift)
    db.commit()
    return gift


def get_editable_gift(db: Session, author: User, gift_id: int) -> Gift:
    """RG-21 : le cadeau `gift_id`, à condition que `author` puisse le modifier.

    Lève `GiftNotFoundError` si le cadeau n'existe pas ; `NotGiftAuthorError` si `author`
    n'en est pas l'auteur, **avant** toute autre vérification (RG-21 : un autre membre
    reçoit toujours 403, y compris via un id de cadeau retiré/archivé forgé) ; sinon, une
    fois l'auteur confirmé, `GiftNotFoundError` à nouveau si le cadeau est retiré ou
    archivé (RG-22 : disparu de la vue de son auteur, donc plus modifiable par lui).
    """
    gift = db.get(Gift, gift_id)
    if gift is None:
        raise GiftNotFoundError
    if gift.author_id != author.id:
        raise NotGiftAuthorError
    if gift.removed_at is not None or gift.archived_year is not None:
        raise GiftNotFoundError
    return gift


def update_gift(
    db: Session,
    author: User,
    gift_id: int,
    name: str,
    *,
    price: str | None = None,
    url: str | None = None,
    image: bytes | None = None,
    remove_image: bool = False,
) -> Gift:
    """RG-21 : modification d'un cadeau par son auteur, mêmes validations qu'à la création
    (RG-14 à RG-17). Le destinataire n'est pas un paramètre : impossible à modifier, même
    via une requête forgée. Remplacer ou supprimer l'image retire l'ancienne du disque.
    """
    gift = get_editable_gift(db, author, gift_id)

    cleaned_name = _clean_name(name)
    parsed_price = _parse_price(price)
    cleaned_url = _clean_url(url)

    new_image_path = gift.image_path
    if image:
        try:
            new_image_path = save_profile_photo(image)
        except InvalidImageError as exc:
            raise ValueError(str(exc)) from exc
    elif remove_image:
        new_image_path = None

    if new_image_path != gift.image_path and gift.image_path is not None:
        delete_profile_photo(gift.image_path)

    gift.name = cleaned_name
    gift.price = parsed_price
    gift.url = cleaned_url
    gift.image_path = new_image_path
    db.commit()
    db.refresh(gift)
    return gift


def delete_gift(db: Session, author: User, gift_id: int) -> None:
    """RG-22 : suppression par l'auteur. Sans réservation, achat ni commentaire,
    suppression définitive (ligne et image) ; sinon, suppression douce : `removed_at` est
    renseigné, le cadeau disparaît de la vue de l'auteur et les autres le voient marqué
    « Retiré par <auteur> » (déjà géré par `visible_gifts_for`/`get_visible_gift`), plus
    réservable, mais les commentaires restent en lecture/écriture (PO-04).
    """
    gift = get_editable_gift(db, author, gift_id)

    a_une_activite = (
        bool(gift.reservations) or gift.purchased_by_id is not None or bool(gift.comments)
    )
    if a_une_activite:
        gift.removed_at = _now()
        db.commit()
        return

    if gift.image_path:
        delete_profile_photo(gift.image_path)
    db.delete(gift)
    db.commit()


def _normalize(text: str) -> str:
    """Insensible à la casse et aux accents (RG-24)."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


def search_and_sort_gifts(
    vues: list[GiftView], *, q: str = "", sort: str = "nom", direction: str = "croissant"
) -> list[GiftView]:
    """RG-24/RG-25 : recherche et tri. `vues` est déjà la liste filtrée par RG-30
    (`visible_gifts_for`) — jamais ré-élargie ici, le filtre/tri ne fait que réordonner
    ou retirer, jamais ajouter.
    """
    if q:
        needle = _normalize(q)
        vues = [v for v in vues if needle in _normalize(v.gift.name)]

    reverse = direction == "decroissant"

    if sort == "prix":
        avec_prix = sorted(
            (v for v in vues if v.gift.price is not None),
            key=lambda v: v.gift.price,
            reverse=reverse,
        )
        sans_prix = [v for v in vues if v.gift.price is None]
        return avec_prix + sans_prix

    if sort == "statut":
        return sorted(vues, key=lambda v: STATUS_ORDER.get(v.status, 0), reverse=reverse)

    return sorted(vues, key=lambda v: v.gift.name.casefold(), reverse=reverse)
