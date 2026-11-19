"""공개 API 보호 — 토큰 인증과 사용량 제한."""
import importlib

from fastapi.testclient import TestClient

BODY = {"title": "Managerial coaching and employee engagement"}


def client(monkeypatch, token="", per_min="60"):
    monkeypatch.setenv("API_TOKEN", token)
    monkeypatch.setenv("RATE_LIMIT_PER_MIN", per_min)
    monkeypatch.setenv("MODEL_DIR", "/nonexistent")
    import api.app as app_module
    importlib.reload(app_module)
    return TestClient(app_module.app)


def test_no_token_configured_is_open(monkeypatch):
    c = client(monkeypatch)
    assert c.post("/predict", json=BODY).status_code == 503  # 모델 없음 — 인증은 통과
    assert c.get("/health").json()["guard"]["auth"] is False


def test_token_required(monkeypatch):
    c = client(monkeypatch, token="s3cret")
    assert c.post("/predict", json=BODY).status_code == 401
    assert c.post("/predict", json=BODY, headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert c.post("/predict", json=BODY, headers={"Authorization": "Bearer s3cret"}).status_code == 503
    assert c.get("/health").status_code == 200  # health 는 공개


def test_rate_limit_per_ip(monkeypatch):
    c = client(monkeypatch, per_min="2")
    h = {"X-Forwarded-For": "203.0.113.7"}
    assert [c.post("/predict", json=BODY, headers=h).status_code for _ in range(3)] == [503, 503, 429]
    r = c.post("/predict", json=BODY, headers=h)
    assert r.status_code == 429 and int(r.headers["Retry-After"]) >= 1
    assert c.post("/predict", json=BODY, headers={"X-Forwarded-For": "203.0.113.8"}).status_code == 503  # 다른 IP
