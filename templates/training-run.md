---
title: "학습 실행 YYYY-MM-DD"
description: "데이터 버전과 승격 여부 한 줄"
tags: [experiment, model]
date: YYYY-MM-DD
model_version: 
data_version: 
trigger: data-change  # data-change | manual | schedule
gate: pending  # pass | fail | pending
parity: pending  # pass | fail | pending
promoted: false
---

# 학습 실행 YYYY-MM-DD

## 입력

| 항목 | 값 |
|---|---|
| 데이터 위치(버킷 키) |  |
| 코드 커밋 |  |
| 워크플로 실행 |  |

## 지표와 게이트

| 지표 | 현재 운영 모델 | 새 모델 | 기준 | 판정 |
|---|---|---|---|---|

## parity (원본 모델 ↔ 배포 형식 예측 일치)

| 표본 수 | 최대 오차 | 허용 오차 | 판정 |
|---|---|---|---|

## 결정

승격 / 보류 — 근거:
