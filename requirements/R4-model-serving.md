---
title: R4 통과 모델 API 서버 배포
description: 게이트·parity를 통과한 모델만 승격되어 API 서버가 그 모델로 예측한다
tags:
  - requirement
  - serving
  - api
id: R4
status: todo
---
# R4 통과 모델 API 서버 배포

## 요구사항

"통과한 모델을 api 서버로 배포" — [과제 브리프](../sources/project-brief.md) 4번.

## 강의 근거

[강의 자료 색인](../sources/lecture-index.md#필수-기능과-강의-절-대응): 02 › 모델 릴리스 자동화·ONNX, 03 › 4 모델 배포 — 다시 학습해 승격.

## 설계

[아키텍처 개요](../architecture/overview.md#모델-판) — 승격 포인터와 API 서버의 모델 적재.

AI 에게도 같은 모델 제공: MCP 도구 `classify_paper`(`api/mcp_server.py`, 로컬 stdio, 테스트 `tests/test_mcp.py`).

## 완료 기준 (초안)

- [ ] 승격된 모델 버전이 버킷에 기록되고 API 서버가 그 버전을 적재
- [ ] `/health`(또는 별도 엔드포인트)가 현재 모델 버전을 돌려줌
- [ ] 미통과 모델은 어떤 경로로도 서버에 올라가지 않음
- [ ] 런북: [모델 승격](../runbooks/promote-model.md)

## 검증 증거

| 날짜 | 무엇을 확인 | 결과 | 증거 |
|---|---|---|---|

## 미해결

- ~~모델 형식(pickle/ONNX)~~ → ONNX — [ADR-005](../decisions/ADR-005-student-model-snapshot.md)
- 교체 방식(재시작/핫 리로드)
