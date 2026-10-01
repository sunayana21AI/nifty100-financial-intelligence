"""
pages/02_profile.py
Company Profile Screen — Search, KPI tiles, charts.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from dashboard.utils import db


def _get(row, *keys, default=None):
    """Try multiple column names, return first non-NaN value."""
    for k in keys:
        if k in row and pd.notna(row[k]):
            return row[k]
    return default


def show():
    st.markdown("### 🏢 Company Profile")

    try:
        # ---------- Company list ----------
        companies = db.get_companies()
        if companies.empty:
            st.warning("No companies found in database.")
            return

        # ---------- Search dropdown ----------
        company_options = {}
        for _, row in companies.iterrows():
            label = f"{row['company_name']} ({row['ticker']})"
            company_options[label] = row["ticker"]

        search = st.selectbox("🔍 Search for a company",
                              options=list(company_options.keys()), index=0)
        ticker = company_options.get(search)

        if not ticker:
            st.warning("Ticker not found — please try another")
            return

        # ---------- Load data ----------
        ratios = db.get_ratios(ticker)
        pl = db.get_pl(ticker)
        sectors = db.get_sectors()

        if ratios.empty:
            st.warning(f"No financial data found for {ticker}")
            return

        # ---------- Sector info ----------
        sector_info = sectors[sectors["ticker"] == ticker]
        broad_sector = sector_info["broad_sector"].iloc[0] if not sector_info.empty else "N/A"
        sub_sector = sector_info["sub_sector"].iloc[0] if not sector_info.empty else "N/A"

        company_name = (companies[companies["ticker"] == ticker]["company_name"].iloc[0]
                        if not companies.empty else ticker)

        st.markdown(f"#### {company_name} ({ticker})")
        st.caption(f"**Sector:** {broad_sector} | **Sub-Sector:** {sub_sector}")

        # ---------- Latest year row ----------
        ratios_sorted = ratios.sort_values("year")
        latest = ratios_sorted.iloc[-1] if not ratios_sorted.empty else None

        if latest is not None:
            st.caption(f"📅 Latest year: **{int(latest['year'])}**")

            col1, col2, col3, col4, col5, col6 = st.columns(6)

            with col1:
                val = _get(latest, "roe", "return_on_equity_pct")
                st.metric("ROE", f"{val:.1f}%" if val is not None else "N/A")
            with col2:
                val = _get(latest, "roce", "return_on_capital_employed_pct")
                st.metric("ROCE", f"{val:.1f}%" if val is not None else "N/A")
            with col3:
                val = _get(latest, "npm", "net_profit_margin_pct")
                st.metric("NPM", f"{val:.1f}%" if val is not None else "N/A")
            with col4:
                val = _get(latest, "debt_to_equity")
                st.metric("D/E", f"{val:.2f}" if val is not None else "N/A")
            with col5:
                val = _get(latest, "revenue_cagr_5yr")
                st.metric("Rev CAGR (5yr)", f"{val:.1f}%" if val is not None else "N/A")
            with col6:
                val = _get(latest, "fcf", "free_cash_flow_cr")
                st.metric("FCF", f"₹{val:.1f} Cr" if val is not None else "N/A")

        st.markdown("---")

        # ---------- Charts ----------
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📈 Revenue & Net Profit")
            if not pl.empty:
                pl_sorted = pl.sort_values("year").tail(10)

                fig = make_subplots(specs=[[{"secondary_y": True}]])
                fig.add_trace(
                    go.Bar(name="Revenue", x=pl_sorted["year"], y=pl_sorted["sales"],
                           marker_color="#1E3A5F"),
                    secondary_y=False)
                fig.add_trace(
                    go.Scatter(name="Net Profit", x=pl_sorted["year"],
                               y=pl_sorted["net_profit"], mode="lines+markers",
                               line=dict(color="#E74C3C", width=3)),
                    secondary_y=True)
                fig.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
                fig.update_yaxes(title_text="Revenue (Cr)", secondary_y=False)
                fig.update_yaxes(title_text="Net Profit (Cr)", secondary_y=True)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No P&L data available")

        with col2:
            st.subheader("📊 ROE & ROCE Trend")
            if not ratios.empty:
                ratios_10 = ratios.sort_values("year").tail(10)
                roe_col = "roe" if "roe" in ratios_10.columns else "return_on_equity_pct"
                roce_col = "roce" if "roce" in ratios_10.columns else "return_on_capital_employed_pct"

                fig = make_subplots(specs=[[{"secondary_y": True}]])
                fig.add_trace(
                    go.Bar(name="ROE", x=ratios_10["year"], y=ratios_10[roe_col],
                           marker_color="#2ECC71"),
                    secondary_y=False)
                fig.add_trace(
                    go.Scatter(name="ROCE", x=ratios_10["year"], y=ratios_10[roce_col],
                               mode="lines+markers",
                               line=dict(color="#E67E22", width=3)),
                    secondary_y=True)
                fig.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
                fig.update_yaxes(title_text="ROE (%)", secondary_y=False)
                fig.update_yaxes(title_text="ROCE (%)", secondary_y=True)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No ratio data available")

        # ---------- Pros & Cons ----------
        st.markdown("---")
        st.subheader("👍 Pros & 👎 Cons")
        try:
            pc = db.get_prosandcons(ticker)
            if not pc.empty:
                row = pc.iloc[0]
                pros = str(row.get("pros", "")).split("|") if row.get("pros") else []
                cons = str(row.get("cons", "")).split("|") if row.get("cons") else []

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**✅ Pros**")
                    if pros and pros != [""]:
                        for p in pros:
                            if p.strip():
                                st.markdown(f"- {p.strip()}")
                    else:
                        st.caption("No pros available")
                with c2:
                    st.markdown("**❌ Cons**")
                    if cons and cons != [""]:
                        for c in cons:
                            if c.strip():
                                st.markdown(f"- {c.strip()}")
                    else:
                        st.caption("No cons available")
            else:
                st.caption("No pros/cons data available for this company.")
        except Exception as e:
            st.caption(f"Pros/cons not available: {e}")

    except Exception as e:
        st.error(f"⚠️ Error loading company profile: {e}")
        st.info("Please try another ticker or check the database connection.")


if __name__ == "__main__":
    show()