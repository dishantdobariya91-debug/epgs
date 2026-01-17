# src/epgs/orchestrator/run.py

from pathlib import Path
import json
import hashlib
import shutil
from typing import Dict, Any

# Optional profile hook (CI-safe)
try:
    from epgs.profiles.base import apply_profile  # type: ignore
except ImportError:
    def apply_profile(_scenario: Dict[str, Any]) -> Dict[str, Any]:
        # Safe no-op fallback
        return _scenario


def _hash_payload(payload: Dict[str, Any]) -> str:
    """
    Deterministic content hash.
    """
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()


def _ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def run_scenario(
    scenario_path: str,
    output_root: str,
) -> Dict[str, Any]:
    """
    Executes a single scenario deterministically.

    Returns a dict (NOT an object) so tests can inspect fields safely.
    """

    scenario_path = Path(scenario_path)
    output_root = Path(output_root)

    with open(scenario_path, "r", encoding="utf-8") as f:
        scenario = json.load(f)

    # Apply optional profile (no-op in CI if missing)
    scenario = apply_profile(scenario)

    scenario_name = scenario_path.stem
    run_dir = output_root / scenario_name
    ledger_dir = run_dir / "ledger"

    _ensure_clean_dir(run_dir)
    ledger_dir.mkdir(parents=True, exist_ok=True)

    # Deterministic result payload
    result_payload = {
        "scenario": scenario_name,
        "sector": scenario.get("sector"),
        "perm": scenario.get("perm"),
        "stop": scenario.get("stop"),
        "final": scenario.get("final"),
    }

    result_hash = _hash_payload(result_payload)

    ledger_entry = {
        "hash": result_hash,
        "payload": result_payload,
    }

    ledger_file = ledger_dir / "result.json"
    with open(ledger_file, "w", encoding="utf-8") as f:
        json.dump(ledger_entry, f, indent=2, sort_keys=True)

    return {
        "scenario": scenario_name,
        "hash": result_hash,
        "ledger_path": str(ledger_file),
    }
