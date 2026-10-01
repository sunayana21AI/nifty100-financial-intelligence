import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Trends", page_icon="📈", layout="wide")
st.title("📈 Trend Analysis")

DB = ROOT / "nifty100.db"


# ---------- Direct DB queries — NO CACHE ----------

def get_tickers():
    """Get ticker list directly from sectors table."""
    with sqlite3.connect(str(DB)) as c:
        df = pd.read_sql(
            "SELECT DISTINCT ticker FROM sectors WHERE ticker IS NOT NULL ORDER BY ticker",
            c
        )
    return df["ticker"].dropna().tolist()


def get_ratios(ticker):
    """Get all ratios for a ticker, with friendly column aliases."""
    with sqlite3.connect(str(DB)) as c:
        df = pd.read_sql(
            "SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year",
            c, params=[ticker]
        )

    # Add friendly aliases (keep original too)
    rename = {
        "return_on_equity_pct":           "roe",
        "return_on_capital_employed_pct": "roce",
        "net_profit_margin_pct":          "npm",
        "operating_profit_margin_pct":    "opm",
        "pe_ratio":                       "pe",
        "pb_ratio":                       "pb",
        "free_cash_flow_cr":              "fcf",
        "market_cap_crore":               "market_cap",
        "earnings_per_share":             "eps",
    }
    for raw, friendly in rename.items():
        if raw in df.columns and friendly not in df.columns:
            df[friendly] = df[raw]

    return df


# ---------- UI ----------

tickers = get_tickers()

# Debug caption — remove later
st.caption(f"✅ Loaded {len(tickers)} tickers | First 3: {tickers[:3]}")

if not tickers:
    st.error("No tickers found in `sectors` table. Check DB.")
    st.stop()

ticker = st.selectbox("Select Company", tickers)
df = get_ratios(ticker)

if df.empty:
    st.warning(f"No ratio data for **{ticker}**. Try another company.")
    st.stop()

# ---------- Metric picker ----------
ALL_METRICS = {
    "ROE (%)":         "roe",
    "ROCE (%)":        "roce",
    "NPM (%)":         "npm",
    "OPM (%)":         "opm",
    "P/E":             "pe",
    "P/B":             "pb",
    "D/E":             "debt_to_equity",
    "FCF (Cr)":        "fcf",
    "Market Cap (Cr)": "market_cap",
    "Rev CAGR 5yr":    "revenue_cagr_5yr",
    "PAT CAGR 5yr":    "pat_cagr_5yr",
    "EPS":             "eps",
}
available = {k: v for k, v in ALL_METRICS.items() if v in df.columns}

default = [k for k in ["ROE (%)", "P/E"] if k in available][:2]
picked = st.multiselect(
    "Choose up to 3 metrics",
    list(available.keys()),
    default=default,
)

if not picked:
    st.info("👆 Select at least one metric to see the trend.")
    st.stop()

# ---------- Chart ----------
df = df.sort_values("year")
cols = [available[k] for k in picked[:3]]

long = df.melt(id_vars="year", value_vars=cols,
               var_name="metric", value_name="value")
long = long.dropna(subset=["value"])

if long.empty:
    st.warning("Selected metrics have no data for this company.")
    st.stop()

fig = px.line(long, x="year", y="value", color="metric", markers=True,
              title=f"{ticker} — Trend")
st.plotly_chart(fig, use_container_width=True)

# ---------- Raw data table ----------
st.subheader("Raw Data")
st.dataframe(
    df[["year"] + cols].sort_values("year", ascending=False),
    use_container_width=True,
    hide_index=True,
)