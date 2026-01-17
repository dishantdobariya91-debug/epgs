from __future__ import annotations

from epgs.core.types import UBEOut, StabilityClass
from epgs.scenarios.schema import UBEStepVector
from epgs.profiles.base import BaseProfile


def classify(v: UBEStepVector, p: BaseProfile) -> UBEOut:
    invariant_violation = False

    if not (0.0 <= v.phi <= 1.0):
        invariant_violation = True
    if v.degradation_rate < 0.0 or v.risk_load < 0.0:
        invariant_violation = True

    if invariant_violation:
        return UBEOut(
            phi=max(0.0, min(1.0, v.phi)),
            degradation_rate=max(0.0, v.degradation_rate),
            risk_load=max(0.0, v.risk_load),
            stability_class=StabilityClass.UNSAFE,
            invariant_violation=True,
        )

    if (
        v.phi >= p.phi_min_safe
        and v.risk_load <= p.risk_load_max_safe
        and v.degradation_rate <= p.degradation_max_safe
    ):
        sc = StabilityClass.SAFE
    elif v.phi >= (p.phi_min_safe - 0.10):
        sc = StabilityClass.CAUTION
    else:
        sc = StabilityClass.UNSAFE

    return UBEOut(
        phi=v.phi,
        degradation_rate=v.degradation_rate,
        risk_load=v.risk_load,
        stability_class=sc,
        invariant_violation=False,
    )
