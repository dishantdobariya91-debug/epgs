# src/epgs/orchestrator/run.py

from __future__ import annotations

import json
import hashlib
import uuid
from pathlib import Path
from typing import Dict, Any

from epgs.profiles.base import apply_profile
from epgs.modules.neurochain import write_rblock

__all__ = ["run_scenario"]

# --------------------------------------------------------------
# Deterministic UUID namespace (constant, CI-authoritative)
# --------------------------------------------------------------
NAMESPACE = uuid.UUID("12345678-1234-5678-1234-567812345678")


def _hash_payload(payload: Dict[str, Any]) -> str:
    """
    Canonical SHA-256 hash of execution payload.
    """
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def run_scenario(
    scenario_path: str | Path,
    *,
    output_root: str | Path,
) -> Dict[str, Any]:
    """
    Deterministic scenario execution (CI authoritative).
    Same scenario input => same hashes, every time.
    """

    scenario_path = Path(scenario_path)
    output_root = Path(output_root)

    scenario = json.loads(scenario_path.read_text(encoding="utf-8"))

    if "scenario" not in scenario:
        raise KeyError("Scenario JSON must contain 'scenario'")

    scenario_name = scenario["scenario"]

    # ----------------------------------------------------------
    # Deterministic identifiers (per scenario)
    # ----------------------------------------------------------
    run_id = str(uuid.uuid5(NAMESPACE, f"{scenario_name}::run"))
    rblock_id = str(uuid.uuid5(NAMESPACE, f"{scenario_name}::rblock"))

    ledger_dir = output_root / scenario_name / run_id / "ledger"
    ledger_dir.mkdir(parents=True, exist_ok=True)

    # ----------------------------------------------------------
    # Apply deterministic governance policy
    # ----------------------------------------------------------
    policy = apply_profile(scenario)

    permission = policy["permission"]
    stop_issued = policy["stop_issued"]
    neuro_pause = policy["neuro_pause"]

    # ----------------------------------------------------------
    # Canonical execution payload (NO run_id, NO UUIDs)
    # ----------------------------------------------------------
    execution_payload = {
        "scenario": scenario_name,
        "permission": permission,
        "stop_issued": stop_issued,
        "neuro_pause": neuro_pause,
    }

    execution_hash = _hash_payload(execution_payload)

    # ----------------------------------------------------------
    # Immutable R-Block payload
    # ----------------------------------------------------------
    rblock_payload = {
        "rblock_id": rblock_id,
        "scenario": scenario_name,
        "permission": permission,
        "stop_issued": stop_issued,
        "neuro_pause": neuro_pause,
        "previous_hash": None,
        "execution_hash": execution_hash,
    }

    rblock_hash = write_rblock(
        payload=rblock_payload,
        ledger_dir=ledger_dir,
    )

    return {
        "scenario": scenario_name,
        "hash": execution_hash,
        "rblock_hash": rblock_hash,
        "ledger_dir": str(ledger_dir),
        "permission": permission,
        "stop_issued": stop_issued,
        "neuro_pause": neuro_pause,
        "ok": True,
    }
