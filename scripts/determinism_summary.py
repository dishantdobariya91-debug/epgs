from __future__ import annotations

import argparse
import uuid
from pathlib import Path

import epgs.orchestrator.run as run_module
from epgs.orchestrator.run import run_scenario
from epgs.orchestrator.replay import verify_chain


SCENARIOS = [
    "src/epgs/scenarios/S-STABLE-SAFE.json",
    "src/epgs/scenarios/S-FAST-NOTREADY.json",
    "src/epgs/scenarios/S-CAUTION-ASSIST.json",
    "src/epgs/scenarios/S-MIDSTOP-DEGRADE.json",
    "src/epgs/scenarios/S-NRRP-TERMINATE.json",
]


class FixedUUIDSequence:
    """
    CI-only deterministic UUID injector.
    Ensures identical UUIDs for run #1 and run #2 of the same scenario.
    """

    def __init__(self, run_id: str, rblock_id: str):
        self.values = [run_id, rblock_id]
        self.idx = 0

    def reset(self):
        self.idx = 0

    def uuid4(self):
        v = self.values[self.idx]
        self.idx = (self.idx + 1) % 2
        return v


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        default="output_ci",
        help="Output root for CI runs",
    )
    args = parser.parse_args()

    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)

    print("=== Determinism Proof Summary (UGS-2027 EPGS) ===")
    print("Format:")
    print(
        "[#] SCENARIO | SECTOR | PERM | STOP | FINAL | HASH | "
        "LEDGER_RUN1 | LEDGER_RUN2 | VERIFY | MATCH"
    )
    print("-" * 120)

    ok = True

    for i, scenario_path in enumerate(SCENARIOS):
        # --- Fixed UUIDs (deterministic identity) ---
        run_uuid = f"11111111-1111-1111-1111-{i:012d}"
        rblock_uuid = f"22222222-2222-2222-2222-{i:012d}"

        fixed = FixedUUIDSequence(run_uuid, rblock_uuid)
        run_module.uuid.uuid4 = fixed.uuid4  # CI-only monkey patch

        # --- UNIQUE per-run isolation (CRITICAL FIX) ---
        run_ns = f"scenario_{i}_{uuid.uuid4().hex[:8]}"
        out1 = out_root / run_ns / "run1"
        out2 = out_root / run_ns / "run2"

        # --- Run #1 ---
        fixed.reset()
        res1 = run_scenario(
            scenario_path,
            output_root=str(out1),
        )
        v1 = verify_chain(res1["ledger_dir"])

        # --- Run #2 ---
        fixed.reset()
        res2 = run_scenario(
            scenario_path,
            output_root=str(out2),
        )
        v2 = verify_chain(res2["ledger_dir"])

        same = (
            res1 == res2
            and v1.get("ok") is True
            and v2.get("ok") is True
        )

        line = (
            f"[{i}] {res1['scenario_id']:<18} | "
            f"{res1['sector_label']:<18} | "
            f"{res1['permission']:<6} | "
            f"{str(res1['stop_issued']):<5} | "
            f"{res1['final_state']:<10} | "
            f"{res1['rblock_hash'][:16]}... | "
            f"{res1['ledger_dir']} | "
            f"{res2['ledger_dir']} | "
            f"{v1.get('ok') and v2.get('ok')} | "
            f"{same}"
        )

        print(line)

        if not same:
            ok = False
            print(f"  ERROR: Determinism or verification failure for {scenario_path}")
            print(f"  run1={res1}")
            print(f"  run2={res2}")
            print(f"  verify1={v1}")
            print(f"  verify2={v2}")

    print("-" * 120)
    print("=== Determinism Proof Result:", "PASS" if ok else "FAIL", "===")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
