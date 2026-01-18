from __future__ import annotations

import json
import hashlib
import uuid
from pathlib import Path
from typing import Dict, Any

from epgs.profiles.base import apply_profile
from epgs.modules.neurochain import write_rblock

__all__ = ["run_scenario"]


# ------------------------------------------------------------
# Deterministic helpers
# ------------------------------------------------------------

NAMESPACE = uuid.UUID("12345678-1234-5678-1234-567812345678")


def _hash_payload(payload: Dict[str, Any]) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _deterministic_run_id(scenario_name: str) -> str:
    return uuid.uuid5(NAMESPACE, f"{scenario_name}::run").hex


# ------------------------------------------------------------
# Core execution
# ------------------------------------------------------------

def run_scenario(
    scenario_path: str | Path,
    *,
    output_root: str | Path,
) -> Dict[str, Any]:
    """
    Deterministic scenario execution (CI authoritative).

    Supports:
    - scenario JSON with "scenario"
    - scenario JSON with "path" (CI uses this)
    """

    scenario_path = Path(scenario_path)
    output_root = Path(output_root)

    scenario_obj = json.loads(scenario_path.read_text(encoding="utf-8"))

    # --------------------------------------------------------
    # Resolve scenario source (CRITICAL CI FIX)
    # --------------------------------------------------------
    if "scenario" in scenario_obj:
        scenario_name = scenario_obj["scenario"]
        scenario = scenario_obj

    elif "path" in scenario_obj:
        resolved = Path(scenario_obj["path"]).resolve()
        scenario = json.loads(resolved.read_text(encoding="utf-8"))

        if "scenario" not in scenario:
            raise KeyError("Resolved scenario JSON must contain 'scenario'")

        scenario_name = scenario["scenario"]

    else:
        raise KeyError("Scenario JSON must contain 'scenario' or 'path'")

    # --------------------------------------------------------
    # Deterministic identifiers
    # --------------------------------------------------------
    run_id = _deterministic_run_id(scenario_name)

    ledger_dir = output_root / scenario_name / run_id / "ledger"
    ledger_dir.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------
    # Governance (CI authoritative)
    # --------------------------------------------------------
    policy = apply_profile(scenario)

    permission = policy["permission"]
    stop_issued = policy["stop_issued"]
    neuro_pause = policy["neuro_pause"]

    # --------------------------------------------------------
    # Deterministic execution payload
    # --------------------------------------------------------
    execution_payload = {
        "scenario": scenario_name,
        "permission": permission,
        "stop_issued": stop_issued,
        "neuro_pause": neuro_pause,
    }

    execution_hash = _hash_payload(execution_payload)

    # --------------------------------------------------------
    # Immutable R-Block
    # --------------------------------------------------------
    rblock_payload = {
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

    # --------------------------------------------------------
    # CI-expected return schema
    # --------------------------------------------------------
    return {
        "scenario": scenario_name,
        "hash": execution_hash,
        "rblock_hash": rblock_hash,
        "ledger_dir": str(ledger_dir),
        "ledger_path": str(ledger_dir),
        "permission": permission,
        "stop_issued": stop_issued,
        "neuro_pause": neuro_pause,
        "ok": True,
    }
