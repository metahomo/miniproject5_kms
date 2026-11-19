---
title: R2 GitHub CI/CD
description: 코드 변경이 GitHub Actions 테스트를 거쳐 Lightsail 서버까지 자동 배포된다
tags:
  - requirement
  - cicd
  - github-actions
id: R2
status: done
---
# R2 GitHub CI/CD

## 요구사항

"깃허브 CI/CD - 코드 변경이 테스트를 거쳐 서버까지" — [과제 브리프](../sources/project-brief.md) 2번.

## 강의 근거

[강의 자료 색인](../sources/lecture-index.md#필수-기능과-강의-절-대응): 02 › CI/CD·태그 배포, 03 › 2·3 코드 배포(SSH 방식 → 자체 호스팅 러너 방식).

## 설계

[아키텍처 개요](../architecture/overview.md#코드-판) — 코드 판.

## 완료 기준

- [x] PR에서 테스트 워크플로가 돌고, 실패하면 배포되지 않음 — deploy 잡은 `needs: image`(← test), 태그·`DEPLOY_ENABLED` 일 때만
- [x] 배포 트리거(예: 태그)가 테스트 통과 뒤 서버에 반영되고 `/health` 로 확인 — v0.1.1 test·image·deploy 성공, `https://54-252-22-31.sslip.io/health` → app_version v0.1.1
- [x] 비밀값은 저장소 시크릿·변수에만 둔다 — `GITHUB_TOKEN`·서버 `.env` 뿐
- [x] 런북: [코드 배포](../runbooks/deploy-code.md)

## 검증 증거

| 날짜 | 무엇을 확인 | 결과 | 증거 |
|---|---|---|---|
| 2026-11-19 | `v0.1.0` 태그 실행(ci.yml) | test ✓ · image ✓ · deploy 건너뜀(`DEPLOY_ENABLED` 꺼짐) | [실행 44453216170](https://github.com/metahomo/miniproject5_kms/actions/runs/44453216170), 이미지 `ghcr.io/metahomo/miniproject5_kms/paperclf-api:v0.1.0` |
| 2026-11-19 | `v0.1.1` 태그 → test·image·deploy, 밖에서 HTTPS `/health` | 전부 성공, app_version v0.1.1 | [실행 44513840582](https://github.com/metahomo/miniproject5_kms/actions/runs/44513840582), https://54-252-22-31.sslip.io/health |
| 2026-11-19 | 이후 `v0.1.2`(예측 로그)·`v0.1.3`(공개 API 토큰 인증·분당 60 제한) | 같은 길로 배포 | 이슈 #2 닫음 |

## 미해결

- ~~배포 방식(GitHub 러너 + SSH / 자체 호스팅 러너) 선택~~ → self-hosted 러너(`deploy/lightsail/bootstrap.sh` ④, `.github/workflows/ci.yml` `deploy` 잡) — [ADR-009](../decisions/ADR-009-ledger-writer.md)
