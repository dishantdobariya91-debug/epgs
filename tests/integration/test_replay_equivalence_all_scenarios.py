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
    Deterministic UUID generator.
    Each run_scenario() calls uuid.uuid4() twice:
      1) run_id
      2) rblock_id
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


def test_replay_equivalence_all_scenarios(monkeypatch, tmp_path):
    for i, scenario_path in enumerate(SCENARIOS):
        # Unique deterministic IDs per scenario
        run_id = f"11111111-1111-1111-1111-{i:012d}"
        rblock_id = f"22222222-2222-2222-2222-{i:012d}"

        fixed = FixedUUIDSequence(run_id, rblock_id)
        monkeypatch.setattr(run_module.uuid, "uuid4", fixed.uuid4)

        out1 = tmp_path / f"scenario_{i}_run1"
        out2 = tmp_path / f"scenario_{i}_run2"

        # --- Run #1 ---
        fixed.reset()
        res1 = run_scenario(scenario_path, output_root=str(out1))
        v1 = verify_chain(res1["ledger_dir"])
        assert v1["ok"] is True

        # --- Run #2 ---
        fixed.reset()
        res2 = run_scenario(scenario_path, output_root=str(out2))
        v2 = verify_chain(res2["ledger_dir"])
        assert v2["ok"] is True

        # Compare run results EXCEPT filesystem paths
        r1 = dict(res1)
        r2 = dict(res2)
        r1.pop("ledger_dir")
        r2.pop("ledger_dir")

        assert r1 == r2, f"Run mismatch for {scenario_path}"

        # Strongest proof: byte-identical R-Blocks
        ledger1 = Path(res1["ledger_dir"])
        ledger2 = Path(res2["ledger_dir"])

        files1 = sorted(ledger1.glob("*.json"))
        files2 = sorted(ledger2.glob("*.json"))
        assert len(files1) == len(files2) >= 1

        for f1, f2 in zip(files1, files2):
            assert f1.read_text(encoding="utf-8") == f2.read_text(encoding="utf-8")
