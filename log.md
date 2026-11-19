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
