---
title: 강의 자료 색인
description: docs/lecture 의 강의 01~03 원문·교과서판 md 위치, 주요 절과 필수 기능 R1~R5 대응
tags:
  - source
  - lecture
source_path: Z:\miniproject-kms\docs\lecture
captured: 2026-11-18
---
# 강의 자료 색인

원본은 이 프로젝트 밖 `Z:\miniproject-kms\docs\lecture` 에 있다. 2026-11-18 각 HTML 을 원문 md 로 변환하고, 최신 정보를 웹으로 확인해 초보자용 교과서판을 만들었다. 교과서판의 `🔄 업데이트` 상자가 원 강의와 달라진 점이고, 출처 URL 과 확인 날짜는 각 판의 부록 C 에 있다. 본문을 KB 에 인용할 때는 해당 절을 이 폴더로 옮긴 뒤 링크한다(TODO).

| 강의 | 원본 HTML | 원문 md (줄) | 교과서판 md (줄) | 이미지 |
|---|---|---|---|---|
| 01 실습환경 확인 및 핵심 개념 | `01 실습환경 확인 및 핵심 개념.html` | `01 …_원문.md` (1,476) | `00_Overview.md` (2,498, 2026-11-18 보완) | `assets/01/` 1개 |
| 02 MLOps 개요 및 아키텍처 | `02 MLOps 개요 및 아키텍처.html` | `02 …_원문.md` (1,904) | `02 …_교과서.md` (2,637) | 없음 |
| 03 AWS 기반 ML 인프라 구축 | `03 AWS 기반 ML 인프라 구축.html` | `03 …_원문.md` (1,171) | `03 …_교과서.md` (1,826) | `assets/03/` 23개 |

## 필수 기능과 강의 절 대응

| 기능 | 강의 절 (파일 › 절) |
|---|---|
| [R1 Lightsail 인스턴스·버킷](../requirements/R1-lightsail.md) | 03 › 1 서버 — Lightsail 인스턴스 (인스턴스 만들기 ①②③, 고정 IP, 방화벽, SSH) · 03 › 4 모델 배포 (버킷 만들기, 버킷에 서버 붙이기 — 키 없이) · 03 › 6 지우기 |
| [R2 GitHub CI/CD](../requirements/R2-cicd.md) | 02 › CI/CD, GitHub Actions 워크플로, PR로 테스트, 태그로 배포 · 03 › 2 코드 배포 ① — GitHub 러너가 SSH 로 · 03 › 3 코드 배포 ② — 내 서버를 러너로 |
| [R3 자동 학습·검증](../requirements/R3-auto-train-validate.md) | 02 › DevOps + ML, 연습문제: 검증 게이트, 연습문제: 일치 확인 (parity), 운영 지표가 재학습을 트리거 · 03 › 데이터를 바꿀 수 있게 — 세 곳 고치기, model 워크플로 |
| [R4 모델 API 배포](../requirements/R4-model-serving.md) | 02 › 모델 릴리스 자동화, ONNX 변환, CD에서 python/go/rust 이미지 빌드 · 03 › 4 모델 배포 — 다시 학습해 승격, 버킷에서 판을 본다 |
| [R5 롤백](../requirements/R5-rollback.md) | 03 › 5 되돌리기 (rollback 실행하기, 서버에서 확인, 연습문제: 되돌렸다가 다시 앞으로) |

## 공통 개념

- 03 › "판은 둘 — 코드 판과 모델 판": 코드 배포와 모델 배포를 따로 다룬다.
- 03 › "오늘 만드는 것 — 요청이 지나가는 길 / 배포가 지나가는 길".
- 01 › Git과 원격 서버(SSH), 컨테이너(Docker·nginx·Compose) — 기반 지식.

## 교과서판에서 미니 프로젝트에 영향을 주는 변경 (각 판 부록 C 기준)

- 02: `astral-sh/setup-uv` 는 원 강의 v7 → 최신 v10 계열. Python 3.15 가 나왔지만 onnxruntime wheel 이 3.14 까지라 `<3.15` 상한 유지.
- 03: AWS Free 플랜은 가입 크레딧 + 활동 크레딧 구조. 버킷은 같은 리전 인스턴스만 키 없이 연결. 고정 IP 는 떼어 두면 과금. self-hosted runner 는 비공개 저장소에서만 권장.
- 미확인 항목(서울 리전 가격, 버킷 연결 반영 시간 등)은 각 판 부록 C 에 "미확인"으로 남아 있다.
