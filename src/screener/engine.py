import copy
import sqlite3
from pathlib import Path

import pandas as pd
import yaml


class ScreenerEngine:

    def __init__(self, config_path):
        self.config_path = Path(config_path)

        with open(self.config_path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)

        self.filters = config["filters"]

    # ---------------------------------------------------------
    # LOAD DATA
    # ---------------------------------------------------------
    def load_data(self, db_path):

        conn = sqlite3.connect(db_path)

        ratios_query = """
        SELECT
            fr.*,
            c.company_name,
            c.ticker,
            c.company_id AS numeric_company_id,
            s.broad_sector,
            s.sub_sector,
            s.market_cap_category
        FROM financial_ratios fr
        JOIN companies c
            ON fr.company_id = c.ticker
        LEFT JOIN sectors s
            ON c.sector_id = s.id
        """

        df = pd.read_sql(ratios_query, conn)

        pnl_query = """
        SELECT
            company_id,
            year,
            sales,
            net_profit
        FROM profitandloss
        """

        pnl = pd.read_sql(pnl_query, conn)

        companies = pd.read_sql(
            """
            SELECT company_id, ticker
            FROM companies
            """,
            conn
        )

        conn.close()
        
        # -----------------------------------------------------
        # Normalize company_id types before merge
        # -----------------------------------------------------
        pnl["company_id"] = pd.to_numeric(
            pnl["company_id"],
            errors="coerce"
        ).astype("Int64")

        companies["company_id"] = pd.to_numeric(
            companies["company_id"],
            errors="coerce"
        ).astype("Int64")

        # -----------------------------------------------------
        # Normalize P&L company ID -> ticker
        # -----------------------------------------------------
        pnl = pnl.merge(
            companies,
            on="company_id",
            how="left"
        )

        pnl["year"] = pd.to_numeric(
            pnl["year"],
            errors="coerce"
        )

        df["year"] = pd.to_numeric(
            df["year"],
            errors="coerce"
        )

        # Keep latest P&L record for each ticker/year
        pnl = (
            pnl
            .dropna(subset=["ticker"])
            .drop_duplicates(
                subset=["ticker", "year"],
                keep="first"
            )
        )

        pnl = pnl[
            [
                "ticker",
                "year",
                "sales",
                "net_profit"
            ]
        ]

        # -----------------------------------------------------
        # Merge P&L metrics
        # -----------------------------------------------------
        df = df.merge(
            pnl,
            on=["ticker", "year"],
            how="left"
        )

        df.rename(
            columns={
                "sales": "sales_cr",
                "net_profit": "net_profit_cr"
            },
            inplace=True
        )

        # -----------------------------------------------------
        # Use latest available financial year per company
        # -----------------------------------------------------
        df = df.sort_values(
            ["company_id", "year"],
            ascending=[True, False]
        )

        df = df.drop_duplicates(
            subset=["company_id"],
            keep="first"
        )

        df.reset_index(drop=True, inplace=True)

        return df

    # ---------------------------------------------------------
    # APPLY FILTERS
    # ---------------------------------------------------------
    def apply_filters(self, df, custom_filters=None):

        filters = copy.deepcopy(self.filters)

        # Custom threshold override
        if custom_filters:
            for key, value in custom_filters.items():

                if key not in filters:
                    raise ValueError(
                        f"Unknown filter: {key}"
                    )

                filters[key]["default"] = value

        result = df.copy()

        # -----------------------------------------------------
        # Convert filter columns to numeric where required
        # -----------------------------------------------------
        numeric_columns = [
            rule["column"]
            for rule in filters.values()
            if rule["column"] in result.columns
        ]

        for column in numeric_columns:

            if column == "interest_coverage":

                result[column] = result[column].replace(
                    "Debt Free",
                    float("inf")
                )

            result[column] = pd.to_numeric(
                result[column],
                errors="coerce"
            )

        # -----------------------------------------------------
        # Apply every filter
        # -----------------------------------------------------
        for filter_name, rule in filters.items():

            column = rule["column"]
            operator = rule["operator"]
            value = rule["default"]

            print(f"\nApplying Filter : {filter_name}")
            print("Rows Before    :", len(result))

            if column not in result.columns:
                raise ValueError(
                    f"Required filter column missing: {column}"
                )

            # -------------------------------------------------
            # D/E exception:
            # Financials are NOT filtered on D/E
            # -------------------------------------------------
            if filter_name == "de_max":

                if "broad_sector" in result.columns:

                    financial_mask = (
                        result["broad_sector"]
                        .fillna("")
                        .str.strip()
                        .str.lower()
                        .eq("financials")
                    )

                    financials = result[
                        financial_mask
                    ]

                    non_financials = result[
                        ~financial_mask
                    ]

                    if operator == "<":
                        non_financials = non_financials[
                            non_financials[column] < value
                        ]

                    elif operator == "<=":
                        non_financials = non_financials[
                            non_financials[column] <= value
                        ]

                    elif operator == ">":
                        non_financials = non_financials[
                            non_financials[column] > value
                        ]

                    elif operator == ">=":
                        non_financials = non_financials[
                            non_financials[column] >= value
                        ]

                    elif operator == "==":
                        non_financials = non_financials[
                            non_financials[column] == value
                        ]

                    result = pd.concat(
                        [
                            non_financials,
                            financials
                        ],
                        ignore_index=True
                    )

                    print("Rows After     :", len(result))
                    continue

            # -------------------------------------------------
            # Standard operators
            # -------------------------------------------------
            if operator == ">":

                result = result[
                    result[column] > value
                ]

            elif operator == ">=":

                result = result[
                    result[column] >= value
                ]

            elif operator == "<":

                result = result[
                    result[column] < value
                ]

            elif operator == "<=":

                result = result[
                    result[column] <= value
                ]

            elif operator == "==":

                result = result[
                    result[column] == value
                ]

            else:
                raise ValueError(
                    f"Unsupported operator '{operator}' "
                    f"for filter '{filter_name}'"
                )

            print("Rows After     :", len(result))

        # -----------------------------------------------------
        # Remove duplicate companies if any
        # -----------------------------------------------------
        result = result.drop_duplicates(
            subset=["company_id"],
            keep="first"
        )

        # -----------------------------------------------------
        # Temporary composite score
        # Day 17 will replace this with the official
        # 35/30/20/15 weighted methodology.
        # -----------------------------------------------------
        result["composite_quality_score"] = (
            self._calculate_basic_score(result)
        )

        result = result.sort_values(
            by="composite_quality_score",
            ascending=False
        )

        result.reset_index(drop=True, inplace=True)

        return result

    # ---------------------------------------------------------
    # BASIC COMPOSITE
    # ---------------------------------------------------------
    def _calculate_basic_score(self, df):

        score_columns = []

        metrics = {
            "return_on_equity_pct": True,
            "operating_profit_margin_pct": True,
            "revenue_cagr_5yr": True,
            "pat_cagr_5yr": True,
            "free_cash_flow_cr": True,
            "interest_coverage": True,
            "asset_turnover": True,
            "debt_to_equity": False,
        }

        for column, higher_is_better in metrics.items():

            if column not in df.columns:
                continue

            series = pd.to_numeric(
                df[column],
                errors="coerce"
            )

            if not higher_is_better:
                series = -series

            min_value = series.min()
            max_value = series.max()

            if pd.isna(min_value) or pd.isna(max_value):
                continue

            if max_value == min_value:

                scaled = pd.Series(
                    50.0,
                    index=df.index
                )

            else:

                scaled = (
                    (series - min_value)
                    / (max_value - min_value)
                ) * 100

            score_columns.append(scaled)

        if not score_columns:

            return pd.Series(
                0.0,
                index=df.index
            )

        return pd.concat(
            score_columns,
            axis=1
        ).mean(axis=1)

    # ---------------------------------------------------------
    # SAVE RESULTS
    # ---------------------------------------------------------
    def save_results(self, df, output_path):

        output_path = Path(output_path)
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        df.to_excel(
            output_path,
            index=False
        )

        print(
            f"\n✔ Screener output saved to: {output_path}"
        )


# =============================================================
# TEST RUN
# =============================================================
if __name__ == "__main__":

    engine = ScreenerEngine(
        "config/screener_config.yaml"
    )

    df = engine.load_data(
        "nifty100.db"
    )

    print("\nRows Loaded :", len(df))

    print("\nColumns:")
    print(df.columns.tolist())

    result = engine.apply_filters(df)

    print(
        "\nCompanies Selected :",
        len(result)
    )

    display_columns = [
        "company_name",
        "ticker",
        "broad_sector",
        "year",
        "return_on_equity_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "operating_profit_margin_pct",
        "pe_ratio",
        "pb_ratio",
        "dividend_yield_pct",
        "interest_coverage",
        "market_cap_crore",
        "net_profit_cr",
        "eps_cagr_5yr",
        "asset_turnover",
        "sales_cr",
        "composite_quality_score"
    ]

    available_columns = [
        column
        for column in display_columns
        if column in result.columns
    ]

    print(
        result[available_columns].head(10)
    )

    engine.save_results(
        result,
        "output/screener_output.xlsx"
    )