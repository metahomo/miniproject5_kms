"""예측 로그 — DB 없이: 꺼져 있으면 아무것도 안 하고, 켜져도 원문 대신 해시·길이만 큐에 넣는다."""
from api.prediction_log import PredictionLog, input_digest


def test_disabled_without_dsn():
    log = PredictionLog(dsn="")
    log.record("m20261119-11", "t", "a", 0.9, "include", 1.0)
    assert not log.enabled and log._q.qsize() == 0


def test_digest_no_raw_text():
    sha, chars = input_digest("Leadership", "coaching")
    assert len(sha) == 64 and chars == len("Leadership") + len("coaching")


def test_queue_holds_hash_only():
    log = PredictionLog(dsn="")
    log.enabled = True  # 스레드 없이 큐만 본다
    log.record("m20261119-11", "Leadership coaching", "abstract text", 0.74, "include", 2.5)
    row = log._q.get_nowait()
    assert row[0] == "m20261119-11" and len(row[1]) == 64
    assert "Leadership" not in repr(row)


def test_model_none_not_logged():
    log = PredictionLog(dsn="")
    log.enabled = True
    log.record("none", "t", None, 0.5, "uncertain", 1.0)
    assert log._q.qsize() == 0
