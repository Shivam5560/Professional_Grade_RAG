from __future__ import annotations

import json
from typing import TypeVar

from pydantic import BaseModel


ContractT = TypeVar("ContractT", bound=BaseModel)


class SerializationError(ValueError):
    """Raised when a public contract cannot be represented as strict JSON."""


def _strict_json_copy(payload: object) -> object:
    try:
        encoded = json.dumps(
            payload,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise SerializationError("contracts must contain finite JSON values") from exc
    return json.loads(encoded)


def serialize_contract(contract: BaseModel) -> dict[str, object]:
    """Return an independent, database-safe JSON representation."""

    copied = _strict_json_copy(contract.model_dump(mode="json"))
    if not isinstance(copied, dict):  # pragma: no cover - BaseModel always dumps a mapping
        raise SerializationError("contract serialization must produce a JSON object")
    return copied


def hydrate_contract(
    contract_type: type[ContractT],
    payload: object,
) -> ContractT:
    """Validate stored JSON through its public Pydantic contract."""

    copied = _strict_json_copy(payload)
    return contract_type.model_validate(copied)
