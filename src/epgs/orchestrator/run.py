from __future__ import annotations

import json
import uuid
import hashlib
from pathlib import Path
from typing import Dict, Any

from epgs.modules.neurochain import write_rblock
from epgs.profiles.base import apply_profile


# ---------------------------------------------------------------------
# Deterministic namespace (CI authoritative – DO NOT CHANGE)
# ---------------------------------------------------------------------
NAMESPACE = uuid.UUID("12345678-1234-5678-1234-567812345678")


def _hash_payload(payload: Dict[str, Any]) -> str:
    """
    Canonical deterministic hash of execution payload.
    """
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def run_scenario(
    scenario_path: Path,
    output_root: Path,
) -> Dict[str, Any]:
    """
    Run a single scenario deterministically.

    Supports:
    - Inline scenario JSON (contains "scenario")
    - Scenario reference JSON (contains "path")
    """

    scenario_path = Path(scenario_path)
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------------------
    # Load scenario manifest
    # -----------------------------------------------------------------
    raw = json.loads(scenario_path.read_text(encoding="utf-8"))

    # --------------------------------------------------------------
    # Scenario resolution (CI-authoritative)
    # --------------------------------------------------------------
    if "scenario" in raw:
        scenario = raw
    elif "path" in raw:
        scenario_file = Path(raw["path"])
        if not scenario_file.is_absolute():
            scenario_file = scenario_path.parent / scenario_file
        scenario = json.loads(scenario_file.read_text(encoding="utf-8"))
    else:
        raise KeyError("Scenario JSON must contain 'scenario' or 'path'")

    scenario_name = scenario["scenario"]

    # -----------------------------------------------------------------
    # Deterministic identifiers (per scenario)
    # -----------------------------------------------------------------
    run_id = str(uuid.uuid5(NAMESPACE, f"{scenario_name}::run"))
    rblock_id = str(uuid.uuid5(NAMESPACE, f"{scenario_name}::rblock"))

    # -----------------------------------------------------------------
    # Apply governance profile
    # -----------------------------------------------------------------
    profile = apply_profile(scenario)

    # -----------------------------------------------------------------
    # Execution payload (hash-authoritative)
    # -----------------------------------------------------------------
    execution_payload: Dict[str, Any] = {
        "scenario": scenario_name,
        "run_id": run_id,
        "rblock_id": rblock_id,
        "permission": profile["permission"],
        "stop_issued": profile["stop_issued"],
        "neuro_pause": profile["neuro_pause"],
    }

    execution_hash = _hash_payload(execution_payload)

    # -----------------------------------------------------------------
    # Write deterministic R-block ledger entry
    # -----------------------------------------------------------------
    ledger_dir = output_root / "ledger"
    rblock_hash = write_rblock(
        payload=execution_payload,
        ledger_dir=ledger_dir,
    )

    # -----------------------------------------------------------------
    # Final result (used by tests)
    # -----------------------------------------------------------------
    return {
        "scenario": scenario_name,
        "run_id": run_id,
        "rblock_id": rblock_id,
        "execution_hash": execution_hash,
        "rblock_hash": rblock_hash,
        "permission": profile["permission"],
        "stop_issued": profile["stop_issued"],
        "neuro_pause": profile["neuro_pause"],
    }
