from __future__ import annotations

import pytest

from app.studios.data_analyst.api.service import (
    CsvUploadPolicy,
    InMemorySnapshotStore,
    UnsafeDatasetUpload,
    parse_bounded_csv,
)


def test_valid_csv_is_bounded_and_storage_key_is_opaque() -> None:
    payload = b"revenue,profit\n10,2\n20,4\n"
    frame = parse_bounded_csv(
        payload,
        filename="../../quarterly.csv",
        media_type="text/csv",
        policy=CsvUploadPolicy(max_bytes=100, max_rows=5, max_columns=4),
    )
    store = InMemorySnapshotStore()
    key = store.put(payload, content_digest="a" * 64)

    assert frame.shape == (2, 2)
    assert "quarterly.csv" not in key
    assert ".." not in key
    assert store.get(key) == payload


@pytest.mark.parametrize(
    ("payload", "filename", "media_type", "code"),
    [
        (b"a,b\n1,2\n", "data.txt", "text/csv", "extension-mismatch"),
        (b"a,b\n1,2\n", "data.csv", "application/pdf", "mime-mismatch"),
        (b"PK\x03\x04archive", "data.csv", "text/csv", "archive-content"),
        (b"a,b\n1,\x002\n", "data.csv", "text/csv", "binary-content"),
        (b"name,value\nrow,=2+2\n", "data.csv", "text/csv", "formula-content"),
        (b"name,value\nrow,@SUM(A1)\n", "data.csv", "text/csv", "formula-content"),
    ],
)
def test_unsafe_csv_content_is_rejected(payload: bytes, filename: str, media_type: str, code: str) -> None:
    with pytest.raises(UnsafeDatasetUpload, match=code):
        parse_bounded_csv(payload, filename=filename, media_type=media_type)


def test_size_row_column_and_field_limits_are_enforced() -> None:
    with pytest.raises(UnsafeDatasetUpload, match="request-too-large"):
        parse_bounded_csv(b"a\n123456\n", filename="data.csv", media_type="text/csv", policy=CsvUploadPolicy(max_bytes=4))
    with pytest.raises(UnsafeDatasetUpload, match="too-many-rows"):
        parse_bounded_csv(b"a\n1\n2\n", filename="data.csv", media_type="text/csv", policy=CsvUploadPolicy(max_rows=1))
    with pytest.raises(UnsafeDatasetUpload, match="too-many-columns"):
        parse_bounded_csv(b"a,b\n1,2\n", filename="data.csv", media_type="text/csv", policy=CsvUploadPolicy(max_columns=1))
    with pytest.raises(UnsafeDatasetUpload, match="field-too-large"):
        parse_bounded_csv(b"a\n12345\n", filename="data.csv", media_type="text/csv", policy=CsvUploadPolicy(max_field_bytes=3))
