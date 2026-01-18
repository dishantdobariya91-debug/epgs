from __future__ import annotations

from pathlib import Path
import json
import re

from epgs.core.crypto import chained_hash

GENESIS_HASH = "0" * 64

# UUID filename matcher (strict R-block identification)
_RBLOCK_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.json$",
    re.IGNORECASE,
)


def load_rblock(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_chain(ledger_dir: str) -> dict:
    p = Path(ledger_dir)

    # Only accept real R-block files
    files = sorted(
        f for f in p.glob("*.json")
        if _RBLOCK_RE.match(f.name)
    )

    if not files:
        return {"ok": False, "reason": "No R-Blocks found"}

    prev = GENESIS_HASH

    for f in files:
        rb = load_rblock(f)
        payload = dict(rb)

        embedded_prev = payload.pop("previous_hash")
        embedded_hash = payload.pop("rblock_hash")

        if embedded_prev != prev:
            return {
                "ok": False,
                "reason": f"previous_hash mismatch in {f.name}",
            }

        recomputed = chained_hash(payload, prev)
        if recomputed != embedded_hash:
            return {
                "ok": False,
                "reason": f"hash mismatch in {f.name}",
            }

        prev = embedded_hash

    return {
        "ok": True,
        "final_hash": prev,
        "count": len(files),
    }
