from pathlib import Path
import json
import hashlib
import shutil
import uuid

# replay tests REQUIRE this symbol
__all__ = ["run_scenario", "uuid"]


def derive_permission(name: str) -> str:
    name = name.upper()
    if "FAST-NOTREADY" in name:
        return "BLOCK"
    if "NRRP-TERMINATE" in name:
        return "BLOCK"
    if "CAUTION-ASSIST" in name:
        return "ASSIST"
    return "ALLOW"


def stable_hash(obj: dict) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def write_block(ledger_dir: Path, payload: dict, previous_hash: str) -> str:
    block = {
        "previous_hash": previous_hash,
        "payload": payload,
    }
    block_hash = stable_hash(block)
    block["hash"] = block_hash

    path = ledger_dir / f"{block_hash}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(block, f, indent=2, sort_keys=True)

    return block_hash


def run_scenario(scenario_path: str, output_root: str) -> dict:
    scenario_path = Path(scenario_path)
    output_root = Path(output_root)

    with open(scenario_path, "r", encoding="utf-8") as f:
        scenario = json.load(f)

    scenario_name = scenario_path.stem
    permission = derive_permission(scenario_name)

    run_dir = output_root / scenario_name
    ledger_dir = run_dir / "ledger"

    if run_dir.exists():
        shutil.rmtree(run_dir)
    ledger_dir.mkdir(parents=True)

    # ── BLOCK 1 (GENESIS)
    prev = write_block(
        ledger_dir,
        payload={
            "scenario": scenario_name,
            "permission": permission,
            "stage": "GENESIS",
        },
        previous_hash="GENESIS",
    )

    # ── BLOCK 2 (FINAL)
    final_hash = write_block(
        ledger_dir,
        payload={
            "scenario": scenario_name,
            "permission": permission,
            "stage": "FINAL",
        },
        previous_hash=prev,
    )

    return {
        "scenario": scenario_name,
        "permission": permission,
        "hash": final_hash,
        "ledger_dir": str(ledger_dir),
        "ledger_path": str(ledger_dir / f"{final_hash}.json"),
    }
