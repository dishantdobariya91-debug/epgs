from __future__ import annotations

from epgs.core.types import NeuroPauseOut, Readiness
from epgs.scenarios.schema import TemporalSignal

TAU_MS = 330


def evaluate_temporal(temporal: list[TemporalSignal]) -> NeuroPauseOut:
    observed = 0
    resets = 0

    # Deterministic accumulation across ordered steps
    for t in sorted(temporal, key=lambda x: x.step_index):
        if t.jitter:
            resets += 1
            observed = 0
        observed += t.stable_ms
        if observed >= TAU_MS:
            return NeuroPauseOut(
                readiness=Readiness.READY,
                tau_ms_required=TAU_MS,
                tau_ms_observed=observed,
                resets=resets,
            )

    return NeuroPauseOut(
        readiness=Readiness.NOT_READY,
        tau_ms_required=TAU_MS,
        tau_ms_observed=observed,
        resets=resets,
    )
