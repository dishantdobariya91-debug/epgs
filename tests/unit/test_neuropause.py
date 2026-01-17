from epgs.modules.neuropause import evaluate_temporal
from epgs.scenarios.schema import TemporalSignal
from epgs.core.types import Readiness


def test_tau_resets_on_jitter():
    temporal = [
        TemporalSignal(step_index=0, stable_ms=200, jitter=False),
        TemporalSignal(step_index=1, stable_ms=50, jitter=True),
        TemporalSignal(step_index=2, stable_ms=200, jitter=False),
    ]
    out = evaluate_temporal(temporal)
    assert out.readiness == Readiness.NOT_READY
    assert out.resets == 1
