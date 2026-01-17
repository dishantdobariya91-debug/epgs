#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
import uuid

from epgs.orchestrator.run import run_scenario


def run_once(scenario_path: Path, base_out: Path, run_id: str):
    """
    Run a scenario once with full isolation by output directory.
    """
    out_dir = base_out / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    result = run_scenario(
        scenario_path=scenario_path,
        output_root=str(out_dir),
    )

    return result


def extract_hash(result):
    """
    Normalize hash extraction across implementations.
    """
    if isinstance(result, dict):
        return (
            result.get("rblock_hash")
            or result.get("hash")
            or result.get("final_hash")
        )
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    base_out = Path(args.out).resolve()
    base_out.mkdir(parents=True, exist_ok=True)

    scenarios_dir = Path("src/epgs/scenarios")
    scenarios = sorted(scenarios_dir.glob("*.json"))

    if not scenarios:
        print("No scenarios found.")
        return 0

    print("\n=== Determinism Proof Summary (UGS-2027 EPGS) ===")
    print("Format:")
    print("[#] SCENARIO | HASH_RUN1 | HASH_RUN2 | MATCH")
    print("-" * 80)

    ok = True

    for i, scenario in enumerate(scenarios, 1):
        name = scenario.stem

        # Stable seed for deterministic paths
        seed = uuid.UUID("12345678-1234-5678-1234-567812345678")

        r1 = run_once(
            scenario,
            base_out,
            f"{name}_run1_{seed.hex[:8]}",
        )

        r2 = run_once(
            scenario,
            base_out,
            f"{name}_run2_{seed.hex[:8]}",
        )

        h1 = extract_hash(r1)
        h2 = extract_hash(r2)

        match = h1 == h2
        ok = ok and match

        print(
            f"[{i}] {name} | "
            f"{str(h1)[:12]} | {str(h2)[:12]} | "
            f"{'OK' if match else 'FAIL'}"
        )

    print("-" * 80)

    if not ok:
        print("Determinism check FAILED")
        return 1

    print("Determinism check PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
