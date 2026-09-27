"""
Financial Ratio Engine

Sprint 2 - Day 08

Implements profitability ratios used throughout the
N100 Financial Intelligence Platform.

Author: Your Name
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

def net_profit_margin(
    net_profit: float,
    sales: float
) -> Optional[float]:
    """
    Calculate Net Profit Margin.

    Formula:
        Net Profit / Sales × 100

    Returns
    -------
    float
        Percentage

    None
        When sales is zero.
    """

    if sales == 0:
        logger.warning("Sales is zero. Net Profit Margin cannot be computed.")
        return None

    return round((net_profit / sales) * 100, 2)

def operating_profit_margin(
    operating_profit: float,
    sales: float,
    reported_opm: Optional[float] = None,
    tolerance: float = 1.0
) -> tuple[Optional[float], bool]:
    """
    Calculate Operating Profit Margin.

    Returns
    -------
    (value, mismatch_flag)

    mismatch_flag=True when computed OPM differs
    from reported value by more than tolerance.
    """

    if sales == 0:
        logger.warning("Sales is zero. OPM cannot be calculated.")
        return None, False

    computed = round((operating_profit / sales) * 100, 2)

    mismatch = False

    if reported_opm is not None:
        if abs(computed - reported_opm) > tolerance:
            mismatch = True

            logger.warning(
                "OPM mismatch. "
                f"Computed={computed} "
                f"Reported={reported_opm}"
            )

    return computed, mismatch

def return_on_equity(
    net_profit: float,
    equity_capital: float,
    reserves: float
) -> Optional[float]:
    """
    ROE

    Formula

    Net Profit /
    (Equity Capital + Reserves)
    ×100
    """

    equity = equity_capital + reserves

    if equity <= 0:
        logger.warning("Negative or zero equity. ROE unavailable.")
        return None

    return round((net_profit / equity) * 100, 2)

def return_on_capital_employed(
    ebit: float,
    equity_capital: float,
    reserves: float,
    borrowings: float,
    broad_sector: str = ""
) -> tuple[Optional[float], Optional[str]]:
    """
    ROCE

    Returns

    (roce, benchmark)

    benchmark

    None
        Normal companies

    Sector Relative
        Financial sector
    """

    capital = equity_capital + reserves + borrowings

    if capital <= 0:
        logger.warning("Capital employed <=0.")
        return None, None

    roce = round((ebit / capital) * 100, 2)

    benchmark = None

    if broad_sector.lower() == "financials":
        benchmark = "Sector Relative"

    return roce, benchmark

def return_on_assets(
    net_profit: float,
    total_assets: float
) -> Optional[float]:
    """
    ROA

    Net Profit /
    Total Assets ×100
    """

    if total_assets == 0:
        logger.warning("Total assets zero.")
        return None

    return round((net_profit / total_assets) * 100, 2)

def debt_to_equity(
    borrowings: float,
    equity_capital: float,
    reserves: float,
    broad_sector: str = ""
) -> tuple[Optional[float], bool]:
    """
    Calculate Debt-to-Equity Ratio.

    Formula:
        Borrowings / (Equity Capital + Reserves)

    Returns
    -------
    tuple
        (de_ratio, high_leverage_flag)

    Rules
    -----
    - If borrowings == 0, return (0.0, False)
    - If equity <= 0, return (None, False)
    - high_leverage_flag=True when D/E > 5
    """

    if borrowings == 0:
        return 0.0, False

    equity = equity_capital + reserves

    if equity <= 0:
        logger.warning("Equity is zero or negative. D/E unavailable.")
        return None, False

    ratio = round(borrowings / equity, 2)

    high_leverage = (
    ratio > 5 and
    broad_sector.lower() != "financials"
    )

    return ratio, high_leverage

def interest_coverage(
    operating_profit: float,
    other_income: float,
    interest: float
) -> tuple[Optional[float], Optional[str], bool]:
    """
    Calculate Interest Coverage Ratio.

    Formula:
        (Operating Profit + Other Income) / Interest

    Returns
    -------
    tuple
        (icr, label, warning_flag)

    Rules
    -----
    - interest == 0
        -> (None, "Debt Free", False)

    - ICR < 1.5
        -> warning_flag=True
    """

    if interest == 0:
        return None, "Debt Free", False

    icr = round(
        (operating_profit + other_income) / interest,
        2
    )

    warning = icr < 1.5

    return icr, None, warning

def net_debt(
    borrowings: float,
    investments: float
) -> float:
    """
    Calculate Net Debt.

    Formula

    Borrowings - Investments
    """

    return round(
        borrowings - investments,
        2
    )
    
def asset_turnover(
    sales: float,
    total_assets: float
) -> Optional[float]:
    """
    Calculate Asset Turnover Ratio.

    Formula

    Sales / Total Assets
    """

    if total_assets == 0:
        logger.warning("Total assets zero.")
        return None

    return round(
        sales / total_assets,
        2
    )

# --------------------------------------------------------
# Return on Equity (ROE)
# --------------------------------------------------------

def return_on_equity(
    net_profit,
    total_assets,
    total_liabilities
):
    """
    ROE = Net Profit / Shareholder Equity

    Equity = Total Assets - Total Liabilities
    """

    if (
        net_profit is None
        or total_assets is None
        or total_liabilities is None
    ):
        return None

    equity = total_assets - total_liabilities

    if equity <= 0:
        return None

    return round(
        (net_profit / equity) * 100,
        2
    )


# --------------------------------------------------------
# Debt to Equity
# --------------------------------------------------------

def debt_to_equity(
    total_liabilities,
    total_assets
):
    """
    Debt to Equity ≈ Total Liabilities / Equity

    Equity = Total Assets - Total Liabilities
    """

    if (
        total_assets is None
        or total_liabilities is None
    ):
        return None

    equity = total_assets - total_liabilities

    if equity <= 0:
        return None

    return round(
        total_liabilities / equity,
        2
    )
     
if __name__ == "__main__":
    print(debt_to_equity(500, 200, 300))
    print(interest_coverage(1000, 100, 200))
    print(net_debt(1000, 250))
    print(asset_turnover(5000, 2500))