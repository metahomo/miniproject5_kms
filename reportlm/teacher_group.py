"""① 데이터 2판: 1판과 같은 논문을 **3편 묶음**(운영 KMS 의 group_size=3 과 같은 입력)으로 교사에게 다시 정리시킨다.

    python3 reportlm/teacher_group.py      # 결과: $REPORTLM_WORK/data/teacher_group.jsonl
묶음은 같은 분할(학습/게이트) 안에서만 만든다 — 게이트 논문이 학습 묶음에 섞이지 않게.
11-23 점검: 1편씩 물으면 교사도 한계 칸을 거의 채우지 않았다(30편 중 1편, 3편 묶음은 6편).
"""

from __future__ import annotations

import json
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import GROUP, KMS_ROOT, WORK, build_group_prompt, canonical_group, parse_group  # noqa: E402
from teacher import generate  # noqa: E402


def main() -> int:
    first = [json.loads(l) for l in (WORK / "data/teacher.jsonl").open(encoding="utf-8")]
    ids = {"train": [r["work_id"] for r in first if r["split"] == "train"], "gate": [r["work_id"] for r in first if r["split"] == "gate"]}
    db = sqlite3.connect(f"file:{KMS_ROOT / 'data/kms.sqlite3'}?mode=ro", uri=True)
    rows = {r[0]: {"id": r[0], "title": r[1], "year": r[2], "abstract": r[3]} for r in
            db.execute(f"SELECT id, title, year, abstract FROM works WHERE id IN ({','.join(str(i) for s in ids.values() for i in s)})")}
    out = WORK / "data/teacher_group.jsonl"
    done = {tuple(json.loads(l)["work_ids"]) for l in out.open(encoding="utf-8")} if out.exists() else set()
    groups = [(split, part[i:i + GROUP]) for split, part in ids.items() for i in range(0, len(part), GROUP)]
    todo = [(s, g) for s, g in groups if tuple(g) not in done]
    print(f"묶음 {len(groups)} · 이미 {len(done)} · 남음 {len(todo)}", flush=True)
    with out.open("a", encoding="utf-8") as f:
        for n, (split, g) in enumerate(todo, 1):
            t0 = time.time()
            prompt = build_group_prompt([rows[i] for i in g])
            raw = generate(prompt)
            parsed = parse_group(raw, g)
            f.write(json.dumps({"work_ids": g, "split": split, "ok": parsed is not None, "prompt": prompt,
                                "target": canonical_group(g, parsed) if parsed else None, "raw": raw}, ensure_ascii=False) + "\n")
            f.flush()
            print(f"{n}/{len(todo)} {split} {g} {'ok' if parsed else 'BAD'} {time.time()-t0:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
