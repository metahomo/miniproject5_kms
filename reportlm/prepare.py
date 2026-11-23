"""② 데이터 준비: 교사 결과 → mlx-lm 학습 형식(chat). 게이트 시험지(고정 20%)는 학습에서 뺀다.

    DATA_MODE=group python3 reportlm/prepare.py   # 2판(기본): teacher_group.jsonl → $REPORTLM_WORK/data_group/
    DATA_MODE=single python3 reportlm/prepare.py  # 1판: teacher.jsonl → $REPORTLM_WORK/data/
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import WORK  # noqa: E402

MODE = os.environ.get("DATA_MODE", "group")
SRC = {"single": "teacher.jsonl", "group": "teacher_group.jsonl"}[MODE]
OUT = WORK / ("data" if MODE == "single" else "data_group")


def main() -> int:
    rows = [json.loads(l) for l in (WORK / "data" / SRC).open(encoding="utf-8")]
    ok = [r for r in rows if r["ok"]]
    for r in ok:
        r.setdefault("work_ids", [r.get("work_id")])
    train = [r for r in ok if r["split"] == "train"]
    gate = [r for r in ok if r["split"] == "gate"]
    k = max(1, len(train) // 10)
    valid, train = train[:k], train[k:]
    # 한계 칸이 있는 학습 묶음을 OVERSAMPLE_LIM 배로 늘린다(3판, 11-23: 2판 한계 칸 재현율 0.333 로 게이트 실패)
    over = int(os.environ.get("OVERSAMPLE_LIM", "1"))
    if over > 1:
        has_lim = [r for r in train if any(p["limitations"] for p in json.loads(r["target"])["papers"])]
        train = train + has_lim * (over - 1)
    OUT.mkdir(parents=True, exist_ok=True)
    def chat(r):
        return {"messages": [{"role": "user", "content": r["prompt"]}, {"role": "assistant", "content": r["target"]}]}
    for name, part in (("train", train), ("valid", valid)):
        with (OUT / f"{name}.jsonl").open("w", encoding="utf-8") as f:
            for r in part:
                f.write(json.dumps(chat(r), ensure_ascii=False) + "\n")
    with (OUT / "gate.jsonl").open("w", encoding="utf-8") as f:
        for r in gate:
            f.write(json.dumps({"work_ids": r["work_ids"], "prompt": r["prompt"], "target": r["target"]}, ensure_ascii=False) + "\n")
    summary = {"mode": MODE, "oversample_lim": int(os.environ.get("OVERSAMPLE_LIM", "1")), "teacher_rows": len(rows), "teacher_ok": len(ok), "train": len(train), "valid": len(valid), "gate": len(gate)}
    (OUT / "dataset.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
