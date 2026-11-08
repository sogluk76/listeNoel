import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Comment, Gift, Reservation, User


def _make_user(session, first_name, **kwargs):
    user = User(first_name=first_name, password_hash="hash", **kwargs)
    session.add(user)
    session.commit()
    return user


def _make_gift(session, recipient, author=None, **kwargs):
    author_id = (author or recipient).id
    gift = Gift(name="Vélo", recipient_id=recipient.id, author_id=author_id, **kwargs)
    session.add(gift)
    session.commit()
    return gift


def test_role_par_defaut_membre(db_session):
    user = User(first_name="Alice", password_hash="hash")
    db_session.add(user)
    db_session.commit()

    assert user.role == "member"
    assert user.is_active is True
    assert user.failed_login_count == 0


def test_prenom_unique(db_session, alice):
    db_session.add(User(first_name="Alice", password_hash="hash"))

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_role_invalide_refuse(db_session):
    db_session.add(User(first_name="Alice", password_hash="hash", role="superadmin"))

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_nom_de_cadeau_vide_refuse(db_session, alice):
    db_session.add(Gift(name="   ", recipient_id=alice.id, author_id=alice.id))

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_prix_negatif_refuse(db_session, alice):
    db_session.add(Gift(name="Vélo", price=-1, recipient_id=alice.id, author_id=alice.id))

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_acheteur_ne_peut_pas_etre_le_destinataire(db_session, alice):
    db_session.add(
        Gift(
            name="Vélo",
            recipient_id=alice.id,
            author_id=alice.id,
            purchased_by_id=alice.id,
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_commentaire_vide_refuse(db_session, alice):
    gift = _make_gift(db_session, alice)
    db_session.add(Comment(gift_id=gift.id, author_id=alice.id, content="   "))

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_commentaire_trop_long_refuse(db_session, alice):
    gift = _make_gift(db_session, alice)
    db_session.add(Comment(gift_id=gift.id, author_id=alice.id, content="x" * 1001))

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_foreign_keys_actives_empeche_commentaire_orphelin(db_session):
    db_session.add(Comment(gift_id=999, author_id=999, content="test"))

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_reservation_dupliquee_refusee(db_session, alice, bob):
    gift = _make_gift(db_session, alice)

    db_session.add(Reservation(gift_id=gift.id, user_id=bob.id))
    db_session.commit()

    db_session.add(Reservation(gift_id=gift.id, user_id=bob.id))
    with pytest.raises(IntegrityError):
        db_session.commit()
