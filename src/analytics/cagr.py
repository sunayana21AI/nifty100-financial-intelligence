"""
CAGR Engine

Sprint 2 - Day 10

Computes CAGR for Revenue, PAT and EPS with
all required edge-case handling.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

def calculate_cagr(
    start_value: float,
    end_value: float,
    years: int
) -> tuple[Optional[float], str]:
    """
    Calculate CAGR.

    Returns
    -------
    (cagr, flag)

    Flags
    -----
    OK
    DECLINE_TO_LOSS
    TURNAROUND
    BOTH_NEGATIVE
    ZERO_BASE
    INSUFFICIENT
    """

    if years <= 0:
        return None, "INSUFFICIENT"

    if start_value == 0:
        return None, "ZERO_BASE"

    if start_value > 0 and end_value < 0:
        return None, "DECLINE_TO_LOSS"

    if start_value < 0 and end_value > 0:
        return None, "TURNAROUND"

    if start_value < 0 and end_value < 0:
        return None, "BOTH_NEGATIVE"

    cagr = (
        ((end_value / start_value) ** (1 / years) - 1)
        * 100
    )

    return round(cagr, 2), "OK"

def revenue_cagr(
    start_revenue: float,
    end_revenue: float,
    years: int
):
    """
    Revenue CAGR
    """
    return calculate_cagr(
        start_revenue,
        end_revenue,
        years
    )

def pat_cagr(
    start_pat: float,
    end_pat: float,
    years: int
):
    """
    PAT CAGR
    """
    return calculate_cagr(
        start_pat,
        end_pat,
        years
    )

def eps_cagr(
    start_eps: float,
    end_eps: float,
    years: int
):
    """
    EPS CAGR
    """
    return calculate_cagr(
        start_eps,
        end_eps,
        years
    )
    
if __name__ == "__main__":
    print(calculate_cagr(100, 200, 5))
    print(calculate_cagr(100, -50, 5))
    print(calculate_cagr(-50, 100, 5))
    print(calculate_cagr(-50, -100, 5))
    print(calculate_cagr(0, 100, 5))