---
title: ADR-009 장부 기록은 서버의 self-hosted runner 와 API 가 localhost 로 한다
description: 학습 결과·배포 이력은 model.yml promote 잡이, 예측 로그는 API 가 쓴다. DB 는 밖에 열지 않는다. 이슈 #15
tags:
  - adr
  - database
  - cicd
status: accepted
date: 2026-11-19
decider: "연구자(위임: 사령관 작성). 이슈 #15"
---
# ADR-009 장부에 누가 쓰나

## 배경

장부 DB 는 서버 안 `127.0.0.1` 에만 열린다([ADR-008](./ADR-008-ledger-db-ops.md)). 그런데 학습은 GitHub 호스팅 러너(`ubuntu-24.04`)에서 돈다. 학습 결과를 장부에 어떻게 넣을지 결정 이슈 [#15](https://github.com/metahomo/miniproject5_kms/issues/15)가 열려 있었다. 저장소 `metahomo/miniproject5_kms` 는 **공개**다. 연구자가 2026-11-19 "연구자가 해야 할 일도 바로 해줘"를 지시해 사령관이 권장안 A 로 확정했다.

## 선택지

| 선택지 | 장점 | 단점 |
|---|---|---|
| **A. 서버의 self-hosted runner(promote 잡)가 기록, API 는 localhost 로 직접** | DB 를 밖에 열지 않는다. promote 잡은 이미 서버에서 돈다(`runs-on: [self-hosted, lightsail, paperclf]`) | 게이트에서 멈춘 실행은 promote 까지 가지 않아 실패 이력을 따로 넘겨야 한다 |
| B. 호스팅 러너가 DB 에 직접 접속 | 구현이 단순하다 | DB 포트를 인터넷에 열어야 한다. 공개 저장소라 워크플로·로그가 모두에게 보인다 — **기각** |
| C. 버킷 경유(러너가 JSON 을 버킷에 두고 서버가 주워 기록) | DB 를 열지 않는다 | 줍는 작업·중복 처리를 따로 만들어야 한다 |
| D. 관리형 DB 를 public 으로 | 어디서나 접속 | 비용([ADR-008](./ADR-008-ledger-db-ops.md) 대안 B)에 공개 노출까지 더해진다 |

## 결정

- **학습 결과(`datasets`·`model_versions`)**: `model.yml` 의 `promote` 잡이 `train`·`parity` 잡의 모델 카드·parity 결과(artifact)를 받아 기록한다.
- **순서**: `datasets`·`model_versions` 기록 → 서버 교체 → `/health` 확인 → `deployments` 기록 → 버킷 `current.json` 마지막([데이터 모델](../architecture/data-model.md) 27행의 순서 규칙 앞에 장부 기록을 붙인 것).
- **게이트 실패 이력도 남긴다**: 실패한 실행은 실패 요약을 artifact 로 올리고, 다음 `promote` 실행이 그것을 받아 기록한다.
- **예측 로그(`predictions`)**: API 컨테이너가 localhost 로 직접 쓴다.
- **DB 는 밖에 열지 않는다.**

## 근거 (연구자의 언어로 채울 칸)

(2026-11-19 연구자 위임으로 사령관 작성 — 연구자가 말로 다듬을 수 있다)

- 저장소가 공개라 DB 를 인터넷에 여는 대안(B·D)은 받아들이기 어렵다.
- `promote` 잡이 이미 서버의 runner 에서 돌기 때문에, 장부 기록을 거기에 붙이면 새 경로를 만들지 않아도 된다.
- 연구자가 2026-11-19 "연구자가 해야 할 일도 바로 해줘"라고 위임해 권장안 A 를 확정했다.

## 영향

- 모델 카드에 **데이터 sha256 · `onnx_sha256` · `parity_max_diff`** 필드가 더 필요하다(장부 `datasets`·`model_versions` 칸을 채우려면). 이 ADR 에서는 코드를 고치지 않는다 — 별도 작업.
- 게이트 실패 요약 artifact 와 "다음 promote 가 줍는" 단계도 별도 작업이다. artifact 보관 기간 안에 다음 promote 가 돌지 않으면 그 실패 이력은 빠질 수 있다.
- `DEPLOY_ENABLED` 가 꺼져 있으면 `promote` 가 돌지 않으므로 장부에도 기록되지 않는다.
