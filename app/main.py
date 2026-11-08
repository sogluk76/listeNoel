from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse

from app.config import settings
from app.security import RedirectToLogin, current_member, get_csrf_token

app = FastAPI(title="Liste de Noël")

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    max_age=settings.session_max_age_seconds,
    same_site="lax",
    https_only=settings.session_https_only,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")


@app.exception_handler(RedirectToLogin)
async def _handle_redirect_to_login(request: Request, exc: RedirectToLogin) -> RedirectResponse:
    return RedirectResponse(url=exc.location, status_code=303)


@app.get("/", dependencies=[Depends(current_member)])
def index(request: Request):
    return templates.TemplateResponse(
        request, "index.html", {"csrf_token": get_csrf_token(request)}
    )
