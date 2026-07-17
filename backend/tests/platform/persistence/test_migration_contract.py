from __future__ import annotations

import re
from pathlib import Path


MIGRATION = (
    Path(__file__).resolve().parents[3]
    / "migrations"
    / "specialist_studios_v2_0001.sql"
)


def _normalized_sql() -> str:
    return re.sub(r"\s+", " ", MIGRATION.read_text(encoding="utf-8").lower()).strip()


def test_migration_is_guarded_and_creates_every_shared_table() -> None:
    sql = _normalized_sql()

    assert sql.startswith("begin;")
    assert sql.endswith("commit;")
    for table_name in (
        "studio_runs",
        "studio_evidence",
        "studio_artifacts",
        "studio_approvals",
        "studio_quality_results",
    ):
        assert f"create table if not exists {table_name}" in sql


def test_migration_declares_required_uniqueness_foreign_keys_and_indexes() -> None:
    sql = _normalized_sql()

    assert "unique (owner_id, studio_id, idempotency_key)" in sql
    assert "unique (artifact_id, revision)" in sql
    assert sql.count("references studio_runs(id)") >= 4
    assert "references studio_artifacts(revision_id)" in sql
    assert "ck_studio_artifacts_immediate_parent check" in sql
    assert "(revision = 1 and supersedes_revision_id is null)" in sql
    for index_name in (
        "ix_studio_runs_owner_id",
        "ix_studio_evidence_run_id",
        "ix_studio_artifacts_run_id",
        "ix_studio_approvals_run_id",
        "ix_studio_quality_results_run_id",
    ):
        assert f"create index if not exists {index_name}" in sql
