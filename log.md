---
title: 작업 일지
description: 지식 베이스 변경을 날짜순으로 덧붙이는 기록(아래로 추가만)
tags:
  - log
---
# 작업 일지

## 2026-11-18

- 프로젝트 골격 생성: 폴더 6개(`requirements`·`architecture`·`runbooks`·`experiments`·`decisions`·`sources`), 템플릿 6개, 필수 기능 R1~R5 문서, 아키텍처 개요 초안, 런북 4개 골격, AGENTS.md 규칙.

- 브리프 보강(설계 원칙·발표 요구사항) 반영: `presentation/`(절 4개, `slide-section` 템플릿)·`ai-usage/`(`ai-session` 템플릿, 첫 기록) 추가, 홈·AGENTS·아키텍처·결정 색인 갱신.

- 강의 01~03 원문·교과서판 md 생성(docs/lecture, KB 밖) → [강의 자료 색인](./sources/lecture-index.md) 갱신. CLAUDE.md(사령관)·AGENTS.md(부관) 재작성. `reports/` 신설, [KMS 활용 타당성 보고서](./reports/2026-11-18-kms-feasibility.md). 조감도는 claude.ai 문서로 작성.

- PostgreSQL 장부 DB: [ADR-002](./decisions/ADR-002-postgresql.md)·[데이터 모델](./architecture/data-model.md) 작성 → `db/compose.yml`·`db/init/001_schema.sql` 로 로컬 `postgres:18.7` 기동(127.0.0.1:5433), 테이블 4·뷰 2 확인, 트리거가 게이트 미통과 모델 배포를 거부하는 것 확인.

- GitHub 진행 관리 구성: 라벨 8·마일스톤 6(단계 0~5)·이슈 16(R1~R5 추적 #1~#5, 단계 작업 #6~#11, 결정 #12~#16). 조감도에 "GitHub 바로가기" 절 추가. [사령관 지침](./CLAUDE.md) 8절에 규칙 기록. DB 작업분은 커밋 명령이 없어 푸시 대기.

- 도메인·서버 확정: [ADR-003](./decisions/ADR-003-domain-server.md) (`nlpwizard.eta.pyhub.kr` → `13.237.237.56`). DNS 일치, HTTPS 인증서 없음. 조감도 갱신.

- GitHub 기능 전체 사용 결정: Kanban Board 완성 = 프로젝트 완성([사령관 지침](./CLAUDE.md) 8절). Discussions 켬(공지 #18). 조감도에 "GitHub 조감도" 절(칸반 5열 그림 + 기능별 상태 표) 추가. 보드는 토큰 `project` 권한, Wiki 는 첫 페이지 생성 대기.

- 작업 점검 후속: AI 활용 기록 4건([색인](./ai-usage/index.md)), 트리거 거부 시험(트랜잭션 안에서 시험 후 되돌림, 데이터 0건), 이슈 #1 → 마일스톤 "2 서버 배포", [ADR-002](./decisions/ADR-002-postgresql.md) 오타 수정, [사령관 지침](./CLAUDE.md) 8절 표 세분화, 조감도 칸반 그림을 상태 색으로 다시 그림, `.gitignore` 정리(스킬 사본·폴더별 `.ok/` 제외, 맨 위 `.ok/config.yml` 추적).

- KMS 자동 수집 요청(KCI·OpenAlex): KMS 18절 동결을 자동 수집에 한해 푸는 결정만 기록 — [ADR-004](./decisions/ADR-004-kms-auto-collection-unfreeze.md). KMS 저장소·`.env` 는 손대지 않음.

- KMS 자동 수집: 로그온 2분 뒤 `kms run`(OpenAlex) 작업 `KMS-수집-로그온` 등록(KMS `scripts/register-task.ps1`). 깨진 KMS `.venv`(없는 Python 3.11 가리킴)를 uv 의 3.11 로 다시 만듦. 시험 실행 결과 0, 실행 이력 succeeded. KMS 설계 확장은 중단(사용자 지시). 조감도에 "GitHub 영역별 세부"·"강의 순서 대조 — 진행 체크" 절 추가.

- 발표 = 조감도(연구자 결정). 조감도에 "발표 순서"·"AI 활용"·"강의 대비 개선점"·"AI 에게 서비스 제공하기" 절과 강의 순서 그림 추가, 바뀐 사실 3건(저장소 공개·자동 수집·초록 보관) 고침. [개선점](./presentation/03-improvements.md) 7개 기록, [발표 개요](./presentation/index.md)에 결정 반영.

## 2026-11-18 마무리 — 한 일·할 일

한 일

- 장부 DB(PostgreSQL) 설계·기동·트리거 시험 통과 — [ADR-002](./decisions/ADR-002-postgresql.md), [데이터 모델](./architecture/data-model.md)
- GitHub 라벨 8·마일스톤 6·이슈 16·Discussions, 이슈 #1 → 마일스톤 "2 서버 배포"
- 도메인·서버 확정 — [ADR-003](./decisions/ADR-003-domain-server.md)
- KMS 로그온 자동 수집 등록·시험 성공 — [ADR-004](./decisions/ADR-004-kms-auto-collection-unfreeze.md)
- 조감도 = 발표 자료: 발표 순서·AI 활용·개선점·AI 서비스·GitHub 영역별 세부·강의 순서 대조(그림+체크리스트), 한눈에 그림에 장부 DB, 절 순서 재배치
- AI 활용 기록 4건, [개선점](./presentation/03-improvements.md) 7개, `.gitignore` 정리
- 문서 점검 워크플로(`.github/workflows/docs.yml`, `scripts/check_docs.py`) 작성 — 브랜치 `ci/docs-check`, 로컬 위반 0건

할 일 (다음 세션에 바로)

1. Projects 보드 완성 — `gh auth refresh -h github.com -s project,read:project` 승인(연구자) → 보드·열 5개·이슈 16개 카드·저장소 연결 → 조감도 "보드 없음" 표시·상태 칸 갱신
2. 문서 점검 PR — `ci/docs-check` 브랜치로 PR(Refs #7) → Actions 결과 확인 → 조감도 Actions·PR 상태와 강의 대조표(02 · 5.1~5.3)에 증거 링크
3. 조감도 문서 표의 "푸시 대기" 목록을 GitHub 링크로 옮기기(푸시 뒤)
4. 연구자 작성 칸: 개선점 이유·AI 활용 검수 방법·ADR 근거 — 연구자의 언어로
5. 보류 결정: 저장소 공개/비공개(자체 러너 전), `main` 보호 규칙·squash, 마일스톤 마감일, KCI 엔드포인트 확인(활용가이드 PDF)

## 2026-11-19 — Mac 서버 이전 후 자율 진행 (연구자 외출, 전권 위임)

- 작업 환경을 Windows → Mac 서버 Studio-C 로 옮김. KMS 판정 모델 qwen3 4B, 지식베이스 `data/`(KMS `logs/changes/changes_261119.md`). 조감도(claude.ai 문서)는 이 세션에서 열리지 않아 보충 문안을 [보고서](./reports/2026-11-19-autonomous-progress.md)에 둠.
- 칸반보드: 비어 있던 Projects #12 를 "miniproject5 Kanban Board" 로, 열 5개(Backlog → Todo → In Progress → Review → Done), 이슈 16 + PR 카드.
- KMS 수집 867편(ADR-004 범위) → 교사 라벨 867편(include 641 · exclude 211 · uncertain 15, 스키마 위반 0) → 공개 스냅숏(원문 없음) — [ADR-005](./decisions/ADR-005-student-model-snapshot.md).
- 학생 모델·게이트·ONNX·모델 카드·parity·서빙 API·Dockerfile·워크플로 3개 — [ADR-006](./decisions/ADR-006-gate-parity.md). 로컬 pytest 15 통과, 게이트 F1 0.9603, 5% 모델은 게이트 실패.
- PR [#19](https://github.com/metahomo/miniproject5_kms/pull/19). 배포·승격·되돌리기 잡은 `vars.DEPLOY_ENABLED` 로 꺼 둠(서버 접근 수단 없음).
- [AI 활용 기록](./ai-usage/2026-11-19-student-model-pipeline.md).

## 2026-11-19 오후 — 진행판 정리와 연구자 위임 작업

- 연구자 지시: "모든 수행을 멀티로, 필요하면 모든 부관 파견, 토큰 걱정 없음", "연구자가 해야 할 일도 바로 해줘 — 중단되지 않도록". 부관 6명 병렬 조사 → 사령관이 명령으로 재확인 → 이슈 닫기·결정 확정·문서 병렬 작성 — [AI 활용 기록](./ai-usage/2026-11-19-board-and-delegation.md).
- 이슈 #6(0 준비)·#7(1 코드 판)·#9(3 모델 판) 문 통과로 닫고 보드 Done. #3(R3)은 진행 댓글만 — 기준 4(실행마다 기록 1건) 미충족.
- 증거: [약한 모델 게이트 실패 F1 0.9021](https://github.com/metahomo/miniproject5_kms/actions/runs/44452096551), [정상 F1 0.9603 · parity 5.8e-7](https://github.com/metahomo/miniproject5_kms/actions/runs/44451897410), [v0.1.0 태그 → GHCR `paperclf-api:v0.1.0`](https://github.com/metahomo/miniproject5_kms/actions/runs/44453216170).
- 결정 #14 · #15 · #16 권장안 확정 → [ADR-007](./decisions/ADR-007-region-instance.md)(리전 시드니 `ap-southeast-2`) · [ADR-008](./decisions/ADR-008-ledger-db-ops.md)(운영 DB 서버 compose, `pg_dump` → 버킷 매일 + 승격·롤백 직후, 14개 보관) · [ADR-009](./decisions/ADR-009-ledger-writer.md)(장부 기록은 서버 러너 대행, 예측 로그는 API 가 localhost) — [결정 색인](./decisions/index.md).
- 서버 13.237.237.56: `/health` 는 여전히 eta(app_version v2.4), https 연결 실패, Caddy·러너 미설치, 저장소 변수 0개. 이 Mac 에 서버 SSH 키·AWS 자격 증명 없음 → 2·4단계 대기.
- 발표 보조 슬라이드 17장([공개](https://metahomo.github.io/md-slides/miniproject5-kms/)), claude.ai 페이지(비공개). 오전에 OpenKnowledge 제거, 템플릿은 [`templates/`](./templates/) 로.
- 문서 갱신: [보고서](./reports/2026-11-19-autonomous-progress.md) 2·6·7절, [R3](./requirements/R3-auto-train-validate.md)(doing, 검증 증거 3건), [홈](./index.md) R1~R5 표, AI 활용 기록 7건의 "사람이 정한 것"(연구자 위임 초안).

## 2026-11-19 오후 — 작업용 서버·AWS 정리

- 연구자 결정으로 작업 분리: ① R1~R5 는 작업용 서버 `Amazon_Linux_2026_kms`(`54.252.22.31`)에서, ② 교수님 사이트(`13.237.237.56`) 게시는 맨 마지막에 교수님 지시대로. DNS 그대로, PR #21 보류.
- 작업용 서버: Docker·Compose·Caddy(임시)·`/srv/paperclf`·러너 `paperclf` 온라인. Mac AWS CLI 는 IAM 사용자 `paperclf-commander` + 정책 `paperclf-lightsail`. 노출된 첫 접근 키 삭제·교체. 실습 잔여물(버킷 `nlpwi-eta-models`, 고정 IP `eta-deploy-ip`, 키 페어 2개) 삭제.
- 문서: [R1](./requirements/R1-lightsail.md) 서버 절, [자원 정리](./runbooks/teardown.md) 절차 ③, [보고서](./reports/2026-11-19-autonomous-progress.md) 8절.

## 2026-11-19 저녁 — 조감도 정비와 사령관 지침 정리

한 일

- PR [#22](https://github.com/metahomo/miniproject5_kms/pull/22)·[#23](https://github.com/metahomo/miniproject5_kms/pull/23)·[#24](https://github.com/metahomo/miniproject5_kms/pull/24) 병합(검사 통과), 보드 카드 Done.
- 조감도 경로 확정: claude.ai 조감도(연구자 계정)는 Mac 서버 계정에서 읽기·쓰기 불가, 맥서버 계정 외부 공유 불가(교수님 확인), 연구자 PC 의 Z: 는 Mac 서버가 아님. → 연구자가 보는 조감도 = 연구자 PC 저장소 사본의 [`reports/birdseye-update.html`](./reports/birdseye-update.html). 예약 작업 `birdseye-pull`(5분마다 `git pull`) + 페이지 1분 자동 새로 고침으로 연구자 손 없이 갱신.
- 조감도 두 파일(md·html)은 진행이 바뀌면 사령관이 묻지 않고 main 에 커밋·푸시(연구자 상시 허락). 연구자가 "조감도"라고 하면 = 볼 수 없는 상태 → 사령관이 볼 수 있게 조처하고 한 일·할 일로 보고(절대규칙).
- 조감도를 Windows 때 구성(이 로그 2026-11-18 줄, [AI 활용 기록](./ai-usage/2026-11-18-github-progress.md))대로 다시 만듦: 한 눈에(6단계 × GitHub 기능) · 자세히(칸반 카드 16장 ↔ 단계·소주제) · 흐름도 · 단계별 설명 · GitHub 영역별 세부 · 강의 순서 대조 · 발표 순서 · AI 활용 · 강의 대비 개선점 · AI 에게 서비스 + 단계별 문·R1~R5·자원·PR·할 일. 상태 칸은 `gh` 조회에서 옮기는 생성기(Mac `~/.claude/birdseye/build.py`)로 만든다.
- [사령관 지침](./CLAUDE.md) 정리: 조감도 규칙을 2절 한 곳으로, 멀티 수행·커밋 규칙·사실 규칙 중복 제거, 옛 경로(`Z:\`)와 없는 절 지시 삭제(98 → 91줄).
- GitHub Pages(`gh-pages`)·claude.ai 아티팩트판 조감도는 연구자가 열 수 없어 쓰지 않음.

할 일

1. 결정 이슈 #14·#15·#16 — ADR-008·009·007 링크 댓글 후 닫기(보드 Review → Done).
2. 연구자 "배포 시작해" → 버킷·저장소 변수, HTTPS·Tailscale, `v0.1.1` 첫 배포 → `/health` (2단계 문).
3. 모델 첫 승격 → 되돌리기 → 다시 앞으로 (4단계 문).
4. 조감도 화면이 원본 claude.ai 조감도와 다른 곳은 연구자 스크린샷을 받아 고침.
5. 쓰지 않는 `gh-pages` 브랜치·claude.ai 아티팩트판 정리 여부 결정.

## 2026-11-19 밤 — 서버 배포·승격·롤백·운영 장부 ("배포 시작해")

- 결정 이슈 #14·#15·#16 닫음(ADR-008·009·007).
- 버킷 `paperclf-models-apse2`(small_1_0) 생성·인스턴스 리소스 액세스(키 없이 쓰기, 반영 80초). 저장소 변수 MODEL_BUCKET·AWS_REGION·DEPLOY_ENABLED=true.
- `v0.1.1` 태그 → 서버 첫 배포, HTTPS `https://54-252-22-31.sslip.io`(Let's Encrypt), Tailscale `paperclf`(100.102.186.119). 22번은 마감 직전에 닫기로(연구자 결정).
- 승격 m20261119-7·8 → 되돌리기 7 → 다시 8, 미통과 모델 차단(F1 0.9021), 코드 되돌리기 v0.1.0 → 다시 v0.1.1 → 이슈 #2·#4·#5·#10 닫음.
- 런북 3개(배포·승격·롤백) PR #25. 운영 장부 DB(서버 `/srv/ledger`, 실행마다 기록·배포 기록·백업, parity 실패 시험 입력) PR #26 → 정상 m20261119-11 승격·기록, parity 실패 -12 차단·기록 → 이슈 #3 닫음.
- 보드 Done 13/16. 남은 카드: #1(22번·정리), #8(22번), #11(마감·발표).

## 2026-11-20 저녁 — 과제 도메인 첫 화면 = KMS 웹, 운영 점검

한 일

- KMS 지식베이스 내용 채움: 저널 평가 646개(핵심 3·후보 52·제외 591), 주제 보고서 `261120.md`·주제 MOC, Obsidian 노트 6,061개(논문 4,374·저널 1,685). 자동 수집(6시간마다)에 `journals`·`report`·`notes` 를 붙임. 운영 DB 는 추가만(ADR-004), 작업 전 백업.
- 연구자 결정: `https://nlpwizard.eta.pyhub.kr` 첫 화면 = KMS 웹(HTTPS + 접속 암호). `/health`·`/predict`·`/model`·`/mcp` 는 paperclf 그대로. API 소개 화면·`/docs` 는 `https://54-253-32-153.sslip.io`, KMS 같은 화면은 `https://kms.54-253-32-153.sslip.io`.
- 최종 서버: Mac → 서버 역방향 SSH 터널(`~/.claude/autonomy/kms-tunnel-final-loop.sh`, 끊기면 다시 이음) + Caddy. 저장소 [`Caddyfile`](./deploy/lightsail/caddy/Caddyfile) 을 서버와 같게 맞춤 — 공개 저장소라 해시는 자리표시 `KMS_HASH`, `bootstrap.sh` 가 서버 `/srv/caddy/kms.hash`(root 600, 두 서버)로 채움. DNS 없는 이름(`kms.nlpwizard…`)의 인증서 재시도 실패와 아무것도 없는 8090 으로 가던 `:80` 블록을 없앰.
- 점검 결과(2026-11-20 17시대, 명령 출력): 도메인 첫 화면 암호 없이 `401`·암호로 `200`(대시보드 · KMS), `/health` ok v0.1.6 · m20261120-24, `/predict` 토큰 없이 `401`·토큰으로 `include` 0.9967, `/mcp` 토큰 없이 거절, HTTP → `308`, HSTS. 작업용 서버 ok. pytest 83 통과·6 건너뜀. CI 최근 6회 성공, 러너 둘 다 online, 열린 PR 0, Dependabot 열린 경고 0.
- 문서 최신화: README·시연 대본 ①·[최종 서버 런북](./runbooks/final-server.md)(KMS 절 새로)·[아키텍처 개요](./architecture/overview.md)·[ADR-003](./decisions/ADR-003-domain-server.md) 갱신 절.

할 일

1. 발표 직전: KMS 화면 확인 — Mac 을 다시 켰다면 KMS `serve` 와 터널 두 개를 다시 띄운다(런북 KMS 절 3·4단계, launchd·crontab 은 이 계정에서 막힘).
2. 운영 감시(`uptime.yml`)는 작업용 서버만 본다 — 최종 도메인 `/health` 도 넣을지 결정.
3. 낡은 서술(`13.237.237.56` 을 최종 서버로 쓴 옛 문서: R1·teardown·옛 보고서)은 기록으로 두고, 런북 teardown 의 최종 서버 절은 새 서버 기준으로 다시 씀.
4. 마감 직전 SSH 22번 닫기(연구자 결정) → #1·#8, 발표 뒤 자원 정리 → #11.
