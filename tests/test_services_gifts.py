from decimal import Decimal

import pytest

from app.config import settings
from app.models import Comment, Gift, Reservation
from app.services.gifts import (
    NotGiftAuthorError,
    create_gift,
    delete_gift,
    search_and_sort_gifts,
    update_gift,
)
from app.services.visibility import GiftNotFoundError, visible_gifts_for


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


def test_us12_suggestion_cree_avec_auteur_moi_et_destinataire_choisi(db_session, alice, bob):
    gift = create_gift(db_session, alice, "Jeu", is_suggestion=True, recipient_id=bob.id)

    assert gift.author_id == alice.id
    assert gift.recipient_id == bob.id


def test_us12_suggestion_sans_destinataire_refuse(db_session, alice):
    with pytest.raises(ValueError):
        create_gift(db_session, alice, "Jeu", is_suggestion=True)


def test_us12_suggestion_pour_soi_meme_refuse(db_session, alice):
    with pytest.raises(ValueError):
        create_gift(db_session, alice, "Jeu", is_suggestion=True, recipient_id=alice.id)


def test_us12_suggestion_pour_membre_inactif_refuse(db_session, alice, bob):
    bob.is_active = False
    db_session.commit()

    with pytest.raises(ValueError):
        create_gift(db_session, alice, "Jeu", is_suggestion=True, recipient_id=bob.id)


def test_us12_suggestion_pour_admin_refuse(db_session, alice, admin):
    with pytest.raises(ValueError):
        create_gift(db_session, alice, "Jeu", is_suggestion=True, recipient_id=admin.id)


def test_us12_suggestion_pour_destinataire_inexistant_refuse(db_session, alice):
    with pytest.raises(ValueError):
        create_gift(db_session, alice, "Jeu", is_suggestion=True, recipient_id=9999)


def test_us14_recherche_insensible_a_la_casse_et_aux_accents(db_session, alice, create_gift):
    create_gift(alice, name="Vélo électrique")
    create_gift(alice, name="Casque audio")

    vues = search_and_sort_gifts(visible_gifts_for(db_session, alice, alice), q="VELO")

    assert [v.gift.name for v in vues] == ["Vélo électrique"]


def test_us14_tri_prix_croissant_place_les_cadeaux_sans_prix_en_fin(db_session, alice, create_gift):
    create_gift(alice, name="B", price=Decimal("20"))
    create_gift(alice, name="A", price=Decimal("10"))
    create_gift(alice, name="C")

    vues = search_and_sort_gifts(visible_gifts_for(db_session, alice, alice), sort="prix")

    assert [v.gift.name for v in vues] == ["A", "B", "C"]


def test_us14_tri_prix_decroissant_place_aussi_les_cadeaux_sans_prix_en_fin(
    db_session, alice, create_gift
):
    create_gift(alice, name="B", price=Decimal("20"))
    create_gift(alice, name="A", price=Decimal("10"))
    create_gift(alice, name="C")

    vues = search_and_sort_gifts(
        visible_gifts_for(db_session, alice, alice), sort="prix", direction="decroissant"
    )

    assert [v.gift.name for v in vues] == ["B", "A", "C"]


def test_us14_tri_statut_ordonne_disponible_achete_retire(db_session, alice, bob, create_gift):
    create_gift(alice, name="Disponible")
    create_gift(alice, name="Achete", purchased_by=bob)
    create_gift(alice, name="Retire", removed=True)

    vues = search_and_sort_gifts(visible_gifts_for(db_session, bob, alice), sort="statut")

    assert [v.gift.name for v in vues] == ["Disponible", "Achete", "Retire"]


def test_us14_recherche_naffiche_jamais_une_suggestion_sur_sa_propre_liste(
    db_session, alice, bob, create_gift
):
    create_gift(bob, recipient=alice, name="Cadeau secret")

    vues = search_and_sort_gifts(visible_gifts_for(db_session, alice, alice), q="cadeau")

    assert vues == []


def test_us16_auteur_modifie_nom_prix_lien(db_session, alice, create_gift):
    gift = create_gift(alice, name="Vélo", price=Decimal("50"))

    modifie = update_gift(
        db_session, alice, gift.id, "Trottinette", price="30", url="https://ex.fr"
    )

    assert modifie.name == "Trottinette"
    assert modifie.price == Decimal("30")
    assert modifie.url == "https://ex.fr"


def test_us16_autre_membre_leve_not_author(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo")

    with pytest.raises(NotGiftAuthorError):
        update_gift(db_session, bob, gift.id, "Piraté")


def test_us16_cadeau_inexistant_leve_not_found(db_session, alice):
    with pytest.raises(GiftNotFoundError):
        update_gift(db_session, alice, 9999, "Nom")


def test_us16_cadeau_retire_leve_not_found_meme_pour_lauteur(db_session, alice, create_gift):
    gift = create_gift(alice, name="Vélo", removed=True)

    with pytest.raises(GiftNotFoundError):
        update_gift(db_session, alice, gift.id, "Nom")


def test_us16_cadeau_archive_leve_not_found_meme_pour_lauteur(db_session, alice, create_gift):
    gift = create_gift(alice, name="Vélo", archived_year=2025)

    with pytest.raises(GiftNotFoundError):
        update_gift(db_session, alice, gift.id, "Nom")


def test_us16_nom_vide_refuse(db_session, alice, create_gift):
    gift = create_gift(alice, name="Vélo")

    with pytest.raises(ValueError):
        update_gift(db_session, alice, gift.id, "   ")


def test_us16_prix_invalide_refuse(db_session, alice, create_gift):
    gift = create_gift(alice, name="Vélo")

    with pytest.raises(ValueError):
        update_gift(db_session, alice, gift.id, "Vélo", price="-5")


def test_us16_lien_invalide_refuse(db_session, alice, create_gift):
    gift = create_gift(alice, name="Vélo")

    with pytest.raises(ValueError):
        update_gift(db_session, alice, gift.id, "Vélo", url="www.exemple.fr")


def test_us16_remplacer_image_supprime_lancienne(db_session, alice, make_image_bytes):
    gift = create_gift(db_session, alice, "Vélo", image=make_image_bytes("PNG"))
    ancien_image_path = gift.image_path
    ancien_chemin = settings.media_dir / ancien_image_path

    modifie = update_gift(db_session, alice, gift.id, "Vélo", image=make_image_bytes("PNG"))

    assert modifie.image_path != ancien_image_path
    assert not ancien_chemin.exists()
    assert (settings.media_dir / modifie.image_path).exists()


def test_us16_supprimer_image_sans_remplacement(db_session, alice, make_image_bytes):
    gift = create_gift(db_session, alice, "Vélo", image=make_image_bytes("PNG"))
    ancien_chemin = settings.media_dir / gift.image_path

    modifie = update_gift(db_session, alice, gift.id, "Vélo", remove_image=True)

    assert modifie.image_path is None
    assert not ancien_chemin.exists()


def test_us17_autre_membre_leve_not_author(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo")

    with pytest.raises(NotGiftAuthorError):
        delete_gift(db_session, bob, gift.id)


def test_us17_sans_activite_supprime_definitivement_ligne_et_image(
    db_session, alice, make_image_bytes
):
    gift = create_gift(db_session, alice, "Vélo", image=make_image_bytes("PNG"))
    chemin_image = settings.media_dir / gift.image_path
    gift_id = gift.id

    delete_gift(db_session, alice, gift_id)

    assert db_session.get(Gift, gift_id) is None
    assert not chemin_image.exists()


def test_us17_avec_reservation_supprime_en_douceur(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo")
    db_session.add(Reservation(gift_id=gift.id, user_id=bob.id))
    db_session.commit()

    delete_gift(db_session, alice, gift.id)

    db_session.refresh(gift)
    assert gift.removed_at is not None


def test_us17_avec_achat_supprime_en_douceur(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo", purchased_by=bob)

    delete_gift(db_session, alice, gift.id)

    db_session.refresh(gift)
    assert gift.removed_at is not None


def test_us17_avec_commentaire_supprime_en_douceur(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo")
    db_session.add(Comment(gift_id=gift.id, author_id=bob.id, content="Chouette idée"))
    db_session.commit()

    delete_gift(db_session, alice, gift.id)

    db_session.refresh(gift)
    assert gift.removed_at is not None


def test_us17_suppression_douce_conserve_les_donnees(db_session, alice, bob, create_gift):
    gift = create_gift(alice, name="Vélo")
    db_session.add(Reservation(gift_id=gift.id, user_id=bob.id))
    db_session.commit()
    gift_id = gift.id

    delete_gift(db_session, alice, gift_id)

    assert db_session.get(Gift, gift_id) is not None
    assert db_session.query(Reservation).filter_by(gift_id=gift_id).count() == 1


def test_us17_cadeau_inexistant_leve_not_found(db_session, alice):
    with pytest.raises(GiftNotFoundError):
        delete_gift(db_session, alice, 9999)


def test_us17_cadeau_deja_retire_leve_not_found_meme_pour_lauteur(db_session, alice, create_gift):
    gift = create_gift(alice, name="Vélo", removed=True)

    with pytest.raises(GiftNotFoundError):
        delete_gift(db_session, alice, gift.id)
