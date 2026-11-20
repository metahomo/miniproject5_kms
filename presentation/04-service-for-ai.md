---
title: 발표 — AI에게 서비스 제공하기
description: 사람이 아니라 AI 에이전트가 쓴다면 예측 API를 어떤 방식으로 제공할지 (옵션)
tags:
  - presentation
required: false
status: draft
---
# 발표 — AI에게 서비스 제공하기

## 핵심 메시지 (내 언어로)

(연구자 위임 초안) AI 가 쓰는 서비스는 사람이 쓰는 서비스보다 "약속"이 더 단단해야 한다. AI 는 화면을 보고 눈치로 고치지 못하고, 받은 응답을 그대로 다음 판단에 쓰기 때문이다. 그래서 같은 예측 함수를 세 겹으로 내놓는다 — 어떤 프로그램이든 부를 수 있는 REST + OpenAPI(이미 있음), 에이전트가 도구로 바로 고르는 MCP 서버(로컬 판 구현 중), 언제·어떻게 쓰는지 알려 주는 스킬 문서(`skills/paperclf-classify`). 세 겹 모두 입·출력 스키마를 고정하고, 응답에 모델 판과 확률·임계값을 함께 실어 AI 가 결과를 얼마나 믿을지 스스로 판단하게 한다.

## 검토할 방식

선택은 [결정 기록](../decisions/index.md)에 ADR로 남긴다(아직 ADR 없음 — 아래는 검토안).

| 방식 | AI 쪽에서 보는 모습 | 장점 | 단점 | 이 프로젝트 적용 |
|---|---|---|---|---|
| REST API + 기계가 읽는 명세(OpenAPI) | `/openapi.json` 을 읽어 경로·필드·형식을 알고, HTTP 요청(`POST /predict`)을 직접 만든다 | 언어·도구를 가리지 않는 표준. 사람·프로그램·AI 가 같은 주소를 쓴다. 명세를 코드에서 자동 생성해 문서와 구현이 어긋나지 않는다 | 에이전트가 "언제 이 API 를 써야 하는지"는 명세에 없다. 호출 코드를 AI 가 만들어야 하고, parity 용 `features` 같은 내부 필드까지 보인다 | 있음 — FastAPI 가 `/docs`·`/openapi.json` 을 자동 제공(`api/app.py`, `FastAPI(title="paperclf")`). 경로는 `/health` · `/predict` · `/model` 셋. 공개 조건 HTTPS 는 켜졌다(`https://54-252-22-31.sslip.io`), 인증·사용량 제한은 아직 없다([ADR-003](../decisions/ADR-003-domain-server.md)) |
| MCP 서버(도구로 노출) | 도구 목록에 `classify_paper` 하나가 이름·설명·입력 스키마와 함께 뜨고, 에이전트가 대화 중에 골라 부른다 | 도구 설명이 "언제 쓰는지"까지 알려 준다. 입력을 `title`·`abstract` 로 좁혀 내부 필드를 숨긴다. 결과가 구조화(`structuredContent`)되어 바로 다음 판단에 쓴다. 읽기 전용 표시(`readOnlyHint`) | MCP 를 지원하는 클라이언트에서만 쓴다. 로컬 stdio 판은 그 컴퓨터 안에서만 돈다. 원격 판은 인증·전송 구성이 더 필요하다 | 구현 중 — 로컬 stdio 서버 `api/mcp_server.py`(한 줄에 JSON-RPC 2.0 메시지 하나). 도구 `classify_paper`: 입력 `title`(필수, ≤1000자)·`abstract`(≤20000자), 출력 `p_include`·`label`·`model_version`·`thresholds`(+`feature_version`). 모델은 HTTP 를 거치지 않고 `api.app` 의 같은 모델을 프로세스 안에서 쓴다. 원격 판은 아직 없다(서버 HTTPS 는 켜졌고, 인증·전송 구성이 남았다). 구조는 KMS 본체 MCP(`kms/mcp/`, stdio, 도구 5개)를 따랐다 |
| 에이전트 스킬(사용법 문서) | 에이전트가 작업에 맞는 스킬 문서를 불러와 "이 도구를 언제, 어떤 순서로, 결과를 어떻게 읽는지"를 읽는다 | 가장 싸다 — 코드 없이 문서 하나. 임계값 해석(uncertain 이면 사람에게 넘기기 등)·주의점 같은 운영 지식을 전한다 | 스스로는 아무것도 실행하지 못한다 — REST 나 MCP 가 있어야 한다. 문서가 코드와 어긋나도 자동으로 잡히지 않는다 | 있음 — [`skills/paperclf-classify/SKILL.md`](../skills/paperclf-classify/SKILL.md)(2026-11-19): 언제 쓰나·부르는 길 셋·결과 읽기(uncertain 은 사람에게)·오류 표·실제 응답 예 |

## AI 사용자를 위한 설계 고려

- **입력·출력 스키마 고정**: REST 는 pydantic 모델(`Paper` · `Prediction`)이 곧 OpenAPI 명세다. MCP 도구는 `inputSchema`·`outputSchema` 를 선언하고 `additionalProperties: false` 로 모르는 인자를 받지 않는다. 길이 한도는 두 쪽이 같다(title 1000자, abstract 20000자).
- **모델 버전·확신도 표시**: 응답마다 `model_version` 을 실어 어떤 판이 답했는지 남긴다(롤백 뒤에도 추적 가능). 확신도는 `p_include` 확률 그대로 주고, MCP 는 `thresholds`(include ≥ 0.7, exclude ≤ 0.3 — `paperclf/labels.py`, KMS 와 같은 값)를 함께 줘서 AI 가 `uncertain` 구간을 스스로 해석하게 한다. 단, 이 확률은 교사(LLM)와의 일치를 배운 값이다(ADR-005·ADR-006).
- **오류 형식**: MCP 는 인자 오류를 JSON-RPC 프로토콜 오류 `-32602`(Invalid params)로, 모델이 없을 때는 도구 결과 `isError: true` + `structuredContent.code = "no_model"` 로 돌려준다. 어떤 요청이 실패해도 프로세스는 다음 줄을 계속 읽는다. REST 는 입력 검증 실패 시 FastAPI 기본 422, 모델 없음은 503, `/health` 의 `status` 는 `ok`/`no_model`.
- **인증·사용량 제한**: 있다(v0.1.3~). 공개 조건이던 HTTPS(ADR-003)는 켜졌고(`https://54-252-22-31.sslip.io`, Let's Encrypt), REST `/predict` 는 v0.1.3 부터 **토큰 인증**(`Authorization: Bearer`, 토큰은 서버 `.env` 에만)과 **IP 별 사용량 제한**(분당 60, 넘으면 `429` + `Retry-After`)을 거친다 — 실제 요청으로 401·200·429 확인(PR #30). `/health` 는 공개, 거절 건수가 보인다. 원격 MCP 도 v0.1.4 부터 같은 보호 뒤에 연다 — `POST /mcp`(JSON-RPC 2.0, JSON 응답 방식, 도구 `classify_paper`, 처리는 표준 입출력 판과 같은 `handle`). 예측은 원문 없이 해시·길이·점수만 장부에 남는다(v0.1.2).

## 슬라이드 원고

보조 슬라이드 [15–16장](https://metahomo.github.io/md-slides/miniproject5-kms/)에 맞춘 말하기 원고. 16장 표의 MCP 칸("마감 단계 계획")과 발표자 메모("구현된 것은 세 경로뿐")는 로컬 MCP 서버 구현 뒤 슬라이드 쪽을 고쳐야 한다.

| # | 제목 | 내용 | 그림·시연 |
|---|---|---|---|
| 15 | 4. AI에게 서비스 제공하기 | 장 표지. "이 판정기를 사람이 아니라 AI 에이전트가 쓴다면?" 질문으로 넘어간다 | 표지 슬라이드 |
| 16-1 | 사람 대신 AI가 쓴다면 — 세 방식 | REST + OpenAPI 는 이미 있다(FastAPI 가 `/openapi.json` 자동 생성). MCP 는 도구 `classify_paper` 하나를 로컬 stdio 로 낸다 — 제목·초록을 넣으면 확률·라벨·모델 판·임계값이 온다. 스킬 문서는 계획 | 16장 표. 시연(가능하면): 로컬에서 `tools/call` 한 줄 → 응답 JSON |
| 16-2 | AI 사용자를 위한 설계 | 스키마 고정, 응답에 모델 판과 확률, 오류는 `-32602`·`no_model` 처럼 일정한 형식, 인증·사용량 제한은 아직 없다(HTTPS 는 켜짐) — 붙이기 전엔 원격 판을 열지 않는다 | 16장 하단 굵은 줄 |

## 예상 질문과 답

| 질문 | 답 | 근거 |
|---|---|---|
| REST 가 있는데 MCP 를 왜 또 만드나? | 같은 모델을 쓰지만 AI 에게 보이는 모습이 다르다. MCP 는 도구 설명과 스키마가 에이전트의 도구 목록에 바로 뜨고, 입력을 `title`·`abstract` 로 좁혀 parity 용 `features` 같은 내부 필드를 숨긴다 | `api/mcp_server.py`, `api/app.py` |
| 지금 외부의 AI 가 이 서비스를 쓸 수 있나? | 아니다. MCP 는 로컬 stdio 판이다. 서버 HTTPS 는 켜졌지만 원격 판·인증·사용량 제한이 아직 없다. 원격 판은 인증 뒤다 | ADR-003, [자율 진행 보고서](../reports/2026-11-19-autonomous-progress.md) 2·4절 |
| AI 가 확률을 잘못 믿으면? | 확률만이 아니라 `label` 과 `thresholds` 를 같이 줘서 0.3~0.7 은 `uncertain` 으로 드러난다. `model_version` 으로 어떤 판의 답인지도 남는다. 다만 이 확률은 교사(LLM) 판정과의 일치를 배운 값이다 | `paperclf/labels.py`, ADR-005·ADR-006 |
| LLM 교사를 직접 MCP 로 내면 더 정확하지 않나? | 서빙할 Lightsail 에 GPU 가 없다. 비싼 판단은 PC 에서 한 번 하고, 배운 학생 모델(F1 0.9603)을 싸게 서빙하는 것이 이 프로젝트의 구조다 | ADR-005, 03 개선점 #8 |
| KMS 의 MCP 와는 어떤 관계인가? | KMS 본체 MCP 는 지식베이스 질의 도구 5개(`ask_kms`·`search_works`·`get_work`·`list_topics`·`get_topic_journals`)를 stdio 로 낸다. 이번 서버는 판정 도구 하나지만 같은 구조(한 줄 JSON-RPC, 표준 출력에는 프로토콜만, 실패해도 계속 읽기)를 따랐다. 타당성 보고서도 KMS 의 MCP 경험을 이 절에 쓸 강점으로 꼽았다 | `~/miniproject-kms/kms/mcp/`, [KMS 활용 타당성 보고서](../reports/2026-11-18-kms-feasibility.md) 3절 |
| 남용·비용은 어떻게 막나? | 토큰 인증과 IP 별 분당 60회 제한(API 안, `api/guard.py`). 기본 Caddy 에는 사용량 제한 모듈이 없어 API 에 넣었다. 예측 로그로 얼마나 불렸는지 장부에서 본다 | PR #30, `runbooks/deploy-code.md`, ADR-003 |
