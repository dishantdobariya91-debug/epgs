from __future__ import annotations

import argparse
import sys
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
    parser.add_argument("--out", default="output_ci", help="Output root for CI runs")
    args = parser.parse_args()

    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)

    print("=== Determinism Proof Summary (UGS-2027 EPGS) ===")
    print("Format:")
    print("[#] SCENARIO | SECTOR | PERM | STOP | FINAL | HASH | LEDGER_RUN1 | LEDGER_RUN2 | VERIFY | MATCH")
    print("-" * 120)

    ok = True

    for i, scenario_path in enumerate(SCENARIOS):
        run_id = f"11111111-1111-1111-1111-{i:012d}"
        rblock_id = f"22222222-2222-2222-2222-{i:012d}"

        fixed = FixedUUIDSequence(run_id, rblock_id)
        run_module.uuid.uuid4 = fixed.uuid4  # CI-only patch

        out1 = out_root / f"scenario_{i}_run1"
        out2 = out_root / f"scenario_{i}_run2"

        # --- Run #1 ---
        fixed.reset()
        res1 = run_scenario(scenario_path, output_root=str(out1))
        v1 = verify_chain(res1["ledger_dir"])

        # --- Run #2 ---
        fixed.reset()
        res2 = run_scenario(scenario_path, output_root=str(out2))
        v2 = verify_chain(res2["ledger_dir"])

        match = (
            res1["rblock_hash"] == res2["rblock_hash"]
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
            f"{match}"
        )

        print(line)

        if not match:
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
    sys.exit(main())
