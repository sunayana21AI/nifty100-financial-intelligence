"""
Unit tests for data quality validator.
"""

from src.etl.validator import DataValidator


def test_pk_unique_failure():

    validator = DataValidator()

    data = {
        "id": [1, 2, 2]
    }

    import pandas as pd

    df = pd.DataFrame(data)

    validator.check_pk_unique(
        df,
        "id",
        "companies"
    )

    assert len(validator.failures) == 1
    assert validator.failures[0]["rule_id"] == "DQ-01"



def test_positive_sales_failure():

    validator = DataValidator()

    import pandas as pd

    df = pd.DataFrame(
        {
            "sales":[100,-50,200]
        }
    )

    validator.check_positive_sales(
        df,
        "sales",
        "profitandloss"
    )

    assert len(validator.failures) == 1
    assert validator.failures[0]["rule_id"] == "DQ-06"



def test_company_year_duplicate():

    validator = DataValidator()

    import pandas as pd

    df = pd.DataFrame(
        {
            "company_id":[1,1],
            "year":[2024,2024]
        }
    )


    validator.check_duplicate_company_year(
        df,
        ["company_id","year"],
        "profitandloss"
    )


    assert validator.failures[0]["rule_id"] == "DQ-02"



def test_url_validation():

    validator = DataValidator()


    validator.check_url(
        "google.com",
        "documents"
    )


    assert validator.failures[0]["rule_id"] == "DQ-11"



def test_missing_ticker():

    validator = DataValidator()


    validator.check_ticker(
        "",
        "companies"
    )


    assert validator.failures[0]["rule_id"] == "DQ-14"



def test_export_csv(tmp_path):

    validator = DataValidator()

    validator.add_failure(
        "DQ-01",
        "companies",
        "duplicate key",
        "CRITICAL"
    )


    file = tmp_path / "validation_failures.csv"


    validator.export_failures(file)


    assert file.exists()