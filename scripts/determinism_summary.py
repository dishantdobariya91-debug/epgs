#!/usr/bin/env python3
import argparse
import sys
import uuid as uuid_lib
from pathlib import Path

from epgs.orchestrator.run import run_scenario


HEADER = (
    "=== Determinism Proof Summary (UGS-2027 EPGS) ===\n"
    "Format:\n"
    "[#] SCENARIO | SECTOR | PERM | STOP | FINAL | HASH | "
    "LEDGER_RUN1 | LEDGER_RUN2 | VERIFY | MATCH\n"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="Output directory")
    args = parser.parse_args()

    output_root = Path(args.out)
    output_root.mkdir(parents=True, exist_ok=True)

    scenarios_dir = Path("src/epgs/scenarios")
    scenario_files = sorted(p for p in scenarios_dir.glob("*.json"))

    print(HEADER)

    ok = True

    for i, scenario_path in enumerate(scenario_files):
        # 🔐 Unique namespace per run (CRITICAL FIX)
        run_ns = f"scenario_{i}_{uuid_lib.uuid4().hex[:8]}"

        run1_out = output_root / run_ns / "run1"
        run2_out = output_root / run_ns / "run2"

        run1_out.mkdir(parents=True, exist_ok=True)
        run2_out.mkdir(parents=True, exist_ok=True)

        res1 = run_scenario(
            scenario_path=scenario_path,
            output_root=str(run1_out),
        )
        res2 = run_scenario(
            scenario_path=scenario_path,
            output_root=str(run2_out),
        )

        match = res1.hash == res2.hash

        print(
            f"[{i}] {res1.scenario} | {res1.sector} | {res1.permission} | "
            f"{res1.stop} | {res1.final} | {res1.hash[:16]}... | "
            f"{run1_out} | {run2_out} | {res1.verified} | {match}"
        )

        if not match:
            ok = False

    print("\n=== Determinism Proof Result:", "PASS" if ok else "FAIL", "===")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
