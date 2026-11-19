---
title: 롤백
description: 코드·모델을 직전 버전으로 되돌리고 다시 앞으로 돌리는 절차
tags:
  - runbook
  - rollback
requirement: R5
---
# 롤백

요구사항: [R5 롤백](../requirements/R5-rollback.md)

## 언제 쓰나

- 새 모델 판이 운영에서 문제를 일으킬 때 — 모델만 직전 판으로 (이미지는 그대로)
- 새 코드(이미지 태그)가 문제를 일으킬 때 — 코드만 직전 태그로 (모델은 그대로)
- 배포·승격 중 `/health` 가 실패하면 `server.sh` 가 직전 판으로 **스스로** 돌아간다. 아래 절차는 사람이 일부러 되돌릴 때다

## 전제조건

- [ ] 저장소 변수 `DEPLOY_ENABLED=true`, `MODEL_BUCKET`, `AWS_REGION` (확인: `gh variable list`)
- [ ] 러너 `paperclf` 온라인 (저장소 Settings → Actions → Runners)
- [ ] 되돌릴 판이 버킷에 있다: `aws s3 ls s3://paperclf-models-apse2/models/` (서버에서) — 모델
- [ ] 되돌릴 태그의 ci 실행이 있다: `gh run list --workflow ci.yml --branch <태그>` — 코드

## 절차 — 모델

| # | 단계 | 명령·화면 | 기대 결과 |
|---|---|---|---|
| 1 | 지금 판 확인 | `curl -fsS https://54-252-22-31.sslip.io/health` | `model_version` = 지금 판 |
| 2 | 되돌리기 실행 | `gh workflow run rollback.yml --ref main -f version=<직전 판>` | rollback 실행 시작 |
| 3 | 결과 | `gh run watch <실행 ID> --exit-status` | 성공 — 버킷에서 받아 `server.sh model <판>`, `current.json` 갱신 |
| 4 | 확인 | `curl -fsS https://54-252-22-31.sslip.io/health` | `model_version` = 직전 판 |

시연(2026-11-19): m20261119-8 → 7 [https://github.com/metahomo/miniproject5_kms/actions/runs/44514983743](https://github.com/metahomo/miniproject5_kms/actions/runs/44514983743)

## 절차 — 코드

ci 의 deploy 잡은 태그 push 때만 돈다. 직전 태그의 **ci 실행을 다시 돌리면** 그 태그 이미지로 다시 배포된다(모델은 `.env` 의 MODEL_VERSION 그대로).

| # | 단계 | 명령·화면 | 기대 결과 |
|---|---|---|---|
| 1 | 지금 판 확인 | `curl -fsS https://54-252-22-31.sslip.io/health` | `app_version` = 지금 태그 |
| 2 | 직전 태그의 ci 실행 찾기 | `gh run list --workflow ci.yml --branch <직전 태그> -L 1` | 실행 ID |
| 3 | 다시 돌리기 | `gh run rerun <실행 ID>` | test → image → deploy |
| 4 | 결과 | `gh run watch <실행 ID> --exit-status` | deploy 성공 |
| 5 | 확인 | `curl -fsS https://54-252-22-31.sslip.io/health` | `app_version` = 직전 태그, `model_version` 그대로 |

시연(2026-11-19): v0.1.1 → v0.1.0 [https://github.com/metahomo/miniproject5_kms/actions/runs/44453216170](https://github.com/metahomo/miniproject5_kms/actions/runs/44453216170)

## 확인

| 무엇 | 명령 | 기대 |
|---|---|---|
| 밖에서 | `curl -fsS https://54-252-22-31.sslip.io/health` | `status: ok`, 바꾼 판 |
| 버킷 포인터(모델) | 서버에서 `aws s3 cp s3://paperclf-models-apse2/models/current.json -` | `model_version` = 바꾼 판 |
| 서버 상태 | 서버에서 `bash /srv/paperclf/server.sh status` | `.env` 의 TAG·MODEL_VERSION |

## 다시 앞으로

- 모델: 같은 rollback 워크플로에 **새 판**을 넣는다 — m20261119-7 → 8 [https://github.com/metahomo/miniproject5_kms/actions/runs/44515052182](https://github.com/metahomo/miniproject5_kms/actions/runs/44515052182)
- 코드: 새 태그의 ci 실행을 다시 돌린다 — v0.1.0 → v0.1.1 [https://github.com/metahomo/miniproject5_kms/actions/runs/44513840582](https://github.com/metahomo/miniproject5_kms/actions/runs/44513840582)
