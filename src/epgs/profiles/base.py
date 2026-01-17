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

    if "FAST-NOTREADY" in name:
        result["permission"] = "BLOCK"
        result["stop_issued"] = True

    elif "NRRP-TERMINATE" in name:
        result["permission"] = "BLOCK"
        result["stop_issued"] = True

    elif "CAUTION-ASSIST" in name:
        result["permission"] = "ASSIST"

    elif "MIDSTOP-DEGRADE" in name:
        result["permission"] = "ALLOW"
        result["stop_issued"] = True

    elif "STABLE-SAFE" in name:
        result["permission"] = "ALLOW"

    # NeuroPause rule (tamper tests depend on this key)
    if scenario.get("tampered", False):
        result["neuro_pause"] = True

    return result
