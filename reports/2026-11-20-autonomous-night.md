---
title: 보고서 — 2026-11-19 밤~20 연구자 외출 중 자율 진행
description: 전권 위임("귀가할 때까지 계속") 동안 사령관이 한 일, 실제 확인한 증거, 연구자가 귀가 후 결정할 것
tags:
  - report
date: 2026-11-20
---
# 보고서 — 2026-11-19 밤 ~ 11-20 자율 진행

연구자 지시(2026-11-19 21:4x): "모든 권한 위임, 프로젝트 완수. KMS 웹 DB 자료 계속 수집, 깃허브·강의안·아티팩트·강의 발표안 완성도 높이기. 귀가할 때까지 계속. 15분마다 1문단 보고." 확정한 권장안: 공개 API 보호, KMS 수집 계속(추가만, [ADR-004](../decisions/ADR-004-kms-auto-collection-unfreeze.md))·재학습은 새 논문이 생기면 하루 1번, 하지 않을 것 — 22번 닫기·자원 삭제·교수님 서버·새 유료 자원.

## 1. 지금 상태 (한눈에)

| 항목 | 값 |
|---|---|
| 운영 | app `v0.1.4` · model `m20261120-17`(새 데이터로 자동 재학습) · <https://54-252-22-31.sslip.io/health> |
| 보드 | Done 13/16 — 남은 #1·#8(22번 닫기·정리), #11(마감·발표) |
| 릴리스 | [v0.1.1](https://github.com/metahomo/miniproject5_kms/releases/tag/v0.1.1) · [v0.1.4](https://github.com/metahomo/miniproject5_kms/releases/tag/v0.1.4) |
| 조감도 | 연구자 PC `reports/birdseye-update.html` — 5분마다 자동 받기, 1분마다 새로 고침 |

## 2. 한 일 (PR·증거)

| 일 | 결과 | 증거 |
|---|---|---|
| 공개 API 보호 | `/predict` 토큰 인증 + IP 별 분당 60 → 토큰 없이 401, 있으면 200, 65번 중 5번 429 | PR #30, v0.1.3 |
| 원격 MCP | `POST /mcp`(JSON-RPC, `classify_paper`) 같은 보호 뒤 — 밖에서 401, initialize·tools/call 정상 | PR #38, v0.1.4 |
| 에이전트 스킬 | [`skills/paperclf-classify`](../skills/paperclf-classify/SKILL.md) — AI 서비스 세 겹(REST·MCP·스킬) 완성 | PR #39 |
| 자동 복귀 시연 | 깨진 판(가짜 ONNX) → `/health` 30초 실패 → 직전 판 복귀·확인 37초. `server.sh` 보강 | PR #36 |
| 장부 복구 훈련 | 버킷 최신 덤프 → 임시 DB, 건수·운영 판·트리거 일치. 절차에 API 계정 선생성 추가 | PR #37 |
| 기록 | 학습 실행 5건([experiments](../experiments/index.md)), [AI 활용 기록](../ai-usage/2026-11-19-deploy-ledger-night.md), R1·R2·R4·R5 완료 기준 | PR #31 |
| 발표 | [시연 대본](../presentation/05-demo-script.md)(7분), 슬라이드 17장 다듬기(장 제목=결론, 시연 4장) | PR #33, md-slides |
| GitHub | [README](../README.md) 신설, [공지 #35](https://github.com/metahomo/miniproject5_kms/discussions/35), 릴리스 v0.1.4, 마일스톤 0·1·3·4 닫음 | PR #34 |
| 문서 상태 맞춤 | 저장소 전체 상대 링크 깨짐 0, 낡은 "버킷 미생성·배포 꺼 둠" 정리 | PR #32 |
| 보안 헤더 | HTTPS 응답에 HSTS 1년·nosniff·no-referrer, Server 헤더 숨김 — 적용·확인 | PR #41 |
| 운영 감시 | 매시간 밖에서 `/health`(uptime 워크플로), 실패 시 GitHub 알림 — 첫 실행 성공 | PR #42 |
| **새 데이터 자동 재학습** | KMS 11-20 수집 새 논문 7편 → 교사 라벨(include 6·exclude 1) → 스냅숏 → main 병합만으로 자동 학습·게이트 F1 0.9609·parity 5.5e-7·승격 m20261120-17·장부 기록 — R3 의 실제 흐름 | PR #44, [실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44643935701) |
| 조감도 | 흐름도에 운영 장부·API 보호, 단계·카드 상태는 `gh` 조회 생성기로 | main 자동 푸시 |
| KMS | 수집 2회(fetched 1,200 · unique 867 · 새 논문 0 — OpenAlex 응답이 UTC 날짜별 캐시), 6시간마다 예약. KMS 웹 `127.0.0.1:10001` 다시 띄움(works 867) | — |

## 3. 귀가 후 연구자가 정할 것

- [ ] SSH 22번 닫기 시점 — 닫으면 #1·#8 → Done 15/16 (Mac 에서 서버 SSH 는 끊긴다, 배포·승격은 러너로 계속)
- [ ] 자원 정리 시점(발표 뒤) — [자원 정리 런북](../runbooks/teardown.md) ③, 장부 백업 먼저 PC 로
- [ ] KMS 의미 검색 임베딩(`kms embed`) — DB 쓰기라 위임 범위(수집 추가만) 밖으로 보고 보류
- [ ] KMS 수집 쿼리 확대 — 1,200건 상한이라 하루 새 논문이 적다(11-20 은 7편, `topics.yaml` 변경 필요)
- [ ] GitHub Wiki 첫 페이지 — 웹 화면에서만 만들 수 있다
- [ ] AI 활용 기록·ADR·개선점의 "연구자 언어" 칸 다듬기

## 4. 하지 않은 것 (지시대로)

22번 닫기·자원 삭제·교수님 서버(13.237.237.56) 작업·새 유료 자원 생성은 하지 않았다. 버킷($1/월)은 외출 전 연구자 승인으로 만든 것이다.

## 5. 2차 자율 진행 (2026-11-20 오전, 연구자 외출)

| 일 | 결과 | 증거 |
|---|---|---|
| 운영 점검 | health ok(v0.1.4 · m20261120-17), CI 연속 성공, 러너 온라인, 보안 경고 0, 컨테이너 3개 healthy | 15분마다 |
| 시연 리허설 | 대본의 읽기 전용 명령을 운영에 실제로: `/health`, 토큰 없이 `/predict`·`/mcp` 401, 토큰으로 200, 장부 status, HTTP→308 | 대본 05 증거 칸 갱신 |
| 문서 최신화 | 운영 판(v0.1.2·0.1.3·m20261119-11 → v0.1.4·m20261120-17), 학습 기록 m20261120-17, 시험 수 15→32, 발표 04 인증 문구 | PR #47 · #48 · #49 |
| 발표 덱 | 16:9 한 장 기준 28장, 넘치는 4장 나눔, 알림 상자·코드 줄 강조, 인라인 글자 크기 제거 | md-slides main |
| 슬라이드 앱(오전, 연구자와) | Marp 장 지시어·GitHub 알림·줄 강조·16:9·여백 0·장표 경계, 작성 가이드 `docs/slide-authoring.md` | md-slides |
| 조감도(오전, 연구자와) | 흐름도·칸반 오른쪽 넘침 없앰(단계별 카드), 노트북 Claude Code 가 발표용 아티팩트 담당(지침 2절) | PR #46 |

## 6. 3차 자율 진행 (2026-11-20 저녁 ~ 귀가, 연구자 외출 · 전권 위임)

연구자 지시: 멈춤 없이 조감도 수행사항 완결 → 구현된 웹을 템플릿을 찾아 대입하며 심미적으로 보완, 15분 보고마다 템플릿 이름과 결과.

| 일 | 결과 | 증거 |
|---|---|---|
| 남은 할 일 4 | PR #59·#60 병합, 운영 감시 두 서버(최종·작업용), 자원 정리 런북 새 최종 서버 기준, SSH 22 = Mac 공인 IP + 브라우저 SSH(KMS 터널 때문에 완전 닫기 대신) | PR [#59](https://github.com/metahomo/miniproject5_kms/pull/59) · [#60](https://github.com/metahomo/miniproject5_kms/pull/60), uptime 실행 44704300507 |
| 보드 | 이슈 #1(R1)·#8 닫음 → Done 15/16. 남은 #11 은 발표 원고·발표 뒤 자원 정리 | 이슈 댓글 |
| KMS 연구 보고서(046) | 1·2단계 절차(앞단 A1~A4 → 목표 설계 4종 → 명세 → G3 → 구현 → 정리 2회). 과제 도메인 KMS 웹에서 생성: v3 77초, 근거 30·인용 27, 동향 연도순·방법 표본/분석·공백·제언 제자리, 참고문헌 DB 값만 | KMS 저장소 `logs/process/process_261120.md` 1~6절, 시연 대본 ⑩ PR [#61](https://github.com/metahomo/miniproject5_kms/pull/61) |
| KMS 웹 보완(047) | 템플릿 16회 대입(Simple·Pico·Water·Tabler·MVP·Bootstrap·Primer·GOV.UK·Tufte·LaTeX.css·Sakura·AdminLTE/CoreUI) → 운영 반영 보정 14, 결함 수정 8, 회귀 점검 13화면 × 4조합 통과, 색 대비 11쌍 × 2테마 AA | [전후 비교 그림](./img/kms-web-before-after-20261120.png), KMS 저장소 `docs/design/target/웹템플릿_대입기록.md` |
| 시험 | KMS 909 통과(실패 2 = Mac 사본 기존 문제: base.html 외부 글꼴, UC_목표_웹.md 없음) | 매 반영마다 사령관 실행 |
| 운영 | 15분마다: 과제 도메인 health·KMS 401/200·작업용·터널 2·수집 루프 — 모두 정상. 21:42 자동 수집에 저널 평가·보고서·노트 단계 동작 | progress.md |

### 귀가 후 연구자가 정할 것

1. 보정안 G(왼쪽 사이드바, 1100px 이상) 운영 반영 여부 — 전 화면 뼈대 변화라 보류
2. 위임 판정 유지 여부 — 근거 30편·볼트 저장·EDITOR 생성·보고서 메타에 역할만·검색 방식
3. KMS 저장소 커밋(KMS 규칙: 명령 때만) — 046·047 코드·명세·목표 문서·과정 기록이 커밋 전
4. 관리자 진행 레일 시각 형식 통일, 로그인 화면(지금 로그인 꺼짐이라 안 보임)
5. 접근성 자동 검사(axe-core 주입) — 사령관 권한 확인에서 거부되어 하지 않음

### 이어 가는 방법

- Claude Code 창이 열려 있으면 그대로 15분마다 이어 간다. 닫혔으면 Mac 에서 `claude -c` → `계속`.
- Mac 을 다시 켰으면 `KMS 다시 켜` — KMS 웹·터널 두 개·자동 수집.
