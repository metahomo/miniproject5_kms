---
title: AI 활용 — GitHub 진행 관리 구성과 조감도
description: 라벨·마일스톤·이슈·Discussions 를 AI가 구성하고 조감도에 GitHub 기능을 세분화해 제시한 기록
tags:
  - ai-usage
date: 2026-11-18
requirement: R2
tool: Claude Code(사령관) + gh CLI + Claude Docs
mode: delegate
---
# AI 활용 — GitHub 진행 관리 구성과 조감도

## 목표

진행 상황을 GitHub 기능으로 관리하고(완성 = Kanban Board 의 모든 카드 Done), 조감도에서 기능별 쓰임과 현재 상태를 한눈에 보이게 한다.

## 사람이 정한 것 (주도)

- 연구자 지시: GitHub 가 진행판, Kanban Board 완성 = 프로젝트 완성, GitHub 기능 전체 사용, 조감도의 GitHub 기능을 더 세밀하게 제시 — [사령관 지침](../CLAUDE.md) 8절
- 계약·제약·금지 사항: (연구자가 채울 것)
- 검수 기준: (연구자가 채울 것)

## AI에게 맡긴 것

| 일 | 산출물 |
|---|---|
| 라벨 8·마일스톤 6(단계 0~5, 문 조건)·이슈 16 생성, Discussions 공지 | 저장소 `metahomo/miniproject5_kms` |
| 지침 8절(기능별 쓰임) 작성 | [사령관 지침](../CLAUDE.md) |
| 조감도 "GitHub 조감도" 절: 칸반 그림, 기능 10개 × 7열 표 | claude.ai 조감도 문서 |
| 이슈 #1(R1)을 마일스톤 "2 서버 배포"로 이동 | 이슈 #1 |

## 결과와 검수

| AI 산출물 | 사령관이 확인한 방법 | 연구자 검수 |
|---|---|---|
| 이슈·마일스톤 | `gh issue list`, `gh api .../milestones` 출력으로 개수·배정 확인 |  |
| 조감도 표의 현재 상태 칸 | 라벨 18, 보호 규칙 없음, 워크플로·릴리스·PR 0, Discussions 범주 6 을 `gh` 조회 결과에서만 옮김 |  |

## 배운 점 / 다음엔

- 이 앱(OpenKnowledge, ACP) 채팅에서는 체크박스·선택창이 동작하지 않아, 결정은 번호로 답받는다.
