"""Mots de passe, session, contrôle d'accès et protection CSRF."""

import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import Forbidden, NotAuthenticated
from app.models import User, utcnow

_hasher = PasswordHasher()

SESSION_USER_KEY = "uid"
SESSION_CSRF_KEY = "csrf"
SESSION_FLASH_KEY = "flash"
PRESENCE_EVERY_SECONDS = 60


# --- Mots de passe (RG-10) -------------------------------------------------


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


# --- Session ---------------------------------------------------------------


def login_session(request: Request, user: User) -> None:
    request.session.clear()
    request.session[SESSION_USER_KEY] = user.id


def logout_session(request: Request) -> None:
    request.session.clear()


def session_user(request: Request, db: Session) -> User | None:
    """Utilisateur de la session, ou None. Un compte désactivé perd sa session (RG-11)."""
    uid = request.session.get(SESSION_USER_KEY)
    if uid is None:
        return None
    user = db.get(User, uid)
    if user is None or not user.is_active:
        request.session.clear()
        return None
    return user


def current_member(request: Request, db: Session = Depends(get_db)) -> User:
    """Dépendance des écrans membres : refuse l'admin (RG-09)."""
    user = session_user(request, db)
    if user is None:
        raise NotAuthenticated(admin=False)
    if not user.is_member:
        raise Forbidden()
    touch_presence(db, user)
    return user


def touch_presence(db: Session, user: User) -> None:
    """Note l'activité du membre, au plus une fois par minute (« En ligne », RG-52)."""
    now = utcnow()
    last = user.last_seen_at
    if last is None or (now - last).total_seconds() >= PRESENCE_EVERY_SECONDS:
        user.last_seen_at = now
        db.commit()


def current_admin(request: Request, db: Session = Depends(get_db)) -> User:
    """Dépendance du panel admin : refuse les membres (RG-09)."""
    user = session_user(request, db)
    if user is None:
        raise NotAuthenticated(admin=True)
    if not user.is_admin:
        raise Forbidden()
    return user


# --- CSRF ------------------------------------------------------------------


def csrf_token(request: Request) -> str:
    token = request.session.get(SESSION_CSRF_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        request.session[SESSION_CSRF_KEY] = token
    return token


async def csrf_protect(request: Request) -> None:
    """Vérifie le jeton CSRF (en-tête HTMX ou champ caché) sur toute requête d'écriture."""
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    expected = request.session.get(SESSION_CSRF_KEY)
    sent = request.headers.get("X-CSRF-Token")
    if sent is None:
        form = await request.form()
        sent = form.get("csrf_token")
    if not expected or not isinstance(sent, str) or not secrets.compare_digest(sent, expected):
        raise Forbidden()


# --- Messages flash --------------------------------------------------------


def flash(request: Request, message: str, kind: str = "success") -> None:
    messages = request.session.get(SESSION_FLASH_KEY, [])
    messages.append({"message": message, "kind": kind})
    request.session[SESSION_FLASH_KEY] = messages


def pop_flashes(request: Request) -> list[dict]:
    return request.session.pop(SESSION_FLASH_KEY, [])
