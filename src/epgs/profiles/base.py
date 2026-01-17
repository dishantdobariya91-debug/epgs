from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict


class BaseProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    # Retry policy
    max_retries: int = Field(default=0, ge=0)

    # Aegixa gating thresholds (prototype-level, conservative)
    phi_min_safe: float = 0.75
    risk_load_max_safe: float = 0.30
    degradation_max_safe: float = 0.05
