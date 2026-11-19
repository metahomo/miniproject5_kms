"""교사 라벨 JSONL → 공개 가능한 라벨 스냅숏(특징만, 원문 없음).

    python -m training.snapshot <teacher.jsonl> data/snapshots/<주제>-<YYYYMMDD>.jsonl.gz

스냅숏 한 줄: key · year · label · relevance · split · features([[위치, 빈도], …]) · teacher.
제목·초록·판정 사유는 넣지 않는다(공개 저장소, 저작권). 열쇠는 공개 식별자(openalex/kci)다.
"""

from __future__ import annotations

import gzip
import json
import sys
from collections import Counter
from pathlib import Path

from paperclf.features import FEATURE_VERSION, counts, doc_text
from paperclf.labels import split_of


def key_of(source_ids: dict) -> str | None:
    for src in ("openalex", "kci", "doi"):
        if source_ids.get(src):
            return f"{src}:{source_ids[src]}"
    return None


def build(src: Path, dst: Path) -> dict:
    rows, skipped, topic = [], Counter(), None
    for line in src.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        topic = topic or r.get("topic")
        key = key_of(r.get("source_ids") or {})
        if key is None:
            skipped["no_key"] += 1
            continue
        if not r.get("schema_ok", True):
            skipped["schema_fail"] += 1
            continue
        feats = counts(doc_text(r.get("title"), r.get("abstract")))
        rows.append(
            {
                "key": key,
                "year": r.get("year"),
                "label": r["label"],
                "relevance": r.get("relevance"),
                "split": split_of(key),
                "has_abstract": bool(r.get("abstract")),
                "features": sorted([k, v] for k, v in feats.items()),
                "teacher": r.get("teacher"),
                "labeled_at": r.get("labeled_at"),
            }
        )
    dst.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(dst, "wt", encoding="utf-8") as fh:
        meta = {"_meta": {"feature_version": FEATURE_VERSION, "topic": topic, "n": len(rows)}}
        if rows:
            meta["_meta"]["teacher"] = rows[0]["teacher"]
        fh.write(json.dumps(meta, ensure_ascii=False) + "\n")
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    summary = {
        "n": len(rows),
        "labels": dict(Counter(r["label"] for r in rows)),
        "splits": dict(Counter(r["split"] for r in rows)),
        "skipped": dict(skipped),
    }
    return summary


if __name__ == "__main__":
    print(json.dumps(build(Path(sys.argv[1]), Path(sys.argv[2])), ensure_ascii=False, indent=2))
