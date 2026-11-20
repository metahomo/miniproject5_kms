---
title: ADR-003 서비스 도메인과 서버
description: 도메인 nlpwizard.eta.pyhub.kr, 서버 IP 13.237.237.56 으로 한다. 2026-11-18 현재 HTTPS 미설정
tags:
  - adr
  - infra
  - domain
status: accepted
date: 2026-11-18
decider: 연구자
---
# ADR-003 서비스 도메인과 서버

## 결정

연구자 지시(2026-11-18): 도메인은 **`nlpwizard.eta.pyhub.kr`**, 서버는 **`13.237.237.56`** 으로 한다.

## 갱신 (2026-11-20)

- 도메인은 그대로, **서버는 `54.253.32.153`**(연구자 프로젝트 계정 Lightsail, 고정 IP `paperclf-final-ip`)으로 바뀌었다. 연구자가 A 레코드를 바꿨다(2026-11-20 16:46 HTTPS 개통). `13.237.237.56` 은 처음부터 우리 열쇠가 없던 서버였다.
- 첫 화면은 KMS 웹(접속 암호), `/health`·`/predict`·`/model`·`/mcp` 는 paperclf — [최종 서버 런북](../runbooks/final-server.md), `deploy/lightsail/caddy/Caddyfile`.

## 확인한 현재 상태 (2026-11-18, 사령관이 읽기 전용으로 확인)

| 항목 | 결과 | 확인 방법 |
|---|---|---|
| DNS A 레코드 | `nlpwizard.eta.pyhub.kr` → `13.237.237.56` | `nslookup` |
| HTTP 80 | 응답함 | `curl` |
| HTTPS 443 | 연결은 되지만 TLS 핸드셰이크 실패 — 인증서 미발급 | `curl -v` |

## 근거 (연구자의 언어로 채울 칸)


## 영향

- [R1](../requirements/R1-lightsail.md)의 인스턴스·고정 IP 는 이미 있다. 새로 만들지 않고 이 서버를 쓴다.
- HTTPS(Caddy · Let's Encrypt)는 5단계 작업이다. 로그인·HTTPS 없는 외부 공개는 피해야 하므로, 예측 API 를 공개하기 전에 HTTPS 를 먼저 갖추는 것을 권장한다.
