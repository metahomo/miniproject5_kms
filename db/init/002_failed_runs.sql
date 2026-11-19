-- 미니 프로젝트 5 — 장부 스키마 v2: 게이트에서 멈춘 실행도 model_versions 에 한 건 남긴다 (ADR-009 "게이트 실패 이력도 남긴다")
-- 게이트 실패 실행은 ONNX 를 만들기 전에 멈추므로 onnx_sha256 이 없다. 통과한 판에는 여전히 반드시 있어야 한다.
-- 배포 기록 트리거(deployments_require_validated)는 그대로 — 실패 판은 배포 기록에 들어갈 수 없다.
ALTER TABLE model_versions ALTER COLUMN onnx_sha256 DROP NOT NULL;
ALTER TABLE model_versions ADD CONSTRAINT model_versions_onnx_when_gate_passed
    CHECK (onnx_sha256 IS NOT NULL OR NOT gate_passed);
