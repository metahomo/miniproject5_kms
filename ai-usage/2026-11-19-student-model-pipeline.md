---
title: AI 활용 — 교사 라벨부터 학습·게이트·ONNX·서빙·워크플로까지 (연구자 외출 중 자율 수행)
description: 연구자가 전권을 위임하고 외출한 동안 사령관이 0·1·3단계 코드와 GitHub 진행판을 만든 기록
tags:
  - ai-usage
date: 2026-11-19
requirement: R2, R3, R4, R5
tool: Claude Code(사령관) + gh CLI + 로컬 LLM(교사)
mode: delegate
---
# AI 활용 — 교사 라벨부터 워크플로까지

## 목표

조감도·GitHub·칸반·강의안 순서(0 준비 → 1 코드 판 → 3 모델 판)대로, 서버 접근 없이 할 수 있는 부분을 끝까지 만든다.

## 사람이 정한 것 (주도)

- 연구자 지시(2026-11-19): "조감도 깃허브/칸반보드/강의안 순서에 따라 프로젝트를 진행해줘. 연구자는 외출한다. 권한은 사령관에게 모두 위임한다."
- 계약·제약·금지 사항: 지시 원문(위)에는 별도 제약이 없다 — "권한은 사령관에게 모두 위임한다". 그 밖의 제약 원문은 미확인. 상시 제약은 [사령관 지침](../CLAUDE.md) 1절. 병합은 위임 범위에 명시되지 않아 하지 않았다([보고서](../reports/2026-11-19-autonomous-progress.md) 6절) (연구자 위임 초안)
- 검수 기준: 코드는 사령관이 테스트를 돌려 통과를 본 뒤에만 완료로 표시한다 — [사령관 지침](../CLAUDE.md) 5절. 로컬 pytest·Actions test 잡, 게이트 F1 통과·약한 모델 실패, ONNX 차이 ≤ 1e-5, API `/health`·`/predict`, 스냅숏에 원문 필드 없음(아래 표) (연구자 위임 초안)

## AI에게 맡긴 것

| 일 | 산출물 |
|---|---|
| 칸반보드 구성(5열, 이슈 16 + PR 카드) | GitHub Projects "miniproject5 Kanban Board"(#12) |
| KMS 수집(OpenAlex·KCI 867편, ADR-004 범위) | KMS `data/kms.sqlite3` 에 새 논문 추가만 |
| 교사 라벨(로컬 LLM 867편, KMS DB 읽기 전용) | `labeler/teacher_label.py` |
| 공개 스냅숏 형식(원문 없이 해싱 특징) | `training/snapshot.py`, `data/snapshots/`, [ADR-005](../decisions/ADR-005-student-model-snapshot.md) |
| 학생 모델·게이트·ONNX·모델 카드·parity | `paperclf/`, `training/`, [ADR-006](../decisions/ADR-006-gate-parity.md) |
| 서빙 API·이미지·서버 스크립트 | `api/`, `deploy/lightsail/` |
| 워크플로 | `.github/workflows/ci.yml` · `model.yml` · `rollback.yml` |

## 결과와 검수

| AI 산출물 | 사령관이 확인한 방법 | 연구자 검수 |
|---|---|---|
| 시험 | 로컬 `uv run --group train pytest` 15 통과, GitHub Actions `ci` test 잡 통과 |  |
| 게이트 | 전체 데이터 F1 0.9603 통과, 데이터 5% 모델 F1 0.9021 실패(로컬 명령 출력) |  |
| ONNX | 원본과 최대 차이 5.4e-7. `sublinear_tf=True` 는 0.0018 어긋나 껐다(진단 스크립트로 확인) |  |
| API | 로컬 uvicorn `/health`·`/predict` 응답, parity 스크립트 통과 |  |
| 저작권 | 스냅숏에 제목·초록·사유 필드가 없음을 `training/snapshot.py` 출력 형식으로 확인 |  |

## 배운 점 / 다음엔

- 변환기(skl2onnx)는 옵션 하나(`sublinear_tf`)로 원본과 달라질 수 있다 — parity 를 학습 직후와 이미지 두 곳에서 본다.
- 게이트 시험지로 하이퍼파라미터를 고르면 시험지가 오염된다 — 미리 정한 값을 유지했다.
