from epgs.orchestrator.run import run_scenario
from epgs.orchestrator.replay import verify_chain


def test_run_produces_valid_chain(tmp_path):
    out_root = tmp_path.as_posix()
    result = run_scenario(
        "src/epgs/scenarios/S-STABLE-SAFE.json",
        output_root=out_root,
    )
    v = verify_chain(result["ledger_dir"])
    assert v["ok"] is True
