from __future__ import annotations

import csv
import hashlib
import io
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import PurePath
from typing import Any, Protocol
from collections.abc import Mapping

import pandas as pd

from sqlalchemy.orm import Session

from app.platform.persistence import (
    RecordNotFound,
    StudioEvidenceRepository,
    StudioQualityRepository,
    StudioRunRepository,
)
from app.platform.quality import QualityMetadata, ValidationIssue, ValidationStatus
from app.platform.runtime import StudioRun, StudioRunState
from app.studios.data_analyst import DataAnalystSpecialist
from app.studios.data_analyst.domain import canonical_digest, thaw_json
from app.studios.data_analyst.persistence import DataAnalystRepository, DatasetSnapshot
from app.studios.data_analyst.profiling import profile_dataframe

from .contracts import AnalysisRunResponse


class UnsafeDatasetUpload(ValueError):
    """Stable, categorized rejection for an unsafe or excessive upload."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        super().__init__(f"{code}: {detail}")


@dataclass(frozen=True)
class CsvUploadPolicy:
    max_bytes: int = 10 * 1024 * 1024
    max_rows: int = 100_000
    max_columns: int = 500
    max_field_bytes: int = 64 * 1024


class SnapshotStore(Protocol):
    def put(self, content: bytes, *, content_digest: str) -> str: ...
    def get(self, storage_key: str) -> bytes: ...


class InMemorySnapshotStore:
    def __init__(self) -> None:
        self._values: dict[str, bytes] = {}

    def put(self, content: bytes, *, content_digest: str) -> str:
        key = f"sha256/{content_digest}"
        self._values.setdefault(key, bytes(content))
        return key

    def get(self, storage_key: str) -> bytes:
        try:
            return self._values[storage_key]
        except KeyError as exc:
            raise KeyError("snapshot content not found") from exc


_CSV_MEDIA_TYPES = frozenset({"text/csv", "application/csv", "application/vnd.ms-excel"})
_ARCHIVE_SIGNATURES = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08", b"\x1f\x8b")
_FORMULA_PREFIXES = ("=", "+", "-", "@")


def safe_display_filename(filename: str) -> str:
    normalized = filename.replace("\\", "/")
    name = PurePath(normalized).name
    if not name or name in {".", ".."}:
        raise UnsafeDatasetUpload("invalid-filename", "filename has no safe basename")
    return name


def parse_bounded_csv(
    content: bytes,
    *,
    filename: str,
    media_type: str,
    policy: CsvUploadPolicy | None = None,
) -> pd.DataFrame:
    policy = policy or CsvUploadPolicy()
    safe_name = safe_display_filename(filename)
    if not safe_name.lower().endswith(".csv"):
        raise UnsafeDatasetUpload("extension-mismatch", "only .csv snapshots are supported")
    clean_media_type = media_type.split(";", 1)[0].strip().lower()
    if clean_media_type not in _CSV_MEDIA_TYPES:
        raise UnsafeDatasetUpload("mime-mismatch", "content type is not CSV")
    if len(content) > policy.max_bytes:
        raise UnsafeDatasetUpload("request-too-large", "dataset exceeds the byte limit")
    if not content:
        raise UnsafeDatasetUpload("empty-content", "dataset is empty")
    if content.startswith(_ARCHIVE_SIGNATURES):
        raise UnsafeDatasetUpload("archive-content", "archives are not accepted")
    if b"\x00" in content:
        raise UnsafeDatasetUpload("binary-content", "NUL bytes are not accepted")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise UnsafeDatasetUpload("binary-content", "dataset must be UTF-8 text") from exc

    try:
        rows = csv.reader(io.StringIO(text, newline=""), strict=True)
        header = next(rows)
        if not header or any(not column.strip() for column in header):
            raise UnsafeDatasetUpload("invalid-header", "CSV requires named columns")
        if len(header) > policy.max_columns:
            raise UnsafeDatasetUpload("too-many-columns", "dataset exceeds the column limit")
        if len(set(header)) != len(header):
            raise UnsafeDatasetUpload("invalid-header", "column names must be unique")
        row_count = 0
        for row in rows:
            row_count += 1
            if row_count > policy.max_rows:
                raise UnsafeDatasetUpload("too-many-rows", "dataset exceeds the row limit")
            if len(row) != len(header):
                raise UnsafeDatasetUpload("invalid-shape", "rows must match the header")
            for value in row:
                if len(value.encode("utf-8")) > policy.max_field_bytes:
                    raise UnsafeDatasetUpload("field-too-large", "a field exceeds the parser limit")
                if value.lstrip().startswith(_FORMULA_PREFIXES):
                    raise UnsafeDatasetUpload("formula-content", "formula-prefixed cells are unsafe")
    except csv.Error as exc:
        raise UnsafeDatasetUpload("invalid-csv", "CSV parsing failed") from exc

    try:
        frame = pd.read_csv(io.StringIO(text), keep_default_na=True)
    except Exception as exc:
        raise UnsafeDatasetUpload("invalid-csv", "CSV parsing failed") from exc
    if len(frame) != row_count or len(frame.columns) != len(header):
        raise UnsafeDatasetUpload("invalid-csv", "CSV parser produced an inconsistent shape")
    return frame


def content_digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


class DataAnalystApplicationService:
    def __init__(
        self,
        session: Session,
        storage: SnapshotStore,
        *,
        specialist: DataAnalystSpecialist | None = None,
    ) -> None:
        self.session = session
        self.storage = storage
        self.specialist = specialist or DataAnalystSpecialist()
        self.data = DataAnalystRepository(session)
        self.runs = StudioRunRepository(session)

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def upload_dataset(
        self,
        content: bytes,
        *,
        owner_id: int,
        filename: str,
        media_type: str,
        policy: CsvUploadPolicy | None = None,
    ) -> DatasetSnapshot:
        frame = parse_bounded_csv(content, filename=filename, media_type=media_type, policy=policy)
        profile = profile_dataframe(frame)
        digest = content_digest(content)
        storage_key = self.storage.put(content, content_digest=digest)
        try:
            snapshot = self.data.add_snapshot(
                snapshot_id=f"snapshot-{canonical_digest({'owner_id': owner_id, 'content_digest': digest})[:24]}",
                owner_id=owner_id,
                filename=safe_display_filename(filename),
                media_type="text/csv",
                byte_size=len(content),
                content_digest=digest,
                storage_key=storage_key,
                profile=profile,
                created_at=self._now(),
            )
            self.session.commit()
            return snapshot
        except Exception:
            self.session.rollback()
            raise

    def _request_fingerprint(
        self,
        snapshot: DatasetSnapshot,
        *,
        question: str,
        business_context: Mapping[str, Any],
    ) -> str:
        return canonical_digest(
            {
                "snapshot_content_digest": snapshot.content_digest,
                "question": question.strip(),
                "business_context": thaw_json(business_context),
            }
        )

    def start_analysis(
        self,
        *,
        owner_id: int,
        snapshot_id: str,
        question: str,
        business_context: Mapping[str, Any],
        idempotency_key: str,
    ) -> tuple[AnalysisRunResponse, bool]:
        snapshot = self.data.get_snapshot(snapshot_id, owner_id=owner_id)
        fingerprint = self._request_fingerprint(snapshot, question=question, business_context=business_context)
        run_id = f"run-{canonical_digest({'owner_id': owner_id, 'key': idempotency_key})[:24]}"
        now = self._now()
        queued = StudioRun(
            id=run_id,
            owner_id=owner_id,
            studio_id="data-analyst",
            operation="analyze",
            idempotency_key=idempotency_key,
            input_fingerprint=fingerprint,
            created_at=now,
            updated_at=now,
        )
        try:
            persisted = self.runs.create(queued, owner_id=owner_id)
            if persisted.state is not StudioRunState.QUEUED:
                return self.get_run(run_id, owner_id=owner_id), False
            try:
                self.data.get_plan(run_id, owner_id=owner_id)
            except RecordNotFound:
                pass
            else:
                return self.get_run(run_id, owner_id=owner_id), False

            running = self.runs.transition(
                run_id, StudioRunState.RUNNING, owner_id=owner_id, now=now,
                current_step="profile", progress=0.1,
            )
            if not re.search(r"[A-Za-z0-9]", question):
                return self._persist_abstention(
                    queued=queued, running=running, snapshot=snapshot,
                    owner_id=owner_id, now=now,
                    detail="The question did not contain an analyzable objective.",
                ), True

            frame = parse_bounded_csv(
                self.storage.get(snapshot.storage_key),
                filename=snapshot.filename,
                media_type=snapshot.media_type,
            )
            try:
                result = self.specialist.analyze(
                    frame,
                    question,
                    owner_id=owner_id,
                    run_id=run_id,
                    idempotency_key=idempotency_key,
                    now=now,
                    business_context=business_context,
                )
            except (TypeError, ValueError) as exc:
                return self._persist_abstention(
                    queued=queued, running=running, snapshot=snapshot,
                    owner_id=owner_id, now=now,
                    detail=f"The deterministic analysis could not proceed: {type(exc).__name__}.",
                ), True
            self.data.persist_run_result(result, owner_id=owner_id, created_at=now)
            evidence_repository = StudioEvidenceRepository(self.session)
            for computation in result.computations:
                evidence_repository.add(run_id, computation.evidence, owner_id=owner_id, created_at=now)
            StudioQualityRepository(self.session).add(
                f"quality-{run_id}", run_id, result.result.quality,
                owner_id=owner_id, created_at=now,
            )
            final_core = result.run_history[-1]
            final = self.runs.transition(
                run_id,
                final_core.state,
                owner_id=owner_id,
                now=now,
                current_step=final_core.current_step,
                progress=final_core.progress,
                failure_code=final_core.failure_code,
            )
            self.session.commit()
            return AnalysisRunResponse(
                run=final,
                run_history=(queued, running, final),
                profile=result.profile,
                plan=result.plan,
                limitations=tuple(dict.fromkeys(warning for item in result.computations for warning in item.warnings)),
                quality=result.result.quality,
                abstention_reason=result.result.quality.abstention_reason,
            ), True
        except Exception:
            self.session.rollback()
            raise

    def _persist_abstention(
        self,
        *,
        queued: StudioRun,
        running: StudioRun,
        snapshot: DatasetSnapshot,
        owner_id: int,
        now: datetime,
        detail: str,
    ) -> AnalysisRunResponse:
        reason = "The analysis request could not be interpreted or executed safely."
        failed = self.runs.transition(
            queued.id, StudioRunState.FAILED, owner_id=owner_id, now=now,
            current_step="validate-analysis", progress=running.progress,
            failure_code="invalid-analysis-request",
        )
        quality = QualityMetadata(
            algorithm_versions={"data-analyst-api": "2.0.0"},
            model_versions={},
            prompt_versions={},
            confidence_components={"request-validity": 0.0},
            validations=(ValidationIssue(
                code="analysis-request-validity",
                message=detail,
                status=ValidationStatus.ERROR,
                critical=True,
            ),),
            warnings=(),
            abstention_reason=reason,
            latency_ms=0.0,
            input_tokens=0,
            output_tokens=0,
            estimated_cost_usd=0.0,
            trace_id=f"trace-{canonical_digest({'run_id': queued.id, 'category': 'invalid-analysis-request'})[:24]}",
        )
        StudioQualityRepository(self.session).add(
            f"quality-{queued.id}", queued.id, quality,
            owner_id=owner_id, created_at=now,
        )
        self.session.commit()
        return AnalysisRunResponse(
            run=failed,
            run_history=(queued, running, failed),
            profile=snapshot.profile,
            limitations=(detail,),
            quality=quality,
            abstention_reason=reason,
        )

    def get_run(self, run_id: str, *, owner_id: int) -> AnalysisRunResponse:
        run = self.runs.get(run_id, owner_id=owner_id)
        try:
            plan = self.data.get_plan(run_id, owner_id=owner_id)
            profile = self.data.get_snapshot_by_domain_id(
                plan.dataset_snapshot_id,
                owner_id=owner_id,
            ).profile
        except RecordNotFound:
            plan = None
            profile = None
        try:
            quality = StudioQualityRepository(self.session).get(f"quality-{run_id}", owner_id=owner_id)
        except RecordNotFound:
            quality = None
        return AnalysisRunResponse(
            run=run,
            run_history=(run,),
            profile=profile,
            plan=plan,
            quality=quality,
            abstention_reason=quality.abstention_reason if quality else ("The analysis request was rejected." if run.state is StudioRunState.FAILED else None),
        )

    def cancel(self, run_id: str, *, owner_id: int) -> AnalysisRunResponse:
        now = self._now()
        try:
            self.runs.request_cancellation(run_id, owner_id=owner_id, now=now)
            cancelled = self.runs.transition(run_id, StudioRunState.CANCELLED, owner_id=owner_id, now=now)
            self.session.commit()
            return AnalysisRunResponse(run=cancelled, run_history=(cancelled,))
        except Exception:
            self.session.rollback()
            raise
