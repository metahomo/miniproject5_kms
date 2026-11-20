"""MCP 서버 — 표준 입출력, 한 줄에 JSON-RPC 2.0 메시지 하나. 도구는 classify_paper 하나(읽기 전용).

    MODEL_DIR=artifacts uv run python -m api.mcp_server

모델은 HTTP 로 부르지 않고 api.app 의 MODEL·vectorize·label_for 를 프로세스 안에서 그대로 쓴다
(MODEL_DIR·MODEL_IMPL 환경변수도 app.py 와 같다). 표준 출력에는 프로토콜 메시지만, 진단은 표준 오류로.
어떤 요청이 실패해도 다음 줄을 계속 읽는다.
"""

from __future__ import annotations

import json
import logging
import math
import sys
from typing import BinaryIO

from api import app as app_module
from paperclf.features import FEATURE_VERSION, vectorize
from paperclf.labels import EXCLUDE_AT, INCLUDE_AT, label_for

SUPPORTED_VERSIONS = ("2025-11-25", "2024-11-05")
PARSE_ERROR, INVALID_REQUEST, METHOD_NOT_FOUND, INVALID_PARAMS, INTERNAL_ERROR = -32700, -32600, -32601, -32602, -32603
TITLE_MAX, ABSTRACT_MAX = 1000, 20000

log = logging.getLogger("paperclf.mcp")

TOOL = {
    "name": "classify_paper",
    "title": "논문 주제 적합도 판정",
    "description": "논문 제목(과 초록)이 KMS 주제(coaching-leadership)에 맞는지 학생 모델로 판정한다. 읽기 전용.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "minLength": 1, "maxLength": TITLE_MAX},
            "abstract": {"type": "string", "maxLength": ABSTRACT_MAX},
        },
        "required": ["title"],
        "additionalProperties": False,
    },
    "outputSchema": {
        "type": "object",
        "properties": {
            "p_include": {"type": "number", "minimum": 0, "maximum": 1},
            "label": {"type": "string", "enum": ["include", "exclude", "uncertain"]},
            "model_version": {"type": "string"},
            "feature_version": {"type": "string"},
            "thresholds": {
                "type": "object",
                "properties": {"include_at": {"type": "number"}, "exclude_at": {"type": "number"}},
                "required": ["include_at", "exclude_at"],
            },
        },
        "required": ["p_include", "label", "model_version", "thresholds"],
    },
    "annotations": {"readOnlyHint": True, "openWorldHint": False},
}


def _server_info() -> dict:
    return {"name": "paperclf", "version": app_module.APP_VERSION}


def _error(msg_id, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


class _ProtocolError(Exception):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code


def _check(arguments: object) -> tuple[str, str | None]:
    if not isinstance(arguments, dict):
        raise _ProtocolError(INVALID_PARAMS, "arguments 는 객체여야 한다")
    extra = sorted(set(arguments) - {"title", "abstract"})
    if extra:
        raise _ProtocolError(INVALID_PARAMS, f"알 수 없는 인자: {', '.join(extra)}")
    title = arguments.get("title")
    if not isinstance(title, str) or not title.strip():
        raise _ProtocolError(INVALID_PARAMS, "title(비어 있지 않은 문자열)이 필요하다")
    if len(title) > TITLE_MAX:
        raise _ProtocolError(INVALID_PARAMS, f"title 은 {TITLE_MAX}자 이하여야 한다")
    abstract = arguments.get("abstract")
    if abstract is not None and not isinstance(abstract, str):
        raise _ProtocolError(INVALID_PARAMS, "abstract 는 문자열이어야 한다")
    if abstract is not None and len(abstract) > ABSTRACT_MAX:
        raise _ProtocolError(INVALID_PARAMS, f"abstract 는 {ABSTRACT_MAX}자 이하여야 한다")
    return title, abstract


def classify(arguments: object) -> dict:
    """tools/call 결과. 인자 오류는 -32602(_ProtocolError), 모델 없음은 isError 결과."""
    title, abstract = _check(arguments)
    x = vectorize(title, abstract)
    if not x.any():  # 영벡터는 p_include 가 NaN 이 된다 — /predict 의 422 와 같은 경우
        raise _ProtocolError(INVALID_PARAMS, "특징이 없다 — title·abstract 에 글자나 숫자가 있어야 한다")
    model = app_module.MODEL  # 시험에서 api.app 을 다시 불러와도 최신 모델을 쓰도록 호출마다 읽는다
    if not model.ready:
        detail = "모델이 없다 (MODEL_DIR·MODEL_IMPL 확인)"
        return {"content": [{"type": "text", "text": f"{detail} (code: no_model)"}],
                "structuredContent": {"code": "no_model", "detail": detail}, "isError": True}
    p = float(model.p_include(x.reshape(1, -1))[0])
    label = label_for(p)
    structured = {
        "p_include": p,
        "label": label,
        "model_version": model.version,
        "feature_version": FEATURE_VERSION,
        "thresholds": {"include_at": INCLUDE_AT, "exclude_at": EXCLUDE_AT},
    }
    text = f"{label} (p={p:.2f}, 모델 {model.version})"
    return {"content": [{"type": "text", "text": text}], "structuredContent": structured, "isError": False}


def _dispatch(method: str, params: dict) -> dict:
    if method == "initialize":
        requested = params.get("protocolVersion")
        chosen = requested if requested in SUPPORTED_VERSIONS else SUPPORTED_VERSIONS[0]
        return {"protocolVersion": chosen, "capabilities": {"tools": {}}, "serverInfo": _server_info()}
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": [TOOL]}
    if method == "tools/call":
        name = params.get("name")
        if name != TOOL["name"]:
            raise _ProtocolError(INVALID_PARAMS, f"Unknown tool: {name}")
        return classify(params.get("arguments", {}))
    raise _ProtocolError(METHOD_NOT_FOUND, f"Method not found: {method}")


def handle(message: object) -> dict | None:
    """요청 하나 → 응답(알림이면 None)."""
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0" or not isinstance(message.get("method"), str):
        msg_id = message.get("id") if isinstance(message, dict) else None
        return _error(msg_id, INVALID_REQUEST, "Invalid Request")
    method = message["method"]
    if "id" not in message:  # 알림 — notifications/initialized 등
        log.info("알림 %s", method)
        return None
    msg_id = message["id"]
    if isinstance(msg_id, bool) or not (msg_id is None or isinstance(msg_id, (str, int))
                                        or (isinstance(msg_id, float) and math.isfinite(msg_id))):
        return _error(None, INVALID_REQUEST, "id 는 문자열·숫자·null 이어야 한다")  # NaN id 는 응답을 JSON 으로 못 쓴다
    params = message.get("params") or {}
    if not isinstance(params, dict):
        return _error(msg_id, INVALID_PARAMS, "params 는 객체여야 한다")
    try:
        result = _dispatch(method, params)
    except _ProtocolError as exc:
        return _error(msg_id, exc.code, str(exc))
    except Exception:  # 내부 예외도 프로세스를 끝내지 않는다
        log.exception("MCP 요청 처리 실패: %s", method)
        return _error(msg_id, INTERNAL_ERROR, "Internal error")
    log.info("요청 %s 처리", method)
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def handle_line(raw: bytes) -> dict | None:
    if not raw.strip():
        return None
    try:
        message = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _error(None, PARSE_ERROR, "Parse error")
    return handle(message)


def serve(stdin: BinaryIO, stdout: BinaryIO) -> int:
    """입력이 닫힐 때까지 한 줄씩 처리한다."""
    for raw in stdin:
        response = handle_line(raw)
        if response is None:
            continue
        stdout.write(json.dumps(response, ensure_ascii=False, separators=(",", ":")).encode("utf-8") + b"\n")
        stdout.flush()
    return 0


def main() -> int:
    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    log.info("paperclf MCP 시작: model=%s version=%s ready=%s",
             app_module.MODEL_IMPL, app_module.MODEL.version, app_module.MODEL.ready)
    return serve(sys.stdin.buffer, sys.stdout.buffer)


if __name__ == "__main__":
    raise SystemExit(main())
