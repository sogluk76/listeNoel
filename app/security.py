import hmac
import secrets

from fastapi import HTTPException, Request

CSRF_SESSION_KEY = "csrf_token"
CSRF_FORM_FIELD = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"


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
