from __future__ import annotations

from dataclasses import dataclass
import time


@dataclass
class OfferPolicyState:
    last_offered_amps: float = 0.0
    last_change_ts: float = 0.0


def enforce_offer_policy(
    desired_amps: float,
    min_amps_per_twc: float,
    state: OfferPolicyState,
    now: float | None = None,
    min_on_off_interval_s: float = 60.0,
) -> float:
    """Apply basic anti-flap semantics inspired by legacy behavior.

    - If desired is between 0 and minimum, force 0.
    - Once set to 0, keep it off for at least min_on_off_interval_s.
    - Once turned on (>0), keep it on for at least min_on_off_interval_s unless desired remains >0.
    """
    t = now if now is not None else time.time()

    if 0 < desired_amps < min_amps_per_twc:
        desired_amps = 0.0

    # Prevent fast off->on toggling.
    if state.last_offered_amps == 0.0 and desired_amps > 0:
        if t - state.last_change_ts < min_on_off_interval_s:
            return 0.0

    # Prevent fast on->off toggling.
    if state.last_offered_amps > 0 and desired_amps == 0.0:
        if t - state.last_change_ts < min_on_off_interval_s:
            return state.last_offered_amps

    if desired_amps != state.last_offered_amps:
        state.last_change_ts = t
        state.last_offered_amps = desired_amps

    return desired_amps
