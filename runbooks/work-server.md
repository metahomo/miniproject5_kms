---
title: 작업용 서버 HTTPS·Tailscale
description: 내 AWS Lightsail 작업용 서버(54.252.22.31)에 sslip.io HTTPS 를 붙이고, Tailscale 로 tailnet 에 넣은 뒤 SSH(22) 방화벽을 좁히는 절차
tags:
  - runbook
  - aws
  - https
  - tailscale
requirement: R1
last_verified:
---
# 작업용 서버 HTTPS·Tailscale

요구사항: [R1 Lightsail](../requirements/R1-lightsail.md)

## 언제 쓰나

- 작업용 서버(Amazon Linux 2023 x86_64, 고정 IP `54.252.22.31`, ap-southeast-2)에서 임시 Caddyfile(`:80 → 127.0.0.1:8080`)을 HTTPS 로 바꿀 때 — 가 절
- 이 서버를 Tailscale tailnet 에 붙일 때 — 나 절
- tailnet 으로 접속이 되는 것을 확인한 뒤 Lightsail 의 22 번 포트를 좁힐 때 — 다 절

이 서버에는 delivery-eta 가 없다. 최종 서버(nlpwizard.eta.pyhub.kr, eta 와 공존)는 `caddy/Caddyfile` 을 쓰고, 이 런북은 쓰지 않는다.

## 전제조건

- [ ] Mac 에서 `ssh ec2-user@54.252.22.31` 이 된다 (아래 명령은 `S=ec2-user@54.252.22.31` 로 줄여 쓴다. 키 파일을 쓰면 `ssh -i …` 를 붙인다)
- [ ] 서버에 `/srv/caddy`(compose 프로젝트 `caddy`, `caddy:2.11.9-alpine`, `network_mode: host`)와 `/srv/paperclf` 가 있고, 앱이 `127.0.0.1:8080` 에서 돈다
- [ ] Lightsail 방화벽에 TCP 80·443 이 열려 있다 (80 은 인증서 발급 확인과 HTTPS 리디렉트에 필요)
- [ ] 나 절: Mac 에 `~/.config/paperclf/tailscale-authkey` 가 있고 권한이 600 이다 (`chmod 600 ~/.config/paperclf/tailscale-authkey`). 키는 이 파일에만 둔다 — 저장소·명령줄·채팅에 붙이지 않는다

## 절차

### 가. Caddy 를 Caddyfile.work 로 (sslip.io 자동 HTTPS)

`54-252-22-31.sslip.io` 는 이름 속 숫자를 그대로 `54.252.22.31` 로 돌려주므로 도메인 없이 Let's Encrypt 인증서를 받는다. Caddyfile 에 `admin off` 가 있어 `caddy reload` 가 안 되므로 컨테이너를 다시 시작한다.

| # | 단계 | 명령·화면 | 기대 결과 |
|---|---|---|---|
| 1 | 파일 올리기 (Mac, 저장소 루트에서) | `scp deploy/lightsail/caddy/Caddyfile.work "$S":/srv/caddy/Caddyfile.work` | 오류 없음 |
| 2 | 바꾸기 전 검사 | `ssh "$S" 'docker run --rm -v /srv/caddy/Caddyfile.work:/etc/caddy/Caddyfile:ro caddy:2.11.9-alpine caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile'` | `Valid configuration` |
| 3 | 지금 판 보관 후 바꾸기 | `ssh "$S" 'cd /srv/caddy && cp Caddyfile Caddyfile.bak && cp Caddyfile.work Caddyfile && docker compose restart caddy'` | `caddy` 재시작 |
| 4 | 인증서 발급 로그 | `ssh "$S" 'cd /srv/caddy && docker compose logs --since 2m caddy \| grep -iE "certificate obtained\|error"'` | `certificate obtained successfully` |

`cp` 로 덮어쓰는 것은 compose 가 파일 하나를 bind mount 하기 때문이다 — `mv` 로 바꾸면 컨테이너가 옛 파일을 계속 볼 수 있다.

### 나. Tailscale 로 tailnet 에 붙이기

스크립트와 키가 둘 다 stdin 을 쓰지 않게, 스크립트는 먼저 `scp` 로 올리고 stdin 에는 키만 넣는다. 스크립트는 키를 `mktemp`(0600) 파일에 잠깐 두고 `tailscale up --auth-key=file:<경로>` 로 넘긴 뒤 끝날 때 지운다(키가 `ps` 에 보이지 않게). `--ssh`(Tailscale SSH)는 켜지 않는다.

| # | 단계 | 명령·화면 | 기대 결과 |
|---|---|---|---|
| 1 | 스크립트 올리기 | `scp deploy/lightsail/tailscale.sh "$S":~/tailscale.sh` | 오류 없음 |
| 2 | 설치·접속 (키는 stdin 으로만) | `ssh "$S" 'sudo bash ~/tailscale.sh' < ~/.config/paperclf/tailscale-authkey` | 마지막 줄에 `100.x.y.z` |
| 3 | 관리 콘솔 확인 | Tailscale 관리 콘솔 → Machines | `paperclf` 가 Connected |
| 4 | 키 만료 끄기 (선택) | Machines → `paperclf` → ⋯ → Disable key expiry | 서버가 주기적으로 로그아웃되지 않는다 |

다시 돌려도 된다 — 이미 붙어 있으면 `tailscale up` 을 건너뛰고(받은 키는 쓰지 않고 지운다) IP 만 출력한다.

### 다. Lightsail 22 번 포트 좁히기 (tailnet 접속 확인 뒤에만)

tailnet 트래픽은 `tailscale0` 으로 들어오므로 Lightsail 방화벽 규칙과 상관없이 `ssh ec2-user@<100.x IP>` 가 된다. 그러니 **tailnet 쪽 SSH 가 되는 것을 먼저 확인한 뒤** 22 를 닫는다.

| # | 단계 | 명령·화면 | 기대 결과 |
|---|---|---|---|
| 1 | tailnet 으로 SSH 시험 (tailnet 에 붙은 기기에서) | `ssh ec2-user@<tailscale ip -4 값> true` | 오류 없음 |
| 2 | 22 규칙 좁히기 | Lightsail 콘솔 → 인스턴스 → Networking → IPv4 Firewall → SSH 규칙 편집 → "Restrict to IP address" 에서 Lightsail browser SSH 만 남긴다 | 규칙에 HTTP 80·HTTPS 443 은 그대로, SSH 는 브라우저 SSH 만 |
| 3 | 밖에서 막혔는지 | `ssh -o ConnectTimeout=5 ec2-user@54.252.22.31 true` (tailnet 밖 기기) | 시간 초과 |

- 브라우저 SSH 는 비상구로 남긴다 — tailnet 이 끊겨도 콘솔에서 들어가 되돌릴 수 있다.
- CLI 로 할 때 `aws lightsail put-instance-public-ports` 는 **규칙 전체를 바꿔 쓴다** — 80·443 을 빠뜨리면 HTTPS 가 끊긴다. 콘솔 편집을 권한다.
- self-hosted 러너(paperclf)는 GitHub 로 나가는 연결만 쓰므로 22 를 닫아도 배포·승격·되돌리기는 그대로 돈다.

## 확인

| 무엇 | 명령 | 기대 |
|---|---|---|
| HTTPS | `curl -fsS https://54-252-22-31.sslip.io/health` | JSON 응답(`"status":"ok"`) |
| HTTP → HTTPS | `curl -sI http://54-252-22-31.sslip.io/health \| head -1` | `308 Permanent Redirect` |
| 앱 직접(배포 확인 경로) | `ssh "$S" 'bash /srv/paperclf/server.sh status'` | health JSON |
| tailnet | `ssh "$S" 'tailscale ip -4; tailscale status \| head -3'` | `100.x` 주소, `paperclf` |

IP 로 직접 오는 평문 HTTP(`http://54.252.22.31/`)는 응답하지 않는 것이 정상이다 — Caddyfile.work 에 `:80` 블록을 일부러 두지 않았다(파일 주석 참고).

## 실패 시

- 인증서 발급 실패(로그에 `challenge failed`·`timeout`): Lightsail 방화벽 80·443, `dig +short 54-252-22-31.sslip.io` 가 `54.252.22.31` 인지 본다. 여러 번 실패하면 Let's Encrypt 발급 한도에 걸릴 수 있으니 반복 재시작하지 말고 원인부터 고친다. 그동안은 아래 되돌리기로 임시 Caddyfile 로 돌린다.
- `tailscale.sh` 가 "인증 키(tskey-…)가 없다": stdin 리디렉트(`< ~/.config/paperclf/tailscale-authkey`)를 빠뜨렸거나 파일이 비었다.
- `tailscale up` 이 키를 거절: 키가 만료·사용됨(1회용 키). 관리 콘솔에서 새 키를 만들어 Mac 의 키 파일만 바꾸고 2단계를 다시 돌린다.
- 22 를 좁힌 뒤 접속이 안 됨: Lightsail 콘솔의 브라우저 SSH 로 들어가 `sudo systemctl status tailscaled` 를 보거나, 방화벽 SSH 규칙을 Any IPv4 로 되돌린다.

## 되돌리기

| 무엇 | 명령·화면 |
|---|---|
| Caddy | `ssh "$S" 'cd /srv/caddy && cp Caddyfile.bak Caddyfile && docker compose restart caddy'` |
| Tailscale | `ssh "$S" 'sudo tailscale logout; sudo systemctl disable --now tailscaled; sudo dnf remove -y tailscale; sudo rm -f /etc/yum.repos.d/tailscale.repo'` 후 관리 콘솔에서 `paperclf` 삭제 |
| 22 번 포트 | Lightsail 콘솔 → Networking → SSH 규칙을 Any IPv4 로 |

## 미결

- Mac 쪽도 tailnet 에 있어야 다 절을 할 수 있다. 공용 Mac(Studio-C)은 관리자 권한이 없어 Tailscale 앱·시스템 확장을 못 깔 수 있다 — 대안(사용자 공간 `tailscaled --tun=userspace-networking` + `ssh -o ProxyCommand='tailscale nc %h %p'`, 또는 개인 기기에서만 접속)은 미검증.
- 인증 키 종류(1회용·재사용, 태그 `tag:` 부여 여부)와 키 만료 끄기는 연구자가 정한다.
- `tailscale up` 기본값은 tailnet DNS 를 받는다(`--accept-dns=true`). 서버 DNS 가 바뀌어 GHCR·S3 접속에 영향이 있는지는 미확인 — 문제가 되면 `--accept-dns=false` 를 검토한다.

## 장부 DB (ADR-008·009, 2026-11-19 구성)

| # | 단계 | 명령 | 기대 |
|---|---|---|---|
| 1 | 파일 올리기 | `scp deploy/lightsail/ledger/{compose.yml,ledger.py} "$S":/srv/ledger/` · `scp db/init/*.sql "$S":/srv/ledger/init/` | 오류 없음 |
| 2 | 접속 정보(서버에서만, 600) | `/srv/ledger/.env`: `POSTGRES_DB`·`POSTGRES_USER`·`POSTGRES_PASSWORD`(서버에서 `openssl rand -hex 24`)·`BUCKET`·`AWS_REGION` | 저장소·채팅에 비밀번호 없음 |
| 3 | 띄우기 | `ssh "$S" 'cd /srv/ledger && docker compose up -d'` | `paperclf-ledger` healthy, `127.0.0.1:5433` 에만 |
| 4 | 매일 백업 | `paperclf-ledger-backup.{service,timer}` 를 `/etc/systemd/system/` 에 두고 `systemctl enable --now paperclf-ledger-backup.timer` | 매일 03:17 UTC → 버킷 `ledger/`, 최근 14개 |
| 5 | 확인 | `ssh "$S" 'python3 /srv/ledger/ledger.py status'` | 건수·운영 중인 판 |

기록은 워크플로가 한다: `model.yml` promote(실행·배포·백업), record-failure(게이트·parity 에서 멈춘 실행), `rollback.yml`(되돌리기·백업). 미통과 판의 배포 기록은 트리거가 거부한다(`ERROR: model … has not passed gate and parity`).

복구 (빈 볼륨에서, 2026-11-19 훈련으로 확인):

1. 버킷에서 덤프: `aws s3 cp s3://paperclf-models-apse2/ledger/ledger-<시각>.sql.gz /tmp/ --region ap-southeast-2`
2. API 계정을 먼저 만든다(없으면 GRANT 3줄이 `role "predictor" does not exist` 로 실패): `docker exec -i paperclf-ledger psql -U ledger -d ledger -c 'CREATE ROLE predictor LOGIN'`
3. 복원: `gunzip -c /tmp/ledger-<시각>.sql.gz | docker exec -i paperclf-ledger psql -U ledger -d ledger`
4. API 계정 비밀번호를 `/srv/paperclf/.env` 의 `LEDGER_DSN` 과 같게: `ALTER ROLE predictor PASSWORD '…'` (값은 채팅·저장소에 쓰지 않는다)
5. 확인: `python3 /srv/ledger/ledger.py status` 건수가 백업 시점과 같다

훈련 결과(2026-11-19 14:06 UTC 덤프 → 임시 컨테이너): datasets 1 · model_versions 5 · deployments 5 · predictions 64 · 운영 판 m20261119-11 이 운영 DB 와 같았고, 복원한 DB 에서도 미통과 판 배포 기록을 트리거가 거부했다.
