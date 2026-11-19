---
title: 모델 승격
description: 새 데이터로 학습·검증한 모델을 API 서버에 배포하는 절차
tags:
  - runbook
  - model
requirement: R3, R4
---
# 모델 승격

요구사항: [R3 자동 학습·검증](../requirements/R3-auto-train-validate.md), [R4 모델 API 배포](../requirements/R4-model-serving.md)

## 언제 쓰나

- 새 라벨 스냅숏(`data/snapshots/**`)이 main 에 들어오면 **자동**으로 돈다
- 손으로 다시 학습·승격할 때, 또는 게이트를 시험할 때(일부러 약한 모델)

## 전제조건

- [ ] `DEPLOY_ENABLED=true`, `MODEL_BUCKET=paperclf-models-apse2`, `AWS_REGION=ap-southeast-2`
- [ ] 러너 `paperclf` 온라인, 인스턴스가 버킷에 리소스 액세스(키 없이 읽고 씀)

## 절차

| # | 단계 | 명령·화면 | 기대 결과 |
|---|---|---|---|
| 1 | 실행 | `gh workflow run model.yml --ref main` (게이트 시험: `-f data_fraction=0.05`) | train → parity → promote |
| 2 | 결과 | `gh run watch <실행 ID> --exit-status` | 정상: 셋 다 성공 / 약한 모델: train 실패, 나머지 skipped |
| 3 | 확인 | `curl -fsS https://54-252-22-31.sslip.io/health` | `model_version` = 새 판 `m<날짜>-<실행 번호>` (약한 모델이면 그대로) |

promote 잡 순서: 낡은 실행 검사 → 버킷 `models/<판>/` 에 올리기(있는 판은 덮어쓰지 않음) → 서버로 받아 `server.sh model <판>`(health 실패 시 직전 판 복귀) → `current.json` 갱신.

시연(2026-11-19): 승격 m20261119-7 [https://github.com/metahomo/miniproject5_kms/actions/runs/44514427871](https://github.com/metahomo/miniproject5_kms/actions/runs/44514427871), m20261119-8 [https://github.com/metahomo/miniproject5_kms/actions/runs/44514698446](https://github.com/metahomo/miniproject5_kms/actions/runs/44514698446) · 미통과 차단(F1 0.9021 < 0.8805+0.05) [https://github.com/metahomo/miniproject5_kms/actions/runs/44515846566](https://github.com/metahomo/miniproject5_kms/actions/runs/44515846566)

## 확인

실행 결과는 [학습·검증 기록](../experiments/index.md)에 남긴다.
