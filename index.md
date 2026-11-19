---
title: 미니 프로젝트 5 — ML 시스템 클라우드 배포
description: Lightsail·GitHub CI/CD 기반 ML 모델 자동 학습·검증·배포·롤백 프로젝트의 홈
tags:
  - home
---
# 미니 프로젝트 5 — ML 시스템 클라우드 배포

과제 원문: [과제 브리프](./sources/project-brief.md) · 학습 자료: [강의 자료 색인](./sources/lecture-index.md) · 전체 그림: [아키텍처 개요](./architecture/overview.md)

## 필수 기능 현황

방법은 자유, 다섯 가지 모두 지원해야 한다. 이 표는 요약이고, 상태의 정본은 GitHub 마일스톤·이슈다(R1~R5 = 이슈 #1~#5, 단계 0~5 = 마일스톤 1~6) — [사령관 지침 8절](./CLAUDE.md#8-진행-관리--github-가-진행판이다-2026-11-18-연구자-지시).

| # | 기능 | 상태 | 런북 |
|---|---|---|---|
| R1 | [Lightsail 인스턴스·버킷 활용](./requirements/R1-lightsail.md) | blocked — 서버 SSH 키·AWS 자격 증명 없음. 리전 시드니 `ap-southeast-2` 확정([ADR-007](./decisions/ADR-007-region-instance.md)), 서버 /health 는 아직 eta | [자원 정리](./runbooks/teardown.md) |
| R2 | [GitHub CI/CD — 테스트를 거쳐 서버까지](./requirements/R2-cicd.md) | doing — ci.yml 시험·이미지 완료, `v0.1.0` 태그 → GHCR `paperclf-api:v0.1.0` 공개, 서버 배포 대기(러너 미설치) | [코드 배포](./runbooks/deploy-code.md) |
| R3 | [새 데이터 자동 학습·검증(게이트·parity)](./requirements/R3-auto-train-validate.md) | doing — 게이트·자동 학습 시연 완료(약한 모델 F1 0.9021 실패, 데이터 변경 push 로 자동 학습 F1 0.9603·parity 5.8e-7), 실행별 기록 남음 | [모델 승격](./runbooks/promote-model.md) |
| R4 | [통과 모델 API 서버 배포](./requirements/R4-model-serving.md) | doing — API·이미지(`v0.1.0`) 완료, 승격 잡은 서버 대기. 예측 로그는 API 가 localhost 로([ADR-009](./decisions/ADR-009-ledger-writer.md)) | [모델 승격](./runbooks/promote-model.md) |
| R5 | [롤백 지원](./requirements/R5-rollback.md) | doing — rollback.yml·server.sh 작성, 서버·버킷 대기. DB 백업 14개 보관([ADR-008](./decisions/ADR-008-ledger-db-ops.md)) | [롤백](./runbooks/rollback.md) |

## 폴더

| 폴더 | 담는 것 | 템플릿 |
|---|---|---|
| `requirements/` | 필수 기능별 요구사항·완료 기준·검증 증거 | [`requirement`](./templates/requirement.md) |
| `architecture/` | 설계 문서 | [`design-doc`](./templates/design-doc.md) |
| `runbooks/` | 그대로 실행하는 운영 절차 | [`runbook`](./templates/runbook.md) |
| `experiments/` | 학습 실행별 게이트·parity·승격 기록 — [색인](./experiments/index.md) | [`training-run`](./templates/training-run.md) |
| `decisions/` | 설계 결정(ADR) — [색인](./decisions/index.md) | [`adr`](./templates/adr.md) |
| `sources/` | 근거 원자료 | [`source`](./templates/source.md) |
| `ai-usage/` | 작업별 AI 활용 기록(주도한 점·맡긴 점) — [색인](./ai-usage/index.md) | [`ai-session`](./templates/ai-session.md) |
| `presentation/` | 발표 원고 — [발표 개요](./presentation/index.md) | [`slide-section`](./templates/slide-section.md) |
| `reports/` | 사령관 보고서 — [KMS 활용 타당성](./reports/2026-11-18-kms-feasibility.md) | — |

## 설계 원칙

정답은 없다. 도메인보다 기술의 이해·활용에 초점을 두고, 강의 아키텍처는 예시로만 쓴다. 이해한 범위 안에서 최대한 온전한 서비스를 만든다 — [과제 브리프](./sources/project-brief.md#설계-원칙--정답은-없다).

사령관 지침: [CLAUDE.md](./CLAUDE.md) · 부관 지침: [AGENTS.md](./AGENTS.md) · 작업 일지: [log](./log.md)
