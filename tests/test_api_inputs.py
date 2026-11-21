"""/predict 입력 검증 경계와 /health·/model 의 판 보고 — 모델 없이 되는 것과 임시 모델로 하는 것."""
from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient
from test_mcp import model_dir  # noqa: F401 — 픽스처 재사용(고정 예문으로 학습한 임시 모델)
from test_pipeline import workdir  # noqa: F401

from paperclf.features import FEATURE_VERSION, N_FEATURES


def _client(monkeypatch, model_dir_path: str = "/nonexistent", app_version: str = "dev") -> TestClient:
    monkeypatch.setenv("API_TOKEN", "")
    monkeypatch.setenv("RATE_LIMIT_PER_MIN", "0")
    monkeypatch.setenv("MODEL_DIR", model_dir_path)
    monkeypatch.setenv("APP_VERSION", app_version)
    import api.app as app_module

    importlib.reload(app_module)
    return TestClient(app_module.app)


def _post_raw(c: TestClient, raw: bytes):
    return c.post("/predict", content=raw, headers={"content-type": "application/json"})


@pytest.mark.parametrize("body", [
    {},                                   # 제목도 특징도 없음
    {"title": ""},
    {"title": "   \n\t"},                # 공백만
    {"title": None, "abstract": "초록만 있음"},
    {"title": 123},                       # 숫자는 문자열로 바꾸지 않는다
    {"title": ["a"]},
    {"title": "x" * 1001},
    {"title": "x", "abstract": "y" * 20001},
    {"features": [[N_FEATURES, 1.0]]},    # 위치 범위 밖
    {"features": [[-1, 1.0]]},
    {"features": [[0, -0.5]]},            # 음수 빈도
    {"features": [[1.5, 1.0]]},           # 소수 위치
    {"features": [[1, 1.0, 1.0]]},        # 짝이 아님
    {"features": "1:1"},
    {"features": []},                     # 영벡터 — 아래 회귀 시험 참고
    {"features": [[5, 0.0]]},
    {"title": "?!"},                      # 글자·숫자가 없어 n-gram 이 하나도 안 나온다
    {"title": "\U0001F600", "abstract": "..."},
])
def test_predict_rejects_bad_input(monkeypatch, body):
    c = _client(monkeypatch)
    assert c.post("/predict", json=body).status_code == 422, body


@pytest.mark.parametrize("raw", [b'{"features":[[1,NaN]]}', b'{"features":[[1,Infinity]]}', b"[]", b"{not json", b""])
def test_predict_rejects_non_finite_and_malformed(monkeypatch, raw):
    """JSON 표준 밖의 NaN·Infinity 빈도도 422 — 통과하면 모델이 NaN 을 내고 응답 직렬화에서 500 이 난다."""
    c = _client(monkeypatch)
    assert _post_raw(c, raw).status_code == 422, raw


@pytest.mark.parametrize("body", [
    {"title": "x" * 1000, "abstract": "y" * 20000},   # 상한 그대로는 통과
    {"title": "x"},
    {"features": [[0, 0.0], [N_FEATURES - 1, 3.0]]},
])
def test_predict_accepts_boundaries_without_model(monkeypatch, body):
    """검증을 통과하면 모델이 없을 때 503 (422 가 아님)."""
    c = _client(monkeypatch)
    assert c.post("/predict", json=body).status_code == 503, body


def test_health_without_model(monkeypatch):
    c = _client(monkeypatch, app_version="v9.9.9")
    h = c.get("/health").json()
    assert h["status"] == "no_model" and h["model_version"] == "none"
    assert h["app_version"] == "v9.9.9" and h["feature_version"] == FEATURE_VERSION
    assert h["prediction_log"] == {"enabled": False, "written": 0, "dropped": 0}
    assert c.get("/model").status_code == 404


def test_health_reports_started_at(monkeypatch):
    """배포·되돌리기 뒤 컨테이너가 새로 떴는지 /health 만으로 보이게 — UTC ISO 시각."""
    import re

    h = _client(monkeypatch).get("/health").json()
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", h["started_at"])


def test_health_and_model_card_report_version(model_dir, monkeypatch):  # noqa: F811
    c = _client(monkeypatch, str(model_dir), app_version="v1.2.3")
    h = c.get("/health").json()
    assert h["status"] == "ok" and h["model"] == "onnx"
    assert h["model_version"] == "m20261119-7" and h["app_version"] == "v1.2.3"
    card = c.get("/model").json()
    assert card["model_version"] == h["model_version"]
    p = c.post("/predict", json={"title": "Managerial coaching", "abstract": "y" * 20000}).json()
    assert p["model_version"] == "m20261119-7" and 0.0 <= p["p_include"] <= 1.0


def test_predict_features_extremes_with_model(model_dir, monkeypatch):  # noqa: F811
    """빈 특징·아주 큰 빈도도 0~1 확률과 정해진 라벨을 돌려준다(500 이 아님)."""
    c = _client(monkeypatch, str(model_dir))
    for feats in ([[0, 1e30]], [[i, 1.0] for i in range(0, N_FEATURES, 64)]):
        r = c.post("/predict", json={"features": feats})
        assert r.status_code == 200, (feats[:2], r.text)
        body = r.json()
        assert 0.0 <= body["p_include"] <= 1.0 and body["label"] in ("include", "exclude", "uncertain")
    for raw in (b'{"features":[[1,NaN]]}', b'{"features":[[1,Infinity]]}'):
        assert _post_raw(c, raw).status_code == 422


@pytest.mark.parametrize("body", [{"title": "?!"}, {"title": "\U0001F600"}, {"features": []}])
def test_zero_vector_is_422_not_nan(model_dir, monkeypatch, body):  # noqa: F811
    """회귀: 특징이 하나도 없으면 ONNX tf-idf 정규화가 0/0 → p_include NaN 이었다
    (/predict 는 p_include=null·label=uncertain, /mcp 는 500, 표준 입출력 MCP 는 JSON 이 아닌 NaN)."""
    c = _client(monkeypatch, str(model_dir))
    r = c.post("/predict", json=body)
    assert r.status_code == 422 and "특징" in r.json()["detail"]
