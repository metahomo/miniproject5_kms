---
title: README — paperclf (미니 프로젝트 5)
description: 저장소 입구 — 무엇을 하는 시스템인지, 지금 어디서 돌고 있는지, 어떻게 검증·배포·되돌리는지
tags:
  - home
---
# paperclf — 논문 적합도 분류기의 자동 학습·검증·배포·롤백

KMS(지식관리시스템)가 모은 논문을 로컬 LLM 이 판정한 결과를 **교사 라벨**로 삼아, CPU 로 도는 **학생 모델**(해싱 글자 n-gram → TF-IDF → 로지스틱 회귀, ONNX 서빙)을 학습하고, 검증을 통과한 판만 AWS Lightsail 서버에 자동으로 올린다. 미니 프로젝트 5 "ML 시스템 클라우드 배포" 과제 — [과제 브리프](./sources/project-brief.md).

**지금 운영 중**: <https://nlpwizard.eta.pyhub.kr> (최종 — 첫 화면 KMS 웹, API 는 `/health`·`/predict`·`/model`·`/mcp`) · <https://54-252-22-31.sslip.io/health> (작업용) — app `v0.1.6` · model `m20261120-24`, 2026-11-20

| 주소 | 상태 |
|---|---|
| 작업용 서버 <https://54-252-22-31.sslip.io> | R1~R5 모두 여기서 실행·확인 — 게이트 F1 0.9609, parity 5.5e-7, 시험 87개 |
| 최종 서버 <https://nlpwizard.eta.pyhub.kr> | **운영 중** — 연구자 계정 Lightsail(고정 IP 54.253.32.153), 러너 `paperclf-final`, `FINAL_ENABLED=true` 로 태그 하나가 두 서버에 배포(PR [#45](https://github.com/metahomo/miniproject5_kms/pull/45)·[#56](https://github.com/metahomo/miniproject5_kms/pull/56)) |
| KMS 웹 <https://nlpwizard.eta.pyhub.kr> | **과제 도메인 첫 화면**(2026-11-20 연구자 결정) — HTTPS + 접속 암호(basic auth). Mac KMS → 역방향 SSH 터널 → 최종 서버 Caddy. 같은 화면: <https://kms.54-253-32-153.sslip.io> · 작업용 <https://kms.54-252-22-31.sslip.io>(PR [#51](https://github.com/metahomo/miniproject5_kms/pull/51)) |
| API 소개 화면·`/docs` <https://54-253-32-153.sslip.io> | 최종 서버의 paperclf 전체(과제 도메인 첫 화면이 KMS 로 바뀌어 여기로) |

## 한 줄 흐름

```text
코드 변경 → PR 시험 → v* 태그 → 이미지(GHCR) → 서버 교체 → /health 확인 (실패하면 직전 판으로 자동 복귀)
데이터 변경 → 학습 → 게이트(F1) → ONNX → parity(서빙 이미지와 1e-5) → 버킷 → 서버 → current.json → 장부·백업
되돌리기 → rollback.yml(모델 판) · 직전 태그 ci 재실행(코드)
```

## 필수 기능 (R1~R5)

| # | 기능 | 상태 | 증거 |
|---|---|---|---|
| R1 | Lightsail 인스턴스·버킷 | 인스턴스·버킷(키 없이 읽고 씀) ✔ — 22번 닫기·정리 남음 | [R1](./requirements/R1-lightsail.md) |
| R2 | CI/CD — 시험 거쳐 서버까지 | ✔ | [v0.1.1 배포](https://github.com/metahomo/miniproject5_kms/actions/runs/44513840582) |
| R3 | 새 데이터 자동 학습·검증 | ✔ 게이트·parity 실패 시 승격 안 됨, 실행마다 장부 1건 | [게이트 차단](https://github.com/metahomo/miniproject5_kms/actions/runs/44515846566) · [parity 차단](https://github.com/metahomo/miniproject5_kms/actions/runs/44519475156) · [새 데이터 자동 재학습 m20261120-17](https://github.com/metahomo/miniproject5_kms/actions/runs/44643935701) |
| R4 | 통과 모델 API 서버 배포 | ✔ | [승격 m20261119-11](https://github.com/metahomo/miniproject5_kms/actions/runs/44519470540) · [승격 m20261120-17](https://github.com/metahomo/miniproject5_kms/actions/runs/44643935701) |
| R5 | 롤백 | ✔ 모델·코드 모두 되돌리고 다시 앞으로(모델 되돌리기 실행 약 20초, health 실패 시 자동 복귀 37초) | [→7](https://github.com/metahomo/miniproject5_kms/actions/runs/44514983743) · [→8](https://github.com/metahomo/miniproject5_kms/actions/runs/44515052182) |

진행판: [Projects 칸반](https://github.com/users/metahomo/projects/12) · [마일스톤](https://github.com/metahomo/miniproject5_kms/milestones) · [릴리스](https://github.com/metahomo/miniproject5_kms/releases)

## 저장소 구성

| 경로 | 내용 |
|---|---|
| `labeler/` | KMS DB(읽기 전용) → 교사 라벨 → 원문 없는 스냅숏 |
| `data/snapshots/` | 공개 학습 데이터 — 해싱 특징만, 초록 원문 없음([ADR-005](./decisions/ADR-005-student-model-snapshot.md)) |
| `paperclf/` · `training/` | 특징·라벨 규칙, 학습·게이트·ONNX 변환·모델 카드·parity |
| `skills/` | 에이전트 스킬 — [`paperclf-classify`](./skills/paperclf-classify/SKILL.md): 판정 도구를 언제·어떻게 쓰고 결과를 어떻게 읽는지 |
| `api/` | FastAPI 서빙(`/health` · `/predict` · `/model`), MCP 서버(`classify_paper`), 토큰 인증·사용량 제한, 예측 로그 |
| `deploy/lightsail/` | 서버 스크립트(`server.sh`), compose, Caddy(HTTPS), 운영 장부 DB(`ledger/`) |
| `db/init/` | 장부 스키마(트리거가 미통과 모델의 배포 기록을 거부) |
| `.github/workflows/` | `ci`(코드 판) · `model`(모델 판) · `rollback` · `uptime`(매시간 밖에서 `/health`) |
| `runbooks/` | [배포](./runbooks/deploy-code.md) · [승격](./runbooks/promote-model.md) · [롤백](./runbooks/rollback.md) · [작업용 서버](./runbooks/work-server.md) · [자원 정리](./runbooks/teardown.md) · [예상 질문](./presentation/06-qa.md) |
| `decisions/` · `architecture/` | [결정 기록(ADR)](./decisions/index.md) · [아키텍처 개요](./architecture/overview.md) |
| `experiments/` · `ai-usage/` · `presentation/` | [학습 실행 기록](./experiments/index.md) · [AI 활용 기록](./ai-usage/index.md) · [발표](./presentation/index.md) |

## 로컬에서

```sh
uv sync --locked --group train        # Python 3.12, uv
uv run --locked --group train pytest  # 시험(외부 네트워크 차단)
uv run --locked --group train python -m training.train && uv run --locked python -m training.validate_model
MODEL_DIR=artifacts uv run uvicorn api.app:app --port 8080   # 로컬 서빙
```

## 공개 API

- `GET /health` — 상태, app·model 판, 보호·예측 로그 건수(공개)
- `POST /predict` — `{"title": …, "abstract": …}` → `p_include` · `label`(include/exclude/uncertain) · `model_version`. `Authorization: Bearer <토큰>` 필요, IP 하나당 분당 60번
- `GET /model` — 운영 모델 카드
- `POST /mcp` — 원격 MCP(JSON-RPC 2.0, 도구 `classify_paper`). `/predict` 와 같은 토큰·사용량 제한. 표준 입출력 판은 `uv run python -m api.mcp_server`

토큰·DB 비밀번호는 서버 `.env` 에만 있고 저장소에는 없다. 예측 입력 원문은 저장하지 않는다(해시·길이·점수만).

## 지침

이 저장소는 AI(Claude Code)가 사령관·부관 구조로 만들고 사람이 결정·검수했다 — [사령관 지침](./CLAUDE.md) · [부관 지침](./AGENTS.md) · [AI 활용 방식](./presentation/02-ai-usage.md).
