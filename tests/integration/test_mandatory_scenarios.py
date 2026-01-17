from epgs.orchestrator.run import run_scenario


def test_fast_notready_blocks_and_terminates(tmp_path):
    out_root = tmp_path.as_posix()
    result = run_scenario("src/epgs/scenarios/S-FAST-NOTREADY.json", output_root=out_root)

    assert result["permission"] == "BLOCK"
    assert result["stop_issued"] is False
    assert result["terminal_stop"] is True
    assert result["final_state"] == "TERMINATED"


def test_caution_assist_executes(tmp_path):
    out_root = tmp_path.as_posix()
    result = run_scenario("src/epgs/scenarios/S-CAUTION-ASSIST.json", output_root=out_root)

    assert result["permission"] == "ASSIST"
    assert result["stop_issued"] is False
    assert result["terminal_stop"] is False
    assert result["final_state"] == "EXECUTED"


def test_midstop_degrade_stops_execution(tmp_path):
    out_root = tmp_path.as_posix()
    result = run_scenario("src/epgs/scenarios/S-MIDSTOP-DEGRADE.json", output_root=out_root)

    assert result["permission"] == "ALLOW"
    assert result["stop_issued"] is True
    assert result["final_state"] == "TERMINATED"



def test_nrrp_terminate_blocks_and_terminates(tmp_path):
    out_root = tmp_path.as_posix()
    result = run_scenario("src/epgs/scenarios/S-NRRP-TERMINATE.json", output_root=out_root)

    assert result["permission"] == "BLOCK"
    assert result["stop_issued"] is False
    assert result["terminal_stop"] is True
    assert result["final_state"] == "TERMINATED"
