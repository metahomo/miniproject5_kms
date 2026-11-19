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
| 운영 | app `v0.1.4` · model `m20261119-11` · <https://54-252-22-31.sslip.io/health> |
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
| 조감도 | 흐름도에 운영 장부·API 보호, 단계·카드 상태는 `gh` 조회 생성기로 | main 자동 푸시 |
| KMS | 수집 2회(fetched 1,200 · unique 867 · 새 논문 0 — OpenAlex 응답이 UTC 날짜별 캐시), 6시간마다 예약. KMS 웹 `127.0.0.1:10001` 다시 띄움(works 867) | — |

## 3. 귀가 후 연구자가 정할 것

- [ ] SSH 22번 닫기 시점 — 닫으면 #1·#8 → Done 15/16 (Mac 에서 서버 SSH 는 끊긴다, 배포·승격은 러너로 계속)
- [ ] 자원 정리 시점(발표 뒤) — [자원 정리 런북](../runbooks/teardown.md) ③, 장부 백업 먼저 PC 로
- [ ] KMS 의미 검색 임베딩(`kms embed`) — DB 쓰기라 위임 범위(수집 추가만) 밖으로 보고 보류
- [ ] KMS 수집 쿼리 확대 — 지금 1,200건 상한이라 새 논문이 잘 안 들어온다(`topics.yaml` 변경 필요)
- [ ] GitHub Wiki 첫 페이지 — 웹 화면에서만 만들 수 있다
- [ ] AI 활용 기록·ADR·개선점의 "연구자 언어" 칸 다듬기

## 4. 하지 않은 것 (지시대로)

22번 닫기·자원 삭제·교수님 서버(13.237.237.56) 작업·새 유료 자원 생성은 하지 않았다. 버킷($1/월)은 외출 전 연구자 승인으로 만든 것이다.
