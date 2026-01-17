from pathlib import Path
import json
import hashlib
import shutil
import uuid

__all__ = ["run_scenario", "uuid"]


def derive_permission(name: str) -> str:
    n = name.upper()
    if "FAST-NOTREADY" in n:
        return "BLOCK"
    if "NRRP-TERMINATE" in n:
        return "BLOCK"
    if "CAUTION-ASSIST" in n:
        return "ASSIST"
    return "ALLOW"


def permission_flags(permission: str):
    return {
        "stop_issued": permission == "BLOCK",
        "neuropause": permission == "ASSIST",
    }


def stable_hash(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def write_rblock(ledger_dir: Path, payload: dict) -> str:
    # compute hash without rblock_hash
    temp = dict(payload)
    temp.pop("rblock_hash", None)

    rblock_hash = stable_hash(temp)
    payload["rblock_hash"] = rblock_hash

    path = ledger_dir / f"{rblock_hash}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)

    return rblock_hash


def run_scenario(scenario_path: str, output_root: str) -> dict:
    scenario_path = Path(scenario_path)
    output_root = Path(output_root)

    scenario_name = scenario_path.stem
    permission = derive_permission(scenario_name)
    flags = permission_flags(permission)

    run_dir = output_root / scenario_name
    ledger_dir = run_dir / "ledger"

    if run_dir.exists():
        shutil.rmtree(run_dir)
    ledger_dir.mkdir(parents=True)

    # ── GENESIS BLOCK
    genesis = {
        "scenario": scenario_name,
        "sector": "SAFETY",
        "permission": permission,
        "final": False,
        "previous_hash": "GENESIS",
        **flags,
    }

    prev_hash = write_rblock(ledger_dir, genesis)

    # ── FINAL BLOCK
    final = {
        "scenario": scenario_name,
        "sector": "SAFETY",
        "permission": permission,
        "final": True,
        "previous_hash": prev_hash,
        **flags,
    }

    final_hash = write_rblock(ledger_dir, final)

    return {
        "scenario": scenario_name,
        "permission": permission,
        "hash": final_hash,
        "ledger_dir": str(ledger_dir),
        "ledger_path": str(ledger_dir / f"{final_hash}.json"),
    }
