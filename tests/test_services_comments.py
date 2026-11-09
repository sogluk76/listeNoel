import pytest

from app.services.comments import create_comment
from app.services.visibility import IsRecipientError


def test_us21_message_enregistre_avec_le_bon_auteur(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo")

    comment = create_comment(db_session, bob, gift.id, "Super idée !")

    assert comment.gift_id == gift.id
    assert comment.author_id == bob.id
    assert comment.content == "Super idée !"


def test_us21_message_vide_refuse(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo")

    with pytest.raises(ValueError):
        create_comment(db_session, bob, gift.id, "   ")


def test_us21_message_trop_long_refuse(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo")

    with pytest.raises(ValueError):
        create_comment(db_session, bob, gift.id, "a" * 1001)


def test_us21_message_de_1000_caracteres_accepte(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo")

    comment = create_comment(db_session, bob, gift.id, "a" * 1000)

    assert len(comment.content) == 1000


def test_us21_emojis_enregistres(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo")

    comment = create_comment(db_session, bob, gift.id, "Trop bien 🎉🎄")

    assert comment.content == "Trop bien 🎉🎄"


def test_us21_destinataire_leve_is_recipient(db_session, alice, create_gift):
    gift = create_gift(alice, name="Vélo")

    with pytest.raises(IsRecipientError):
        create_comment(db_session, alice, gift.id, "Je commente mon propre cadeau")


def test_us21_badge_incremente(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo")

    create_comment(db_session, bob, gift.id, "Un")
    create_comment(db_session, bob, gift.id, "Deux")

    assert len(gift.comments) == 2
