"""
src/dashboard/app.py
Main Streamlit entry point for Nifty 100 Analytics Dashboard
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Page configuration - must be first Streamlit command
st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A5F;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .kpi-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        border-left: 4px solid #1E3A5F;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1E3A5F;
    }
    .kpi-label {
        font-size: 0.9rem;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.image("https://img.icons8.com/fluency/96/000000/stock.png", width=80)
st.sidebar.title("📊 Nifty 100 Analytics")
st.sidebar.markdown("---")

# Navigation options
pages = {
    "🏠 Home": "home",
    "🏢 Company Profile": "profile",
    "🔍 Screener": "screener",
    "👥 Peer Comparison": "peers",
    "📈 Trend Analysis": "trends",
    "🏭 Sector Analysis": "sectors",
    "💰 Capital Allocation": "capital",
    "📄 Reports": "reports"
}

selection = st.sidebar.radio("Navigate", list(pages.keys()), index=0)

st.sidebar.markdown("---")
st.sidebar.info(
    "**Data Source:** Nifty 100 Financial Database\n"
    "**Last Updated:** 2024\n"
    "**Version:** 1.0.0"
)

# Route to selected page
page_name = pages[selection]

try:
    if page_name == "home":
        from pages import home as page_module
    elif page_name == "profile":
        from pages import profile as page_module
    elif page_name == "screener":
        from pages import screener as page_module
    elif page_name == "peers":
        from pages import peers as page_module
    elif page_name == "trends":
        from pages import trends as page_module
    elif page_name == "sectors":
        from pages import sectors as page_module
    elif page_name == "capital":
        from pages import capital as page_module
    elif page_name == "reports":
        from pages import reports as page_module
    
    # Run the page
    page_module.show()
    
except ImportError as e:
    st.error(f"⚠️ Page not implemented yet: {e}")
    st.info("This page is under development. Please check back soon.")
except Exception as e:
    st.error(f"⚠️ Error loading page: {e}")

st.sidebar.markdown("---")
st.sidebar.caption("Nifty 100 Screener Dashboard v1.0")