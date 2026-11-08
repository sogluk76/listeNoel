from datetime import datetime
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
