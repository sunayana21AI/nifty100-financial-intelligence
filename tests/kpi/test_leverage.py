from src.analytics.ratios import (
    debt_to_equity,
    interest_coverage,
    net_debt,
    asset_turnover,
)


def test_debt_to_equity_normal():
    ratio, flag = debt_to_equity(500, 200, 300)

    assert ratio == 1.0
    assert flag is False


def test_debt_to_equity_debt_free():
    ratio, flag = debt_to_equity(0, 500, 500)

    assert ratio == 0.0
    assert flag is False


def test_debt_to_equity_negative_equity():
    ratio, flag = debt_to_equity(500, -200, 100)

    assert ratio is None
    assert flag is False


def test_debt_to_equity_high_leverage():
    ratio, flag = debt_to_equity(7000, 500, 500)

    assert ratio == 7.0
    assert flag is True


def test_debt_to_equity_financials():
    ratio, flag = debt_to_equity(
        7000,
        500,
        500,
        broad_sector="Financials"
    )

    assert ratio == 7.0
    assert flag is False


def test_interest_coverage_normal():
    icr, label, warning = interest_coverage(
        1000,
        100,
        200
    )

    assert icr == 5.5
    assert label is None
    assert warning is False


def test_interest_coverage_debt_free():
    icr, label, warning = interest_coverage(
        1000,
        100,
        0
    )

    assert icr is None
    assert label == "Debt Free"
    assert warning is False


def test_interest_coverage_warning():
    icr, label, warning = interest_coverage(
        100,
        0,
        100
    )

    assert icr == 1.0
    assert warning is True


def test_net_debt():
    assert net_debt(1000, 250) == 750


def test_asset_turnover():
    assert asset_turnover(5000, 2500) == 2.0


def test_asset_turnover_zero_assets():
    assert asset_turnover(1000, 0) is None