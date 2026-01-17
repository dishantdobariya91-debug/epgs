from __future__ import annotations

from epgs.core.types import NRRPOut, FailureClass
from epgs.profiles.base import BaseProfile


def decide(
    pre_permission: str,
    stop_issued: bool,
    retries_attempted: int,
    profile: BaseProfile,
) -> NRRPOut:
    # Fail-closed posture
    if stop_issued:
        return NRRPOut(
            retries_attempted=retries_attempted,
            retry_allowed=False,
            terminal_stop=True,
            failure_class=FailureClass.HIGH,
        )

    if pre_permission == "BLOCK":
        if retries_attempted < profile.max_retries:
            return NRRPOut(
                retries_attempted=retries_attempted,
                retry_allowed=True,
                terminal_stop=False,
                failure_class=FailureClass.MEDIUM,
            )

        return NRRPOut(
            retries_attempted=retries_attempted,
            retry_allowed=False,
            terminal_stop=True,
            failure_class=FailureClass.HIGH,
        )

    return NRRPOut(
        retries_attempted=retries_attempted,
        retry_allowed=False,
        terminal_stop=False,
        failure_class=FailureClass.LOW,
    )
