"""
src/dashboard/app.py
Main Streamlit entry point for Nifty 100 Analytics Dashboard.

This is a minimal entry point. The real 8 screens live in the
`pages/` directory (auto-detected by Streamlit's multipage system).
"""
import sys
from pathlib import Path
import streamlit as st

# ---------- Paths ----------
ROOT = Path(__file__).resolve().parents[2]      # project root
sys.path.insert(0, str(ROOT / "src"))

# ---------- Page config ----------
st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Sidebar (optional custom content) ----------
with st.sidebar:
    st.markdown("### 📊 Nifty 100 Analytics")
    st.caption("Sprint 4 — Dashboard & Valuation")
    st.markdown("---")
    st.markdown(
        "**Data Source:** Nifty 100 Financial Database  \n"
        "**Last Updated:** 2024  \n"
        "**Version:** 1.0.0"
    )

# ---------- Welcome content ----------
st.title("📊 Nifty 100 Analytics Dashboard")
st.caption("Comprehensive analytics for Nifty 100 companies")

st.markdown(
    """
    ### 👈 Use the sidebar to navigate the 8 screens

    | Screen | What it shows |
    |--------|---------------|
    | 🏠 **Home** | Overall KPIs & sector donut |
    | 🏢 **Company Profile** | Company details & charts |
    | 🔎 **Screener** | Filter companies, export CSV |
    | 👥 **Peer Comparison** | Peer radar & comparison |
    | 📈 **Trend Analysis** | 10-year multi-metric trends |
    | 🗂️ **Sector Analysis** | Sector bubble & medians |
    | 💰 **Capital Allocation** | Capital allocation treemap |
    | 📄 **Reports** | Annual report PDF links |
    """
)

st.info(f"📁 Project root: `{ROOT}`")