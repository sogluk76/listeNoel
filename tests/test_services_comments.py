import pytest

from app.services.comments import (
    CommentNotFoundError,
    NotCommentAuthorError,
    create_comment,
    delete_comment,
    update_comment,
)
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


def test_us22_auteur_modifie_son_message(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo")
    comment = create_comment(db_session, bob, gift.id, "Premier texte")

    modifie = update_comment(db_session, bob, comment.id, "Texte corrigé")

    assert modifie.content == "Texte corrigé"
    assert modifie.updated_at is not None


def test_us22_modifier_message_dun_autre_leve_not_author(
    db_session, alice, bob, chloe, create_gift
):
    gift = create_gift(alice, name="Vélo")
    comment = create_comment(db_session, bob, gift.id, "Texte de Bob")

    with pytest.raises(NotCommentAuthorError):
        update_comment(db_session, chloe, comment.id, "Piraté")


def test_us22_modifier_message_meme_validations_qua_lecriture(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo")
    comment = create_comment(db_session, bob, gift.id, "Texte")

    with pytest.raises(ValueError):
        update_comment(db_session, bob, comment.id, "   ")


def test_us22_auteur_supprime_son_message(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo")
    comment = create_comment(db_session, bob, gift.id, "À supprimer")
    comment_id = comment.id

    delete_comment(db_session, bob, comment_id)

    assert len(gift.comments) == 0


def test_us22_supprimer_message_dun_autre_leve_not_author(
    db_session, alice, bob, chloe, create_gift
):
    gift = create_gift(alice, name="Vélo")
    comment = create_comment(db_session, bob, gift.id, "Texte de Bob")

    with pytest.raises(NotCommentAuthorError):
        delete_comment(db_session, chloe, comment.id)


def test_us22_commentaire_inexistant_leve_not_found(db_session, bob):
    with pytest.raises(CommentNotFoundError):
        update_comment(db_session, bob, 9999, "Nom")


def test_us22_commentaire_dun_cadeau_archive_leve_not_found(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo")
    comment = create_comment(db_session, bob, gift.id, "Texte")
    gift.archived_year = 2025
    db_session.commit()

    with pytest.raises(CommentNotFoundError):
        update_comment(db_session, bob, comment.id, "Nouveau texte")


def test_us22_commentaire_dun_cadeau_retire_reste_modifiable(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo")
    comment = create_comment(db_session, bob, gift.id, "Texte")
    gift.removed_at = gift.created_at
    db_session.commit()

    modifie = update_comment(db_session, bob, comment.id, "Texte corrigé")

    assert modifie.content == "Texte corrigé"
