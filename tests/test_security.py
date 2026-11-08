from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from app.security import CSRF_HEADER_NAME, get_csrf_token, verify_csrf


def _make_test_app():
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test-secret")

    @app.get("/jeton")
    def jeton(request: Request):
        return {"csrf_token": get_csrf_token(request)}

    @app.post("/protege", dependencies=[Depends(verify_csrf)])
    def protege():
        return {"ok": True}

    return app


def test_le_jeton_reste_stable_sur_la_meme_session():
    client = TestClient(_make_test_app())

    premier = client.get("/jeton").json()["csrf_token"]
    second = client.get("/jeton").json()["csrf_token"]

    assert premier == second


def test_requete_sans_jeton_refusee():
    client = TestClient(_make_test_app())
    client.get("/jeton")

    response = client.post("/protege")

    assert response.status_code == 403


def test_requete_avec_en_tete_htmx_valide_acceptee():
    client = TestClient(_make_test_app())
    token = client.get("/jeton").json()["csrf_token"]

    response = client.post("/protege", headers={CSRF_HEADER_NAME: token})

    assert response.status_code == 200


def test_requete_avec_champ_formulaire_valide_acceptee():
    client = TestClient(_make_test_app())
    token = client.get("/jeton").json()["csrf_token"]

    response = client.post("/protege", data={"csrf_token": token})

    assert response.status_code == 200


def test_requete_avec_jeton_invalide_refusee():
    client = TestClient(_make_test_app())
    client.get("/jeton")

    response = client.post("/protege", headers={CSRF_HEADER_NAME: "mauvais-jeton"})

    assert response.status_code == 403
