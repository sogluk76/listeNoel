from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import User
from app.security import hash_password, verify_password
from app.services.images import InvalidImageError, delete_profile_photo, save_profile_photo

GENERIC_AUTH_ERROR_MESSAGE = "Mot de passe incorrect"  # RG-06 : jamais plus précis
MIN_PASSWORD_LENGTH = 8  # RG-10 / PO-09


class AuthenticationError(Exception):
    pass


class MemberNotFoundError(Exception):
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


def _first_name_deja_pris(db: Session, first_name: str, exclude_id: int | None = None) -> bool:
    query = db.query(User).filter(func.lower(User.first_name) == first_name.lower())
    if exclude_id is not None:
        query = query.filter(User.id != exclude_id)
    return query.first() is not None


def _create_user(
    db: Session, first_name: str, password: str, role: str, photo: bytes | None = None
) -> User:
    first_name = first_name.strip()
    if not first_name:
        raise ValueError("Le prénom est obligatoire.")
    if len(password) < MIN_PASSWORD_LENGTH:
        msg = f"Le mot de passe doit contenir au moins {MIN_PASSWORD_LENGTH} caractères."
        raise ValueError(msg)
    if _first_name_deja_pris(db, first_name):
        raise ValueError(f"Le prénom « {first_name} » est déjà utilisé.")

    photo_path = None
    if photo is not None:
        try:
            photo_path = save_profile_photo(photo)
        except InvalidImageError as exc:
            raise ValueError(str(exc)) from exc

    user = User(
        first_name=first_name,
        password_hash=hash_password(password),
        role=role,
        photo_path=photo_path,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_admin(db: Session, first_name: str, password: str) -> User:
    """Crée le compte admin (US-04). Lève `ValueError` si une donnée est invalide."""
    return _create_user(db, first_name, password, role="admin")


def create_member(
    db: Session,
    first_name: str,
    password: str,
    password_confirmation: str,
    photo: bytes | None = None,
) -> User:
    """Crée un compte membre actif (US-05). Lève `ValueError` sinon (RG-02, RG-10, RG-17)."""
    if password != password_confirmation:
        raise ValueError("Les mots de passe ne correspondent pas.")
    return _create_user(db, first_name, password, role="member", photo=photo)


def list_members(db: Session) -> list[User]:
    """Tous les comptes membres, actifs ou non (US-06). L'admin n'y figure jamais."""
    return db.query(User).filter(User.role == "member").order_by(func.lower(User.first_name)).all()


def get_member(db: Session, member_id: int) -> User:
    """Un compte membre par id. Lève `MemberNotFoundError` sinon (jamais l'admin)."""
    user = db.query(User).filter(User.id == member_id, User.role == "member").first()
    if user is None:
        raise MemberNotFoundError
    return user


def update_member(
    db: Session,
    member_id: int,
    first_name: str,
    is_active: bool,
    photo: bytes | None = None,
    remove_photo: bool = False,
) -> User:
    """Modifie le prénom, la photo et le statut actif d'un membre (US-06, RG-02, RG-11, RG-17).

    Lève `MemberNotFoundError` si `member_id` ne désigne pas un compte membre : cette fonction
    ne doit jamais pouvoir modifier ou désactiver le compte admin, même via un id forgé.
    """
    member = get_member(db, member_id)

    first_name = first_name.strip()
    if not first_name:
        raise ValueError("Le prénom est obligatoire.")
    if _first_name_deja_pris(db, first_name, exclude_id=member.id):
        raise ValueError(f"Le prénom « {first_name} » est déjà utilisé.")

    nouveau_photo_path = member.photo_path
    if photo is not None:
        try:
            nouveau_photo_path = save_profile_photo(photo)
        except InvalidImageError as exc:
            raise ValueError(str(exc)) from exc
    elif remove_photo:
        nouveau_photo_path = None

    if nouveau_photo_path != member.photo_path and member.photo_path is not None:
        delete_profile_photo(member.photo_path)

    member.first_name = first_name
    member.is_active = is_active
    member.photo_path = nouveau_photo_path
    db.commit()
    db.refresh(member)
    return member
