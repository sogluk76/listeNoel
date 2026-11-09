from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.db import get_db
from app.security import current_member, get_csrf_token, verify_csrf
from app.services.users import update_own_photo
from app.templating import templates

router = APIRouter()


@router.get("/profil")
def profil(request: Request, membre=Depends(current_member)):
    return templates.TemplateResponse(
        request,
        "profile.html",
        {"csrf_token": get_csrf_token(request), "membre": membre, "erreur_photo": None},
    )


@router.post("/profil/photo", dependencies=[Depends(verify_csrf)])
async def changer_photo(
    request: Request,
    remove_photo: str = Form("non"),
    photo: UploadFile | None = File(None),
    membre=Depends(current_member),
    db: Session = Depends(get_db),
):
    """RG-36 (US-23)."""
    photo_bytes = await photo.read() if photo is not None and photo.filename else None

    try:
        update_own_photo(db, membre, photo=photo_bytes, remove_photo=(remove_photo == "oui"))
    except ValueError as exc:
        return templates.TemplateResponse(
            request,
            "profile.html",
            {"csrf_token": get_csrf_token(request), "membre": membre, "erreur_photo": str(exc)},
            status_code=400,
        )
    return RedirectResponse("/profil", status_code=303)
