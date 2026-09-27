from src.analytics.cashflow_kpis import (
    free_cash_flow,
    cfo_quality_score,
    capex_intensity,
    fcf_conversion,
    capital_allocation_classifier,
)


def test_free_cash_flow():
    assert free_cash_flow(1000, -300) == 700


def test_cfo_quality_high():
    score, label = cfo_quality_score(
        [100, 120, 130],
        [90, 100, 110]
    )

    assert score == 1.16
    assert label == "High Quality"


def test_cfo_quality_moderate():
    score, label = cfo_quality_score(
        [60, 70],
        [100, 100]
    )

    assert score == 0.65
    assert label == "Moderate"


def test_cfo_quality_accrual():
    score, label = cfo_quality_score(
        [20, 30],
        [100, 100]
    )

    assert score == 0.25
    assert label == "Accrual Risk"


def test_cfo_quality_none():
    score, label = cfo_quality_score(
        [100],
        [0]
    )

    assert score is None
    assert label is None


def test_capex_intensity_asset_light():
    value, label = capex_intensity(-100, 10000)

    assert value == 1.0
    assert label == "Asset Light"


def test_capex_intensity_moderate():
    value, label = capex_intensity(-500, 10000)

    assert value == 5.0
    assert label == "Moderate"


def test_capex_intensity_capital_intensive():
    value, label = capex_intensity(-1200, 10000)

    assert value == 12.0
    assert label == "Capital Intensive"


def test_fcf_conversion():
    assert fcf_conversion(700, 1000) == 70.0


def test_fcf_conversion_zero():
    assert fcf_conversion(700, 0) is None


def test_capital_allocation_reinvestor():
    assert (
        capital_allocation_classifier(
            1000,
            -500,
            -200
        )
        == "Reinvestor"
    )


def test_capital_allocation_shareholder_returns():
    assert (
        capital_allocation_classifier(
            1000,
            -500,
            -200,
            cfo_pat_ratio=1.3
        )
        == "Shareholder Returns"
    )


def test_capital_allocation_distress():
    assert (
        capital_allocation_classifier(
            -500,
            100,
            200
        )
        == "Distress Signal"
    )