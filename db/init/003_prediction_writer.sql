-- 미니 프로젝트 5 — 장부 스키마 v3: 예측 로그 (ADR-009 "예측 로그는 API 가 직접")
-- uncertain(0.3 < p < 0.7) 도 예측 결과이므로 남긴다.
ALTER TABLE predictions DROP CONSTRAINT IF EXISTS predictions_label_check;
ALTER TABLE predictions ADD CONSTRAINT predictions_label_check CHECK (label IN ('include', 'exclude', 'uncertain'));

-- API 전용 계정: predictions 에 넣기만 한다(읽기·다른 표 쓰기 불가). 비밀번호는 서버에서 ALTER ROLE 로만 정한다.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'predictor') THEN
        CREATE ROLE predictor LOGIN;
    END IF;
END $$;
GRANT USAGE ON SCHEMA public TO predictor;
GRANT INSERT ON predictions TO predictor;
GRANT SELECT (version) ON model_versions TO predictor; -- 외래 키 확인용
