import argparse
import sys
from getpass import getpass

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import User
from app.security import hash_password

MIN_PASSWORD_LENGTH = 8


def _first_name_deja_pris(session: Session, first_name: str) -> bool:
    return (
        session.query(User).filter(func.lower(User.first_name) == first_name.lower()).first()
        is not None
    )


def create_admin(first_name: str, password: str, session: Session | None = None) -> User:
    """Crée le compte admin. Lève `ValueError` si le prénom ou le mot de passe sont invalides."""
    first_name = first_name.strip()
    if not first_name:
        raise ValueError("Le prénom est obligatoire.")
    if len(password) < MIN_PASSWORD_LENGTH:
        msg = f"Le mot de passe doit contenir au moins {MIN_PASSWORD_LENGTH} caractères."
        raise ValueError(msg)

    own_session = session is None
    session = session or SessionLocal()
    try:
        if _first_name_deja_pris(session, first_name):
            raise ValueError(f"Le prénom « {first_name} » est déjà utilisé.")

        admin = User(first_name=first_name, password_hash=hash_password(password), role="admin")
        session.add(admin)
        session.commit()
        session.refresh(admin)
        if own_session:
            session.expunge(admin)
        return admin
    finally:
        if own_session:
            session.close()


def _prompt_create_admin() -> None:
    first_name = input("Prénom de l'admin : ").strip()
    password = getpass("Mot de passe : ")
    confirmation = getpass("Confirmation : ")

    if password != confirmation:
        print("Les mots de passe ne correspondent pas.", file=sys.stderr)
        raise SystemExit(1)

    try:
        admin = create_admin(first_name, password)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    print(f"Compte admin « {admin.first_name} » créé.")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("create-admin", help="Créer le compte admin")

    args = parser.parse_args(argv)

    if args.command == "create-admin":
        _prompt_create_admin()


if __name__ == "__main__":
    main()
