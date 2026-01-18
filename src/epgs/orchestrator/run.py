from __future__ import annotations

import json
import uuid
import hashlib
from pathlib import Path
from typing import Dict, Any

from epgs.profiles.base import apply_profile

# ------------------------------------------------------------------
# Deterministic UUID namespace
# ------------------------------------------------------------------
NAMESPACE = uuid.UUID("12345678-1234-5678-1234-567812345678")


def _hash_payload(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _with_hash(payload: Dict[str, Any]) -> Dict[str, Any]:
    h = _hash_payload(payload)
    out = dict(payload)
    out["rblock_hash"] = h
    return out


def _neuropause(enabled: bool) -> Dict[str, Any]:
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
    # Deterministic IDs
    # ------------------------------------------------------------------
    run_id = str(uuid.uuid5(NAMESPACE, f"{scenario_name}::run"))
    rblock_id = str(uuid.uuid5(NAMESPACE, f"{scenario_name}::rblock"))

    # ------------------------------------------------------------------
    # Governance
    # ------------------------------------------------------------------
    policy = apply_profile({"scenario": scenario_name, **scenario})

    permission = policy["permission"]
    stop_issued = policy["stop_issued"]
    neuro_pause = policy["neuro_pause"]

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
    ledger_dir = Path(output_root) / "ledger"
    ledger_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Genesis block
    # ------------------------------------------------------------------
    genesis_payload = {
        "type": "genesis",
        "run_id": run_id,
        "scenario": scenario_name,
        "previous_hash": "GENESIS",
        "neuropause": _neuropause(False),
    }
    genesis = _with_hash(genesis_payload)

    (ledger_dir / "000_genesis.json").write_text(
        json.dumps(genesis, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    # ------------------------------------------------------------------
    # Execution block
    # ------------------------------------------------------------------
    execution_payload = {
        "type": "execution",
        "run_id": run_id,
        "scenario": scenario_name,
        "permission": permission,
        "stop_issued": stop_issued,
        "previous_hash": genesis["rblock_hash"],
        "neuropause": _neuropause(neuro_pause),
    }
    execution = _with_hash(execution_payload)

    (ledger_dir / "001_execution.json").write_text(
        json.dumps(execution, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    # ------------------------------------------------------------------
    # R-Block
    # ------------------------------------------------------------------
    rblock_payload = {
        "type": "rblock",
        "rblock_id": rblock_id,
        "permission": permission,
        "terminal_stop": terminal_stop,
        "final_state": final_state,
        "previous_hash": execution["rblock_hash"],
        "neuropause": _neuropause(neuro_pause),
    }
    rblock = _with_hash(rblock_payload)

    (ledger_dir / "002_rblock.json").write_text(
        json.dumps(rblock, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    # ------------------------------------------------------------------
    # Return contract (tests rely on this)
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
        "execution_hash": execution["rblock_hash"],
        "rblock_hash": rblock["rblock_hash"],
        "ledger_dir": str(ledger_dir),
    }
