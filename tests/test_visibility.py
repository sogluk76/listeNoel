from app.services.visibility import visible_gift_count


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
