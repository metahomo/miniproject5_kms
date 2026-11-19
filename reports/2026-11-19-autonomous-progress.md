---
title: 보고서 — 2026-11-19 연구자 외출 중 자율 진행과 조감도 보충 문안
description: 전권 위임 동안 사령관이 한 일, 단계별 문 통과 여부, 막힌 것, 조감도에 옮길 문안, 오후 진행(이슈 닫기·결정 확정, 작업용 서버·AWS 정리)
tags:
  - report
date: 2026-11-19
---
# 보고서 — 2026-11-19 자율 진행

조감도(`https://claude.ai/artifact/3WMUPTn1hXPA5nzGT1mVvt`)는 Mac 서버 세션에서 읽기·쓰기 모두 거부되어 직접 고치지 못했다. 아래 "조감도 보충 문안"을 조감도에 옮기면 된다.

## 1. 진행판 (GitHub)

- 칸반보드: [miniproject5 Kanban Board](https://github.com/users/metahomo/projects/12) — 열 Backlog · Todo · In Progress · Review · Done. 이슈 #1~#16 과 PR 을 카드로 올렸다.
- 같은 날 만들어진 빈 보드 3개(#9 · #10 · #11 "untitled project")와 미니 프로젝트 4 의 "Kanban Board"(#8)는 손대지 않았다(삭제는 연구자 결정).

## 2. 단계별 문

2026-11-19 오후 기준. 문 통과 = 단계 이슈 닫힘·보드 Done(7절).

| 단계 | 문(마일스톤 설명) | 상태 | 증거 |
|---|---|---|---|
| 0 준비 | 라벨 스냅숏 1개, 시험지 확정 | ✔ 문 통과(이슈 #6 닫힘). 스냅숏 ✔, 시험지 확정([ADR-006](../decisions/ADR-006-gate-parity.md), 연구자 확정) | `data/snapshots/coaching-leadership-20261119.jsonl.gz` |
| 1 코드 판 | pytest 실패 PR 은 배포 안 됨, v* 태그 → GHCR 이미지 | ✔ 문 통과(이슈 #7 닫힘). `image` 가 `needs: test`, `v0.1.0` 태그 → GHCR `paperclf-api:v0.1.0` 공개 | [ci 실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44450941769) · [v0.1.0 태그 실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44453216170) |
| 2 서버 배포 | 밖에서 /health 응답, 밖에서 SSH 막힘 | **서버 대기** — /health 는 아직 eta(app_version v2.4), Caddy·러너 미설치 | 아래 4절 |
| 3 모델 판 | 일부러 낮춘 모델이 게이트에서 멈춤 | ✔ 문 통과(이슈 #9 닫힘). 약한 모델 F1 0.9021 게이트 실패, 정상 모델 F1 0.9603·parity 5.8e-7 | [약한 모델 실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44452096551) · [정상 실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44451897410) |
| 4 승격·롤백 | 되돌렸다 다시 앞으로 | **서버 대기**(버킷·서버). 운영 DB·백업 방식은 ADR-008 로 확정 | 워크플로만 작성 |
| 5 마감·발표 | HTTPS·MCP·발표·정리 | 진행 중 — 발표 보조 슬라이드 17장, HTTPS 는 연결 실패(서버 대기) | [슬라이드](https://metahomo.github.io/md-slides/miniproject5-kms/) |

## 3. 숫자 (2026-11-19 명령 출력)

| 항목 | 값 |
|---|---|
| KMS 수집 | 867편(OpenAlex + KCI), 초록 있음 794편 |
| 교사 라벨 | include 641 · exclude 211 · uncertain 15, 스키마 위반 0, 약 1.6편/초 |
| 분할 | 학습 674 · 게이트 178 (uncertain 제외) |
| 게이트 F1 | 0.9603 (기준선 0.8805, 통과선 0.9305) |
| 5% 데이터 모델 | F1 0.9021 → 게이트 실패 |
| ONNX 차이 | 5.4e-7 (허용 1e-5) |

## 4. 막힌 것 — 연구자가 풀어야 함

1. **서버 접근**: 13.237.237.56 은 80 에서 uvicorn 이 응답하고 22 가 열려 있으나, 이 작업 환경(Mac 서버)에는 그 서버의 SSH 키가 없다. self-hosted runner 등록(2단계)부터 막힌다.
2. **AWS**: 버킷(4단계)은 AWS 콘솔·자격 증명이 필요하다. 비용이 드는 자원이라 사령관이 만들지 않는다.
3. 풀리면: 서버에 러너를 `lightsail` 라벨로 등록 → 저장소 변수 `DEPLOY_ENABLED=true`, `MODEL_BUCKET`, `AWS_REGION` → `model` 수동 실행. 워크플로는 이미 들어 있다. (`v0.1.0` 태그는 오후에 끝남 — 7절. 리전은 ADR-007 로 시드니 `ap-southeast-2`)
4. **Docker 권한**: Mac 서버에서 `docker` 가 permission denied — 로컬 장부 DB(PostgreSQL 5433)는 여기서 못 띄운다. 이미지 빌드는 Actions 에서 한다.

## 5. 조감도 보충 문안

> **2026-11-19 진행 (연구자 외출 중, 사령관 전권)** — 작업 환경을 Mac 서버로 옮겼다. 칸반보드를 5열로 완성하고 이슈 16개를 올렸다. KMS 가 867편을 모으고 로컬 LLM(qwen3 4B)이 교사로 라벨을 붙였다. 공개 저장소에는 원문 대신 해싱 특징만 올린다. 학생 모델(해싱 TF-IDF + 로지스틱 회귀)은 게이트 F1 0.96 으로 통과하고, 데이터 5% 로 만든 약한 모델은 게이트에서 멈춘다. ONNX 와 원본의 확률 차이는 5.4e-7. ci · model · rollback 워크플로가 들어갔고, 서버 배포·승격·되돌리기 잡은 서버 접근이 생기면 변수 하나로 켠다.

조감도 "GitHub 조감도" 표에 고칠 칸: Projects = 있음(#12, 5열) · Actions = ci 실행 초록 · PR = #19 · 결정 = ADR-005 · ADR-006(확정) · ADR-007~009(오후 확정, 7절).

## 6. 연구자 확인이 필요한 것 (2026-11-19 오후 갱신)

해소

- ~~PR #19 병합~~ — 병합됨(오전에는 위임 범위에 병합이 명시되지 않아 사령관이 하지 않았다). 병합 push 로 `model` 이 main 에서 자동으로 돌아 train·parity 통과([실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44451897410)).
- ~~ADR-005 · ADR-006 의 잠정 결정 확인~~ — 둘 다 `accepted`(연구자 확정 2026-11-19). 시험지는 확정.
- ~~결정 이슈 #14 · #15 · #16~~ — 권장안으로 확정(ADR-007 · ADR-008 · ADR-009, 7절).

남음

- **서버 SSH 키·AWS 자격 증명** — 이 Mac 에 둘 다 없다. 2단계(러너·Caddy)와 4단계(버킷)가 여기서 막힌다.
- ADR 의 "근거" 칸(연구자의 언어) — ADR-005 · ADR-006 은 비어 있다. ADR-007~009 는 다른 부관이 작성 — 근거 칸 채움 여부 미확인.
- AI 활용 기록의 "연구자 검수" 열 — 사령관이 "사람이 정한 것"을 위임 초안으로 채웠다(7절). 원문 확인과 검수 열은 연구자 몫.
- 빈 Projects 보드 #9 · #10 · #11 정리 여부 — 오후에도 손대지 않음.
- 이슈 #3(R3) — 진행 댓글만. 기준 4(실행마다 기록 1건) 미충족.

## 7. 2026-11-19 오후 진행

사용자 지시(오늘): "모든 수행을 멀티로, 필요하면 모든 부관 파견, 토큰 걱정 없음", "연구자가 해야 할 일도 바로 해줘 — 중단되지 않도록".

| 일 | 결과 | 증거 |
|---|---|---|
| 단계 이슈 닫기 | #6(0 준비) · #7(1 코드 판) · #9(3 모델 판) 문 통과로 닫고 보드 Done | 위 2절 표의 실행 링크 |
| R3 진행 | 이슈 #3 에 진행 댓글만 — 기준 4 미충족 | [R3](../requirements/R3-auto-train-validate.md) |
| 결정 확정 | #14 → [ADR-007](../decisions/ADR-007-region-instance.md) 리전 시드니 `ap-southeast-2`(기존 인스턴스·버킷 같은 리전) · #15 → [ADR-008](../decisions/ADR-008-ledger-db-ops.md) 운영 DB 는 서버 compose, `pg_dump` → 버킷 매일 + 승격·롤백 직후, 14개 보관 · #16 → [ADR-009](../decisions/ADR-009-ledger-writer.md) 장부 기록은 서버 러너가 대행, 예측 로그는 API 가 localhost 로 | [결정 색인](../decisions/index.md) |
| v0.1.0 태그 | test·image 통과, GHCR `paperclf-api:v0.1.0` 공개, deploy 는 서버 대기로 건너뜀 | [실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44453216170) |
| 서버 확인 | 13.237.237.56 `/health` 는 여전히 eta(app_version v2.4, `server: uvicorn`). https 연결 실패. Caddy·러너 미설치, 저장소 변수 0개 | 사령관 명령 확인 |
| 발표 보조 | 슬라이드 17장, claude.ai 페이지(비공개) | [슬라이드](https://metahomo.github.io/md-slides/miniproject5-kms/) · `https://claude.ai/artifact/7TLMuRWcCT9w8buwWknH4q` |
| 정리 | OpenKnowledge 를 프로젝트에서 모두 제거, 템플릿은 [`templates/`](../templates/) 로 옮김(오전) | — |
| 진행 방식 | 부관 6명 병렬 조사 → 사령관이 명령으로 재확인 → 이슈 닫기·결정 확정·문서 병렬 작성 | [AI 활용 기록](../ai-usage/2026-11-19-board-and-delegation.md) |

## 8. 2026-11-19 오후 — 작업용 서버·AWS 정리

연구자가 일을 두 갈래로 나눴다.

1. **① R1~R5 는 강의 순서대로 연구자의 작업용 서버에서 한다** — Lightsail `Amazon_Linux_2026_kms`(Amazon Linux 2023, 2GB·2vCPU·60GB, `ap-southeast-2a`), 고정 IP `54.252.22.31`(`StaticIp-1`).
2. **② 교수님 사이트 `nlpwizard.eta.pyhub.kr`(`13.237.237.56`)에 최종 결과를 올리는 일은 맨 마지막에, 교수님 지시대로 따로 한다.** DNS 는 바꾸지 않는다. eta 와 Caddy 를 함께 두는 계획(PR #21)은 ②에 속해 보류.

4절의 "서버 접근"·"AWS" 막힘은 작업용 서버로 풀렸다(② 는 여전히 대기).

| 일 | 결과 | 증거 |
|---|---|---|
| 작업용 서버 | Docker 25, Compose 2.40.3, Caddy(임시 `:80 → 127.0.0.1:8080`), `/srv/paperclf`, 러너 `paperclf` 온라인. HTTPS 는 `54-252-22-31.sslip.io` 로 예정 | [작업용 서버 런북](../runbooks/work-server.md) · [R1](../requirements/R1-lightsail.md) |
| AWS CLI(Mac) | IAM 사용자 `paperclf-commander` + 고객 관리형 정책 `paperclf-lightsail`(`lightsail:*`), 리전 `ap-southeast-2`. 조직 SCP 가 `ap-southeast-2`·`us-east-1` 외 리전을 막음 | 사령관 명령 확인 |
| 접근 키 교체 | 첫 접근 키가 대화에 노출되어 삭제하고 새 키로 바꿈. 키 값은 어떤 문서에도 적지 않는다 | — |
| 실습 잔여물 삭제(연구자 지시) | 버킷 `nlpwi-eta-models`, 붙어 있지 않던 고정 IP `eta-deploy-ip`(13.210.129.4), 키 페어 `eta-mini-aws-key`·`eta-mini-ip` | 사령관 명령 확인 |
| 남은 자원 | 인스턴스 1, `StaticIp-1`, 키 페어 `LightsailDefaultKeyPair`·`miniproject5`, 버킷 0(프로젝트 버킷은 "배포 시작해" 뒤) | — |
| 정리 절차 | IAM 키·사용자·정책, Tailscale 기기·인증 키, 버킷, 인스턴스, `StaticIp-1`, 키 페어 `miniproject5` 를 지우는 절차 ③ 추가 | [자원 정리](../runbooks/teardown.md) |

대기

- GitHub 저장소 `metahomo/eta-mini-aws` · `metahomo/eta-mini` 완전 삭제 — 연구자 결정, `delete_repo` 권한 승인 대기.
- Tailscale — 연구자 가입 중, 서버 미설치.
- 배포 — 연구자의 "배포 시작해" 대기(그때 프로젝트 버킷 생성).
