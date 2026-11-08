from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse

from app.db import get_db
from app.security import RedirectToLogin, current_admin, current_member


def _make_test_app(db_session):
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test-secret")

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    @app.exception_handler(RedirectToLogin)
    async def _redirect(_request: Request, exc: RedirectToLogin) -> RedirectResponse:
        return RedirectResponse(url=exc.location, status_code=303)

    @app.post("/connexion-test/{user_id}")
    def connexion_test(user_id: int, request: Request):
        request.session["user_id"] = user_id
        return {"ok": True}

    @app.get("/zone-membre")
    def zone_membre(user=Depends(current_member)):
        return {"first_name": user.first_name}

    @app.get("/zone-admin")
    def zone_admin(user=Depends(current_admin)):
        return {"first_name": user.first_name}

    return app


def test_current_member_redirige_vers_login_si_anonyme(db_session):
    client = TestClient(_make_test_app(db_session), follow_redirects=False)

    response = client.get("/zone-membre")

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_current_member_refuse_un_admin(db_session, admin):
    client = TestClient(_make_test_app(db_session))
    client.post(f"/connexion-test/{admin.id}")

    response = client.get("/zone-membre")

    assert response.status_code == 403


def test_current_member_accepte_un_membre(db_session, alice):
    client = TestClient(_make_test_app(db_session))
    client.post(f"/connexion-test/{alice.id}")

    response = client.get("/zone-membre")

    assert response.status_code == 200
    assert response.json()["first_name"] == "Alice"


def test_current_admin_redirige_vers_admin_login_si_anonyme(db_session):
    client = TestClient(_make_test_app(db_session), follow_redirects=False)

    response = client.get("/zone-admin")

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/login"


def test_current_admin_refuse_un_membre(db_session, alice):
    client = TestClient(_make_test_app(db_session))
    client.post(f"/connexion-test/{alice.id}")

    response = client.get("/zone-admin")

    assert response.status_code == 403


def test_current_admin_accepte_un_admin(db_session, admin):
    client = TestClient(_make_test_app(db_session))
    client.post(f"/connexion-test/{admin.id}")

    response = client.get("/zone-admin")

    assert response.status_code == 200


def test_session_avec_utilisateur_inexistant_redirige_vers_login(db_session):
    client = TestClient(_make_test_app(db_session), follow_redirects=False)
    client.post("/connexion-test/9999")

    response = client.get("/zone-membre")

    assert response.status_code == 303
    assert response.headers["location"] == "/login"
