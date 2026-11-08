from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from app.templating import format_datetime_fr, format_price_fr


def test_format_datetime_fr_date_naive_traitee_comme_utc():
    valeur = datetime(2025, 12, 7, 16, 0)  # UTC -> 17h00 à Paris (heure d'hiver, UTC+1)

    assert format_datetime_fr(valeur) == "07/12/2025 17:00"


def test_format_datetime_fr_convertit_depuis_un_autre_fuseau():
    valeur = datetime(2025, 12, 7, 11, 0, tzinfo=ZoneInfo("America/New_York"))  # UTC-5

    assert format_datetime_fr(valeur) == "07/12/2025 17:00"


def test_format_price_fr_formate_en_francais():
    assert format_price_fr(Decimal("39.99")) == "39,99 €"


def test_format_price_fr_absent_est_une_chaine_vide():
    assert format_price_fr(None) == ""
