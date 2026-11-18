"""Menu des applications (RG-58) et accueil de la liste de Noël : les personnes (US-10)."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.security import current_member
from app.services import visibility
from app.web import render

router = APIRouter()

# Applications proposées dans le menu, dans l'ordre d'affichage.
APPS = [
    {
        "href": "/noel",
        "icon": "gift",
        "name": "Liste de Noël",
        "text": "Les listes de cadeaux de la famille.",
    },
    {
        "href": "/courses",
        "icon": "cart",
        "name": "Liste de courses",
        "text": "Les listes de courses partagées.",
    },
]


@router.get("/")
def menu(request: Request, user: User = Depends(current_member)):
    """Page d'arrivée après la connexion : on choisit l'application (RG-58)."""
    return render(request, "menu.html", {"apps": APPS}, user=user)


@router.get("/noel")
def people(request: Request, user: User = Depends(current_member), db: Session = Depends(get_db)):
    return render(
        request,
        "people.html",
        {"people": visibility.people_with_counts(db, user)},
        user=user,
    )
