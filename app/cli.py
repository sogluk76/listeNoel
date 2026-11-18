"""Commandes d'administration.

uv run python -m app.cli create-admin
uv run python -m app.cli create-admin --name admin --password "motdepasse"
"""

import argparse
import getpass
import sys

from app.db import SessionLocal, run_migrations
from app.errors import Invalid
from app.models import ROLE_ADMIN
from app.services import users as users_service


def create_admin(name: str | None, password: str | None) -> int:
    run_migrations()
    name = name or input("Identifiant de l'admin : ").strip()
    if password is None:
        password = getpass.getpass("Mot de passe (8 caractères minimum) : ")
        confirmation = getpass.getpass("Confirmation : ")
    else:
        confirmation = password
    with SessionLocal() as db:
        try:
            admin = users_service.create_user(db, name, password, confirmation, role=ROLE_ADMIN)
        except Invalid as exc:
            print(f"Erreur : {exc.message}", file=sys.stderr)
            return 1
    print(f"Compte admin « {admin.first_name} » créé. Connexion sur /admin/login")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="app.cli", description="La Famille")
    commands = parser.add_subparsers(dest="command", required=True)
    admin = commands.add_parser("create-admin", help="Crée le compte admin")
    admin.add_argument("--name")
    admin.add_argument("--password")
    args = parser.parse_args()
    if args.command == "create-admin":
        return create_admin(args.name, args.password)
    return 1


if __name__ == "__main__":
    sys.exit(main())
