from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Dict, Any

from epgs.core.crypto import chained_hash
from epgs.profiles.base import apply_profile

GENESIS_HASH = "0" * 64

# Stable namespace for per-scenario determinism
NAMESPACE = uuid.UUID("12345678-1234-5678-1234-567812345678")


def run_scenario(
    scenario_path: str | Path,
    *,
    output_root: str | Path,
) -> Dict[str, Any]:
    """
    Deterministic scenario execution.

    Accepts scenario schemas:
    - { "scenario": "NAME" }          (legacy)
    - { "scenario_id": "NAME" }       (current)
    - { "path": "other.json" }        (wrapper)
    - filename stem fallback
    """

    scenario_path = Path(scenario_path)
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    scenario_obj = json.loads(scenario_path.read_text(encoding="utf-8"))

    # --------------------------------------------------------
    # Resolve scenario source (robust + deterministic)
    # --------------------------------------------------------
    scenario = None
    scenario_name = None

    if "path" in scenario_obj:
        # Wrapper pointing to another JSON file
        resolved = (scenario_path.parent / scenario_obj["path"]).resolve()
        scenario = json.loads(resolved.read_text(encoding="utf-8"))
        scenario_name = (
            scenario.get("scenario")
            or scenario.get("scenario_id")
            or resolved.stem
        )
    else:
        # Direct scenario JSON
        scenario = scenario_obj
        scenario_name = (
            scenario.get("scenario")
            or scenario.get("scenario_id")
            or scenario_path.stem
        )

    # Canonical internal key expected downstream
    scenario["scenario"] = str(scenario_name)

    # ------------------------------------------------------------
    # Deterministic identifiers (per scenario)
    # ------------------------------------------------------------
    run_id = str(uuid.uuid5(NAMESPACE, f"{scenario_name}::run"))
    rblock_id = str(uuid.uuid5(NAMESPACE, f"{scenario_name}::rblock"))

    # ------------------------------------------------------------
    # Apply governance profile
    # ------------------------------------------------------------
    profile = apply_profile(scenario)

    permission = profile["permission"]
    stop_issued = profile["stop_issued"]
    neuro_pause = profile["neuro_pause"]

    # ------------------------------------------------------------
    # Determine terminal semantics
    # ------------------------------------------------------------
    terminal_stop = permission == "BLOCK"

    if stop_issued:
        final_state = "TERMINATED"
    elif permission == "ASSIST":
        final_state = "EXECUTED"
    else:
        final_state = "COMPLETED"

    # ------------------------------------------------------------
    # Ledger directory
    # ------------------------------------------------------------
    ledger_dir = output_root / "ledger"
    ledger_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------
    # Build R-Block payload (NO hashes yet)
    # ------------------------------------------------------------
    payload: Dict[str, Any] = {
        "run_id": run_id,
        "rblock_id": rblock_id,
        "scenario": scenario_name,
        "permission": permission,
        "stop_issued": stop_issued,
        "terminal_stop": terminal_stop,
        "final_state": final_state,
        "neuropause": {
            "enabled": neuro_pause,
            "tau_ms_observed": 0,
        },
    }

    # ------------------------------------------------------------
    # Chain hashing (authoritative)
    # ------------------------------------------------------------
    previous_hash = GENESIS_HASH
    rblock_hash = chained_hash(payload, previous_hash)

    rblock = dict(payload)
    rblock["previous_hash"] = previous_hash
    rblock["rblock_hash"] = rblock_hash

    # ------------------------------------------------------------
    # Write ledger file (stable ordering)
    # ------------------------------------------------------------
    ledger_path = ledger_dir / "0001.json"
    ledger_path.write_text(
        json.dumps(
            rblock,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )

    # ------------------------------------------------------------
    # Return execution result
    # ------------------------------------------------------------
    return {
        "run_id": run_id,
        "rblock_id": rblock_id,
        "permission": permission,
        "stop_issued": stop_issued,
        "terminal_stop": terminal_stop,
        "final_state": final_state,
        "neuro_pause": neuro_pause,
        "ledger_dir": str(ledger_dir),
        "execution_hash": rblock_hash,
        "output_root": str(output_root),
    }
