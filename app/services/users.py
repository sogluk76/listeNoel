from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import User
from app.security import verify_password

GENERIC_AUTH_ERROR_MESSAGE = "Mot de passe incorrect"  # RG-06 : jamais plus précis


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
