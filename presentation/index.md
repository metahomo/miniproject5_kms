---
title: 발표 개요
description: 발표 필수 2절·옵션 2절의 순서와 준비 현황
tags:
  - presentation
---
# 발표 개요

**발표는 별도 자료 없이 조감도 문서(claude.ai "미니 프로젝트 5 조감도")로 한다(2026-11-18 연구자 결정).** 조감도의 "발표 순서" 절이 아래 4절을 어느 절에서 채우는지 안내한다. 이 폴더의 문서는 그 근거·초안이다.

**보조 슬라이드(공개)**: [metahomo.github.io/md-slides/miniproject5-kms](https://metahomo.github.io/md-slides/miniproject5-kms/) — 아래 4절을 17장으로 옮긴 것(2026-11-19). 원본은 [metahomo/md-slides](https://github.com/metahomo/md-slides)의 `decks/miniproject5-kms.md`이고, `main`에 push하면 사이트에 반영된다.

요구사항 원문: [과제 브리프](../sources/project-brief.md#발표에-반드시-담을-것). 각 절은 `slide-section` 템플릿을 따른다.

| 순서 | 절 | 구분 | 상태 |
|---|---|---|---|
| 1 | [아키텍처 설계의 이유와 Flow](./01-architecture-why-flow.md) | 필수 | draft |
| 2 | [AI 활용 방식](./02-ai-usage.md) | 필수 | draft |
| 3 | [강의 대비 개선점](./03-improvements.md) | 옵션 | draft |
| 4 | [AI에게 서비스 제공하기](./04-service-for-ai.md) | 옵션 | draft |
| 5 | [시연 대본](./05-demo-script.md) | 시연 | draft |
| 6 | [예상 질문과 답](./06-qa.md) | 질의응답 | draft |

## 발표 원칙

- 도메인 설명은 짧게, 기술 선택의 **이유**에 시간을 쓴다.
- 모든 "왜"는 [결정 기록](../decisions/index.md)의 ADR에서, 모든 "어떻게 AI를"는 [AI 활용 기록](../ai-usage/index.md)에서 가져온다 — 발표용으로 새로 지어내지 않는다.
- 시연은 R1~R5 흐름 하나(코드 변경 → 배포, 데이터 변경 → 학습·게이트 → 승격 → 롤백)로 묶는다.
