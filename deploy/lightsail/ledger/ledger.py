#!/usr/bin/env python3
"""운영 장부 기록 — 서버 러너가 돌린다 (ADR-008·009). 표준 라이브러리만, 서버의 python3(3.9)에서 돈다.

    ledger.py run <산출물 폴더> <스냅숏 폴더> <판> <실행 URL> <git sha>   학습 실행 1건 (통과·실패 모두)
    ledger.py deploy <판> promote|rollback <직전 판|-> <health_ok true|false> <실행 URL> [--at ISO시각]
    ledger.py backup                                                   pg_dump → 버킷 ledger/, 최근 14개 보관
    ledger.py status                                                   건수와 운영 중인 판

DB 는 127.0.0.1 에만 열려 있고(밖에서 접속 불가), 기록은 `docker exec paperclf-ledger psql` 로 한다.
값은 모두 psql 변수(-v)로 넘기고 SQL 안에서는 :'이름' 으로만 쓴다 — 문자열을 SQL 에 이어 붙이지 않는다.
접속 정보·버킷은 /srv/ledger/.env (권한 600).
"""
import datetime
import gzip
import hashlib
import json
import os
import pathlib
import subprocess
import sys

CONTAINER = "paperclf-ledger"
ENV_FILE = pathlib.Path(os.environ.get("LEDGER_ENV", "/srv/ledger/.env"))
KEEP_BACKUPS = 14


def load_env(path=ENV_FILE):
    env = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot_stats(paths):
    """스냅숏 파일 하나 또는 여러 개(이름순, 같은 논문은 뒤 파일이 이김 — training/data.py 와 같음).

    파일마다 첫 줄 _meta, 나머지는 한 줄에 논문 하나(key·label: include/exclude/uncertain).
    여러 파일이면 데이터셋 하나로 본다: sha256 은 파일별 sha256 을 이어 붙인 것의 sha256.
    """
    if isinstance(paths, (str, pathlib.Path)):
        paths = [paths]
    paths = sorted((pathlib.Path(p) for p in paths), key=lambda p: p.name)
    meta, labels, shas = {}, {}, []
    for path in paths:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for i, line in enumerate(f):
                row = json.loads(line)
                if "_meta" in row:
                    meta = row["_meta"]
                    continue
                labels[row.get("key") or f"{path.name}:{i}"] = row.get("label")
        shas.append(sha256_file(path))
    sha = shas[0] if len(shas) == 1 else hashlib.sha256("".join(shas).encode()).hexdigest()
    name = paths[-1].name.split(".")[0] if len(paths) == 1 else f"{paths[0].name.split('-')[0]}-x{len(paths)}"
    n = len(labels)
    inc = sum(1 for v in labels.values() if v == "include")
    exc = sum(1 for v in labels.values() if v == "exclude")
    return {"dataset_id": f"{name}-{sha[:12]}", "bucket_key": "snapshots/" + "+".join(p.name for p in paths), "sha256": sha,
            "n_rows": n, "n_include": inc, "n_exclude": exc, "label_source": {**meta, "files": [p.name for p in paths]}}


def run_record(art_dir, snap_dir, version, run_url, git_sha):
    """산출물 폴더(metrics.json 필수, model.json·model.onnx·parity.json 있으면)로 model_versions 한 행."""
    art = pathlib.Path(art_dir)
    metrics = json.loads((art / "metrics.json").read_text(encoding="utf-8"))
    card = json.loads((art / "model.json").read_text(encoding="utf-8")) if (art / "model.json").exists() else {}
    parity = json.loads((art / "parity.json").read_text(encoding="utf-8")) if (art / "parity.json").exists() else None
    snaps = (card.get("data") or metrics.get("data") or {}).get("snapshots") or sorted(p.name for p in pathlib.Path(snap_dir).glob("*.jsonl.gz"))
    if not snaps:
        raise SystemExit("스냅숏이 없다")
    ds = snapshot_stats([pathlib.Path(snap_dir) / pathlib.Path(n).name for n in snaps])
    gate = metrics.get("gate_result") or card.get("gate_result") or {}
    parity_diff = None
    if parity:
        # training/check_parity.py: targets.<이름>.gate_max_diff · text_max_diff 중 가장 큰 값
        parity_diff = max((max(t.get("gate_max_diff", 0.0), t.get("text_max_diff", 0.0)) for t in parity.get("targets", {}).values()), default=None)
    mv = {
        "version": version, "dataset_id": ds["dataset_id"], "git_sha": git_sha or card.get("git_sha", ""),
        "run_url": run_url or card.get("run_url", ""), "algorithm": "hashing-char-ngram tfidf + logistic regression (onnx)",
        "bucket_key": f"models/{version}/", "onnx_sha256": sha256_file(art / "model.onnx") if (art / "model.onnx").exists() else "",
        "metrics": {"gate": metrics.get("gate"), "train": metrics.get("train"), "baseline_f1": metrics.get("baseline_f1"),
                    "data": metrics.get("data"), "fails": gate.get("fails", [])},
        "gate_passed": bool(gate.get("passed")), "parity_max_diff": "" if parity_diff is None else repr(float(parity_diff)),
        "parity_passed": bool(parity and parity.get("passed")),
    }
    return ds, mv


SQL_RUN = """
INSERT INTO datasets (dataset_id, bucket_key, sha256, n_rows, n_include, n_exclude, label_source)
VALUES (:'dataset_id', :'ds_bucket_key', :'sha256', :'n_rows'::int, :'n_include'::int, :'n_exclude'::int, :'label_source'::jsonb)
ON CONFLICT DO NOTHING;
INSERT INTO model_versions (version, dataset_id, git_sha, run_url, algorithm, bucket_key, onnx_sha256, metrics,
                            gate_passed, parity_max_diff, parity_passed)
VALUES (:'version', (SELECT dataset_id FROM datasets WHERE sha256 = :'sha256'), NULLIF(:'git_sha', ''), NULLIF(:'run_url', ''),
        :'algorithm', :'bucket_key', NULLIF(:'onnx_sha256', ''), :'metrics'::jsonb, :'gate_passed'::boolean,
        NULLIF(:'parity_max_diff', '')::double precision, :'parity_passed'::boolean)
ON CONFLICT (version) DO NOTHING;
SELECT version, gate_passed, parity_passed FROM model_versions WHERE version = :'version';
"""

SQL_DEPLOY = """
INSERT INTO deployments (version, action, previous_version, actor, run_url, health_ok, deployed_at)
VALUES (:'version', :'action', (SELECT version FROM model_versions WHERE version = NULLIF(:'previous', '-')),
        :'actor', NULLIF(:'run_url', ''), :'health_ok'::boolean, COALESCE(NULLIF(:'at', '')::timestamptz, now()));
SELECT * FROM current_model;
"""

SQL_STATUS = """
SELECT (SELECT count(*) FROM datasets) AS datasets, (SELECT count(*) FROM model_versions) AS model_versions,
       (SELECT count(*) FROM model_versions WHERE NOT gate_passed OR NOT parity_passed) AS failed_runs,
       (SELECT count(*) FROM deployments) AS deployments;
SELECT * FROM current_model;
SELECT version, gate_passed, parity_passed, parity_max_diff, created_at FROM model_versions ORDER BY created_at DESC LIMIT 5;
"""


def psql(env, sql, variables, extra=()):
    cmd = ["docker", "exec", "-i", CONTAINER, "psql", "-X", "-v", "ON_ERROR_STOP=1", "-U", env["POSTGRES_USER"], "-d", env["POSTGRES_DB"], *extra]
    for k, v in variables.items():
        cmd += ["-v", f"{k}={v}"]
    r = subprocess.run(cmd, input=sql, text=True, capture_output=True)
    if r.returncode:
        # 값은 이미 -v 로 넘겼으니 명령 전체 대신 psql 의 오류만 보인다 (예: 트리거의 "has not passed gate and parity")
        raise SystemExit(r.stderr.strip() or f"psql 실패 {r.returncode}")
    return r.stdout


def cmd_run(argv):
    art, snap, version, run_url, git_sha = argv
    ds, mv = run_record(art, snap, version, run_url, git_sha)
    v = {**{k: ds[k] for k in ("dataset_id", "sha256", "n_rows", "n_include", "n_exclude")},
         "ds_bucket_key": ds["bucket_key"], "label_source": json.dumps(ds["label_source"], ensure_ascii=False),
         **{k: mv[k] for k in ("version", "git_sha", "run_url", "algorithm", "bucket_key", "onnx_sha256", "parity_max_diff")},
         "metrics": json.dumps(mv["metrics"], ensure_ascii=False), "gate_passed": str(mv["gate_passed"]).lower(),
         "parity_passed": str(mv["parity_passed"]).lower()}
    print(psql(load_env(), SQL_RUN, v), end="")


def cmd_deploy(argv):
    at = ""
    if "--at" in argv:
        i = argv.index("--at"); at = argv[i + 1]; argv = argv[:i] + argv[i + 2:]
    version, action, previous, health_ok, run_url = argv
    if action not in ("promote", "rollback") or health_ok not in ("true", "false"):
        raise SystemExit("사용: deploy <판> promote|rollback <직전|-> true|false <URL>")
    actor = os.environ.get("GITHUB_ACTOR", "runner")
    print(psql(load_env(), SQL_DEPLOY, {"version": version, "action": action, "previous": previous, "actor": actor,
                                        "run_url": run_url, "health_ok": health_ok, "at": at}), end="")


def cmd_backup(_argv):
    env = load_env()
    bucket, region = env["BUCKET"], env.get("AWS_REGION", "ap-southeast-2")
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dump = subprocess.run(["docker", "exec", CONTAINER, "pg_dump", "-U", env["POSTGRES_USER"], "-d", env["POSTGRES_DB"]],
                          check=True, capture_output=True).stdout
    key = f"ledger/ledger-{stamp}.sql.gz"
    subprocess.run(["aws", "s3", "cp", "-", f"s3://{bucket}/{key}", "--region", region], input=gzip.compress(dump), check=True)
    listing = subprocess.run(["aws", "s3", "ls", f"s3://{bucket}/ledger/", "--region", region], check=True, capture_output=True, text=True).stdout
    names = sorted(l.split()[-1] for l in listing.splitlines() if l.strip().endswith(".sql.gz"))
    for old in names[:-KEEP_BACKUPS]:
        subprocess.run(["aws", "s3", "rm", f"s3://{bucket}/ledger/{old}", "--region", region], check=True, capture_output=True)
    print(f"백업 {key} ({len(dump)} bytes), 보관 {min(len(names), KEEP_BACKUPS)}개")


def cmd_status(_argv):
    print(psql(load_env(), SQL_STATUS, {}), end="")


if __name__ == "__main__":
    cmds = {"run": cmd_run, "deploy": cmd_deploy, "backup": cmd_backup, "status": cmd_status}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        raise SystemExit(__doc__)
    cmds[sys.argv[1]](sys.argv[2:])
