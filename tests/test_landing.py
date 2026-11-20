"""첫 화면 — 토큰 없이 열리고, 판 이름이 보이며, 비밀값이 없다."""
from fastapi.testclient import TestClient

from api.app import APP_VERSION, app


def test_landing_page_opens_without_token():
    r = TestClient(app).get("/")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    body = r.text
    assert "paperclf API" in body and "/predict" in body and "/health" in body
    assert APP_VERSION in body


def test_landing_page_has_no_token_value(monkeypatch):
    monkeypatch.setenv("API_TOKEN", "secret-token-should-not-appear")
    r = TestClient(app).get("/")
    assert "secret-token-should-not-appear" not in r.text
