from datetime import UTC, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

PARIS_TZ = ZoneInfo("Europe/Paris")


def format_datetime_fr(value: datetime) -> str:
    """Convention du projet : `07/12/2025 17:00`, fuseau Europe/Paris."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=ZoneInfo("UTC"))
    return value.astimezone(PARIS_TZ).strftime("%d/%m/%Y %H:%M")


templates.env.filters["date_fr"] = format_datetime_fr


def est_bloque(membre) -> bool:
    """RG-05 : un compte n'est bloqué que si `locked_until` est dans le futur (sinon le
    prochain essai de connexion le lèvera de lui-même, cf. `authenticate()`)."""
    locked_until = membre.locked_until
    return locked_until is not None and locked_until > datetime.now(UTC).replace(tzinfo=None)


templates.env.filters["est_bloque"] = est_bloque


def format_price_fr(value: Decimal | None) -> str:
    """RG-15 : format français, ex. `39,99 €`."""
    if value is None:
        return ""
    return f"{value:.2f}".replace(".", ",") + " €"


templates.env.filters["prix_fr"] = format_price_fr
