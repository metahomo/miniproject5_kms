"""⑦ 승격·롤백: 게이트와 parity 를 둘 다 통과한 판만 current 로 올린다. 장부(ledger.jsonl)에 남긴다.

    python3 reportlm/promote.py --run runs/<version>      # 승격
    python3 reportlm/promote.py --rollback <version>        # 이전 판으로 되돌리기(통과 기록이 있는 판만)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import WORK  # noqa: E402


def ledger(entry: dict) -> None:
    (WORK / "models").mkdir(parents=True, exist_ok=True)
    with (WORK / "models/ledger.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **entry}, ensure_ascii=False) + "\n")


def card(run: Path) -> dict:
    g = json.loads((run / "gate.json").read_text(encoding="utf-8"))
    p = json.loads((run / "parity.json").read_text(encoding="utf-8"))
    t = json.loads((run / "train.json").read_text(encoding="utf-8"))
    return {"version": run.name, "path": str(run / "fused"), "base": t["base"], "train": t, "metrics": g, "parity": p,
            "gate_passed": g["passed"], "parity_passed": p["passed"]}


def set_current(c: dict, action: str) -> None:
    cur = WORK / "models/current.json"
    prev = json.loads(cur.read_text())["version"] if cur.exists() else None
    if not (c["gate_passed"] and c["parity_passed"]):
        ledger({"action": action, "version": c["version"], "refused": True, "reason": "gate·parity 미통과"})
        raise SystemExit(f"거부: {c['version']} 는 게이트·parity 를 통과하지 않았다")
    cur.parent.mkdir(parents=True, exist_ok=True)
    cur.write_text(json.dumps({**c, "previous": prev}, ensure_ascii=False, indent=2), encoding="utf-8")
    ledger({"action": action, "version": c["version"], "previous": prev, "similarity": c["metrics"]["student"]["similarity"]})
    print(f"{action}: {prev} → {c['version']}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run")
    ap.add_argument("--rollback")
    a = ap.parse_args()
    if a.run:
        run = WORK / a.run
        c = card(run)
        (run / "model_card.json").write_text(json.dumps(c, ensure_ascii=False, indent=2), encoding="utf-8")
        set_current(c, "promote")
    elif a.rollback:
        set_current(json.loads((WORK / "runs" / a.rollback / "model_card.json").read_text(encoding="utf-8")), "rollback")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
