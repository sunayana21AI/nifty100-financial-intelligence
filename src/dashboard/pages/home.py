import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
import streamlit as st
import plotly.express as px
from dashboard.utils.db import (
    get_companies, get_ratios_for_year, get_years, get_valuation_summary
)

st.set_page_config(page_title="Home", page_icon="🏠", layout="wide")

st.markdown("🏠 **Nifty 100 Dashboard**")
st.caption("Comprehensive analytics for Nifty 100 companies")

# ---------- Year Selector ----------
YEARS = get_years()
DEFAULT_YEARS = [y for y in YEARS if 2019 <= y <= 2024]
if not DEFAULT_YEARS:
    DEFAULT_YEARS = YEARS[-6:]

selected_year = st.selectbox("Select Year", DEFAULT_YEARS,
                             index=len(DEFAULT_YEARS) - 1)

# ---------- Load data (single query, correct year) ----------
ratios = get_ratios_for_year(selected_year)
companies = get_companies()

# ---------- Helpers ----------
def safe_median(df, col, lo=None, hi=None, decimals=1):
    if df.empty or col not in df.columns:
        return None
    s = pd.to_numeric(df[col], errors="coerce").dropna()
    if lo is not None: s = s[s >= lo]
    if hi is not None: s = s[s <= hi]
    if s.empty:
        return None
    return round(s.median(), decimals)

def fmt(v, suffix="", decimals=1):
    if v is None:
        return "N/A"
    return f"{v:.{decimals}f}{suffix}"

# ---------- KPI Tiles ----------
st.markdown("### 📊 Key Metrics")

median_roe   = safe_median(ratios, "roe", lo=-100, hi=200, decimals=1)
median_pe    = safe_median(ratios, "pe",  lo=0,    hi=200, decimals=1)
median_de    = safe_median(ratios, "debt_to_equity", lo=-10, hi=10, decimals=2)
median_cagr  = safe_median(ratios, "revenue_cagr_5yr", lo=-50, hi=100, decimals=1)

debt_free = 0
if not ratios.empty and "debt_to_equity" in ratios.columns:
    de = pd.to_numeric(ratios["debt_to_equity"], errors="coerce").fillna(0)
    debt_free = int((de <= 0.05).sum())

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Median ROE",       fmt(median_roe, "%"))
c2.metric("Median P/E",       fmt(median_pe, "x"))
c3.metric("Median D/E",       fmt(median_de, "", 2))
c4.metric("Total Companies",  len(companies))
c5.metric("Median Rev CAGR",  fmt(median_cagr, "%"))
c6.metric("Debt-Free",        debt_free)

st.caption(f"📅 Data for year **{selected_year}** | {len(ratios)} companies with data")

# ---------- Sector Distribution + Top Sectors ----------
st.markdown("---")
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("🏭 Sector Distribution")
    if not companies.empty and "sector" in companies.columns:
        sec = companies["sector"].value_counts().reset_index()
        sec.columns = ["Sector", "Count"]
        fig = px.pie(sec, names="Sector", values="Count", hole=0.55,
                     title=f"Sector Distribution ({selected_year})")
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sector column not available.")

with col_right:
    st.subheader("📊 Top Sectors")
    if not companies.empty and "sector" in companies.columns:
        top = companies["sector"].value_counts().head(5).reset_index()
        top.columns = ["Sector", "Count"]
        st.dataframe(top, use_container_width=True, hide_index=True)

# ---------- Top 5 by Composite Score ----------
st.markdown("---")
st.subheader(f"🏆 Top 5 Companies by Composite Score ({selected_year})")

if not ratios.empty and "composite_score" in ratios.columns:
    top5 = (ratios.dropna(subset=["composite_score"])
                  .nlargest(5, "composite_score")
                  [["company_id", "company_name", "sector",
                    "composite_score", "roe", "pe"]]
                  .rename(columns={
                      "company_id": "Ticker",
                      "company_name": "Company",
                      "sector": "Sector",
                      "composite_score": "Score",
                      "roe": "ROE %",
                      "pe": "P/E",
                  }))
    st.dataframe(top5, use_container_width=True, hide_index=True)
else:
    st.info("Composite score data not available for this year.")

st.markdown("---")
st.caption(f"Data as of {selected_year} | Nifty 100 Analytics v1.0")