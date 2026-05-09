"""
Thread-safe dataset cache. Datasets are loaded from disk ONCE per workflow
and reused across all pipeline steps.
"""

from __future__ import annotations

import threading
from typing import Dict

import pandas as pd

from app.services.analysis.data_ingestion import load_dataset_from_disk
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DatasetCache:
    """Thread-safe in-memory cache for loaded DataFrames.

    Usage:
        df = DatasetCache.get_or_load(source_id, str(user_id), max_rows=50000)
        # ... all workflow steps use the same df reference ...
        DatasetCache.invalidate(source_id)
    """

    _cache: Dict[str, pd.DataFrame] = {}
    _lock = threading.Lock()

    @classmethod
    def get_or_load(cls, source_id: str, user_id: str, max_rows: int = 50000) -> pd.DataFrame:
        with cls._lock:
            if source_id in cls._cache:
                logger.debug("DatasetCache HIT for source_id=%s", source_id)
                return cls._cache[source_id]

            logger.debug("DatasetCache MISS for source_id=%s — loading from disk", source_id)
            df = load_dataset_from_disk(source_id, user_id, max_rows)
            cls._cache[source_id] = df
            return df

    @classmethod
    def invalidate(cls, source_id: str) -> None:
        with cls._lock:
            if source_id in cls._cache:
                del cls._cache[source_id]
                logger.debug("DatasetCache invalidated source_id=%s", source_id)

    @classmethod
    def clear(cls) -> None:
        with cls._lock:
            count = len(cls._cache)
            cls._cache.clear()
            logger.debug("DatasetCache cleared (%d entries)", count)

    @classmethod
    def size(cls) -> int:
        with cls._lock:
            return len(cls._cache)
