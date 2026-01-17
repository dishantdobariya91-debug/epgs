from pathlib import Path
import json

from epgs.modules.neurochain import write_rblock
from epgs.scenarios.load import load_scenario
from epgs.profiles.base import apply_profile


def run_scenario(
    scenario_path: Path,
    output_root: str,
    ledger_root: str,
):
    """
    Execute a single EPGS scenario deterministically.

    Args:
        scenario_path: path to scenario JSON
        output_root: directory for run outputs
        ledger_root: isolated ledger directory (per run)

    Returns:
        dict with deterministic hash
    """

    scenario_path = Path(scenario_path)
    output_root = Path(output_root)
    ledger_root = Path(ledger_root)

    output_root.mkdir(parents=True, exist_ok=True)
    ledger_root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------
    # 1. Load scenario (pure input)
    # ------------------------------------------------------------
    scenario = load_scenario(scenario_path)

    # ------------------------------------------------------------
    # 2. Apply profile deterministically
    #    (NO timestamps, NO randomness here)
    # ------------------------------------------------------------
    final_state = apply_profile(scenario)

    # ------------------------------------------------------------
    # 3. Write immutable R-Block (content-hash only)
    # ------------------------------------------------------------
    rblock_hash = write_rblock(
        state=final_state,
        ledger_dir=str(ledger_root),
    )

    # ------------------------------------------------------------
    # 4. Persist run metadata (NON-HASHED, informational only)
    # ------------------------------------------------------------
    run_meta = {
        "scenario": scenario_path.name,
        "rblock_hash": rblock_hash,
    }

    (output_root / "run.json").write_text(
        json.dumps(run_meta, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    # ------------------------------------------------------------
    # 5. Return deterministic result ONLY
    # ------------------------------------------------------------
    return {
        "hash": rblock_hash
    }
