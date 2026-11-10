"""Panel d'administration (US-04 à US-09). Réservé au compte admin (RG-09)."""

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import Invalid, NotFound
from app.models import Gift, User, utcnow
from app.security import current_admin, flash, login_session, logout_session, session_user
from app.services import admin as admin_service
from app.services import gifts as gifts_service
from app.services import images
from app.services import users as users_service
from app.web import redirect, render

router = APIRouter(prefix="/admin")


def _to_int(value: str | None) -> int | None:
    try:
        return int(value) if value not in (None, "") else None
    except ValueError:
        return None


def _get_member(db: Session, member_id: int) -> User:
    member = db.get(User, member_id)
    if member is None or not member.is_member:
        raise NotFound()
    return member


# --- Connexion (US-04) -------------------------------------------------------


@router.get("/login")
def login_form(request: Request, db: Session = Depends(get_db)):
    user = session_user(request, db)
    if user is not None and user.is_admin:
        return redirect("/admin")
    return render(request, "admin/login.html", {"error": None, "name": ""})


@router.post("/login")
def login(
    request: Request,
    name: str = Form(""),
    password: str = Form(""),
    db: Session = Depends(get_db),
):
    account = users_service.find_by_name(db, name) if name.strip() else None
    error = users_service.MSG_BAD_PASSWORD
    if account is not None and account.is_admin and account.is_active:
        result = users_service.authenticate(db, account, password)
        if result == users_service.AUTH_OK:
            login_session(request, account)
            return redirect("/admin")
        if result == users_service.AUTH_LOCKED:
            error = users_service.MSG_LOCKED
    return render(request, "admin/login.html", {"error": error, "name": name}, status_code=401)


@router.post("/logout")
def logout(request: Request):
    logout_session(request)
    return redirect("/admin/login")


# --- Comptes (US-05 à US-07) -------------------------------------------------


@router.get("")
def members(request: Request, admin: User = Depends(current_admin), db: Session = Depends(get_db)):
    return render(
        request,
        "admin/members.html",
        {"members": users_service.all_members(db), "now": utcnow()},
        user=admin,
    )


@router.get("/membres/nouveau")
def new_member_form(request: Request, admin: User = Depends(current_admin)):
    return render(request, "admin/member_new.html", {"error": None, "name": ""}, user=admin)


@router.post("/membres")
def create_member(
    request: Request,
    name: str = Form(""),
    password: str = Form(""),
    confirmation: str = Form(""),
    photo: UploadFile | None = File(None),
    admin: User = Depends(current_admin),
    db: Session = Depends(get_db),
):
    photo_path = None
    try:
        users_service.clean_name(db, name)
        users_service.check_new_password(password, confirmation)
        if images.has_file(photo):
            photo_path = images.save_image(photo, "avatars", images.AVATAR_MAX_SIDE)
        member = users_service.create_user(db, name, password, confirmation)
    except Invalid as exc:
        images.delete_image(photo_path)
        return render(
            request,
            "admin/member_new.html",
            {"error": exc.message, "name": name},
            user=admin,
            status_code=422,
        )
    if photo_path:
        member.photo_path = photo_path
        db.commit()
    flash(request, f"Compte de {member.first_name} créé.")
    return redirect("/admin")


def _member_page(request, admin, member, error=None, status_code=200):
    return render(
        request,
        "admin/member_edit.html",
        {"member": member, "error": error, "locked": member.is_locked()},
        user=admin,
        status_code=status_code,
    )


@router.get("/membres/{member_id}")
def member_form(
    request: Request,
    member_id: int,
    admin: User = Depends(current_admin),
    db: Session = Depends(get_db),
):
    return _member_page(request, admin, _get_member(db, member_id))


@router.post("/membres/{member_id}")
def update_member(
    request: Request,
    member_id: int,
    name: str = Form(""),
    is_active: str = Form(""),
    remove_photo: str = Form(""),
    photo: UploadFile | None = File(None),
    admin: User = Depends(current_admin),
    db: Session = Depends(get_db),
):
    member = _get_member(db, member_id)
    try:
        clean = users_service.clean_name(db, name, exclude_id=member.id)
        new_photo = None
        if images.has_file(photo):
            new_photo = images.save_image(photo, "avatars", images.AVATAR_MAX_SIDE)
    except Invalid as exc:
        return _member_page(request, admin, member, exc.message, 422)

    member.first_name = clean
    member.is_active = bool(is_active)
    old_photo = None
    if new_photo:
        old_photo, member.photo_path = member.photo_path, new_photo
    elif remove_photo:
        old_photo, member.photo_path = member.photo_path, None
    db.commit()
    images.delete_image(old_photo)
    flash(request, "Compte mis à jour.")
    return redirect(f"/admin/membres/{member.id}")


@router.post("/membres/{member_id}/mot-de-passe")
def reset_password(
    request: Request,
    member_id: int,
    password: str = Form(""),
    confirmation: str = Form(""),
    admin: User = Depends(current_admin),
    db: Session = Depends(get_db),
):
    member = _get_member(db, member_id)
    try:
        users_service.set_password(db, member, password, confirmation)
    except Invalid as exc:
        return _member_page(request, admin, member, exc.message, 422)
    flash(request, "Mot de passe réinitialisé.")
    return redirect(f"/admin/membres/{member.id}")


@router.post("/membres/{member_id}/debloquer")
def unlock_member(
    request: Request,
    member_id: int,
    admin: User = Depends(current_admin),
    db: Session = Depends(get_db),
):
    member = _get_member(db, member_id)
    users_service.unlock(db, member)
    flash(request, "Compte débloqué.")
    return redirect(f"/admin/membres/{member.id}")


# --- Cadeaux (US-08) ---------------------------------------------------------


@router.get("/cadeaux")
def gifts(
    request: Request,
    pour: str = "",
    admin: User = Depends(current_admin),
    db: Session = Depends(get_db),
):
    recipient_id = _to_int(pour)
    return render(
        request,
        "admin/gifts.html",
        {
            "gifts": admin_service.list_gifts(db, recipient_id),
            "members": users_service.all_members(db),
            "recipient_id": recipient_id,
        },
        user=admin,
    )


@router.post("/cadeaux/{gift_id}/supprimer")
def delete_gift(
    request: Request,
    gift_id: int,
    confirm: str = Form(""),
    admin: User = Depends(current_admin),
    db: Session = Depends(get_db),
):
    gift = db.get(Gift, gift_id)
    if gift is None:
        raise NotFound()
    if not confirm:
        flash(request, "Suppression non confirmée : rien n'a été supprimé.", "error")
        return redirect("/admin/cadeaux")
    gifts_service.hard_delete(db, gift)
    flash(request, "Cadeau supprimé définitivement.")
    return redirect("/admin/cadeaux")


# --- Clôture de l'année (US-09) ----------------------------------------------


@router.get("/cloture")
def close_year_form(
    request: Request, admin: User = Depends(current_admin), db: Session = Depends(get_db)
):
    return render(
        request,
        "admin/close_year.html",
        {"count": admin_service.count_to_archive(db), "year": utcnow().year, "error": None},
        user=admin,
    )


@router.post("/cloture")
def close_year(
    request: Request,
    year: str = Form(""),
    confirm: str = Form(""),
    admin: User = Depends(current_admin),
    db: Session = Depends(get_db),
):
    value = _to_int(year)
    error = None
    if value is None or not 2000 <= value <= 2100:
        error = "L'année n'est pas valide."
    elif not confirm:
        error = "Coche la case de confirmation pour clôturer l'année."
    if error:
        return render(
            request,
            "admin/close_year.html",
            {"count": admin_service.count_to_archive(db), "year": year, "error": error},
            user=admin,
            status_code=422,
        )
    count = admin_service.close_year(db, value)
    flash(request, f"Année {value} clôturée : {count} cadeau(x) archivé(s).")
    return redirect("/admin/cloture")
