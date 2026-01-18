from __future__ import annotations

import json
import uuid
import hashlib
from pathlib import Path
from typing import Any, Dict

from epgs.profiles.base import apply_profile


# ---------------------------------------------------------------------
# Deterministic UUID namespace (CI authoritative)
# ---------------------------------------------------------------------
NAMESPACE = uuid.UUID("12345678-1234-5678-1234-567812345678")


def _hash_dict(obj: Dict[str, Any]) -> str:
    """Deterministic SHA256 hash of a dict."""
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def run_scenario(
    scenario_path: str | Path,
    *,
    output_root: str | Path,
) -> Dict[str, Any]:
    """
    Deterministic scenario execution (CI authoritative).

    Supported inputs:
    1) Scenario JSON containing "scenario"
    2) Scenario JSON containing "path"
    3) Direct scenario JSON file (CI default)
    """

    scenario_path = Path(scenario_path)
    output_root = Path(output_root)

    scenario_obj = json.loads(scenario_path.read_text(encoding="utf-8"))

    # ------------------------------------------------------------------
    # Resolve scenario source (CRITICAL CI FIX)
    # ------------------------------------------------------------------
    if "scenario" in scenario_obj:
        # Inline scenario
        scenario_name = scenario_obj["scenario"]
        scenario = scenario_obj

    elif "path" in scenario_obj:
        # Indirect scenario reference
        resolved = Path(scenario_obj["path"]).resolve()
        scenario = json.loads(resolved.read_text(encoding="utf-8"))
        scenario_name = resolved.stem

    else:
        # Direct scenario file (CI default behavior)
        scenario = scenario_obj
        scenario_name = scenario_path.stem

    # ------------------------------------------------------------------
    # Deterministic identifiers (per scenario)
    # ------------------------------------------------------------------
    run_id = str(uuid.uuid5(NAMESPACE, f"{scenario_name}::run"))
    rblock_id = str(uuid.uuid5(NAMESPACE, f"{scenario_name}::rblock"))

    # ------------------------------------------------------------------
    # Governance profile (CI authoritative)
    # ------------------------------------------------------------------
    profile = apply_profile({"scenario": scenario_name, **scenario})

    # ------------------------------------------------------------------
    # Execution payload (MUST be deterministic)
    # ------------------------------------------------------------------
    execution_payload = {
        "run_id": run_id,
        "scenario": scenario_name,
        "scenario_data": scenario,
        "governance": profile,
    }

    execution_hash = _hash_dict(execution_payload)

    # ------------------------------------------------------------------
    # RBlock (ledger block)
    # ------------------------------------------------------------------
    rblock = {
        "rblock_id": rblock_id,
        "execution_hash": execution_hash,
        "permission": profile["permission"],
        "stop_issued": profile["stop_issued"],
        "neuro_pause": profile["neuro_pause"],
    }

    rblock_hash = _hash_dict(rblock)

    # ------------------------------------------------------------------
    # Persist artifacts (CI requires presence, content deterministic)
    # ------------------------------------------------------------------
    output_root.mkdir(parents=True, exist_ok=True)

    (output_root / "execution.json").write_text(
        json.dumps(execution_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    (output_root / "rblock.json").write_text(
        json.dumps(rblock, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    (output_root / "hashes.json").write_text(
        json.dumps(
            {
                "execution_hash": execution_hash,
                "rblock_hash": rblock_hash,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    # ------------------------------------------------------------------
    # Final result (API + tests rely on this schema)
    # ------------------------------------------------------------------
    return {
        "run_id": run_id,
        "rblock_id": rblock_id,
        "scenario": scenario_name,
        "permission": profile["permission"],
        "stop_issued": profile["stop_issued"],
        "neuro_pause": profile["neuro_pause"],
        "execution_hash": execution_hash,
        "rblock_hash": rblock_hash,
        "output_root": str(output_root),
    }
