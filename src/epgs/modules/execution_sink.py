from __future__ import annotations

from epgs.core.types import ExecutionSinkOut, ExecutionFinalState
from epgs.core.crypto import sha256_hex


def sink(
    permission: str,
    stop_issued: bool,
    terminal_stop: bool,
    effect_payload: dict,
) -> ExecutionSinkOut:
    effect_hash = sha256_hex(str(sorted(effect_payload.items())))

    if terminal_stop:
        return ExecutionSinkOut(
            executed=False,
            final_state=ExecutionFinalState.TERMINATED,
            reason_code="NRRP_TERMINAL_STOP",
            execution_effect_hash=effect_hash,
        )

    if stop_issued:
        return ExecutionSinkOut(
            executed=False,
            final_state=ExecutionFinalState.STOPPED,
            reason_code="AEGIXA_STOP",
            execution_effect_hash=effect_hash,
        )

    if permission in ("ALLOW", "ASSIST"):
        return ExecutionSinkOut(
            executed=True,
            final_state=ExecutionFinalState.EXECUTED,
            reason_code="PERMITTED",
            execution_effect_hash=effect_hash,
        )

    return ExecutionSinkOut(
        executed=False,
        final_state=ExecutionFinalState.BLOCKED,
        reason_code="BLOCKED",
        execution_effect_hash=effect_hash,
    )
