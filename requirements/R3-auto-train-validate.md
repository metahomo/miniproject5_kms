---
title: R3 새 데이터 자동 학습·모델 검증(게이트·parity)
description: 새 데이터가 들어오면 자동으로 학습하고, 성능 게이트와 parity 검사를 통과해야 승격 후보가 된다
tags:
  - requirement
  - training
  - validation
id: R3
status: doing
---
# R3 새 데이터 자동 학습·모델 검증

## 요구사항

"새로운 데이터에 대해 자동화된 학습과 모델 검증(게이트·parity)" — [과제 브리프](../sources/project-brief.md) 3번.

## 강의 근거

[강의 자료 색인](../sources/lecture-index.md#필수-기능과-강의-절-대응): 02 › 검증 게이트·일치 확인(parity)·운영 지표 재학습 트리거, 03 › model 워크플로.

## 설계

[아키텍처 개요](../architecture/overview.md#모델-판) — 모델 판.

## 용어

- **게이트**: 새 모델 지표가 기준(절대 기준 또는 현재 운영 모델 대비)을 넘어야 통과.
- **parity**: 학습에 쓴 모델과 배포 형식(예: ONNX, 다른 언어 서버)의 예측이 허용 오차 안에서 일치해야 통과.

## 완료 기준 (초안)

- [x] 버킷(또는 저장소)의 데이터가 바뀌면 학습 워크플로가 사람 개입 없이 실행 — 저장소 `data/snapshots/**` 변경 push 로 `model` 자동 실행(아래 증거 2)
- [x] 게이트 실패 시 승격되지 않고 운영 모델 그대로 — 배포를 켠 상태에서 F1 0.9021 → promote 건너뜀, 서버 판 그대로([https://github.com/metahomo/miniproject5_kms/actions/runs/44515846566](https://github.com/metahomo/miniproject5_kms/actions/runs/44515846566))
- [x] parity 실패 시 승격되지 않음 — `parity_tol=1e-12` 로 parity 실패 → promote 건너뜀, 서버 m20261119-11 그대로([https://github.com/metahomo/miniproject5_kms/actions/runs/44519475156](https://github.com/metahomo/miniproject5_kms/actions/runs/44519475156))
- [x] 실행마다 학습·검증 기록 한 건 — 운영 장부 DB `model_versions`(통과는 promote, 멈춘 실행은 record-failure 가 기록, [ADR-009](../decisions/ADR-009-ledger-writer.md), PR #26). 조회: 서버에서 `python3 /srv/ledger/ledger.py status`

## 검증 증거

| 날짜 | 무엇을 확인 | 결과 | 증거 |
|---|---|---|---|
| 2026-11-19 | 일부러 낮춘 모델(`data_fraction=0.05`, 수동 실행)이 게이트에서 멈추는가 | F1 0.9021 → 게이트 실패, parity·promote 건너뜀 | [model 실행 44452096551](https://github.com/metahomo/miniproject5_kms/actions/runs/44452096551) |
| 2026-11-19 | 데이터(스냅숏) 변경 push 로 자동 학습, 정상 모델 게이트·parity | 자동 실행(main push), F1 0.9603 통과, parity 최대 차이 5.8e-7(허용 1e-5) 통과. promote 는 서버 대기로 건너뜀 | [model 실행 44451897410](https://github.com/metahomo/miniproject5_kms/actions/runs/44451897410) |
| 2026-11-19 | 서빙 이미지 태그 배포(R4 와 공유) | `v0.1.0` 태그 → test·image 통과, GHCR `paperclf-api:v0.1.0` 공개. deploy 는 서버 대기로 건너뜀 | [ci 실행 44453216170](https://github.com/metahomo/miniproject5_kms/actions/runs/44453216170) |

## 미해결

- ~~모델·데이터셋 주제~~ → [ADR-005](../decisions/ADR-005-student-model-snapshot.md)
- ~~게이트 지표·임계값, parity 허용 오차~~ → [ADR-006](../decisions/ADR-006-gate-parity.md)(시험지 확정: 교사 라벨 고정 20% 분할 178편)
- ~~트리거 방식~~ → `model.yml`: `data/snapshots/**` 변경 push(자동)·PR(승격 없이 검사)·수동 실행
- ~~실행마다 기록(기준 4)~~ · ~~parity 실패 시연(기준 3)~~ → 2026-11-19 완료
