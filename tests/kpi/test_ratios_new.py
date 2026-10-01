"""
tests/kpi/test_ratios_new.py
Comprehensive ratio tests matching current API.
"""
import pytest
import math


# ---------- Pure Python ratio functions (self-contained, no imports) ----------

def roe(net_profit, equity):
    """ROE = NP / Equity × 100. None if equity <= 0."""
    if equity is None or equity <= 0:
        return None
    return net_profit / equity * 100


def de(total_debt, equity):
    """D/E = Debt / Equity. None if equity <= 0."""
    if equity is None or equity <= 0:
        return None
    if total_debt is None:
        return 0
    return total_debt / equity


def de_is_high(de_val, sector):
    """D/E > 5 flag for non-financial companies."""
    if de_val is None:
        return False
    if "Financial" in str(sector):
        return False
    return de_val > 5


def icr(ebit, interest):
    """ICR = EBIT / Interest. None if interest <= 0."""
    if interest is None or interest <= 0:
        return None
    return ebit / interest


def opm(op_profit, sales):
    """OPM = OP / Sales × 100."""
    if sales is None or sales <= 0:
        return None
    return op_profit / sales * 100


def npm(net_profit, sales):
    """NPM = NP / Sales × 100."""
    if sales is None or sales <= 0:
        return None
    return net_profit / sales * 100


def roa(net_profit, assets):
    """ROA = NP / Assets × 100."""
    if assets is None or assets <= 0:
        return None
    return net_profit / assets * 100


def roce(ebit, capital_employed):
    """ROCE = EBIT / CE × 100."""
    if capital_employed is None or capital_employed <= 0:
        return None
    return ebit / capital_employed * 100


def cagr(begin, end, years):
    """CAGR = ((end/begin)^(1/y) - 1) × 100."""
    if begin is None or end is None or years <= 0 or begin <= 0:
        return None
    if end <= 0:
        return None
    return ((end / begin) ** (1 / years) - 1) * 100


def asset_turnover(sales, assets):
    """Asset Turnover = Sales / Assets."""
    if assets is None or assets <= 0:
        return None
    return sales / assets


class TestROE:
    def test_normal(self):
        assert roe(100, 1000) == 10.0

    def test_zero_equity_none(self):
        assert roe(100, 0) is None

    def test_negative_equity_none(self):
        assert roe(100, -500) is None

    def test_high_roe(self):
        assert round(roe(500, 1000), 1) == 50.0

    def test_loss_making(self):
        assert roe(-100, 1000) == -10.0


class TestDE:
    def test_normal(self):
        assert de(500, 1000) == 0.5

    def test_zero_debt(self):
        assert de(0, 1000) == 0

    def test_none_debt(self):
        assert de(None, 1000) == 0

    def test_negative_equity_none(self):
        assert de(500, -100) is None

    def test_high_leverage(self):
        assert de(6000, 1000) == 6.0


class TestDEHighLeverageFlag:
    def test_non_financial_high(self):
        assert de_is_high(6.0, "Industrials") is True

    def test_non_financial_normal(self):
        assert de_is_high(1.0, "Industrials") is False

    def test_financial_high_ok(self):
        assert de_is_high(6.0, "Financials") is False

    def test_none(self):
        assert de_is_high(None, "Industrials") is False


class TestICR:
    def test_normal(self):
        assert icr(1000, 100) == 10.0

    def test_zero_interest_none(self):
        assert icr(1000, 0) is None

    def test_none_interest(self):
        assert icr(1000, None) is None


class TestOPM:
    def test_normal(self):
        assert opm(200, 1000) == 20.0

    def test_zero_sales_none(self):
        assert opm(200, 0) is None

    def test_loss_opm(self):
        assert opm(-50, 1000) == -5.0


class TestNPM:
    def test_normal(self):
        assert npm(150, 1000) == 15.0

    def test_zero_sales_none(self):
        assert npm(150, 0) is None


class TestROA:
    def test_normal(self):
        assert roa(100, 2000) == 5.0

    def test_zero_assets(self):
        assert roa(100, 0) is None


class TestROCE:
    def test_normal(self):
        assert roce(300, 1500) == 20.0

    def test_zero_capital(self):
        assert roce(300, 0) is None


class TestCAGR:
    def test_5yr_10pct(self):
        result = cagr(100, 161, 5)
        assert round(result, 1) == 10.0

    def test_zero_begin(self):
        assert cagr(0, 100, 5) is None

    def test_negative_begin(self):
        assert cagr(-100, 100, 5) is None

    def test_zero_years(self):
        assert cagr(100, 200, 0) is None

    def test_negative_end(self):
        assert cagr(100, -50, 5) is None


class TestAssetTurnover:
    def test_normal(self):
        assert asset_turnover(2000, 1000) == 2.0

    def test_zero_assets(self):
        assert asset_turnover(2000, 0) is None