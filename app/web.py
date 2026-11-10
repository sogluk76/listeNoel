"""Rendu des templates : filtres d'affichage et contexte commun."""

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.models import User
from app.security import csrf_token, pop_flashes
from app.services.text import color_index, initials

PARIS = ZoneInfo("Europe/Paris")
THIN_SPACE = "\u202f"
STATUS_LABELS = {
    "available": "Disponible",
    "reserved": "Réservé",
    "bought": "Acheté",
    "removed": "Retiré",
}

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def format_datetime(value: datetime | None) -> str:
    """UTC en base -> « 07/12/2025 17:00 » à l'heure de Paris."""
    if value is None:
        return ""
    return value.replace(tzinfo=UTC).astimezone(PARIS).strftime("%d/%m/%Y %H:%M")


def format_date(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.replace(tzinfo=UTC).astimezone(PARIS).strftime("%d/%m/%Y")


def format_price(value: Decimal | int | None) -> str:
    """39.99 -> « 39,99 € »."""
    if value is None:
        return ""
    whole, _, cents = f"{Decimal(value):.2f}".partition(".")
    groups = []
    while len(whole) > 3:
        groups.insert(0, whole[-3:])
        whole = whole[:-3]
    groups.insert(0, whole)
    return f"{' '.join(groups)},{cents} €"


templates.env.filters["dt"] = format_datetime
templates.env.filters["d"] = format_date
templates.env.filters["price"] = format_price
templates.env.filters["initials"] = initials
templates.env.filters["color_index"] = color_index
templates.env.globals["STATUS_LABELS"] = STATUS_LABELS


def render(
    request: Request,
    name: str,
    context: dict | None = None,
    user: User | None = None,
    status_code: int = 200,
) -> HTMLResponse:
    ctx = dict(context or {})
    ctx["user"] = user
    ctx["csrf_token"] = csrf_token(request)
    ctx["flashes"] = pop_flashes(request)
    ctx["settings"] = settings
    return templates.TemplateResponse(request, name, ctx, status_code=status_code)


def fragment(
    request: Request, name: str, context: dict | None = None, status_code: int = 200
) -> HTMLResponse:
    """Fragment HTMX : ne consomme pas les messages flash."""
    ctx = dict(context or {})
    ctx["csrf_token"] = csrf_token(request)
    ctx["settings"] = settings
    return templates.TemplateResponse(request, name, ctx, status_code=status_code)


def redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=303)


def is_htmx(request: Request) -> bool:
    return (
        request.headers.get("HX-Request") == "true"
        and request.headers.get("HX-History-Restore-Request") != "true"
    )


def htmx_redirect(url: str) -> Response:
    return Response(status_code=200, headers={"HX-Redirect": url})
