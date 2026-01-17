from __future__ import annotations

from epgs.scenarios.schema import Scenario
from epgs.core.types import ExecutionRequest


def generate_requests(s: Scenario) -> list[ExecutionRequest]:
    # Deterministic: scenario already includes requests
    return list(s.requests)
