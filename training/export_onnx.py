"""scikit-learn → ONNX. 변환 직후 게이트 시험지로 원본과 확률을 비교한다.

    uv run --group train python -m training.export_onnx
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import onnxruntime as ort
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import DoubleTensorType
from sklearn.linear_model import LogisticRegression

from paperclf.features import N_FEATURES
from training.data import load

ART = Path("artifacts")
TOL = 1e-5


def main() -> None:
    with open(ART / "model_sklearn.pkl", "rb") as fh:
        model = pickle.load(fh)
    onx = convert_sklearn(
        model,
        initial_types=[("input", DoubleTensorType([None, N_FEATURES]))],
        options={LogisticRegression: {"zipmap": False}},
        target_opset=17,
    )
    (ART / "model.onnx").write_bytes(onx.SerializeToString())

    _, gate, _ = load()
    sess = ort.InferenceSession(str(ART / "model.onnx"), providers=["CPUExecutionProvider"])
    X = gate.X.toarray().astype(np.float64)
    p_onnx = sess.run(None, {"input": X})[1][:, 1]
    p_skl = model.predict_proba(gate.X)[:, 1]
    diff = float(np.max(np.abs(p_onnx - p_skl))) if len(X) else 0.0
    out = {"max_abs_diff": diff, "tolerance": TOL, "n": int(len(X))}
    (ART / "onnx_check.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out))
    if diff > TOL:
        raise SystemExit(f"ONNX 확률이 원본과 다르다: {diff} > {TOL}")


if __name__ == "__main__":
    main()
