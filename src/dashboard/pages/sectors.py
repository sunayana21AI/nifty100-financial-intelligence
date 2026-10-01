import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
import streamlit as st
import plotly.express as px
from dashboard.utils.db import get_all_ratios_latest, get_companies

st.set_page_config(page_title="Sectors", page_icon="🗂️", layout="wide")
st.title("🗂️ Sector Analysis")

df = get_all_ratios_latest()
if df.empty:
    st.error("No data.")
    st.stop()

if "sector" not in df.columns:
    st.error("Sector column not found in merged data.")
    st.write("Columns:", df.columns.tolist())
    st.stop()

# ---------- Bubble chart ----------
x_col = "market_cap" if "market_cap" in df.columns else "fcf"
y_col = "roe" if "roe" in df.columns else None

if y_col and x_col in df.columns:
    fig = px.scatter(
        df, x=x_col, y=y_col,
        color="sector",
        size="market_cap" if "market_cap" in df.columns else None,
        hover_name="company_id",
        title="Sector Bubble — Market Cap vs ROE",
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------- Median KPI by sector ----------
st.subheader("Median ROE by Sector")
sec = df.groupby("sector")["roe"].median().reset_index().dropna()
sec = sec.sort_values("roe", ascending=False)
fig2 = px.bar(sec, x="sector", y="roe", title="Median ROE by Sector")
st.plotly_chart(fig2, use_container_width=True)