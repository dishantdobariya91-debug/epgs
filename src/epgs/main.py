from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

from epgs.orchestrator.run import run_scenario
from epgs.orchestrator.replay import verify_chain

app = FastAPI(
    title="EPGS – Execution Permission Gate Simulator",
    version="0.1.0",
)


class RunRequest(BaseModel):
    scenario_path: str
    output_root: Optional[str] = None


class VerifyRequest(BaseModel):
    ledger_dir: Optional[str] = None
    output_root: Optional[str] = None


def normalize_ledger_dir(
    ledger_dir: Optional[str],
    output_root: Optional[str],
) -> Path:
    if ledger_dir:
        p = Path(ledger_dir)

        if p.exists() and p.is_file() and p.suffix == ".json":
            return p.parent

        if p.exists() and p.is_dir():
            if list(p.glob("*.json")):
                return p
            ledger = p / "ledger"
            if ledger.exists():
                return ledger
            return p

        ledger = p / "ledger"
        if ledger.exists():
            return ledger

        return p

    if output_root:
        return Path(output_root) / "ledger"

    return Path(".")


@app.post("/run")
def run(req: RunRequest):
    return run_scenario(
        scenario_path=req.scenario_path,
        output_root=req.output_root or ".",
    )


@app.post("/verify")
def verify(req: VerifyRequest):
    ledger_path = normalize_ledger_dir(req.ledger_dir, req.output_root)
    return verify_chain(str(ledger_path))
