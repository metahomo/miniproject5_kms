"""학습 → 게이트 → ONNX → 모델 카드 → API 를 고정 예문 스냅숏으로 끝까지 돌린다."""

from __future__ import annotations

import gzip
import importlib
import json
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from paperclf.features import FEATURE_VERSION, counts, doc_text

FIX = Path(__file__).parent / "fixtures" / "papers.json"


def _write_snapshot(d: Path) -> None:
    papers = json.loads(FIX.read_text(encoding="utf-8"))
    d.mkdir(parents=True)
    with gzip.open(d / "fixture-20261119.jsonl.gz", "wt", encoding="utf-8") as fh:
        fh.write(json.dumps({"_meta": {"feature_version": FEATURE_VERSION, "topic": "t", "n": 48}}) + "\n")
        for rep in range(4):  # 같은 예문을 키만 바꿔 4번 — 두 분할 모두에 두 클래스가 들어가게
            for i, p in enumerate(papers):
                key = f"fix:{rep}-{i}"
                fh.write(json.dumps({
                    "key": key, "label": p["label"], "split": "gate" if rep == 0 else "train",
                    "features": sorted([k, v] for k, v in counts(doc_text(p["title"], p["abstract"])).items()),
                }) + "\n")


@pytest.fixture()
def workdir(tmp_path, monkeypatch):
    _write_snapshot(tmp_path / "snaps")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SNAPSHOT_DIR", str(tmp_path / "snaps"))
    (tmp_path / "tests" / "fixtures").mkdir(parents=True)
    (tmp_path / "tests" / "fixtures" / "papers.json").write_text(FIX.read_text(encoding="utf-8"), encoding="utf-8")
    import training.data
    importlib.reload(training.data)
    for m in ("training.train", "training.export_onnx", "training.check_parity"):
        importlib.reload(importlib.import_module(m))
    return tmp_path


def test_train_gate_onnx_card_and_serve(workdir, monkeypatch):
    from training import export_onnx, model_card, train, validate_model

    train.main()
    assert validate_model.main() == 0
    export_onnx.main()
    assert json.loads((workdir / "artifacts" / "onnx_check.json").read_text())["max_abs_diff"] <= 1e-5
    monkeypatch.setenv("MODEL_VERSION", "m20261119-1")
    model_card.main()
    card = json.loads((workdir / "artifacts" / "model.json").read_text(encoding="utf-8"))
    assert card["model_version"] == "m20261119-1" and card["gate_result"]["passed"]

    monkeypatch.setenv("MODEL_DIR", str(workdir / "artifacts"))
    results = {}
    for impl in ("onnx", "sklearn"):
        monkeypatch.setenv("MODEL_IMPL", impl)
        import api.app as app_module
        importlib.reload(app_module)
        c = TestClient(app_module.app)
        h = c.get("/health").json()
        assert h["status"] == "ok" and h["model_version"] == "m20261119-1" and h["model"] == impl
        r = c.post("/predict", json={"title": "Managerial coaching and employee engagement",
                                     "abstract": "supervisors coaching employees"}).json()
        results[impl] = r["p_include"]
        assert r["model_version"] == "m20261119-1"
    assert abs(results["onnx"] - results["sklearn"]) <= 1e-5


def test_gate_blocks_degraded_model(workdir, monkeypatch):
    from training import train, validate_model

    train.main()
    monkeypatch.setenv("GATE_MIN_F1", "1.01")  # 도달할 수 없는 하한 → 반드시 막혀야 한다
    assert validate_model.main() == 1
    m = json.loads((workdir / "artifacts" / "metrics.json").read_text(encoding="utf-8"))
    assert m["gate_result"]["passed"] is False


def test_card_refuses_ungated_model(workdir, monkeypatch):
    from training import model_card, train

    train.main()
    monkeypatch.setenv("MODEL_VERSION", "m20261119-2")
    with pytest.raises(SystemExit):
        model_card.main()


def test_api_without_model_reports_no_model(tmp_path, monkeypatch):
    monkeypatch.setenv("MODEL_DIR", str(tmp_path))
    monkeypatch.setenv("MODEL_IMPL", "onnx")
    import api.app as app_module
    importlib.reload(app_module)
    c = TestClient(app_module.app)
    assert c.get("/health").json()["status"] == "no_model"
    assert c.post("/predict", json={"title": "x"}).status_code == 503
    assert c.post("/predict", json={}).status_code == 422
    assert c.post("/predict", json={"features": [[99999999, 1]]}).status_code == 422
