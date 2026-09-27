from __future__ import annotations

import pandas as pd


class ScreenerAnalytics:
    """
    Analytics utilities for Screener results.
    """

    # ---------------------------------------------------------
    # Company Count
    # ---------------------------------------------------------

    @staticmethod
    def company_count(df: pd.DataFrame) -> int:
        return len(df)

    # ---------------------------------------------------------
    # Average KPI Summary
    # ---------------------------------------------------------

    @staticmethod
    def average_kpis(df: pd.DataFrame) -> dict:

        metrics = {
            "Operating Profit Margin (%)": "operating_profit_margin_pct",
            "Return on Assets (%)": "return_on_assets_pct",
            "Asset Turnover": "asset_turnover",
            "Revenue CAGR (5Y %)": "revenue_cagr_5yr",
            "PAT CAGR (5Y %)": "pat_cagr_5yr",
            "Free Cash Flow (Cr)": "free_cash_flow_cr"
        }

        summary = {}

        for label, column in metrics.items():

            if column in df.columns:

                summary[label] = round(
                    df[column].mean(skipna=True),
                    2
                )

        return summary

    # ---------------------------------------------------------
    # Sector Distribution
    # ---------------------------------------------------------

    @staticmethod
    def sector_distribution(df: pd.DataFrame) -> pd.Series:

        if "broad_sector" not in df.columns:
            return pd.Series(dtype=int)

        return (
            df["broad_sector"]
            .fillna("Unknown")
            .value_counts()
        )

    # ---------------------------------------------------------
    # Market Cap Distribution
    # ---------------------------------------------------------

    @staticmethod
    def market_cap_distribution(df: pd.DataFrame) -> pd.Series:

        if "market_cap_category" not in df.columns:
            return pd.Series(dtype=int)

        return (
            df["market_cap_category"]
            .fillna("Unknown")
            .value_counts()
        )

    # ---------------------------------------------------------
    # Top Companies
    # ---------------------------------------------------------

    @staticmethod
    def top_companies(
        df: pd.DataFrame,
        top_n: int = 10
    ) -> pd.DataFrame:

        if "composite_quality_score" not in df.columns:
            return df.head(top_n)

        columns = [
            col
            for col in [
                "company_name",
                "ticker",
                "broad_sector",
                "composite_quality_score"
            ]
            if col in df.columns
        ]

        return (
            df.sort_values(
                by="composite_quality_score",
                ascending=False
            )[columns]
            .head(top_n)
            .reset_index(drop=True)
        )

    # ---------------------------------------------------------
    # Complete Summary
    # ---------------------------------------------------------

    @classmethod
    def generate_summary(cls, df: pd.DataFrame):

        print("\n" + "=" * 60)
        print("SCREENER ANALYTICS SUMMARY")
        print("=" * 60)

        print(f"\nCompanies Selected : {cls.company_count(df)}")

        print("\nAverage KPIs")
        print("-" * 40)

        averages = cls.average_kpis(df)

        for metric, value in averages.items():
            print(f"{metric:<30} : {value}")

        print("\nSector Distribution")
        print("-" * 40)

        print(cls.sector_distribution(df))

        print("\nMarket Cap Distribution")
        print("-" * 40)

        print(cls.market_cap_distribution(df))

        print("\nTop Companies")
        print("-" * 40)

        print(cls.top_companies(df))

        print("=" * 60)