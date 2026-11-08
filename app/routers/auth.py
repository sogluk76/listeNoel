from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.db import get_db
from app.models import User
from app.security import current_member, get_csrf_token, user_from_session, verify_csrf
from app.services.users import AuthenticationError, authenticate, list_active_members
from app.templating import templates

router = APIRouter()


@router.get("/login")
def login_form(request: Request, db: Session = Depends(get_db)):
    membre = user_from_session(request, db)
    if membre is not None and membre.role == "member":
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(
        request,
        "login.html",
        {
            "csrf_token": get_csrf_token(request),
            "membres": list_active_members(db),
            "erreur": None,
        },
    )


@router.post("/login", dependencies=[Depends(verify_csrf)])
def login(
    request: Request,
    first_name: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        user = authenticate(db, first_name, password, role="member")
    except AuthenticationError as exc:
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "csrf_token": get_csrf_token(request),
                "membres": list_active_members(db),
                "erreur": str(exc),
            },
            status_code=400,
        )
    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=303)


@router.post("/logout", dependencies=[Depends(verify_csrf)])
def logout(request: Request, _membre: User = Depends(current_member)):
    """RG-07 : destruction de la session, réservée au membre connecté (RG-09)."""
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@router.get("/login/photo")
def login_photo(request: Request, first_name: str = "", db: Session = Depends(get_db)):
    """Fragment HTMX (RG-04) : photo ou placeholder initiales pour le prénom sélectionné.

    Un prénom inconnu ou désactivé retombe silencieusement sur un placeholder vide (pas
    d'initiales, pas d'erreur) : la liste déroulante ne proposant que des membres actifs,
    ce cas ne peut survenir qu'en forgeant la requête, et ne doit rien laisser deviner.
    """
    membre = next((m for m in list_active_members(db) if m.first_name == first_name), None)
    return templates.TemplateResponse(request, "_photo_login.html", {"membre": membre})
