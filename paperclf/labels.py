"""라벨·판정 규칙. 임계값은 KMS 주제 설정(relevance_threshold)과 같게 둔다."""

from __future__ import annotations

import hashlib

INCLUDE, EXCLUDE, UNCERTAIN = "include", "exclude", "uncertain"
INCLUDE_AT, EXCLUDE_AT = 0.7, 0.3  # KMS topics.yaml coaching-leadership 과 같은 값
GATE_SHARE = 5  # 열쇠 해시 % 5 == 0 → 게이트 시험지 (약 20%)


def label_for(p_include: float) -> str:
    if p_include >= INCLUDE_AT:
        return INCLUDE
    if p_include <= EXCLUDE_AT:
        return EXCLUDE
    return UNCERTAIN


def split_of(key: str) -> str:
    """논문 열쇠로 정하는 고정 분할. 새 데이터가 들어와도 기존 논문의 분할은 바뀌지 않는다."""
    h = int.from_bytes(hashlib.blake2b(key.encode("utf-8"), digest_size=8).digest(), "little")
    return "gate" if h % GATE_SHARE == 0 else "train"
