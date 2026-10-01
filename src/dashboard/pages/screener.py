import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
import streamlit as st
from dashboard.utils.db import get_all_ratios_latest, get_companies

st.set_page_config(page_title="Screener", page_icon="🔎", layout="wide")
st.title("🔎 Screener")

# Load latest data
df = get_all_ratios_latest()
if df.empty:
    st.error("No data available.")
    st.stop()

# Merge company names
comp = get_companies()
if "company_name" not in df.columns and "company_name" in comp.columns:
    df = df.merge(comp[["company_id", "company_name"]], on="company_id", how="left")

# ---------- Sidebar sliders ----------
st.sidebar.header("Filters")

roe_min = st.sidebar.slider("Min ROE %", -50.0, 100.0, 10.0, step=1.0)
pe_max  = st.sidebar.slider("Max P/E", 0.0, 200.0, 50.0, step=1.0)
de_max  = st.sidebar.slider("Max D/E", 0.0, 5.0, 2.0, step=0.1)
fcf_min = st.sidebar.slider("Min FCF (Cr)", -5000.0, 50000.0, 0.0, step=100.0)

# ---------- Presets ----------
preset = st.sidebar.selectbox("Preset",
    ["Custom", "Quality", "Value", "Growth", "Dividend", "Low Debt"])

if preset == "Quality":
    roe_min, pe_max, de_max = 18.0, 40.0, 1.0
elif preset == "Value":
    roe_min, pe_max, de_max = 10.0, 20.0, 2.0
elif preset == "Growth":
    roe_min, pe_max, de_max = 15.0, 60.0, 3.0
elif preset == "Dividend":
    roe_min, pe_max, de_max = 12.0, 35.0, 1.5
elif preset == "Low Debt":
    roe_min, pe_max, de_max = 10.0, 50.0, 0.3

# ---------- Apply filters ----------
f = df.copy()
if "roe" in f.columns:
    f = f[pd.to_numeric(f["roe"], errors="coerce") >= roe_min]
if "pe" in f.columns:
    f = f[pd.to_numeric(f["pe"], errors="coerce") <= pe_max]
if "debt_to_equity" in f.columns:
    f = f[pd.to_numeric(f["debt_to_equity"], errors="coerce") <= de_max]
if "fcf" in f.columns:
    f = f[pd.to_numeric(f["fcf"], errors="coerce") >= fcf_min]

# ---------- Result count ----------
st.metric("Companies Matching", len(f))

# ---------- Show table ----------
display_cols = [c for c in ["company_id", "company_name", "sector",
                            "roe", "pe", "debt_to_equity", "fcf",
                            "composite_score"]
                if c in f.columns]

st.dataframe(f[display_cols].head(100), use_container_width=True, hide_index=True)

# ---------- CSV Download ----------
st.download_button(
    "⬇️ Download CSV",
    f[display_cols].to_csv(index=False).encode("utf-8"),
    file_name="screener_results.csv",
    mime="text/csv",
)