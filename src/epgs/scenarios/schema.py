from __future__ import annotations

from typing import List, Literal
from pydantic import BaseModel, Field, ConfigDict
from epgs.core.types import ExecutionRequest


class TemporalSignal(BaseModel):
    model_config = ConfigDict(frozen=True)

    step_index: int = Field(ge=0)
    stable_ms: int = Field(ge=0)
    jitter: bool


class UBEStepVector(BaseModel):
    model_config = ConfigDict(frozen=True)

    step_index: int = Field(ge=0)
    phi: float = Field(ge=0.0, le=1.0)
    degradation_rate: float = Field(ge=0.0)
    risk_load: float = Field(ge=0.0)


class Scenario(BaseModel):
    model_config = ConfigDict(frozen=True)

    scenario_id: str
    sector_label: Literal["ENERGY", "AEROSPACE_DEFENSE", "MOBILITY", "ROBOTICS"]
    requests: List[ExecutionRequest]
    temporal: List[TemporalSignal]
    ube_vectors: List[UBEStepVector]
