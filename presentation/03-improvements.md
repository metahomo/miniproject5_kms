---
title: 발표 — 강의 대비 개선점
description: 강의 예시 아키텍처에서 무엇을 왜, 어떻게 바꿨는지 (옵션)
tags:
  - presentation
required: false
status: draft
---
# 발표 — 강의 대비 개선점

## 핵심 메시지 (내 언어로)

(연구자 위임 초안) 강의의 뼈대(코드 판·모델 판·게이트·parity·롤백)는 그대로 두었다. 내가 바꾼 것은 "검증이 실제로 무언가를 막는가"다. 합성 데이터 대신 실제 논문 데이터를 썼더니 하한 하나짜리 게이트는 "전부 include"(F1 0.88)도 통과시켰고, 그래서 게이트를 셋으로 늘렸다. parity 는 실제 서빙 이미지로 돌렸더니 변환기 옵션 하나에서 0.0018 어긋남을 잡았다. 규칙은 문서가 아니라 워크플로의 `needs` 와 DB 트리거가 지키게 했다.

## 개선 목록

강의 쪽 설명은 [강의 자료 색인](../sources/lecture-index.md)의 파일·절을 밝힌다.

발표는 조감도 문서(claude.ai)의 "강의 대비 개선점" 절로 한다. 이 표는 그 절의 근거 사본이다. 이유 칸은 연구자 위임(2026-11-19 "연구자가 해야 할 일도 바로 해줘")으로 사령관이 연구자 말투로 쓴 초안이다 — 사실은 바꾸지 않았고, 연구자가 읽고 확정한다.

| # | 강의(파일 › 절) | 내 방식 | 이유 (연구자 위임 초안) | 증거·ADR |
|---|---|---|---|---|
| 1 | 02 › 연습문제 6·7, 03 › 7.5 | 배포 뒤 `/health` 확인을 네 번째 검증 다리로, 실패 시 이전 판 자동 복귀 | 검증을 통과한 모델이라도 서버에서 실제로 대답해야 배포가 끝난 것이라고 봤다. 그래서 새 판이 `/health` 에 자기 `model_version` 으로 답하지 않으면 바로 이전 판으로 돌아가게 했다 | 작업용 서버에서 실행 — 승격 [m20261119-7](https://github.com/metahomo/miniproject5_kms/actions/runs/44514427871) · [m20261119-8](https://github.com/metahomo/miniproject5_kms/actions/runs/44514698446), 되돌리기 [→7](https://github.com/metahomo/miniproject5_kms/actions/runs/44514983743) · [다시 →8](https://github.com/metahomo/miniproject5_kms/actions/runs/44515052182) 마다 `/health` 의 `model_version` 일치. `deploy/lightsail/server.sh`(health 확인 후 실패 시 `PREV` 로 복귀), `ci.yml` deploy · `model.yml` promote 잡 — [아키텍처 개요](../architecture/overview.md) |
| 2 | 03 › 7.7 모델 카드 · 7.11 | PostgreSQL 장부 + 트리거 — 게이트·parity 미통과 모델의 배포 기록 거부 | 모델 이력·지표·예측 로그를 파일을 뒤지지 않고 질의 한 줄로 보고 싶었다. 그리고 "검증 안 된 모델은 배포하지 않는다"는 규칙을 사람이 아니라 DB 가 거부하게 만들었다 | 운영 DB(PR #26, 서버 `/srv/ledger` postgres:18.7)에서 게이트 미통과 판 m20261119-9 의 배포 기록을 트리거가 `ERROR: model m20261119-9 has not passed gate and parity` 로 거부, 정상 승격 [m20261119-11](https://github.com/metahomo/miniproject5_kms/actions/runs/44519470540). 앞서 2026-11-18 로컬 시험: 미통과 모델 → `ERROR: model m20261118-1 has not passed gate and parity`, 통과 모델 → `INSERT 0 1` — [ADR-002](../decisions/ADR-002-postgresql.md), [AI 활용 기록](../ai-usage/2026-11-18-postgresql-ledger.md) |
| 3 | 02 › 연습문제 6 | 시험지를 사람 검수 라벨로 | 교사(LLM) 답으로 채점하면 교사가 틀린 것까지 맞았다고 나온다. 사람 검수 라벨이 정답에 더 가깝다고 생각했다 | 확정: Mac KMS 에 사람 검수 라벨 0편이라 지금은 불가 → 교사 라벨 고정 분할(열쇠 해시 20%, 178편)을 시험지로 확정. 사람 검수 시험지가 생기면 시험지만 바꾸고 기준을 다시 정한다 — [ADR-006](../decisions/ADR-006-gate-parity.md), 이슈 #12 |
| 4 | 03 › 7.8 · 7.12 | KMS 가 로그온마다 새 논문 자동 수집 — 새 데이터의 원천 | 강의는 새 데이터를 가정하지만, 나는 새 데이터가 실제로 생기는 구조를 원했다 | 동작(작업 결과 0) — [ADR-004](../decisions/ADR-004-kms-auto-collection-unfreeze.md) |
| 5 | 02 › 3.3 | 사령관(CLAUDE.md)·부관(AGENTS.md) 이원 지침, 위임 지시서 5요소 | 에이전트 여럿에게 일을 나눠 주면 누가 어디까지 손대는지, 무엇을 증거로 내는지가 흐려진다. 지침을 둘로 나눠 범위와 증거를 통제했다 | [사령관 지침](../CLAUDE.md) |
| 6 | (강의에 없음) | GitHub 이슈·마일스톤·칸반 + 강의 순서 대조표 | 진행 상황을 말로 설명하지 않고, 증거를 링크로 한 곳에 모아 두고 싶었다 | 조감도 "GitHub 영역별 세부", [칸반보드 #12](https://github.com/users/metahomo/projects/12) |
| 7 | 03 › 4장 | 도메인 연결, HTTPS 를 공개 조건으로 | 로그인도 HTTPS 도 없는 서비스를 밖에 여는 것은 하지 않기로 했다 | HTTPS 켬 — `https://54-252-22-31.sslip.io`(Let's Encrypt, HTTP→308). 인증·사용량 제한은 아직 없음 — [ADR-003](../decisions/ADR-003-domain-server.md) |
| 8 | 02 › 8.2 데이터(합성) | 실제 데이터: GPU LLM 판정을 교사로, CPU 학생 모델로 증류 | 서빙할 Lightsail 에는 GPU 가 없다. 비싼 LLM 판단은 내 PC 에서 한 번만 하고, 그 판단을 배운 가벼운 모델을 싸게 서빙한다 | Actions 모델 판 m20261119-1 F1 0.9603 — [ADR-005](../decisions/ADR-005-student-model-snapshot.md) |
| 9 | (강의에 없음) | 공개 저장소에 원문 대신 해싱 특징만 올림 | 초록에는 저작권이 있다. 해싱 특징만 올리면 학습은 누구나 재현할 수 있고, 원문은 되살릴 수 없다 | ADR-005 |
| 10 | 02 › 9.2~9.7 Go·Rust | 서빙은 Python+ONNX 한 종류, parity 는 원본 ↔ 실제 서빙 이미지 | 배포되는 바로 그 이미지를 검사해야 의미가 있다고 봤다. 실제로 변환기 옵션(`sublinear_tf`) 하나 때문에 확률이 0.0018 어긋나는 것을 이 검사로 잡았다 | [ADR-006](../decisions/ADR-006-gate-parity.md), ADR-005 "확인한 사실" |
| 11 | 03 › 7.5 model.yml(수동 실행) | 모델에 닿는 PR 에서도 학습·게이트·parity, 승격은 main 에서만 | 병합하고 나서가 아니라 병합하기 전에 모델 품질을 보고 싶었다 | PR #19 의 model 실행 |
| 12 | 02 › 8.3 "일부러 덜 학습" | 게이트를 하한·기준선 여유·운영 대비 하락폭 셋으로 | 데이터가 불균형하다(include 79%). "전부 include" 라고만 답해도 F1 이 0.88 이라 하한 0.80 하나로는 약한 모델을 못 거른다 | ADR-006 — 데이터 5% 모델 F1 0.9021 → 하한은 넘지만 기준선+0.05(0.9305) 미달로 실패 |

## 슬라이드 원고

보조 슬라이드 [13–14장](https://metahomo.github.io/md-slides/miniproject5-kms/)에 맞춘 말하기 원고. 14장 표의 여섯 줄 가운데 수치 근거가 있는 넷(#2 · #8 · #10 · #12)을 중심으로 말하고, 시간이 부족하면 #8 · #12 · #10 셋만 말한다(슬라이드 발표자 메모와 같음).

| # | 제목 | 내용 | 그림·시연 |
|---|---|---|---|
| 13 | 3. 강의 대비 개선점 | 장 표지. "강의 뼈대는 그대로 두고, 검증이 실제로 무언가를 막도록 바꿨다" 한 문장으로 넘어간다 | 표지 슬라이드 |
| 14-1 | 강의보다 한 걸음 더 — 증류 (#8) | 강의는 합성 데이터. 나는 KMS 가 모은 실제 논문 867편에 내 PC 의 LLM(qwen3 4B)이 교사로 라벨을 붙이고, CPU 로 도는 학생 모델(해싱 TF-IDF + 로지스틱 회귀)이 배운다. Actions 모델 판 m20261119-1 게이트 F1 **0.9603**. GPU 없는 Lightsail 에서 LLM 판단을 싸게 서빙하려는 것 | 14장 표 1행. 필요하면 [Actions 실행](https://github.com/metahomo/miniproject5_kms/actions/runs/44451140771) |
| 14-2 | 게이트 셋 (#12) | 하한 0.80 · 기준선(전부 include 0.8805)+0.05 · 운영 대비 −0.02. 데이터 5% 모델은 F1 0.9021 로 하한은 넘지만 둘째 조건에서 멈춘다 — 하한 하나였다면 통과했을 모델 | 14장 표 3행, 앞 6장 "게이트" 표를 다시 가리킨다 |
| 14-3 | parity 는 실제 이미지로 (#10) | 강의는 Go·Rust 서빙 예시. 나는 Python+ONNX 한 종류로 줄이고 원본 ↔ 서빙 이미지의 확률을 비교한다. `sublinear_tf=True` 에서 **0.0018** 어긋남을 잡아 끄고 4.4e-9, 현재 5.4e-7(허용 1e-5) | 14장 표 5행, 앞 7장 "parity" |
| 14-4 | 규칙을 DB 가 지킨다 (#2) | 모델 카드 대신 PostgreSQL 장부. 게이트·parity 미통과 모델을 배포 기록에 넣으면 트리거가 `ERROR: … has not passed gate and parity` 로 거부한다(2026-11-18 로컬 시험, 운영 DB 에서도 m20261119-9 거부 확인) | 14장 표 2행. 운영 DB 는 서버 `/srv/ledger`(PR #26), [정상 승격 m20261119-11](https://github.com/metahomo/miniproject5_kms/actions/runs/44519470540) |

## 예상 질문과 답

| 질문 | 답 | 근거 |
|---|---|---|
| 교사(LLM) 라벨로 채점하면 자기 채점 아닌가? | 맞다. 게이트 F1 은 정답률이 아니라 "교사와 얼마나 일치하나"다. Mac 의 KMS 에는 사람 검수 라벨이 0편이라 지금은 교사 라벨 고정 분할(178편)이 최선이고, 사람 검수 시험지가 생기면 시험지만 바꾸고 기준을 다시 정한다 | ADR-006 선택지·영향, ADR-005 영향 |
| 기준선 + 0.05 는 왜 필요한가? | include 가 79% 라 "전부 include" 만 답해도 F1 0.8805 다. 데이터 5% 모델(F1 0.9021)은 하한 0.80 을 넘지만 이 조건(0.9305)에서 걸린다 | ADR-006 결정·확인한 사실 |
| 하이퍼파라미터는 튜닝했나? | C 를 1·4·16 으로 시험했다(F1 0.938 / 0.960 / 0.964). 게이트 시험지로 고르면 시험지에 과적합하므로 미리 정한 4 를 유지했다 | ADR-006 확인한 사실 |
| Go·Rust 서빙을 왜 안 했나? | 서빙 언어를 늘리면 parity 로 확인할 대상도 늘어난다. 한 종류로 줄이고, 배포되는 바로 그 이미지를 검사하는 쪽을 택했다. 그 검사로 `sublinear_tf` 0.0018 어긋남을 실제로 잡았다 | ADR-006, ADR-005 확인한 사실 |
| 버킷의 모델 카드로 충분하지 않나, DB 는 왜? | 서버가 읽는 정본은 여전히 버킷(`current.json`)이다. DB 는 이력·지표·예측 로그를 질의로 보고, 미통과 모델 배포 기록을 트리거로 거부하는 장부다. 운영 배치는 서버 `/srv/ledger` 의 postgres:18.7(127.0.0.1만, PR #26), 백업은 승격·롤백 직후와 매일 03:17 UTC 에 버킷 `ledger/` 로 간다(14개 보관) | ADR-002 결정·영향, PR #26 |
| `/health` 확인 다리와 자동 복귀는 실제로 돌려 봤나? | `/health` 확인은 돌렸다. 작업용 서버에서 승격 m20261119-7·8, 되돌리기 →7, 다시 앞으로 →8 마다 `/health` 의 `model_version` 이 일치했다. 확인 실패 때 이전 판으로 자동 복귀하는 경우의 실행 증거는 아직 없다 | [승격 →7](https://github.com/metahomo/miniproject5_kms/actions/runs/44514427871) · [→8](https://github.com/metahomo/miniproject5_kms/actions/runs/44514698446), [되돌리기 →7](https://github.com/metahomo/miniproject5_kms/actions/runs/44514983743) · [다시 →8](https://github.com/metahomo/miniproject5_kms/actions/runs/44515052182), `deploy/lightsail/server.sh` |
| 원문 없이 해싱 특징만으로 학습이 재현되나? | 스냅숏에 특징·라벨·분할·교사 판이 들어 있어 학습은 오프라인으로 재현된다. 대신 사람이 스냅숏을 읽어 검수할 수는 없고, 교사 JSONL 은 로컬에만 있다 | ADR-005 선택지·결정 |
