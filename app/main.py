from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse

from app.config import settings
from app.routers.admin import router as admin_router
from app.routers.auth import router as auth_router
from app.routers.gifts import router as gifts_router
from app.routers.people import router as people_router
from app.security import RedirectToLogin

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
app.include_router(auth_router)
app.include_router(gifts_router)
app.include_router(people_router)


@app.exception_handler(RedirectToLogin)
async def _handle_redirect_to_login(request: Request, exc: RedirectToLogin) -> RedirectResponse:
    return RedirectResponse(url=exc.location, status_code=303)


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
