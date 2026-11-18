---
title: R2 GitHub CI/CD
description: 코드 변경이 GitHub Actions 테스트를 거쳐 Lightsail 서버까지 자동 배포된다
tags:
  - requirement
  - cicd
  - github-actions
id: R2
status: todo
---
# R2 GitHub CI/CD

## 요구사항

"깃허브 CI/CD - 코드 변경이 테스트를 거쳐 서버까지" — [과제 브리프](../sources/project-brief.md) 2번.

## 강의 근거

[강의 자료 색인](../sources/lecture-index.md#필수-기능과-강의-절-대응): 02 › CI/CD·태그 배포, 03 › 2·3 코드 배포(SSH 방식 → 자체 호스팅 러너 방식).

## 설계

[아키텍처 개요](../architecture/overview.md#코드-판) — 코드 판.

## 완료 기준 (초안)

- [ ] PR에서 테스트 워크플로가 돌고, 실패하면 배포되지 않음
- [ ] 배포 트리거(예: 태그)가 테스트 통과 뒤 서버에 반영되고 `/health` 로 확인
- [ ] 비밀값은 저장소 시크릿·변수에만 둔다
- [ ] 런북: [코드 배포](../runbooks/deploy-code.md)

## 검증 증거

| 날짜 | 무엇을 확인 | 결과 | 증거 |
|---|---|---|---|

## 미해결

- 배포 방식(GitHub 러너 + SSH / 자체 호스팅 러너) 선택
