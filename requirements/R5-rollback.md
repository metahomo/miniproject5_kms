---
title: R5 롤백 지원
description: 코드와 모델을 각각 이전 버전으로 되돌리고 다시 앞으로 돌릴 수 있다
tags:
  - requirement
  - rollback
id: R5
status: todo
---
# R5 롤백 지원

## 요구사항

"롤백 지원" — [과제 브리프](../sources/project-brief.md) 5번.

## 강의 근거

[강의 자료 색인](../sources/lecture-index.md#필수-기능과-강의-절-대응): 03 › 5 되돌리기.

## 설계

[아키텍처 개요](../architecture/overview.md#롤백) — 코드 판·모델 판 각각의 되돌리기.

## 완료 기준 (초안)

- [ ] 모델을 직전 승격 버전으로 되돌리는 워크플로(수동 실행)
- [ ] 코드를 직전 배포 버전으로 되돌리는 방법
- [ ] 되돌린 뒤 `/health` 로 버전 확인, 다시 앞으로 돌리기도 확인
- [ ] 런북: [롤백](../runbooks/rollback.md)

## 검증 증거

| 날짜 | 무엇을 확인 | 결과 | 증거 |
|---|---|---|---|

## 미해결

- 버전 이력을 몇 개까지 보관할지
