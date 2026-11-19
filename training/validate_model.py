"""검증 게이트 — 기준을 못 넘으면 0 이 아닌 코드로 끝나 승격을 막는다.

    uv run python -m training.validate_model

기준(ADR-005, 잠정):
  ① 게이트 시험지 F1(include) >= GATE_MIN_F1 (기본 0.80)
  ② F1 >= 기준선(전부 include) + GATE_MARGIN (기본 0.05)
  ③ 운영 모델 카드(PROD_CARD, 있을 때) F1 - GATE_MAX_DROP (기본 0.02) 이상
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ART = Path("artifacts")


def check(metrics: dict, prod: dict | None, *, min_f1: float, margin: float, max_drop: float) -> list[str]:
    f1 = metrics["gate"]["f1"]
    fails = []
    if f1 < min_f1:
        fails.append(f"F1 {f1} < 하한 {min_f1}")
    if f1 < metrics["baseline_f1"] + margin:
        fails.append(f"F1 {f1} < 기준선 {metrics['baseline_f1']} + {margin}")
    if prod is not None:
        prod_f1 = prod["metrics"]["gate"]["f1"]
        if f1 < prod_f1 - max_drop:
            fails.append(f"F1 {f1} < 운영 {prod['model_version']} {prod_f1} - {max_drop}")
    return fails


def main() -> int:
    metrics = json.loads((ART / "metrics.json").read_text(encoding="utf-8"))
    prod_path = os.getenv("PROD_CARD", "")
    prod = json.loads(Path(prod_path).read_text(encoding="utf-8")) if prod_path and Path(prod_path).is_file() else None
    th = {
        "min_f1": float(os.getenv("GATE_MIN_F1", "0.80")),
        "margin": float(os.getenv("GATE_MARGIN", "0.05")),
        "max_drop": float(os.getenv("GATE_MAX_DROP", "0.02")),
    }
    fails = check(metrics, prod, **th)
    metrics["gate_result"] = {
        "passed": not fails,
        "thresholds": th,
        "compared_to": prod["model_version"] if prod else None,
        "fails": fails,
    }
    (ART / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    if fails:
        print("게이트 실패 — 승격하지 않는다:\n  " + "\n  ".join(fails), file=sys.stderr)
        return 1
    print(f"게이트 통과: F1 {metrics['gate']['f1']} (기준선 {metrics['baseline_f1']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
