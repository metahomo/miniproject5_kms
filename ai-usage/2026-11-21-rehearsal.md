---
title: AI 활용 — 발표 총연습(R1~R5·KMS 연구 보고서를 운영 서버에서 실제로)
description: 시연 대본 순서대로 코드 변경 PR 부터 롤백·장부·연구 보고서까지 실제로 돌리고, 실행 시간·화면·증거로 발표 자료와 조감도를 고친 기록
tags:
  - ai-usage
date: 2026-11-21
requirement: R1, R2, R3, R4, R5
tool: Claude Code(사령관) + gh CLI + 로컬 LLM(교사·보고서) + 서브에이전트 1
mode: delegate
---
# AI 활용 — 발표 총연습

## 목표

시연 대본([presentation/05](../presentation/05-demo-script.md)) 순서대로 R1~R5 를 운영 서버(작업용·최종)에서 실제로 돌려, 걸린 시간·화면·증거로 발표 자료를 고치고 7분 안에 들어가는지 잰다.

## 사람이 정한 것 (주도)

- 연구자 지시(2026-11-21): "발표 총연습을 끝까지 해. 시연 대본(presentation/05) 순서대로 R1~R5를 운영 서버에서 실제로 돌려 … 끝나면 7분 안에 들어가는지 재고, 귀가 후 확인 목록 중 사령관이 결정 없이 할 수 있는 것은 처리하고 결정이 필요한 것만 체크리스트로 줘."
- 

## AI에게 맡긴 것

| 일 | 산출물 |
|---|---|
| 코드 변경(`/health` 에 `started_at`)·시험·PR·태그 배포 | PR #63, 태그 `v0.1.7` |
| KMS 새 논문 3,511편 교사 라벨·스냅숏 | PR #64, `data/snapshots/coaching-leadership-20261121.jsonl.gz` |
| 게이트·parity 차단, 승격, 롤백, 코드 되돌리기, 장부 조회 | Actions 실행 8건(대본 2-1절 표) |
| KMS 연구 보고서 생성 | 보고서 `261121-1442` |
| 실행 시간 실측·7분 시간표·대본 결함 수정 | [대본](../presentation/05-demo-script.md) 2-1·3절, 화면 [img/rehearsal-20261121](../presentation/img/rehearsal-20261121/) |
| 학습 실행 기록 3건(서브에이전트) | [experiments](../experiments/index.md) m20261121-27·28·30 |

## 결과와 검수

| AI 산출물 | 사령관이 확인한 방법 | 연구자 검수 |
|---|---|---|
| 코드 변경 | 로컬 pytest 통과, PR 검사 통과, 두 서버 `/health` 의 `app_version`·`started_at` |  |
| 승격·롤백 | 두 서버 `/health` 의 `model_version`, 장부 `ledger.py status` |  |
| 스냅숏 원문 없음 | 스냅숏에서 `title`·`abstract` 키 0건(grep) |  |
| 7분 시간표 | 실측 실행 시간으로 누적 계산(대본 3절) |  |
