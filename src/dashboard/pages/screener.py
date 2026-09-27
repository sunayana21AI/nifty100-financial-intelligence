"""
pages/screener.py
Screener Screen with filters and preset buttons
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.dashboard.utils import db


def show():
    st.markdown('<div class="main-header">🔍 Screener</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Filter Nifty 100 companies using multiple criteria</div>', unsafe_allow_html=True)
    
    # Get data
    df = db.get_all_valuation()
    
    if df.empty:
        st.warning("No data available")
        return
    
    # Sidebar filters
    st.sidebar.markdown("### 📊 Filters")
    
    # Preset buttons
    st.sidebar.markdown("**Presets:**")
    col1, col2 = st.sidebar.columns(2)
    
    preset_values = {
        'Quality': {'roe_min': 15, 'de_max': 1, 'fcf_min': 0, 'rev_cagr_min': 10, 'pat_cagr_min': 10, 'opm_min': 10, 'pe_max': 50, 'pb_max': 5, 'div_yield_min': 0, 'icr_min': 1},
        'Value': {'roe_min': 0, 'de_max': 2, 'fcf_min': 0, 'rev_cagr_min': 0, 'pat_cagr_min': 0, 'opm_min': 0, 'pe_max': 20, 'pb_max': 3, 'div_yield_min': 1, 'icr_min': 0},
        'Growth': {'roe_min': 0, 'de_max': 2, 'fcf_min': 0, 'rev_cagr_min': 15, 'pat_cagr_min': 20, 'opm_min': 0, 'pe_max': 100, 'pb_max': 10, 'div_yield_min': 0, 'icr_min': 1},
        'Dividend': {'roe_min': 0, 'de_max': 3, 'fcf_min': 0, 'rev_cagr_min': 0, 'pat_cagr_min': 0, 'opm_min': 0, 'pe_max': 100, 'pb_max': 10, 'div_yield_min': 2, 'icr_min': 0},
        'Debt-Free': {'roe_min': 12, 'de_max': 0.05, 'fcf_min': 0, 'rev_cagr_min': 0, 'pat_cagr_min': 0, 'opm_min': 0, 'pe_max': 100, 'pb_max': 10, 'div_yield_min': 0, 'icr_min': 0},
        'Turnaround': {'roe_min': 0, 'de_max': 3, 'fcf_min': 0, 'rev_cagr_min': 10, 'pat_cagr_min': 0, 'opm_min': 0, 'pe_max': 100, 'pb_max': 10, 'div_yield_min': 0, 'icr_min': 0}
    }
    
    if col1.button("🏆 Quality"):
        st.session_state.filters = preset_values['Quality']
    if col2.button("💰 Value"):
        st.session_state.filters = preset_values['Value']
    if col1.button("🚀 Growth"):
        st.session_state.filters = preset_values['Growth']
    if col2.button("📈 Dividend"):
        st.session_state.filters = preset_values['Dividend']
    if col1.button("🟢 Debt-Free"):
        st.session_state.filters = preset_values['Debt-Free']
    if col2.button("🔄 Turnaround"):
        st.session_state.filters = preset_values['Turnaround']
    
    st.sidebar.markdown("---")
    
    # Initialize session state for filters
    if 'filters' not in st.session_state:
        st.session_state.filters = {
            'roe_min': 0,
            'de_max': 10,
            'fcf_min': 0,
            'rev_cagr_min': 0,
            'pat_cagr_min': 0,
            'opm_min': 0,
            'pe_max': 100,
            'pb_max': 10,
            'div_yield_min': 0,
            'icr_min': 0
        }
    
    # Sliders
    st.sidebar.markdown("**Adjust Filters:**")
    
    roe_min = st.sidebar.slider("ROE Min %", 0, 50, st.session_state.filters.get('roe_min', 0))
    de_max = st.sidebar.slider("D/E Max", 0, 10, st.session_state.filters.get('de_max', 10))
    fcf_min = st.sidebar.slider("FCF Min (Cr)", -10000, 50000, st.session_state.filters.get('fcf_min', 0), step=500)
    rev_cagr_min = st.sidebar.slider("Revenue CAGR Min %", 0, 50, st.session_state.filters.get('rev_cagr_min', 0))
    pat_cagr_min = st.sidebar.slider("PAT CAGR Min %", 0, 50, st.session_state.filters.get('pat_cagr_min', 0))
    opm_min = st.sidebar.slider("OPM Min %", 0, 50, st.session_state.filters.get('opm_min', 0))
    pe_max = st.sidebar.slider("P/E Max", 0, 100, st.session_state.filters.get('pe_max', 100))
    pb_max = st.sidebar.slider("P/B Max", 0, 20, st.session_state.filters.get('pb_max', 10))
    div_yield_min = st.sidebar.slider("Dividend Yield Min %", 0, 10, st.session_state.filters.get('div_yield_min', 0))
    icr_min = st.sidebar.slider("Interest Coverage Min", 0, 20, st.session_state.filters.get('icr_min', 0))
    
    # Apply filters
    filtered = df.copy()
    
    if 'return_on_equity_pct' in filtered.columns:
        filtered = filtered[filtered['return_on_equity_pct'].fillna(0) >= roe_min]
    if 'debt_to_equity' in filtered.columns:
        filtered = filtered[filtered['debt_to_equity'].fillna(0) <= de_max]
    if 'free_cash_flow_cr' in filtered.columns:
        filtered = filtered[filtered['free_cash_flow_cr'].fillna(0) >= fcf_min]
    if 'revenue_cagr_5yr' in filtered.columns:
        filtered = filtered[filtered['revenue_cagr_5yr'].fillna(0) >= rev_cagr_min]
    if 'pat_cagr_5yr' in filtered.columns:
        filtered = filtered[filtered['pat_cagr_5yr'].fillna(0) >= pat_cagr_min]
    if 'operating_profit_margin_pct' in filtered.columns:
        filtered = filtered[filtered['operating_profit_margin_pct'].fillna(0) >= opm_min]
    if 'pe_ratio' in filtered.columns:
        filtered = filtered[filtered['pe_ratio'].fillna(0) <= pe_max]
    if 'pb_ratio' in filtered.columns:
        filtered = filtered[filtered['pb_ratio'].fillna(0) <= pb_max]
    if 'dividend_yield_pct' in filtered.columns:
        filtered = filtered[filtered['dividend_yield_pct'].fillna(0) >= div_yield_min]
    if 'interest_coverage' in filtered.columns:
        filtered = filtered[filtered['interest_coverage'].fillna(0) >= icr_min]
    
    # Results
    st.markdown(f"### 📊 Results: **{len(filtered)}** companies match your filters")
    
    if not filtered.empty:
        # Display columns
        display_cols = ['company_name', 'company_id', 'broad_sector', 'return_on_equity_pct', 
                       'debt_to_equity', 'pe_ratio', 'revenue_cagr_5yr']
        display_cols = [c for c in display_cols if c in filtered.columns]
        
        st.dataframe(filtered[display_cols], use_container_width=True, hide_index=True)
        
        # CSV Download
        csv = filtered.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name="screener_results.csv",
            mime="text/csv"
        )
    else:
        st.info("No companies match your filters. Try adjusting the criteria.")


if __name__ == "__main__":
    show()