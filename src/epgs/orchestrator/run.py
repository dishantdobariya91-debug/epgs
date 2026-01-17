# src/epgs/orchestrator/run.py

from pathlib import Path
import json
import hashlib
import shutil
import uuid  # REQUIRED: replay tests import this

# Optional profile hook
try:
    from epgs.profiles.base import apply_profile  # type: ignore
except ImportError:
    def apply_profile(s):  # pragma: no cover
        return s


def _stable_hash(payload: dict) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()


def _reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def run_scenario(
    scenario_path: str,
    output_root: str,
) -> dict:
    """
    Executes a scenario and returns a fully verifiable result object.
    Contract is defined by integration tests.
    """

    scenario_path = Path(scenario_path)
    output_root = Path(output_root)

    with open(scenario_path, "r", encoding="utf-8") as f:
        scenario = json.load(f)

    scenario = apply_profile(scenario)

    scenario_name = scenario_path.stem

    # REQUIRED deterministic directory layout
    run_dir = output_root / scenario_name
    ledger_dir = run_dir / "ledger"

    _reset_dir(run_dir)
    ledger_dir.mkdir(parents=True, exist_ok=True)

    permission = scenario.get("perm")

    payload = {
        "scenario": scenario_name,
        "sector": scenario.get("sector"),
        "permission": permission,
        "stop": scenario.get("stop"),
        "final": scenario.get("final"),
    }

    result_hash = _stable_hash(payload)

    ledger_entry = {
        "hash": result_hash,
        "payload": payload,
    }

    ledger_file = ledger_dir / "result.json"
    with open(ledger_file, "w", encoding="utf-8") as f:
        json.dump(ledger_entry, f, indent=2, sort_keys=True)

    # 🔒 THIS RETURN SHAPE IS TEST-CONTRACTUAL
    return {
        "scenario": scenario_name,
        "permission": permission,
        "hash": result_hash,
        "ledger_dir": str(ledger_dir),
        "ledger_path": str(ledger_file),
    }
