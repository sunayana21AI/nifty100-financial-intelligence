"""
Data Quality Validator for Nifty100 ETL pipeline.
"""

import pandas as pd


class DataValidator:
    """
    Runs DQ checks on financial datasets.
    """

    def __init__(self):
        self.failures = []


    def add_failure(self, rule_id, table, message, severity):
        self.failures.append(
            {
                "rule_id": rule_id,
                "table": table,
                "message": message,
                "severity": severity
            }
        )


    def export_failures(self, path):
        df = pd.DataFrame(self.failures)

        df.to_csv(
            path,
            index=False
        )


    # DQ-01 Primary Key
    def check_pk_unique(self, df, column, table):

        duplicates = df[column].duplicated().sum()

        if duplicates > 0:
            self.add_failure(
                "DQ-01",
                table,
                f"{duplicates} duplicate primary keys found",
                "CRITICAL"
            )


    # DQ-02 Company Year
    def check_duplicate_company_year(self, df, columns, table):

        duplicates = df.duplicated(
            subset=columns
        ).sum()

        if duplicates > 0:
            self.add_failure(
                "DQ-02",
                table,
                f"{duplicates} duplicate company-year records found",
                "CRITICAL"
            )


    # DQ-03 Foreign Key
    def check_foreign_key(self, child_df, parent_df, column, table):

        missing = (
            ~child_df[column].isin(parent_df[column])
        ).sum()

        if missing > 0:
            self.add_failure(
                "DQ-03",
                table,
                f"{missing} missing foreign keys",
                "CRITICAL"
            )


    # DQ-04 Balance Sheet
    def check_balance_sheet(self, assets, liabilities, table):

        difference = abs(assets - liabilities)

        if difference > abs(assets * 0.01):

            self.add_failure(
                "DQ-04",
                table,
                "Balance sheet mismatch >1%",
                "WARNING"
            )


    # DQ-05 OPM
    def check_opm(self, sales, operating_profit, reported_opm, table):

        calculated = (
            operating_profit / sales
        ) * 100

        if abs(calculated - reported_opm) > 1:

            self.add_failure(
                "DQ-05",
                table,
                "OPM mismatch",
                "WARNING"
            )


    # DQ-06 Sales Positive
    def check_positive_sales(self, df, column, table):

        invalid = (df[column] <= 0).sum()

        if invalid > 0:

            self.add_failure(
                "DQ-06",
                table,
                f"{invalid} negative/zero sales found",
                "WARNING"
            )


    # DQ-07 EPS
    def check_eps(self, eps, table):

        if eps is None:

            self.add_failure(
                "DQ-07",
                table,
                "Missing EPS value",
                "WARNING"
            )


    # DQ-08 Net Cash
    def check_net_cash(self, cash, debt, table):

        if cash is None or debt is None:

            self.add_failure(
                "DQ-08",
                table,
                "Missing cash/debt data",
                "WARNING"
            )


    # DQ-09 Tax Rate
    def check_tax_rate(self, tax_rate, table):

        if tax_rate < 0 or tax_rate > 100:

            self.add_failure(
                "DQ-09",
                table,
                "Invalid tax rate percentage",
                "WARNING"
            )


    # DQ-10 Dividend
    def check_dividend_cap(self, dividend, profit, table):

        if dividend > profit:

            self.add_failure(
                "DQ-10",
                table,
                "Dividend greater than profit",
                "WARNING"
            )


    # DQ-11 URL
    def check_url(self, url, table):

        if url and not url.startswith("http"):

            self.add_failure(
                "DQ-11",
                table,
                "Invalid URL format",
                "WARNING"
            )


    # DQ-12 Coverage
    def check_year_coverage(self, years, minimum=5, table=""):

        if len(years) < minimum:

            self.add_failure(
                "DQ-12",
                table,
                "Less than 5 years data available",
                "WARNING"
            )


    # DQ-13 Company ID
    def check_company_exists(self, company_id, table):

        if company_id is None:

            self.add_failure(
                "DQ-13",
                table,
                "Missing company ID",
                "CRITICAL"
            )


    # DQ-14 Ticker
    def check_ticker(self, ticker, table):

        if ticker is None or str(ticker).strip() == "":

            self.add_failure(
                "DQ-14",
                table,
                "Missing ticker symbol",
                "CRITICAL"
            )


    # DQ-15 BSE Balance
    def check_bse_balance(self, value, table):

        if value is None:

            self.add_failure(
                "DQ-15",
                table,
                "Missing BSE balance data",
                "WARNING"
            )


    # DQ-16 Financial Ratio
    def check_financial_ratio(self, ratio, table):

        if ratio is None:

            self.add_failure(
                "DQ-16",
                table,
                "Missing financial ratio",
                "WARNING"
            )
            
if __name__ == "__main__":
    
    validator = DataValidator()

    validator.export_failures(
        "output/validation_failures.csv"
    )

    print("validation_failures.csv generated")