---
title: AI 활용 — 작업 점검과 저장소 추적 정리
description: 하루 작업을 AI가 점검해 빠진 기록·설정을 찾고, git 추적 대상을 정리한 기록
tags:
  - ai-usage
date: 2026-11-18
requirement: —
tool: Claude Code(사령관) + OpenKnowledge
mode: review
---
# AI 활용 — 작업 점검과 저장소 추적 정리

## 목표

오늘 작업이 지침대로 되었는지 점검하고, 저장소에 들어갈 것과 뺄 것을 정리한다.

## 사람이 정한 것 (주도)

- 연구자 선택: 스킬 사본 세 벌은 git 에서 빼고, 맨 위 `.ok/config.yml` 만 추적, 폴더별 `.ok/` 는 제외
- 검수 기준: (연구자가 채울 것)

## AI에게 맡긴 것

| 일 | 결과 |
|---|---|
| 작업 점검(변경 파일·DB·GitHub·링크) | 빠진 AI 활용 기록, 칸반 보드 권한 없음, 마일스톤 배정 어긋남, 문서 점검 미실행, 오타 발견 |
| 스킬 사본 비교 | 세 폴더 내용 동일(`diff -rq` 차이 0) |
| `.gitignore` 정리 | `.claude/skills/`·`.codex/`·`.github/skills/`·`*/.ok/` 추가, `.git/info/exclude` 의 `.ok/` 삭제 |

## 결과와 검수

| AI 산출물 | 사령관이 확인한 방법 | 연구자 검수 |
|---|---|---|
| 추적 대상 | `git check-ignore -v`, `git status` 로 의도한 파일만 남은 것 확인 |  |
| 예상 밖 영향 | `.ok/` 줄 삭제가 폴더별 템플릿 18개까지 드러낸 것을 보고하고 연구자 선택(`*/.ok/`)으로 처리 |  |

## 배운 점 / 다음엔
