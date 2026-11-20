---
title: 최종 결과물 서버 (nlpwizard.eta.pyhub.kr)
description: 교수님 서버 13.237.237.56 에 eta 와 함께 paperclf 를 올리는 절차 — 점검·준비·배포·확인·되돌리기
tags:
  - runbook
requirement: R1
---
# 최종 결과물 서버 (nlpwizard.eta.pyhub.kr)

요구사항: [R1](../requirements/R1-lightsail.md) · 결정: [ADR-003](../decisions/ADR-003-domain-server.md)(도메인), PR #21(eta 와 Caddy 공존)

## 언제 쓰나

최종 발표용으로 교수님 서버(Lightsail, `13.237.237.56`, 강의 앱 delivery-eta 가 이미 돌고 있다)에 paperclf 를 함께 올릴 때. 작업용 서버(`54.252.22.31`)는 그대로 두고 **두 서버에 같이** 배포한다.

## 전제조건

- [ ] 교수님이 서버에 사령관 공개키를 등록 → 사용자 이름 확인(이 문서는 `ec2-user` 로 쓴다. 다르면 `bootstrap.sh` 의 `ec2-user` 를 바꾼다)
- [ ] 교수님 승인: eta 를 `127.0.0.1:8090` 으로 옮기고 Caddy 가 80·443 을 맡는다(IP 로 오는 요청은 그대로 eta)
- [ ] DNS `nlpwizard.eta.pyhub.kr` → `13.237.237.56` (2026-11-20 확인), Lightsail 방화벽 80·443 열림
- [ ] 이 서버는 교수님 AWS 계정이라 연구자 버킷에 붙일 수 없다 → 모델은 Actions 실행 산출물에서 직접 받는다(`promote-final`)

## 절차

| # | 단계 | 명령·화면 | 기대 결과 |
|---|---|---|---|
| 1 | 점검(읽기만) | `ssh <user>@13.237.237.56 'uname -m; docker compose version; ls /srv; docker ps; free -m; df -h /'` | x86_64, Compose ≥ 2.24.4, `/srv/eta` 와 eta 컨테이너 |
| 2 | 러너 등록 토큰 | PC: `gh api -X POST repos/metahomo/miniproject5_kms/actions/runners/registration-token -q .token` | 토큰 한 줄(1시간) |
| 3 | 준비 스크립트 | 서버: `curl -fsSL https://raw.githubusercontent.com/metahomo/miniproject5_kms/main/deploy/lightsail/bootstrap.sh -o bootstrap.sh && bash bootstrap.sh` → 토큰 붙여 넣기 | ① 폴더·토큰 ② eta → 8090 ③ Caddy ④ 러너 `paperclf-final`(이름표 `final`) |
| 4 | 최종 배포 켜기 | PC: `gh variable set FINAL_ENABLED --body true` | `deploy-final`·`promote-final`·`rollback-final` 잡이 이 서버로 |
| 5 | 코드 배포 | 지금 태그의 ci 실행을 다시 돌리거나 새 태그 `v0.1.5` | `deploy-final` 성공 |
| 6 | 모델 | `gh workflow run model.yml --ref main` | `promote` 다음 `promote-final` 성공 |

## 확인

| 무엇 | 명령 | 기대 |
|---|---|---|
| HTTPS | `curl -fsS https://nlpwizard.eta.pyhub.kr/health` | `status: ok`, 작업용 서버와 같은 app·model 판 |
| 보호 | 토큰 없이 `POST /predict` | `401` |
| eta | `curl -fsS http://13.237.237.56/health` | eta 응답(바뀌지 않음) |
| 러너 | GitHub → Settings → Actions → Runners | `paperclf`·`paperclf-final` 둘 다 Idle |

## 되돌리기

- 앱만 내리기: `cd /srv/paperclf && docker compose down`
- eta 를 원래대로(Caddy 빼기): `cd /srv/caddy && docker compose down -v; rm /srv/eta/compose.override.yml; cd /srv/eta && docker compose up -d` — [자원 정리](./teardown.md) ①의 6·7단계와 같다
- 최종 배포 끄기: `gh variable set FINAL_ENABLED --body false`
