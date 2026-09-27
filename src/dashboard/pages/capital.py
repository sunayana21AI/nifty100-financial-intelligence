"""
pages/capital.py
Capital Allocation Map - Treemap of companies
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.dashboard.utils import db


def show():
    st.markdown('<div class="main-header">💰 Capital Allocation</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Visualize companies by capital allocation patterns</div>', unsafe_allow_html=True)
    
    # Get data
    df = db.get_all_valuation()
    sectors = db.get_sectors()
    
    if df.empty:
        st.warning("No data available")
        return
    
    # Merge with sectors
    df = df.merge(sectors, left_on='company_id', right_on='ticker', how='left')
    
    # Fix column names after merge
    if 'broad_sector_x' in df.columns:
        df['broad_sector'] = df['broad_sector_x']
    elif 'broad_sector_y' in df.columns:
        df['broad_sector'] = df['broad_sector_y']
    
    # Create capital allocation categories based on metrics
    def get_capital_pattern(row):
        roe = row.get('return_on_equity_pct', 0)
        de = row.get('debt_to_equity', 0)
        fcf = row.get('free_cash_flow_cr', 0)
        
        if pd.isna(roe) or pd.isna(de) or pd.isna(fcf):
            return 'Unknown'
        
        if roe > 20 and de < 0.5:
            return 'Quality Compounders'
        elif roe > 15 and fcf > 0:
            return 'Cash Generators'
        elif de > 2:
            return 'Leveraged'
        elif roe < 10:
            return 'Low Returns'
        else:
            return 'Balanced'
    
    df['capital_pattern'] = df.apply(get_capital_pattern, axis=1)
    
    # Treemap
    st.subheader("📊 Capital Allocation Treemap")
    
    # Ensure we have the required columns
    if 'broad_sector' not in df.columns:
        st.warning("Sector data not available")
        return
    
    if df['broad_sector'].dropna().empty:
        st.warning("No sector data available for treemap")
        return
    
    fig = px.treemap(
        df,
        path=['broad_sector', 'capital_pattern', 'company_name'],
        values='market_cap_crore',
        color='return_on_equity_pct',
        color_continuous_scale='RdYlGn',
        title='Companies by Sector, Capital Pattern, and ROE'
    )
    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)
    
    # Pattern breakdown
    st.subheader("📊 Capital Pattern Breakdown")
    
    pattern_counts = df['capital_pattern'].value_counts().reset_index()
    pattern_counts.columns = ['Pattern', 'Count']
    
    st.dataframe(pattern_counts, use_container_width=True, hide_index=True)
    
    # Show companies by pattern
    if not pattern_counts.empty:
        selected_pattern = st.selectbox("Select Pattern to View Companies", pattern_counts['Pattern'].tolist())
        
        if selected_pattern:
            pattern_df = df[df['capital_pattern'] == selected_pattern]
            display_cols = ['company_name', 'company_id', 'broad_sector', 'return_on_equity_pct', 'debt_to_equity', 'free_cash_flow_cr']
            display_cols = [c for c in display_cols if c in pattern_df.columns]
            st.dataframe(pattern_df[display_cols], use_container_width=True, hide_index=True)
    else:
        st.info("No capital pattern data available")


if __name__ == "__main__":
    show()