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
# Internal utilities
# ------------------------------------------------------------------

def _stable_hash(obj: Dict[str, Any]) -> str:
    """
    Produce a deterministic SHA256 hash of a JSON-serializable object.
    """
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _load_scenario(path: str | Path) -> Dict[str, Any]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


# ------------------------------------------------------------------
# Core orchestrator entrypoint
# ------------------------------------------------------------------

def run_scenario(
    scenario_path: str | Path,
    *,
    output_root: str | Path,
) -> Dict[str, Any]:
    """
    Execute a single EPGS scenario and emit an immutable ledger.

    This function is intentionally explicit because CI + integration
    tests rely on its output contract.
    """

    # -----------------------------
    # Resolve inputs
    # -----------------------------
    scenario_path = Path(scenario_path)
    output_root = Path(output_root)

    scenario = _load_scenario(scenario_path)
    scenario_name = scenario.get("scenario", scenario_path.stem)

    # -----------------------------
    # Output directories
    # -----------------------------
    ledger_dir = output_root / scenario_name / "ledger"
    ledger_dir.mkdir(parents=True, exist_ok=True)

    # -----------------------------
    # Apply policy profile
    # -----------------------------
    profile = apply_profile(scenario) or {}

    permission = profile.get("permission", "ALLOW")
    stop_issued = bool(profile.get("stop_issued", False))
    neuro_pause = bool(profile.get("neuro_pause", False))

    # -----------------------------
    # Execution payload (canonical)
    # -----------------------------
    execution_payload: Dict[str, Any] = {
        "scenario": scenario_name,
        "permission": permission,
        "stop_issued": stop_issued,
        "neuro_pause": neuro_pause,
    }

    execution_hash = _stable_hash(execution_payload)

    # -----------------------------
    # Ledger block payload
    # -----------------------------
    rblock_payload: Dict[str, Any] = {
        "scenario": scenario_name,
        "permission": permission,
        "stop_issued": stop_issued,
        "neuro_pause": neuro_pause,
        "previous_hash": None,          # genesis block
        "rblock_hash": execution_hash,  # embedded hash
    }

    # -----------------------------
    # Immutable ledger write
    # -----------------------------
    rblock_hash = write_rblock(
        rblock_payload,
        None,
        str(ledger_dir),
    )

    # -----------------------------
    # Advanced invariants (non-fatal)
    # -----------------------------
    ok = True
    if permission not in {"ALLOW", "BLOCK", "ASSIST"}:
        ok = False

    # -----------------------------
    # Return contract (tests rely on this)
    # -----------------------------
    return {
        "scenario": scenario_name,
        "hash": execution_hash,
        "rblock_hash": rblock_hash,
        "ledger_dir": str(ledger_dir),
        "ledger_path": str(ledger_dir),
        "permission": permission,
        "stop_issued": stop_issued,
        "neuro_pause": neuro_pause,
        "ok": ok,
    }
