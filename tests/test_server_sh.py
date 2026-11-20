"""서버 배포 스크립트(deploy/lightsail/server.sh) — docker·curl·sleep 을 가짜로 바꿔 임시 폴더에서 돌린다.

가짜 curl 은 그 폴더의 .env 를 읽어 health 를 흉내 낸다: MODEL_VERSION 을 model_version 으로 돌려주고,
TAG 나 MODEL_VERSION 이 BAD 파일에 적힌 값이면 실패한다(새 판이 안 뜨는 경우).
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "deploy/lightsail/server.sh"
BASH = shutil.which("bash")
pytestmark = pytest.mark.skipif(BASH is None, reason="bash 없음")

DOCKER = """#!/bin/sh
echo "docker $*" >> "$STUB/calls"
case "$1" in
  login) cat > "$STUB/login_stdin"; echo "$DOCKER_CONFIG" > "$STUB/docker_config" ;;
  compose) [ "$2" = ps ] && echo "api ghcr.io/x/paperclf-api:v1 Up" ;;
esac
exit 0
"""
CURL = """#!/bin/sh
echo curl >> "$STUB/calls"
TAG=$(grep '^TAG=' .env | cut -d= -f2); VER=$(grep '^MODEL_VERSION=' .env | cut -d= -f2)
BAD=$(cat "$STUB/BAD" 2>/dev/null)
if [ -n "$BAD" ] && { [ "$TAG" = "$BAD" ] || [ "$VER" = "$BAD" ]; }; then exit 22; fi
printf '{"status":"ok","model_version":"%s","app_version":"%s"}\\n' "${VER:-none}" "${TAG:-dev}"
"""


@pytest.fixture()
def srv(tmp_path):
    stub, home = tmp_path / "stub", tmp_path / "srv"
    stub.mkdir()
    home.mkdir()
    for name, body in {"docker": DOCKER, "curl": CURL, "sleep": "#!/bin/sh\nexit 0\n"}.items():
        (stub / name).write_text(body)
        (stub / name).chmod(0o755)
    text = SCRIPT.read_text(encoding="utf-8")
    assert text.count("cd /srv/paperclf\n") == 1
    (tmp_path / "server.sh").write_text(text.replace("cd /srv/paperclf\n", f"cd '{home}'\n"))

    def run(*args: str, stdin: str = "", bad: str = "") -> subprocess.CompletedProcess:
        (stub / "BAD").write_text(bad)
        (stub / "calls").write_text("")
        env = {**os.environ, "PATH": f"{stub}:{os.environ['PATH']}", "STUB": str(stub)}
        return subprocess.run([BASH, str(tmp_path / "server.sh"), *args], input=stdin, capture_output=True,
                              text=True, env=env, timeout=30, check=False)

    run.home, run.stub = home, stub
    return run


def env_of(home: Path) -> dict[str, str]:
    lines = (home / ".env").read_text().splitlines()
    keys = [line.split("=", 1)[0] for line in lines]
    assert len(keys) == len(set(keys)), lines  # setenv 는 키를 겹쳐 쓰지 않는다
    return dict(line.split("=", 1) for line in lines)


def calls(srv) -> list[str]:
    return (srv.stub / "calls").read_text().splitlines()


def put_model(home: Path, ver: str) -> None:
    d = home / "models" / ver
    d.mkdir(parents=True)
    (d / "model.onnx").write_bytes(b"x")
    (d / "model.json").write_text("{}")


def test_usage_and_input_validation(srv):
    assert srv().returncode == 2
    for args in (("model", "latest"), ("model", "m2026111-1"), ("model", "m20261119-1;rm"), ("model", "../m20261119-1"),
                 ("image", "latest", "ghcr.io/a/b"), ("image", "v1.0", "docker.io/a/b"), ("image", "v1.0", "ghcr.io/A/b"),
                 ("image", "v1.0", "ghcr.io/a/b;id")):
        r = srv(*args, stdin="tok\n")
        assert r.returncode == 1 and "형식" in r.stderr, args
        assert calls(srv) == [], args  # 형식이 틀리면 docker 를 부르지 않는다
    r = srv("model", "m20261119-3")
    assert r.returncode == 1 and "없다" in r.stderr and calls(srv) == []


def test_model_switch_ok_keeps_other_keys(srv):
    (srv.home / ".env").write_text("API_TOKEN=abc\nTAG=v1.0\nMODEL_VERSION=m20261119-1\nMODEL_DIR=/models/m20261119-1\n")
    put_model(srv.home, "m20261119-2")
    r = srv("model", "m20261119-2")
    assert r.returncode == 0, r.stderr
    assert '"model_version":"m20261119-2"' in r.stdout
    assert env_of(srv.home) == {"API_TOKEN": "abc", "TAG": "v1.0", "MODEL_VERSION": "m20261119-2", "MODEL_DIR": "/models/m20261119-2"}
    assert calls(srv).count("docker compose up -d") == 1


def test_model_health_fail_rolls_back_to_previous(srv):
    (srv.home / ".env").write_text("MODEL_VERSION=m20261119-1\nMODEL_DIR=/models/m20261119-1\n")
    put_model(srv.home, "m20261119-2")
    r = srv("model", "m20261119-2", bad="m20261119-2")
    assert r.returncode == 1 and "직전 m20261119-1 으로 돌아간다" in r.stderr
    assert env_of(srv.home) == {"MODEL_VERSION": "m20261119-1", "MODEL_DIR": "/models/m20261119-1"}
    assert calls(srv).count("docker compose up -d") == 2
    assert calls(srv).count("curl") == 31  # 새 판 30번 시도 + 복귀 판 1번에 성공


@pytest.mark.skipif(subprocess.run(["sed", "--version"], capture_output=True).returncode != 0,
                    reason="GNU sed 전용(sed -i) — 서버·CI 는 리눅스")
def test_model_health_fail_without_previous_clears_keys(srv):
    (srv.home / ".env").write_text("TAG=v1.0\n")
    put_model(srv.home, "m20261119-2")
    r = srv("model", "m20261119-2", bad="m20261119-2")
    assert r.returncode == 1 and "직전 없음" in r.stderr
    assert env_of(srv.home) == {"TAG": "v1.0"}


def test_image_ok_and_token_handling(srv):
    (srv.home / ".env").write_text("TAG=v1.0\nIMAGE=ghcr.io/metahomo/old\n")
    r = srv("image", "v1.1", "ghcr.io/metahomo/miniproject5_kms", stdin="ghp_secret\n")
    assert r.returncode == 0, r.stderr
    assert env_of(srv.home) == {"TAG": "v1.1", "IMAGE": "ghcr.io/metahomo/miniproject5_kms"}
    assert (srv.stub / "login_stdin").read_text() == "ghp_secret"
    assert "docker pull -q ghcr.io/metahomo/miniproject5_kms/paperclf-api:v1.1" in calls(srv)
    assert all("ghp_secret" not in c for c in calls(srv))  # 토큰은 인자로 넘기지 않는다
    cfg = (srv.stub / "docker_config").read_text().strip()
    assert cfg and not Path(cfg).exists()  # 임시 DOCKER_CONFIG 는 끝나면 지운다


def test_image_health_fail_rolls_back_tag(srv):
    (srv.home / ".env").write_text("TAG=v1.0\n")
    r = srv("image", "v1.1", "ghcr.io/metahomo/x", stdin="t\n", bad="v1.1")
    assert r.returncode == 1 and "직전 v1.0 로 돌아간다" in r.stderr
    assert env_of(srv.home)["TAG"] == "v1.0"
    assert calls(srv).count("docker compose up -d") == 2


def test_image_health_fail_first_deploy(srv):
    """직전 판이 없으면 되돌리지 않고 실패만 알린다."""
    r = srv("image", "v1.1", "ghcr.io/metahomo/x", stdin="t\n", bad="v1.1")
    assert r.returncode == 1 and env_of(srv.home)["TAG"] == "v1.1"
    assert calls(srv).count("docker compose up -d") == 1


def test_status_masks_secrets(srv):
    (srv.home / ".env").write_text(
        "API_TOKEN=tok123\n"
        "LEDGER_DSN=postgresql://predictor:pw-1@127.0.0.1:5432/ledger\n"
        "LEDGER_DSN2=x\n"
        "TAG=v1.0\n")
    r = srv("status")
    assert r.returncode == 0, r.stderr
    assert "tok123" not in r.stdout and "pw-1" not in r.stdout
    assert "API_TOKEN=***" in r.stdout and "LEDGER_DSN=postgresql://predictor:***@127.0.0.1:5432/ledger" in r.stdout
    assert "TAG=v1.0" in r.stdout and "api ghcr.io/x/paperclf-api:v1 Up" in r.stdout
