"""5판 게이트(v3): 게이트 시험지(학습에 안 쓴 고정 20%, 3편 묶음)에서 학생·기준선(학습 전)·운영 판(current)을 같은 시험지로 잰다.

    reportlm-work/.venv/bin/python reportlm/evaluate_v3.py --run runs/<version> [--limit 60] [--data data_v3]
조건(전부 통과해야 승격 후보):
  1. 형식 통과율 ≥ 0.95  — JSON·MAP_SCHEMA·work_id 집합(빠짐·중복·낯선 번호 없음)
  2. 교사 유사도(글자 F1) ≥ 기준선 + 0.05
  3. 한계 재현율 ≥ 0.5   — 교사 record 의 own_limitations 가 있는 논문 중 학생도 own_limitations 를 채운 비율
  4. 학생 인용 검증 통과율 ≥ 0.8 — 학생이 낸 own_limitations·reported_gaps 가 초록(앞 1,500자) 부분 문자열인 비율(kms verify.quote_in_abstract)
  (참고) 운영 판 대비 유사도 하락 ≤ 0.02 는 v2 시험지에서 v3 로 바뀌어 비교표로만 싣는다.
"""
from __future__ import annotations

import argparse, hashlib, json, re, sys, time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(Path.home() / "miniproject-kms")); sys.path.insert(0, str(HERE))
from common import WORK, hangul_ratio  # noqa: E402
from kms.research.verify import STUDY_TYPES, quote_in_abstract  # noqa: E402

MIN_FORMAT, MARGIN, MIN_LIM_RECALL, MIN_QUOTE_OK = 0.95, 0.05, 0.5, 0.8
STR_ARR = ("quant_results", "own_limitations", "reported_gaps", "findings", "implications")


def char_f1(a: str, b: str) -> float:
    ca, cb = Counter(a.replace(" ", "")), Counter(b.replace(" ", ""))
    common = sum((ca & cb).values())
    if not common:
        return 0.0
    p, r = common / sum(ca.values()), common / sum(cb.values())
    return 2 * p * r / (p + r)


def _strs(v) -> bool:
    return isinstance(v, list) and all(isinstance(x, str) for x in v)


def parse(text: str, ids: list[int]) -> dict[int, dict] | None:
    """MAP_SCHEMA 형식 검사 + work_id 집합 일치. 틀리면 None."""
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    papers = data.get("papers") if isinstance(data, dict) else None
    if not isinstance(papers, list):
        return None
    out = {}
    for p in papers:
        if not isinstance(p, dict):
            return None
        wid = p.get("work_id")
        if isinstance(wid, bool) or not isinstance(wid, int) or wid not in ids or wid in out:
            return None
        if p.get("study_type") not in STUDY_TYPES or not _strs(p.get("findings")):
            return None
        for k in STR_ARR:
            if k in p and not _strs(p[k]):
                return None
        if "design" in p and not isinstance(p["design"], str):
            return None
        ss = p.get("sample_size")
        if ss is not None and (isinstance(ss, bool) or not isinstance(ss, int)):
            return None
        v = p.get("variables", {})
        if not isinstance(v, dict) or not all(_strs(x) for x in v.values()):
            return None
        out[wid] = p
    return out if set(out) == set(ids) else None


def flat(p: dict) -> str:
    v = p.get("variables") or {}
    parts = [p.get("study_type", ""), p.get("design", ""), str(p.get("sample_size"))]
    parts += [f"{k}:" + " ".join(v.get(k, [])) for k in ("independent", "mediator", "moderator", "dependent")]
    parts += [f"{k}:" + " ".join(p.get(k, [])) for k in STR_ARR]
    return "\n".join(parts)


def run_model(model_path: str, adapter: str | None, rows: list[dict]) -> list[str]:
    from mlx_lm import generate, load
    from mlx_lm.sample_utils import make_sampler  # noqa: F401
    model, tok = load(model_path, adapter_path=adapter)
    outs = []
    for r in rows:
        prompt = tok.apply_chat_template([{"role": "user", "content": r["prompt"]}], add_generation_prompt=True, tokenize=False)
        outs.append(generate(model, tok, prompt=prompt, max_tokens=1500, verbose=False))
    return outs


def score(rows: list[dict], outs: list[str]) -> dict:
    fmt = papers = 0
    sims = han = 0.0
    lim_t = lim_hit = q_total = q_ok = good = 0
    for r, o in zip(rows, outs):
        ids = r["work_ids"]
        s, t = parse(o, ids), parse(r["target"], ids)
        papers += len(ids)
        fmt += s is not None
        for i in ids:
            if t[i].get("own_limitations"):
                lim_t += 1
                lim_hit += bool(s and s[i].get("own_limitations"))
            if s:
                sims += char_f1(flat(s[i]), flat(t[i]))
                han += hangul_ratio(flat(s[i]))
                good += 1
                ab = r["abstracts"][str(i)]
                for q in (s[i].get("own_limitations") or []) + (s[i].get("reported_gaps") or []):
                    q_total += 1
                    q_ok += quote_in_abstract(q, ab)
    return {"rows": len(rows), "papers": papers, "format_ok": round(fmt / len(rows), 4), "similarity": round(sims / papers, 4),
            "hangul": round(han / max(good, 1), 4), "limitation_papers_teacher": lim_t,
            "limitation_recall": round(lim_hit / lim_t, 4) if lim_t else None,
            "quotes": q_total, "quote_ok": round(q_ok / q_total, 4) if q_total else None}


def cached(name: str, rows: list[dict], fn) -> dict:
    key = hashlib.sha256("".join(r["prompt"] + r["target"] for r in rows).encode()).hexdigest()[:12]
    f = WORK / "eval_cache" / f"v3-{name}-{key}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    out = fn()
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run")
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--data", default="data_v3")
    ap.add_argument("--only-refs", action="store_true", help="기준선·운영 판만 재서 캐시한다")
    a = ap.parse_args()
    rows = [json.loads(l) for l in (WORK / a.data / "gate.jsonl").open(encoding="utf-8")][: a.limit]
    base = str(WORK / "base/Qwen2.5-1.5B-Instruct")
    t0 = time.time()
    if a.run:
        run = WORK / a.run
        meta = json.loads((run / "train.json").read_text(encoding="utf-8"))
        base = meta["base"]
    baseline = cached("baseline-" + Path(base).name, rows, lambda: score(rows, run_model(base, None, rows)))
    cur_file = WORK / "models/current.json"
    current = None
    if cur_file.exists():
        cur = json.loads(cur_file.read_text(encoding="utf-8"))
        current = {"version": cur["version"], **cached(f"current-{cur['version']}", rows, lambda: score(rows, run_model(cur["path"], None, rows)))}
    if not a.run:
        print(json.dumps({"baseline": baseline, "current": current}, ensure_ascii=False)); return 0
    outs = run_model(base, str(run / "adapters"), rows)
    student = score(rows, outs)
    (run / "gate_outputs.jsonl").write_text("".join(json.dumps({"work_ids": r["work_ids"], "out": o}, ensure_ascii=False) + "\n" for r, o in zip(rows, outs)), encoding="utf-8")
    fails = []
    if student["format_ok"] < MIN_FORMAT:
        fails.append(f"format_ok {student['format_ok']} < {MIN_FORMAT}")
    if student["similarity"] < baseline["similarity"] + MARGIN:
        fails.append(f"similarity {student['similarity']} < baseline {baseline['similarity']} + {MARGIN}")
    if student["limitation_recall"] is not None and student["limitation_recall"] < MIN_LIM_RECALL:
        fails.append(f"limitation_recall {student['limitation_recall']} < {MIN_LIM_RECALL}")
    if student["quote_ok"] is not None and student["quote_ok"] < MIN_QUOTE_OK:
        fails.append(f"quote_ok {student['quote_ok']} < {MIN_QUOTE_OK}")
    result = {"student": student, "baseline": baseline, "current": current,
              "thresholds": {"min_format": MIN_FORMAT, "margin": MARGIN, "min_limitation_recall": MIN_LIM_RECALL, "min_quote_ok": MIN_QUOTE_OK},
              "passed": not fails, "fails": fails, "seconds": round(time.time() - t0, 1)}
    (run / "gate.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
