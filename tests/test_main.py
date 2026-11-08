from fastapi.testclient import TestClient

from app.main import app


def test_page_accueil_repond_200():
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200


def test_page_accueil_charge_htmx():
    client = TestClient(app)
    response = client.get("/")

    assert "static/js/htmx.min.js" in response.text


def test_page_accueil_porte_le_jeton_csrf_en_en_tete_htmx():
    client = TestClient(app)
    response = client.get("/")

    assert "X-CSRF-Token" in response.text
