---
title: 발표 — 시연 대본
description: R1~R5 를 한 흐름(코드 배포 → 데이터·학습·게이트 → 승격 → 롤백)으로 5~7분 안에 보이는 대본. 단계마다 막히면 쓸 증거 링크가 붙어 있다
tags: [presentation]
required: false
status: draft
---

# 발표 — 시연 대본

## 핵심 메시지 (내 언어로)

나쁜 코드·나쁜 모델은 사람 손 없이 서버 앞에서 멈추고, 좋은 모델은 자동으로 올라가며, 문제가 생기면 한 번에 직전 판으로 돌아간다 — 그 기록은 모두 장부에 남는다.

## 근거 문서

- [코드 배포 런북](../runbooks/deploy-code.md) — `/health`, 태그 배포, 공개 API 보호(토큰·사용량 제한)
- [모델 승격 런북](../runbooks/promote-model.md) — `model.yml` 입력, 게이트 시험
- [롤백 런북](../runbooks/rollback.md) — 모델·코드 되돌리기, 다시 앞으로
- [작업용 서버 런북](../runbooks/work-server.md) — 서버 접속(`S=ec2-user@54.252.22.31`), HTTPS, 장부 `ledger.py status`
- [학습·검증 기록 색인](../experiments/index.md) — 실행별 게이트·parity·승격 결과
- 워크플로 입력: `model.yml` 의 `data_fraction`(기본 `1.0`)·`parity_tol`(기본 `1e-5`), `rollback.yml` 의 `version`(필수, 형식 `m<8자리 날짜>-<번호>`)

## 1. 준비물

- [ ] 발표 직전: 노트북 Claude Code 에서 `조감도 아티팩트 갱신해줘` → 발표용 조감도 <https://claude.ai/artifact/AdmNgiPUDRdAk1dp5uojxm> 가 최신인지(맨 위 "마지막 갱신" 시각) 확인

### 시연 전날

- [ ] 저장소 변수 세 개가 있다: `gh variable list` → `DEPLOY_ENABLED=true`, `MODEL_BUCKET=paperclf-models-apse2`, `AWS_REGION=ap-southeast-2` ([롤백 런북](../runbooks/rollback.md#전제조건))
- [ ] 러너 `paperclf` 온라인: 저장소 Settings → Actions → Runners
- [ ] 되돌릴 판이 버킷에 있다(서버에서): `aws s3 ls s3://paperclf-models-apse2/models/`
- [ ] 되돌릴 태그의 ci 실행이 있다(⑨용): `gh run list --workflow ci.yml --branch <직전 태그> -L 1`
- [ ] 서버 상태(서버에서): `bash /srv/paperclf/server.sh status` → `.env` 의 TAG·MODEL_VERSION 을 적어 둔다
- [ ] 토큰 위치만 확인한다: 서버 `/srv/paperclf/.env` 의 `API_TOKEN`(권한 600). **값은 화면·슬라이드·채팅에 띄우지 않는다** — 시연 명령은 서버 안에서 변수 `T` 로만 읽는다
- [ ] 아래 "막히면" 칸의 링크를 브라우저 탭에 미리 열어 둔다

### 시연 직전 (5분 전)

- [ ] 밖에서 `curl -fsS https://54-252-22-31.sslip.io/health` → `"status":"ok"`, `app_version`·`model_version` 을 메모(① 에서 말할 값)
- [ ] 터미널 두 개: 왼쪽 Mac(`gh`), 오른쪽 서버 셸(`S=ec2-user@54.252.22.31` 후 `ssh "$S"`)
- [ ] Actions 탭(`model`·`rollback` 워크플로 화면)을 브라우저에 띄워 둔다
- [ ] 다른 `model`·`rollback`·`ci` 실행이 돌고 있지 않다 — 서버 잡은 `concurrency: lightsail` 한 줄로 서서 기다린다

## 2. 대본

**학습 실행은 수 분 걸린다.** 그래서 ④⑤⑥ 세 실행은 ④ 에서 **한꺼번에 시작만** 하고, 앞서 찍어 둔 결과 링크로 설명한 뒤 ①②③ 은 이미 끝냈으니 ⑧ 전후에 돌아와 실제 결과를 확인한다. train·parity 잡은 GitHub 러너(ubuntu)에서 동시에 돌고, 서버 잡(promote·record-failure)만 서버 러너를 쓴다.

| 순서 | 말할 것(한 문장) | 화면·명령(복사해 쓸 수 있게) | 기대 결과 | 막히면(증거 링크) | 걸리는 시간 |
|---|---|---|---|---|---|
| ① 지금 판 (R1·R2) | "Lightsail 서버가 HTTPS 로 지금 돌고 있는 코드 판과 모델 판을 스스로 알려 줍니다." | Mac: `curl -fsS https://54-252-22-31.sslip.io/health` | `"status":"ok"`, `app_version`(이미지 태그), `model_version`(운영 모델 판, 2026-11-20 기준 [m20261120-17](../experiments/2026-11-20-m20261120-17.md)) | 코드 배포 v0.1.1 [44513840582](https://github.com/metahomo/miniproject5_kms/actions/runs/44513840582) | 30초 |
| ② 인증 401 → 200 (R4) | "예측 API 는 공개 주소에 있지만 토큰 없이는 거절하고, 토큰은 서버 `.env` 에만 있습니다." | 서버에서 토큰 없이(런북 명령에서 `Authorization` 줄만 뺀 것): `curl -fsS -H 'content-type: application/json' -d '{"title":"…"}' localhost:8080/predict` → 이어서 런북 그대로: `T=$(grep ^API_TOKEN= /srv/paperclf/.env \| cut -d= -f2); curl -fsS -H "Authorization: Bearer $T" -H 'content-type: application/json' -d '{"title":"…"}' localhost:8080/predict` | 첫 번째는 `401` 로 실패, 두 번째는 예측 JSON(`200`) | 2026-11-19 사령관 확인(v0.1.3 배포 직후): 밖에서 토큰 없이 `401`, 서버에서 토큰으로 `200` — [발표 4절](./04-service-for-ai.md), PR #30 | 40초 |
| ③ (선택) 사용량 제한 429 | "한 IP 가 1분에 60번을 넘으면 `429` 와 `Retry-After` 로 막습니다." | 서버에서(토큰을 넣어 1분 안에 65번): `T=$(grep ^API_TOKEN= /srv/paperclf/.env \| cut -d= -f2); for i in $(seq 1 65); do curl -s -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $T" -H 'content-type: application/json' -d '{"title":"t"}' https://54-252-22-31.sslip.io/predict; done \| sort \| uniq -c` → 이어서 Mac 에서 `/health` 의 `guard` | `60 200`, `5 429`, `guard.rejected_rate` 증가 | 2026-11-19 사령관 확인: `60 200` · `5 429`, `/health` guard `rejected_rate: 5` (PR #30) | 20초 |
| ④ 데이터 변경 → 학습·게이트 차단 (R3) | "일부러 데이터 5% 로 약한 모델을 만들면 게이트가 사람 대신 멈춰 세웁니다." | Mac에서 세 실행을 **연달아 시작**: `gh workflow run model.yml --ref main -f data_fraction=0.05` · `gh workflow run model.yml --ref main -f parity_tol=1e-12` · `gh workflow run model.yml --ref main` → 브라우저 Actions 의 `model` 화면에 세 줄이 뜨는 것만 보이고, 설명은 증거 링크로 | train 의 "검증 게이트" 실패, parity·promote skipped, record-failure 가 장부에 한 건 | 게이트 차단 m20261119-9 (F1 0.9021 < 0.8805+0.05) [44515846566](https://github.com/metahomo/miniproject5_kms/actions/runs/44515846566) · 기록 [m20261119-9](../experiments/2026-11-19-m20261119-9.md) | 시작 20초 + 링크 설명 40초 |
| ⑤ parity 차단 (R3) | "게이트를 통과해도, 서빙 이미지(ONNX)가 원본과 다른 확률을 내면 승격하지 않습니다 — 허용 오차를 1e-12 로 좁혀 일부러 실패시켰습니다." | (④ 에서 이미 시작) 브라우저: 두 번째 실행 화면 | train 성공, parity 실패(최대 차이 약 5.8e-7 > 1e-12), promote skipped | parity 차단 m20261119-12 [44519475156](https://github.com/metahomo/miniproject5_kms/actions/runs/44519475156) · 기록 [m20261119-12](../experiments/2026-11-19-m20261119-12.md) | 40초 |
| ⑥ 정상 실행 → 승격 (R3·R4) | "기본값으로 돌린 모델은 게이트·parity 를 통과해 버킷에 올라가고, 서버가 새 판으로 바뀝니다." | (④ 에서 이미 시작) 실행 ID 찾기: `gh run list --workflow model.yml -L 3` → `gh run watch <실행 ID> --exit-status` → 끝나면 `curl -fsS https://54-252-22-31.sslip.io/health` | train → parity → promote 셋 다 성공, `model_version` = 새 판 `m<오늘 UTC 날짜>-<실행 번호>` | 승격 m20261119-11 [44519470540](https://github.com/metahomo/miniproject5_kms/actions/runs/44519470540) · m20261119-8 [44514698446](https://github.com/metahomo/miniproject5_kms/actions/runs/44514698446) | 설명 40초 (실행 자체는 미확인 — 끝날 때까지 다음 단계 진행) |
| ⑦ 롤백 → 다시 앞으로 (R5) | "새 판이 문제라면 이미지는 그대로 두고 모델 판만 직전 판으로 되돌리고, 같은 방법으로 다시 앞으로 갑니다." | **⑥ promote 가 끝난 뒤에만**: `gh workflow run rollback.yml --ref main -f version=m20261120-17` → `gh run watch <실행 ID> --exit-status` → `curl -fsS https://54-252-22-31.sslip.io/health` → 다시 앞으로: `gh workflow run rollback.yml --ref main -f version=<⑥ 새 판>` | 첫 실행 뒤 `model_version` = m20261120-17(시연 전 운영 판), 두 번째 뒤 = ⑥ 새 판 | 되돌리기 8 → 7 [44514983743](https://github.com/metahomo/miniproject5_kms/actions/runs/44514983743) · 다시 앞으로 7 → 8 [44515052182](https://github.com/metahomo/miniproject5_kms/actions/runs/44515052182) | 1분 |
| ⑧ 장부 조회 (R3·R5) | "통과든 실패든 실행마다 한 건, 배포·되돌리기마다 한 건이 장부에 남습니다." | 서버에서: `python3 /srv/ledger/ledger.py status` (Mac 에서는 `ssh "$S" 'python3 /srv/ledger/ledger.py status'`) | 건수·운영 중인 판 — 오늘 ④⑤ 의 멈춘 실행과 ⑥⑦ 의 배포가 늘어 있다 | 2026-11-19 밤 출력: datasets 2 · model_versions 6(실패 2) · deployments 6, 운영 m20261120-17 (2026-11-20 리허설) — 장부 사본 [학습·검증 기록 색인](../experiments/index.md) | 40초 |
| ⑨ (시간 나면) 코드 되돌리기 (R2·R5) | "코드도 같은 생각입니다 — 직전 태그의 ci 실행을 다시 돌리면 그 이미지로 돌아가고, 모델은 그대로입니다." | `gh run list --workflow ci.yml --branch <직전 태그> -L 1` → `gh run rerun <실행 ID>` → `gh run watch <실행 ID> --exit-status` → `curl -fsS https://54-252-22-31.sslip.io/health` | `app_version` = 직전 태그, `model_version` 그대로 | 코드 되돌리기 v0.1.1 → v0.1.0 [44453216170](https://github.com/metahomo/miniproject5_kms/actions/runs/44453216170) · 다시 앞으로 [44513840582](https://github.com/metahomo/miniproject5_kms/actions/runs/44513840582) | 생략 가능 (실행 시간 미확인 — 발표 중엔 링크로만 권함) |

### 돌아와 확인하는 순서

1. ④ 직후 ①②③ 은 이미 끝났으므로, ⑤⑥ 링크 설명 뒤 Actions 화면으로 돌아가 세 실행 상태를 본다.
2. ⑥ promote 가 아직이면 ⑧ 장부 조회를 먼저 하고, 끝나면 `/health` 로 새 판 → ⑦ 롤백.
3. 발표 시간이 끝날 때까지 ⑥ 이 안 끝나면 ⑦ 은 증거 링크로만 설명하고, 롤백 실행은 하지 않는다(아래 위험 표 "낡은 실행").

## 3. 시간표 (총 7분 이내)

시간은 배정(계획)이다. 실제 실행 소요는 문서에 기록이 없어 미확인.

| 구간 | 단계 | 배정 | 누적 |
|---|---|---|---|
| 도입 | ① 지금 판 | 0:30 | 0:30 |
| 공개 API | ② 401 → 200, ③ guard(선택) | 1:00 | 1:30 |
| 학습 시작·게이트 | ④ 세 실행 시작 + 게이트 차단 설명 | 1:00 | 2:30 |
| parity | ⑤ | 0:40 | 3:10 |
| 승격 | ⑥ 설명(+ 끝났으면 `/health`) | 0:40 | 3:50 |
| 장부 | ⑧ | 0:40 | 4:30 |
| 롤백 | ⑦ 되돌리기 → 다시 앞으로 (⑥ 끝난 뒤) | 1:00 | 5:30 |
| 여유 | 대기·질문, 시간 나면 ⑨ 는 링크로 | 1:30 | 7:00 |

## 4. 위험과 대응

| 위험 | 알아채는 법 | 대응 |
|---|---|---|
| 러너 `paperclf` 오프라인 | promote·rollback·record-failure 잡이 "Waiting for a runner" 로만 있음 | 서버에서 러너 서비스 상태 확인([코드 배포 런북](../runbooks/deploy-code.md#실패-시)). 발표 중엔 고치지 말고 해당 단계 증거 링크로 넘어간다 |
| 실행 대기열 | 서버 잡은 `concurrency: { group: lightsail }` 로 한 번에 하나씩, `cancel-in-progress: false` 라 앞 잡이 끝날 때까지 기다린다 | 시연 직전 다른 실행이 없는지 본다. ⑥ promote 와 ⑦ rollback 이 겹치지 않게 ⑦ 은 ⑥ 이 끝난 뒤에만 |
| 낡은 실행 | promote 의 "낡은 실행인지" 단계가 실패("낡은 실행 — 승격하지 않는다") | ⑥ 이 시작된 뒤 ⑦ 롤백으로 `current.json` 을 바꾸면 ⑥ 은 승격하지 않는다. 그래서 ⑦ 은 ⑥ 이 끝난 뒤. 이미 났다면 "포인터를 지키는 안전장치"로 설명하고 ⑥ 증거 링크로 넘어간다 |
| Let's Encrypt·HTTPS | `curl` 이 인증서 오류 또는 접속 실패 | 반복 재시작 금지(발급 한도). 원인 확인은 [작업용 서버 런북](../runbooks/work-server.md#실패-시) — Lightsail 방화벽 80·443, `dig +short 54-252-22-31.sslip.io`. 발표 중엔 서버 셸에서 `bash /srv/paperclf/server.sh status` 로 health JSON 을 보여 준다 |
| 429 (사용량 제한) | `/predict` 가 `429` + `Retry-After` | IP 하나당 분당 60번 — 리허설 직후 바로 시연하면 걸릴 수 있다. `Retry-After` 만큼 기다리거나 ② 를 증거 문장으로 넘긴다. ② 는 서버 안 `localhost:8080` 에서 부르므로 IP 가 바깥과 다를 수 있음(미확인) |
| 서버 SSH 안 됨 | `ssh "$S"` 시간 초과 | 22 번을 좁혔으면 tailnet IP 또는 Lightsail 브라우저 SSH 로([작업용 서버 런북](../runbooks/work-server.md#다-lightsail-22-번-포트-좁히기-tailnet-접속-확인-뒤에만)). ②⑧ 은 증거 대안으로 |
| ⑨ 코드 되돌리기 뒤 보호 해제 | 직전 태그가 v0.1.3 보다 앞이면 `/predict` 토큰 인증이 없는 판이다([코드 배포 런북](../runbooks/deploy-code.md#공개-api-보호-v013) "v0.1.3~") | ⑨ 를 했다면 반드시 새 태그 ci 를 다시 돌려 앞으로 돌린다. 발표 중엔 링크로만 권함 |
| 토큰 노출 | 화면에 `API_TOKEN` 값이 보임 | 값은 `T=$(grep …)` 로만 읽고 `echo $T` 하지 않는다. 보였으면 발표 뒤 `.env` 의 `API_TOKEN` 을 새 값으로 바꾸고 `cd /srv/paperclf && docker compose up -d` |

## 예상 질문과 답

| 질문 | 답 | 근거 |
|---|---|---|
| 약한 모델은 장부에 남나? | 남는다 — record-failure 잡이 게이트·parity 에서 멈춘 실행도 한 건 기록하고, 미통과 판의 배포 기록은 트리거가 거부한다 | [작업용 서버 런북 장부 절](../runbooks/work-server.md#장부-db-adr-008009-2026-11-19-구성) |
| 롤백할 때 이미지도 바뀌나? | 아니다 — `rollback.yml` 은 모델 판만, 코드는 직전 태그 ci 재실행으로 따로 | [롤백 런북](../runbooks/rollback.md) |
