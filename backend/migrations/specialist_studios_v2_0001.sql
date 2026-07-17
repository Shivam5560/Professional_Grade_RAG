BEGIN;

CREATE TABLE IF NOT EXISTS studio_runs (
    id VARCHAR(255) PRIMARY KEY,
    owner_id INTEGER NOT NULL REFERENCES users_nexus_rag(id) ON DELETE CASCADE,
    studio_id VARCHAR(100) NOT NULL,
    operation VARCHAR(100) NOT NULL,
    idempotency_key VARCHAR(200) NOT NULL,
    input_fingerprint VARCHAR(64) NOT NULL,
    state VARCHAR(32) NOT NULL,
    current_step VARCHAR(255),
    progress DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    failure_code VARCHAR(100),
    cancellation_requested BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_studio_runs_owner_studio_idempotency
        UNIQUE (owner_id, studio_id, idempotency_key)
);

CREATE INDEX IF NOT EXISTS ix_studio_runs_owner_id
    ON studio_runs(owner_id);
CREATE INDEX IF NOT EXISTS ix_studio_runs_owner_state
    ON studio_runs(owner_id, state);

CREATE TABLE IF NOT EXISTS studio_evidence (
    id VARCHAR(255) PRIMARY KEY,
    owner_id INTEGER NOT NULL REFERENCES users_nexus_rag(id) ON DELETE CASCADE,
    run_id VARCHAR(255) NOT NULL REFERENCES studio_runs(id) ON DELETE CASCADE,
    evidence_kind VARCHAR(32) NOT NULL,
    contract_name VARCHAR(100) NOT NULL,
    payload_version INTEGER NOT NULL DEFAULT 1,
    payload JSONB NOT NULL,
    payload_digest VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_studio_evidence_run_id
    ON studio_evidence(run_id);
CREATE INDEX IF NOT EXISTS ix_studio_evidence_owner_run
    ON studio_evidence(owner_id, run_id);

CREATE TABLE IF NOT EXISTS studio_artifacts (
    revision_id VARCHAR(255) PRIMARY KEY,
    artifact_id VARCHAR(255) NOT NULL,
    revision INTEGER NOT NULL CHECK (revision >= 1),
    owner_id INTEGER NOT NULL REFERENCES users_nexus_rag(id) ON DELETE CASCADE,
    studio_id VARCHAR(100) NOT NULL,
    run_id VARCHAR(255) NOT NULL REFERENCES studio_runs(id) ON DELETE CASCADE,
    media_type VARCHAR(255) NOT NULL,
    content_digest VARCHAR(64) NOT NULL,
    evidence_ids JSONB NOT NULL,
    supersedes_revision_id VARCHAR(255)
        REFERENCES studio_artifacts(revision_id),
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_studio_artifacts_artifact_revision
        UNIQUE (artifact_id, revision),
    CONSTRAINT ck_studio_artifacts_immediate_parent CHECK (
        (revision = 1 AND supersedes_revision_id IS NULL)
        OR (
            revision > 1
            AND supersedes_revision_id =
                artifact_id || ':r' || CAST(revision - 1 AS VARCHAR)
        )
    )
);

CREATE INDEX IF NOT EXISTS ix_studio_artifacts_run_id
    ON studio_artifacts(run_id);
CREATE INDEX IF NOT EXISTS ix_studio_artifacts_owner_artifact
    ON studio_artifacts(owner_id, artifact_id);

CREATE TABLE IF NOT EXISTS studio_approvals (
    id VARCHAR(255) PRIMARY KEY,
    owner_id INTEGER NOT NULL REFERENCES users_nexus_rag(id) ON DELETE CASCADE,
    run_id VARCHAR(255) NOT NULL REFERENCES studio_runs(id) ON DELETE CASCADE,
    decision_type VARCHAR(100) NOT NULL,
    proposed_changes JSONB NOT NULL,
    evidence_ids JSONB NOT NULL,
    status VARCHAR(32) NOT NULL,
    reviewer_id INTEGER,
    comment TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_studio_approvals_run_id
    ON studio_approvals(run_id);
CREATE INDEX IF NOT EXISTS ix_studio_approvals_owner_run
    ON studio_approvals(owner_id, run_id);

CREATE TABLE IF NOT EXISTS studio_quality_results (
    id VARCHAR(255) PRIMARY KEY,
    owner_id INTEGER NOT NULL REFERENCES users_nexus_rag(id) ON DELETE CASCADE,
    run_id VARCHAR(255) NOT NULL REFERENCES studio_runs(id) ON DELETE CASCADE,
    payload_version INTEGER NOT NULL DEFAULT 1,
    payload JSONB NOT NULL,
    payload_digest VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_studio_quality_results_run_id
    ON studio_quality_results(run_id);
CREATE INDEX IF NOT EXISTS ix_studio_quality_results_owner_run
    ON studio_quality_results(owner_id, run_id);

COMMIT;
