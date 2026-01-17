from pathlib import Path

import epgs.orchestrator.run as run_module
from epgs.orchestrator.run import run_scenario
from epgs.orchestrator.replay import verify_chain


class FixedUUIDSequence:
    """
    Deterministic UUID generator for tests.
    run_scenario() calls uuid.uuid4() twice:
      1) run_id
      2) rblock_id
    """
    def __init__(self):
        self.values = [
            "11111111-1111-1111-1111-111111111111",  # run_id
            "22222222-2222-2222-2222-222222222222",  # rblock_id
        ]
        self.idx = 0

    def reset(self):
        self.idx = 0

    def uuid4(self):
        v = self.values[self.idx]
        self.idx = (self.idx + 1) % len(self.values)
        return v


def test_replay_equivalence_same_inputs_same_outputs_and_hashes(monkeypatch, tmp_path):
    scenario_path = "src/epgs/scenarios/S-STABLE-SAFE.json"

    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"

    fixed = FixedUUIDSequence()

    # Patch uuid.uuid4 ONLY inside orchestrator
    monkeypatch.setattr(run_module.uuid, "uuid4", fixed.uuid4)

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

    # Remove environment-specific fields before comparison
    r1 = dict(res1)
    r2 = dict(res2)
    r1.pop("ledger_dir")
    r2.pop("ledger_dir")

    # Deterministic run result
    assert r1 == r2

    # Extra proof: R-Block contents identical
    ledger1 = Path(res1["ledger_dir"])
    ledger2 = Path(res2["ledger_dir"])

    files1 = sorted(ledger1.glob("*.json"))
    files2 = sorted(ledger2.glob("*.json"))
    assert len(files1) == len(files2) >= 1

    content1 = files1[0].read_text(encoding="utf-8")
    content2 = files2[0].read_text(encoding="utf-8")
    assert content1 == content2
