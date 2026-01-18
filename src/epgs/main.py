from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query
from pydantic import BaseModel

from epgs.orchestrator.run import run_scenario
from epgs.orchestrator.replay import verify_chain

app = FastAPI(
    title="EPGS – Execution Permission Gate Simulator",
    version="0.1.0",
)


# ------------------------------------------------------------
# Models
# ------------------------------------------------------------
class RunRequest(BaseModel):
    scenario_path: str
    output_root: Optional[str] = None


# ------------------------------------------------------------
# Ledger normalization (CI-FINAL)
# ------------------------------------------------------------
def normalize_ledger_dir(ledger_dir: str) -> Path:
    p = Path(ledger_dir)

    # ✅ ABSOLUTE RULE: if <path>/ledger exists, use it
    ledger = p / "ledger"
    if ledger.exists() and ledger.is_dir():
        return ledger

    # rblock file → parent
    if p.exists() and p.is_file() and p.suffix == ".json":
        return p.parent

    # direct ledger dir
    if p.exists() and p.is_dir():
        return p

    return p  # verify_chain will fail cleanly if invalid


# ------------------------------------------------------------
# API: run scenario
# ------------------------------------------------------------
@app.post("/run")
def run(req: RunRequest):
    if req.output_root is not None:
        return run_scenario(req.scenario_path, req.output_root)
    return run_scenario(req.scenario_path)


# ------------------------------------------------------------
# API: verify ledger (GET — REQUIRED BY TESTS)
# ------------------------------------------------------------
@app.get("/verify")
def verify(
    ledger_dir: str = Query(..., description="Ledger directory"),
):
    ledger_path = normalize_ledger_dir(ledger_dir)
    return verify_chain(str(ledger_path))
