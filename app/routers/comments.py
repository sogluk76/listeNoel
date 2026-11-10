"""Commentaires d'un cadeau (US-20 à US-22).

Chaque route passe par visibility.get_gift_with_secrets : le destinataire reçoit
une erreur 403, y compris sur le fragment de rafraîchissement HTMX.
"""

from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import Invalid
from app.models import User
from app.security import current_member, flash
from app.services import comments as comments_service
from app.services import visibility
from app.web import fragment, is_htmx, redirect, render

router = APIRouter()


def _thread(request: Request, user: User, gift, error: str | None = None, status_code: int = 200):
    return fragment(
        request,
        "_comment_thread.html",
        {"gift": gift, "comments": comments_service.thread(gift), "user": user, "error": error},
        status_code=status_code,
    )


@router.get("/cadeaux/{gift_id}/commentaires")
def comments_page(
    request: Request,
    gift_id: int,
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    gift = visibility.get_gift_with_secrets(db, user, gift_id)
    return render(
        request,
        "comments.html",
        {"gift": gift, "comments": comments_service.thread(gift), "error": None},
        user=user,
    )


@router.get("/cadeaux/{gift_id}/commentaires/fil")
def comments_thread(
    request: Request,
    gift_id: int,
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    """Fragment rechargé toutes les 20 secondes (RG-34)."""
    gift = visibility.get_gift_with_secrets(db, user, gift_id)
    return _thread(request, user, gift)


@router.post("/cadeaux/{gift_id}/commentaires")
def add_comment(
    request: Request,
    gift_id: int,
    content: str = Form(""),
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    gift = visibility.get_gift_with_secrets(db, user, gift_id)
    try:
        comments_service.add(db, user, gift, content)
    except Invalid as exc:
        if is_htmx(request):
            return _thread(request, user, gift, error=exc.message, status_code=422)
        return render(
            request,
            "comments.html",
            {"gift": gift, "comments": comments_service.thread(gift), "error": exc.message},
            user=user,
            status_code=422,
        )
    if is_htmx(request):
        return _thread(request, user, gift)
    return redirect(f"/cadeaux/{gift_id}/commentaires")


@router.get("/commentaires/{comment_id}/modifier")
def edit_comment_form(
    request: Request,
    comment_id: int,
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    comment = comments_service.get_own(db, user, comment_id)
    return render(
        request,
        "comment_edit.html",
        {"comment": comment, "content": comment.content, "error": None},
        user=user,
    )


@router.post("/commentaires/{comment_id}/modifier")
def edit_comment(
    request: Request,
    comment_id: int,
    content: str = Form(""),
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    comment = comments_service.get_own(db, user, comment_id)
    try:
        comments_service.edit(db, comment, content)
    except Invalid as exc:
        return render(
            request,
            "comment_edit.html",
            {"comment": comment, "content": content, "error": exc.message},
            user=user,
            status_code=422,
        )
    flash(request, "Message modifié.")
    return redirect(f"/cadeaux/{comment.gift_id}/commentaires")


@router.post("/commentaires/{comment_id}/supprimer")
def delete_comment(
    request: Request,
    comment_id: int,
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    comment = comments_service.get_own(db, user, comment_id)
    gift = comment.gift
    comments_service.delete(db, comment)
    if is_htmx(request):
        db.refresh(gift)
        return _thread(request, user, gift)
    return redirect(f"/cadeaux/{gift.id}/commentaires")
