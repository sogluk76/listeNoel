"""Profil : photo, mot de passe, mes réservations (US-23 à US-25)."""

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import Invalid
from app.models import User
from app.security import current_member, flash, verify_password
from app.services import images, visibility
from app.services import users as users_service
from app.web import redirect, render

router = APIRouter()


def _page(request: Request, db: Session, user: User, error: str | None = None, status_code=200):
    return render(
        request,
        "profile.html",
        {"groups": visibility.my_reservations(db, user), "password_error": error},
        user=user,
        status_code=status_code,
    )


@router.get("/profil")
def profile(request: Request, user: User = Depends(current_member), db: Session = Depends(get_db)):
    return _page(request, db, user)


@router.post("/profil/photo")
def change_photo(
    request: Request,
    photo: UploadFile | None = File(None),
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    if not images.has_file(photo):
        flash(request, "Choisis d'abord une image.", "error")
        return redirect("/profil")
    try:
        new_path = images.save_image(photo, "avatars", images.AVATAR_MAX_SIDE)
    except Invalid as exc:
        flash(request, exc.message, "error")
        return redirect("/profil")
    old_path, user.photo_path = user.photo_path, new_path
    db.commit()
    images.delete_image(old_path)
    flash(request, "Photo mise à jour.")
    return redirect("/profil")


@router.post("/profil/photo/supprimer")
def remove_photo(
    request: Request, user: User = Depends(current_member), db: Session = Depends(get_db)
):
    old_path, user.photo_path = user.photo_path, None
    db.commit()
    images.delete_image(old_path)
    flash(request, "Photo supprimée.")
    return redirect("/profil")


@router.post("/profil/mot-de-passe")
def change_password(
    request: Request,
    current_password: str = Form(""),
    new_password: str = Form(""),
    confirmation: str = Form(""),
    user: User = Depends(current_member),
    db: Session = Depends(get_db),
):
    if not verify_password(user.password_hash, current_password):
        return _page(request, db, user, "Le mot de passe actuel est incorrect.", 422)
    try:
        users_service.set_password(db, user, new_password, confirmation)
    except Invalid as exc:
        return _page(request, db, user, exc.message, 422)
    flash(request, "Mot de passe modifié.")
    return redirect("/profil")
