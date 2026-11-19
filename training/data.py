"""라벨 스냅숏을 읽어 학습·게이트 데이터를 만든다.

- 스냅숏은 data/snapshots/*.jsonl.gz. 같은 논문이 여러 스냅숏에 있으면 이름순으로 뒤의 것이 이긴다.
- uncertain(교사도 애매)은 학습·채점에서 뺀다.
- DATA_FRACTION(기본 1.0): 학습 데이터 일부만 쓴다 — 일부러 약한 모델을 만들어 게이트를 시험할 때.
"""

from __future__ import annotations

import gzip
import json
import os
import random
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy import sparse

from paperclf.features import FEATURE_VERSION, N_FEATURES
from paperclf.labels import EXCLUDE, INCLUDE

SNAPSHOT_DIR = Path(os.getenv("SNAPSHOT_DIR", "data/snapshots"))
DATA_FRACTION = float(os.getenv("DATA_FRACTION", "1.0"))
DATA_SEED = int(os.getenv("DATA_SEED", "0"))


@dataclass
class Split:
    X: sparse.csr_matrix
    y: np.ndarray
    keys: list[str]


def load_rows(snapshot_dir: Path = SNAPSHOT_DIR) -> tuple[dict[str, dict], list[str]]:
    files = sorted(snapshot_dir.glob("*.jsonl.gz"))
    if not files:
        raise FileNotFoundError(f"스냅숏이 없다: {snapshot_dir}/*.jsonl.gz")
    rows: dict[str, dict] = {}
    for f in files:
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            meta = json.loads(fh.readline())["_meta"]
            if meta["feature_version"] != FEATURE_VERSION:
                raise ValueError(f"{f.name}: 특징 판이 다르다 {meta['feature_version']} != {FEATURE_VERSION}")
            for line in fh:
                r = json.loads(line)
                rows[r["key"]] = r
    return rows, [f.name for f in files]


def _matrix(rows: list[dict]) -> Split:
    data, ind, ptr = [], [], [0]
    for r in rows:
        for idx, cnt in r["features"]:
            ind.append(idx)
            data.append(float(cnt))
        ptr.append(len(ind))
    X = sparse.csr_matrix(
        (np.array(data, dtype=np.float32), np.array(ind, dtype=np.int32), np.array(ptr)),
        shape=(len(rows), N_FEATURES),
    )
    y = np.array([1 if r["label"] == INCLUDE else 0 for r in rows], dtype=np.int64)
    return Split(X, y, [r["key"] for r in rows])


def load(snapshot_dir: Path = SNAPSHOT_DIR) -> tuple[Split, Split, dict]:
    rows, files = load_rows(snapshot_dir)
    usable = [r for r in rows.values() if r["label"] in (INCLUDE, EXCLUDE)]
    usable.sort(key=lambda r: r["key"])
    train = [r for r in usable if r["split"] == "train"]
    gate = [r for r in usable if r["split"] == "gate"]
    if DATA_FRACTION < 1.0:
        rnd = random.Random(DATA_SEED)
        train = rnd.sample(train, max(2, int(len(train) * DATA_FRACTION)))
    info = {
        "snapshots": files,
        "n_total": len(rows),
        "n_uncertain_dropped": len(rows) - len(usable),
        "n_train": len(train),
        "n_gate": len(gate),
        "train_include": sum(r["label"] == INCLUDE for r in train),
        "gate_include": sum(r["label"] == INCLUDE for r in gate),
        "data_fraction": DATA_FRACTION,
        "data_seed": DATA_SEED,
        "feature_version": FEATURE_VERSION,
    }
    return _matrix(train), _matrix(gate), info
