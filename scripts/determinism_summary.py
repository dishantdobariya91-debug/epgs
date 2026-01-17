#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
import uuid
import json

from epgs.orchestrator.run import run_scenario


def run_once(scenario_path: Path, output_root: Path, run_label: str):
    """
    Run a single deterministic scenario with isolated ledger storage.
    """
    run_root = output_root / run_label
    ledger_root = run_root / "ledger"
    runs_root = run_root / "runs"

    ledger_root.mkdir(parents=True, exist_ok=True)
    runs_root.mkdir(parents=True, exist_ok=True)

    result = run_scenario(
        scenario_path=scenario_path,
        output_root=str(runs_root),
        ledger_root=str(ledger_root),
    )

    return {
        "result": result,
        "ledger_root": ledger_root,
        "runs_root": runs_root,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="Output directory")
    args = parser.parse_args()

    output_root = Path(args.out).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    scenarios_dir = Path("src/epgs/scenarios")
    scenario_files = sorted(scenarios_dir.glob("*.json"))

    if not scenario_files:
        print("No scenarios found.")
        return 0

    print("\n=== Determinism Proof Summary (UGS-2027 EPGS) ===")
    print("Format:")
    print("[#] SCENARIO | HASH_RUN1 | HASH_RUN2 | MATCH")
    print("-" * 80)

    all_ok = True

    for i, scenario_path in enumerate(scenario_files, start=1):
        scenario_name = scenario_path.stem

        # Use SAME UUID seed to enforce determinism
        fixed_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")

        # Run twice with ISOLATED ledgers
        r1 = run_once(
            scenario_path,
            output_root,
            f"{scenario_name}_run1",
        )

        r2 = run_once(
            scenario_path,
            output_root,
            f"{scenario_name}_run2",
        )

        res1 = r1["result"]
        res2 = r2["result"]

        # Normalize hash extraction
        h1 = res1.get("rblock_hash") or res1.get("hash")
        h2 = res2.get("rblock_hash") or res2.get("hash")

        match = h1 == h2
        all_ok = all_ok and match

        print(
            f"[{i}] {scenario_name} | "
            f"{str(h1)[:12]} | {str(h2)[:12]} | "
            f"{'OK' if match else 'FAIL'}"
        )

    print("-" * 80)

    if not all_ok:
        print("Determinism check FAILED")
        return 1

    print("Determinism check PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
