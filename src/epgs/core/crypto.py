from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(obj: Any) -> str:
    """
    Deterministic JSON serialization:
    - sorted keys
    - no whitespace
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def chained_hash(payload_obj: Any, previous_hash: str) -> str:
    payload = canonical_json(payload_obj)
    return sha256_hex(payload + previous_hash)
