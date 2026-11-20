"""MCP 서버(api.mcp_server) — 고정 예문으로 만든 임시 모델로 프로토콜·도구·HTTP 일치·표준 입출력을 확인한다."""

from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from test_pipeline import workdir  # noqa: F401 — 픽스처 재사용(고정 예문 스냅숏 → 임시 작업 폴더)

from paperclf.labels import EXCLUDE_AT, INCLUDE_AT

ROOT = Path(__file__).resolve().parents[1]
PAPER = {"title": "Managerial coaching and employee engagement", "abstract": "supervisors coaching employees"}


def _rpc(method: str, params: dict | None = None, msg_id: int = 1) -> dict:
    msg = {"jsonrpc": "2.0", "id": msg_id, "method": method}
    if params is not None:
        msg["params"] = params
    return msg


@pytest.fixture()
def model_dir(workdir, monkeypatch):  # noqa: F811
    from training import export_onnx, model_card, train, validate_model

    train.main()
    assert validate_model.main() == 0
    export_onnx.main()
    monkeypatch.setenv("MODEL_VERSION", "m20261119-7")
    model_card.main()
    art = workdir / "artifacts"
    monkeypatch.setenv("MODEL_DIR", str(art))
    monkeypatch.setenv("MODEL_IMPL", "onnx")
    return art


@pytest.fixture()
def mcp(model_dir):
    import api.app as app_module

    importlib.reload(app_module)
    import api.mcp_server as mcp_module

    importlib.reload(mcp_module)
    assert app_module.MODEL.ready
    return mcp_module


def test_initialize_and_tools_list(mcp):
    for ver in ("2025-11-25", "2024-11-05"):
        r = mcp.handle(_rpc("initialize", {"protocolVersion": ver, "capabilities": {}, "clientInfo": {"name": "t"}}))
        res = r["result"]
        assert res["protocolVersion"] == ver and res["capabilities"] == {"tools": {}}
        assert res["serverInfo"]["name"] == "paperclf" and res["serverInfo"]["version"]
    assert mcp.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None

    tools = mcp.handle(_rpc("tools/list"))["result"]["tools"]
    assert [t["name"] for t in tools] == ["classify_paper"]
    t = tools[0]
    assert t["inputSchema"] == {
        "type": "object",
        "properties": {"title": {"type": "string", "minLength": 1, "maxLength": 1000},
                       "abstract": {"type": "string", "maxLength": 20000}},
        "required": ["title"], "additionalProperties": False,
    }
    assert "p_include" in t["outputSchema"]["properties"] and "읽기 전용" in t["description"]


def test_tools_call_ok_and_errors(mcp):
    r = mcp.handle(_rpc("tools/call", {"name": "classify_paper", "arguments": PAPER}))["result"]
    s = r["structuredContent"]
    assert r["isError"] is False and 0.0 <= s["p_include"] <= 1.0
    assert s["label"] in ("include", "exclude", "uncertain") and s["model_version"] == "m20261119-7"
    assert s["thresholds"] == {"include_at": INCLUDE_AT, "exclude_at": EXCLUDE_AT} == {"include_at": 0.7, "exclude_at": 0.3}
    assert r["content"][0]["type"] == "text" and r["content"][0]["text"].startswith(f"{s['label']} (p=")
    assert "m20261119-7" in r["content"][0]["text"] and s["feature_version"]

    for bad in ({"title": ""}, {"title": "   "}, {}, {"title": "x", "extra": 1}, {"title": "x" * 1001},
                {"title": "x", "abstract": 3}, {"title": "?!"}, {"title": "\U0001F600", "abstract": "..."}):
        e = mcp.handle(_rpc("tools/call", {"name": "classify_paper", "arguments": bad}))
        assert e["error"]["code"] == -32602, bad
    assert mcp.handle(_rpc("tools/call", {"name": "nope", "arguments": PAPER}))["error"]["code"] == -32602
    assert mcp.handle(_rpc("resources/list"))["error"]["code"] == -32601
    assert mcp.handle_line(b"{not json")["error"]["code"] == -32700


def test_no_model_is_tool_error(tmp_path, monkeypatch):
    monkeypatch.setenv("MODEL_DIR", str(tmp_path))
    monkeypatch.setenv("MODEL_IMPL", "onnx")
    import api.app as app_module

    importlib.reload(app_module)
    import api.mcp_server as mcp_module

    r = mcp_module.handle(_rpc("tools/call", {"name": "classify_paper", "arguments": {"title": "x"}}))["result"]
    assert r["isError"] is True and r["structuredContent"]["code"] == "no_model"


def test_mcp_matches_http_predict(mcp):
    import api.app as app_module

    http = TestClient(app_module.app).post("/predict", json=PAPER).json()
    s = mcp.handle(_rpc("tools/call", {"name": "classify_paper", "arguments": PAPER}))["result"]["structuredContent"]
    assert s["p_include"] == http["p_include"]
    assert s["label"] == http["label"] and s["model_version"] == http["model_version"]


def test_stdio_subprocess(model_dir):
    lines = [
        _rpc("initialize", {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "t"}}, 1),
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        _rpc("tools/call", {"name": "classify_paper", "arguments": PAPER}, 2),
    ]
    stdin = "".join(json.dumps(m, ensure_ascii=False) + "\n" for m in lines).encode("utf-8")
    env = {**os.environ, "MODEL_DIR": str(model_dir), "MODEL_IMPL": "onnx"}
    proc = subprocess.run([sys.executable, "-m", "api.mcp_server"], input=stdin, capture_output=True,
                          cwd=ROOT, env=env, timeout=60, check=False)
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    out = [json.loads(x) for x in proc.stdout.decode("utf-8").splitlines()]
    assert [m["id"] for m in out] == [1, 2]  # 알림에는 응답이 없고, 표준 출력에는 프로토콜 메시지만
    assert out[0]["result"]["serverInfo"]["name"] == "paperclf"
    res = out[1]["result"]
    assert res["isError"] is False and res["structuredContent"]["model_version"] == "m20261119-7"


def test_remote_mcp_http(mcp, monkeypatch):
    """원격 MCP(POST /mcp): 토큰이 있어야 하고, 표준 입출력 판과 같은 답을 한다."""
    import api.app as app_module

    monkeypatch.setenv("API_TOKEN", "t0ken")
    app_module.GUARD = app_module.Guard()
    c = TestClient(app_module.app)
    assert c.post("/mcp", json=_rpc("tools/list")).status_code == 401
    h = {"Authorization": "Bearer t0ken"}
    init = c.post("/mcp", json=_rpc("initialize", {"protocolVersion": "2025-06-18"}), headers=h).json()
    assert init["result"]["capabilities"] == {"tools": {}}
    assert c.post("/mcp", json={"jsonrpc": "2.0", "method": "notifications/initialized"}, headers=h).status_code == 202
    tools = c.post("/mcp", json=_rpc("tools/list"), headers=h).json()["result"]["tools"]
    assert [t["name"] for t in tools] == ["classify_paper"]
    r = c.post("/mcp", json=_rpc("tools/call", {"name": "classify_paper", "arguments": PAPER}), headers=h).json()["result"]
    assert r["structuredContent"]["model_version"] == "m20261119-7"
    p = c.post("/predict", json=PAPER, headers=h).json()
    assert abs(r["structuredContent"]["p_include"] - p["p_include"]) < 1e-12
    assert c.post("/mcp", content=b"{not json", headers={**h, "content-type": "application/json"}).status_code == 400
    assert c.get("/mcp").status_code == 405



def test_protocol_error_paths(mcp, monkeypatch):
    """JSON-RPC 오류 경로: 잘못된 요청 모양, params, id 보존, ping, 버전 협상, 내부 예외."""
    assert mcp.handle([_rpc("ping")]) == mcp._error(None, -32600, "Invalid Request")  # 일괄(배열)은 지원하지 않는다
    assert mcp.handle("ping")["error"]["code"] == -32600
    assert mcp.handle({"jsonrpc": "1.0", "id": 5, "method": "ping"}) == mcp._error(5, -32600, "Invalid Request")
    assert mcp.handle({"jsonrpc": "2.0", "id": 6})["error"]["code"] == -32600  # method 없음
    assert mcp.handle({"jsonrpc": "2.0", "id": 7, "method": 3})["error"]["code"] == -32600
    assert mcp.handle({**_rpc("ping", msg_id=8), "params": [1]}) == mcp._error(8, -32602, "params 는 객체여야 한다")
    assert mcp.handle({**_rpc("ping", msg_id=9), "params": None})["result"] == {}
    for msg_id in ("abc", 0, None, 2.0):
        assert mcp.handle({"jsonrpc": "2.0", "id": msg_id, "method": "ping"}) == {"jsonrpc": "2.0", "id": msg_id, "result": {}}
    for bad_id in (float("nan"), float("inf"), True, {"a": 1}, [1]):
        r = mcp.handle({"jsonrpc": "2.0", "id": bad_id, "method": "ping"})
        assert r["id"] is None and r["error"]["code"] == -32600, bad_id
    assert mcp.handle({"jsonrpc": "2.0", "method": "no/such"}) is None  # 알림에는 오류도 답하지 않는다
    assert mcp.handle(_rpc("initialize", {"protocolVersion": "1999-01-01"}))["result"]["protocolVersion"] == "2025-11-25"
    assert mcp.handle(_rpc("initialize"))["result"]["protocolVersion"] == "2025-11-25"
    assert mcp.handle(_rpc("tools/call", {"name": "classify_paper"}))["error"]["code"] == -32602  # arguments 없음
    assert mcp.handle(_rpc("tools/call", {"name": "classify_paper", "arguments": "x"}))["error"]["code"] == -32602

    def boom(_):
        raise RuntimeError("secret detail")
    monkeypatch.setattr(mcp, "classify", boom)
    r = mcp.handle(_rpc("tools/call", {"name": "classify_paper", "arguments": PAPER}, msg_id=10))
    assert r == mcp._error(10, -32603, "Internal error")  # 내부 메시지는 밖으로 내보내지 않는다


def test_handle_line_and_serve_keep_going(mcp):
    import io

    assert mcp.handle_line(b"   \n") is None
    assert mcp.handle_line(b"\xff\xfe\n")["error"]["code"] == -32700  # UTF-8 아님
    lines = b"{bad\n\n" + json.dumps(_rpc("ping", msg_id=1)).encode() + b"\n" + b'{"jsonrpc":"2.0","id":NaN,"method":"ping"}\n' \
        + json.dumps(_rpc("tools/call", {"name": "classify_paper", "arguments": PAPER}, 2)).encode() + b"\n"
    out = io.BytesIO()
    assert mcp.serve(io.BytesIO(lines), out) == 0
    replies = [json.loads(x) for x in out.getvalue().decode().splitlines()]  # 모두 표준 JSON 이어야 한다
    assert [r.get("id") for r in replies] == [None, 1, None, 2]
    assert [r.get("error", {}).get("code") for r in replies] == [-32700, None, -32600, None]


def test_remote_mcp_http_edge(mcp, monkeypatch):
    """POST /mcp: 배열·NaN id 는 200 + 오류 객체(500 이 아님), 사용량 제한은 /predict 와 같은 바구니."""
    import api.app as app_module

    monkeypatch.setenv("API_TOKEN", "")
    monkeypatch.setenv("RATE_LIMIT_PER_MIN", "3")
    app_module.GUARD = app_module.Guard()
    c = TestClient(app_module.app)
    h = {"X-Forwarded-For": "198.51.100.1", "content-type": "application/json"}
    r = c.post("/mcp", content=b"[]", headers=h)
    assert r.status_code == 200 and r.json()["error"]["code"] == -32600
    r = c.post("/mcp", content=b'{"jsonrpc":"2.0","id":NaN,"method":"ping"}', headers=h)
    assert r.status_code == 200 and r.json()["error"]["code"] == -32600
    assert c.post("/predict", json=PAPER, headers=h).status_code == 200
    assert c.post("/mcp", json=_rpc("ping"), headers=h).status_code == 429
