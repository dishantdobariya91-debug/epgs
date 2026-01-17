from __future__ import annotations

from pathlib import Path
from typing import Any

from epgs.core.crypto import canonical_json, chained_hash


def write_rblock(
    ledger_dir: Path,
    rblock_payload: dict[str, Any],
    previous_hash: str,
) -> tuple[str, str]:
    ledger_dir.mkdir(parents=True, exist_ok=True)

    rblock_hash = chained_hash(rblock_payload, previous_hash)
    rblock_id = rblock_payload["rblock_id"]

    out_path = ledger_dir / f"{rblock_id}.json"
    if out_path.exists():
        raise RuntimeError("R-Block already exists. Immutability violation.")

    record = dict(rblock_payload)
    record["previous_hash"] = previous_hash
    record["rblock_hash"] = rblock_hash

    out_path.write_text(canonical_json(record), encoding="utf-8")
    return rblock_hash, rblock_id
