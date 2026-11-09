import pytest

from app.services.purchases import (
    NotPurchaserError,
    NotReservantError,
    cancel_purchase,
    mark_purchased,
)
from app.services.reservations import reserve_gift
from app.services.visibility import GiftNotFoundError, IsRecipientError


def test_us19_reservant_marque_achete(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo")
    reserve_gift(db_session, bob, gift.id)

    mark_purchased(db_session, bob, gift.id)

    assert gift.purchased_by_id == bob.id
    assert gift.purchased_at is not None


def test_us19_non_reservant_leve_not_reservant(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo")

    with pytest.raises(NotReservantError):
        mark_purchased(db_session, bob, gift.id)


def test_us19_destinataire_leve_is_recipient(db_session, alice, create_gift):
    gift = create_gift(alice, name="Vélo")

    with pytest.raises(IsRecipientError):
        mark_purchased(db_session, alice, gift.id)


def test_us19_deja_achete_refuse(db_session, alice, bob, chloe, create_gift):
    gift = create_gift(alice, name="Vélo", purchased_by=bob)

    with pytest.raises(ValueError):
        mark_purchased(db_session, chloe, gift.id)


def test_us19_cadeau_retire_refuse(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo", removed=True)

    with pytest.raises(ValueError):
        mark_purchased(db_session, bob, gift.id)


def test_us19_cadeau_archive_leve_not_found(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo", archived_year=2025)

    with pytest.raises(GiftNotFoundError):
        mark_purchased(db_session, bob, gift.id)


def test_us19_acheteur_annule_lachat_repasse_en_reserve(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo")
    reserve_gift(db_session, bob, gift.id)
    mark_purchased(db_session, bob, gift.id)

    cancel_purchase(db_session, bob, gift.id)

    assert gift.purchased_by_id is None
    assert gift.purchased_at is None
    assert {r.user_id for r in gift.reservations} == {bob.id}


def test_us19_non_acheteur_leve_not_purchaser(db_session, alice, bob, chloe, create_gift):
    gift = create_gift(alice, name="Vélo", purchased_by=bob)

    with pytest.raises(NotPurchaserError):
        cancel_purchase(db_session, chloe, gift.id)


def test_us19_annuler_achat_non_achete_refuse(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo")
    reserve_gift(db_session, bob, gift.id)

    with pytest.raises(ValueError):
        cancel_purchase(db_session, bob, gift.id)


def test_us19_destinataire_leve_is_recipient_pour_annuler(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo", purchased_by=bob)

    with pytest.raises(IsRecipientError):
        cancel_purchase(db_session, alice, gift.id)
