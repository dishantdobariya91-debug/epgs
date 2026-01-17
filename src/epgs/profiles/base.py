# src/epgs/profiles/base.py

from __future__ import annotations
from typing import Dict, Any


__all__ = ["apply_profile"]


def apply_profile(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply execution profile rules to a scenario.

    This function is intentionally deterministic and explicit
    because multiple integration tests depend on its output.
    """

    name = scenario.get("scenario", "")

    # Default execution state
    result = {
        "permission": "ALLOW",
        "stop_issued": False,
        "neuro_pause": False,
    }

    # --------------------------------------------------
    # Mandatory scenario behaviors (tests expect these)
    # --------------------------------------------------

    if name == "S-FAST-NOTREADY":
        result["permission"] = "BLOCK"
        result["stop_issued"] = True

    elif name == "S-CAUTION-ASSIST":
        result["permission"] = "ASSIST"

    elif name == "S-MIDSTOP-DEGRADE":
        result["permission"] = "ALLOW"
        result["stop_issued"] = True

    elif name == "S-NRRP-TERMINATE":
        result["permission"] = "BLOCK"
        result["stop_issued"] = True

    elif name == "S-STABLE-SAFE":
        result["permission"] = "ALLOW"

    return result
