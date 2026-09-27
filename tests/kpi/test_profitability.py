import pytest

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    return_on_capital_employed,
    return_on_assets,
)

def test_net_profit_margin_normal():
    assert net_profit_margin(100, 1000) == 10.0

def test_net_profit_margin_zero_sales():
    assert net_profit_margin(100, 0) is None
    
def test_operating_profit_margin_normal():
    value, mismatch = operating_profit_margin(150, 1000)

    assert value == 15.0
    assert mismatch is False
    
def test_operating_profit_margin_mismatch():
    value, mismatch = operating_profit_margin(
        operating_profit=150,
        sales=1000,
        reported_opm=12.0
    )

    assert value == 15.0
    assert mismatch is True
    
def test_return_on_equity_normal():
    assert return_on_equity(
        net_profit=200,
        equity_capital=500,
        reserves=500
    ) == 20.0
    
def test_return_on_equity_negative_equity():
    assert return_on_equity(
        net_profit=100,
        equity_capital=-500,
        reserves=400
    ) is None
    
def test_return_on_capital_employed_normal():
    value, benchmark = return_on_capital_employed(
        ebit=300,
        equity_capital=500,
        reserves=500,
        borrowings=200
    )

    assert value == 25.0
    assert benchmark is None
    
def test_return_on_assets_zero_assets():
    assert return_on_assets(
        net_profit=100,
        total_assets=0
    ) is None
    
    