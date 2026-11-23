"""reportlm 공통 — 보고서 1단계(논문별 네 칸 정리) 프롬프트·스키마·분할·검사.

교사(qwen3 4B, KMS 프롬프트 research_map_v2)와 학생(미세 조정한 작은 LLM)이 같은 입력 문장을 쓰도록
프롬프트 만들기를 이 한 곳에 둔다. 데이터·모델 산출물은 공개 저장소 밖(REPORTLM_WORK, 기본 ~/reportlm-work)에 둔다
— 학습 데이터에 초록 원문이 들어가기 때문이다(공개 snapshot 원칙, ADR-005).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

KMS_ROOT = Path(os.environ.get("KMS_ROOT", Path.home() / "miniproject-kms"))
WORK = Path(os.environ.get("REPORTLM_WORK", Path.home() / "reportlm-work"))
PROMPT_FILE = KMS_ROOT / "kms/llm/prompts/research_map_v2.md"
QUESTION = "관리자 코칭이 직원 성과와 태도에 미치는 효과는 무엇인가?"
FIELDS = ("findings", "methods", "limitations", "implications")
MAX_ABSTRACT = 1500
GATE_SHARE = 5  # paperclf 와 같은 고정 분할: 열쇠 해시 % 5 == 0 → 게이트 시험지(약 20%)


def split_of(work_id: int) -> str:
    h = int.from_bytes(hashlib.blake2b(f"W{work_id}".encode("utf-8"), digest_size=8).digest(), "little")
    return "gate" if h % GATE_SHARE == 0 else "train"


def build_prompt(work: dict, question: str = QUESTION) -> str:
    template = PROMPT_FILE.read_text(encoding="utf-8")
    abstract = (work.get("abstract") or "(초록 없음)")[:MAX_ABSTRACT]
    context = f"[W{work['id']}] {work['title']} ({work.get('year') or '연도 미상'})\n{abstract}"
    return template.format(question=question, context=context)


def parse_output(text: str, work_id: int) -> dict | None:
    """모델 출력 → 정규화한 한 논문 칸. 형식이 틀리면 None."""
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    papers = data.get("papers") if isinstance(data, dict) else None
    if not isinstance(papers, list) or len(papers) != 1 or not isinstance(papers[0], dict):
        return None
    p = papers[0]
    if p.get("work_id") != work_id:
        return {"work_id_ok": False, **{f: p.get(f) or [] for f in FIELDS}}
    out = {"work_id_ok": True}
    for f in FIELDS:
        v = p.get(f, [])
        if not isinstance(v, list) or not all(isinstance(s, str) for s in v):
            return None
        out[f] = [s.strip() for s in v if s.strip()][:2]
    return out


def canonical(work_id: int, fields: dict) -> str:
    """학습 정답 문자열 — 교사 출력을 같은 모양으로 다시 쓴다."""
    return json.dumps({"papers": [{"work_id": work_id, **{f: fields.get(f, []) for f in FIELDS}}]}, ensure_ascii=False)


def hangul_ratio(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    return sum("가" <= c <= "힣" for c in letters) / len(letters) if letters else 1.0


# ---------------------------------------------------------------- 2판: 3편 묶음 (운영 KMS 의 group_size=3 과 같은 입력)
GROUP = 3


def build_group_prompt(works: list[dict], question: str = QUESTION) -> str:
    template = PROMPT_FILE.read_text(encoding="utf-8")
    blocks = [f"[W{w['id']}] {w['title']} ({w.get('year') or '연도 미상'})\n{(w.get('abstract') or '(초록 없음)')[:MAX_ABSTRACT]}" for w in works]
    return template.format(question=question, context="\n\n".join(blocks))


def parse_group(text: str, ids: list[int]) -> dict[int, dict] | None:
    """묶음 출력 → {work_id: 네 칸}. 형식이 틀리거나 근거에 없는 번호·빠진 번호가 있으면 None."""
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
    out: dict[int, dict] = {}
    for p in papers:
        if not isinstance(p, dict) or p.get("work_id") not in ids or p["work_id"] in out:
            return None
        fields = {}
        for f in FIELDS:
            v = p.get(f, [])
            if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
                return None
            fields[f] = [x.strip() for x in v if x.strip()][:2]
        out[p["work_id"]] = fields
    return out if set(out) == set(ids) else None


def canonical_group(ids: list[int], parsed: dict[int, dict]) -> str:
    return json.dumps({"papers": [{"work_id": i, **{f: parsed[i].get(f, []) for f in FIELDS}} for i in ids]}, ensure_ascii=False)
