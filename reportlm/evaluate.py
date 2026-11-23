"""④ 게이트: 게이트 시험지(학습에 안 쓴 고정 20%)에서 학생 · 기준선(미세 조정 전) · 운영 중인 판을 **같은 시험지로** 잰다.

    python3 reportlm/evaluate.py --run runs/<version> [--limit 80]
판정 조건(넷 다 통과해야 승격 후보):
  1. 형식 통과율 ≥ 0.95 — JSON·네 칸·근거 번호가 모두 맞다
  2. 교사와의 유사도(글자 F1) ≥ 기준선 + 0.05 — 미세 조정이 실제로 배웠다
  3. 한계 칸 재현율 ≥ 0.5 — 교사가 한계를 뽑은 논문 중 학생도 뽑은 비율 (2판, 11-23 연구 공백 결함에서 추가)
  4. 운영 중인 판(current) 대비 유사도 하락 ≤ 0.02 — 운영 판도 **같은 시험지로 다시 재서** 비교한다
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import FIELDS, WORK, hangul_ratio, parse_group  # noqa: E402

MIN_FORMAT, MARGIN, MIN_LIM_RECALL, MAX_DROP = 0.95, 0.05, 0.5, 0.02


def char_f1(a: str, b: str) -> float:
    ca, cb = Counter(a.replace(" ", "")), Counter(b.replace(" ", ""))
    common = sum((ca & cb).values())
    if not common:
        return 0.0
    p, r = common / sum(ca.values()), common / sum(cb.values())
    return 2 * p * r / (p + r)


def flat(fields: dict) -> str:
    return "\n".join(f"{f}:" + " ".join(fields.get(f, [])) for f in FIELDS)


def ids_of(r: dict) -> list[int]:
    return r.get("work_ids") or [r["work_id"]]


def run_model(model_path: str, adapter: str | None, rows: list[dict]) -> list[str]:
    from mlx_lm import generate, load
    model, tok = load(model_path, adapter_path=adapter)
    outs = []
    for r in rows:
        prompt = tok.apply_chat_template([{"role": "user", "content": r["prompt"]}], add_generation_prompt=True, tokenize=False)
        outs.append(generate(model, tok, prompt=prompt, max_tokens=1400, verbose=False))
    return outs


def score(rows: list[dict], outs: list[str]) -> dict:
    fmt = 0
    sims, han, papers = 0.0, 0.0, 0
    lim_teacher = lim_hit = 0
    for r, o in zip(rows, outs):
        ids = ids_of(r)
        s, t = parse_group(o, ids), parse_group(r["target"], ids)
        papers += len(ids)
        fmt += s is not None
        for i in ids:
            if t[i]["limitations"]:
                lim_teacher += 1
                lim_hit += bool(s and s[i]["limitations"])
            if s:
                sims += char_f1(flat(s[i]), flat(t[i]))
                han += hangul_ratio(flat(s[i]))
    good = sum(len(ids_of(r)) for r, o in zip(rows, outs) if parse_group(o, ids_of(r)))
    return {"rows": len(rows), "papers": papers, "format_ok": round(fmt / len(rows), 4), "similarity": round(sims / papers, 4),
            "hangul": round(han / max(good, 1), 4), "limitation_papers_teacher": lim_teacher,
            "limitation_recall": round(lim_hit / lim_teacher, 4) if lim_teacher else None}


def cached(name: str, rows: list[dict], fn) -> dict:
    key = hashlib.sha256("".join(r["prompt"] for r in rows).encode("utf-8")).hexdigest()[:12]
    f = WORK / "eval_cache" / f"{name}-{key}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    out = fn()
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--limit", type=int, default=80)
    a = ap.parse_args()
    run = WORK / a.run
    meta = json.loads((run / "train.json").read_text(encoding="utf-8"))
    base, data_dir = meta["base"], Path(meta.get("data_dir", WORK / "data"))
    rows = [json.loads(l) for l in (data_dir / "gate.jsonl").open(encoding="utf-8")][: a.limit]
    t0 = time.time()
    outs = run_model(base, str(run / "adapters"), rows)
    student = score(rows, outs)
    (run / "gate_outputs.jsonl").write_text("".join(json.dumps({"work_ids": ids_of(r), "out": o}, ensure_ascii=False) + "\n" for r, o in zip(rows, outs)), encoding="utf-8")
    baseline = cached("baseline", rows, lambda: score(rows, run_model(base, None, rows)))
    cur_file = WORK / "models/current.json"
    current = None
    if cur_file.exists():
        cur = json.loads(cur_file.read_text(encoding="utf-8"))
        current = {"version": cur["version"], **cached(f"current-{cur['version']}", rows, lambda: score(rows, run_model(cur["path"], None, rows)))}
    fails = []
    if student["format_ok"] < MIN_FORMAT:
        fails.append(f"format_ok {student['format_ok']} < {MIN_FORMAT}")
    if student["similarity"] < baseline["similarity"] + MARGIN:
        fails.append(f"similarity {student['similarity']} < baseline {baseline['similarity']} + {MARGIN}")
    if student["limitation_recall"] is not None and student["limitation_recall"] < MIN_LIM_RECALL:
        fails.append(f"limitation_recall {student['limitation_recall']} < {MIN_LIM_RECALL}")
    if current and student["similarity"] < current["similarity"] - MAX_DROP:
        fails.append(f"similarity {student['similarity']} < current {current['version']} {current['similarity']} - {MAX_DROP}")
    result = {"student": student, "baseline": baseline, "current": current,
              "thresholds": {"min_format": MIN_FORMAT, "margin": MARGIN, "min_limitation_recall": MIN_LIM_RECALL, "max_drop": MAX_DROP},
              "passed": not fails, "fails": fails, "seconds": round(time.time() - t0, 1)}
    (run / "gate.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
