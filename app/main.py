from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse

from app.config import settings
from app.routers.admin import router as admin_router
from app.security import RedirectToLogin, current_member, get_csrf_token
from app.templating import templates

app = FastAPI(title="Liste de Noël")

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    max_age=settings.session_max_age_seconds,
    same_site="lax",
    https_only=settings.session_https_only,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(admin_router)


@app.exception_handler(RedirectToLogin)
async def _handle_redirect_to_login(request: Request, exc: RedirectToLogin) -> RedirectResponse:
    return RedirectResponse(url=exc.location, status_code=303)


@app.get("/", dependencies=[Depends(current_member)])
def index(request: Request):
    return templates.TemplateResponse(
        request, "index.html", {"csrf_token": get_csrf_token(request)}
    )


@app.get("/media/{filename}")
def media_file(filename: str):
    """Sert les photos de profil (RG-17). Route dédiée (et non un montage statique figé au
    démarrage) pour que `media_dir` reste reconfigurable, notamment par les tests.
    """
    media_root = settings.media_dir.resolve()
    chemin = (media_root / filename).resolve()
    if not chemin.is_relative_to(media_root) or not chemin.is_file():
        raise HTTPException(status_code=404)
    return FileResponse(chemin)
