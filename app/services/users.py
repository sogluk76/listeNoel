"""Comptes : création, validation, authentification (RG-01 à RG-11)."""

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.errors import Invalid
from app.models import ROLE_ADMIN, ROLE_MEMBER, User, utcnow
from app.security import hash_password, verify_password
from app.services.text import fold

AUTH_OK = "ok"
AUTH_BAD = "bad"
AUTH_LOCKED = "locked"

MSG_BAD_PASSWORD = "Mot de passe incorrect"
MSG_LOCKED = "Compte temporairement bloqué, réessaie plus tard"


def active_members(db: Session) -> list[User]:
    """Membres actifs par ordre alphabétique, sans l'admin (RG-03, RG-12)."""
    users = db.scalars(select(User).where(User.role == ROLE_MEMBER, User.is_active.is_(True))).all()
    return sorted(users, key=lambda u: fold(u.first_name))


def all_members(db: Session) -> list[User]:
    users = db.scalars(select(User).where(User.role == ROLE_MEMBER)).all()
    return sorted(users, key=lambda u: fold(u.first_name))


def get_active_member(db: Session, user_id: int | None) -> User | None:
    if user_id is None:
        return None
    user = db.get(User, user_id)
    if user is None or not user.is_member or not user.is_active:
        return None
    return user


def find_by_name(db: Session, name: str) -> User | None:
    wanted = fold(name)
    for user in db.scalars(select(User)).all():
        if fold(user.first_name) == wanted:
            return user
    return None


def clean_name(db: Session, name: str, exclude_id: int | None = None) -> str:
    """Valide un prénom : 1 à 50 caractères, unique sans tenir compte de la casse (RG-02)."""
    name = " ".join((name or "").split())
    if not name:
        raise Invalid("Le prénom est obligatoire.")
    if len(name) > 50:
        raise Invalid("Le prénom ne doit pas dépasser 50 caractères.")
    existing = find_by_name(db, name)
    if existing is not None and existing.id != exclude_id:
        raise Invalid("Ce prénom est déjà utilisé.")
    return name


def check_new_password(password: str, confirmation: str) -> None:
    if len(password or "") < settings.password_min_length:
        raise Invalid(
            f"Le mot de passe doit contenir au moins {settings.password_min_length} caractères."
        )
    if password != confirmation:
        raise Invalid("La confirmation ne correspond pas au mot de passe.")


def create_user(
    db: Session, name: str, password: str, confirmation: str, role: str = ROLE_MEMBER
) -> User:
    name = clean_name(db, name)
    check_new_password(password, confirmation)
    user = User(first_name=name, password_hash=hash_password(password), role=role)
    db.add(user)
    db.commit()
    return user


def has_admin(db: Session) -> bool:
    return db.scalar(select(User.id).where(User.role == ROLE_ADMIN).limit(1)) is not None


def set_password(db: Session, user: User, password: str, confirmation: str) -> None:
    """Change le mot de passe et lève un éventuel blocage (US-07)."""
    check_new_password(password, confirmation)
    user.password_hash = hash_password(password)
    unlock(db, user, commit=False)
    db.commit()


def unlock(db: Session, user: User, commit: bool = True) -> None:
    user.failed_login_count = 0
    user.locked_until = None
    if commit:
        db.commit()


def authenticate(db: Session, user: User, password: str, now: datetime | None = None) -> str:
    """Vérifie un mot de passe en appliquant le blocage après 5 échecs (RG-05)."""
    now = now or utcnow()
    if user.locked_until is not None:
        if user.locked_until > now:
            return AUTH_LOCKED
        user.locked_until = None
        user.failed_login_count = 0

    if verify_password(user.password_hash, password or ""):
        user.failed_login_count = 0
        db.commit()
        return AUTH_OK

    user.failed_login_count += 1
    result = AUTH_BAD
    if user.failed_login_count >= settings.max_login_failures:
        user.locked_until = now + timedelta(minutes=settings.lock_minutes)
        result = AUTH_LOCKED
    db.commit()
    return result
