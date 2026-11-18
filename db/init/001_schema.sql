-- 미니 프로젝트 5 — 모델·예측 장부 스키마 v1
-- 설계: architecture/data-model.md
-- 모델 파일·current.json 의 정본은 버킷이고, 이 DB 는 이력·조회용 장부다.

-- 버킷에 올린 라벨 스냅숏 1개
CREATE TABLE datasets (
    dataset_id   text PRIMARY KEY,
    bucket_key   text NOT NULL,
    sha256       char(64) NOT NULL UNIQUE,
    n_rows       integer NOT NULL CHECK (n_rows >= 0),
    n_include    integer NOT NULL CHECK (n_include >= 0),
    n_exclude    integer NOT NULL CHECK (n_exclude >= 0),
    -- 라벨 출처: 교사 모델, 프롬프트 버전, 사람 검수 수 등
    label_source jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at   timestamptz NOT NULL DEFAULT now(),
    CHECK (n_include + n_exclude <= n_rows)
);

-- 학습 실행 1회가 만든 모델
CREATE TABLE model_versions (
    version         text PRIMARY KEY CHECK (version ~ '^m[0-9]{8}-[0-9]+$'),
    dataset_id      text NOT NULL REFERENCES datasets (dataset_id),
    git_sha         text,
    run_url         text,
    algorithm       text NOT NULL,
    bucket_key      text NOT NULL,
    onnx_sha256     char(64) NOT NULL,
    metrics         jsonb NOT NULL DEFAULT '{}'::jsonb,
    gate_passed     boolean NOT NULL,
    parity_max_diff double precision,
    parity_passed   boolean NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now()
);

-- 승격 또는 롤백 1건
CREATE TABLE deployments (
    id               bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    version          text NOT NULL REFERENCES model_versions (version),
    action           text NOT NULL CHECK (action IN ('promote', 'rollback')),
    previous_version text REFERENCES model_versions (version),
    actor            text NOT NULL,
    run_url          text,
    health_ok        boolean NOT NULL,
    deployed_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX deployments_recent_idx ON deployments (deployed_at DESC, id DESC);

-- 게이트·parity 를 둘 다 통과한 모델만 배포 기록에 들어갈 수 있다
CREATE FUNCTION deployments_require_validated() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM model_versions m
        WHERE m.version = NEW.version AND m.gate_passed AND m.parity_passed
    ) THEN
        RAISE EXCEPTION 'model % has not passed gate and parity', NEW.version;
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER deployments_validated
    BEFORE INSERT ON deployments
    FOR EACH ROW EXECUTE FUNCTION deployments_require_validated();

-- 운영 예측 1건 (원문은 저장하지 않고 해시·길이만)
CREATE TABLE predictions (
    id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_version text NOT NULL REFERENCES model_versions (version),
    input_sha256  char(64) NOT NULL,
    input_chars   integer NOT NULL CHECK (input_chars >= 0),
    score         real NOT NULL CHECK (score >= 0 AND score <= 1),
    label         text NOT NULL CHECK (label IN ('include', 'exclude')),
    latency_ms    real,
    requested_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX predictions_model_time_idx ON predictions (model_version, requested_at);

-- 지금 운영 중인 판: 확인(health_ok)된 마지막 배포
CREATE VIEW current_model AS
SELECT version, action, deployed_at
FROM deployments
WHERE health_ok
ORDER BY deployed_at DESC, id DESC
LIMIT 1;

-- 롤백 대상: 운영 중인 판과 다른, 그 직전의 확인된 배포
CREATE VIEW previous_model AS
SELECT d.version, d.action, d.deployed_at
FROM deployments d, current_model c
WHERE d.health_ok AND d.version <> c.version
ORDER BY d.deployed_at DESC, d.id DESC
LIMIT 1;
