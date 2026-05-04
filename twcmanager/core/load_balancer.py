from __future__ import annotations


def compute_allowed_amps(
    main_fuse_amps: float,
    household_grid_amps: float,
    current_charging_amps: float,
    min_amps_per_twc: float,
    wiring_max_amps_all_twcs: float,
    safety_margin_amps: float = 2.0,
) -> float:
    """Compute max amps we can offer charging without exceeding main fuse.

    household_grid_amps is measured total import current from grid.
    To estimate non-EV household load we subtract current charging amps.
    """
    non_ev_load_amps = max(0.0, household_grid_amps - current_charging_amps)
    headroom = main_fuse_amps - non_ev_load_amps - safety_margin_amps
    allowed = min(wiring_max_amps_all_twcs, max(0.0, headroom))

    # Preserve legacy behavior: if below min threshold, offer 0A to stop charging.
    if 0 < allowed < min_amps_per_twc:
        return 0.0
    return float(int(allowed))
