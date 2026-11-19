---
name: paperclf-classify
description: 논문 제목·초록이 코칭 리더십(coaching-leadership) 주제에 맞는지 판정할 때 쓴다. paperclf 의 MCP 도구 classify_paper(원격 POST /mcp 또는 로컬 stdio) 또는 REST POST /predict 를 부르고, 확률·임계값·모델 판으로 결과를 해석하는 법. 논문 선별·문헌 목록 거르기·KMS 수집 결과 점검에 사용.
---

# paperclf — 논문 주제 적합도 판정 쓰는 법

## 언제 쓰나

- 논문 목록에서 "직장 안 리더·관리자가 자기 구성원에게 코칭 행동을 쓰는" 연구(주제 `coaching-leadership`)만 고를 때
- KMS 가 새로 모은 논문을 사람이 보기 전에 1차로 거를 때
- 쓰지 말 것: 다른 주제 판정, 논문 품질·인용 평가, 원문 요약 — 이 모델은 위 한 주제의 포함/제외만 배웠다

## 어떻게 부르나

| 길 | 주소 | 인증 |
|---|---|---|
| 원격 MCP | `POST https://54-252-22-31.sslip.io/mcp` (JSON-RPC 2.0, `tools/call` → `classify_paper`) | `Authorization: Bearer <토큰>` |
| REST | `POST https://54-252-22-31.sslip.io/predict` `{"title": …, "abstract": …}` | 같은 토큰 |
| 로컬 MCP | `MODEL_DIR=artifacts uv run python -m api.mcp_server` (표준 입출력) | 없음 |

- 입력: `title`(필수, 1~1000자), `abstract`(선택, 20000자까지). 다른 인자는 받지 않는다
- 초록을 넣으면 판정이 더 정확하다 — 제목만이면 확신이 낮아질 수 있다
- 사용량: IP 하나당 분당 60번. 넘으면 `429` 와 `Retry-After`(초) — 그만큼 기다렸다가 다시
- 토큰은 서버 관리자에게 받는다. 대화·코드·저장소에 붙여 넣지 않는다

## 결과 읽는 법

| 필드 | 뜻 | 쓰는 법 |
|---|---|---|
| `p_include` | 포함일 확률(0~1) | 그대로 정렬 기준으로 써도 된다 |
| `label` | `include`(≥ 0.7) · `exclude`(≤ 0.3) · `uncertain`(그 사이) | **uncertain 은 사람에게 넘긴다** — 자동으로 포함·제외하지 않는다 |
| `thresholds` | `include_at` 0.7, `exclude_at` 0.3 (MCP 만) | 임계값이 바뀌어도 이 값으로 판단한다 |
| `model_version` | 답한 모델 판(예: `m20261119-11`) | 결과를 저장할 때 같이 남긴다 — 롤백 뒤에도 어느 판의 답인지 안다 |

주의: 확률은 교사(LLM) 판정과의 일치를 배운 값이다(시험지 F1 약 0.96). 사람 검수 정답이 아니다. 중요한 결정에는 `include` 도 표본으로 사람이 확인한다.

## 오류

| 응답 | 뜻 | 할 일 |
|---|---|---|
| `401` | 토큰 없음·틀림 | 토큰 확인 |
| `429` | 사용량 초과 | `Retry-After` 초 뒤 다시 |
| `503` / MCP `isError` + `no_model` | 서버에 모델이 없다 | 잠시 뒤 다시, 계속이면 관리자 |
| JSON-RPC `-32602` | 인자 오류(빈 제목, 너무 긺, 모르는 인자) | 입력 고치기 |

## 예

```json
{"jsonrpc":"2.0","id":1,"method":"tools/call",
 "params":{"name":"classify_paper","arguments":{"title":"Executive coaching and leadership effectiveness"}}}
```

→ `structuredContent`: `{"p_include": 0.849, "label": "include", "model_version": "m20261119-11", "thresholds": {"include_at": 0.7, "exclude_at": 0.3}}` (2026-11-19 실제 응답)
