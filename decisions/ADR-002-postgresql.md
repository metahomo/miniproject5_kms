---
title: ADR-002 모델·예측 장부 DB 로 PostgreSQL 을 쓴다
description: 모델 레지스트리·배포 이력·예측 로그를 PostgreSQL 18 에 둔다. KMS DB 는 이관하지 않는다
tags:
  - adr
  - database
status: accepted
date: 2026-11-18
decider: "연구자(지시: PostgreSQL 로 생성)"
---
# ADR-002 모델·예측 장부 DB 로 PostgreSQL 을 쓴다

## 배경

연구자가 2026-11-18 "DB 는 PostgreSQL 로 생성"을 지시했다. 용도는 지시에 없었으므로 사령관이 권장안(미니 프로젝트 전용 장부)을 적용했다. KMS 의 SQLite 이관은 상위 규칙(DB 불가침)이 풀리지 않아 범위에서 뜬다.

## 선택지

| 선택지 | 장점 | 단점 |
|---|---|---|
| 버킷의 JSON 파일만 (강의 방식) | 추가 구성 요소 없음 | 이력 조회·집계가 어렵고 예측 로그를 두기 나쁨 |
| SQLite | 파일 하나 | API 컨테이너·runner · 학습 잡이 동시에 쓰기 어렵다 |
| **PostgreSQL 18** | 동시 쓰기, 제약조건·뷰로 "운영 중인 판"을 질의로 얻음, 강의 01 6.7절에서 다룸 | 컨테이너 하나와 백업 절차가 늘어난다 |

## 결정

PostgreSQL 18 을 **장부**로 쓴다. 설계는 [데이터 모델](../architecture/data-model.md).

- 개발: 내 PC Docker, `127.0.0.1:5433` (이미 다른 PostgreSQL 이 5432 를 쓴다).
- 운영: 미정 — 권장안은 같은 Lightsail 인스턴스의 compose 컨테이너 + 버킷으로 정기 백업.

## 근거 (연구자의 언어로 채울 칸)


## 영향

- 모델 파일과 `current.json` 은 계속 버킷에 둔다. 서버가 읽는 정본은 버킷, DB 는 이력·조회용 장부다.
- 롤백은 DB 의 배포 이력에서 직전 판을 찾고, 버킷 `current.json` 을 마지막에 바꾼다.
