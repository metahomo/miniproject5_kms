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

도메인 `nlpwizard.eta.pyhub.kr` → `13.237.237.56` — [ADR-003](../decisions/ADR-003-domain-server.md). 2026-11-18 현재 HTTPS 미설정.

## 완료 기준 (초안)

- [ ] 인스턴스 생성, 고정 IP 연결, 시작 스크립트로 실행 환경 구성
- [ ] 버킷 생성, 인스턴스가 접근 키 없이 버킷을 읽고 씀
- [ ] 외부에서 열린 포트 확인(22번 닫힘 여부 포함)
- [ ] 자원 정리 런북으로 비용 발생 자원을 모두 지울 수 있음 — [자원 정리](../runbooks/teardown.md)

## 검증 증거

| 날짜 | 무엇을 확인 | 결과 | 증거 |
|---|---|---|---|

## 미해결

- 인스턴스 요금제·리전·버킷 이름 — [결정 기록](../decisions/index.md)에 남기기
