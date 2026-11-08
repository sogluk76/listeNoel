from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.security import current_member, get_csrf_token
from app.services.users import list_active_members
from app.services.visibility import visible_gift_count
from app.templating import templates

router = APIRouter()


@router.get("/")
def people_list(
    request: Request, membre: User = Depends(current_member), db: Session = Depends(get_db)
):
    """RG-12 : liste des membres actifs, moi compris, avec le compteur RG-13/RG-30."""
    membres = list_active_members(db)
    compteurs = {m.id: visible_gift_count(db, membre, m) for m in membres}
    return templates.TemplateResponse(
        request,
        "people.html",
        {
            "csrf_token": get_csrf_token(request),
            "membres": membres,
            "compteurs": compteurs,
        },
    )
