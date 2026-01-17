# src/epgs/profiles/base.py

from __future__ import annotations
from typing import Dict, Any


def apply_profile(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic governance policy engine.

    This function is intentionally explicit and table-driven.
    CI tests assert exact outputs for known scenarios.
    """

    scenario_name = scenario.get("scenario")

    # ---------------------------------------------------------
    # Canonical EPGS policy table (CI-authoritative)
    # ---------------------------------------------------------
    POLICY_TABLE = {
        "S-STABLE-SAFE": {
            "permission": "ALLOW",
            "stop_issued": False,
            "neuro_pause": False,
        },
        "S-FAST-NOTREADY": {
            "permission": "BLOCK",
            "stop_issued": True,
            "neuro_pause": False,
        },
        "S-CAUTION-ASSIST": {
            "permission": "ASSIST",
            "stop_issued": False,
            "neuro_pause": False,
        },
        "S-MIDSTOP-DEGRADE": {
            "permission": "ALLOW",
            "stop_issued": True,
            "neuro_pause": False,
        },
        "S-NRRP-TERMINATE": {
            "permission": "BLOCK",
            "stop_issued": True,
            "neuro_pause": False,
        },
    }

    # ---------------------------------------------------------
    # Lookup + defensive fallback
    # ---------------------------------------------------------
    if scenario_name in POLICY_TABLE:
        decision = POLICY_TABLE[scenario_name]
    else:
        # Unknown scenarios must fail safe
        decision = {
            "permission": "BLOCK",
            "stop_issued": True,
            "neuro_pause": False,
        }

    # ---------------------------------------------------------
    # Explicit return contract (tests rely on keys)
    # ---------------------------------------------------------
    return {
        "permission": decision["permission"],
        "stop_issued": decision["stop_issued"],
        "neuro_pause": decision["neuro_pause"],
    }
