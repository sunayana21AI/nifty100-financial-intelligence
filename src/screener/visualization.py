from __future__ import annotations

import pandas as pd
import plotly.express as px


class ScreenerVisualization:
    """
    Visualization utilities for Screener results.

    Each function returns a Plotly Figure object.
    The caller (Console / Streamlit / Notebook)
    can display it using fig.show() or st.plotly_chart().
    """

    # ---------------------------------------------------------
    # Sector Distribution
    # ---------------------------------------------------------

    @staticmethod
    def plot_sector_distribution(df: pd.DataFrame):

        if "broad_sector" not in df.columns:
            return None

        sector_df = (
            df["broad_sector"]
            .fillna("Unknown")
            .value_counts()
            .reset_index()
        )

        sector_df.columns = ["Sector", "Companies"]

        fig = px.bar(
            sector_df,
            x="Sector",
            y="Companies",
            title="Sector Distribution",
            text="Companies"
        )

        fig.update_layout(
            xaxis_title="Sector",
            yaxis_title="Number of Companies"
        )

        return fig

    # ---------------------------------------------------------
    # Market Cap Distribution
    # ---------------------------------------------------------

    @staticmethod
    def plot_market_cap_distribution(df: pd.DataFrame):

        if "market_cap_category" not in df.columns:
            return None

        cap_df = (
            df["market_cap_category"]
            .fillna("Unknown")
            .value_counts()
            .reset_index()
        )

        cap_df.columns = ["Market Cap", "Companies"]

        fig = px.bar(
            cap_df,
            x="Market Cap",
            y="Companies",
            title="Market Cap Distribution",
            text="Companies"
        )

        fig.update_layout(
            xaxis_title="Market Cap Category",
            yaxis_title="Number of Companies"
        )

        return fig

    # ---------------------------------------------------------
    # Composite Quality Score Distribution
    # ---------------------------------------------------------

    @staticmethod
    def plot_quality_score_distribution(df: pd.DataFrame):

        if "composite_quality_score" not in df.columns:
            return None

        fig = px.histogram(
            df,
            x="composite_quality_score",
            nbins=20,
            title="Composite Quality Score Distribution"
        )

        fig.update_layout(
            xaxis_title="Composite Quality Score",
            yaxis_title="Company Count"
        )

        return fig

    # ---------------------------------------------------------
    # Revenue CAGR Distribution
    # ---------------------------------------------------------

    @staticmethod
    def plot_revenue_cagr_distribution(df: pd.DataFrame):

        if "revenue_cagr_5yr" not in df.columns:
            return None

        fig = px.histogram(
            df,
            x="revenue_cagr_5yr",
            nbins=20,
            title="Revenue CAGR (5Y) Distribution"
        )

        fig.update_layout(
            xaxis_title="Revenue CAGR (%)",
            yaxis_title="Company Count"
        )

        return fig

    # ---------------------------------------------------------
    # PAT CAGR Distribution
    # ---------------------------------------------------------

    @staticmethod
    def plot_pat_cagr_distribution(df: pd.DataFrame):

        if "pat_cagr_5yr" not in df.columns:
            return None

        fig = px.histogram(
            df,
            x="pat_cagr_5yr",
            nbins=20,
            title="PAT CAGR (5Y) Distribution"
        )

        fig.update_layout(
            xaxis_title="PAT CAGR (%)",
            yaxis_title="Company Count"
        )

        return fig

    # ---------------------------------------------------------
    # Free Cash Flow Distribution
    # ---------------------------------------------------------

    @staticmethod
    def plot_fcf_distribution(df: pd.DataFrame):

        if "free_cash_flow_cr" not in df.columns:
            return None

        fig = px.box(
            df,
            y="free_cash_flow_cr",
            title="Free Cash Flow Distribution"
        )

        fig.update_layout(
            yaxis_title="Free Cash Flow (Cr)"
        )

        return fig

    # ---------------------------------------------------------
    # Top Companies by Composite Score
    # ---------------------------------------------------------

    @staticmethod
    def plot_top_companies(
        df: pd.DataFrame,
        top_n: int = 10
    ):

        required = [
            "company_name",
            "composite_quality_score"
        ]

        if not all(col in df.columns for col in required):
            return None

        top_df = (
            df.sort_values(
                by="composite_quality_score",
                ascending=False
            )
            .head(top_n)
        )

        fig = px.bar(
            top_df,
            x="composite_quality_score",
            y="company_name",
            orientation="h",
            text="composite_quality_score",
            title=f"Top {top_n} Companies by Composite Quality Score"
        )

        fig.update_layout(
            xaxis_title="Composite Quality Score",
            yaxis_title="Company"
        )

        fig.update_yaxes(
            categoryorder="total ascending"
        )

        return fig


# ============================================================
# Test Runner
# ============================================================

if __name__ == "__main__":

    from engine import ScreenerEngine

    engine = ScreenerEngine(
        "config/screener_config.yaml"
    )

    df = engine.load_data(
        "nifty100.db"
    )

    result = engine.apply_filters(df)

    viz = ScreenerVisualization()

    charts = [
        viz.plot_sector_distribution(result),
        viz.plot_market_cap_distribution(result),
        viz.plot_quality_score_distribution(result),
        viz.plot_revenue_cagr_distribution(result),
        viz.plot_pat_cagr_distribution(result),
        viz.plot_fcf_distribution(result),
        viz.plot_top_companies(result)
    ]

    for fig in charts:
        if fig is not None:
            fig.show()