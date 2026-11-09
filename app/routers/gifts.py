from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.db import get_db
from app.models import User
from app.security import current_member, get_csrf_token, verify_csrf
from app.services.gifts import (
    NotGiftAuthorError,
    create_gift,
    delete_gift,
    get_editable_gift,
    search_and_sort_gifts,
    update_gift,
)
from app.services.users import MemberNotFoundError, get_active_member, list_other_active_members
from app.services.visibility import GiftNotFoundError, get_visible_gift, visible_gifts_for
from app.templating import templates

router = APIRouter()


@router.get("/personnes/{person_id}")
def liste_cadeaux(
    person_id: int,
    request: Request,
    q: str = "",
    tri: str = "nom",
    sens: str = "croissant",
    membre: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    """RG-30 (US-13), RG-24/RG-25 (US-14) : liste de cadeaux d'une personne, filtrée
    selon le viewer, puis recherchée/triée. Le tri par statut n'a pas de sens sur sa
    propre liste (aucun cadeau n'y a de statut) : un `tri=statut` forgé y est ignoré.
    """
    try:
        personne = get_active_member(db, person_id)
    except MemberNotFoundError as exc:
        raise HTTPException(status_code=404) from exc

    est_ma_liste = membre.id == personne.id
    tri_effectif = "nom" if (est_ma_liste and tri == "statut") else tri

    cadeaux = search_and_sort_gifts(
        visible_gifts_for(db, membre, personne), q=q, sort=tri_effectif, direction=sens
    )

    return templates.TemplateResponse(
        request,
        "gifts/liste.html",
        {
            "csrf_token": get_csrf_token(request),
            "personne": personne,
            "cadeaux": cadeaux,
            "q": q,
            "tri": tri_effectif,
            "sens": sens,
            "est_ma_liste": est_ma_liste,
        },
    )


@router.get("/cadeaux/nouveau")
def nouveau_cadeau_form(
    request: Request, membre: User = Depends(current_member), db: Session = Depends(get_db)
):
    return templates.TemplateResponse(
        request,
        "gifts/nouveau.html",
        {
            "csrf_token": get_csrf_token(request),
            "membre": membre,
            "is_suggestion": False,
            "autres_membres": list_other_active_members(db, membre),
            "erreur": None,
        },
    )


@router.get("/cadeaux/nouveau/destinataire")
def destinataire_fragment(
    request: Request,
    is_suggestion: str = "non",
    membre: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    """RG-18/RG-19 (US-12) : fragment HTMX affiché/masqué au basculement de l'interrupteur."""
    return templates.TemplateResponse(
        request,
        "gifts/_destinataire.html",
        {
            "membre": membre,
            "is_suggestion": is_suggestion == "oui",
            "autres_membres": list_other_active_members(db, membre),
        },
    )


@router.post("/cadeaux/nouveau", dependencies=[Depends(verify_csrf)])
async def creer_cadeau(
    request: Request,
    name: str = Form(...),
    price: str = Form(""),
    url: str = Form(""),
    is_suggestion: str = Form("non"),
    recipient_id: str = Form(""),
    image: UploadFile | None = File(None),
    membre: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    image_bytes = await image.read() if image is not None and image.filename else None
    try:
        parsed_recipient_id = int(recipient_id) if recipient_id else None
    except ValueError:
        parsed_recipient_id = None

    try:
        create_gift(
            db,
            membre,
            name,
            price=price or None,
            url=url or None,
            image=image_bytes,
            is_suggestion=(is_suggestion == "oui"),
            recipient_id=parsed_recipient_id,
        )
    except ValueError as exc:
        return templates.TemplateResponse(
            request,
            "gifts/nouveau.html",
            {
                "csrf_token": get_csrf_token(request),
                "membre": membre,
                "is_suggestion": False,
                "autres_membres": list_other_active_members(db, membre),
                "erreur": str(exc),
            },
            status_code=400,
        )
    return RedirectResponse("/", status_code=303)


@router.get("/cadeaux/{gift_id}")
def detail_cadeau(
    gift_id: int,
    request: Request,
    membre: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    """RG-30/RG-40 (US-15) : détail d'un cadeau."""
    try:
        vue = get_visible_gift(db, membre, gift_id)
    except GiftNotFoundError as exc:
        raise HTTPException(status_code=404) from exc

    return templates.TemplateResponse(
        request,
        "gifts/detail.html",
        {"csrf_token": get_csrf_token(request), "membre": membre, "vue": vue},
    )


@router.get("/cadeaux/{gift_id}/modifier")
def modifier_cadeau_form(
    gift_id: int,
    request: Request,
    membre: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    """RG-21 (US-16) : formulaire de modification, réservé à l'auteur."""
    try:
        gift = get_editable_gift(db, membre, gift_id)
    except GiftNotFoundError as exc:
        raise HTTPException(status_code=404) from exc
    except NotGiftAuthorError as exc:
        raise HTTPException(status_code=403) from exc

    return templates.TemplateResponse(
        request,
        "gifts/modifier.html",
        {"csrf_token": get_csrf_token(request), "gift": gift, "erreur": None},
    )


@router.post("/cadeaux/{gift_id}/modifier", dependencies=[Depends(verify_csrf)])
async def modifier_cadeau(
    gift_id: int,
    request: Request,
    name: str = Form(...),
    price: str = Form(""),
    url: str = Form(""),
    remove_image: str = Form("non"),
    image: UploadFile | None = File(None),
    membre: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    image_bytes = await image.read() if image is not None and image.filename else None

    try:
        gift = update_gift(
            db,
            membre,
            gift_id,
            name,
            price=price or None,
            url=url or None,
            image=image_bytes,
            remove_image=(remove_image == "oui"),
        )
    except GiftNotFoundError as exc:
        raise HTTPException(status_code=404) from exc
    except NotGiftAuthorError as exc:
        raise HTTPException(status_code=403) from exc
    except ValueError as exc:
        return templates.TemplateResponse(
            request,
            "gifts/modifier.html",
            {
                "csrf_token": get_csrf_token(request),
                "gift": get_editable_gift(db, membre, gift_id),
                "erreur": str(exc),
            },
            status_code=400,
        )
    return RedirectResponse(f"/cadeaux/{gift.id}", status_code=303)


@router.post("/cadeaux/{gift_id}/supprimer", dependencies=[Depends(verify_csrf)])
def supprimer_cadeau(
    gift_id: int,
    request: Request,
    membre: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    """RG-22 (US-17) : suppression (définitive ou douce) par l'auteur. Même message dans
    les deux cas, pour ne rien révéler au destinataire (règle n°1 — la surprise)."""
    try:
        delete_gift(db, membre, gift_id)
    except GiftNotFoundError as exc:
        raise HTTPException(status_code=404) from exc
    except NotGiftAuthorError as exc:
        raise HTTPException(status_code=403) from exc

    return templates.TemplateResponse(
        request, "gifts/supprime.html", {"csrf_token": get_csrf_token(request)}
    )
