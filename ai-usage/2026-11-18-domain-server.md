---
title: AI 활용 — 도메인·서버 상태 확인
description: 지정받은 도메인·서버의 DNS·HTTP·HTTPS 상태를 AI가 읽기 전용으로 확인하고 결정으로 기록
tags:
  - ai-usage
date: 2026-11-18
requirement: R1
tool: Claude Code(사령관)
mode: review
---
# AI 활용 — 도메인·서버 상태 확인

## 목표

연구자가 정한 도메인과 서버가 실제로 연결되어 있는지 확인하고, 다음 작업(HTTPS)을 정한다.

## 사람이 정한 것 (주도)

- 연구자 지시: 도메인 `nlpwizard.eta.pyhub.kr`, 서버 `13.237.237.56` — [ADR-003](../decisions/ADR-003-domain-server.md)
- 검수 기준: (연구자가 채울 것)

## AI에게 맡긴 것

읽기 전용 확인(`nslookup`·`curl`)과 결정 기록. 서버 설정은 바꾸지 않았다.

## 결과와 검수

| AI 산출물 | 사령관이 확인한 방법 | 연구자 검수 |
|---|---|---|
| DNS A 레코드 일치 | `nslookup` |  |
| HTTP 80 응답, HTTPS 443 TLS 실패(인증서 없음) | `curl`, `curl -v` |  |
| [ADR-003](../decisions/ADR-003-domain-server.md), [R1](../requirements/R1-lightsail.md) 서버 절 | 문서 링크 확인 |  |

## 배운 점 / 다음엔
