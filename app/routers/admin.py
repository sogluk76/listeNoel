from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.db import get_db
from app.security import current_admin, get_csrf_token, verify_csrf
from app.services.users import AuthenticationError, authenticate, create_member
from app.templating import templates

router = APIRouter(prefix="/admin")


@router.get("/login")
def admin_login_form(request: Request):
    return templates.TemplateResponse(
        request, "admin/login.html", {"csrf_token": get_csrf_token(request), "erreur": None}
    )


@router.post("/login", dependencies=[Depends(verify_csrf)])
def admin_login(
    request: Request,
    first_name: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        user = authenticate(db, first_name, password, role="admin")
    except AuthenticationError as exc:
        return templates.TemplateResponse(
            request,
            "admin/login.html",
            {"csrf_token": get_csrf_token(request), "erreur": str(exc)},
            status_code=400,
        )
    request.session["user_id"] = user.id
    return RedirectResponse("/admin", status_code=303)


@router.get("")
def admin_dashboard(request: Request, admin=Depends(current_admin)):
    return templates.TemplateResponse(
        request,
        "admin/dashboard.html",
        {"csrf_token": get_csrf_token(request), "admin": admin},
    )


@router.get("/membres/nouveau")
def nouveau_membre_form(request: Request, _admin=Depends(current_admin)):
    return templates.TemplateResponse(
        request,
        "admin/nouveau_membre.html",
        {"csrf_token": get_csrf_token(request), "erreur": None, "succes": None},
    )


@router.post("/membres/nouveau", dependencies=[Depends(verify_csrf)])
def nouveau_membre(
    request: Request,
    first_name: str = Form(...),
    password: str = Form(...),
    password_confirmation: str = Form(...),
    db: Session = Depends(get_db),
    _admin=Depends(current_admin),
):
    try:
        membre = create_member(db, first_name, password, password_confirmation)
    except ValueError as exc:
        return templates.TemplateResponse(
            request,
            "admin/nouveau_membre.html",
            {"csrf_token": get_csrf_token(request), "erreur": str(exc), "succes": None},
            status_code=400,
        )
    return templates.TemplateResponse(
        request,
        "admin/nouveau_membre.html",
        {
            "csrf_token": get_csrf_token(request),
            "erreur": None,
            "succes": f"Compte « {membre.first_name} » créé.",
        },
    )
