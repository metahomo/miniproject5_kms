"""운영 장부 스키마(db/init/*.sql)와 ledger.py 의 SQL — 실제 PostgreSQL 에서.

LEDGER_TEST_DSN(관리자 접속, 예: postgresql://postgres:test@127.0.0.1:5432/postgres)이 있을 때만 돈다.
CI 는 postgres 서비스 컨테이너로 준다. 시험마다 새 데이터베이스를 만들고 지운다.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest

ADMIN_DSN = os.getenv("LEDGER_TEST_DSN", "")
pytestmark = pytest.mark.skipif(not ADMIN_DSN, reason="LEDGER_TEST_DSN 없음 (CI 의 postgres 서비스에서 돈다)")
ROOT = Path(__file__).resolve().parents[1]
SHA = "a" * 64


@pytest.fixture()
def db():
    import psycopg
    from psycopg.conninfo import make_conninfo

    name = f"ledger_t_{uuid.uuid4().hex[:10]}"
    with psycopg.connect(ADMIN_DSN, autocommit=True) as admin:
        admin.execute(f'CREATE DATABASE "{name}"')
    dsn = make_conninfo(ADMIN_DSN, dbname=name)
    conn = psycopg.connect(dsn, autocommit=True)
    for f in sorted((ROOT / "db/init").glob("*.sql")):
        conn.execute(f.read_text(encoding="utf-8"))
    yield conn
    conn.close()
    with psycopg.connect(ADMIN_DSN, autocommit=True) as admin:
        admin.execute(f'DROP DATABASE "{name}" WITH (FORCE)')


def add_dataset(conn, ds="ds-1"):
    conn.execute("INSERT INTO datasets (dataset_id, bucket_key, sha256, n_rows, n_include, n_exclude) VALUES (%s, 'k', %s, 10, 3, 4)",
                 (ds, (ds.encode().hex() * 64)[:64]))


def add_model(conn, ver, gate=True, parity=True, onnx=SHA, ds="ds-1"):
    conn.execute("INSERT INTO model_versions (version, dataset_id, algorithm, bucket_key, onnx_sha256, gate_passed, parity_passed)"
                 " VALUES (%s, %s, 'lr', 'models/', %s, %s, %s)", (ver, ds, onnx, gate, parity))


def deploy(conn, ver, action="promote", prev=None, ok=True, at=None):
    conn.execute("INSERT INTO deployments (version, action, previous_version, actor, health_ok, deployed_at)"
                 " VALUES (%s, %s, %s, 't', %s, COALESCE(%s::timestamptz, now()))", (ver, action, prev, ok, at))


def test_trigger_rejects_unvalidated_deploy(db):
    import psycopg

    add_dataset(db)
    add_model(db, "m20261119-1", gate=True, parity=False)
    add_model(db, "m20261119-2", gate=False, parity=False, onnx=None)  # 게이트 실패 실행도 이력에는 남는다(v2)
    add_model(db, "m20261119-3")
    for ver in ("m20261119-1", "m20261119-2"):
        with pytest.raises(psycopg.errors.RaiseException, match="has not passed gate and parity"):
            deploy(db, ver)
    with pytest.raises(psycopg.errors.RaiseException):  # 없는 판도 트리거가 먼저 막는다
        deploy(db, "m20261119-9")
    deploy(db, "m20261119-3")
    assert db.execute("SELECT count(*) FROM deployments").fetchone()[0] == 1


def test_model_versions_constraints(db):
    import psycopg

    add_dataset(db)
    with pytest.raises(psycopg.errors.CheckViolation):  # 통과한 판에는 ONNX 해시가 있어야 한다
        add_model(db, "m20261119-1", gate=True, onnx=None)
    with pytest.raises(psycopg.errors.CheckViolation):  # 판 이름 형식
        add_model(db, "v1.0")
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        add_model(db, "m20261119-2", ds="nope")


def test_current_and_previous_model_views(db):
    add_dataset(db)
    for i in (1, 2, 3):
        add_model(db, f"m20261119-{i}")
    deploy(db, "m20261119-1", at="2026-11-19T01:00Z")
    deploy(db, "m20261119-2", prev="m20261119-1", at="2026-11-19T02:00Z")
    deploy(db, "m20261119-3", prev="m20261119-2", ok=False, at="2026-11-19T03:00Z")  # health 실패 — 운영 판 아님
    assert db.execute("SELECT version FROM current_model").fetchone()[0] == "m20261119-2"
    assert db.execute("SELECT version FROM previous_model").fetchone()[0] == "m20261119-1"
    deploy(db, "m20261119-1", action="rollback", prev="m20261119-2", at="2026-11-19T04:00Z")
    assert db.execute("SELECT version, action FROM current_model").fetchone() == ("m20261119-1", "rollback")
    assert db.execute("SELECT version FROM previous_model").fetchone()[0] == "m20261119-2"


def test_predictor_role_insert_only(db):
    import psycopg

    add_dataset(db)
    add_model(db, "m20261119-1")
    db.execute("SET ROLE predictor")
    db.execute("INSERT INTO predictions (model_version, input_sha256, input_chars, score, label) VALUES ('m20261119-1', %s, 5, 0.5, 'uncertain')", (SHA,))
    for sql in ("SELECT * FROM predictions", "SELECT * FROM deployments", "DELETE FROM predictions",
                "INSERT INTO datasets (dataset_id, bucket_key, sha256, n_rows, n_include, n_exclude) VALUES ('x','k','" + "b" * 64 + "',1,0,0)"):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            db.execute(sql)
    for score, label in ((1.5, "include"), (float("nan"), "include"), (0.5, "maybe")):
        with pytest.raises(psycopg.errors.CheckViolation):
            db.execute("INSERT INTO predictions (model_version, input_sha256, input_chars, score, label) VALUES ('m20261119-1', %s, 5, %s, %s)",
                       (SHA, score, label))
    db.execute("RESET ROLE")
    assert db.execute("SELECT count(*) FROM predictions").fetchone()[0] == 1


@pytest.mark.skipif(shutil.which("psql") is None, reason="psql 없음")
def test_ledger_script_run_and_deploy(db, tmp_path, monkeypatch):
    """ledger.py 의 SQL_RUN·SQL_DEPLOY 를 psql 변수 그대로 — docker exec 대신 psql 을 직접 부른다."""
    from test_ledger import ledger, make_snapshot

    info = db.info
    monkeypatch.setattr(ledger, "load_env", lambda: {"POSTGRES_USER": info.user, "POSTGRES_DB": info.dbname})
    real_run = subprocess.run
    pg_env = {**os.environ, "PGHOST": info.host, "PGPORT": str(info.port), "PGPASSWORD": info.password or ""}

    def fake_run(cmd, **kw):
        assert cmd[:4] == ["docker", "exec", "-i", ledger.CONTAINER]
        return real_run(cmd[4:], env=pg_env, **kw)
    monkeypatch.setattr(ledger.subprocess, "run", fake_run)

    make_snapshot(tmp_path)
    for ver, passed in (("m20261119-10", False), ("m20261119-11", True)):
        art = tmp_path / ver
        art.mkdir()
        (art / "metrics.json").write_text(json.dumps({"gate": {"f1": 0.9}, "gate_result": {"passed": passed, "fails": [] if passed else ["F1 낮음"]},
                                                      "data": {"snapshots": ["topic-20261119.jsonl.gz"]}}))
        if passed:
            (art / "model.onnx").write_bytes(b"onnx")
            (art / "parity.json").write_text(json.dumps({"targets": {"a": {"gate_max_diff": 1e-7}}, "passed": True}))
        ledger.cmd_run([str(art), str(tmp_path), ver, "https://x/run", "abc"])
    rows = db.execute("SELECT version, gate_passed, parity_passed, onnx_sha256 IS NULL, parity_max_diff FROM model_versions ORDER BY version").fetchall()
    assert rows == [("m20261119-10", False, False, True, None), ("m20261119-11", True, True, False, 1e-7)]
    assert db.execute("SELECT count(*) FROM datasets").fetchone()[0] == 1  # 같은 스냅숏은 한 번만

    with pytest.raises(SystemExit, match="has not passed gate and parity"):
        ledger.cmd_deploy(["m20261119-10", "promote", "-", "true", ""])
    ledger.cmd_deploy(["m20261119-11", "promote", "-", "true", "https://x/run", "--at", "2026-11-19T05:00:00Z"])
    assert db.execute("SELECT version, previous_version, run_url FROM deployments").fetchall() == [("m20261119-11", None, "https://x/run")]
    assert db.execute("SELECT version FROM current_model").fetchone()[0] == "m20261119-11"
    # 값에 따옴표·세미콜론이 있어도 SQL 로 해석되지 않는다(psql 변수 :'이름')
    ledger.cmd_deploy(["m20261119-11", "rollback", "x'); DROP TABLE deployments; --", "false", "u'v"])
    assert db.execute("SELECT count(*), max(run_url) FILTER (WHERE NOT health_ok) FROM deployments").fetchone() == (2, "u'v")
