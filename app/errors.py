"""Exceptions métier, traduites en réponses HTTP dans app/main.py."""


class NotAuthenticated(Exception):
    """Aucune session valide : redirection vers la page de connexion."""

    def __init__(self, admin: bool = False) -> None:
        self.admin = admin


class Forbidden(Exception):
    """Action interdite pour cet utilisateur (HTTP 403)."""


class NotFound(Exception):
    """Ressource inexistante ou invisible pour cet utilisateur (HTTP 404)."""


class Invalid(Exception):
    """Donnée ou action refusée par une règle métier."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
