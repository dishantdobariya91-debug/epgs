from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from epgs.orchestrator.run import run_scenario
from epgs.orchestrator.replay import verify_chain

app = FastAPI(
    title="EPGS - Execution Permission Gate Simulator",
    version="0.1.0",
)


class RunRequest(BaseModel):
    scenario_path: str


@app.post("/run")
def run(req: RunRequest):
    return run_scenario(req.scenario_path)


@app.get("/verify")
def verify(ledger_dir: str):
    return verify_chain(ledger_dir)
