"""채점 — 포함(include) 클래스 기준 F1·정밀도·재현율과 비교 기준선."""

from __future__ import annotations

import numpy as np


def score(y: np.ndarray, p: np.ndarray, at: float = 0.5) -> dict:
    pred = (p >= at).astype(int)
    tp = int(((pred == 1) & (y == 1)).sum())
    fp = int(((pred == 1) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "f1": round(f1, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "accuracy": round(float((pred == y).mean()) if len(y) else 0.0, 4),
        "n": int(len(y)),
    }


def baseline_f1(y: np.ndarray) -> float:
    """아무것도 배우지 않고 전부 include 라고 답할 때의 F1."""
    p = float(y.mean()) if len(y) else 0.0
    return round(2 * p / (1 + p), 4) if p else 0.0
