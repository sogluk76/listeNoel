from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.db import get_db
from app.security import current_admin, get_csrf_token, verify_csrf
from app.services.users import (
    AuthenticationError,
    MemberNotFoundError,
    authenticate,
    create_member,
    get_member,
    list_members,
    reset_password,
    unlock_member,
    update_member,
)
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
async def nouveau_membre(
    request: Request,
    first_name: str = Form(...),
    password: str = Form(...),
    password_confirmation: str = Form(...),
    photo: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    _admin=Depends(current_admin),
):
    photo_bytes = await photo.read() if photo is not None and photo.filename else None

    try:
        membre = create_member(db, first_name, password, password_confirmation, photo=photo_bytes)
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


@router.get("/membres")
def liste_membres(request: Request, db: Session = Depends(get_db), admin=Depends(current_admin)):
    return templates.TemplateResponse(
        request,
        "admin/membres.html",
        {"csrf_token": get_csrf_token(request), "membres": list_members(db)},
    )


@router.get("/membres/{member_id}/modifier")
def modifier_membre_form(
    member_id: int,
    request: Request,
    succes: str | None = None,
    db: Session = Depends(get_db),
    _admin=Depends(current_admin),
):
    try:
        membre = get_member(db, member_id)
    except MemberNotFoundError as exc:
        raise HTTPException(status_code=404) from exc
    return templates.TemplateResponse(
        request,
        "admin/modifier_membre.html",
        {
            "csrf_token": get_csrf_token(request),
            "membre": membre,
            "erreur_profil": None,
            "erreur_mot_de_passe": None,
            "succes": succes,
        },
    )


@router.post("/membres/{member_id}/modifier", dependencies=[Depends(verify_csrf)])
async def modifier_membre(
    member_id: int,
    request: Request,
    first_name: str = Form(...),
    active: bool = Form(False),
    remove_photo: bool = Form(False),
    photo: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    _admin=Depends(current_admin),
):
    photo_bytes = await photo.read() if photo is not None and photo.filename else None

    try:
        membre = update_member(
            db,
            member_id,
            first_name,
            is_active=active,
            photo=photo_bytes,
            remove_photo=remove_photo,
        )
    except MemberNotFoundError as exc:
        raise HTTPException(status_code=404) from exc
    except ValueError as exc:
        return templates.TemplateResponse(
            request,
            "admin/modifier_membre.html",
            {
                "csrf_token": get_csrf_token(request),
                "membre": get_member(db, member_id),
                "erreur_profil": str(exc),
                "erreur_mot_de_passe": None,
                "succes": None,
            },
            status_code=400,
        )
    return RedirectResponse(f"/admin/membres/{membre.id}/modifier?succes=profil", status_code=303)


@router.post("/membres/{member_id}/mot-de-passe", dependencies=[Depends(verify_csrf)])
def reinitialiser_mot_de_passe(
    member_id: int,
    request: Request,
    password: str = Form(...),
    password_confirmation: str = Form(...),
    db: Session = Depends(get_db),
    _admin=Depends(current_admin),
):
    try:
        reset_password(db, member_id, password, password_confirmation)
    except MemberNotFoundError as exc:
        raise HTTPException(status_code=404) from exc
    except ValueError as exc:
        return templates.TemplateResponse(
            request,
            "admin/modifier_membre.html",
            {
                "csrf_token": get_csrf_token(request),
                "membre": get_member(db, member_id),
                "erreur_profil": None,
                "erreur_mot_de_passe": str(exc),
                "succes": None,
            },
            status_code=400,
        )
    return RedirectResponse(
        f"/admin/membres/{member_id}/modifier?succes=mot_de_passe", status_code=303
    )


@router.post("/membres/{member_id}/debloquer", dependencies=[Depends(verify_csrf)])
def debloquer_membre(
    member_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(current_admin),
):
    try:
        unlock_member(db, member_id)
    except MemberNotFoundError as exc:
        raise HTTPException(status_code=404) from exc
    return RedirectResponse(
        f"/admin/membres/{member_id}/modifier?succes=deblocage", status_code=303
    )
