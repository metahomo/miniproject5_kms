"""학습 모델 전/후 보고서 비교표 — 두 보고서 파일의 머리·절·인용을 숫자로 맞대 보인다(본문 문장은 옮기지 않는다).

    python3 reportlm/compare.py --before 261121-1746 --after <새 번호>   # 표를 출력하고 $REPORTLM_WORK/compare/ 에 저장
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import WORK, hangul_ratio  # noqa: E402

VAULT = Path.home() / "miniproject-kms/data/vault/topics"
SECTIONS = ("연구 동향", "주요 발견", "방법", "연구 공백", "제언")


def stats(topic: str, rid: str) -> dict:
    text = (VAULT / topic / "research" / f"{rid}.md").read_text(encoding="utf-8")
    fm = dict(l.split(":", 1) for l in re.match(r"---\n(.*?)\n---", text, re.S).group(1).splitlines() if ":" in l)
    body = text.split("\n---\n", 1)[1]
    out = {"report": rid, "model": json.loads(fm["model"].strip()), "cited_count": int(fm["cited_count"]),
           "work_count": int(fm["work_count"]), "dropped_sentences": int(fm["dropped_sentences"])}
    for name in SECTIONS:
        m = re.search(rf"^## {name}[^\n]*\n(.*?)(?=^## |\Z)", body, re.S | re.M)
        sec = (m.group(1) if m else "").strip()
        sents = re.findall(r"\.(?=\s|$)", sec)  # 문장 끝 마침표 수
        out[name] = {"sentences": len(sents), "chars": len(sec), "cites": len(set(re.findall(r"\[W(\d+)\]", sec)))}
    all_text = "\n".join(re.findall(r"^(?!#|>|\[W|- ).+$", body, re.M))
    out["hangul_ratio"] = round(hangul_ratio(all_text), 3)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", required=True)
    ap.add_argument("--after", required=True)
    ap.add_argument("--topic", default="coaching-leadership")
    a = ap.parse_args()
    b, f = stats(a.topic, a.before), stats(a.topic, a.after)
    extra = WORK / "compare" / f"{a.after}.json"
    run = json.loads(extra.read_text(encoding="utf-8")) if extra.exists() else {}
    rows = [("1단계(논문별 정리) 모델", b["model"], f["model"]),
            ("근거 논문", b["work_count"], f["work_count"]),
            ("인용한 논문 수", b["cited_count"], f["cited_count"]),
            ("버린 문장(인용 없음·허용 밖)", b["dropped_sentences"], f["dropped_sentences"]),
            ("본문 한글 비율", b["hangul_ratio"], f["hangul_ratio"])]
    for name in SECTIONS:
        rows.append((f"{name} — 문장 / 인용 논문", f"{b[name]['sentences']} / {b[name]['cites']}", f"{f[name]['sentences']} / {f[name]['cites']}"))
    if run:
        rows.append(("1단계 학생 호출 / 형식 실패", "—", f"{run['map_calls']} / {run['map_format_fail']}"))
        rows.append(("1단계 시간(초) / 전체(초)", "—", f"{run['map_seconds']} / {run['total_seconds']}"))
    md = "| 항목 | 전 (" + a.before + ") | 후 (" + a.after + ") |\n|---|---|---|\n" + "".join(f"| {r[0]} | {r[1]} | {r[2]} |\n" for r in rows)
    (WORK / "compare").mkdir(parents=True, exist_ok=True)
    (WORK / "compare" / f"{a.before}_vs_{a.after}.md").write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
