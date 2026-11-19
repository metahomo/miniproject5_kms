---
title: R5 롤백 지원
description: 코드와 모델을 각각 이전 버전으로 되돌리고 다시 앞으로 돌릴 수 있다
tags:
  - requirement
  - rollback
id: R5
status: done
---
# R5 롤백 지원

## 요구사항

"롤백 지원" — [과제 브리프](../sources/project-brief.md) 5번.

## 강의 근거

[강의 자료 색인](../sources/lecture-index.md#필수-기능과-강의-절-대응): 03 › 5 되돌리기.

## 설계

[아키텍처 개요](../architecture/overview.md#롤백) — 코드 판·모델 판 각각의 되돌리기.

## 완료 기준

- [x] 모델을 직전 승격 버전으로 되돌리는 워크플로(수동 실행) — `rollback.yml` → m20261119-7([실행 44514983743](https://github.com/metahomo/miniproject5_kms/actions/runs/44514983743))
- [x] 코드를 직전 배포 버전으로 되돌리는 방법 — 직전 태그 실행을 `gh run rerun` 으로 재배포, v0.1.0([실행 44453216170](https://github.com/metahomo/miniproject5_kms/actions/runs/44453216170)). 배포 중 health 실패 시 `server.sh` 가 직전 TAG 로 자동 복귀
- [x] 되돌린 뒤 `/health` 로 버전 확인, 다시 앞으로 돌리기도 확인 — 모델 →8([실행 44515052182](https://github.com/metahomo/miniproject5_kms/actions/runs/44515052182)), 코드 v0.1.1([실행 44513840582](https://github.com/metahomo/miniproject5_kms/actions/runs/44513840582))
- [x] 런북: [롤백](../runbooks/rollback.md)

## 검증 증거

| 날짜 | 무엇을 확인 | 결과 | 증거 |
|---|---|---|---|
| 2026-11-19 | 모델 직전 판으로 되돌리기(`rollback.yml`) | m20261119-7 | [실행 44514983743](https://github.com/metahomo/miniproject5_kms/actions/runs/44514983743) |
| 2026-11-19 | 모델 다시 앞으로 | m20261119-8 | [실행 44515052182](https://github.com/metahomo/miniproject5_kms/actions/runs/44515052182) |
| 2026-11-19 | 코드 직전 배포로 되돌리기(`gh run rerun`) | v0.1.0 재배포, `/health` app_version v0.1.0, 모델 m20261119-8 유지 | [실행 44453216170](https://github.com/metahomo/miniproject5_kms/actions/runs/44453216170) |
| 2026-11-19 | 코드 다시 앞으로 | v0.1.1 재배포, app_version v0.1.1 | [실행 44513840582](https://github.com/metahomo/miniproject5_kms/actions/runs/44513840582) |

## 미해결

- 버전 이력을 몇 개까지 보관할지
- ~~코드(이미지) 되돌리기 워크플로가 아직 없다 — 모델 되돌리기만 `.github/workflows/rollback.yml` 이 있다~~ → 직전 태그의 ci 실행을 다시 돌려 되돌린다(`gh run rerun`, [롤백 런북](../runbooks/rollback.md) 절차 — 코드)
