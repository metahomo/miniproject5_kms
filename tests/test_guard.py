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


class _Clock:
    def __init__(self, t: float = 1000.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t


def test_rate_limit_window_resets(monkeypatch):
    """1분 창이 지나면 다시 허용, Retry-After 는 가장 오래된 요청이 창을 벗어나는 시각에 맞춘다."""
    import api.guard as guard_module

    clock = _Clock()
    monkeypatch.setattr(guard_module.time, "monotonic", clock)
    c = client(monkeypatch, per_min="2")
    h = {"X-Forwarded-For": "203.0.113.9"}
    post = lambda: c.post("/predict", json=BODY, headers=h)  # noqa: E731
    assert post().status_code == 503
    clock.t += 30
    assert post().status_code == 503
    clock.t += 20  # 첫 요청 뒤 50초
    r = post()
    assert r.status_code == 429 and r.headers["Retry-After"] == "11"
    clock.t += 9.9  # 59.9초 — 아직 창 안
    assert post().status_code == 429
    clock.t += 0.1  # 정확히 60초 — 첫 요청이 빠진다
    assert post().status_code == 503
    assert post().status_code == 429  # 두 번째(30초) 요청이 아직 창 안
    clock.t += 1000
    assert [post().status_code for _ in range(3)] == [503, 503, 429]
    g = c.get("/health").json()["guard"]
    assert g["rejected_rate"] == 4 and g["rejected_auth"] == 0


def test_rate_limit_off_and_rejected_counts(monkeypatch):
    c = client(monkeypatch, token="s3cret", per_min="0")
    h = {"Authorization": "Bearer s3cret"}
    assert {c.post("/predict", json=BODY, headers=h).status_code for _ in range(100)} == {503}
    c.post("/predict", json=BODY)
    assert c.get("/health").json()["guard"] == {"auth": True, "rate_limit_per_min": 0, "rejected_auth": 1, "rejected_rate": 0}


def test_auth_header_variants(monkeypatch):
    """Bearer 형식만, 토큰은 정확히 같아야(접두어·대소문자·공백 차이 거부)."""
    c = client(monkeypatch, token="s3cret")
    for value in ("s3cret", "bearer s3cret", "Bearer  s3cret", "Bearer s3cret ", "Bearer s3cre", "Bearer s3cretX",
                  "Basic czNjcmV0", "Bearer ", "Bearer"):
        r = c.post("/predict", json=BODY, headers={"Authorization": value})
        assert r.status_code == 401 and r.headers["WWW-Authenticate"] == "Bearer", value


def test_auth_runs_before_rate_limit(monkeypatch):
    """토큰 없는 요청은 사용량을 쓰지 않는다 — 남의 IP 로 401 을 쏟아 정상 사용자를 막을 수 없다."""
    c = client(monkeypatch, token="s3cret", per_min="1")
    h = {"X-Forwarded-For": "203.0.113.20"}
    for _ in range(5):
        assert c.post("/predict", json=BODY, headers=h).status_code == 401
    assert c.post("/predict", json=BODY, headers={**h, "Authorization": "Bearer s3cret"}).status_code == 503


def test_token_compare_is_constant_time(monkeypatch):
    """비교는 hmac.compare_digest 로만 한다(== 비교는 시간 차로 토큰이 샌다)."""
    import api.guard as guard_module

    calls = []
    real = guard_module.hmac.compare_digest
    monkeypatch.setattr(guard_module.hmac, "compare_digest", lambda a, b: calls.append((a, b)) or real(a, b))
    c = client(monkeypatch, token="s3cret")
    assert c.post("/predict", json=BODY, headers={"Authorization": "Bearer nope"}).status_code == 401
    assert c.post("/predict", json=BODY, headers={"Authorization": "Bearer s3cret"}).status_code == 503
    assert calls == [(b"nope", b"s3cret"), (b"s3cret", b"s3cret")]


def test_client_ip_uses_last_forwarded_hop(monkeypatch):
    """X-Forwarded-For 의 마지막 값(Caddy 가 붙인 실제 주소) — 앞쪽은 클라이언트가 꾸밀 수 있다."""
    c = client(monkeypatch, per_min="1")
    assert c.post("/predict", json=BODY, headers={"X-Forwarded-For": "1.1.1.1, 203.0.113.30"}).status_code == 503
    # 앞쪽 값을 바꿔도 같은 IP 로 센다
    assert c.post("/predict", json=BODY, headers={"X-Forwarded-For": "9.9.9.9, 203.0.113.30"}).status_code == 429
    assert c.post("/predict", json=BODY, headers={"X-Forwarded-For": "203.0.113.30 , 203.0.113.31"}).status_code == 503
    assert c.post("/predict", json=BODY).status_code == 503  # 헤더 없음 → 소켓 주소(testclient)


def test_stale_ips_pruned(monkeypatch):
    """IP 가 1만 개를 넘으면 창이 지난 IP 는 지운다(메모리 상한)."""
    import api.guard as guard_module

    clock = _Clock()
    monkeypatch.setattr(guard_module.time, "monotonic", clock)
    g = guard_module.Guard(token="", per_min=5)
    for i in range(10000):
        g._hits[f"old-{i}"] = guard_module.deque([clock.t])
    clock.t += 61

    class _Req:
        headers = {"x-forwarded-for": "203.0.113.40"}
        client = None
    g.check(_Req())
    assert list(g._hits) == ["203.0.113.40"]
