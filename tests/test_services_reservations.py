import pytest

from app.services.reservations import IsRecipientError, cancel_reservation, reserve_gift
from app.services.visibility import GiftNotFoundError


def test_us18_deux_membres_differents_peuvent_reserver(db_session, alice, bob, chloe, create_gift):
    gift = create_gift(alice, name="Vélo")

    reserve_gift(db_session, bob, gift.id)
    reserve_gift(db_session, chloe, gift.id)

    assert {r.user_id for r in gift.reservations} == {bob.id, chloe.id}


def test_us18_reservation_double_refusee(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo")
    reserve_gift(db_session, bob, gift.id)

    with pytest.raises(ValueError):
        reserve_gift(db_session, bob, gift.id)


def test_us18_annulation_de_sa_propre_reservation(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo")
    reserve_gift(db_session, bob, gift.id)

    cancel_reservation(db_session, bob, gift.id)

    assert gift.reservations == []


def test_us18_destinataire_leve_is_recipient_pour_reserver(db_session, alice, create_gift):
    gift = create_gift(alice, name="Vélo")

    with pytest.raises(IsRecipientError):
        reserve_gift(db_session, alice, gift.id)


def test_us18_destinataire_leve_is_recipient_pour_annuler(db_session, alice, create_gift):
    gift = create_gift(alice, name="Vélo")

    with pytest.raises(IsRecipientError):
        cancel_reservation(db_session, alice, gift.id)


def test_us18_reserver_cadeau_achete_refuse(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo", purchased_by=bob)

    with pytest.raises(ValueError):
        reserve_gift(db_session, bob, gift.id)


def test_us18_reserver_cadeau_retire_refuse(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo", removed=True)

    with pytest.raises(ValueError):
        reserve_gift(db_session, bob, gift.id)


def test_us18_annuler_cadeau_achete_refuse(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo", purchased_by=bob)

    with pytest.raises(ValueError):
        cancel_reservation(db_session, bob, gift.id)


def test_us18_cadeau_archive_leve_not_found(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo", archived_year=2025)

    with pytest.raises(GiftNotFoundError):
        reserve_gift(db_session, bob, gift.id)


def test_us18_cadeau_inexistant_leve_not_found(db_session, bob):
    with pytest.raises(GiftNotFoundError):
        reserve_gift(db_session, bob, 9999)


def test_us18_annuler_sans_reservation_refuse(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo")

    with pytest.raises(ValueError):
        cancel_reservation(db_session, bob, gift.id)
