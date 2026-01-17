# src/epgs/orchestrator/run.py

from __future__ import annotations

import json
import uuid
import hashlib
from pathlib import Path
from typing import Dict, Any

from epgs.profiles.base import apply_profile
from epgs.modules.neurochain import write_rblock


# ------------------------------------------------------------------
# Public module attributes (tests expect these)
# ------------------------------------------------------------------

__all__ = ["run_scenario", "uuid"]


# ------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------

def _hash_payload(payload: Dict[str, Any]) -> str:
    """
    Deterministic hash for any JSON-serializable payload.
    """
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _load_scenario(path: str | Path) -> Dict[str, Any]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


# ------------------------------------------------------------------
# Core execution
# ------------------------------------------------------------------

def run_scenario(
    scenario_path: str | Path,
    *,
    output_root: str | Path,
) -> Dict[str, Any]:
    """
    Execute a single EPGS scenario deterministically.

    This function is intentionally conservative and explicit,
    because CI + integration tests depend on its output contract.
    """

    scenario_path = Path(scenario_path)
    output_root = Path(output_root)

    scenario = _load_scenario(scenario_path)

    scenario_name = scenario.get("scenario", scenario_path.stem)

    # Unique but deterministic-per-run namespace
    run_id = uuid.uuid4().hex[:8]

    ledger_dir = output_root / scenario_name / "ledger"
    ledger_dir.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------------
    # Apply profile (tests require this hook)
    # --------------------------------------------------------------
    profile_result = apply_profile(scenario)

    # Defensive defaults expected by tests
    permission = profile_result.get("permission", "ALLOW")
    stop_issued = profile_result.get("stop_issued", False)
    neuro_pause = profile_result.get("neuro_pause", False)

    # --------------------------------------------------------------
    # Execution payload (canonical)
    # --------------------------------------------------------------
    execution_payload: Dict[str, Any] = {
        "scenario": scenario_name,
        "permission": permission,
        "stop_issued": stop_issued,
        "neuro_pause": neuro_pause,
    }

    execution_hash = _hash_payload(execution_payload)

    # --------------------------------------------------------------
    # Ledger write (immutable)
    # --------------------------------------------------------------
    rblock_payload = {
        "scenario": scenario_name,
        "permission": permission,
        "stop_issued": stop_issued,
        "neuro_pause": neuro_pause,
        "previous_hash": None,
        "rblock_hash": execution_hash,
    }

    rblock_hash = write_rblock(
        payload=rblock_payload,
        ledger_dir=ledger_dir,
    )

    # --------------------------------------------------------------
    # Return contract (tests rely on these keys)
    # --------------------------------------------------------------
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
