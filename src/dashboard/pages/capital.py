import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
import streamlit as st
import plotly.express as px
from dashboard.utils.db import get_all_ratios_latest, OUTPUT_DIR

st.set_page_config(page_title="Capital", page_icon="💰", layout="wide")
st.title("💰 Capital Allocation")

# ---------- Try CSV first, but handle empty ----------
cap_path = OUTPUT_DIR / "capital_allocation.csv"
df = None

if cap_path.exists() and cap_path.stat().st_size > 20:
    try:
        df = pd.read_csv(cap_path)
        if df.empty or len(df.columns) == 0:
            df = None
    except Exception:
        df = None

# ---------- Fallback: derive from ratios ----------
if df is None:
    st.info("📊 Using D/E-based capital pattern classification (CSV was empty).")
    data = get_all_ratios_latest()

    if data.empty:
        st.error("No data available.")
        st.stop()

    de = pd.to_numeric(data["debt_to_equity"], errors="coerce").fillna(0)

    def cat(v):
        if v <= 0.1:  return "Debt-Free"
        if v <= 0.5:  return "Low Debt"
        if v <= 1.5:  return "Moderate Debt"
        return "High Debt"

    data["Capital Pattern"] = de.apply(cat)
    df = (data["Capital Pattern"].value_counts()
          .reset_index()
          .rename(columns={"index": "Pattern", "Capital Pattern": "Pattern"}))
    df.columns = ["Pattern", "Count"]

# ---------- Display count table ----------
st.subheader("Capital Allocation Patterns")
st.dataframe(df, use_container_width=True, hide_index=True)

# ---------- Treemap ----------
label_col = df.columns[0]
value_col = df.columns[1] if len(df.columns) > 1 else None

if value_col:
    fig = px.treemap(df, path=[label_col], values=value_col,
                     title="Capital Allocation Patterns")
    fig.update_traces(textinfo="label+value+percent root")
    st.plotly_chart(fig, use_container_width=True)

# ---------- Show companies per pattern (if fallback) ----------
if "data" in dir() and "Capital Pattern" in data.columns:
    st.markdown("---")
    st.subheader("Companies by Pattern")
    pattern = st.selectbox("Select Pattern", sorted(data["Capital Pattern"].unique()))
    subset = data[data["Capital Pattern"] == pattern][
        ["company_id", "company_name", "sector", "debt_to_equity", "roe"]
    ].dropna(how="all")
    st.dataframe(subset, use_container_width=True, hide_index=True)
    st.caption(f"Total: {len(subset)} companies in {pattern}")