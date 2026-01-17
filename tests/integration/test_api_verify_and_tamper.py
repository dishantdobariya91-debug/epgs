import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from epgs.main import app
import epgs.main as main_module  # for monkeypatching run_scenario


SCENARIOS = [
    "src/epgs/scenarios/S-STABLE-SAFE.json",
    "src/epgs/scenarios/S-FAST-NOTREADY.json",
    "src/epgs/scenarios/S-CAUTION-ASSIST.json",
    "src/epgs/scenarios/S-MIDSTOP-DEGRADE.json",
    "src/epgs/scenarios/S-NRRP-TERMINATE.json",
]


def make_client():
    """
    Correct sync test client for FastAPI.
    No ASGITransport, no async, no context manager required.
    """
    return TestClient(app)


def _monkeypatch_run_to_tmp(monkeypatch, tmp_path: Path):
    """
    Patch epgs.main.run_scenario so /run writes into tmp_path
    instead of real output/ directory.
    """
    from epgs.orchestrator.run import run_scenario as real_run_scenario

    def _run_to_tmp(scenario_path: str):
        return real_run_scenario(
            scenario_path=scenario_path,
            output_root=str(tmp_path),
        )

    monkeypatch.setattr(main_module, "run_scenario", _run_to_tmp)


def _run_via_api(client: TestClient, scenario_path: str) -> dict:
    r = client.post("/run", json={"scenario_path": scenario_path})
    assert r.status_code == 200, r.text
    return r.json()


def _verify_via_api(client: TestClient, ledger_dir: str) -> dict:
    r = client.get("/verify", params={"ledger_dir": ledger_dir})
    assert r.status_code == 200, r.text
    return r.json()


def test_verify_endpoint_passes_for_each_scenario(monkeypatch, tmp_path):
    _monkeypatch_run_to_tmp(monkeypatch, tmp_path)

    client = make_client()

    for scenario in SCENARIOS:
        result = _run_via_api(client, scenario)
        assert "ledger_dir" in result

        verification = _verify_via_api(client, result["ledger_dir"])
        assert verification["ok"] is True


def test_tamper_rblock_causes_verify_to_fail(monkeypatch, tmp_path):
    _monkeypatch_run_to_tmp(monkeypatch, tmp_path)

    client = make_client()

    # Run a clean scenario
    result = _run_via_api(client, "src/epgs/scenarios/S-STABLE-SAFE.json")
    ledger_dir = Path(result["ledger_dir"])
    assert ledger_dir.exists()

    # Find first R-Block
    rblock_files = sorted(ledger_dir.glob("*.json"))
    assert rblock_files, "No R-Block files found"

    target = rblock_files[0]

    # Load and tamper
    rb = json.loads(target.read_text(encoding="utf-8"))
    rb["neuropause"]["tau_ms_observed"] += 1  # intentional corruption

    target.write_text(
        json.dumps(rb, sort_keys=True, separators=(",", ":"), ensure_ascii=True),
        encoding="utf-8",
    )

    # Verification must fail
    verification = _verify_via_api(client, str(ledger_dir))
    assert verification["ok"] is False
    assert (
        "hash mismatch" in verification.get("reason", "")
        or "previous_hash mismatch" in verification.get("reason", "")
    )
