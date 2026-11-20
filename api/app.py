"""논문 적합도 예측 API.

- MODEL_IMPL=onnx(기본): MODEL_DIR 의 model.onnx 를 onnxruntime 으로 돌린다(서버용, sklearn 불필요).
- MODEL_IMPL=sklearn: MODEL_DIR 의 model_sklearn.pkl — parity 비교 기준(학습 그룹 필요).
- /health 는 app_version(이미지 태그)과 model_version(모델 카드)을 알려 준다.
"""

from __future__ import annotations

import json
import math
import os
import pickle
import time
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field, model_validator

from paperclf.features import FEATURE_VERSION, N_FEATURES, to_dense, vectorize
from paperclf.labels import label_for

from api.guard import Guard
from api.prediction_log import PredictionLog

APP_VERSION = os.getenv("APP_VERSION", "dev")
MODEL_IMPL = os.getenv("MODEL_IMPL", "onnx")
MODEL_DIR = Path(os.getenv("MODEL_DIR", "artifacts"))


def _load_card() -> dict | None:
    p = MODEL_DIR / "model.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


class _Model:
    def __init__(self) -> None:
        self.card = _load_card()
        self.version = self.card["model_version"] if self.card else "none"
        self._predict = None
        if MODEL_IMPL == "onnx" and (MODEL_DIR / "model.onnx").is_file():
            import onnxruntime as ort

            sess = ort.InferenceSession(str(MODEL_DIR / "model.onnx"), providers=["CPUExecutionProvider"])
            self._predict = lambda X: sess.run(None, {"input": X.astype(np.float64)})[1][:, 1]
        elif MODEL_IMPL == "sklearn" and (MODEL_DIR / "model_sklearn.pkl").is_file():
            with open(MODEL_DIR / "model_sklearn.pkl", "rb") as fh:
                skl = pickle.load(fh)
            self._predict = lambda X: skl.predict_proba(X)[:, 1]

    @property
    def ready(self) -> bool:
        return self._predict is not None

    def p_include(self, X: np.ndarray) -> np.ndarray:
        if self._predict is None:
            raise HTTPException(status_code=503, detail="모델이 없다")
        return np.asarray(self._predict(X), dtype=np.float64)


MODEL = _Model()
PREDICTION_LOG = PredictionLog()
GUARD = Guard()
app = FastAPI(title="paperclf", version=APP_VERSION)


@app.exception_handler(RequestValidationError)
async def _validation_error(request: Request, exc: RequestValidationError):
    """422 본문은 입력을 되돌려 주는데, 입력에 NaN·Infinity(표준 밖 JSON)가 있으면 직렬화가 실패해 500 이 된다.
    그때만 input·ctx 를 빼고 422 로 답한다."""
    try:
        return await request_validation_exception_handler(request, exc)
    except ValueError:
        detail = [{k: v for k, v in e.items() if k not in ("input", "ctx")} for e in exc.errors()]
        return JSONResponse(status_code=422, content={"detail": detail})


class Paper(BaseModel):
    title: str | None = Field(default=None, max_length=1000)
    abstract: str | None = Field(default=None, max_length=20000)
    features: list[tuple[int, float]] | None = Field(
        default=None, max_length=N_FEATURES, description="parity 확인용: 해싱 특징 [[위치, 빈도], …]"
    )

    @model_validator(mode="after")
    def _one_input(self):
        if self.features is None and not (self.title or "").strip():
            raise ValueError("title 또는 features 가 필요하다")
        if self.features is not None and any(not 0 <= i < N_FEATURES or not math.isfinite(c) or c < 0 for i, c in self.features):
            raise ValueError("features 범위 밖")
        return self


class Prediction(BaseModel):
    p_include: float
    label: str
    model_version: str


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok" if MODEL.ready else "no_model",
        "model": MODEL_IMPL,
        "app_version": APP_VERSION,
        "model_version": MODEL.version,
        "feature_version": FEATURE_VERSION,
        "guard": GUARD.status(),
        "prediction_log": {"enabled": PREDICTION_LOG.enabled, "written": PREDICTION_LOG.written, "dropped": PREDICTION_LOG.dropped},
    }


@app.post("/predict", response_model=Prediction)
def predict(paper: Paper, request: Request) -> Prediction:
    GUARD.check(request)
    t0 = time.perf_counter()
    x = to_dense(paper.features) if paper.features is not None else vectorize(paper.title, paper.abstract)
    if not x.any():  # 영벡터는 tf-idf 정규화에서 0/0 → p_include 가 NaN 이 된다 (예: 제목 "?"·이모지만)
        raise HTTPException(status_code=422, detail="특징이 없다 — 제목·초록에 글자나 숫자가 있어야 한다")
    p = float(MODEL.p_include(x.reshape(1, -1))[0])
    label = label_for(p)
    if paper.features is None:  # parity 확인용 특징 입력은 운영 예측이 아니라 남기지 않는다
        PREDICTION_LOG.record(MODEL.version, paper.title, paper.abstract, p, label, (time.perf_counter() - t0) * 1000)
    return Prediction(p_include=p, label=label, model_version=MODEL.version)


@app.get("/model")
def model_card() -> dict:
    if MODEL.card is None:
        raise HTTPException(status_code=404, detail="모델 카드가 없다")
    return MODEL.card


@app.post("/mcp")
async def mcp_http(request: Request):
    """원격 MCP(Streamable HTTP 의 JSON 응답 방식) — 도구 classify_paper. /predict 와 같은 토큰·사용량 제한.

    요청 하나(JSON-RPC 2.0)를 받아 응답 하나를 JSON 으로 돌려준다. 알림(id 없음)은 202.
    처리는 표준 입출력 판과 같은 api.mcp_server.handle 을 쓴다.
    """
    GUARD.check(request)
    from api import mcp_server  # 순환 import 를 피해 호출 때 읽는다

    try:
        message = await request.json()
    except Exception:
        return JSONResponse(mcp_server._error(None, -32700, "Parse error"), status_code=400)
    reply = mcp_server.handle(message)
    if reply is None:
        return Response(status_code=202)
    return JSONResponse(reply)


@app.get("/mcp")
def mcp_http_get() -> Response:
    return Response(status_code=405, headers={"Allow": "POST"})  # 서버 → 클라이언트 스트림(SSE)은 쓰지 않는다

