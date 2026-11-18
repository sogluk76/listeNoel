"""Création de l'application FastAPI."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.db import run_migrations
from app.errors import Forbidden, NotAuthenticated, NotFound
from app.routers import (
    admin,
    auth,
    comments,
    gifts,
    messages,
    notifications,
    people,
    profile,
    shopping,
)
from app.security import csrf_protect
from app.web import htmx_redirect, redirect, render

STATIC_DIR = Path(__file__).parent / "static"

ERRORS = {
    403: ("Accès refusé", "Tu n'as pas accès à cette page."),
    404: ("Page introuvable", "Cette page n'existe pas ou n'est plus disponible."),
}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if not settings.testing:
        run_migrations()
    yield


def _error_page(request: Request, status_code: int):
    title, message = ERRORS.get(status_code, ("Erreur", "Une erreur est survenue."))
    is_admin_area = request.url.path.startswith("/admin")
    return render(
        request,
        "error.html",
        {"title": title, "message": message, "code": status_code, "is_admin_area": is_admin_area},
        status_code=status_code,
    )


def create_app() -> FastAPI:
    app = FastAPI(
        title="La Famille",
        lifespan=lifespan,
        dependencies=[Depends(csrf_protect)],
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.resolved_secret_key(),
        session_cookie="noel_session",
        max_age=settings.session_days * 24 * 3600,
        same_site="lax",
        https_only=settings.secure_cookies,
    )

    settings.media_dir.mkdir(parents=True, exist_ok=True)
    settings.private_media_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.mount("/media", StaticFiles(directory=settings.media_dir), name="media")

    for module in (
        auth,
        people,
        gifts,
        comments,
        notifications,
        messages,
        shopping,
        profile,
        admin,
    ):
        app.include_router(module.router)

    @app.exception_handler(NotAuthenticated)
    async def _not_authenticated(request: Request, exc: NotAuthenticated):
        target = "/admin/login" if exc.admin else "/login"
        if request.headers.get("HX-Request") == "true":
            return htmx_redirect(target)
        return redirect(target)

    @app.exception_handler(Forbidden)
    async def _forbidden(request: Request, _exc: Forbidden):
        return _error_page(request, 403)

    @app.exception_handler(NotFound)
    async def _not_found(request: Request, _exc: NotFound):
        return _error_page(request, 404)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(request: Request, exc: StarletteHTTPException):
        return _error_page(request, exc.status_code)

    return app


app = create_app()
