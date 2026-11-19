"""교사 라벨 — KMS 판정기(로컬 LLM)로 KMS 논문에 적합도 라벨을 붙인다.

KMS 운영 DB 는 읽기 전용(sqlite mode=ro)으로만 연다. 판정 결과는 KMS DB 에 쓰지 않고
이 저장소 밖 작업 폴더의 JSONL 에 덧붙인다(중단 후 다시 돌리면 이어서 한다).

실행은 KMS 가상환경으로 한다(kms 패키지를 읽기 전용으로 import):
    ~/miniproject-kms/.venv/bin/python labeler/teacher_label.py \
        --kms-root ~/miniproject-kms --topic coaching-leadership --out <작업폴더>/teacher.jsonl
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kms-root", type=Path, required=True)
    ap.add_argument("--topic", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    root = args.kms_root.expanduser().resolve()
    sys.path.insert(0, str(root))
    from kms.config import load_config  # noqa: E402
    from kms.judge.local import LocalJudge  # noqa: E402
    from kms.llm.factory import open_client  # noqa: E402
    from kms.storage.base import Work  # noqa: E402
    from kms.topics import load_topics  # noqa: E402

    config, _warnings = load_config(root / "config.yaml", root, create_dirs=False)
    topic = load_topics(root / "topics.yaml").get(args.topic)
    if topic is None:
        print(f"주제 없음: {args.topic}", file=sys.stderr)
        return 2

    db = Path(config.paths.db)
    if not db.is_absolute():
        db = root / db
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    rows = con.execute(
        "SELECT w.id, w.title, w.abstract, w.year, w.language, w.source_ids_json "
        "FROM works w JOIN topic_works tw ON tw.work_id = w.id "
        "WHERE tw.topic_id = ? ORDER BY w.id",
        (args.topic,),
    ).fetchall()
    con.close()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    done: set[int] = set()
    if args.out.exists():
        for line in args.out.read_text(encoding="utf-8").splitlines():
            if line.strip():
                done.add(json.loads(line)["kms_work_id"])

    client = open_client(config.llm)
    judge = LocalJudge(
        client,
        model=config.llm.model,
        model_version=client.digest(config.llm.model),
        prompt_version=config.llm.prompt_version,
        num_ctx=config.llm.num_ctx,
    )
    todo = [r for r in rows if r[0] not in done]
    if args.limit:
        todo = todo[: args.limit]
    print(f"대상 {len(rows)}편, 완료 {len(done)}편, 이번 {len(todo)}편", flush=True)
    t0 = time.time()
    with args.out.open("a", encoding="utf-8") as fh:
        for i, (wid, title, abstract, year, lang, sids) in enumerate(todo, 1):
            work = Work(title=title, id=wid, abstract=abstract, year=year, language=lang)
            j = judge.judge(topic, work)
            rec = {
                "kms_work_id": wid,
                "source_ids": json.loads(sids or "{}"),
                "year": year,
                "title": title,
                "abstract": abstract,
                "label": str(getattr(j.label, "value", j.label)),
                "relevance": j.relevance,
                "reason": j.reason,
                "schema_ok": j.schema_ok,
                "teacher": {
                    "backend": j.backend,
                    "model": j.model,
                    "model_version": j.model_version,
                    "prompt_version": j.prompt_version,
                },
                "topic": args.topic,
                "labeled_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            if i % 25 == 0:
                rate = i / (time.time() - t0)
                print(f"{i}/{len(todo)} ({rate:.2f}편/초)", flush=True)
    client.close()
    print("완료", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
