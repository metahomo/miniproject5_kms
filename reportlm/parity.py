"""⑥ parity: 배포할 합친 모델(fused)이 학습 직후(기본 + 어댑터)와 같은 판단을 하는지 본다.

    python3 reportlm/parity.py --run runs/<version> [--limit 20]

LLM 은 한 토큰만 달라도 그 뒤 문장이 갈라지므로, 생성 문자열 일치가 아니라
같은 입력 + 같은 정답(교사 출력)을 넣었을 때 정답 자리마다 두 모델의
  - 1순위 토큰 일치율 ≥ 0.99
  - 정답 토큰 확률 차이의 평균 ≤ 0.01
를 본다(paperclf 의 "확률 차이 ≤ 1e-5" 에 해당하는 검사). 어휘 전체의 최대 확률 차이는 기록만 한다 —
어댑터를 bf16 가중치에 합치면 반올림으로 드문 자리에서 0.05 안팎까지 차이가 나고(11-23 실측 0.0514),
그 때문에 탐욕 생성 문자열은 수십 토큰 뒤 갈라질 수 있다(실측: 2편 중 0편 일치). 그래서 문자열 일치는 판정에 쓰지 않는다.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import WORK  # noqa: E402

MIN_TOP1, MAX_MEAN_TARGET_DIFF = 0.99, 0.01


def positions(model_path: str, adapter: str | None, rows: list[dict]):
    import mlx.core as mx
    from mlx_lm import load
    model, tok = load(model_path, adapter_path=adapter)
    out = []
    for r in rows:
        prompt = tok.apply_chat_template([{"role": "user", "content": r["prompt"]}], add_generation_prompt=True, tokenize=False)
        p_ids = tok.encode(prompt)
        t_ids = tok.encode(r["target"], add_special_tokens=False)
        ids = mx.array(p_ids + t_ids)[None]
        logits = model(ids)[0, len(p_ids) - 1: -1].astype(mx.float32)
        probs = mx.softmax(logits, axis=-1)
        tgt = probs[mx.arange(len(t_ids)), mx.array(t_ids)]
        out.append((mx.argmax(probs, axis=-1), probs, tgt))
        mx.eval(*out[-1])
    return out


def main() -> int:
    import mlx.core as mx
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--limit", type=int, default=20)
    a = ap.parse_args()
    run = WORK / a.run
    meta = json.loads((run / "train.json").read_text(encoding="utf-8"))
    base, data_dir = meta["base"], Path(meta.get("data_dir", WORK / "data"))
    rows = [json.loads(l) for l in (data_dir / "gate.jsonl").open(encoding="utf-8")][: a.limit]
    pa = positions(base, str(run / "adapters"), rows)
    pf = positions(str(run / "fused"), None, rows)
    agree = total = 0
    max_diff = tgt_sum = 0.0
    for (aa, ap_, at), (fa, fp, ft) in zip(pa, pf):
        agree += int(mx.sum(aa == fa).item())
        total += aa.shape[0]
        max_diff = max(max_diff, float(mx.max(mx.abs(ap_ - fp)).item()))
        tgt_sum += float(mx.sum(mx.abs(at - ft)).item())
    top1 = agree / total
    mean_tgt = tgt_sum / total
    result = {"n": len(rows), "tokens": total, "top1_agreement": round(top1, 5), "mean_target_prob_diff": round(mean_tgt, 6),
              "max_prob_diff_info": round(max_diff, 5),
              "thresholds": {"min_top1": MIN_TOP1, "max_mean_target_prob_diff": MAX_MEAN_TARGET_DIFF},
              "passed": top1 >= MIN_TOP1 and mean_tgt <= MAX_MEAN_TARGET_DIFF}
    (run / "parity.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
