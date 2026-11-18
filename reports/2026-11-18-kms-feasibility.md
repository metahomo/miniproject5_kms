---
title: 보고서 — KMS 를 미니 프로젝트 5 재료로 쓸 수 있는가
description: KMS 저장소 조사 결과와, LLM 판정을 교사로 쓰는 경량 적합도 분류기 배포안 제시
tags:
  - report
  - kms
  - feasibility
date: 2026-11-18
author: 사령관(Claude)
status: proposed
---
# 보고서 — KMS 를 미니 프로젝트 5 재료로 쓸 수 있는가

**결론: 쓸 수 있다.** KMS 의 GPU LLM 판정(qwen2.5:3b)을 교사로, CPU 에서 도는 경량 적합도 분류기(TF-IDF + 로지스틱 회귀)를 학생으로 두면 필수 기능 R1~R5 를 모두 채울 수 있다. 단, KMS 자체를 배포하지 않고 **별도 비공개 저장소**를 만들며, KMS 는 라벨 데이터를 내보내는 역할만 한다.

- 조감도: "미니 프로젝트 5 조감도 — KMS 논문 판정기 클라우드 배포" (claude.ai 문서, 2026-11-18 작성) — `https://claude.ai/artifact/3WMUPTn1hXPA5nzGT1mVvt`
- 근거: 아래 사실은 2026-11-18 KMS 저장소를 읽기 전용으로 조사한 결과다. 파일 경로는 `Z:\miniproject-kms` 기준이고, 사령관이 일부를 직접 다시 확인했다(✔ 표시).

## 1. KMS 조사 사실

| 영역 | 사실 | 근거 |
|---|---|---|
| 런타임 | Python >=3.11, FastAPI · uvicorn · chromadb · rdflib · httpx. scikit-learn · 학습 코드 없음 | `pyproject.toml` 9~21행 ✔ |
| LLM 판정 | 입력은 제목·초록만. 출력 relevance 0~1 → include / exclude / uncertain | `kms/llm/prompts/screen_v5.md` 1~2행 ✔, `kms/judge/base.py` 74~79행 ✔ |
| GPU 의존 | 판정 qwen2.5:3b, 임베딩 bge-m3 모두 Ollama + GPU 4GB | 상위 `CLAUDE.md` 4절 |
| 데이터 규모 | 논문 590편, 사람 검수 라벨 10편 | 상위 `CLAUDE.md` 16절 |
| API | `/health`(status · version · components), 읽기 · 쓰기 JSON API, `serve` 는 인증 끄면 127.0.0.1 외 거부 | `kms/server.py`, `kms/api/schemas.py`, `kms/cli.py` |
| 테스트 | 시험 파일 36개, 외부 네트워크 차단, `filterwarnings=error`, 계층·OS 분기 금지 자동 검사 | `tests/` ✔, `pyproject.toml`, `tests/test_layering.py` |
| 배포 산출물 | Dockerfile · compose · `.github/` 없음. 실행 스크립트는 Windows `.bat` · `.ps1` 뿐 | 저장소 루트 ✔ |
| 금지 규칙 | DB · 참고문헌 수정 금지, 로그인 · HTTPS 없는 외부 공개 금지 | 상위 `CLAUDE.md` 18절 |

조사 중 발견한 어긋남(미니 프로젝트와 무관, 기록만): 상위 `CLAUDE.md` 는 저장소를 `Z:\kms-pym` 으로 적지만 실제는 `Z:\miniproject-kms` 다. `docs/project-reference.md` · `docs/search-eval.md` 가 없다. `.claude/settings.json` 훅 경로도 옛 경로다.

## 2. 배포 대상 후보 비교

| 후보 | R3 자동 학습 | Lightsail(무 GPU) | parity | 판단 |
|---|---|---|---|---|
| **A. 경량 적합도 분류기** (TF-IDF + 로지스틱) | 새 라벨 → 재학습이 자연스럽다 | CPU 로 충분 | sklearn ↔ ONNX 확률 비교 | **권장** |
| B. 하이브리드 검색 API | "학습"이 없고 인덱스 재구축만 | 질의 임베딩 bge-m3 를 CPU 로 돌려야 함(속도 미확인) | 정의가 애매 | 보류 |
| C. LLM 판정 그대로 | 학습 없음 | GPU 없이 불가 | — | 제외 |

A 를 권장하는 이유: 라벨이 이미 쌓이고 있고, 판정 입력(제목·초록)과 학생 입력이 같으며, 강의의 학습 → ONNX → parity → 승격 → 롤백 흐름에 그대로 올라탄다. "GPU LLM 을 CPU 모델로 증류해 싸게 서빙한다"는 점이 강의 예제(eta-mini)와 다른 설계 이유가 된다.

## 3. 강점과 위험

| 강점 | 위험 |
|---|---|
| 테스트 문화가 이미 강하다 — CI 기준으로 바로 쓴다 | 라벨이 작다(590편) — 게이트 점수가 흔들린다 |
| 라벨에 출처(모델 · 프롬프트 버전 · 판정 주체)가 남는다 — 모델 카드로 잇는다 | 교사 라벨로 채점하면 자기 채점 — 사람 검수 시험지가 10편뿐 |
| 설정 기반 호스트 역할 설계 — "GPU 는 내 PC, 서빙은 Lightsail" 분리와 맞다 | CI/CD · 컨테이너가 전무 — 새로 만들어야 한다 |
| MCP 서버 경험 — 발표 옵션 "AI 에게 서비스"에 바로 쓴다 | KMS 자동 수집(M6) 미완 — "새 데이터"는 처음엔 수동 내보내기 |

## 4. 제안하는 진행 순서

조감도의 "진행 순서"와 같다: 0 준비 → 1 코드 판 → 2 서버 배포 → 3 모델 판 → 4 승격·롤백 → 5 마감·발표. 각 단계의 구체 절차는 [강의 03 교과서판](../sources/lecture-index.md)을 따르고, 다른 점만 [개선점](../presentation/03-improvements.md)에 남긴다. 요구사항 문서는 [R1](../requirements/R1-lightsail.md) · [R2](../requirements/R2-cicd.md) · [R3](../requirements/R3-auto-train-validate.md) · [R4](../requirements/R4-model-serving.md) · [R5](../requirements/R5-rollback.md).

## 5. 연구자 결정이 필요한 것

결정 목록은 [결정 기록 색인](../decisions/index.md)에 있다. 이 보고서의 채택 여부가 첫 번째 ADR(도메인 선택)이 된다.
