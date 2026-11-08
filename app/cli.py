import argparse
import sys
from getpass import getpass

from app.db import SessionLocal
from app.services.users import create_admin


def _prompt_create_admin() -> None:
    first_name = input("Prénom de l'admin : ").strip()
    password = getpass("Mot de passe : ")
    confirmation = getpass("Confirmation : ")

    if password != confirmation:
        print("Les mots de passe ne correspondent pas.", file=sys.stderr)
        raise SystemExit(1)

    session = SessionLocal()
    try:
        admin = create_admin(session, first_name, password)
        admin_first_name = admin.first_name
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    finally:
        session.close()

    print(f"Compte admin « {admin_first_name} » créé.")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("create-admin", help="Créer le compte admin")

    args = parser.parse_args(argv)

    if args.command == "create-admin":
        _prompt_create_admin()


if __name__ == "__main__":
    main()
