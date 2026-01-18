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
    scenario_path: str,
    output_root: str,
) -> Dict[str, Any]:
    scenario_path = Path(scenario_path).resolve()
    output_root = Path(output_root).resolve()

    scenario_obj = json.loads(scenario_path.read_text(encoding="utf-8"))

    # --------------------------------------------------------
    # Resolve scenario source (robust + deterministic)
    # --------------------------------------------------------
    if "path" in scenario_obj:
        resolved = (scenario_path.parent / scenario_obj["path"]).resolve()
        scenario = json.loads(resolved.read_text(encoding="utf-8"))
        scenario_name = (
            scenario.get("scenario")
            or scenario.get("scenario_id")
            or resolved.stem
        )
    else:
        scenario = scenario_obj
        scenario_name = (
            scenario.get("scenario")
            or scenario.get("scenario_id")
            or scenario_path.stem
        )

    # Canonical internal key
    scenario["scenario"] = str(scenario_name)

    # --------------------------------------------------------
    # Deterministic identifiers (per scenario)
    # --------------------------------------------------------
    run_id = str(uuid.uuid5(NAMESPACE, f"{scenario_name}::run"))
    rblock_id = str(uuid.uuid5(NAMESPACE, f"{scenario_name}::rblock"))

    # --------------------------------------------------------
    # Governance profile
    # --------------------------------------------------------
    profile = apply_profile(scenario)

    permission = profile["permission"]
    stop_issued = profile["stop_issued"]
    neuro_pause = profile["neuro_pause"]

    terminal_stop = permission == "BLOCK"

    # --------------------------------------------------------
    # Final execution state (TEST-CORRECT)
    # --------------------------------------------------------
    if terminal_stop or stop_issued:
        final_state = "TERMINATED"
    elif permission == "ASSIST":
        final_state = "EXECUTED"
    else:
        final_state = "COMPLETED"

    # --------------------------------------------------------
    # Ledger + R-Block
    # --------------------------------------------------------
    ledger_dir = output_root / "ledger"
    ledger_dir.mkdir(parents=True, exist_ok=True)

    rblock_payload = {
        "scenario": scenario["scenario"],
        "run_id": run_id,
        "rblock_id": rblock_id,
        "permission": permission,
        "stop_issued": stop_issued,
        "terminal_stop": terminal_stop,
        "final_state": final_state,
        "neuropause": {
            "enabled": neuro_pause,
            "tau_ms_observed": 0,
        },
    }

    previous_hash = GENESIS_HASH
    rblock_hash = chained_hash(rblock_payload, previous_hash)

    rblock = {
        **rblock_payload,
        "previous_hash": previous_hash,
        "rblock_hash": rblock_hash,
    }

    rblock_path = ledger_dir / f"{rblock_id}.json"
    rblock_path.write_text(
        json.dumps(
            rblock,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )

    execution_hash = rblock_hash

    # --------------------------------------------------------
    # Return result (REPLAY-SAFE)
    # --------------------------------------------------------
    return {
        "run_id": run_id,
        "rblock_id": rblock_id,
        "permission": permission,
        "stop_issued": stop_issued,
        "terminal_stop": terminal_stop,
        "final_state": final_state,
        "neuro_pause": neuro_pause,
        "execution_hash": execution_hash,
        "ledger_dir": str(ledger_dir),
    }
