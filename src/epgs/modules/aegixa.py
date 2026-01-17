from __future__ import annotations

from epgs.core.types import (
    AegixaOut,
    Permission,
    Readiness,
    StabilityClass,
    NeuroPauseOut,
    UBEOut,
)


def precheck(np: NeuroPauseOut, ube: UBEOut) -> AegixaOut:
    if np.readiness != Readiness.READY:
        return AegixaOut(
            permission=Permission.BLOCK,
            stop_issued=False,
            stop_reason_code="NP_NOT_READY",
        )

    if ube.stability_class == StabilityClass.UNSAFE or ube.invariant_violation:
        return AegixaOut(
            permission=Permission.BLOCK,
            stop_issued=False,
            stop_reason_code="UBE_UNSAFE",
        )

    if ube.stability_class == StabilityClass.CAUTION:
        return AegixaOut(permission=Permission.ASSIST, stop_issued=False)

    return AegixaOut(permission=Permission.ALLOW, stop_issued=False)


def mid_execution_monitor(step_index: int, ube: UBEOut) -> AegixaOut | None:
    if ube.stability_class == StabilityClass.UNSAFE or ube.invariant_violation:
        return AegixaOut(
            permission=Permission.BLOCK,
            stop_issued=True,
            stop_reason_code="MID_EXEC_UNSAFE",
            stop_step_index=step_index,
        )
    return None
