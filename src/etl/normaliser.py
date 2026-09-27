"""
Data normalization utilities for Nifty100 ETL pipeline.
"""

import re


def normalize_year(value):
    """
    Convert financial year formats into integer year.

    Examples:
    FY 2023-24 -> 2024
    FY19-20 -> 2020
    2022 -> 2022
    """

    if value is None:
        return None

    value = str(value).strip()

    # Format: FY 2023-24 or 2023-24
    match = re.search(r"(\d{4})-(\d{2,4})", value)

    if match:
        end_year = match.group(2)

        if len(end_year) == 2:
            end_year = "20" + end_year

        return int(end_year)

    # Format: FY19-20
    match = re.search(r"(\d{2})-(\d{2})", value)

    if match:
        end_year = int(match.group(2))

        return 2000 + end_year

    # Normal year
    match = re.search(r"\d{4}", value)

    if match:
        return int(match.group())

    return None


def normalize_ticker(value):
    """
    Clean and standardize company ticker symbols.

    Examples:
    ' infy ' -> 'INFY'
    'tcs.nse' -> 'TCS'
    """

    if value is None:
        return None

    value = str(value).strip().upper()

    # Remove exchange suffix
    value = value.replace(".NSE", "")
    value = value.replace(".BSE", "")

    # Keep only letters/numbers
    value = re.sub(r"[^A-Z0-9]", "", value)

    return value