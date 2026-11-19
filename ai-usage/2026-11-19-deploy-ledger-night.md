---
title: "AI 활용 — 서버 배포·승격·롤백·운영 장부·공개 API 보호 (2026-11-19 밤)"
description: "연구자의 '배포 시작해'와 권한 허용 뒤 사령관이 버킷·배포·HTTPS·승격·롤백·장부 DB·예측 로그·API 보호를 실행하고, 부관이 문서를 병렬 갱신한 기록"
tags: [ai-usage]
date: 2026-11-19
requirement: R1, R2, R3, R4, R5
tool: Claude Code(사령관) + 서브에이전트 4 + gh CLI + AWS CLI(Lightsail 만)
mode: delegate
---

# AI 활용 — 서버 배포·승격·롤백·운영 장부·공개 API 보호

## 목표

준비만 되어 있던 2·4단계를 실제 작업용 서버에서 끝내고(배포 → 승격 → 되돌리기 → 다시 앞으로), R3 의 남은 기준(parity 실패 차단, 실행마다 기록)을 운영 장부 DB 로 채운다.

## 사람이 정한 것 (주도)

- 연구자 지시: "배포 시작해"(권장안 — 결정 이슈 닫기 + 배포), 22번 포트는 마감 직전에 닫기, "3가지 다 수행", "깃허브에 수행하는 것도", 외출 중 전권 위임 (연구자 위임 초안)
- 권한: 연구자가 `/permissions` 로 `aws lightsail`·작업용 서버 `ssh`·`scp` 만 허용. 자동 권한 검사가 거부한 것(서버 접속, 유료 버킷 생성, 설정 파일 수정)은 우회하지 않고 연구자에게 넘겼다
- 검수 기준: 사령관이 밖에서 `curl https://54-252-22-31.sslip.io/health` 의 app_version·model_version 으로 매 단계 확인, 이슈는 증거 링크가 있을 때만 닫음 — [사령관 지침](../CLAUDE.md) 5·7절

## AI에게 맡긴 것

| 일 | 담당 | 결과·증거 |
|---|---|---|
| 버킷 생성·인스턴스 리소스 액세스, 저장소 변수 | 사령관 | `paperclf-models-apse2`, 서버에서 키 없이 쓰기 확인(80초) |
| v0.1.1 첫 배포, HTTPS, Tailscale | 사령관 | [배포](https://github.com/metahomo/miniproject5_kms/actions/runs/44513840582), Let's Encrypt, tailnet 100.102.186.119 |
| 승격·되돌리기·다시 앞으로, 미통과·코드 되돌리기 시연 | 사령관 | [→7](https://github.com/metahomo/miniproject5_kms/actions/runs/44514983743) · [→8](https://github.com/metahomo/miniproject5_kms/actions/runs/44515052182) · [F1 0.9021 차단](https://github.com/metahomo/miniproject5_kms/actions/runs/44515846566) · [v0.1.0 재배포](https://github.com/metahomo/miniproject5_kms/actions/runs/44453216170) |
| 런북 3개 | 사령관 | PR #25 |
| 운영 장부 DB·기록 스크립트·워크플로 연결·백업 | 사령관 | PR #26, [정상 m20261119-11](https://github.com/metahomo/miniproject5_kms/actions/runs/44519470540) · [parity 실패 차단](https://github.com/metahomo/miniproject5_kms/actions/runs/44519475156) |
| 예측 로그(원문 없이) | 사령관 | PR #28, v0.1.2 |
| 공개 API 토큰 인증·사용량 제한 | 사령관 | PR #30, v0.1.3: 토큰 없음 401 · 있음 200 · 분당 60 초과 429 |
| 발표 자료·슬라이드 갱신 | 부관 1 → 사령관 검수(낡은 사실 2곳 직접 고침) | PR #29, md-slides |
| 학습 실행 기록 5건, 요구사항 문서 갱신 | 부관 2 | 이 기록 뒤 PR |

## 결과와 검수

| AI 산출물 | 사령관이 확인한 방법 | 연구자 검수 |
|---|---|---|
| 배포·승격·롤백 | 매 단계 밖에서 `/health` 버전 일치 |  |
| 장부 트리거 | 운영 DB 에서 미통과 판 배포 기록 → `ERROR: model m20261119-9 has not passed gate and parity` |  |
| 예측 로그 | 밖에서 3건 예측 → 장부 3건(해시·길이·점수만) |  |
| API 보호 | 401·200·429 를 실제 요청으로 |  |
| 시험 | 전체 pytest 30 통과(장부 3·예측 로그 4·보호 3 추가) |  |

## 배운 점 / 다음엔

- 자동 권한 검사는 실제 클라우드 자원·서버 접속을 막는다. 연구자가 범위를 좁힌 허용 규칙을 직접 넣자 끝까지 진행됐다.
- Lightsail 리소스 액세스는 붙인 직후 바로 되지 않는다(이번엔 80초) — 재시도로 기다린다.
- 사용량 제한은 기본 Caddy 에 없어 API 안에 넣었다. parity 처럼 한꺼번에 많이 부르는 검사는 제한을 꺼야 한다.
