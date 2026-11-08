import hmac
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User

CSRF_SESSION_KEY = "csrf_token"
CSRF_FORM_FIELD = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"

_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Vérifie un mot de passe. Ne journalise jamais ni le mot de passe ni le hash."""
    try:
        return _password_hasher.verify(password_hash, password)
    except Argon2Error:
        return False


def get_csrf_token(request: Request) -> str:
    """Jeton CSRF stable pour la session en cours, créé au premier appel."""
    token = request.session.get(CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        request.session[CSRF_SESSION_KEY] = token
    return token


async def verify_csrf(request: Request) -> None:
    """Dépendance à poser sur chaque route POST : en-tête HTMX ou champ caché du formulaire."""
    session_token = request.session.get(CSRF_SESSION_KEY)
    submitted_token = request.headers.get(CSRF_HEADER_NAME)
    if submitted_token is None:
        form = await request.form()
        submitted_token = form.get(CSRF_FORM_FIELD)

    jeton_valide = (
        session_token is not None
        and submitted_token is not None
        and hmac.compare_digest(session_token, submitted_token)
    )
    if not jeton_valide:
        raise HTTPException(status_code=403, detail="Jeton CSRF invalide")


class RedirectToLogin(Exception):
    """Levée par `current_member`/`current_admin` quand il n'y a aucune session valide."""

    def __init__(self, location: str):
        self.location = location


def _user_from_session(request: Request, db: Session) -> User | None:
    user_id = request.session.get("user_id")
    if user_id is None:
        return None
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        return None
    return user


def current_member(request: Request, db: Session = Depends(get_db)) -> User:
    """403 si connecté avec le mauvais rôle (RG-09), redirection vers /login sinon."""
    user = _user_from_session(request, db)
    if user is None:
        raise RedirectToLogin("/login")
    if user.role != "member":
        raise HTTPException(status_code=403)
    return user


def current_admin(request: Request, db: Session = Depends(get_db)) -> User:
    """403 si connecté avec le mauvais rôle (RG-09), redirection vers /admin/login sinon."""
    user = _user_from_session(request, db)
    if user is None:
        raise RedirectToLogin("/admin/login")
    if user.role != "admin":
        raise HTTPException(status_code=403)
    return user
