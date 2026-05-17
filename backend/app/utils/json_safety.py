"""Utilities for values that must be valid PostgreSQL JSON/JSONB."""

from __future__ import annotations

import math
from datetime import date, datetime
from decimal import Decimal
from typing import Any


def sanitize_json(value: Any) -> Any:
    """Recursively convert Python/Pandas values into strict JSON-safe data."""
    if value is None or isinstance(value, (str, bool, int)):
        return value

    if isinstance(value, float):
        return value if math.isfinite(value) else None

    if isinstance(value, Decimal):
        as_float = float(value)
        return as_float if math.isfinite(as_float) else None

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, dict):
        return {str(k): sanitize_json(v) for k, v in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [sanitize_json(v) for v in value]

    item = getattr(value, "item", None)
    if callable(item):
        try:
            return sanitize_json(item())
        except Exception:
            pass

    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass

    return str(value)
