---
title: 최종 결과물 서버 (nlpwizard.eta.pyhub.kr)
description: 최종 서버 13.237.237.56 에 eta 와 함께 paperclf 를 올리는 절차 — 연구자 선행 작업·점검·준비·배포·확인·되돌리기, 선택: KMS 웹 게시
tags:
  - runbook
requirement: R1
---
# 최종 결과물 서버 (nlpwizard.eta.pyhub.kr)

요구사항: [R1](../requirements/R1-lightsail.md) · [R5](../requirements/R5-rollback.md) · 결정: [ADR-003](../decisions/ADR-003-domain-server.md)(도메인), [ADR-008](../decisions/ADR-008-ledger-db-ops.md)·[ADR-009](../decisions/ADR-009-ledger-writer.md)(장부), PR #21(eta 와 Caddy 공존)

## 언제 쓰나

최종 발표용 서버(Lightsail, `13.237.237.56`, 강의 앱 delivery-eta 가 이미 돌고 있다)에 paperclf 를 함께 올릴 때. 작업용 서버(`54.252.22.31`)는 그대로 두고 **두 서버에 같이** 배포한다.

이 서버는 작업용과 다른 AWS 계정에 있다(소유 계정 확인 중 — 연구자 nlpwizard 계정 프로젝트 591255906991 에는 없음). 그래서 작업용 서버의 모델 버킷에 키 없이 붙을 수 없고, 모델은 **같은 Actions 실행의 산출물**에서 직접 받는다.

## 어떻게 도나 (한눈에)

| 워크플로 | 작업용 서버 잡 (이름표 `lightsail,paperclf`) | 최종 서버 잡 (이름표 `final`) | 켜는 변수 |
|---|---|---|---|
| `ci.yml` (태그 `v*`) | `deploy` | `deploy-final` | `DEPLOY_ENABLED` / `FINAL_ENABLED` |
| `model.yml` | `promote` (버킷 → 서버 → 장부) | `promote-final` (실행 산출물 → 게이트·parity 재검사 → 서버) | 같음 |
| `rollback.yml` | `rollback` | `rollback-final` (서버에 남은 통과 판으로만) | 같음 |

- `FINAL_ENABLED` 가 `true` 가 아니면 `*-final` 잡은 **건너뛴다**(skipped). 저장소 변수가 없어도 같다.
- `*-final` 잡은 `runs-on: [self-hosted, final]` — 이름표 `final` 이 있는 러너(`paperclf-final`)만 받는다. 작업용 서버 러너(`paperclf`)에는 `final` 이 없어 받지 않는다. 거꾸로 `paperclf-final` 에는 `lightsail`·`paperclf` 가 없어 작업용 잡을 받지 않는다.
- `promote-final` 은 `train`(게이트)·`parity` 가 **성공**한 실행에서만 돈다. 작업용 `promote` 가 실패하면 막히고, 꺼져 있으면(`DEPLOY_ENABLED` 아님 — 작업용 서버를 정리한 뒤) 혼자 돈다. 돌 때 산출물의 `metrics.json`(게이트)·`parity.json` 을 다시 열어 둘 다 통과인지 본다 — 장부 트리거(`has not passed gate and parity`)와 같은 조건.
- 이 서버에는 기본으로 장부 DB 가 없다. 대신 통과 판 폴더에 `validated.json` 을 남기고 `rollback-final` 이 그것을 본다. `/srv/ledger/.env` 가 있으면(아래 선택 절) 작업용과 똑같이 장부에 기록하고 트리거가 거부한다.
- 새 판·되돌릴 판 모두 `server.sh model` 이 띄운 뒤 `/health` 의 `model_version` 이 그 판인지 30초 동안 확인하고, 아니면 **직전 판으로 스스로 되돌린다**(작업용과 같은 스크립트).

## 0. 연구자가 먼저 할 일 — 사령관 공개키 등록 (Lightsail 브라우저 SSH)

이것이 끝나야 Mac(사령관)에서 서버에 들어갈 수 있다. 한 줄에 한 동작:

1. Mac 에서 공개키 한 줄을 복사한다: `cat ~/.ssh/id_ed25519_paperclf.pub` (`ssh-ed25519 … commander@studio-c-paperclf` 한 줄, **`.pub` 만** — 확장자 없는 파일은 비밀키라 절대 붙이지 않는다)
2. 이 서버가 있는 계정으로 Lightsail 콘솔에 로그인한다
3. 인스턴스(`13.237.237.56`) → **Connect using SSH** (브라우저 터미널이 열린다)
4. 터미널에 `whoami` → 사용자 이름을 적어 둔다(이 문서는 `ec2-user` 로 쓴다)
5. `mkdir -p ~/.ssh && chmod 700 ~/.ssh`
6. `echo '<1에서 복사한 한 줄>' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys`
7. Mac 에서 확인: `ssh -i ~/.ssh/id_ed25519_paperclf ec2-user@13.237.237.56 true` → 오류 없이 끝나면 성공

사용자 이름이 `ec2-user` 가 아니면 `bootstrap.sh` 의 `ec2-user`(폴더 소유자·러너 서비스 사용자) 두 곳을 바꾼 뒤 돌린다.

## 전제조건

- [ ] 0절 완료 (Mac 에서 `ssh` 가 된다). 아래 명령은 `S=ec2-user@13.237.237.56` 로 줄여 쓴다(키 파일은 `~/.ssh/config` 에 두거나 `ssh -i …` 를 붙인다)
- [ ] 서버 관리자 승인: eta 를 `127.0.0.1:8090` 으로 옮기고 Caddy 가 80·443 을 맡는다(IP 로 오는 요청은 그대로 eta)
- [ ] DNS `nlpwizard.eta.pyhub.kr` → `13.237.237.56` (2026-11-20 확인: `dig +short nlpwizard.eta.pyhub.kr`), Lightsail 방화벽 TCP 80·443 열림
- [ ] PR #45 가 `main` 에 병합됨 — `bootstrap.sh` 는 `main` 의 파일을 받는다

## 절차

| # | 단계 | 명령·화면 | 기대 결과 |
|---|---|---|---|
| 1 | 점검(읽기만) | `ssh "$S" 'uname -m; docker compose version; docker ps; ls /srv; free -m; df -h /'` | `x86_64`, Compose ≥ 2.24.4, **sudo 없이** `docker ps` 가 된다, `/srv/eta` 와 eta 컨테이너 |
| 2 | 러너 등록 토큰 | PC: `gh api -X POST repos/metahomo/miniproject5_kms/actions/runners/registration-token -q .token` | 토큰 한 줄(1시간 유효). 채팅·파일에 붙이지 않는다 |
| 3 | 준비 스크립트 받기 | `ssh "$S" 'curl -fsSL https://raw.githubusercontent.com/metahomo/miniproject5_kms/main/deploy/lightsail/bootstrap.sh -o bootstrap.sh'` | 오류 없음 |
| 4 | 준비 스크립트 돌리기 | `ssh -t "$S" 'bash bootstrap.sh final'` → 토큰을 물으면 붙여 넣는다(화면에 안 보임) | ① 폴더·`.env`(600, `API_TOKEN` 생성) ② eta → 8090 ③ Caddy ④ 러너 `paperclf-final`(이름표 `final`) |
| 5 | 러너 확인 | GitHub → Settings → Actions → Runners | `paperclf-final` Idle, 이름표 `self-hosted, Linux, X64, final` |
| 6 | 최종 배포 켜기 | PC: `gh variable set FINAL_ENABLED --body true` | `*-final` 잡이 이 서버로 |
| 7 | 코드 배포 | 지금 태그의 ci 실행 다시 돌리기(`gh run rerun <id>`) 또는 새 태그 | `deploy-final` 성공 (모델 전이라 `/health` 는 `no_model`) |
| 8 | 모델 | `gh workflow run model.yml --ref main` | `promote` 다음 `promote-final` 성공 |

- `bootstrap.sh` 인자는 꼭 `final` 이다. `work` 는 작업용 서버를 새로 만들 때만 — 바꿔 쓰면 다른 서버의 잡을 받는다.
- `bootstrap.sh` 는 여러 번 돌려도 된다: 이미 있는 `API_TOKEN`·네트워크·등록된 러너는 건너뛰고, Caddyfile 은 바뀐 때만 덮어쓴다(옛 파일은 `Caddyfile.bak`).
- `API_TOKEN` 값은 화면에 나오지 않는다. 필요하면 서버에서만 본다: `grep ^API_TOKEN= /srv/paperclf/.env` — 채팅·저장소에 쓰지 않는다.
- `server.sh status` 는 `API_TOKEN`·`LEDGER_DSN` 비밀번호를 `***` 로 가린다.

## 확인

| 무엇 | 명령 | 기대 |
|---|---|---|
| HTTPS | `curl -fsS https://nlpwizard.eta.pyhub.kr/health` | `"status":"ok"`, 작업용 서버와 같은 `app_version`·`model_version` |
| HTTP → HTTPS | `curl -sI http://nlpwizard.eta.pyhub.kr/health \| head -1` | `308 Permanent Redirect` |
| 보호 | `curl -s -o /dev/null -w '%{http_code}\n' -X POST https://nlpwizard.eta.pyhub.kr/predict -H 'content-type: application/json' -d '{"title":"x"}'` | `401` |
| MCP | `curl -fsS -X POST https://nlpwizard.eta.pyhub.kr/mcp -H 'content-type: application/json' -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'` | `tools` 목록 JSON |
| 보안 헤더 | `curl -sI https://nlpwizard.eta.pyhub.kr/health \| grep -iE 'strict-transport\|nosniff\|^server'` | HSTS·nosniff 있음, `Server` 없음 |
| eta | `curl -fsS http://13.237.237.56/health` | eta 응답(바뀌지 않음) |
| 판·권한 | `ssh "$S" 'bash /srv/paperclf/server.sh status; ls /srv/paperclf/models; stat -c %a /srv/paperclf/.env'` | 지금 판, 통과 판 폴더(`validated.json` 포함), `600` |
| 러너 | GitHub → Settings → Actions → Runners | `paperclf`·`paperclf-final` 둘 다 Idle |

## 모델 되돌리기

`gh workflow run rollback.yml -f version=<판>` — 한 번에 두 서버 모두(`rollback`·`rollback-final`).

- 최종 서버는 **그 서버 `models/` 에 남아 있고 `validated.json` 이 있는 판**으로만 간다. 남은 판: `ssh "$S" 'ls /srv/paperclf/models'`
- 작업용 서버에만 있는 판(최종 서버를 켜기 전 판)이면 `rollback-final` 이 "통과 판이 아니다" 로 멈춘다 — 정상. 작업용 쪽은 그대로 되돌려진다.
- 되돌린 판의 health 가 실패하면 `server.sh` 가 직전 판으로 돌아가고 잡은 실패한다.

## 실패 시

- `*-final` 잡이 `Waiting for a runner` 에서 멈춤: `paperclf-final` 이 Offline — `ssh "$S" 'cd ~/actions-runner-paperclf && sudo ./svc.sh status'`
- 4단계가 토큰 오류로 멈춤: 2단계에서 새 토큰을 받아 4단계만 다시 (내려받은 러너는 다시 받지 않는다)
- `promote-final` 이 "낡은 실행": 이 실행이 시작된 뒤 다른 실행이 먼저 이 서버 판을 바꿨다(같은 실행의 잡 다시 돌리기도 여기에 걸린다) — 새 실행을 돌린다
- 인증서 발급 실패: [작업용 서버 런북](./work-server.md) "실패 시" 와 같다(방화벽 80·443, DNS). 반복 재시작 금지(발급 한도)

## 되돌리기 (서버 원래대로)

- 최종 배포 끄기: `gh variable set FINAL_ENABLED --body false`
- 앱만 내리기: `ssh "$S" 'cd /srv/paperclf && docker compose down'`
- eta 를 원래대로(Caddy 빼기): `ssh "$S" 'cd /srv/caddy && docker compose down -v; rm /srv/eta/compose.override.yml; cd /srv/eta && docker compose up -d'` — [자원 정리](./teardown.md) ①의 6·7단계와 같다
- 러너 빼기: `ssh -t "$S" 'cd ~/actions-runner-paperclf && sudo ./svc.sh uninstall && ./config.sh remove --token <제거 토큰>'` (제거 토큰: `gh api -X POST repos/metahomo/miniproject5_kms/actions/runners/remove-token -q .token`)

## (선택) 이 서버에도 장부 DB

작업용 서버 런북 "장부 DB" 1~3단계를 `S=ec2-user@13.237.237.56` 로 그대로 한다(`/srv/ledger/.env` 600, 비밀번호는 서버에서 `openssl rand -hex 24`). 그러면 `promote-final`·`rollback-final` 이 작업용과 똑같이 장부에 기록하고, 트리거가 미통과 판 배포를 거부한다. 백업(`ledger.py backup`)은 작업용 버킷에 쓸 수 없으니(다른 계정) 켜지 않는다 — 백업 위치가 정해지면 따로 한다.

## (선택) KMS 웹 게시 — Mac 에서 역방향 SSH 터널

작업용 서버의 "KMS 웹 임시 게시"([work-server.md](./work-server.md), `Caddyfile.work` 의 `kms.` 블록)를 이 서버로 옮길 때만. KMS 웹과 LLM 은 Mac 에서 돌고, 서버는 `127.0.0.1:10011` 로 받은 것을 HTTPS·접속 암호 뒤에서 내보낸다(Caddy 는 `network_mode: host` 라 `127.0.0.1:10011` 에 닿는다).

방식 고르기 — 서브도메인을 권한다:

| 방식 | 주소 | 필요한 것 | 주의 |
|---|---|---|---|
| 가. 서브도메인 | `https://kms.nlpwizard.eta.pyhub.kr` | DNS A 레코드 `kms.nlpwizard.eta.pyhub.kr → 13.237.237.56` (도메인 관리자에게 요청) | 인증서가 따로 발급된다 |
| 나. 하위 경로 | `https://nlpwizard.eta.pyhub.kr/kms/` | DNS 그대로 | KMS 웹이 `/static`·`/api` 같은 절대 경로를 쓰면 화면이 깨진다 — 먼저 시험 |

| # | 단계 | 명령·화면 | 기대 결과 |
|---|---|---|---|
| 1 | 암호 해시 만들기 (Mac, 원문은 Mac 파일에만) | `docker run --rm -i caddy:2.11.9-alpine caddy hash-password < ~/.config/paperclf/kms-web-password` | `$2a$14$…` 한 줄 (해시 — 저장소에는 넣지 않는다) |
| 2 | 서버 Caddyfile 에 블록 추가 | `ssh "$S"` 후 `/srv/caddy/Caddyfile` 에 아래 가 또는 나 블록을 넣고 `KMS_HASH` 를 1의 해시로 바꾼다 | 저장소 파일에는 `KMS_HASH` 그대로 |
| 3 | 검사 | `ssh "$S" 'docker run --rm -v /srv/caddy/Caddyfile:/etc/caddy/Caddyfile:ro caddy:2.11.9-alpine caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile'` | `Valid configuration` |
| 4 | 다시 시작 | `ssh "$S" 'cd /srv/caddy && docker compose restart caddy'` | paperclf·eta 는 그대로 응답 |
| 5 | 터널 (Mac) | `ssh -i ~/.ssh/id_ed25519_paperclf -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -R 127.0.0.1:10011:127.0.0.1:10001 ec2-user@13.237.237.56` (계속 켜 두려면 `~/.claude/autonomy/kms-tunnel-loop.sh` 의 주소만 바꾼 사본을 nohup 으로) | 서버 `127.0.0.1:10011` → Mac `127.0.0.1:10001` |
| 6 | 확인 | 암호 없이 `curl -s -o /dev/null -w '%{http_code}\n' https://kms.nlpwizard.eta.pyhub.kr/health` → `401`, `-u kms:<암호>` 로 → `status ok` (나 방식은 `…/kms/health`) | |

가. 서브도메인 블록 (파일 끝에):

```caddyfile
kms.nlpwizard.eta.pyhub.kr {
	encode zstd gzip
	header {
		Strict-Transport-Security "max-age=31536000"
		X-Content-Type-Options "nosniff"
		Referrer-Policy "no-referrer"
		X-Robots-Tag "noindex, nofollow"
		-Server
	}
	basic_auth {
		kms KMS_HASH
	}
	reverse_proxy 127.0.0.1:10011 {
		header_down -Server
	}
}
```

나. 하위 경로 — `nlpwizard.eta.pyhub.kr { … }` 블록 **안**의 `reverse_proxy 127.0.0.1:8080 { … }` 를 지우고 이것으로 바꾼다:

```caddyfile
	redir /kms /kms/
	handle_path /kms/* {
		header X-Robots-Tag "noindex, nofollow"
		basic_auth {
			kms KMS_HASH
		}
		reverse_proxy 127.0.0.1:10011 {
			header_down -Server
		}
	}
	handle {
		reverse_proxy 127.0.0.1:8080 {
			header_down -Server
		}
	}
```

- 손으로 넣은 블록은 `bootstrap.sh` 를 다시 돌리면 저장소 Caddyfile 로 덮인다(옛 파일은 `/srv/caddy/Caddyfile.bak`) — 다시 돌린 뒤 2~4단계를 반복한다.
- 내리기: Mac 터널을 끄고(`kill <터널 pid>`), 서버 Caddyfile 에서 블록을 지운 뒤 `docker compose restart caddy`.
- 암호 원문·해시를 채팅·저장소·명령 기록에 남기지 않는다.
