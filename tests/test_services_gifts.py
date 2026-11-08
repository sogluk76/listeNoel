from decimal import Decimal

import pytest

from app.config import settings
from app.services.gifts import create_gift


def test_us11_nom_seul_accepte(db_session, alice):
    gift = create_gift(db_session, alice, "Vélo")

    assert gift.name == "Vélo"
    assert gift.author_id == alice.id
    assert gift.recipient_id == alice.id
    assert gift.price is None


def test_us11_nom_vide_refuse(db_session, alice):
    with pytest.raises(ValueError):
        create_gift(db_session, alice, "")


def test_us11_nom_uniquement_espaces_refuse(db_session, alice):
    with pytest.raises(ValueError):
        create_gift(db_session, alice, "   ")


def test_us11_nom_trop_long_refuse(db_session, alice):
    with pytest.raises(ValueError):
        create_gift(db_session, alice, "a" * 151)


def test_us11_prix_negatif_refuse(db_session, alice):
    with pytest.raises(ValueError):
        create_gift(db_session, alice, "Jeu", price="-5")


def test_us11_prix_trop_de_decimales_refuse(db_session, alice):
    with pytest.raises(ValueError):
        create_gift(db_session, alice, "Jeu", price="12.345")


def test_us11_prix_non_numerique_refuse(db_session, alice):
    with pytest.raises(ValueError):
        create_gift(db_session, alice, "Jeu", price="abc")


def test_us11_prix_virgule_acceptee(db_session, alice):
    gift = create_gift(db_session, alice, "Jeu", price="12,50")

    assert gift.price == Decimal("12.50")


def test_us11_prix_point_accepte(db_session, alice):
    gift = create_gift(db_session, alice, "Jeu", price="12.50")

    assert gift.price == Decimal("12.50")


def test_us11_lien_sans_http_refuse(db_session, alice):
    with pytest.raises(ValueError):
        create_gift(db_session, alice, "Jeu", url="www.exemple.fr")


def test_us11_lien_http_et_https_acceptes(db_session, alice):
    gift_http = create_gift(db_session, alice, "Jeu", url="http://exemple.fr")
    gift_https = create_gift(db_session, alice, "Jeu", url="https://exemple.fr")

    assert gift_http.url == "http://exemple.fr"
    assert gift_https.url == "https://exemple.fr"


def test_us11_image_invalide_refusee(db_session, alice):
    with pytest.raises(ValueError):
        create_gift(db_session, alice, "Jeu", image=b"pas une image")


def test_us11_image_valide_enregistree(db_session, alice, make_image_bytes):
    gift = create_gift(db_session, alice, "Jeu", image=make_image_bytes("PNG"))

    assert gift.image_path is not None
    assert (settings.media_dir / gift.image_path).exists()
