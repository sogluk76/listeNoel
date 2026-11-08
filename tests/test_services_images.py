import pytest
from PIL import Image

from app.config import settings
from app.services.images import (
    MAX_DIMENSION,
    InvalidImageError,
    delete_profile_photo,
    save_profile_photo,
)


def test_image_valide_enregistree(make_image_bytes):
    chemin = save_profile_photo(make_image_bytes("PNG", (1600, 800)))

    destination = settings.media_dir / chemin
    assert destination.exists()


def test_image_redimensionnee_sous_la_limite(make_image_bytes):
    chemin = save_profile_photo(make_image_bytes("PNG", (1600, 800)))

    with Image.open(settings.media_dir / chemin) as img:
        assert max(img.size) <= MAX_DIMENSION


def test_ratio_conserve_lors_du_redimensionnement(make_image_bytes):
    chemin = save_profile_photo(make_image_bytes("PNG", (1600, 800)))  # ratio 2:1

    with Image.open(settings.media_dir / chemin) as img:
        largeur, hauteur = img.size
        assert round(largeur / hauteur, 2) == 2.0


def test_image_deja_sous_la_limite_non_agrandie(make_image_bytes):
    chemin = save_profile_photo(make_image_bytes("PNG", (50, 50)))

    with Image.open(settings.media_dir / chemin) as img:
        assert img.size == (50, 50)


@pytest.mark.parametrize(
    ("fmt", "extension"), [("JPEG", ".jpg"), ("PNG", ".png"), ("WEBP", ".webp")]
)
def test_formats_acceptes(make_image_bytes, fmt, extension):
    chemin = save_profile_photo(make_image_bytes(fmt, (100, 100)))

    assert chemin.endswith(extension)


def test_format_non_supporte_refuse(make_image_bytes):
    with pytest.raises(InvalidImageError):
        save_profile_photo(make_image_bytes("GIF", (100, 100)))


def test_fichier_non_image_refuse():
    with pytest.raises(InvalidImageError):
        save_profile_photo(b"ceci n'est pas une image")


def test_fichier_trop_volumineux_refuse():
    enorme = b"\x00" * (5 * 1024 * 1024 + 1)

    with pytest.raises(InvalidImageError):
        save_profile_photo(enorme)


def test_delete_profile_photo_supprime_le_fichier(make_image_bytes):
    chemin = save_profile_photo(make_image_bytes("PNG", (50, 50)))
    destination = settings.media_dir / chemin
    assert destination.exists()

    delete_profile_photo(chemin)

    assert not destination.exists()


def test_delete_profile_photo_tolere_fichier_absent():
    delete_profile_photo("inexistant.png")
