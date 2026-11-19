"""글자 n-gram 해싱 특징 — 학습과 서빙이 같은 함수를 쓴다.

- 한·영 혼합 초록이라 단어 분리 대신 단어 안 글자 n-gram(2~4)을 쓴다(한국어 조사·어미에 강하다).
- 해시는 표준 라이브러리 blake2b 로 한다: 파이썬 버전·플랫폼·실행마다 같은 값이 나와야
  학습한 모델을 서버에서 그대로 쓸 수 있다(내장 hash() 는 실행마다 바뀐다).
- 공개 저장소에는 원문 대신 이 특징(해시 위치·빈도)만 올린다 — 원문으로 되돌릴 수 없다.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import Counter

import numpy as np

N_FEATURES = 2**15
NGRAM_MIN, NGRAM_MAX = 2, 4
FEATURE_VERSION = "char_wb-2-4-blake2b-32768-v1"

_WORD = re.compile(r"\w+", re.UNICODE)


def normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", text or "").lower()


def _bucket(gram: str) -> int:
    digest = hashlib.blake2b(gram.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "little") % N_FEATURES


def doc_text(title: str | None, abstract: str | None) -> str:
    """제목을 두 번 넣어 초록이 없는 논문도 제목 신호가 묻히지 않게 한다."""
    t = title or ""
    return f"{t} {t} {abstract or ''}"


def counts(text: str) -> dict[int, int]:
    """텍스트 → {해시 위치: 빈도}. 희소 표현(스냅숏 저장용)."""
    c: Counter[int] = Counter()
    for word in _WORD.findall(normalize(text)):
        padded = f" {word} "
        for n in range(NGRAM_MIN, NGRAM_MAX + 1):
            if len(padded) < n:
                continue
            for i in range(len(padded) - n + 1):
                c[_bucket(padded[i : i + n])] += 1
    return dict(c)


def to_dense(sparse: dict[int, int] | list[list[int]]) -> np.ndarray:
    """희소 표현 → (N_FEATURES,) float32. 스냅숏의 [[위치, 빈도], …] 도 받는다."""
    v = np.zeros(N_FEATURES, dtype=np.float32)
    items = sparse.items() if isinstance(sparse, dict) else sparse
    for idx, cnt in items:
        v[int(idx)] = float(cnt)
    return v


def vectorize(title: str | None, abstract: str | None) -> np.ndarray:
    return to_dense(counts(doc_text(title, abstract)))
