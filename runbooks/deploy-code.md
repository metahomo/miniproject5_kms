---
title: 코드 배포
description: 코드 변경을 테스트 통과 뒤 Lightsail 서버에 반영하는 절차
tags:
  - runbook
  - cicd
requirement: R2
---
# 코드 배포

요구사항: [R2 GitHub CI/CD](../requirements/R2-cicd.md)

## 언제 쓰나

코드(API·이미지)를 서버에 내보낼 때. 모델 판은 바뀌지 않는다.

## 전제조건

- [ ] main 이 초록(ci test 성공), `DEPLOY_ENABLED=true`
- [ ] 러너 `paperclf` 온라인

## 절차

| # | 단계 | 명령·화면 | 기대 결과 |
|---|---|---|---|
| 1 | 태그 | `git tag -a v<번호> -m "<설명>" && git push origin v<번호>` | ci 실행 시작 |
| 2 | 결과 | `gh run watch <실행 ID> --exit-status` | test → image(GHCR `paperclf-api:<태그>`) → deploy 성공 |
| 3 | 확인 | `curl -fsS https://54-252-22-31.sslip.io/health` | `app_version` = 새 태그 |

deploy 잡은 서버 러너에서 `server.sh image <태그> <이미지>` 를 돌린다 — 새 이미지로 띄우고 `/health` 가 30초 안에 답하지 않으면 직전 TAG 로 돌아간다.

시연(2026-11-19): v0.1.1 첫 배포 [https://github.com/metahomo/miniproject5_kms/actions/runs/44513840582](https://github.com/metahomo/miniproject5_kms/actions/runs/44513840582)

## 확인

밖에서 `curl -fsS https://54-252-22-31.sslip.io/health` · HTTP 는 `308` 로 HTTPS 리디렉트.

## 실패 시

- deploy 잡이 대기만 함: 러너 오프라인 — 서버에서 러너 서비스 상태 확인
- health 실패로 복귀: 서버에서 `docker compose -f /srv/paperclf/compose.yml logs api`

## 되돌리기

[롤백](./rollback.md) — 절차 · 코드
