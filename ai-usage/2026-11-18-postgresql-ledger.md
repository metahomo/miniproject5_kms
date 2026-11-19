---
title: AI 활용 — PostgreSQL 장부 DB 설계·기동
description: 모델·배포·예측 장부 스키마를 AI가 설계하고 로컬 컨테이너로 띄워 트리거까지 시험한 기록
tags:
  - ai-usage
date: 2026-11-18
requirement: R3, R4, R5
tool: Claude Code(사령관)
mode: delegate
---
# AI 활용 — PostgreSQL 장부 DB 설계·기동

## 목표

모델 버전·배포 이력·예측 로그를 질의할 수 있는 장부 DB 를 만들고, 게이트·parity 미통과 모델이 배포 기록에 들어가지 못하게 DB 에서 막는다.

## 사람이 정한 것 (주도)

- 연구자 지시: "DB 는 PostgreSQL 로 생성" (용도는 지시에 없어 사령관 권장안을 적용 — [ADR-002](../decisions/ADR-002-postgresql.md))
- 계약·제약·금지 사항: 미확인 — 이 작업의 지시 원문이 기록에 없다. 상시 제약은 [사령관 지침](../CLAUDE.md) 1절("실행은 연구자의 지시 뒤에만", "커밋·푸시는 명령할 때만") (연구자 위임 초안)
- 검수 기준: 스키마는 시스템 카탈로그 조회로 테이블 4·뷰 2·트리거 존재, 트리거는 트랜잭션 안 시험 후 `ROLLBACK` 으로 미통과 모델 배포 거부와 0행 복귀, 비밀값은 `git check-ignore` 로 확인(아래 표) (연구자 위임 초안)

## AI에게 맡긴 것

| 일 | 산출물 |
|---|---|
| 선택지 비교(버킷 JSON · SQLite · PostgreSQL)와 결정 기록 | [ADR-002](../decisions/ADR-002-postgresql.md) |
| 테이블 4·뷰 2·트리거 설계, 버킷과의 역할 분담 | [데이터 모델](../architecture/data-model.md), `db/init/001_schema.sql` |
| 로컬 컨테이너 구성(`postgres:18.7`, `127.0.0.1:5433`) | `db/compose.yml`, `db/.env.example` |
| 트리거 거부 시험 | 아래 표 |

## 결과와 검수

| AI 산출물 | 사령관이 확인한 방법 | 연구자 검수 |
|---|---|---|
| 스키마 | 시스템 카탈로그 조회: 테이블 4, 뷰 2, 트리거 `deployments_validated` |  |
| 트리거 | 트랜잭션 안에서 시험 후 `ROLLBACK`: 게이트 미통과 모델 배포 → `ERROR: model m20261118-1 has not passed gate and parity`, 통과 모델 → `INSERT 0 1`·`current_model` 에 표시, 되돌린 뒤 세 테이블 0행 |  |
| 비밀값 | `db/.env` 가 `.gitignore` 에 걸리는지 `git check-ignore` 로 확인 |  |

## 배운 점 / 다음엔
