from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.db import get_db
from app.models import User
from app.security import current_member, get_csrf_token, verify_csrf
from app.services.gifts import create_gift
from app.services.users import MemberNotFoundError, get_active_member
from app.services.visibility import visible_gifts_for
from app.templating import templates

router = APIRouter()


@router.get("/personnes/{person_id}")
def liste_cadeaux(
    person_id: int,
    request: Request,
    membre: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    """RG-30 (US-13) : liste de cadeaux d'une personne, filtrée selon le viewer."""
    try:
        personne = get_active_member(db, person_id)
    except MemberNotFoundError as exc:
        raise HTTPException(status_code=404) from exc

    return templates.TemplateResponse(
        request,
        "gifts/liste.html",
        {
            "csrf_token": get_csrf_token(request),
            "personne": personne,
            "cadeaux": visible_gifts_for(db, membre, personne),
        },
    )


@router.get("/cadeaux/nouveau")
def nouveau_cadeau_form(request: Request, _membre: User = Depends(current_member)):
    return templates.TemplateResponse(
        request, "gifts/nouveau.html", {"csrf_token": get_csrf_token(request), "erreur": None}
    )


@router.post("/cadeaux/nouveau", dependencies=[Depends(verify_csrf)])
async def creer_cadeau(
    request: Request,
    name: str = Form(...),
    price: str = Form(""),
    url: str = Form(""),
    image: UploadFile | None = File(None),
    membre: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    image_bytes = await image.read() if image is not None and image.filename else None
    try:
        create_gift(db, membre, name, price=price or None, url=url or None, image=image_bytes)
    except ValueError as exc:
        return templates.TemplateResponse(
            request,
            "gifts/nouveau.html",
            {"csrf_token": get_csrf_token(request), "erreur": str(exc)},
            status_code=400,
        )
    return RedirectResponse("/", status_code=303)
