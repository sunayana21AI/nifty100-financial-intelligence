"""
Unit tests for normaliser functions.
"""

from src.etl.normaliser import normalize_year, normalize_ticker


# -----------------------------
# normalize_year tests
# -----------------------------

def test_year_fy_format():
    assert normalize_year("FY 2023-24") == 2024


def test_year_normal():
    assert normalize_year("2022") == 2022


def test_year_decimal():
    assert normalize_year("2023.0") == 2023


def test_year_with_text():
    assert normalize_year("Year 2021") == 2021


def test_year_none():
    assert normalize_year(None) is None


def test_year_empty():
    assert normalize_year("") is None


def test_year_long_fy():
    assert normalize_year("FY2020-2021") == 2021


def test_year_spaces():
    assert normalize_year(" FY 2024-25 ") == 2025


# -----------------------------
# normalize_ticker tests
# -----------------------------

def test_ticker_lowercase():
    assert normalize_ticker("infy") == "INFY"


def test_ticker_spaces():
    assert normalize_ticker(" tcs ") == "TCS"


def test_ticker_nse():
    assert normalize_ticker("INFY.NSE") == "INFY"


def test_ticker_bse():
    assert normalize_ticker("TCS.BSE") == "TCS"


def test_ticker_special():
    assert normalize_ticker("HDFC@") == "HDFC"


def test_ticker_none():
    assert normalize_ticker(None) is None


def test_ticker_numbers():
    assert normalize_ticker("ABC123") == "ABC123"
    
# -----------------------------
# More normalize_year tests
# -----------------------------

def test_year_fy_lowercase():
    assert normalize_year("fy 2021-22") == 2022


def test_year_only_number():
    assert normalize_year(2025) == 2025


def test_year_float():
    assert normalize_year(2024.0) == 2024


def test_year_with_month():
    assert normalize_year("March 2023") == 2023


def test_year_invalid_text():
    assert normalize_year("abcd") is None


def test_year_none_value():
    assert normalize_year(None) is None


def test_year_extra_spaces():
    assert normalize_year("   FY 2022-23   ") == 2023


def test_year_financial_format():
    assert normalize_year("FY19-20") == 2020


def test_year_slash_format():
    assert normalize_year("2023/24") == 2023


def test_year_multiple_text():
    assert normalize_year("Financial Year 2020") == 2020


# -----------------------------
# More normalize_ticker tests
# -----------------------------

def test_ticker_lower_with_spaces():
    assert normalize_ticker(" reliance ") == "RELIANCE"


def test_ticker_nse_lower():
    assert normalize_ticker("tcs.nse") == "TCS"


def test_ticker_bse_lower():
    assert normalize_ticker("infy.bse") == "INFY"


def test_ticker_dash():
    assert normalize_ticker("M&M") == "MM"


def test_ticker_dot():
    assert normalize_ticker("L&T") == "LT"


def test_ticker_empty():
    assert normalize_ticker("") == ""


def test_ticker_special_symbols():
    assert normalize_ticker("@HDFC#") == "HDFC"


def test_ticker_numeric_string():
    assert normalize_ticker("123") == "123"


def test_ticker_mixed_case():
    assert normalize_ticker("BaNk") == "BANK"


def test_ticker_none_again():
    assert normalize_ticker(None) is None