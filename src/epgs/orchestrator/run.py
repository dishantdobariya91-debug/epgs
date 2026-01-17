from __future__ import annotations

from pathlib import Path
import uuid

from epgs.profiles.base import BaseProfile
from epgs.scenarios.load import load_scenario
from epgs.modules.decision_generator import generate_requests
from epgs.modules.neuropause import evaluate_temporal
from epgs.modules.ube import classify
from epgs.modules.aegixa import precheck, mid_execution_monitor
from epgs.modules.nrrp import decide as nrrp_decide
from epgs.modules.execution_sink import sink
from epgs.modules.neurochain import write_rblock

GENESIS_HASH = "0" * 64


def run_scenario(scenario_path: str, output_root: str = "output") -> dict:
    profile = BaseProfile()
    scenario = load_scenario(scenario_path)
    run_id = str(uuid.uuid4())

    requests = generate_requests(scenario)
    req = requests[0]

    np_out = evaluate_temporal(scenario.temporal)

    ube0_vec = sorted(scenario.ube_vectors, key=lambda x: x.step_index)[0]
    ube0 = classify(ube0_vec, profile)

    aeg0 = precheck(np_out, ube0)

    stop_out = None
    if aeg0.permission.value in ("ALLOW", "ASSIST"):
        for v in sorted(scenario.ube_vectors, key=lambda x: x.step_index):
            u = classify(v, profile)
            stop = mid_execution_monitor(v.step_index, u)
            if stop:
                stop_out = stop
                break

    aeg_final = stop_out if stop_out else aeg0

    nrrp_out = nrrp_decide(
        pre_permission=aeg0.permission.value,
        stop_issued=aeg_final.stop_issued,
        retries_attempted=0,
        profile=profile,
    )

    effect_payload = {
        "sector": scenario.sector_label,
        "action": "SIMULATED_IRREVERSIBLE_ACTION",
        "execution_id": req.execution_id,
    }

    exec_out = sink(
        permission=aeg0.permission.value,
        stop_issued=aeg_final.stop_issued,
        terminal_stop=nrrp_out.terminal_stop,
        effect_payload=effect_payload,
    )

    ledger_dir = Path(output_root) / "ledger" / run_id
    rblock_id = str(uuid.uuid4())

    payload = {
        "rblock_id": rblock_id,
        "run_id": run_id,
        "scenario_id": scenario.scenario_id,
        "step_count": len(scenario.ube_vectors),
        "neuropause": np_out.model_dump(),
        "ube_initial": ube0.model_dump(),
        "aegixa": aeg_final.model_dump(),
        "nrrp": nrrp_out.model_dump(),
        "execution": exec_out.model_dump(),
    }

    rblock_hash, _ = write_rblock(
        ledger_dir=ledger_dir,
        rblock_payload=payload,
        previous_hash=GENESIS_HASH,
    )

    result = {
        "run_id": run_id,
        "scenario_id": scenario.scenario_id,
        "sector_label": scenario.sector_label,
        "permission": aeg0.permission.value,
        "stop_issued": aeg_final.stop_issued,
        "terminal_stop": nrrp_out.terminal_stop,
        "final_state": exec_out.final_state.value,
        "rblock_hash": rblock_hash,
        "ledger_dir": str(ledger_dir),
    }

    out_run_dir = Path(output_root) / "runs" / run_id
    out_run_dir.mkdir(parents=True, exist_ok=True)
    (out_run_dir / "run_result.json").write_text(str(result), encoding="utf-8")

    return result
