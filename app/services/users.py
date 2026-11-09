from datetime import UTC, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import User
from app.security import hash_password, verify_password
from app.services.images import InvalidImageError, delete_profile_photo, save_profile_photo

GENERIC_AUTH_ERROR_MESSAGE = "Mot de passe incorrect"  # RG-06 : jamais plus précis
LOCKED_AUTH_ERROR_MESSAGE = "Compte temporairement bloqué, réessaie plus tard"  # RG-06
MIN_PASSWORD_LENGTH = 8  # RG-10 / PO-09
MAX_FAILED_ATTEMPTS = 5  # RG-05
LOCKOUT_DURATION = timedelta(minutes=15)  # RG-05 / PO-01


class AuthenticationError(Exception):
    pass


class MemberNotFoundError(Exception):
    pass


def _now() -> datetime:
    """Naïf, UTC : même convention que `created_at`/`updated_at` (horodatage SQLite)."""
    return datetime.now(UTC).replace(tzinfo=None)


def authenticate(db: Session, first_name: str, password: str, role: str) -> User:
    """Authentifie un utilisateur d'un rôle donné (RG-05, RG-06).

    Lève `AuthenticationError` avec le message générique si le prénom, le rôle ou le mot de
    passe est incorrect ou le compte désactivé, ou avec le message de blocage si le compte est
    bloqué (RG-05) — même avec le bon mot de passe.
    """
    user = (
        db.query(User)
        .filter(func.lower(User.first_name) == first_name.strip().lower(), User.role == role)
        .first()
    )
    if user is None or not user.is_active:
        raise AuthenticationError(GENERIC_AUTH_ERROR_MESSAGE)

    now = _now()
    if user.locked_until is not None:
        if user.locked_until > now:
            raise AuthenticationError(LOCKED_AUTH_ERROR_MESSAGE)
        user.failed_login_count = 0
        user.locked_until = None

    if not verify_password(password, user.password_hash):
        user.failed_login_count += 1
        if user.failed_login_count >= MAX_FAILED_ATTEMPTS:
            user.locked_until = now + LOCKOUT_DURATION
        db.commit()
        raise AuthenticationError(GENERIC_AUTH_ERROR_MESSAGE)

    user.failed_login_count = 0
    user.locked_until = None
    db.commit()
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


def list_active_members(db: Session) -> list[User]:
    """Membres actifs, triés alphabétiquement (RG-03, US-01). L'admin n'y figure jamais."""
    return (
        db.query(User)
        .filter(User.role == "member", User.is_active.is_(True))
        .order_by(func.lower(User.first_name))
        .all()
    )


def list_other_active_members(db: Session, viewer: User) -> list[User]:
    """RG-19 : membres actifs disponibles comme destinataire d'une suggestion (pas moi)."""
    return [member for member in list_active_members(db) if member.id != viewer.id]


def get_member(db: Session, member_id: int) -> User:
    """Un compte membre par id. Lève `MemberNotFoundError` sinon (jamais l'admin)."""
    user = db.query(User).filter(User.id == member_id, User.role == "member").first()
    if user is None:
        raise MemberNotFoundError
    return user


def get_active_member(db: Session, member_id: int) -> User:
    """Un compte membre **actif** par id (RG-11/RG-12) : un compte désactivé ou l'admin
    lèvent `MemberNotFoundError`, pour que l'appelant renvoie un 404 identique aux deux cas."""
    user = (
        db.query(User)
        .filter(User.id == member_id, User.role == "member", User.is_active.is_(True))
        .first()
    )
    if user is None:
        raise MemberNotFoundError
    return user


def _clear_lockout(member: User) -> None:
    member.failed_login_count = 0
    member.locked_until = None


def reset_password(db: Session, member_id: int, password: str, password_confirmation: str) -> User:
    """Définit un nouveau mot de passe pour un membre et lève son blocage (US-07, RG-05, RG-10).

    Lève `MemberNotFoundError` si `member_id` ne désigne pas un compte membre, `ValueError`
    si la confirmation ne correspond pas ou si le mot de passe est trop court.
    """
    member = get_member(db, member_id)
    if password != password_confirmation:
        raise ValueError("Les mots de passe ne correspondent pas.")
    if len(password) < MIN_PASSWORD_LENGTH:
        msg = f"Le mot de passe doit contenir au moins {MIN_PASSWORD_LENGTH} caractères."
        raise ValueError(msg)

    member.password_hash = hash_password(password)
    _clear_lockout(member)
    db.commit()
    return member


def unlock_member(db: Session, member_id: int) -> User:
    """Lève le blocage RG-05 d'un membre, sans effet s'il n'était pas bloqué (US-07).

    Lève `MemberNotFoundError` si `member_id` ne désigne pas un compte membre.
    """
    member = get_member(db, member_id)
    _clear_lockout(member)
    db.commit()
    return member


def _swap_photo(member: User, photo: bytes | None, remove_photo: bool) -> None:
    """RG-17 : remplace ou supprime la photo d'un membre, en nettoyant l'ancien fichier
    du disque. Ne commite pas : à l'appelant de le faire avec le reste de ses changements.
    """
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

    member.photo_path = nouveau_photo_path


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

    _swap_photo(member, photo, remove_photo)

    member.first_name = first_name
    member.is_active = is_active
    db.commit()
    db.refresh(member)
    return member


def update_own_photo(
    db: Session, member: User, photo: bytes | None = None, remove_photo: bool = False
) -> User:
    """RG-36 (US-23) : un membre change ou supprime sa propre photo de profil."""
    _swap_photo(member, photo, remove_photo)
    db.commit()
    db.refresh(member)
    return member
