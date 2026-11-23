"""6판 게이트: 한 어댑터, 두 과제를 따로 잰다. 과제 A(묶음 정리, 게이트 115묶음) + 과제 B(한계 발췌, 게이트 298편).

    reportlm-work/.venv/bin/python reportlm/evaluate_v6.py --run runs/<version> [--refs-only]
A: 형식 ≥0.95 · 유사도 ≥ 학습 전+0.05 · 인용 통과 ≥0.8 (한계 재현율은 B 로 옮겨 A 에선 참고만)
B: 한계 재현율 ≥0.5 · 한계 없는 논문 오탐률 ≤0.3 · 발췌가 초록 부분 문자열인 비율 ≥0.8
"""
import argparse, json, re, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from evaluate_v3 import WORK, cached, run_model, score  # noqa: E402
from evaluate_v3 import MARGIN, MIN_FORMAT, MIN_QUOTE_OK  # noqa: E402
sys.path.insert(0, str(Path.home() / "miniproject-kms"))
from kms.research.verify import quote_in_abstract  # noqa: E402

MIN_RECALL, MAX_FP = 0.5, 0.3


def parse_b(text: str):
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    v = d.get("own_limitations") if isinstance(d, dict) else None
    return v if isinstance(v, list) and all(isinstance(x, str) for x in v) else None


def score_b(rows, outs) -> dict:
    pos = hit = neg = fp = q = qok = fmt = 0
    for r, o in zip(rows, outs):
        s = parse_b(o)
        fmt += s is not None
        got = [x for x in (s or []) if x.strip()]
        ab = next(iter(r["abstracts"].values()))
        for x in got:
            q += 1
            qok += quote_in_abstract(x, ab)
        if r["positive"]:
            pos += 1
            hit += bool(got)
        else:
            neg += 1
            fp += bool(got)
    return {"papers": len(rows), "format_ok": round(fmt / len(rows), 4), "positives": pos, "recall": round(hit / pos, 4) if pos else None,
            "negatives": neg, "false_positive": round(fp / neg, 4) if neg else None, "quotes": q, "quote_ok": round(qok / q, 4) if q else None}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run")
    ap.add_argument("--refs-only", action="store_true")
    a = ap.parse_args()
    d = WORK / "data_v6"
    rows_a = [json.loads(l) for l in (d / "gate.jsonl").open(encoding="utf-8")]
    rows_b = [json.loads(l) for l in (d / "gate_b.jsonl").open(encoding="utf-8")]
    base = str(WORK / "base/Qwen2.5-1.5B-Instruct")
    t0 = time.time()

    def both(path, adapter, name):
        return {"A": cached(f"A-{name}", rows_a, lambda: score(rows_a, run_model(path, adapter, rows_a))),
                "B": cached(f"B-{name}", rows_b, lambda: score_b(rows_b, run_model(path, adapter, rows_b)))}

    refs = {"baseline": both(base, None, "baseline-Qwen2.5-1.5B-Instruct")}
    cur = json.loads((WORK / "models/current.json").read_text(encoding="utf-8"))
    refs["current_" + cur["version"]] = both(cur["path"], None, "current-" + cur["version"])
    if a.refs_only:
        print(json.dumps(refs, ensure_ascii=False))
        return 0
    run = WORK / a.run
    outs_a = run_model(base, str(run / "adapters"), rows_a)
    outs_b = run_model(base, str(run / "adapters"), rows_b)
    sa, sb = score(rows_a, outs_a), score_b(rows_b, outs_b)
    lines = [{"task": t, "work_ids": r["work_ids"], "out": o} for t, rr, oo in (("A", rows_a, outs_a), ("B", rows_b, outs_b)) for r, o in zip(rr, oo)]
    (run / "gate_outputs.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in lines), encoding="utf-8")
    bl = refs["baseline"]["A"]
    fails = []
    if sa["format_ok"] < MIN_FORMAT:
        fails.append(f"A format_ok {sa['format_ok']} < {MIN_FORMAT}")
    if sa["similarity"] < bl["similarity"] + MARGIN:
        fails.append(f"A similarity {sa['similarity']} < baseline {bl['similarity']} + {MARGIN}")
    if sa["quote_ok"] is not None and sa["quote_ok"] < MIN_QUOTE_OK:
        fails.append(f"A quote_ok {sa['quote_ok']} < {MIN_QUOTE_OK}")
    if sb["recall"] is None or sb["recall"] < MIN_RECALL:
        fails.append(f"B recall {sb['recall']} < {MIN_RECALL}")
    if sb["false_positive"] is not None and sb["false_positive"] > MAX_FP:
        fails.append(f"B false_positive {sb['false_positive']} > {MAX_FP}")
    if sb["quote_ok"] is not None and sb["quote_ok"] < MIN_QUOTE_OK:
        fails.append(f"B quote_ok {sb['quote_ok']} < {MIN_QUOTE_OK}")
    result = {"student": {**sa, "task_B": sb}, "baseline": refs["baseline"], "refs": refs, "A": sa, "B": sb,
              "thresholds": {"A": {"min_format": MIN_FORMAT, "margin": MARGIN, "min_quote_ok": MIN_QUOTE_OK},
                             "B": {"min_recall": MIN_RECALL, "max_false_positive": MAX_FP, "min_quote_ok": MIN_QUOTE_OK}},
              "passed": not fails, "fails": fails, "seconds": round(time.time() - t0, 1)}
    (run / "gate.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
