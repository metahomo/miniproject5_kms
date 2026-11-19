"""외부 네트워크 차단 — 루프백만 허용한다(KMS 시험 문화)."""

from __future__ import annotations

import socket

import pytest

_real_connect = socket.socket.connect


def _guard(self, address):
    host = address[0] if isinstance(address, tuple) else address
    if isinstance(host, str) and host not in ("127.0.0.1", "::1", "localhost") and not host.startswith("/"):
        raise RuntimeError(f"시험 중 외부 연결 금지: {address}")
    return _real_connect(self, address)


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", _guard)
