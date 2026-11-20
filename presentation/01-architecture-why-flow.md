---
title: 발표 — 아키텍처 설계의 이유와 Flow
description: 왜 이 구성인가를 내 언어로 — 도메인은 짧게, 기술 선택 이유와 흐름 중심
tags:
  - presentation
required: true
status: draft
---
# 발표 — 아키텍처 설계의 이유와 Flow

## 핵심 메시지 (내 언어로)

(연구자 위임 초안)

GPU 가 필요한 LLM 의 논문 판정을, GPU 없는 Lightsail 서버에서 싸게 서빙하려고 LLM 을 교사로 두고 CPU 에서 도는 작은 학생 모델을 배포했다([ADR-005](../decisions/ADR-005-student-model-snapshot.md)). 코드와 모델은 "판"을 둘로 나눠 각자 다른 길로 운영에 들어가고([강의 03 › 판은 둘 — 코드 판과 모델 판](../sources/lecture-index.md#공통-개념)), 어느 길이든 **검증을 통과해야만** 들어간다 — 코드는 pytest, 모델은 게이트 F1 과 parity([ADR-006](../decisions/ADR-006-gate-parity.md)). 되돌리기는 이미지는 그대로 두고 모델 판 포인터만 바꾼다.

## 도메인 (한 슬라이드)

**논문 제목·초록 → 주제 `coaching-leadership` 에 맞을 확률 `p(include)`** — [ADR-005](../decisions/ADR-005-student-model-snapshot.md).

- KMS 는 논문을 모아 로컬 LLM 이 포함/제외를 판정하는 연구용 지식 관리 시스템이다. 자동 수집은 [ADR-004](../decisions/ADR-004-kms-auto-collection-unfreeze.md) 범위에서만 한다.
- 2026-11-19 수집 867편(OpenAlex + KCI), 교사 라벨 include 641 · exclude 211 · uncertain 15([자율 진행 보고서](../reports/2026-11-19-autonomous-progress.md) 3절).
- 라벨 임계값은 KMS 와 같다(include ≥ 0.7, exclude ≤ 0.3, 사이는 uncertain).

## 기술 선택과 이유

강의 아키텍처는 예시일 뿐이다. 강의와 같은 것을 써도 이유는 내 말로 적는다.

> "이유 (내 언어)" 칸은 모두 **(연구자 위임 초안)** 이다 — ADR·워크플로에 적힌 사실만 옮겼고, 연구자가 자기 말로 다듬는다.

| 구성 요소 | 선택 | 이유 (내 언어) | 대안과 버린 이유 | ADR |
|---|---|---|---|---|
| 서빙 서버 | Lightsail 인스턴스 | 작업용 서버 Lightsail `Amazon_Linux_2026_kms`(시드니, 고정 IP `54.252.22.31`)에 배포했고, HTTPS 는 `https://54-252-22-31.sslip.io`(Let's Encrypt, HTTP→308)다. GPU 가 없으므로 CPU 학생 모델(ONNX)만 올린다. 기존 서비스(eta)와는 Caddy 가 80/443 을 받아 나눠 공존하고 HTTPS 도 Caddy 가 붙인다(PR [#21](https://github.com/metahomo/miniproject5_kms/pull/21)) | 새 인스턴스 — 이미 있는 인스턴스·고정 IP 를 두고 늘릴 이유가 없다(ADR-003 영향). LLM 직접 서빙 — GPU 가 필요해 이 서버에서 못 돌린다(ADR-005) | [ADR-003](../decisions/ADR-003-domain-server.md) · [ADR-007](../decisions/ADR-007-region-instance.md) (리전 시드니, 기존 인스턴스) |
| 데이터·모델 저장 | Lightsail 버킷 | 모델 파일(`models/<판>/`)과 `current.json` 의 정본을 버킷에 둔다. 서버가 읽는 것은 버킷, DB 는 이력·조회용 장부다. 같은 리전 인스턴스는 키 없이 버킷에 붙는다([강의 03 › 4 모델 배포 — 버킷에 서버 붙이기](../sources/lecture-index.md#필수-기능과-강의-절-대응)). 장부 DB 백업(pg_dump)도 같은 버킷으로 보낸다 | 장부 DB 에 모델 파일까지 — DB 는 이력·조회용으로 한정했다(ADR-002 영향). 버킷 JSON 만으로 이력 관리 — 이력 조회·집계·예측 로그에 약해 장부는 PostgreSQL 로 따로 둔다(ADR-002) | [ADR-002](../decisions/ADR-002-postgresql.md) · [ADR-007](../decisions/ADR-007-region-instance.md) (버킷 같은 리전) · [ADR-008](../decisions/ADR-008-ledger-db-ops.md) (운영 DB 는 서버 compose 컨테이너 + pg_dump → 버킷) |
| CI/CD | GitHub Actions — `ci.yml`(PR·main → pytest, `v*` 태그 → 이미지 → GHCR → 배포), `model.yml`, `rollback.yml`. 서버 작업은 서버의 self-hosted 러너(이름표 `lightsail`·`paperclf`) | 시험을 통과해야만 이미지를 만든다(`image` 가 `needs: test`). 서버를 바꾸는 잡(배포·승격·되돌리기)은 서버 안의 러너가 하므로 밖에서 SSH 를 열 필요가 없다. 배포 잡은 저장소 변수 `DEPLOY_ENABLED` 로 켜며, 켠 뒤 `v0.1.1` 태그에서 test·image·deploy 가 모두 성공했다([실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44513840582)) | GitHub 러너가 SSH 로 접속([강의 03 › 2 코드 배포 ①](../sources/lecture-index.md#필수-기능과-강의-절-대응)) — 서버 접속 키를 Actions 에 넣어야 하고, 작업 환경에는 그 키도 없었다(보고서 4절). self-hosted 러너는 비공개 저장소 권장이라, 공개 저장소 보호로 외부 기여자 PR 워크플로는 승인 필요로 바꾸고 서버 잡은 PR 이벤트에서 돌지 않게 했다(PR #21) | 별도 ADR 없음 — [아키텍처 개요](../architecture/overview.md) 구현 절, [강의 03 › 3 코드 배포 ② — 내 서버를 러너로](../sources/lecture-index.md#필수-기능과-강의-절-대응) · [ADR-009](../decisions/ADR-009-ledger-writer.md) (장부 기록은 서버 러너가 대행) |
| 학습 실행 위치 | GitHub 호스팅 러너(`ubuntu-24.04`) — `model.yml` 의 train·parity 잡 | 스냅숏에 해싱 특징이 들어 있어 학습이 오프라인으로 재현된다. 그래서 서버가 아니라 어떤 러너에서도 같은 결과가 나오고, 서버는 서빙·승격만 한다. 모델에 닿는 PR 에서도 병합 전에 학습·게이트·parity 를 본다(승격은 main 에서만) | 학습 때 OpenAlex·KCI API 로 원문을 다시 받기 — 외부 호출에 의존해 재현성이 떨어진다(ADR-005 선택지). 스냅숏에 원문 저장 — 공개 저장소에 초록 재배포(저작권)(ADR-005) | [ADR-005](../decisions/ADR-005-student-model-snapshot.md) · [강의 03 › model 워크플로](../sources/lecture-index.md#필수-기능과-강의-절-대응) |
| 게이트·parity | 게이트: 교사 라벨 고정 20% 시험지(178편)의 include F1 이 ① ≥ 0.80 ② ≥ 기준선 + 0.05 ③ ≥ 운영 F1 − 0.02, 셋 다. parity: 원본 sklearn ↔ 실제 서빙 이미지(ONNX) 확률 차이 ≤ 1e-5 | include 가 79% 라 "전부 include" 라고만 답해도 F1 0.8805 다 — 하한 하나로는 약해서 기준선 여유를 둔다(통과선 0.9305). parity 는 배포되는 바로 그 이미지로 본다. 변환기 옵션 `sublinear_tf=True` 하나로 0.0018 어긋나는 것을 실제로 잡았다 | 사람 검수 라벨 시험지 — Mac 의 KMS 에 사람 검수 라벨이 0편이라 지금은 불가. 확신 높은 교사 라벨만 — 교사가 relevance 를 거의 0.3/0.7/1.0 으로 내 "확신"의 뜻이 약하다. C 를 시험지로 고르기 — 시험지 과적합이라 미리 정한 4 유지(ADR-006) | [ADR-006](../decisions/ADR-006-gate-parity.md) · [강의 02 › 연습문제: 검증 게이트 · 일치 확인 (parity)](../sources/lecture-index.md#필수-기능과-강의-절-대응) |
| 롤백 | `rollback.yml` — 서버 러너가 버킷의 이전 판을 받아 띄운 뒤 `current.json` 을 마지막에 바꾼다. 이미지는 그대로, 모델 판만 바꾼다 | 코드 판과 모델 판을 따로 다루므로 되돌리기도 모델 판만 바꾼다. 포인터를 맨 마지막에 바꿔, 새 판이 뜨기 전에는 정본이 바뀌지 않는다. 되돌릴 판은 장부 DB 의 배포 이력에서 찾는다 | 판 이름을 자유 입력으로 — 형식 검사(`mYYYYMMDD-번호`)와 env 전달로 스크립트 주입을 막는다(`rollback.yml`). 이미 있는 판 덮어쓰기 — 승격 잡이 거부한다(`model.yml` promote) | [ADR-002](../decisions/ADR-002-postgresql.md) 영향 · [강의 03 › 5 되돌리기](../sources/lecture-index.md#필수-기능과-강의-절-대응) |

## Flow

그림은 [아키텍처 개요](../architecture/overview.md)를 따른다. 요청 경로·코드 배포 경로·모델 배포 경로·롤백 경로를 하나씩 설명한다.

1. **요청 경로** — 사용자 → `https://54-252-22-31.sslip.io`(작업용 서버 54.252.22.31, Let's Encrypt, HTTP→308) → paperclf API 컨테이너(FastAPI + onnxruntime, `/health` · `/predict` · `/model`) → 지금 띄운 모델 판의 ONNX 로 `p(include)` 를 낸다. 지금 운영은 app `v0.1.4` · model `m20261120-17` 이다(2026-11-20).
2. **코드 배포 경로(코드 판)** — PR·main push → `ci.yml` test(pytest) → 통과해야 image 빌드 → `v*` 태그면 GHCR 에 푸시 → `DEPLOY_ENABLED=true` 면 서버 러너가 `server.sh image` 로 교체. `v0.1.0` 태그 실행은 성공해 `ghcr.io/metahomo/miniproject5_kms/paperclf-api:v0.1.0` 을 올렸다([실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44453216170)). `v0.1.1` 태그에서는 서버 교체까지 성공했다([실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44513840582)). 코드 되돌리기도 실행했다 — `v0.1.0` 재배포([실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44453216170)) → 다시 `v0.1.1`([실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44513840582)), 모델은 그대로 유지.
3. **모델 배포 경로(모델 판)** — KMS 운영 DB(읽기 전용) → 교사 LLM 라벨(`labeler/teacher_label.py`) → 원문 없는 라벨 스냅숏(`data/snapshots/`) → main 에 push → `model.yml` train(학습 → 게이트 → ONNX → 모델 카드) → parity(서빙 이미지에 넣어 원본과 비교) → 통과하고 `DEPLOY_ENABLED=true` 면 promote(서버 러너가 버킷에 판 업로드 → 새 판으로 띄우기 → `current.json`). 게이트에서 실패하면 train 잡에서 멈추고 운영 모델은 그대로다. 정상 실행 parity 5.8e-7([실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44451897410)), 데이터 5% 모델은 F1 0.9021 로 게이트 실패([실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44452096551)). 작업용 서버에서 승격 m20261119-7([실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44514427871)) · m20261119-8([실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44514698446)). 배포를 켠 상태에서도 data_fraction=0.05 는 `F1 0.9021 < 기준선 0.8805 + 0.05` 로 멈추고 promote 를 건너뛰었고([실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44515846566)), parity_tol=1e-12 로 좁히면 최대 차이 5.8e-7 로 parity 에서 멈추고 promote 를 건너뛰었다([실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44519475156)). 버킷은 `paperclf-models-apse2`(small_1_0, $1/월)이고 인스턴스가 키 없이(리소스 액세스) 읽고 쓴다(반영까지 80초). 운영 장부 DB(PR #26, 서버 `/srv/ledger` 의 postgres:18.7, 127.0.0.1만)에는 통과 실행은 promote 가, 멈춘 실행은 record-failure 잡이 `model_versions` 에 기록하고 배포 기록은 `deployments` 에 남는다 — 정상 승격 m20261119-11([실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44519470540)). 2026-11-20 에는 새 논문 7편 스냅숏(PR #44)이 main 에 들어오자 사람 손 없이 학습·게이트 F1 0.9609·parity 5.5e-7·승격 m20261120-17 까지 돌았다([실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44643935701)).
4. **롤백 경로** — `rollback.yml` 을 판 이름과 함께 수동 실행 → 서버 러너가 버킷의 그 판을 받아 `server.sh model` 로 띄움 → `current.json` 을 바꿈. 되돌리기 →m20261119-7([실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44514983743)), 다시 앞으로 →m20261119-8([실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44515052182)) 모두 성공했고(실행 각 약 20초) 매번 `/health` 의 `model_version` 이 일치했다. 배포·승격 중 `/health` 가 실패하면 `server.sh` 가 직전 판으로 스스로 돌아간다(깨진 판 시연 37초, PR #36). 장부 백업은 승격·롤백 직후와 매일 03:17 UTC 에 버킷 `ledger/` 로 간다(14개 보관).

## 슬라이드 원고

보조 슬라이드 [metahomo.github.io/md-slides/miniproject5-kms](https://metahomo.github.io/md-slides/miniproject5-kms/) 의 3–9장이 이 절이다.

| # | 제목 | 내용 | 그림·시연 |
|---|---|---|---|
| 1 | 도메인 한 줄 | 논문 제목·초록 → `p(include)`. LLM 판정은 GPU 가 필요 → LLM 을 교사로, CPU 학생 모델을 배포(증류). 수집 867편, include 641 · exclude 211 · uncertain 15 | 보조 슬라이드 3장, 6장(데이터) |
| 2 | 전체 구성도 | 판은 둘: 코드 판(ci.yml) · 모델 판(model.yml) · 롤백(rollback.yml). 기술 선택 표의 이유를 구성 요소별로 말한다 | 구성도 — 보조 슬라이드 4장, 5장(기술 선택과 이유), [아키텍처 개요](../architecture/overview.md) 그림 |
| 3 | 코드 판 Flow | pytest 통과해야 이미지, `v*` 태그면 GHCR 푸시, 서버 러너가 교체. `v0.1.1` 태그로 test·image·deploy 성공, 코드 되돌리기 v0.1.0 → v0.1.1(모델 유지) | CI/CD 실행 화면 — [v0.1.1 태그 실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44513840582), [v0.1.0 재배포](https://github.com/metahomo/miniproject5_kms/actions/runs/44453216170), 보조 슬라이드 4장·9장 |
| 4 | 모델 판 Flow | 게이트 셋(하한 0.80 · 기준선 0.8805 + 0.05 · 운영 대비 −0.02). 전체 데이터 F1 0.9603 통과, 5% 모델 0.9021 실패. parity 허용 1e-5, Actions 5.8e-7, `sublinear_tf` 로 0.0018 어긋남을 잡은 사례 | 게이트·parity 결과 — [정상 실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44451897410), [5% 실패 실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44452096551), 보조 슬라이드 7장·8장 |
| 5 | 롤백 Flow | 이미지는 그대로, 버킷의 이전 판을 띄운 뒤 `current.json` 을 마지막에 바꾼다 | 롤백 실행 — [→m20261119-7](https://github.com/metahomo/miniproject5_kms/actions/runs/44514983743), [다시 →m20261119-8](https://github.com/metahomo/miniproject5_kms/actions/runs/44515052182) (매번 `/health` `model_version` 일치), 보조 슬라이드 4장·9장 |
| 6 | 현재 상태 | 코드 판 ✔, 모델 판 ✔, 서버 배포·승격·롤백 ✔(작업용 서버 54.252.22.31), 운영 장부 DB ✔(PR #26). 지금 운영 app v0.1.4 · model m20261120-17(새 데이터 7편으로 자동 재학습, PR #44). PR #19 · #20 · #21 병합, 이슈 #2 #3 #4 #5 #10 닫음, 보드 Done 13/16 | 보조 슬라이드 9장, [릴리스 v0.1.1](https://github.com/metahomo/miniproject5_kms/releases/tag/v0.1.1) |

## 예상 질문과 답

| 질문 | 답 | 근거 |
|---|---|---|
| LLM 을 바로 서빙하지 않고 왜 작은 모델인가? | Lightsail 에 GPU 가 없다. LLM 판정을 교사 라벨로 받아 CPU 에서 도는 해싱 TF-IDF + 로지스틱 회귀로 증류했다 | [ADR-005](../decisions/ADR-005-student-model-snapshot.md) |
| F1 0.96 은 정답률인가? | 아니다. 교사 라벨과의 일치도다. 교사가 틀리면 같이 틀린다. 사람 검수 시험지는 이슈 [#12](https://github.com/metahomo/miniproject5_kms/issues/12) 에서 다룬다 | [ADR-006](../decisions/ADR-006-gate-parity.md) 영향 |
| 왜 하한 하나가 아니라 게이트가 셋인가? | include 79% 라 "전부 include" 도 F1 0.8805 다. 기준선 + 0.05 가 사실상 통과선(0.9305)이고, 운영 모델보다 크게 나빠지는 것도 막는다 | ADR-006 |
| parity 를 ONNX 파일이 아니라 이미지로 보는 이유는? | 배포되는 바로 그 이미지가 같은 답을 내야 한다. 변환 옵션 하나(`sublinear_tf=True`)로 0.0018 어긋난 실제 사례가 있었다 | ADR-005 확인한 사실, ADR-006 |
| 공개 저장소에 self-hosted 러너는 위험하지 않은가? | 외부 기여자 PR 워크플로는 승인 필요로 바꿨고, 서버 잡은 PR 이벤트에서 돌지 않는다. 이 저장소 전용 러너만 등록한다 | PR [#21](https://github.com/metahomo/miniproject5_kms/pull/21) |
| 공개 저장소에 논문 초록을 올려도 되나? | 올리지 않는다. 스냅숏에는 공개 식별자·라벨·해싱 특징만 있고 원문으로 되돌릴 수 없다 | ADR-005 |
| 서버 배포는 실제로 되었나? | 됐다. 작업용 서버 54.252.22.31(`https://54-252-22-31.sslip.io`)에 `v0.1.1` 태그로 배포했고, 승격 m20261119-7·8, 되돌리기 →7, 다시 앞으로 →8 마다 `/health` 의 `model_version` 이 일치했다. 지금 운영은 app v0.1.4 · model m20261120-17. 서버는 Tailscale(tailnet)에 등록했고, SSH 22번은 아직 열려 있다 — 닫는 시점은 연구자 결정 대기(이슈 #1·#8) | [v0.1.1 배포](https://github.com/metahomo/miniproject5_kms/actions/runs/44513840582), [승격 →7](https://github.com/metahomo/miniproject5_kms/actions/runs/44514427871) · [→8](https://github.com/metahomo/miniproject5_kms/actions/runs/44514698446), [되돌리기 →7](https://github.com/metahomo/miniproject5_kms/actions/runs/44514983743) · [다시 →8](https://github.com/metahomo/miniproject5_kms/actions/runs/44515052182), [릴리스 v0.1.1](https://github.com/metahomo/miniproject5_kms/releases/tag/v0.1.1) |
