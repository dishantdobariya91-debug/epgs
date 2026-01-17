from __future__ import annotations

import json
import uuid
import hashlib
from pathlib import Path
from typing import Dict, Any

from epgs.modules.neurochain import write_rblock
from epgs.profiles.base import apply_profile

__all__ = ["run_scenario", "uuid"]


# ------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------

def _stable_hash(data: Dict[str, Any]) -> str:
    raw = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
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
    Execute a scenario and produce a deterministic ledger.

    This function is the canonical EPGS execution boundary.
    """

    scenario_path = Path(scenario_path)
    output_root = Path(output_root)

    scenario = _load_scenario(scenario_path)
    scenario_name = scenario.get("scenario", scenario_path.stem)

    ledger_dir = output_root / scenario_name / "ledger"
    ledger_dir.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------------
    # Apply execution profile
    # --------------------------------------------------------------
    profile = apply_profile(scenario)

    permission = profile.get("permission", "ALLOW")
    stop_issued = profile.get("stop_issued", False)
    neuro_pause = profile.get("neuro_pause", False)

    # --------------------------------------------------------------
    # Execution payload (canonical, deterministic)
    # --------------------------------------------------------------
    execution_payload: Dict[str, Any] = {
        "scenario": scenario_name,
        "permission": permission,
        "stop_issued": stop_issued,
        "neuro_pause": neuro_pause,
    }

    execution_hash = _stable_hash(execution_payload)

    # --------------------------------------------------------------
    # Ledger write (genesis R-block)
    # --------------------------------------------------------------
    rblock_hash = write_rblock(
        payload=execution_payload,
        previous_hash=None,
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
