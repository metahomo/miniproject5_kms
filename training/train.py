"""학습 — TF-IDF(해싱 빈도 위) + 로지스틱 회귀. 결과는 artifacts/ 에 남긴다.

    uv run --group train python -m training.train
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path

from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from training.data import load
from training.metrics import baseline_f1, score

ART = Path("artifacts")
# 실험 추적 대상: 이 값에 따라 결과가 달라진다
# sublinear_tf=True 는 skl2onnx 변환 결과가 원본과 최대 0.002 어긋나 parity 를 못 넘는다(2026-11-19 확인).
PARAMS = {"C": 4.0, "class_weight": "balanced", "sublinear_tf": False, "max_iter": 5000}


def build_model() -> Pipeline:
    return Pipeline(
        [
            ("tfidf", TfidfTransformer(sublinear_tf=PARAMS["sublinear_tf"])),
            (
                "clf",
                LogisticRegression(
                    C=PARAMS["C"], class_weight=PARAMS["class_weight"], max_iter=PARAMS["max_iter"]
                ),
            ),
        ]
    )


def main() -> None:
    train, gate, info = load()
    if len(set(train.y.tolist())) < 2:
        raise SystemExit("학습 데이터에 두 클래스가 모두 있어야 한다")
    model = build_model().fit(train.X, train.y)
    p_gate = model.predict_proba(gate.X)[:, 1]
    p_train = model.predict_proba(train.X)[:, 1]
    metrics = {
        "data": info,
        "params": PARAMS,
        "gate": score(gate.y, p_gate),
        "train": score(train.y, p_train),
        "baseline_f1": baseline_f1(gate.y),
    }
    ART.mkdir(exist_ok=True)
    with open(ART / "model_sklearn.pkl", "wb") as fh:
        pickle.dump(model, fh)
    (ART / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
