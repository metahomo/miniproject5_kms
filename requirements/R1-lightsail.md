---
title: R1 Lightsail 인스턴스·버킷 활용
description: API 서버는 Lightsail 인스턴스에, 데이터·모델 산출물은 Lightsail 버킷에 둔다
tags:
  - requirement
  - aws
  - lightsail
id: R1
status: todo
---
# R1 Lightsail 인스턴스·버킷 활용

## 요구사항

"Lightsail 인스턴스/버킷 활용" — [과제 브리프](../sources/project-brief.md) 1번.

## 강의 근거

[강의 자료 색인](../sources/lecture-index.md#필수-기능과-강의-절-대응): 03 › 1 서버, 03 › 4 버킷, 03 › 6 지우기.

## 설계

[아키텍처 개요](../architecture/overview.md) — 인스턴스(서빙)·버킷(데이터·모델 저장소).

## 서버

### 지금 R1 대상 — 작업용 서버 (2026-11-19~)

연구자가 일을 두 갈래로 나눴다(2026-11-19). **① R1~R5 는 강의 순서대로 연구자의 작업용 서버에서 한다.**

| 항목 | 값 |
|---|---|
| 인스턴스 | Lightsail `Amazon_Linux_2026_kms` — Amazon Linux 2023, 2GB·2vCPU·60GB, `ap-southeast-2a` |
| 고정 IP | `54.252.22.31` (`StaticIp-1`) |
| 설치됨 | Docker 25, Compose 2.40.3, Caddy(임시 `:80 → 127.0.0.1:8080`), `/srv/paperclf`, 러너 `paperclf` 온라인 |
| HTTPS | `54-252-22-31.sslip.io` 로 예정 — [작업용 서버 런북](../runbooks/work-server.md) |
| Tailscale | 미설치(연구자 가입 중) |
| 버킷 | 0개 — 프로젝트 버킷은 연구자가 "배포 시작해" 라고 한 뒤 만든다 |
| AWS CLI(Mac) | IAM 사용자 `paperclf-commander` + 고객 관리형 정책 `paperclf-lightsail`(`lightsail:*`), 리전 `ap-southeast-2`. 조직 SCP 가 `ap-southeast-2`·`us-east-1` 외 리전을 막는다 |

DNS 는 바꾸지 않는다. 지울 때는 [자원 정리](../runbooks/teardown.md) 절차 ③.

### 마지막 단계 — 교수님 서버에 결과 올리기

**② 최종 결과를 교수님 사이트 `nlpwizard.eta.pyhub.kr`(`13.237.237.56`)에 올리는 일은 따로, 맨 마지막에, 교수님 지시에 따라 한다.** 도메인 → `13.237.237.56` — [ADR-003](../decisions/ADR-003-domain-server.md). eta 와 Caddy 를 함께 두는 계획(PR #21)은 ②에 속하며 보류 중이다.

## 완료 기준 (초안)

- [ ] 인스턴스 생성, 고정 IP 연결, 시작 스크립트로 실행 환경 구성
- [ ] 버킷 생성, 인스턴스가 접근 키 없이 버킷을 읽고 씀
- [ ] 외부에서 열린 포트 확인(22번 닫힘 여부 포함)
- [ ] 자원 정리 런북으로 비용 발생 자원을 모두 지울 수 있음 — [자원 정리](../runbooks/teardown.md)

## 검증 증거

| 날짜 | 무엇을 확인 | 결과 | 증거 |
|---|---|---|---|
| 2026-11-19 | 작업용 서버 인스턴스·고정 IP 연결, Docker·Compose·Caddy·러너 `paperclf` 온라인 | 통과(사령관 확인) | [보고서 8절](../reports/2026-11-19-autonomous-progress.md) |

## 미해결

- ~~인스턴스 요금제·리전~~ → 시드니 `ap-southeast-2` — [ADR-007](../decisions/ADR-007-region-instance.md). 작업용 서버는 2GB·2vCPU(2026-11-19 확인)
- 버킷 이름 — 제안 `paperclf-models-apse2`(미생성, "배포 시작해" 뒤) — [ADR-007](../decisions/ADR-007-region-instance.md)
- 작업용 서버 HTTPS(`54-252-22-31.sslip.io`)·Tailscale — 진행 중
- ② 교수님 서버 게시 방법 — 교수님 지시 대기. PR #21(eta 와 Caddy 공존) 보류
