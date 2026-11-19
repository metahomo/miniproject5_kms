---
title: ADR-005 배포 모델은 LLM 교사 라벨로 학습한 해싱 TF-IDF 로지스틱 회귀, 데이터는 특징만 공개한다
description: 예측 대상(논문 적합도), 교사·학생 구조, 공개 저장소에 올리는 라벨 스냅숏 형식(원문 없음)
tags:
  - adr
  - model
  - data
status: proposed
date: 2026-11-19
decider: "사령관(연구자 외출 중 전권 위임, 2026-11-19) — 연구자 확인 대기"
---
# ADR-005 배포 모델과 라벨 스냅숏

## 배경

[KMS 활용 타당성 보고서](../reports/2026-11-18-kms-feasibility.md) 2절이 후보 A(경량 적합도 분류기)를 권장했다. 연구자가 2026-11-19 "조감도·깃허브·칸반·강의안 순서대로 진행, 권한은 사령관에게 모두 위임"을 지시하고 외출해, 사령관이 권장안을 적용했다. 저장소 `metahomo/miniproject5_kms` 는 **공개**다.

## 선택지

| 선택지 | 장점 | 단점 |
|---|---|---|
| 스냅숏에 제목·초록 원문 | 사람이 읽고 검수하기 쉽다 | 공개 저장소에 출판사 초록을 재배포 — 저작권 위험 |
| 공개 식별자만, 학습 때 API 로 원문 다시 받기 | 원문을 저장하지 않는다 | 학습이 OpenAlex·KCI(키 필요) 호출에 의존, 재현성 떨어짐 |
| **해싱 특징(글자 n-gram 위치·빈도)만** | 원문으로 되돌릴 수 없다. 학습이 오프라인·재현 가능. 서빙도 같은 해싱 함수 | 사람이 스냅숏을 읽어 검수할 수 없다(교사 JSONL 은 로컬에만) |

## 결정 (잠정)

- **예측 대상**: 논문(제목·초록) → `p(include)` — 주제 `coaching-leadership` 적합 확률. 라벨은 KMS 와 같은 임계값(include ≥ 0.7, exclude ≤ 0.3, 사이는 uncertain).
- **교사**: KMS 판정기(`kms.judge.local.LocalJudge`, 프롬프트 v5, `qwen3:4b-instruct-2507-q4_K_M`)를 `labeler/teacher_label.py` 가 **읽기 전용으로 import** 해 호출한다. KMS 운영 DB 는 `mode=ro` 로만 열고, 판정 결과는 KMS DB 에 쓰지 않는다(ADR-004 범위 밖이므로).
- **학생**: `paperclf/features.py` 의 blake2b 해싱 글자 n-gram(2~4, 32,768 차원) → `TfidfTransformer` → `LogisticRegression(class_weight=balanced)`. ONNX(double) 로 서빙.
- **스냅숏**: `data/snapshots/<주제>-<YYYYMMDD>.jsonl.gz` — 공개 식별자(`openalex:`/`kci:`) · 라벨 · relevance · 분할 · 특징 · 교사 판(모델·digest·프롬프트). **제목·초록·판정 사유는 넣지 않는다.** 새 스냅숏을 `main` 에 올리면 `model.yml` 이 자동 재학습한다([R3](../requirements/R3-auto-train-validate.md)).
- **분할**: 열쇠 해시 % 5 == 0 → 게이트 시험지(약 20%). 새 데이터가 와도 기존 논문의 분할은 바뀌지 않는다.

## 확인한 사실 (2026-11-19)

- skl2onnx 변환에서 `TfidfTransformer(sublinear_tf=True)` 는 원본과 확률이 최대 0.0018 어긋났다. `False` 면 4.4e-9. 그래서 `sublinear_tf=False` 로 둔다(`training/train.py`).
- float32 입력도 같은 이유로 오차가 커서 ONNX 입력을 double 로 했다.

## 근거 (연구자의 언어로 채울 칸)


## 영향

- 게이트는 교사 라벨로 채점한다 — "교사와 얼마나 일치하나"이지 정답률이 아니다. 사람 검수 시험지는 [#12](https://github.com/metahomo/miniproject5_kms/issues/12) 결정 대기.
- 교사 모델이 Windows 의 qwen2.5:3b 에서 Mac 의 qwen3 4B 로 바뀌었다(KMS `logs/changes/changes_261119.md`). 카드의 `teacher` 에 남는다.
