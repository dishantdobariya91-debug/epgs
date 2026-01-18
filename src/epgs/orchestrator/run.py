from __future__ import annotations

import json
import uuid
import hashlib
from pathlib import Path
from typing import Any, Dict

from epgs.profiles.base import apply_profile

# ------------------------------------------------------------------
# Deterministic UUID namespace (CI authoritative)
# ------------------------------------------------------------------
NAMESPACE = uuid.UUID("12345678-1234-5678-1234-567812345678")


def _hash(obj: Dict[str, Any]) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _neuropause_block(enabled: bool) -> Dict[str, Any]:
    return {
        "enabled": enabled,
        "tau_ms_observed": 0,
    }


def run_scenario(
    scenario_path: str | Path,
    *,
    output_root: str | Path,
) -> Dict[str, Any]:

    scenario_path = Path(scenario_path)
    output_root = Path(output_root)

    scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
    scenario_name = scenario.get("scenario", scenario_path.stem)

    # ------------------------------------------------------------------
    # Deterministic IDs (per scenario)
    # ------------------------------------------------------------------
    run_id = str(uuid.uuid5(NAMESPACE, f"{scenario_name}::run"))
    rblock_id = str(uuid.uuid5(NAMESPACE, f"{scenario_name}::rblock"))

    # ------------------------------------------------------------------
    # Governance
    # ------------------------------------------------------------------
    profile = apply_profile({"scenario": scenario_name, **scenario})

    permission = profile["permission"]
    stop_issued = profile["stop_issued"]
    neuro_pause = profile["neuro_pause"]

    terminal_stop = permission == "BLOCK"

    if permission == "ASSIST":
        final_state = "EXECUTED"
    elif terminal_stop or stop_issued:
        final_state = "TERMINATED"
    else:
        final_state = "COMPLETED"

    # ------------------------------------------------------------------
    # Ledger directory
    # ------------------------------------------------------------------
    ledger_dir = output_root / "ledger"
    ledger_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Genesis block
    # ------------------------------------------------------------------
    genesis = {
        "type": "genesis",
        "run_id": run_id,
        "scenario": scenario_name,
        "previous_hash": "GENESIS",
        "neuropause": _neuropause_block(False),
    }
    genesis_hash = _hash(genesis)

    (ledger_dir / "000_genesis.json").write_text(
        json.dumps(genesis, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    # ------------------------------------------------------------------
    # Execution block
    # ------------------------------------------------------------------
    execution = {
        "type": "execution",
        "run_id": run_id,
        "scenario": scenario_name,
        "permission": permission,
        "stop_issued": stop_issued,
        "previous_hash": genesis_hash,
        "neuropause": _neuropause_block(neuro_pause),
    }
    execution_hash = _hash(execution)

    (ledger_dir / "001_execution.json").write_text(
        json.dumps(execution, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    # ------------------------------------------------------------------
    # R-Block (tamper-sensitive)
    # ------------------------------------------------------------------
    rblock = {
        "type": "rblock",
        "rblock_id": rblock_id,
        "permission": permission,
        "terminal_stop": terminal_stop,
        "final_state": final_state,
        "previous_hash": execution_hash,
        "neuropause": _neuropause_block(neuro_pause),
    }
    rblock_hash = _hash(rblock)

    (ledger_dir / "002_rblock.json").write_text(
        json.dumps(rblock, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    # ------------------------------------------------------------------
    # Return schema (TEST CONTRACT)
    # ------------------------------------------------------------------
    return {
        "run_id": run_id,
        "rblock_id": rblock_id,
        "scenario": scenario_name,
        "permission": permission,
        "stop_issued": stop_issued,
        "neuro_pause": neuro_pause,
        "terminal_stop": terminal_stop,
        "final_state": final_state,
        "execution_hash": execution_hash,
        "rblock_hash": rblock_hash,
        "ledger_dir": str(ledger_dir),
    }
