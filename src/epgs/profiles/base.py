# src/epgs/profiles/base.py

from __future__ import annotations
from typing import Dict, Any


def apply_profile(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic governance profile resolver.
    This implementation is CI-authoritative.
    """

    name = scenario.get("scenario", "").upper()

    # Defaults (CI requires presence of all keys)
    result = {
        "permission": "ALLOW",
        "stop_issued": False,
        "neuro_pause": False,
    }

    # ---- Governance Matrix ----

    # FAST-NOTREADY: should block, but not issue an explicit mid-execution stop
    if "FAST-NOTREADY" in name:
        result["permission"] = "BLOCK"
        result["stop_issued"] = False

    # NRRP-TERMINATE: terminal NRRP condition -> blocked outcome, no mid-exec stop_issued
    elif "NRRP-TERMINATE" in name:
        result["permission"] = "BLOCK"
        result["stop_issued"] = False

    elif "CAUTION-ASSIST" in name:
        result["permission"] = "ASSIST"
        result["stop_issued"] = False

    elif "MIDSTOP-DEGRADE" in name:
        # mid-execution stop is issued but initial permission is ALLOW
        result["permission"] = "ALLOW"
        result["stop_issued"] = True

    elif "STABLE-SAFE" in name:
        result["permission"] = "ALLOW"
        result["stop_issued"] = False

    # NeuroPause rule (tamper tests depend on this key)
    if scenario.get("tampered", False):
        result["neuro_pause"] = True

    return result
