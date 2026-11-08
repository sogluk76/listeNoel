from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import User
from app.security import hash_password, verify_password

GENERIC_AUTH_ERROR_MESSAGE = "Mot de passe incorrect"  # RG-06 : jamais plus précis
MIN_PASSWORD_LENGTH = 8  # RG-10 / PO-09


class AuthenticationError(Exception):
    pass


def authenticate(db: Session, first_name: str, password: str, role: str) -> User:
    """Authentifie un utilisateur d'un rôle donné. Lève `AuthenticationError` sinon (RG-06)."""
    user = (
        db.query(User)
        .filter(func.lower(User.first_name) == first_name.strip().lower(), User.role == role)
        .first()
    )
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        raise AuthenticationError(GENERIC_AUTH_ERROR_MESSAGE)
    return user


def _first_name_deja_pris(db: Session, first_name: str) -> bool:
    return (
        db.query(User).filter(func.lower(User.first_name) == first_name.lower()).first() is not None
    )


def _create_user(db: Session, first_name: str, password: str, role: str) -> User:
    first_name = first_name.strip()
    if not first_name:
        raise ValueError("Le prénom est obligatoire.")
    if len(password) < MIN_PASSWORD_LENGTH:
        msg = f"Le mot de passe doit contenir au moins {MIN_PASSWORD_LENGTH} caractères."
        raise ValueError(msg)
    if _first_name_deja_pris(db, first_name):
        raise ValueError(f"Le prénom « {first_name} » est déjà utilisé.")

    user = User(first_name=first_name, password_hash=hash_password(password), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_admin(db: Session, first_name: str, password: str) -> User:
    """Crée le compte admin (US-04). Lève `ValueError` si une donnée est invalide."""
    return _create_user(db, first_name, password, role="admin")


def create_member(db: Session, first_name: str, password: str, password_confirmation: str) -> User:
    """Crée un compte membre actif (US-05). Lève `ValueError` sinon (RG-02, RG-10)."""
    if password != password_confirmation:
        raise ValueError("Les mots de passe ne correspondent pas.")
    return _create_user(db, first_name, password, role="member")
