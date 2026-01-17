from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Dict, Any


def write_rblock(
    payload: Dict[str, Any],
    previous_hash: str | None,
    ledger_dir: str | Path,
) -> str:
    """
    Write an immutable R-Block to the ledger directory.

    CONTRACT (tests depend on this):
    - ledger_dir MUST be filesystem path
    - payload MUST be dict
    - returns rblock_hash (hex string)
    """

    ledger_dir = Path(ledger_dir)
    ledger_dir.mkdir(parents=True, exist_ok=True)

    block = dict(payload)
    block["previous_hash"] = previous_hash

    raw = json.dumps(
        block,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    rblock_hash = hashlib.sha256(raw).hexdigest()
    block["rblock_hash"] = rblock_hash

    block_path = ledger_dir / f"{rblock_hash}.json"

    if block_path.exists():
        raise RuntimeError("R-Block already exists. Immutability violation.")

    with block_path.open("w", encoding="utf-8") as f:
        json.dump(block, f, indent=2, sort_keys=True)

    return rblock_hash
