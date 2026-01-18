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
# Internal helper: normalize ledger path
# ------------------------------------------------------------
def normalize_ledger_dir(
    ledger_dir: Optional[str],
    output_root: Optional[str],
) -> Path:
    if ledger_dir:
        p = Path(ledger_dir)

        # rblock file → parent dir
        if p.exists() and p.is_file() and p.suffix == ".json":
            return p.parent

        # direct ledger dir
        if p.exists() and p.is_dir():
            if list(p.glob("*.json")):
                return p
            ledger = p / "ledger"
            if ledger.exists():
                return ledger
            return p

        # maybe output root was passed
        ledger = p / "ledger"
        if ledger.exists():
            return ledger

        return p

    if output_root:
        return Path(output_root) / "ledger"

    return Path(".")


# ------------------------------------------------------------
# API: run scenario
# ------------------------------------------------------------
@app.post("/run")
def run(req: RunRequest):
    if req.output_root is not None:
        return run_scenario(req.scenario_path, req.output_root)
    return run_scenario(req.scenario_path)


# ------------------------------------------------------------
# API: verify ledger  ✅ MUST BE GET
# ------------------------------------------------------------
@app.get("/verify")
def verify(
    ledger_dir: str = Query(..., description="Ledger directory"),
):
    ledger_path = normalize_ledger_dir(ledger_dir, None)
    return verify_chain(str(ledger_path))
