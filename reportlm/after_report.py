"""학습 모델 전/후 비교용 보고서 — KMS 연구 보고서의 1단계(논문별 네 칸 정리)만 학생 LLM 으로 바꿔 한 편을 만든다.

    ~/miniproject-kms/.venv/bin/python reportlm/after_report.py --before 261121-1746 --suffix "(후)"
- 근거 논문은 "전" 보고서와 **같은 30편**(front matter work_ids)을 그대로 쓴다 — 비교를 공정하게.
- 1단계: 승격된 학생(reportlm current, serve.sh 로 띄운 127.0.0.1:10013)이 논문 1편씩 정리한다.
- 2단계(절 작성)는 지금과 같은 교사 qwen3 4B(공용 Ollama). 지식베이스는 읽기만 한다(실행 이력도 쓰지 않음).
- 결과: 볼트 research/ 에 새 보고서 1편 + $REPORTLM_WORK/compare/<새 번호>.json(단계별 시간·형식 실패 수).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import WORK, parse_group, parse_output  # noqa: E402

KMS = Path.home() / "miniproject-kms"
sys.path.insert(0, str(KMS))

from kms.config import load_config  # noqa: E402
from kms.research.writer import Evidence, ResearchWriter, generate_and_save  # noqa: E402
from kms.search.rag import build_context  # noqa: E402
from kms.services.container import Services  # noqa: E402
from kms.storage.factory import open_store  # noqa: E402

STUDENT_URL = "http://127.0.0.1:10013/v1/chat/completions"


class StudentMapWriter(ResearchWriter):
    """1단계(summarize)만 학생 LLM, 나머지는 원래 교사."""

    def __init__(self, base: ResearchWriter, student_version: str, mode: str = "single") -> None:
        self.__dict__.update(base.__dict__)
        self.mode = mode  # single: 1편씩(1판) · group: 운영과 같은 묶음 그대로(2판)
        self.teacher_model = base.model
        self.model = f"reportlm {student_version} (1단계) + {base.model} (2단계)"
        self.stats = {"map_calls": 0, "map_format_fail": 0, "map_seconds": 0.0}

    def _raw(self, prompt, schema):
        """2단계(절 작성)는 교사 모델 이름으로 Ollama 를 부른다 — self.model 은 보고서 머리 표기용."""
        label, self.model = self.model, self.teacher_model
        try:
            return super()._raw(prompt, schema)
        finally:
            self.model = label

    def _ask(self, prompt):
        body = json.dumps({"messages": [{"role": "user", "content": prompt}], "max_tokens": 1400,
                           "temperature": 0}).encode("utf-8")
        t0 = time.time()
        req = urllib.request.Request(STUDENT_URL, data=body, headers={"content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as r:
            text = json.load(r)["choices"][0]["message"]["content"]
        self.stats["map_seconds"] += time.time() - t0
        self.stats["map_calls"] += 1
        return text

    def summarize(self, question, hits):
        if self.mode == "group":
            ids = [h.work.id for h in hits]
            parsed = parse_group(self._ask(self._map.format(question=question, context=build_context(hits))), ids)
            if parsed is None:
                self.stats["map_format_fail"] += 1
                return []
            return [{"work_id": i, **parsed[i]} for i in ids]
        papers = []
        for h in hits:
            prompt = self._map.format(question=question, context=build_context([h]))
            body = json.dumps({"messages": [{"role": "user", "content": prompt}], "max_tokens": 700,
                               "temperature": 0}).encode("utf-8")
            t0 = time.time()
            req = urllib.request.Request(STUDENT_URL, data=body, headers={"content-type": "application/json"})
            with urllib.request.urlopen(req, timeout=300) as r:
                text = json.load(r)["choices"][0]["message"]["content"]
            self.stats["map_seconds"] += time.time() - t0
            self.stats["map_calls"] += 1
            p = parse_output(text, h.work.id)
            if not (p and p.get("work_id_ok")):
                self.stats["map_format_fail"] += 1
                continue
            papers.append({"work_id": h.work.id, **{k: v for k, v in p.items() if k != "work_id_ok"}})
        return papers


def front(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    out = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", required=True)
    ap.add_argument("--topic", default="coaching-leadership")
    ap.add_argument("--suffix", default="(후)")
    a = ap.parse_args()
    config, _ = load_config(KMS / "config.yaml", KMS, create_dirs=False)
    vault = config.paths.vault
    before = vault / "topics" / a.topic / "research" / f"{a.before}.md"
    fm = front(before)
    ids = json.loads(fm["work_ids"])
    question = json.loads(fm["question"]).removesuffix("(전)").strip() + a.suffix
    yf, yt = int(fm["year_from"]), int(fm["year_to"])
    store = open_store(config)
    works = store.works_by_ids(ids)
    evidence = Evidence([works[i] for i in ids if i in works], json.loads(fm.get("search_mode", '"hybrid"')))
    cur = json.loads((WORK / "models/current.json").read_text(encoding="utf-8"))
    svc = Services(config, config_path=KMS / "config.yaml")
    mode = cur.get("train", {}).get("data_mode", "single")
    writer = StudentMapWriter(svc.research_writer(), cur["version"], mode)
    t0 = time.time()
    path = generate_and_save(store, writer, evidence, topic_id=a.topic, question=question, year_from=yf, year_to=yt,
                             config=config.research, vault=vault, run_id=f"reportlm-{cur['version']}",
                             created_by="SUPER_ADMIN", started_local=datetime.now())
    total = time.time() - t0
    stats = {**writer.stats, "map_seconds": round(writer.stats["map_seconds"], 1), "total_seconds": round(total, 1),
             "student_version": cur["version"], "map_mode": mode, "before": a.before, "after": path.stem, "question": question}
    (WORK / "compare").mkdir(parents=True, exist_ok=True)
    (WORK / "compare" / f"{path.stem}.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(path)
    print(json.dumps(stats, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
