"""일치 확인(parity) — 원본(sklearn)과 서빙 API(ONNX 이미지 등)가 같은 확률을 내는가.

    TARGETS=onnx=http://127.0.0.1:8083 uv run --group train python -m training.check_parity

게이트 시험지는 특징으로, 고정 예문(tests/fixtures/papers.json)은 원문으로 보낸다(특징 계산까지 확인).
"""

from __future__ import annotations

import json
import os
import pickle
import sys
from pathlib import Path

import httpx
import numpy as np

from paperclf.features import vectorize
from training.data import load

ART = Path("artifacts")
TOL = float(os.getenv("PARITY_TOL", "1e-5"))
FIXTURES = Path("tests/fixtures/papers.json")


def main() -> int:
    targets = dict(t.split("=", 1) for t in os.environ["TARGETS"].split(",") if t)
    with open(ART / "model_sklearn.pkl", "rb") as fh:
        model = pickle.load(fh)
    _, gate, _ = load()
    p_ref = model.predict_proba(gate.X)[:, 1]
    feats = [[[int(i), float(v)] for i, v in zip(row.indices, row.data)] for row in gate.X]
    papers = json.loads(FIXTURES.read_text(encoding="utf-8"))
    p_ref_text = model.predict_proba(np.stack([vectorize(p["title"], p["abstract"]) for p in papers]))[:, 1]

    report, worst = {}, 0.0
    with httpx.Client(timeout=30) as c:
        for name, url in targets.items():
            got = [c.post(f"{url}/predict", json={"features": f}).json()["p_include"] for f in feats]
            got_text = [c.post(f"{url}/predict", json=p).json()["p_include"] for p in papers]
            d1 = float(np.max(np.abs(np.array(got) - p_ref))) if feats else 0.0
            d2 = float(np.max(np.abs(np.array(got_text) - p_ref_text)))
            report[name] = {"gate_max_diff": d1, "text_max_diff": d2, "n_gate": len(feats), "n_text": len(papers)}
            worst = max(worst, d1, d2)
    out = {"tolerance": TOL, "targets": report, "passed": worst <= TOL}
    ART.mkdir(exist_ok=True)
    (ART / "parity.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    if worst > TOL:
        print(f"parity 실패: {worst} > {TOL}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
