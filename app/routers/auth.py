"""Connexion et déconnexion des membres (US-01 à US-03)."""

from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.security import login_session, logout_session, session_user
from app.services import users as users_service
from app.web import fragment, redirect, render

router = APIRouter()


def _to_int(value: str | None) -> int | None:
    try:
        return int(value) if value not in (None, "") else None
    except ValueError:
        return None


def _login_page(request: Request, db: Session, selected_id=None, error=None, status_code=200):
    members = users_service.active_members(db)
    selected = users_service.get_active_member(db, selected_id)
    if selected is None and members:
        selected = members[0]
    return render(
        request,
        "login.html",
        {"members": members, "selected": selected, "error": error},
        status_code=status_code,
    )


@router.get("/login")
def login_form(request: Request, db: Session = Depends(get_db)):
    user = session_user(request, db)
    if user is not None:
        return redirect("/admin" if user.is_admin else "/")
    return _login_page(request, db)


@router.get("/login/avatar")
def login_avatar(request: Request, user_id: str = "", db: Session = Depends(get_db)):
    """Fragment HTMX : photo ou placeholder du prénom choisi (RG-04)."""
    selected = users_service.get_active_member(db, _to_int(user_id))
    return fragment(request, "_login_avatar.html", {"selected": selected})


@router.post("/login")
def login(
    request: Request,
    user_id: str = Form(""),
    password: str = Form(""),
    db: Session = Depends(get_db),
):
    member = users_service.get_active_member(db, _to_int(user_id))
    if member is None:
        # Compte inexistant, désactivé ou admin : même message générique (RG-06).
        return _login_page(request, db, error=users_service.MSG_BAD_PASSWORD, status_code=401)
    result = users_service.authenticate(db, member, password)
    if result == users_service.AUTH_OK:
        login_session(request, member)
        return redirect("/")
    error = (
        users_service.MSG_LOCKED
        if result == users_service.AUTH_LOCKED
        else users_service.MSG_BAD_PASSWORD
    )
    return _login_page(request, db, selected_id=member.id, error=error, status_code=401)


@router.post("/logout")
def logout(request: Request):
    logout_session(request)
    return redirect("/login")
