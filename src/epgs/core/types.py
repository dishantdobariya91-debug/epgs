from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Optional


class StabilityClass(str, Enum):
    SAFE = "SAFE"
    CAUTION = "CAUTION"
    UNSAFE = "UNSAFE"


class Permission(str, Enum):
    ALLOW = "ALLOW"
    ASSIST = "ASSIST"
    BLOCK = "BLOCK"


class Readiness(str, Enum):
    READY = "READY"
    NOT_READY = "NOT_READY"


class FailureClass(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ExecutionFinalState(str, Enum):
    EXECUTED = "EXECUTED"
    BLOCKED = "BLOCKED"
    STOPPED = "STOPPED"
    TERMINATED = "TERMINATED"


class ExecutionRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    execution_id: str
    action_type: Literal["IRREVERSIBLE"] = "IRREVERSIBLE"
    sector_label: Literal["ENERGY", "AEROSPACE_DEFENSE", "MOBILITY", "ROBOTICS"]
    requested_at_ms: int = Field(ge=0)


class NeuroPauseOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    readiness: Readiness
    tau_ms_required: int = 330
    tau_ms_observed: int = Field(ge=0)
    resets: int = Field(ge=0)


class UBEOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    phi: float = Field(ge=0.0, le=1.0)
    degradation_rate: float = Field(ge=0.0)
    risk_load: float = Field(ge=0.0)
    stability_class: StabilityClass
    invariant_violation: bool = False


class AegixaOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    permission: Permission
    stop_issued: bool
    stop_reason_code: Optional[str] = None
    stop_step_index: Optional[int] = None


class NRRPOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    retries_attempted: int = Field(ge=0)
    retry_allowed: bool
    terminal_stop: bool
    failure_class: FailureClass


class ExecutionSinkOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    executed: bool
    final_state: ExecutionFinalState
    reason_code: str
    execution_effect_hash: str
