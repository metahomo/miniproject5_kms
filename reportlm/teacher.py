"""① 데이터: KMS(읽기 전용)에서 포함 판정·초록 있는 논문을 골라 교사 LLM(qwen3 4B)으로 네 칸 정리를 만든다.

    python3 reportlm/teacher.py --n 360        # 결과: $REPORTLM_WORK/data/teacher.jsonl (이어 쓰기)
공용 Ollama 는 한 번에 한 건만 부르고, 모델을 내리지 않는다(keep_alive 10m).
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
import urllib.request

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from common import FIELDS, KMS_ROOT, WORK, build_prompt, canonical, parse_output, split_of  # noqa: E402

TEACHER = "qwen3:4b-instruct-2507-q4_K_M"
SCHEMA = {"type": "object", "properties": {"papers": {"type": "array", "items": {"type": "object", "properties": {
    "work_id": {"type": "integer"}, **{f: {"type": "array", "items": {"type": "string"}} for f in FIELDS}},
    "required": ["work_id", *FIELDS]}}}, "required": ["papers"]}


def works(n: int) -> list[dict]:
    db = sqlite3.connect(f"file:{KMS_ROOT / 'data/kms.sqlite3'}?mode=ro", uri=True)
    rows = db.execute(
        "SELECT w.id, w.title, w.year, w.abstract FROM topic_works tw JOIN works w ON w.id = tw.work_id "
        "WHERE tw.topic_id = 'coaching-leadership' AND tw.label = 'include' AND length(w.abstract) > 200"
    ).fetchall()
    items = [{"id": r[0], "title": r[1], "year": r[2], "abstract": r[3]} for r in rows]
    items.sort(key=lambda w: __import__("hashlib").blake2b(f"order{w['id']}".encode(), digest_size=8).digest())
    return items[:n]


def generate(prompt: str) -> str:
    body = json.dumps({"model": TEACHER, "prompt": prompt, "format": SCHEMA, "stream": False, "keep_alive": "10m",
                       "options": {"temperature": 0, "seed": 42, "num_ctx": 4096}}).encode("utf-8")
    req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=body, headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)["response"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=360)
    a = ap.parse_args()
    out = WORK / "data/teacher.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    done = {json.loads(l)["work_id"] for l in out.open(encoding="utf-8")} if out.exists() else set()
    todo = [w for w in works(a.n) if w["id"] not in done]
    print(f"대상 {a.n} · 이미 {len(done)} · 남음 {len(todo)}", flush=True)
    with out.open("a", encoding="utf-8") as f:
        for i, w in enumerate(todo, 1):
            t0 = time.time()
            prompt = build_prompt(w)
            raw = generate(prompt)
            parsed = parse_output(raw, w["id"])
            ok = bool(parsed and parsed.get("work_id_ok"))
            f.write(json.dumps({"work_id": w["id"], "split": split_of(w["id"]), "ok": ok, "prompt": prompt,
                                "target": canonical(w["id"], parsed) if ok else None, "raw": raw}, ensure_ascii=False) + "\n")
            f.flush()
            print(f"{i}/{len(todo)} W{w['id']} {'ok' if ok else 'BAD'} {time.time()-t0:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
