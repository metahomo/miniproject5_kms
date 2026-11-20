---
title: 발표 — AI 활용 방식
description: 딘깍이 아니라 어떻게 주도적으로 AI를 썼는지 — 사람의 역할과 AI의 역할
tags:
  - presentation
required: true
status: draft
---
# 발표 — AI 활용 방식

## 핵심 메시지 (내 언어로)

(연구자 위임 초안)

"그냥 딸깍"이 아니라, **사람이 방향·결정·권한을 정하고, AI 가 만들고, 증거로 검수한다.** 사람은 진행 순서(조감도 → GitHub → 칸반 → 강의안)와 위임 범위를 지시하고, AI 가 낸 잠정 결정(ADR-005 · 006)과 서버 구성(Caddy 공존)은 사람이 확정했다. AI 는 사령관(Claude 메인 세션)이 부관(서브에이전트)들을 병렬로 지휘하는 구조로 일했고, 산출물마다 명령 출력·Actions 실행 링크를 증거로 남겼다. 모든 작업은 [AI 활용 기록](../ai-usage/index.md)에 한 건씩(9건) 있다.

## 근거 문서

- [AI 활용 기록](../ai-usage/index.md) — 작업별 기록에서 골라 쓴다.
- 지휘 구조: [사령관 지침](../CLAUDE.md) 3·4절(부관 파견, 위임 지시서 5요소), [부관 지침](../AGENTS.md).
- 결정: [결정 기록](../decisions/index.md), PR [#20](https://github.com/metahomo/miniproject5_kms/pull/20)(ADR-005·006 확정), PR [#21](https://github.com/metahomo/miniproject5_kms/pull/21)(서버 Caddy 공존).
- 진행 증거: [자율 진행 보고서](../reports/2026-11-19-autonomous-progress.md).

## 정리 틀

> "사람이 주도한 것" 칸은 모두 **(연구자 위임 초안)** 이다 — 연구자의 실제 지시·결정만 인용했고, 연구자가 자기 말로 다듬는다. 각 AI 활용 기록의 "연구자 검수" 칸은 아직 비어 있다.

| 단계 | AI에게 맡긴 것 | 사람이 주도한 것(계약·검수·판단) | 증거 |
|---|---|---|---|
| 설계 | 지식 베이스 골격, 강의 3개 교과서화·KMS 조사(부관 4명 병렬), 선택지 비교와 ADR 초안(PostgreSQL 장부, 학생 모델·스냅숏, 게이트·parity), 아키텍처 개요 | 서버 지정(작업용 서버 `54.252.22.31`), "DB 는 PostgreSQL 로 생성", KMS 동결 해제는 자동 수집에 한해(선택 1번), ADR-005 · 006 확정(PR #20), 서버는 기존 eta 와 Caddy 로 공존(PR #21) | [ADR-002](../decisions/ADR-002-postgresql.md) · [ADR-003](../decisions/ADR-003-domain-server.md) · [ADR-004](../decisions/ADR-004-kms-auto-collection-unfreeze.md) · [ADR-005](../decisions/ADR-005-student-model-snapshot.md) · [ADR-006](../decisions/ADR-006-gate-parity.md), [강의 교과서화 기록](../ai-usage/2026-11-18-lecture-and-survey.md) |
| 구현 | KMS 수집 867편(ADR-004 범위), 교사 라벨(로컬 LLM, KMS DB 읽기 전용), 원문 없는 스냅숏, 학생 모델·ONNX·모델 카드, 서빙 API·이미지·서버 스크립트, 장부 DB 스키마·트리거 | "조감도·깃허브·칸반·강의안 순서대로 진행, 권한은 사령관에게 모두 위임"(2026-11-19) — 순서와 위임 범위를 사람이 정함. "모든 수행을 멀티로, 필요하면 모든 부관 파견"(2026-11-19) | [교사 라벨~워크플로 기록](../ai-usage/2026-11-19-student-model-pipeline.md), [장부 DB 기록](../ai-usage/2026-11-18-postgresql-ledger.md), PR [#19](https://github.com/metahomo/miniproject5_kms/pull/19) |
| 테스트 | pytest 32개(처음 15개에서 장부·예측 로그·보호·원격 MCP·다중 스냅숏 시험 추가), 게이트 실패 시연(데이터 5% → F1 0.9021), parity(원본 ↔ 서빙 이미지), 트리거 거부 시험, `sublinear_tf` 오차 진단 | 게이트 기준(하한 0.80 · 기준선 + 0.05 · 운영 대비 −0.02)과 parity 1e-5 를 사람이 확정(PR #20). 사람 검수 시험지는 결정 대기(이슈 [#12](https://github.com/metahomo/miniproject5_kms/issues/12)) | [정상 model 실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44451897410)(parity 5.8e-7), [5% 실패 실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44452096551), 배포 켠 상태 [5% 차단](https://github.com/metahomo/miniproject5_kms/actions/runs/44515846566) · [parity 1e-12 차단](https://github.com/metahomo/miniproject5_kms/actions/runs/44519475156), ADR-006 확인한 사실 |
| 배포·운영 | `ci` · `model` · `rollback` 워크플로, 서버 준비 스크립트(`bootstrap.sh`), 운영 장부 DB(PR #26 — 통과는 promote, 멈춘 실행은 record-failure 잡이 기록, 승격·롤백 직후·매일 03:17 UTC 백업 → 버킷 `ledger/` 14개 보관), 비용이 드는 AWS 자원(버킷 $1/월)은 연구자의 "배포 시작해"와 권한 허용 뒤에 만듦, 예측 로그(v0.1.2 — 원문 없이 해시·길이·점수만 장부 `predictions` 에) | 서버 Caddy 공존 결정과 서버 작업은 연구자가 브라우저 SSH 로 직접(PR #21). 병합은 사람 권한 — 사령관의 PR #19 병합 시도는 권한 확인에 걸려 하지 않음(보고서 6절). 작업용 서버(`https://54-252-22-31.sslip.io`)에서 배포·승격·롤백을 실행해 매번 `/health` 의 `model_version` 일치를 확인. 지금 운영 app v0.1.4 · model m20261120-17 | [v0.1.0 태그 실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44453216170), 이미지 `ghcr.io/metahomo/miniproject5_kms/paperclf-api:v0.1.0`, [v0.1.1 태그 → 배포](https://github.com/metahomo/miniproject5_kms/actions/runs/44513840582), 승격 [m20261119-7](https://github.com/metahomo/miniproject5_kms/actions/runs/44514427871) · [m20261119-8](https://github.com/metahomo/miniproject5_kms/actions/runs/44514698446), 되돌리기 [→7](https://github.com/metahomo/miniproject5_kms/actions/runs/44514983743) · [다시 →8](https://github.com/metahomo/miniproject5_kms/actions/runs/44515052182), [장부 승격 m20261119-11](https://github.com/metahomo/miniproject5_kms/actions/runs/44519470540), [릴리스 v0.1.1](https://github.com/metahomo/miniproject5_kms/releases/tag/v0.1.1), [자율 진행 보고서](../reports/2026-11-19-autonomous-progress.md) 4절 |
| 문서·발표 | AI 활용 기록 9건, GitHub 진행판(라벨·마일스톤·이슈 16·칸반 5열), 조감도 보충 문안, 보조 슬라이드 17장, 이 원고 초안 | 발표는 별도 자료 없이 조감도 문서로(2026-11-18 결정), GitHub 가 진행판이고 칸반 완성 = 프로젝트 완성, "연구자가 해야 할 일도 바로 해줘"(2026-11-19) — 이 칸들의 초안까지 위임 | [발표 개요](./index.md), [GitHub 진행 관리 기록](../ai-usage/2026-11-18-github-progress.md), [보조 슬라이드](https://metahomo.github.io/md-slides/miniproject5-kms/) |

## 슬라이드 원고

보조 슬라이드 [metahomo.github.io/md-slides/miniproject5-kms](https://metahomo.github.io/md-slides/miniproject5-kms/) 의 10–12장이 이 절이다.

| # | 제목 | 내용 | 그림·시연 |
|---|---|---|---|
| 1 | AI 활용 방식 — 한 줄 | "그냥 딸깍"이 아니라, 사람이 계약하고 AI 가 만들고 증거로 검수한다 | 보조 슬라이드 10장 |
| 2 | 역할 나누기 | 사람: 진행 순서·위임 범위 지시, ADR-005 · 006 확정(PR #20), 서버 Caddy 공존 결정(PR #21), 병합·서버 작업. AI: 칸반·교사 라벨·학생 모델·게이트·ONNX·API·워크플로. 지휘 구조: 사령관(`CLAUDE.md`)이 부관(`AGENTS.md`)을 병렬 파견, 위임 지시서 5요소 | 보조 슬라이드 11장, 위 정리 틀 표 |
| 3 | AI 산출물을 어떻게 검수했나 | pytest 32 + Actions `ci`, 게이트 통과·실패를 출력으로, ONNX 차이 5.4e-7(로컬)·5.8e-7(Actions), API `/health`·`/predict`, 스냅숏에 원문 필드 없음 | 보조 슬라이드 12장, [정상 model 실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44451897410), [5% 실패 실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44452096551) |

## 예상 질문과 답

| 질문 | 답 | 근거 |
|---|---|---|
| 전부 AI 가 한 것 아닌가? | 만든 것은 대부분 AI 다. 하지만 무엇을 어떤 순서로 할지, 무엇을 확정할지(ADR-005 · 006, Caddy 공존), 무엇을 사람 권한으로 남길지(병합·서버·비용 드는 자원)는 사람이 정했다 | 위 정리 틀, PR #20 · #21 |
| AI 결과를 어떻게 믿었나? | 설명이 아니라 증거만 받았다 — 명령 출력·Actions 실행 링크. 게이트가 일부러 약한 모델을 실제로 막는지도 실행으로 확인했다 | [교사 라벨~워크플로 기록](../ai-usage/2026-11-19-student-model-pipeline.md) 결과와 검수 표 |
| AI 가 실수한 적은? | 변환기 옵션 `sublinear_tf=True` 로 ONNX 가 원본과 0.0018 어긋났는데, parity 검사로 잡아 껐다(4.4e-9). 게이트 시험지로 하이퍼파라미터를 고르면 시험지가 오염되므로 미리 정한 C=4 를 유지했다 | ADR-005 · ADR-006 확인한 사실 |
| 여러 에이전트를 어떻게 통제했나? | 사령관·부관 두 겹 지침과 위임 지시서 5요소(목표·입력·산출물·완료 기준·금지). 같은 파일은 두 부관에게 동시에 맡기지 않는다 | [사령관 지침](../CLAUDE.md) 3·4절, [부관 지침](../AGENTS.md) |
| 사람 검수는 실제로 했나? | 각 AI 활용 기록의 "연구자 검수" 칸은 아직 비어 있다. 발표 전에 연구자가 채운다 | [AI 활용 기록](../ai-usage/index.md) |
