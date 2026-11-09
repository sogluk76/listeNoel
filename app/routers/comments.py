from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.security import current_member, get_csrf_token, verify_csrf
from app.services.comments import (
    CommentNotFoundError,
    NotCommentAuthorError,
    create_comment,
    delete_comment,
    get_own_comment,
    update_comment,
)
from app.services.visibility import GiftNotFoundError, IsRecipientError, get_commentable_gift
from app.templating import templates

router = APIRouter()


@router.get("/cadeaux/{gift_id}/commentaires")
def fil_commentaires(
    gift_id: int,
    request: Request,
    membre: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    """RG-30/RG-31 (US-20)."""
    try:
        gift = get_commentable_gift(db, membre, gift_id)
    except GiftNotFoundError as exc:
        raise HTTPException(status_code=404) from exc
    except IsRecipientError as exc:
        raise HTTPException(status_code=403) from exc

    return templates.TemplateResponse(
        request,
        "comments/fil.html",
        {"csrf_token": get_csrf_token(request), "membre": membre, "gift": gift},
    )


@router.get("/cadeaux/{gift_id}/commentaires/fil")
def rafraichir_commentaires(
    gift_id: int,
    request: Request,
    membre: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    """RG-30/RG-34 (US-20) : fragment HTMX, interrogé toutes les 20 secondes. Même
    contrôle d'accès que l'écran complet (AC : refusé au destinataire y compris sur
    cette URL de rafraîchissement).
    """
    try:
        gift = get_commentable_gift(db, membre, gift_id)
    except GiftNotFoundError as exc:
        raise HTTPException(status_code=404) from exc
    except IsRecipientError as exc:
        raise HTTPException(status_code=403) from exc

    return templates.TemplateResponse(
        request,
        "comments/_messages.html",
        {"csrf_token": get_csrf_token(request), "membre": membre, "gift": gift},
    )


@router.post("/cadeaux/{gift_id}/commentaires", dependencies=[Depends(verify_csrf)])
def ecrire_commentaire(
    gift_id: int,
    request: Request,
    content: str = Form(...),
    membre: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    """RG-33 (US-21)."""
    try:
        create_comment(db, membre, gift_id, content)
    except GiftNotFoundError as exc:
        raise HTTPException(status_code=404) from exc
    except IsRecipientError as exc:
        raise HTTPException(status_code=403) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    gift = get_commentable_gift(db, membre, gift_id)
    return templates.TemplateResponse(
        request,
        "comments/_messages.html",
        {"csrf_token": get_csrf_token(request), "membre": membre, "gift": gift},
    )


@router.get("/commentaires/{comment_id}/modifier")
def modifier_commentaire_form(
    comment_id: int,
    request: Request,
    membre: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    """RG-35 (US-22)."""
    try:
        comment = get_own_comment(db, membre, comment_id)
    except CommentNotFoundError as exc:
        raise HTTPException(status_code=404) from exc
    except NotCommentAuthorError as exc:
        raise HTTPException(status_code=403) from exc

    return templates.TemplateResponse(
        request,
        "comments/_edit_form.html",
        {"csrf_token": get_csrf_token(request), "comment": comment},
    )


@router.post("/commentaires/{comment_id}/modifier", dependencies=[Depends(verify_csrf)])
def modifier_commentaire(
    comment_id: int,
    request: Request,
    content: str = Form(...),
    membre: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    """RG-33/RG-35 (US-22)."""
    try:
        comment = update_comment(db, membre, comment_id, content)
    except CommentNotFoundError as exc:
        raise HTTPException(status_code=404) from exc
    except NotCommentAuthorError as exc:
        raise HTTPException(status_code=403) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return templates.TemplateResponse(
        request,
        "comments/_message.html",
        {"csrf_token": get_csrf_token(request), "membre": membre, "comment": comment},
    )


@router.post("/commentaires/{comment_id}/supprimer", dependencies=[Depends(verify_csrf)])
def supprimer_commentaire(
    comment_id: int,
    membre: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    """RG-35 (US-22)."""
    try:
        delete_comment(db, membre, comment_id)
    except CommentNotFoundError as exc:
        raise HTTPException(status_code=404) from exc
    except NotCommentAuthorError as exc:
        raise HTTPException(status_code=403) from exc

    return HTMLResponse("")
