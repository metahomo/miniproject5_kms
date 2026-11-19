"""모델 카드(model.json). 서버의 /health 가 model_version 을 여기서 읽는다.

    MODEL_VERSION=m20261119-1 uv run python -m training.model_card
"""

from __future__ import annotations

import datetime
import gzip
import json
import os
import re
from pathlib import Path

ART = Path("artifacts")
VERSION_RE = re.compile(r"^m[0-9]{8}-[0-9]+$")


def main() -> None:
    ver = os.environ["MODEL_VERSION"]
    if not VERSION_RE.match(ver):
        raise SystemExit(f"모델 판 형식이 아니다: {ver}")
    m = json.loads((ART / "metrics.json").read_text(encoding="utf-8"))
    if not m.get("gate_result", {}).get("passed"):
        raise SystemExit("게이트를 통과하지 않은 모델에는 카드를 쓰지 않는다")
    snap_dir = Path(os.getenv("SNAPSHOT_DIR", "data/snapshots"))
    teacher = None
    if m["data"]["snapshots"]:
        with gzip.open(snap_dir / m["data"]["snapshots"][-1], "rt", encoding="utf-8") as fh:
            teacher = json.loads(fh.readline())["_meta"].get("teacher")
    onnx_check = json.loads((ART / "onnx_check.json").read_text(encoding="utf-8"))
    server = os.getenv("GITHUB_SERVER_URL", "")
    repo = os.getenv("GITHUB_REPOSITORY", "")
    run = os.getenv("GITHUB_RUN_ID", "")
    card = {
        "model_version": ver,
        "task": "논문 주제 적합도(coaching-leadership) — p(include)",
        "git_sha": os.getenv("GITHUB_SHA", "local"),
        "run_url": f"{server}/{repo}/actions/runs/{run}" if run else None,
        "data": m["data"],
        "teacher": teacher,
        "params": m["params"],
        "metrics": {"gate": m["gate"], "train": m["train"], "baseline_f1": m["baseline_f1"]},
        "gate_result": m["gate_result"],
        "onnx_check": onnx_check,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    }
    (ART / "model.json").write_text(json.dumps(card, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(card, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
