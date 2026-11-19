---
title: 결정 기록 색인
description: ADR 목록과 아직 정하지 않은 결정
tags:
  - adr
---
# 결정 기록 색인

새 결정은 이 폴더의 `adr` 템플릿으로 `ADR-001-제목` 처럼 만든다.

## 확정된 결정

| ADR | 제목 | 상태 |
|---|---|---|
| [ADR-009](./ADR-009-ledger-writer.md) | 장부 기록은 서버 self-hosted runner 와 API 가 localhost 로 (#15) | accepted |
| [ADR-008](./ADR-008-ledger-db-ops.md) | 운영 장부 DB 는 같은 인스턴스 compose 컨테이너, pg_dump → 버킷 백업 (#14) | accepted |
| [ADR-007](./ADR-007-region-instance.md) | 리전 시드니, 기존 인스턴스·요금제 그대로, 버킷도 같은 리전 (#16) | accepted |
| [ADR-006](./ADR-006-gate-parity.md) | 게이트 시험지·지표·임계값과 parity 허용 오차 (#12 · #13) | accepted |
| [ADR-005](./ADR-005-student-model-snapshot.md) | 배포 모델(교사 LLM → 학생 TF-IDF 로지스틱)과 원문 없는 라벨 스냅숏 | accepted |
| [ADR-004](./ADR-004-kms-auto-collection-unfreeze.md) | KMS 참고문헌·운영 DB 동결을 자동 수집에 한해 푼다 | accepted |
| [ADR-003](./ADR-003-domain-server.md) | 서비스 도메인 nlpwizard.eta.pyhub.kr · 서버 13.237.237.56 | accepted |
| [ADR-002](./ADR-002-postgresql.md) | 모델·예측 장부 DB 로 PostgreSQL 을 쓴다 | accepted |

## 아직 정하지 않은 것

각 요구사항 문서의 미해결 절에서 모았다.

- 도메인(게임·유사 도메인·기존 서비스 벤치마킹 중) — [발표 1절](../presentation/01-architecture-why-flow.md)
- ~~예측 대상 모델·데이터셋~~ → [ADR-005](./ADR-005-student-model-snapshot.md)
- AI에게 서비스 제공 방식(옵션) — [발표 4절](../presentation/04-service-for-ai.md)
- ~~게이트 지표·임계값, parity 허용 오차~~ → [ADR-006](./ADR-006-gate-parity.md)
- ~~코드 배포 방식(SSH / 자체 호스팅 러너)~~ → 자체 호스팅 러너 — [ADR-009](./ADR-009-ledger-writer.md) · [R2](../requirements/R2-cicd.md)
- ~~모델 형식~~ → ONNX — [ADR-005](./ADR-005-student-model-snapshot.md) · 교체 방식 — [R4](../requirements/R4-model-serving.md)
- 버전 이력 보관 개수 — [R5](../requirements/R5-rollback.md)
- ~~인스턴스 요금제·리전~~ → [ADR-007](./ADR-007-region-instance.md) · [R1](../requirements/R1-lightsail.md)
