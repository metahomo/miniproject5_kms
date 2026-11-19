"""공개 API 보호 — /predict 토큰 인증과 IP 별 사용량 제한 (발표 04 "AI 사용자를 위한 설계 고려").

- API_TOKEN 이 비어 있으면 인증을 하지 않는다(개발·시험·parity 실행). 서버에서는 .env 에만 둔다.
  요청은 `Authorization: Bearer <토큰>` 으로. 비교는 hmac.compare_digest(시간 차 공격 방지).
- RATE_LIMIT_PER_MIN(기본 60, 0 이면 끔): 클라이언트 IP 하나가 1분에 부를 수 있는 /predict 횟수.
  넘으면 429 + Retry-After. IP 는 Caddy 가 붙인 X-Forwarded-For 의 마지막 값(앱 포트는 127.0.0.1 에만 열려
  Caddy 만 닿는다), 없으면 소켓 주소.
- /health · /model · /docs 는 공개 그대로.
"""

from __future__ import annotations

import hmac
import os
import threading
import time
from collections import deque

from fastapi import HTTPException, Request

WINDOW_S = 60.0


class Guard:
    def __init__(self, token: str | None = None, per_min: int | None = None) -> None:
        self.token = os.getenv("API_TOKEN", "") if token is None else token
        self.per_min = int(os.getenv("RATE_LIMIT_PER_MIN", "60")) if per_min is None else per_min
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()
        self.rejected_auth = 0
        self.rejected_rate = 0

    @staticmethod
    def client_ip(request: Request) -> str:
        xff = request.headers.get("x-forwarded-for", "")
        if xff:
            return xff.split(",")[-1].strip()
        return request.client.host if request.client else "-"

    def check(self, request: Request) -> None:
        if self.token:
            got = request.headers.get("authorization", "")
            if not got.startswith("Bearer ") or not hmac.compare_digest(got[7:].encode(), self.token.encode()):
                self.rejected_auth += 1
                raise HTTPException(status_code=401, detail="토큰이 필요하다 (Authorization: Bearer …)",
                                    headers={"WWW-Authenticate": "Bearer"})
        if self.per_min > 0:
            ip, now = self.client_ip(request), time.monotonic()
            with self._lock:
                q = self._hits.setdefault(ip, deque())
                while q and now - q[0] >= WINDOW_S:
                    q.popleft()
                if len(q) >= self.per_min:
                    self.rejected_rate += 1
                    retry = max(1, int(WINDOW_S - (now - q[0])) + 1)
                    raise HTTPException(status_code=429, detail=f"1분에 {self.per_min}번까지", headers={"Retry-After": str(retry)})
                q.append(now)
                if len(self._hits) > 10000:  # 오래된 IP 정리 — 메모리 상한
                    for k in [k for k, v in self._hits.items() if not v or now - v[-1] >= WINDOW_S]:
                        del self._hits[k]

    def status(self) -> dict:
        return {"auth": bool(self.token), "rate_limit_per_min": self.per_min,
                "rejected_auth": self.rejected_auth, "rejected_rate": self.rejected_rate}
