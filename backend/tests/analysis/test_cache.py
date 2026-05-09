"""Tests for DatasetCache."""

import pandas as pd
import pytest

from app.analysis.cache import DatasetCache


class TestDatasetCache:
    def test_cache_miss_then_hit(self, monkeypatch):
        """First call loads from disk, second returns cached."""
        load_count = 0

        def mock_load(source_id, user_id, max_rows):
            nonlocal load_count
            load_count += 1
            return pd.DataFrame({"a": [1, 2, 3]})

        monkeypatch.setattr(
            "app.analysis.cache.load_dataset_from_disk", mock_load
        )

        DatasetCache.clear()
        df1 = DatasetCache.get_or_load("test_source", "user1", max_rows=50000)
        df2 = DatasetCache.get_or_load("test_source", "user1", max_rows=50000)

        assert load_count == 1
        assert df1.equals(df2)

    def test_different_sources_loaded_separately(self, monkeypatch):
        load_count = 0

        def mock_load(source_id, user_id, max_rows):
            nonlocal load_count
            load_count += 1
            return pd.DataFrame({"id": [source_id]})

        monkeypatch.setattr(
            "app.analysis.cache.load_dataset_from_disk", mock_load
        )

        DatasetCache.clear()
        DatasetCache.get_or_load("src_a", "user1")
        DatasetCache.get_or_load("src_b", "user1")
        assert load_count == 2

    def test_invalidation(self, monkeypatch):
        load_count = 0

        def mock_load(source_id, user_id, max_rows):
            nonlocal load_count
            load_count += 1
            return pd.DataFrame({"a": [1]})

        monkeypatch.setattr(
            "app.analysis.cache.load_dataset_from_disk", mock_load
        )

        DatasetCache.clear()
        DatasetCache.get_or_load("src", "user1")
        DatasetCache.invalidate("src")
        DatasetCache.get_or_load("src", "user1")
        assert load_count == 2

    def test_clear_all(self, monkeypatch):
        load_count = 0

        def mock_load(source_id, user_id, max_rows):
            nonlocal load_count
            load_count += 1
            return pd.DataFrame({"a": [1]})

        monkeypatch.setattr(
            "app.analysis.cache.load_dataset_from_disk", mock_load
        )

        DatasetCache.clear()
        DatasetCache.get_or_load("s1", "u1")
        DatasetCache.get_or_load("s2", "u1")
        DatasetCache.clear()
        DatasetCache.get_or_load("s1", "u1")
        assert load_count == 3

    def test_size_reporting(self, monkeypatch):
        def mock_load(source_id, user_id, max_rows):
            return pd.DataFrame({"a": [1]})

        monkeypatch.setattr(
            "app.analysis.cache.load_dataset_from_disk", mock_load
        )

        DatasetCache.clear()
        DatasetCache.get_or_load("a", "u1")
        DatasetCache.get_or_load("b", "u1")
        assert DatasetCache.size() == 2
        DatasetCache.clear()
        assert DatasetCache.size() == 0
