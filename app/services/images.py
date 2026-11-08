import io
import uuid
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from app.config import settings

MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 Mo (RG-17)
MAX_DIMENSION = 800  # px, plus grand côté, ratio conservé (RG-17 / PO-10)
ALLOWED_FORMATS = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}


class InvalidImageError(Exception):
    pass


def save_profile_photo(content: bytes) -> str:
    """Valide, redimensionne et enregistre une image dans `media/`. Lève `InvalidImageError`
    si le fichier n'est pas une image valide, dans un format supporté ou dans la limite de taille.
    Retourne le nom de fichier généré (UUID), relatif à `media/`.
    """
    if len(content) > MAX_UPLOAD_SIZE:
        raise InvalidImageError("L'image dépasse la taille maximale de 5 Mo.")

    try:
        image = Image.open(io.BytesIO(content))
        image.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise InvalidImageError("Le fichier n'est pas une image valide.") from exc

    if image.format not in ALLOWED_FORMATS:
        raise InvalidImageError("Format d'image non supporté (JPEG, PNG ou WebP uniquement).")

    image.thumbnail((MAX_DIMENSION, MAX_DIMENSION))

    filename = f"{uuid.uuid4().hex}{ALLOWED_FORMATS[image.format]}"
    destination = settings.media_dir / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination)

    return str(Path(filename))


def delete_profile_photo(path: str) -> None:
    """Supprime un fichier de `media/`. Tolère un chemin déjà absent."""
    (settings.media_dir / path).unlink(missing_ok=True)
