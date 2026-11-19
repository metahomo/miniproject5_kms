"""예측 로그 — 운영 장부 predictions 에 한 건씩 (ADR-009 "예측 로그는 API 가 localhost 로 직접").

- LEDGER_DSN 이 없으면 아무것도 하지 않는다(개발·시험·parity 실행).
- 원문은 저장하지 않는다: 입력의 sha256 과 글자 수만(스키마 주석과 같음).
- 기록은 백그라운드 스레드가 한다 — DB 가 느리거나 멈춰도 예측 응답은 기다리지 않는다.
  큐가 차면 버리고 센다(log_dropped). 기록 실패도 예측을 실패시키지 않는다.
"""

from __future__ import annotations

import hashlib
import logging
import os
import queue
import threading

log = logging.getLogger("paperclf.prediction_log")
QUEUE_MAX = 1000


def input_digest(title: str | None, abstract: str | None) -> tuple[str, int]:
    text = f"{title or ''}\n{abstract or ''}"
    return hashlib.sha256(text.encode("utf-8")).hexdigest(), len(text) - 1


class PredictionLog:
    def __init__(self, dsn: str | None = None) -> None:
        self.dsn = dsn if dsn is not None else os.getenv("LEDGER_DSN", "")
        self.enabled = bool(self.dsn)
        self.dropped = 0
        self.written = 0
        self._q: queue.Queue = queue.Queue(maxsize=QUEUE_MAX)
        if self.enabled:
            threading.Thread(target=self._run, name="prediction-log", daemon=True).start()

    def record(self, model_version: str, title: str | None, abstract: str | None, score: float, label: str, latency_ms: float) -> None:
        if not self.enabled or model_version == "none":
            return
        sha, chars = input_digest(title, abstract)
        try:
            self._q.put_nowait((model_version, sha, chars, score, label, latency_ms))
        except queue.Full:
            self.dropped += 1

    def _run(self) -> None:
        import psycopg

        conn = None
        while True:
            row = self._q.get()
            try:
                if conn is None or conn.closed:
                    conn = psycopg.connect(self.dsn, autocommit=True, connect_timeout=3)
                conn.execute(
                    "INSERT INTO predictions (model_version, input_sha256, input_chars, score, label, latency_ms)"
                    " VALUES (%s, %s, %s, %s, %s, %s)",
                    row,
                )
                self.written += 1
            except Exception as e:  # 장부가 멈춰도 서빙은 계속 (ADR-008: 서버가 읽는 정본은 버킷)
                self.dropped += 1
                log.warning("예측 로그 기록 실패: %s", type(e).__name__)
                try:
                    if conn is not None:
                        conn.close()
                except Exception:
                    pass
                conn = None
