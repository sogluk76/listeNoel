import pytest

from app.models import Reservation
from app.services.visibility import (
    GiftNotFoundError,
    IsRecipientError,
    get_commentable_gift,
    get_visible_gift,
    visible_gift_count,
    visible_gifts_for,
)


def test_us10_cadeau_personnel_compte_pour_le_destinataire_lui_meme(db_session, alice, create_gift):
    create_gift(alice)

    assert visible_gift_count(db_session, alice, alice) == 1


def test_us10_suggestion_ne_compte_pas_pour_le_destinataire_lui_meme(
    db_session, alice, bob, create_gift
):
    create_gift(bob, recipient=alice)

    assert visible_gift_count(db_session, alice, alice) == 0


def test_us10_suggestion_compte_pour_un_autre_viewer(db_session, alice, bob, chloe, create_gift):
    create_gift(bob, recipient=alice)

    assert visible_gift_count(db_session, chloe, alice) == 1
    assert visible_gift_count(db_session, bob, alice) == 1


def test_us10_cadeau_retire_jamais_compte(db_session, alice, chloe, create_gift):
    create_gift(alice, removed=True)

    assert visible_gift_count(db_session, alice, alice) == 0
    assert visible_gift_count(db_session, chloe, alice) == 0


def test_us10_cadeau_archive_jamais_compte(db_session, alice, chloe, create_gift):
    create_gift(alice, archived_year=2025)

    assert visible_gift_count(db_session, alice, alice) == 0
    assert visible_gift_count(db_session, chloe, alice) == 0


def test_us10_cadeau_achete_compte_toujours(db_session, alice, bob, create_gift):
    create_gift(alice, purchased_by=bob)

    assert visible_gift_count(db_session, alice, alice) == 1
    assert visible_gift_count(db_session, bob, alice) == 1


def test_us10_scenario_alice_et_bob_suit_la_matrice_rg30(
    db_session, alice, bob, chloe, create_gift
):
    create_gift(alice, name="Cadeau perso Alice")
    create_gift(bob, recipient=alice, name="Suggestion de Bob pour Alice")
    create_gift(bob, name="Cadeau perso Bob")
    create_gift(chloe, recipient=bob, name="Suggestion de Chloé pour Bob")

    assert visible_gift_count(db_session, alice, alice) == 1
    assert visible_gift_count(db_session, alice, bob) == 2


def test_us13_propre_liste_exclut_les_suggestions(db_session, alice, bob, create_gift):
    create_gift(alice)
    create_gift(bob, recipient=alice)

    vues = visible_gifts_for(db_session, alice, alice)

    assert len(vues) == 1
    assert vues[0].gift.author_id == alice.id


def test_us13_propre_liste_naffiche_ni_statut_ni_reservants_ni_commentaires(
    db_session, alice, create_gift
):
    create_gift(alice)

    vues = visible_gifts_for(db_session, alice, alice)

    assert vues[0].status is None
    assert vues[0].reservants == []
    assert vues[0].comment_count == 0
    assert vues[0].suggested_by is None


def test_us13_liste_dun_autre_inclut_les_suggestions_avec_statut(
    db_session, alice, bob, create_gift
):
    create_gift(bob)
    create_gift(alice, recipient=bob)

    vues = visible_gifts_for(db_session, alice, bob)

    assert len(vues) == 2
    suggestion = next(v for v in vues if v.is_suggestion)
    assert suggestion.suggested_by.id == alice.id
    assert suggestion.status == "disponible"


def test_us13_cadeau_retire_absent_chez_son_auteur_mais_visible_chez_les_autres(
    db_session, alice, bob, create_gift
):
    create_gift(alice, removed=True)

    assert visible_gifts_for(db_session, alice, alice) == []

    vues_bob = visible_gifts_for(db_session, bob, alice)
    assert len(vues_bob) == 1
    assert vues_bob[0].is_removed is True
    assert vues_bob[0].removed_by.id == alice.id
    assert vues_bob[0].status == "retiré"


def test_us13_cadeau_archive_jamais_visible(db_session, alice, bob, create_gift):
    create_gift(alice, archived_year=2025)

    assert visible_gifts_for(db_session, alice, alice) == []
    assert visible_gifts_for(db_session, bob, alice) == []


def test_us13_statut_achete(db_session, alice, bob, create_gift):
    create_gift(alice, purchased_by=bob)

    vues = visible_gifts_for(db_session, bob, alice)

    assert vues[0].status == "acheté"


def test_us13_statut_reserve_et_reservants(db_session, alice, bob, create_gift):
    gift = create_gift(alice)
    db_session.add(Reservation(gift_id=gift.id, user_id=bob.id))
    db_session.commit()

    vues = visible_gifts_for(db_session, bob, alice)

    assert vues[0].status == "réservé"
    assert vues[0].reservants[0].id == bob.id


def test_us15_destinataire_voit_le_detail_de_son_cadeau_personnel(db_session, alice, create_gift):
    gift = create_gift(alice)

    vue = get_visible_gift(db_session, alice, gift.id)

    assert vue.gift.id == gift.id


def test_us15_destinataire_dune_suggestion_recoit_404(db_session, alice, bob, create_gift):
    gift = create_gift(bob, recipient=alice)

    with pytest.raises(GiftNotFoundError):
        get_visible_gift(db_session, alice, gift.id)


def test_us15_auteur_voit_sa_suggestion_chez_le_destinataire(db_session, alice, bob, create_gift):
    gift = create_gift(alice, recipient=bob)

    vue = get_visible_gift(db_session, alice, gift.id)

    assert vue.suggested_by.id == alice.id


def test_us15_autre_membre_voit_le_cadeau_avec_son_statut(db_session, bob, chloe, create_gift):
    gift = create_gift(bob)

    vue = get_visible_gift(db_session, chloe, gift.id)

    assert vue.status == "disponible"


def test_us15_cadeau_retire_absent_chez_son_auteur(db_session, alice, create_gift):
    gift = create_gift(alice, removed=True)

    with pytest.raises(GiftNotFoundError):
        get_visible_gift(db_session, alice, gift.id)


def test_us15_cadeau_archive_404_pour_tous(db_session, alice, bob, create_gift):
    gift = create_gift(alice, archived_year=2025)

    with pytest.raises(GiftNotFoundError):
        get_visible_gift(db_session, alice, gift.id)
    with pytest.raises(GiftNotFoundError):
        get_visible_gift(db_session, bob, gift.id)


def test_us15_cadeau_inexistant_404(db_session, alice):
    with pytest.raises(GiftNotFoundError):
        get_visible_gift(db_session, alice, 9999)


def test_us20_destinataire_dun_cadeau_personnel_leve_is_recipient(db_session, alice, create_gift):
    gift = create_gift(alice, name="Vélo")

    with pytest.raises(IsRecipientError):
        get_commentable_gift(db_session, alice, gift.id)


def test_us20_destinataire_dune_suggestion_leve_is_recipient(db_session, alice, bob, create_gift):
    gift = create_gift(bob, recipient=alice, name="Cadeau secret")

    with pytest.raises(IsRecipientError):
        get_commentable_gift(db_session, alice, gift.id)


def test_us20_autre_membre_accede_au_cadeau(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo")

    assert get_commentable_gift(db_session, bob, gift.id) is gift


def test_us20_cadeau_retire_reste_commentable(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo", removed=True)

    assert get_commentable_gift(db_session, bob, gift.id) is gift


def test_us20_cadeau_archive_leve_not_found(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo", archived_year=2025)

    with pytest.raises(GiftNotFoundError):
        get_commentable_gift(db_session, bob, gift.id)


def test_us20_cadeau_inexistant_leve_not_found(db_session, bob):
    with pytest.raises(GiftNotFoundError):
        get_commentable_gift(db_session, bob, 9999)
