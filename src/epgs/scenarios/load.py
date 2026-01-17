from __future__ import annotations

import json
from pathlib import Path
from epgs.scenarios.schema import Scenario


def load_scenario(path: str | Path) -> Scenario:
    p = Path(path)
    raw = json.loads(p.read_text(encoding="utf-8"))
    return Scenario.model_validate(raw)
