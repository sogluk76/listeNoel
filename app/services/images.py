"""Images envoyées : vérification, redimensionnement, stockage (RG-17)."""

from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError

from app.config import settings
from app.errors import Invalid

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
GIFT_MAX_SIDE = 1200
AVATAR_MAX_SIDE = 400
MESSAGE_MAX_SIDE = 1600


def has_file(upload: UploadFile | None) -> bool:
    return upload is not None and bool(upload.filename)


def save_image(upload: UploadFile, subdir: str, max_side: int, root: Path | None = None) -> str:
    """Enregistre l'image en WebP sous un nom généré et renvoie son chemin relatif.

    `root` vaut le dossier public des images par défaut ; les photos des messages
    privés vont dans settings.private_media_dir.
    """
    root = root or settings.media_dir
    data = upload.file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise Invalid("L'image est trop lourde (5 Mo maximum).")
    try:
        Image.open(BytesIO(data)).verify()
        image = Image.open(BytesIO(data))
        if image.format not in ALLOWED_FORMATS:
            raise Invalid("Format d'image non accepté (JPEG, PNG ou WebP).")
        image = ImageOps.exif_transpose(image)
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGBA" if "transparency" in image.info else "RGB")
        image.thumbnail((max_side, max_side))
        relative = f"{subdir}/{uuid4().hex}.webp"
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        image.save(target, "WEBP", quality=85)
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        raise Invalid("Ce fichier n'est pas une image valide.") from exc
    return relative


def delete_image(relative: str | None, root: Path | None = None) -> None:
    if not relative:
        return
    root = root or settings.media_dir
    target = (root / relative).resolve()
    if root.resolve() in target.parents and target.is_file():
        target.unlink()
